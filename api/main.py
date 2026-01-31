"""
ترجمان API - FastAPI Backend
المساعد الذكي لشرح الشعر العربي الفصيح
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv('env_template.txt')

# إضافة المسار الأساسي
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# ===== Pydantic Models =====

class SearchRequest(BaseModel):
    """طلب البحث"""
    query: str = Field(..., description="النص المراد البحث عنه (بيت شعري أو جزء منه)")


class HistoryMessage(BaseModel):
    """رسالة في سجل المحادثة"""
    role: str = Field(..., description="دور المرسل: user أو assistant")
    content: str = Field(..., description="نص الرسالة")


class ChatRequest(BaseModel):
    """طلب محادثة"""
    query: str = Field(..., description="الاستعلام (بيت شعري أو سؤال)")
    history: Optional[List[HistoryMessage]] = Field(default_factory=list, description="آخر رسائل المحادثة للسياق")


class SearchResultItem(BaseModel):
    """نتيجة بحث واحدة"""
    chunk_id: str
    poet_name: str
    poem_name: str
    verse_number: int
    verse_text: str
    explanation: str  # شرح واحد محسّن (RAG + LLM)
    source_title: str
    source_page: Optional[int] = None
    score: float


class SearchResponse(BaseModel):
    """استجابة البحث"""
    query: str
    total_results: int
    results: List[SearchResultItem]


class ChatResponse(BaseModel):
    """استجابة المحادثة"""
    type: str = Field(..., description="نوع الرد: 'poetry' أو 'chat'")
    result: Optional[SearchResultItem] = None
    response: Optional[str] = None


class PoetInfo(BaseModel):
    """معلومات شاعر"""
    name: str
    poem_count: int
    verse_count: int


class ExampleItem(BaseModel):
    """مثال جاهز"""
    text: str
    poet: str
    poem: str


class HealthResponse(BaseModel):
    """حالة السيرفر"""
    status: str
    database_loaded: bool
    llm_available: bool
    verse_count: int


# ===== FastAPI App =====

app = FastAPI(
    title="ترجمان API",
    description="API لشرح الشعر العربي الفصيح - المعلقات السبع",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # في Production غيّرها للدومين الصحيح
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Global State =====

class AppState:
    """حالة التطبيق (Singleton)"""
    retriever = None
    llm = None
    chunks = []
    poets = []
    
    @classmethod
    def is_loaded(cls):
        return cls.retriever is not None


# ===== Startup Event =====

@app.on_event("startup")
async def startup_event():
    """تحميل الموارد عند بدء السيرفر"""
    print("[*] Loading Tarjuman API...")
    
    # تحميل قاعدة البيانات (المعلقات السبع)
    chunks_path = ROOT_DIR / "data" / "processed" / "all_chunks_final.json"
    vectordb_path = ROOT_DIR / "data" / "vectordb"
    
    try:
        from src.retrieval.hybrid_search import create_hybrid_retriever
        import json
        
        AppState.retriever = create_hybrid_retriever(
            chunks_path=str(chunks_path),
            vectordb_path=str(vectordb_path),
            build_new=False
        )
        print("   [OK] Hybrid Retriever loaded")
        
        # تحميل الـ chunks للمعلومات الإضافية
        with open(chunks_path, 'r', encoding='utf-8') as f:
            AppState.chunks = json.load(f)
        print(f"   [OK] Loaded {len(AppState.chunks)} verses")
        
        # استخراج قائمة الشعراء
        poets_dict = {}
        for chunk in AppState.chunks:
            poet = chunk.get('poet_name', 'Unknown')
            poem = chunk.get('poem_name', '')
            if poet not in poets_dict:
                poets_dict[poet] = {'poems': set(), 'verses': 0}
            poets_dict[poet]['poems'].add(poem)
            poets_dict[poet]['verses'] += 1
        
        AppState.poets = [
            PoetInfo(name=name, poem_count=len(data['poems']), verse_count=data['verses'])
            for name, data in poets_dict.items()
        ]
        print(f"   [OK] Extracted {len(AppState.poets)} poets")
        
    except Exception as e:
        print(f"   [ERROR] Failed to load database: {e}")
    
    # تحميل LLM (Groq - سريع جداً)
    try:
        groq_key = os.environ.get("GROQ_API_KEY")
        if groq_key and groq_key.strip():
            from langchain_groq import ChatGroq
            
            AppState.llm = ChatGroq(
                model="llama-3.3-70b-versatile",  # نموذج Groq - سريع جداً
                temperature=0.1,
                max_tokens=512,
                groq_api_key=groq_key
            )
            print("   [OK] LLM loaded (Groq - Llama 3.3 70B)")
        else:
            print("   [WARN] LLM not available (GROQ_API_KEY missing)")
            AppState.llm = None
    except Exception as e:
        print(f"   [WARN] LLM failed: {e}")
        print("   [INFO] Make sure GROQ_API_KEY is set in environment")
        AppState.llm = None

# ===== Helper Functions =====

def enhance_explanation(verse_text: str, db_explanation: str, poet_name: str) -> str:
    """
    تنظيف الشرح من الزوزني - إزالة البيت والمعلومات الإضافية
    - المصدر: قاعدة البيانات (شرح الزوزني)
    """
    # تنظيف الشرح من البيت والمعلومات الزائدة
    explanation = db_explanation
    
    # إزالة "البيت: ..." إذا كان موجوداً
    if "البيت:" in explanation:
        parts = explanation.split("الشرح:", 1)
        if len(parts) > 1:
            explanation = parts[1].strip()
        else:
            # محاولة إزالة كل شيء قبل السطر الثاني
            lines = explanation.split('\n')
            if len(lines) > 1:
                explanation = '\n'.join(lines[1:]).strip()
    
    # إزالة أي سطر يبدأ بـ "البيت:"
    lines = explanation.split('\n')
    cleaned_lines = []
    skip_next = False
    
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith("البيت:"):
            skip_next = True
            continue
        if skip_next and (line_stripped.startswith("الشرح:") or len(line_stripped) > 50):
            skip_next = False
        if not skip_next and line_stripped:
            # إزالة "الشرح:" إذا كانت في بداية السطر
            if line_stripped.startswith("الشرح:"):
                line_stripped = line_stripped.replace("الشرح:", "").strip()
            if line_stripped:
                cleaned_lines.append(line_stripped)
    
    explanation = ' '.join(cleaned_lines).strip()
    
    return explanation if explanation else db_explanation


def is_general_question(query: str) -> bool:
    """
    التحقق من أن الاستعلام سؤال عام وليس بيت شعري
    """
    query_lower = query.lower().strip()
    query_clean = _strip_harakat(_normalize_arabic(query_lower))

    # استثناء صريح: "هل غادر الشعراء" أو "هل غادر الشعراء من متردم" — بيت عنترة، لا سؤال عام
    if ("غادر" in query_clean and "متردم" in query_clean) or ("غادر" in query_clean and "الشعراء" in query_clean):
        return False

    # أسئلة عامة واضحة + متابعات حوارية (لا تُعامل كبحث عن بيت)
    general_patterns = [
        "كيف حالك", "كيفك", "كيف الحال", "وشلونك", "شلونك", "وش اخبارك", "شخبارك",
        "من أنت", "مين انت", "ما اسمك", "من انت", "وش اسمك",
        "مرحبا", "السلام عليكم", "سلام عليكم", "اهلا", "هاي", "hello", "hi",
        "شكرا", "مشكور", "thanks", "thank you",
        "ماذا تفعل", "وش تسوي", "ما عملك", "وش تقدر تسوي",
        "من هو", "من هي", "مين هو", "وش قصة", "ليه كتب", "لماذا كتب",
        "عن الشاعر", "معلومات عن", "اخبرني عن", "حدثني عن",
        "ما المطلوب", "وش المطلوب", "ماذا اكتب", "وش اكتب", "كيف استخدمك",
        "ما هي المعلقات", "وش المعلقات", "ايش المعلقات", "المعلقات السبع",
        "help", "مساعدة", "ساعدني",
        # متابعات حوارية — تُوجّه للمحادثة (مع history) وليس للبحث عن بيت
        "وضح اكثر", "وضّح أكثر", "وضح أكثر", "واضح اكثر",
        "اشرح اكثر", "اشرح أكثر", "تفصيل اكثر", "تفصيل أكثر",
        "اكثر تفصيلا", "أكثر تفصيلاً", "زدني", "ماذا تقصد", "ماذا تقصد؟",
        "ايش تقصد", "ممكن توضح", "هل يمكن التوضيح"
    ]
    
    # أسماء وألقاب الشعراء - إذا كان الاستعلام اسم شاعر فقط
    poet_names = [
        "امرؤ القيس", "امرئ القيس", "الملك الضليل",
        "طرفة", "طرفة بن العبد", "شاعر الناقة",
        "زهير", "زهير بن أبي سلمى", "شاعر الحكمة",
        "لبيد", "لبيد بن ربيعة",
        "عمرو", "عمرو بن كلثوم", "شاعر الفخر",
        "عنترة", "عنترة بن شداد", "الفارس الشاعر",
        "الحارث", "الحارث بن حلزة", "شاعر القبيلة"
    ]
    
    # إذا كان الاستعلام قصير (أقل من 10 كلمات) ويحتوي على اسم شاعر
    if len(query.split()) < 10:
        for poet in poet_names:
            if poet in query_lower:
                return True
    
    return any(pattern in query_lower for pattern in general_patterns)


def get_poet_info(poet_name: str) -> str:
    """
    معلومات عن الشعراء وأشهر معلقاتهم
    """
    poets_info = {
        "امرؤ القيس": {
            "name": "امرؤ القيس بن حجر الكندي",
            "info": "شاعر جاهلي يُعد من أشهر شعراء العرب، لُقّب بـ 'الملك الضليل'. عاش في القرن السادس الميلادي وكان أميراً من أمراء كندة.",
            "muallaqah": "كتب معلقته الشهيرة 'قفا نبك من ذكرى حبيب ومنزل' وفيها وصف الديار والذكريات والحبيبة، وهي من أشهر المعلقات العربية."
        },
        "طرفة": {
            "name": "طرفة بن العبد البكري",
            "info": "شاعر جاهلي من قبيلة بكر بن وائل، عاش في القرن السادس الميلادي. اشتهر بشعره الحماسي ووصفه للناقة.",
            "muallaqah": "معلقته 'لخولة أطلال ببرقة ثهمد' من أروع المعلقات، وفيها وصف رائع للناقة والحياة الجاهلية."
        },
        "زهير": {
            "name": "زهير بن أبي سُلمى المزني",
            "info": "من أعظم شعراء الجاهلية، اشتهر بالحكمة والموعظة في شعره. عاش في القرن السادس الميلادي.",
            "muallaqah": "معلقته 'أمن أم أوفى دمنة لم تكلم' تتميز بالحكمة والدعوة للسلام والصلح بين القبائل."
        },
        "لبيد": {
            "name": "لبيد بن ربيعة العامري",
            "info": "شاعر جاهلي ثم أسلم في عهد النبي محمد ﷺ. عُمّر طويلاً وأدرك الإسلام وترك الشعر بعد إسلامه.",
            "muallaqah": "معلقته 'عفت الديار محلها فمقامها' من أجمل المعلقات، وفيها وصف للديار والطبيعة والحياة."
        },
        "عمرو": {
            "name": "عمرو بن كلثوم التغلبي",
            "info": "شاعر جاهلي من قبيلة تغلب، اشتهر بالفخر والحماسة. عاش في القرن السادس الميلادي.",
            "muallaqah": "معلقته 'ألا هبي بصحنك فاصبحينا' من أشهر معلقات الفخر والحماسة في الشعر الجاهلي."
        },
        "عنترة": {
            "name": "عنترة بن شداد العبسي",
            "info": "فارس وشاعر جاهلي، ابن أمة حبشية. اشتهر بشجاعته وحبه لابنة عمه عبلة.",
            "muallaqah": "معلقته 'هل غادر الشعراء من متردم' تجمع بين الحماسة والغزل ووصف المعارك."
        },
        "الحارث": {
            "name": "الحارث بن حلزة اليشكري",
            "info": "شاعر جاهلي من قبيلة بكر، عاش في القرن السادس الميلادي.",
            "muallaqah": "معلقته 'آذنتنا ببينها أسماء' فيها دفاع عن قبيلته وفخر بأمجادها."
        }
    }
    
    # البحث عن الشاعر بأسماء مختلفة
    for key, info in poets_info.items():
        if key in poet_name or poet_name in info["name"]:
            label = "عن معلقته:" if "معلقة" in info.get("muallaqah", "") else "من شعره:"
            return f"**{info['name']}**\n\n{info['info']}\n\n**{label}**\n{info['muallaqah']}"
    
    return None


def _normalize_arabic(text: str) -> str:
    """توحيد ي/ى للتطابق."""
    return text.replace('\u0649', '\u064a')  # ى -> ي


def _strip_harakat(text: str) -> str:
    """إزالة التشكيل (الحركات) وحرف التطويل من النص لتحسين التطابق."""
    if not text:
        return text
    # إزالة التطويل (ـ U+0640) أولاً ثم الحركات
    text = text.replace('\u0640', '')  # كشيدة/تطويل
    # نطاق حركات التشكيل في Unicode
    return ''.join(c for c in text if not ('\u064B' <= c <= '\u0652' or c in '\u0670\u0617\u0618\u0619\u061A'))


def is_explain_request_without_verse(query: str) -> bool:
    """
    طلبات شرح/معنى بدون بيت أو كلمات من البيت — نطلب من المستخدم إعطاء بيت.
    مثل: اشرح لي، ما معنى، ما المقصود، شرح، حدثني، أخبرني، ساعدني (بدون ذكر بيت).
    إذا جاء بعد الطلب كلمات من بيت (نص عربي فعلي) لا نعتبره "بدون بيت".
    """
    q = query.strip()
    q_clean = q.replace("؟", "").replace("?", "").strip()
    if len(q_clean) > 40:  # نص طويل غالباً فيه بيت
        return False
    explain_only_patterns = [
        "اشرح لي", "اشرح", "ما معنى", "ما المقصود", "ماهو معنى", "ما هو معنى",
        "تحدث", "حدثني", "أخبرني", "اخبرني", "ساعدني", "وضح", "ما معني",
        "شرح لي", "المقصود"
    ]
    q_lower = q_clean.lower()
    for p in explain_only_patterns:
        if q_lower == p:
            return True
        if q_lower.startswith(p + " ") or q_lower.startswith(p + "؟"):
            remainder = q_clean[len(p):].strip()
            # إذا بقي نص عربي (كلمة أو أكثر) نعتبره ذكراً لبيت/كلمات
            remainder_arabic = "".join(c for c in remainder if "\u0600" <= c <= "\u06FF")
            if len(remainder_arabic) >= 3:  # كلمة عربية على الأقل
                return False
            return True
    return False


def _find_verse_in_chunks_by_keywords(query: str, chunks: list) -> Optional[dict]:
    """
    بحث خطي في الـ chunks: إذا كان الاستعلام (ناقص أو كامل) يطابق بيتاً في verse_text
    نرجعه. يُستخدم كـ fallback عندما يفشل الـ retriever (مثل لخولة أطلال، آذنتنا ببينها أسماء).
    """
    if not query or not chunks:
        return None
    q_clean = _strip_harakat(_normalize_arabic(query.strip()))
    if len(q_clean) < 3:
        return None
    q_words = [w for w in q_clean.split() if len(w) >= 2]
    best_chunk = None
    best_score = 0
    for chunk in chunks:
        vt = chunk.get("verse_text") or ""
        v_clean = _strip_harakat(_normalize_arabic(vt))
        if not v_clean:
            continue
        # تطابق كامل: الاستعلام جزء من البيت
        if q_clean in v_clean:
            return chunk
        # تطابق بالكلمات: عدد كلمات الاستعلام الموجودة في البيت
        matches = sum(1 for w in q_words if w in v_clean)
        if matches >= 2 and matches > best_score:
            best_score = matches
            best_chunk = chunk
    return best_chunk


def get_friendly_response(query: str) -> str:
    """
    ردود ودودة ومرنة على الأسئلة العامة
    """
    query_lower = query.lower().strip()
    query_norm = _normalize_arabic(query_lower)
    
    # ردود على التحيات والأسئلة الشخصية (بما فيها العامية)
    if any(word in query_lower for word in ["كيف حالك", "كيفك", "كيف الحال", "وشلونك", "شلونك", "وش اخبارك", "شخبارك"]):
        return "الحمدلله، أنا ترجمان، مساعدك الذكي في شرح الشعر الفصيح. كيف أقدر أساعدك اليوم؟"
    
    if any(word in query_lower for word in ["من أنت", "مين انت", "ما اسمك", "من انت", "وش اسمك"]) and "الشاعر" not in query_lower:
        return "أنا ترجمان، مساعدك المتخصص في شرح الشعر العربي القديم والمعلقات. أنا هنا لمساعدتك في فهم الأبيات الشعرية من خلال شروحات موثوقة من أمهات الكتب."
    
    if any(word in query_lower for word in ["مرحبا", "السلام عليكم", "سلام عليكم", "اهلا", "هاي", "hello", "hi"]):
        return "أهلاً وسهلاً! وعليكم السلام. أنا ترجمان، مساعدك في شرح الشعر الفصيح. تفضل بإلقاء بيت شعري أو اسألني عما بدا لك."
    
    if any(word in query_lower for word in ["شكرا", "مشكور", "thanks", "thank you"]):
        return "العفو! أنا دائماً هنا لمساعدتك في فهم الشعر العربي. هل لديك بيت آخر تريد شرحه؟"
    
    if any(word in query_lower for word in ["ماذا تفعل", "وش تسوي", "ما عملك", "وش تقدر تسوي", "ما المطلوب", "وش المطلوب", "ماذا اكتب", "وش اكتب", "كيف استخدمك", "مساعدة", "help"]):
        return """يمكنني مساعدتك في:

