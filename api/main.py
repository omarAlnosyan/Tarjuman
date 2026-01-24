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
    
    # تحميل LLM (اختياري)
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            from langchain_groq import ChatGroq
            AppState.llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                max_tokens=512,
                groq_api_key=groq_key
            )
            print("   [OK] LLM loaded (Llama 3.3 70B)")
        except Exception as e:
            print(f"   [WARN] LLM failed: {e}")
    else:
        print("   [WARN] LLM not available (GROQ_API_KEY missing)")
    
    print("[OK] Tarjuman API Ready!")


# ===== Helper Functions =====

def enhance_explanation(verse_text: str, db_explanation: str, poet_name: str) -> str:
    """
    تحسين الشرح باستخدام RAG + LLM
    - المصدر: قاعدة البيانات (شرح الزوزني)
    - التحسين: LLM (إعادة صياغة واضحة)
    """
    if not AppState.llm:
        # إذا LLM غير متاح، أرجع الشرح الأصلي من الـ DB
        return db_explanation
    
    try:
        prompt = f"""أنت خبير في الشعر العربي القديم. لديك شرح من كتاب الزوزني لأحد أبيات المعلقات.

المطلوب: أعد صياغة الشرح التالي بلغة عربية فصيحة وواضحة مع الحفاظ على المعنى الأصلي.

الشاعر: {poet_name}
البيت: {verse_text}

شرح الزوزني:
{db_explanation}

قواعد مهمة:
1. لا تضف معلومات من خارج النص
2. حافظ على المعنى الأصلي
3. اجعل اللغة واضحة ومفهومة
4. اكتب الشرح في فقرة واحدة متماسكة

الشرح المُحسّن:"""
        
        response = AppState.llm.invoke(prompt)
        enhanced = response.content.strip()
        
        # تأكد أن الـ LLM أرجع شيء مفيد
        if len(enhanced) > 20:
            return enhanced
        return db_explanation
        
    except Exception:
        return db_explanation


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
    """
    if not text or len(text.strip()) < 5:
        return False
    
    # رفض الأسئلة العامة
    general_patterns = [
        "كيف حالك", "من أنت", "ما اسمك", "مرحبا", "السلام عليكم",
        "ماذا تفعل", "أخبرني عن", "ما هو", "كيف", "لماذا", "متى",
        "من هو", "أين", "كم", "هل يمكن", "ساعدني", "شكرا",
        "مساء الخير", "صباح الخير", "اهلا", "هاي", "hello", "hi",
        "what", "how", "who", "where", "why", "when"
    ]
    
    text_lower = text.lower().strip()
    for pattern in general_patterns:
        if pattern in text_lower:
            return False
    
    # يجب أن يحتوي على كلمات عربية كافية
    arabic_chars = sum(1 for ch in text if '\u0600' <= ch <= '\u06FF')
    if arabic_chars < 5:
        return False
    
    # يجب أن يكون طوله مناسب (4 كلمات على الأقل للبيت الشعري)
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
            detail="أنا مخصص للأبيات الشعرية فقط. الرجاء إدخال بيت شعري من المعلقات السبع."
        )
    
    try:
        # البحث - نتيجة واحدة فقط (أفضل تطابق)
        results = AppState.retriever.search(query, k=1, score_threshold=0.0)
        
        # ===== GUARDRAILS: التحقق من جودة النتيجة =====
        if not results or results[0].score < 0.3:
            raise HTTPException(
                status_code=404,
                detail="لم أجد هذا البيت في المعلقات السبع. جرّب بيتاً آخر."
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


@app.get("/poets", response_model=List[PoetInfo], tags=["Data"])
async def get_poets():
    """الحصول على قائمة الشعراء"""
    return AppState.poets


@app.get("/examples", response_model=List[ExampleItem], tags=["Data"])
async def get_examples():
    """الحصول على أمثلة جاهزة للبحث"""
    return [
        ExampleItem(text="قفا نبك من ذكرى حبيب ومنزل", poet="امرؤ القيس", poem="معلقة امرئ القيس"),
        ExampleItem(text="هل غادر الشعراء من متردم", poet="عنترة بن شداد", poem="معلقة عنترة"),
        ExampleItem(text="أمن أم أوفى دمنة لم تكلم", poet="زهير بن أبي سلمى", poem="معلقة زهير"),
        ExampleItem(text="عفت الديار محلها فمقامها", poet="لبيد بن ربيعة", poem="معلقة لبيد"),
        ExampleItem(text="ألا هبي بصحنك فاصبحينا", poet="عمرو بن كلثوم", poem="معلقة عمرو بن كلثوم"),
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
