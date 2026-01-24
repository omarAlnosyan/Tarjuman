# 🏛️ ترجمان (Tarjuman)
## مساعد ذكي لشرح الشعر العربي الفصيح

<div dir="rtl">

**ترجمان** هو نظام ذكي متخصص في شرح الشعر العربي الكلاسيكي، مبني على تقنية **RAG** (Retrieval-Augmented Generation)، يجمع بين دقة المصادر الموثوقة وقوة الذكاء الاصطناعي.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 نظرة عامة | Overview

<div dir="rtl">

**ترجمان** يوفر شرحاً دقيقاً وموثوقاً لأبيات الشعر العربي من المعلقات السبع، باستخدام:
- 🔍 **Hybrid Search** (BM25 + FAISS) للبحث الذكي
- 🤖 **Llama 3.3 70B** لتحسين الشرح
- 📚 **687 بيت شعري** من المعلقات السبع مع شروحات الزوزني

</div>

**Tarjuman** provides accurate and reliable explanations for Arabic poetry verses from the Seven Mu'allaqat, using:
- 🔍 **Hybrid Search** (BM25 + FAISS) for intelligent search
- 🤖 **Llama 3.3 70B** for explanation enhancement
- 📚 **687 poetry verses** from the Seven Mu'allaqat with Al-Zawzani's commentaries

---

## ✨ المميزات | Features

<div dir="rtl">

- ✅ **بحث هجين ذكي**: يجمع بين البحث النصي (BM25) والدلالي (FAISS)
- ✅ **تحسين تلقائي**: استخدام LLM لإعادة صياغة الشرح بلغة واضحة
- ✅ **واجهة تراثية**: تصميم عربي أصيل مستوحى من المخطوطات
- ✅ **حماية من الأخطاء**: رفض الأسئلة غير الشعرية تلقائياً
- ✅ **687 بيت**: قاعدة بيانات شاملة من المعلقات السبع

</div>

- ✅ **Intelligent Hybrid Search**: Combines keyword (BM25) and semantic (FAISS) search
- ✅ **Automatic Enhancement**: Uses LLM to rephrase explanations in clear language
- ✅ **Heritage UI**: Authentic Arabic design inspired by manuscripts
- ✅ **Error Protection**: Automatically rejects non-poetry queries
- ✅ **687 Verses**: Comprehensive database from the Seven Mu'allaqat

---

## 🏗️ المعمارية | Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                       │
│                    Port: 3000                               │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/JSON
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│                    Port: 8000                                │
│  • Guardrails → Hybrid Search → LLM Enhancement            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
│  • JSON Database (687 verses)                               │
│  • ChromaDB (Vector Store)                                  │
│  • BM25 Index (In-memory)                                   │
└─────────────────────────────────────────────────────────────┘
```

**للتفاصيل الكاملة:** راجع [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)

---

## 🚀 البدء السريع | Quick Start

### المتطلبات | Requirements

- Python 3.9+
- Node.js 18+
- Groq API Key (للـ LLM - اختياري)

### التثبيت | Installation

```bash
# 1. Clone المشروع
git clone https://github.com/omarAlnosyan/Tarjuman.git
cd Tarjuman

# 2. إعداد Python Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. إعداد Frontend
cd tarjuman-ui
npm install
cd ..

# 4. إعداد API Keys
# انسخ env_template.txt وضيف GROQ_API_KEY
cp env_template.txt .env
# ثم عدّل .env وضيف مفتاحك
```

### تشغيل المشروع | Running

```bash
# Terminal 1: تشغيل API
python run_api.py