• شرح الأبيات الشعرية - أرسل أي بيت من المعلقات السبع
• معلومات عن الشعراء - اسألني: "من هو امرؤ القيس؟"
• معلومات عن المعلقات - اسألني: "ما هي المعلقات؟"

أمثلة:
• قفا نبك من ذكرى حبيب ومنزل
• من هو عنترة؟
• ما هي المعلقات؟"""
    
    # أسئلة عن الشعراء (استخدام النص الموحد ي/ى لتفادي فشل التطابق)
    poets_names = ["امرؤ القيس", "امرئ القيس", "طرفة", "زهير", "لبيد", "عمرو بن كلثوم", "عمرو", "عنترة", "الحارث"]
    for poet in poets_names:
        if _normalize_arabic(poet) in query_norm or poet in query_lower:
            poet_info = get_poet_info(poet)
            if poet_info:
                return poet_info
    
    # أسئلة عن المعلقات بشكل عام
    if any(word in query_lower for word in ["المعلقات", "المعلقه", "ما هي المعلقات", "وش المعلقات"]):
        return """**المعلقات السبع** هي من أشهر وأجود ما قيل في الشعر الجاهلي. سُميت بالمعلقات لأنها كُتبت بماء الذهب وعُلّقت على أستار الكعبة لشدة جودتها.

