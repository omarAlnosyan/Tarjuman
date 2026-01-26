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


class ChatRequest(BaseModel):
    """طلب محادثة"""
    query: str = Field(..., description="الاستعلام (بيت شعري أو سؤال)")


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
    
    # تحميل قاعدة البيانات
    chunks_path = ROOT_DIR / "data" / "processed" / "all_chunks_final.json"
    vectordb_path = ROOT_DIR / "data" / "vectordb"
    
    try:
        from src.retrieval.hybrid_search import create_hybrid_retriever
        import json
        
        # تحميل الـ Retriever
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
    
    # أسئلة عامة واضحة
    general_patterns = [
        "كيف حالك", "كيفك", "كيف الحال",
        "من أنت", "مين انت", "ما اسمك", "من انت", "وش اسمك",
        "مرحبا", "السلام عليكم", "اهلا", "هاي", "hello", "hi",
        "شكرا", "مشكور", "thanks", "thank you",
        "ماذا تفعل", "وش تسوي", "ما عملك", "وش تقدر تسوي",
        "من هو", "من هي", "مين هو", "وش قصة", "ليه كتب", "لماذا كتب",
        "عن الشاعر", "معلومات عن", "اخبرني عن", "حدثني عن",
        "ما المطلوب", "وش المطلوب", "ماذا اكتب", "وش اكتب", "كيف استخدمك",
        "ما هي المعلقات", "وش المعلقات", "ايش المعلقات", "المعلقات السبع",
        "help", "مساعدة", "ساعدني"
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
            return f"**{info['name']}**\n\n{info['info']}\n\n**عن معلقته:**\n{info['muallaqah']}"
    
    return None


def get_friendly_response(query: str) -> str:
    """
    ردود ودودة ومرنة على الأسئلة العامة
    """
    query_lower = query.lower().strip()
    
    # ردود على التحيات والأسئلة الشخصية
    if any(word in query_lower for word in ["كيف حالك", "كيفك", "كيف الحال"]):
        return "الحمدلله، أنا ترجمان، مساعدك الذكي في شرح الشعر الفصيح. كيف أقدر أساعدك اليوم؟"
    
    if any(word in query_lower for word in ["من أنت", "مين انت", "ما اسمك", "من انت", "وش اسمك"]) and "الشاعر" not in query_lower:
        return "أنا ترجمان، مساعدك المتخصص في شرح الشعر العربي القديم والمعلقات. أنا هنا لمساعدتك في فهم الأبيات الشعرية من خلال شروحات موثوقة من أمهات الكتب."
    
    if any(word in query_lower for word in ["مرحبا", "السلام عليكم", "اهلا", "هاي", "hello", "hi"]):
        return "أهلاً وسهلاً! أنا ترجمان، مساعدك في شرح الشعر الفصيح. تفضل بإلقاء بيت شعري أو اسألني عما بدا لك."
    
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
    
    # أسئلة عن الشعراء
    poets_names = ["امرؤ القيس", "امرئ القيس", "طرفة", "زهير", "لبيد", "عمرو بن كلثوم", "عمرو", "عنترة", "الحارث"]
    for poet in poets_names:
        if poet in query_lower:
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
    
    # التحقق من الأسئلة العامة أولاً
    if is_general_question(query):
        friendly_response = get_friendly_response(query)
        return ChatResponse(
            type="chat",
            response=friendly_response
        )
    
    # محاولة البحث عن بيت شعري
    try:
        # تحسين البحث لدعم فهم الكلمات باختلاف السياقات
        # البحث بطرق متنوعة: تطابق النص + معنى الأبيات
        results = AppState.retriever.search(query, k=1, score_threshold=0.0)
        
        if results and len(results) > 0:
            r = results[0]
            
            # طباعة للتشخيص
            print(f"[DEBUG] Query: {query}")
            print(f"[DEBUG] Top result score: {r.score}")
            print(f"[DEBUG] Verse: {r.verse_text[:50]}...")
            
            # التحقق من جودة النتيجة (score threshold منخفض جداً لدعم البحث الدلالي)
            if r.score >= 0.1:  # threshold منخفض جداً للسماح بالبحث الدلالي
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
                # رسالة واضحة للمستخدم
                return ChatResponse(
                    type="chat",
                    response=f"لم أعثر على هذا البيت في قاعدة بياناتي. أنا متخصص في المعلقات السبع فقط:\n\n• امرؤ القيس\n• طرفة بن العبد\n• زهير بن أبي سلمى\n• لبيد بن ربيعة\n• عمرو بن كلثوم\n• عنترة بن شداد\n• الحارث بن حلزة\n\nجرّب بيتاً من أحد هؤلاء الشعراء."
                )
    except Exception as e:
        # في حالة خطأ في البحث، نتابع للرد الودود
        print(f"[DEBUG] Search error: {e}")
        import traceback
        traceback.print_exc()
        pass
    
    # إذا لم يُعثر على نتائج، رسالة واضحة
    return ChatResponse(
        type="chat",
        response=f"لم أعثر على هذا البيت في قاعدة بياناتي. أنا متخصص في المعلقات السبع فقط:\n\n• امرؤ القيس - معلقة امرئ القيس\n• طرفة بن العبد - معلقة طرفة\n• زهير بن أبي سلمى - معلقة زهير\n• لبيد بن ربيعة - معلقة لبيد\n• عمرو بن كلثوم - معلقة عمرو\n• عنترة بن شداد - معلقة عنترة\n• الحارث بن حلزة - معلقة الحارث\n\nتفضل بإرسال بيت من أحد هؤلاء الشعراء."
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