# Terminal 2: تشغيل Frontend
cd tarjuman-ui
npm run dev
```

**الروابط:**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## 📊 قاعدة البيانات | Database

<div dir="rtl">

المشروع يحتوي على **687 بيت شعري** من المعلقات السبع:

| الشاعر | عدد الأبيات |
|--------|-------------|
| امرؤ القيس | 103 |
| طرفة بن العبد | 118 |
| زهير بن أبي سلمى | 74 |
| لبيد بن ربيعة | 106 |
| عمرو بن كلثوم | 115 |
| عنترة بن شداد | 85 |
| الحارث بن حلزة | 86 |

**المصدر:** شرح المعلقات السبع للزوزني

</div>

The project contains **687 poetry verses** from the Seven Mu'allaqat:

| Poet | Verses |
|------|--------|
| Imru' al-Qais | 103 |
| Tarafa | 118 |
| Zuhayr | 74 |
| Labid | 106 |
| Amr ibn Kulthum | 115 |
| Antarah | 85 |
| Al-Harith | 86 |

**Source:** Al-Zawzani's Commentary on the Seven Mu'allaqat

---

## 🔧 التقنيات المستخدمة | Tech Stack

### Backend
- **FastAPI** - Python web framework
- **LangChain** - LLM integration
- **ChromaDB** - Vector database
- **BM25Okapi** - Keyword search
- **FAISS** - Similarity search

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **TailwindCSS** - Styling
- **Amiri Font** - Arabic typography

### LLM
- **Llama 3.3 70B** - Language model
- **Groq API** - LLM provider

### Embeddings
- **multilingual-e5-base** - Embedding model

---

## 📖 الاستخدام | Usage

### مثال | Example

<div dir="rtl">

**المدخل:**
```
عفت الديار محلها فمقامها
```

**المخرج:**
- **الشاعر:** لبيد بن ربيعة
- **رقم البيت:** 3
- **البيت:** عَفَتِ الدِّيَار مَحَلُّهَا فَمُقَامُهَا بِمِنىً تَأَبَّد غَوْلُهَا فَرِجَامُها
- **الشرح:** [شرح محسّن بواسطة LLM]

</div>

**Input:**
```
عفت الديار محلها فمقامها
```

**Output:**
- **Poet:** Labid ibn Rabi'ah
- **Verse Number:** 3
- **Verse:** عَفَتِ الدِّيَار مَحَلُّهَا فَمُقَامُّهَا...
- **Explanation:** [LLM-enhanced explanation]

---

## 🛠️ إعادة بناء الفهارس | Rebuilding Indices

<div dir="rtl">

إذا أضفت بيانات جديدة أو عدّلت البيانات:

```bash
# إعادة بناء جميع الفهارس
python rebuild_index.py
```

</div>

If you add new data or modify existing data:

```bash
# Rebuild all indices
python rebuild_index.py
```

---

## 📁 هيكل المشروع | Project Structure

```
Tarjuman/
├── api/                    # FastAPI Backend
│   └── main.py
├── src/retrieval/          # Search Engine
│   ├── hybrid_search.py
│   ├── sparse_search.py
│   ├── dense_search.py
│   └── embeddings.py
├── data/
│   ├── raw/                # Source DOCX
│   ├── processed/          # JSON database
│   └── vectordb/          # ChromaDB
├── tarjuman-ui/            # Next.js Frontend
├── run_api.py              # API runner
├── rebuild_index.py        # Rebuild indices
└── process_docx_v2.py     # Process DOCX
```

---

## 🔐 المتغيرات البيئية | Environment Variables

```bash
GROQ_API_KEY=gsk_...  # Groq API key for LLM (optional)
```

**ملاحظة:** المشروع يعمل بدون LLM، لكن التحسين لن يكون متاحاً.

**Note:** The project works without LLM, but enhancement won't be available.

---

## 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health check |
| POST | `/search` | Search for verses |
| GET | `/poets` | List of poets |
| GET | `/examples` | Example verses |

**API Documentation:** http://localhost:8000/docs

---

## 🎯 أمثلة للاختبار | Test Examples

<div dir="rtl">

جرّب هذه الأبيات:

1. `قِفا نبك من ذِكرى حبيبٍ ومنزل`
2. `عفت الديار محلها فمقامها`
3. `هل غادر الشعراء من متردم`
4. `ألا هبي بصحنك فاصبحينا`
5. `آذنتنا ببينها أسماء`

</div>

Try these verses:

1. `قِفا نبك من ذِكرى حبيبٍ ومنزل`
2. `عفت الديار محلها فمقامها`
3. `هل غادر الشعراء من متردم`
4. `ألا هبي بصحنك فاصبحينا`
5. `آذنتنا ببينها أسماء`

---

## 🤝 المساهمة | Contributing

<div dir="rtl">

نرحب بمساهماتكم! يرجى:

1. Fork المشروع
2. إنشاء branch جديد (`git checkout -b feature/AmazingFeature`)
3. Commit التغييرات (`git commit -m 'Add some AmazingFeature'`)
4. Push للـ branch (`git push origin feature/AmazingFeature`)
5. فتح Pull Request

</div>

Contributions are welcome! Please:

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 الترخيص | License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 المؤلف | Author

**عمر النوسيان | Omar Alnosyan**

- GitHub: [@omarAlnosyan](https://github.com/omarAlnosyan)

---

## 🙏 شكر وتقدير | Acknowledgments

<div dir="rtl">

- **شرح المعلقات السبع للزوزني** - المصدر الأساسي للبيانات
- **Groq** - لتوفير API سريع لـ Llama 3.3
- **LangChain** - لإطار عمل RAG
- **ChromaDB** - لقاعدة بيانات الـ Vectors

</div>

- **Al-Zawzani's Commentary** - Primary data source
- **Groq** - For fast Llama 3.3 API
- **LangChain** - For RAG framework
- **ChromaDB** - For vector database

---

## 📊 الإحصائيات | Statistics

- **Total Verses:** 687
- **Poets:** 7
- **Poems:** 7
- **Database Size:** ~5 MB
- **Search Latency:** < 3 seconds
- **LLM Response:** < 5 seconds

---

## 🔗 روابط مفيدة | Useful Links

- [Architecture Diagram](ARCHITECTURE_DIAGRAM.md)
- [View Diagrams](view_diagrams.html)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [Groq API](https://console.groq.com/)

---

<div dir="rtl" align="center">

**⭐ إذا أعجبك المشروع، لا تنسى إعطاءه Star! ⭐**

</div>

<div align="center">

**⭐ If you like this project, don't forget to give it a Star! ⭐**

</div>