**الشعراء السبعة:**
• امرؤ القيس - الملك الضليل
• طرفة بن العبد - شاعر الناقة
• زهير بن أبي سلمى - شاعر الحكمة
• لبيد بن ربيعة - أدرك الإسلام
• عمرو بن كلثوم - شاعر الفخر
• عنترة بن شداد - الفارس الشاعر
• الحارث بن حلزة - شاعر القبيلة

تفضل بإرسال بيت شعري أو اسألني عن أي شاعر!"""
    
    # رد افتراضي ودود
    return "أنا ترجمان، مساعدك المتخصص في شرح الشعر العربي القديم. أنا هنا لمساعدتك في فهم الأبيات الشعرية من المعلقات السبع. تفضل بإرسال بيت شعري أو اسألني عن أحد الشعراء!"


def get_llm_response_with_history(
    query: str,
    history: Optional[List] = None,
    context_hint: Optional[str] = None,
) -> Optional[str]:
    """
    استدعاء الـ LLM مع سجل المحادثة لردود حوارية.
    history: قائمة من {role: "user"|"assistant", content: str}
    context_hint: تلميح سياقي (مثلاً: لم نجد البيت في القاعدة).
    """
    if not AppState.llm:
        return None
    try:
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

        system = """أنت ترجمان، مساعد متخصص في شرح الشعر العربي القديم والمعلقات السبع.
تجاوب باختصار ووضوح، وبصيغة Markdown عند الحاجة (عناوين، توكيد، قوائم).

أجب بالعربية الفصحى فقط. لا تستخدم أبداً حروفاً أو كلمات من لغات أخرى (مثل الصينية أو الإنجليزية) في جسم الرد.

المعلقات السبع المعتمدة هنا (ولا غيرها) هي لسبعة شعراء فقط ولا غيرهم أبداً:
امرؤ القيس، طرفة بن العبد، زهير بن أبي سلمى، لبيد بن ربيعة، عمرو بن كلثوم، عنترة بن شداد، الحارث بن حلزة.
لا تذكر أبداً: عبيد بن الأبرص، العجاج، نابغة الذبياني، علقمة بن عبدة، أو أي اسم آخر غير السبعة المذكورين أعلاه.

إذا طُلِب منك «وضّح أكثر» أو «زدني» فاعتمد آخر ما تم التحدث عنه في المحادثة ووضحه أو زد عليه.
لا تختلق أبياتاً غير موجودة؛ إذا لم تعرف، قل ذلك بأدب."""
        if context_hint:
            system += f"\n\nملاحظة سياق: {context_hint}"

        messages = [SystemMessage(content=system)]
        h = (history or [])[-8:]
        for m in h:
            role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else None)
            content = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else "") or ""
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        messages.append(HumanMessage(content=query))

        out = AppState.llm.invoke(messages)
        if hasattr(out, "content") and out.content:
            text = out.content.strip()
            # إزالة حروف من لغات أخرى (مثل الصينية) إن تسربت إلى الرد
            text = _keep_arabic_and_latin(text)
            return text if text else None
        return None
    except Exception as e:
        print(f"[DEBUG] LLM with history error: {e}")
        return None


def _keep_arabic_and_latin(text: str) -> str:
    """الإبقاء على الحروف العربية واللاتينية والأرقام وعلامات الترقيم الشائعة فقط."""
    if not text:
        return text
    result = []
    for c in text:
        if '\u0600' <= c <= '\u06FF':  # عربي
            result.append(c)
        elif 'A' <= c <= 'Z' or 'a' <= c <= 'z':  # لاتيني
            result.append(c)
        elif c.isdigit() or c in ' \n\t.,;:!?\-–—\'\"()[]{}•·*#\u200c\u200d':
            result.append(c)
    return ''.join(result)


# ===== API Endpoints =====

@app.get("/health", response_model=HealthResponse, tags=["Status"])
async def health_check():
    """فحص حالة السيرفر"""
    return HealthResponse(
        status="healthy" if AppState.is_loaded() else "degraded",
        database_loaded=AppState.retriever is not None,
        llm_available=AppState.llm is not None,
        verse_count=len(AppState.chunks)
    )


def is_poetry_query(text: str) -> bool:
    """
    التحقق من أن الاستعلام بيت شعري وليس سؤال عام.
    Guardrails صارمة - رفض أي شيء غير الشعر.
    """
    if not text or len(text.strip()) < 5:
        return False
    
    text_lower = text.lower().strip()
    
    # رفض الأسئلة العامة (قائمة موسعة)
    general_patterns = [
        "كيف حالك", "من أنت", "ما اسمك", "مرحبا", "السلام عليكم",
        "ماذا تفعل", "أخبرني عن", "ما هو", "كيف", "لماذا", "متى",
        "من هو", "أين", "كم", "هل يمكن", "ساعدني", "شكرا",
        "مساء الخير", "صباح الخير", "اهلا", "هاي", "hello", "hi",
        "what", "how", "who", "where", "why", "when",
        "ما معنى", "اشرح لي", "ما المقصود", "تعريف", "ما هي",
        "أخبرني", "حدثني", "تكلم", "تحدث", "شرح", "ما هو معنى"
    ]
    
    for pattern in general_patterns:
        if pattern in text_lower:
            return False
    
    # رفض الأسئلة التي تبدأ بكلمات استفهام (إلا إذا كانت جزء من بيت شعري)
    question_starters = ["ما هو", "ما هي", "من هو", "من هي", "كيف", "لماذا", "متى", "أين"]
    if any(text_lower.startswith(starter) for starter in question_starters):
        # إلا إذا كان النص طويلاً (مثل بيت شعري)
        if len(text) < 20:
            return False
    
    # يجب أن يحتوي على كلمات عربية كافية
    arabic_chars = sum(1 for ch in text if '\u0600' <= ch <= '\u06FF')
    if arabic_chars < 5:
        return False
    
    # يجب أن يكون طوله مناسب (3 كلمات على الأقل للبيت الشعري)
    words = text.split()
    if len(words) < 3:
        return False
    
    return True


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_verses(request: SearchRequest):
    """
    البحث عن الأبيات الشعرية (RAG + LLM)
    
    - يبحث في قاعدة البيانات (943 بيت من المعلقات)
    - يُحسّن الشرح تلقائياً باستخدام LLM
    - يرفض الأسئلة العامة (Guardrails)
    """
    if not AppState.is_loaded():
        raise HTTPException(status_code=503, detail="قاعدة البيانات غير محملة")
    
    query = request.query.strip()
    if len(query) < 3:
        raise HTTPException(status_code=400, detail="يجب أن يكون الاستعلام 3 أحرف على الأقل")
    
    # ===== GUARDRAILS: رفض الأسئلة غير الشعرية =====
    if not is_poetry_query(query):
        raise HTTPException(
            status_code=400, 
            detail="أنا متخصص في الأبيات الشعرية فقط، كيف أقدر أساعدك في الشعر؟"
        )
    
    try:
        # البحث - نتيجة واحدة فقط (أفضل تطابق)
        results = AppState.retriever.search(query, k=1, score_threshold=0.0)
        
        # ===== GUARDRAILS: التحقق من جودة النتيجة =====
        if not results or results[0].score < 0.3:
            raise HTTPException(
                status_code=404,
                detail="لم أجد هذا البيت في قاعدة البيانات. جرّب بيتاً آخر من المعلقات السبع."
            )
        
        # أفضل نتيجة
        r = results[0]
        
        # استخراج الشرح من النص (من الـ Database)
        db_explanation = r.text
        if 'الشرح:' in db_explanation:
            db_explanation = db_explanation.split('الشرح:')[1].strip()
        elif '\n\n' in db_explanation:
            db_explanation = db_explanation.split('\n\n', 1)[1].strip()
        
        # تحسين الشرح باستخدام LLM (RAG + LLM)
        poet_name = r.poet_name or "غير معروف"
        enhanced_explanation = enhance_explanation(r.verse_text, db_explanation, poet_name)
        
        # استخراج رقم البيت (من الـ SearchResult مباشرة)
        verse_num = r.verse_number if r.verse_number else 0
        
        item = SearchResultItem(
            chunk_id=str(r.chunk_id),
            poet_name=poet_name,
            poem_name=r.poem_name or "غير معروف",
            verse_number=verse_num,
            verse_text=r.verse_text or query,
            explanation=enhanced_explanation,
            source_title=r.source_book or "شرح المعلقات السبع للزوزني",
            source_page=None,
            score=r.score
        )
        
        return SearchResponse(
            query=query,
            total_results=1,
            results=[item]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في البحث: {str(e)}")


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    محادثة تفاعلية - يدعم البحث عن الأبيات والردود المرنة على الأسئلة العامة
    
    - إذا كان الاستعلام بيت شعري: يبحث ويعرض النتيجة
    - إذا كان سؤال عام: يرد رداً ودوداً ومرناً
    """
    if not AppState.is_loaded():
        return ChatResponse(
            type="chat",
            response="عذراً، قاعدة البيانات غير محملة حالياً. يرجى المحاولة لاحقاً."
        )
    
    query = request.query.strip()
    if len(query) < 2:
        return ChatResponse(
            type="chat",
            response="يرجى إدخال استعلام أطول."
        )
    
    # تحويل السجل لاستخدامه مع LLM (قائمة كائنات لها role و content)
    history_list = [{"role": m.role, "content": m.content} for m in (request.history or [])]

    query_lower = query.lower().strip()
    query_norm = _normalize_arabic(query_lower)

    # طلبات شرح/معنى بدون ذكر بيت — نطلب إعطاء بيت
    if is_explain_request_without_verse(query):
        return ChatResponse(
            type="chat",
            response="أعطني بيتاً أو كلمات من البيت لأشرحه لك من المعلقات السبع."
        )

    # أسئلة عن المعلقات: رد ثابت دائماً (قائمة صحيحة فقط — لا LLM أبداً)
    if "المعلقات" in query_norm or "المعلقه" in query_norm or "معلقات" in query_norm:
        _muallaqat_list = """**المعلقات السبع** هي من أشهر وأجود ما قيل في الشعر الجاهلي. سُميت بالمعلقات لأنها كُتبت بماء الذهب وعُلّقت على أستار الكعبة لشدة جودتها.

**الشعراء السبعة:**
• امرؤ القيس - الملك الضليل
• طرفة بن العبد - شاعر الناقة
• زهير بن أبي سلمى - شاعر الحكمة
• لبيد بن ربيعة - أدرك الإسلام
• عمرو بن كلثوم - شاعر الفخر
• عنترة بن شداد - الفارس الشاعر
• الحارث بن حلزة - شاعر القبيلة

تفضل بإرسال بيت شعري أو اسألني عن أي شاعر!"""
        return ChatResponse(type="chat", response=_muallaqat_list)

    # استثناء: "هل غادر الشعراء من متردم" (أو "هل غادر الشعراء") — بيت عنترة: بحث مباشر في الـ chunks
    query_clean = _strip_harakat(query_norm)
    is_ghader_verse = ("غادر" in query_clean and "متردم" in query_clean) or ("غادر" in query_clean and "الشعراء" in query_clean)
    if is_ghader_verse and AppState.chunks:
        for chunk in AppState.chunks:
            vt = chunk.get("verse_text") or ""
            v_clean = _strip_harakat(_normalize_arabic(vt))
            if "غادر" in v_clean and "متردم" in v_clean:
                db_explanation = chunk.get("text", "")
                explanation = enhance_explanation(vt, db_explanation, chunk.get("poet_name", ""))
                src = chunk.get("source") or {}
                source_book = src.get("book", "شرح المعلقات السبع للزوزني") if isinstance(src, dict) else "شرح المعلقات السبع للزوزني"
                item = SearchResultItem(
                    chunk_id=str(chunk.get("chunk_id", "")),
                    poet_name=chunk.get("poet_name") or "عنترة بن شداد",
                    poem_name=chunk.get("poem_name") or "معلقة عنترة",
                    verse_number=int(chunk.get("verse_number", 0)),
                    verse_text=vt,
                    explanation=explanation,
                    source_title=source_book,
                    source_page=None,
                    score=1.0,
                )
                return ChatResponse(type="poetry", result=item)

    # التحقق من الأسئلة العامة (تحيات، من أنت، ما اسمك، شعراء، إلخ)
    if is_general_question(query):
        # "من هو / من هي" + اسم شاعر: رد ثابت من get_poet_info (لا LLM أبداً)
        poets_refs_first = ["امرؤ القيس", "امرئ القيس", "طرفة", "زهير", "لبيد", "عمرو بن كلثوم", "عمرو", "عنترة", "الحارث"]
        if ("من هو" in query_lower or "من هي" in query_lower) and any(p in query_lower for p in poets_refs_first):
            friendly = get_friendly_response(query)
            if friendly:
                return ChatResponse(type="chat", response=friendly)
        # تحيات وردود ثابتة: نعتمد get_friendly_response لضمان رد موحد (لا بحث شعري ولا LLM عشوائي)
        static_patterns = [
            "سلام عليكم", "السلام عليكم", "مرحبا", "اهلا", "هاي", "hello", "hi",
            "كيف حالك", "كيفك", "وشلونك", "شلونك", "وش اخبارك", "شخبارك",
            "من أنت", "مين انت", "ما اسمك", "من انت", "وش اسمك",
            "شكرا", "مشكور", "thanks", "ماذا تفعل", "وش تسوي", "ما عملك", "مساعدة", "help"
        ]
        if any(p in query_lower for p in static_patterns):
            friendly = get_friendly_response(query)
            if friendly:
                return ChatResponse(type="chat", response=friendly)
        # أسئلة عن شاعر من السبعة: رد موحد صحيح
        poets_refs = ["امرؤ القيس", "امرئ القيس", "طرفة", "زهير", "لبيد", "عمرو بن كلثوم", "عمرو", "عنترة", "الحارث"]
        if any(p in query_lower for p in poets_refs):
            friendly = get_friendly_response(query)
            if friendly:
                return ChatResponse(type="chat", response=friendly)
        # متابعات (وضّح أكثر، زدني، ماذا تقصد...) نستخدم LLM مع السجل
        llm_reply = get_llm_response_with_history(query, history=history_list)
        if llm_reply:
            return ChatResponse(type="chat", response=llm_reply)
        friendly_response = get_friendly_response(query)
        return ChatResponse(type="chat", response=friendly_response)
    
    # محاولة البحث عن بيت شعري
    try:
        # لاستعلامات معروفة (مثل "هل غادر الشعراء من متردم") نسترجع عدة نتائج ونختار الأنسب
        k_search = 5
        if "غادر" in query_norm and "متردم" in query_norm:
            k_search = 8
        results = AppState.retriever.search(query, k=k_search, score_threshold=0.0)

        # إن كان الاستعلام يحتوي "غادر" و"متردم" نختار أول نتيجة تحتوي البيت (عنترة)، وإلا نترك النتائج فارغة للانتقال للـ fallback
        if results and "غادر" in query_norm and "متردم" in query_norm:
            found_ghader = None
            for candidate in results:
                v_clean = _strip_harakat(_normalize_arabic(candidate.verse_text or ""))
                if "غادر" in v_clean and "متردم" in v_clean:
                    found_ghader = candidate
                    break
            if found_ghader:
                results = [found_ghader]
            else:
                results = []  # لم نجد البيت في نتائج المحرك → نستخدم fallback (بحث مباشر في chunks)
        if not results:
            results = []

        if results and len(results) > 0:
            r = results[0]
            # طباعة للتشخيص
            print(f"[DEBUG] Query: {query}")
            print(f"[DEBUG] Top result score: {r.score}")
            print(f"[DEBUG] Verse: {r.verse_text[:50] if r.verse_text else ''}...")
            # إن اخترنا نتيجة لـ "غادر" و"متردم" نعتبرها مطابقة حتى لو الدرجة منخفضة
            force_verse_match = (
                "غادر" in query_norm and "متردم" in query_norm and r.verse_text and
                "غادر" in _strip_harakat(_normalize_arabic(r.verse_text)) and
                "متردم" in _strip_harakat(_normalize_arabic(r.verse_text))
            )
            # التحقق من جودة النتيجة (score threshold منخفض جداً لدعم البحث الدلالي)
            if r.score >= 0.1 or force_verse_match:  # threshold منخفض أو مطابقة صريحة لبيت "غادر/متردم"
                # تجنب إرجاع بيت خاطئ: إذا الاستعلام فيه 3+ كلمات والبيت المُرجع لا يحتوي على كلمتين على الأقل منه، اعتبره غير مطابق (ما عدا المطابقة الصريحة)
                if not force_verse_match:
                    query_words = set(_normalize_arabic(q) for q in query.split() if len(q.strip()) > 1)
                    verse_norm = _normalize_arabic(r.verse_text or "")
                    overlap = sum(1 for w in query_words if w in verse_norm)
                else:
                    overlap = 2  # تجاوز فحص التداخل عند المطابقة الصريحة
                if not force_verse_match and len(query_words) >= 3 and overlap < 2:
                    hint = "لم نجد البيت في قاعدة المعلقات؛ المستخدم قد يريد متابعة أو سؤالاً آخر."
                    llm_reply = get_llm_response_with_history(query, history=history_list, context_hint=hint)
                    if llm_reply:
                        return ChatResponse(type="chat", response=llm_reply)
                    return ChatResponse(
                        type="chat",
                        response=f"لم أعثر على هذا البيت في قاعدة بياناتي. أنا متخصص في المعلقات السبع:\n\n• امرؤ القيس • طرفة • زهير • لبيد • عمرو بن كلثوم • عنترة • الحارث بن حلزة\n\nجرّب بيتاً من أحد هؤلاء الشعراء."
                    )
                # استخراج الشرح من قاعدة البيانات
                db_explanation = r.text
                
                # الشرح من الزوزني فقط (بدون تحسين LLM)
                explanation = enhance_explanation(r.verse_text, db_explanation, r.poet_name)
                
                # إنشاء نتيجة البحث
                item = SearchResultItem(
                    chunk_id=str(r.chunk_id),
                    poet_name=r.poet_name or "غير معروف",
                    poem_name=r.poem_name or "غير معروف",
                    verse_number=r.verse_number if r.verse_number else 0,
                    verse_text=r.verse_text or query,
                    explanation=explanation,
                    source_title=r.source_book or "شرح المعلقات السبع للزوزني",
                    source_page=None,
                    score=r.score
                )
                
                return ChatResponse(
                    type="poetry",
                    result=item
                )
            else:
                print(f"[DEBUG] Score {r.score} below threshold 0.1")
                hint = "لم نجد البيت في قاعدة المعلقات."
                llm_reply = get_llm_response_with_history(query, history=history_list, context_hint=hint)
                if llm_reply:
                    return ChatResponse(type="chat", response=llm_reply)
                return ChatResponse(
                    type="chat",
                    response=f"لم أعثر على هذا البيت في قاعدة بياناتي. أنا متخصص في المعلقات السبع:\n\n• امرؤ القيس • طرفة • زهير • لبيد • عمرو بن كلثوم • عنترة • الحارث بن حلزة\n\nجرّب بيتاً من أحد هؤلاء الشعراء."
                )
    except Exception as e:
        # في حالة خطأ في البحث، نتابع للرد الودود
        print(f"[DEBUG] Search error: {e}")
        import traceback
        traceback.print_exc()
        pass

    # Fallback لبيت "هل غادر الشعراء (من متردم)": بحث مباشر في القطع إن فشل المحرك
    if is_ghader_verse and AppState.chunks:
        for chunk in AppState.chunks:
            vt = chunk.get("verse_text") or ""
            v_clean = _strip_harakat(_normalize_arabic(vt))
            if "غادر" in v_clean and "متردم" in v_clean:
                db_explanation = chunk.get("text", "")
                explanation = enhance_explanation(vt, db_explanation, chunk.get("poet_name", ""))
                src = chunk.get("source") or {}
                source_book = src.get("book", "شرح المعلقات السبع للزوزني") if isinstance(src, dict) else "شرح المعلقات السبع للزوزني"
                item = SearchResultItem(
                    chunk_id=str(chunk.get("chunk_id", "")),
                    poet_name=chunk.get("poet_name") or "عنترة بن شداد",
                    poem_name=chunk.get("poem_name") or "معلقة عنترة",
                    verse_number=int(chunk.get("verse_number", 0)),
                    verse_text=vt,
                    explanation=explanation,
                    source_title=source_book,
                    source_page=None,
                    score=1.0,
                )
                return ChatResponse(type="poetry", result=item)

    # Fallback عام: بحث بالكلمات المفتاحية في الـ chunks (لخولة أطلال، آذنتنا ببينها، بيت ناقص، إلخ)
    if AppState.chunks and len(query.strip()) >= 4:
        found_chunk = _find_verse_in_chunks_by_keywords(query, AppState.chunks)
        if found_chunk:
            vt = found_chunk.get("verse_text") or ""
            db_explanation = found_chunk.get("text", "")
            explanation = enhance_explanation(vt, db_explanation, found_chunk.get("poet_name", ""))
            src = found_chunk.get("source") or {}
            source_book = src.get("book", "شرح المعلقات السبع للزوزني") if isinstance(src, dict) else "شرح المعلقات السبع للزوزني"
            item = SearchResultItem(
                chunk_id=str(found_chunk.get("chunk_id", "")),
                poet_name=found_chunk.get("poet_name") or "غير معروف",
                poem_name=found_chunk.get("poem_name") or "غير معروف",
                verse_number=int(found_chunk.get("verse_number", 0)),
                verse_text=vt,
                explanation=explanation,
                source_title=source_book,
                source_page=None,
                score=0.9,
            )
            return ChatResponse(type="poetry", result=item)

    # إذا لم يُعثر على نتائج، محاولة رد حواري عبر LLM
    hint = "لم نجد البيت في قاعدة المعلقات."
    llm_reply = get_llm_response_with_history(query, history=history_list, context_hint=hint)
    if llm_reply:
        return ChatResponse(type="chat", response=llm_reply)
    return ChatResponse(
        type="chat",
        response=f"لم أعثر على هذا البيت في قاعدة بياناتي. أنا متخصص في المعلقات السبع:\n\n• امرؤ القيس • طرفة • زهير • لبيد • عمرو بن كلثوم • عنترة • الحارث بن حلزة\n\nتفضل بإرسال بيت من أحد هؤلاء الشعراء."
    )


@app.get("/poets", response_model=List[PoetInfo], tags=["Data"])
async def get_poets():
    """الحصول على قائمة الشعراء"""
    return AppState.poets


@app.get("/examples", response_model=List[ExampleItem], tags=["Data"])
async def get_examples():
    """الحصول على أمثلة جاهزة للبحث - أبيات من المعلقات السبع"""
    return [
        ExampleItem(text="قفا نبك من ذكرى حبيب ومنزل", poet="امرؤ القيس", poem="معلقة امرئ القيس"),
        ExampleItem(text="لخولة أطلال ببرقة ثهمد", poet="طرفة بن العبد", poem="معلقة طرفة"),
        ExampleItem(text="أمن أم أوفى دمنة لم تكلم", poet="زهير بن أبي سلمى", poem="معلقة زهير"),
        ExampleItem(text="عفت الديار محلها فمقامها", poet="لبيد بن ربيعة", poem="معلقة لبيد"),
        ExampleItem(text="ألا هبي بصحنك فاصبحينا", poet="عمرو بن كلثوم", poem="معلقة عمرو بن كلثوم"),
        ExampleItem(text="هل غادر الشعراء من متردم", poet="عنترة بن شداد", poem="معلقة عنترة"),
        ExampleItem(text="آذنتنا ببينها أسماء", poet="الحارث بن حلزة", poem="معلقة الحارث بن حلزة"),
    ]


@app.get("/", tags=["Info"])
async def root():
    """الصفحة الرئيسية"""
    return {
        "name": "ترجمان API",
        "version": "1.0.0",
        "description": "المساعد الذكي لشرح الشعر العربي الفصيح",
        "docs": "/docs",
        "health": "/health"
    }


# ===== Run Server =====

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
