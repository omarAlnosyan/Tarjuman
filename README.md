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
- 🤖 **Llama 3.3 70B** عبر Groq API
- 📚 **687 بيت شعري** من المعلقات السبع مع شروحات الزوزني

</div>

**Tarjuman** provides accurate and reliable explanations for Arabic poetry verses from the Seven Mu'allaqat, using:
- 🔍 **Hybrid Search** (BM25 + FAISS) for intelligent search
- 🤖 **Llama 3.3 70B** via Groq API
- 📚 **687 poetry verses** from the Seven Mu'allaqat with Al-Zawzani's commentaries

---

## ✨ المميزات | Features

<div dir="rtl">

### 🔍 البحث والشرح
- ✅ **بحث هجين ذكي**: يجمع بين البحث النصي (BM25) والدلالي (FAISS)
- ✅ **شرح نقي**: عرض شرح الزوزني مباشرة بدون إضافات
- ✅ **687 بيت**: قاعدة بيانات شاملة من المعلقات السبع

### 💬 المحادثة الذكية
- ✅ **معلومات الشعراء**: اسأل "من هو امرؤ القيس؟" أو "الفارس الشاعر"
- ✅ **معلومات المعلقات**: اسأل "ما هي المعلقات؟" للحصول على نبذة شاملة
- ✅ **ردود ودية**: يجيب على التحيات والأسئلة العامة بذكاء

### 🎨 الواجهة
- ✅ **تصميم تراثي**: واجهة عربية أصيلة مستوحاة من المخطوطات
- ✅ **صفحة هبوط**: تجربة استخدام سلسة مع شعار وعنوان جذاب
- ✅ **أمثلة سريعة**: أبيات شعرية وأسئلة عامة جاهزة للتجربة

</div>

### 🔍 Search & Explanation
- ✅ **Intelligent Hybrid Search**: Combines keyword (BM25) and semantic (FAISS) search
- ✅ **Pure Explanation**: Direct display of Al-Zawzani's commentary without additions
- ✅ **687 Verses**: Comprehensive database from the Seven Mu'allaqat

### 💬 Smart Conversation
- ✅ **Poet Information**: Ask "Who is Imru' al-Qais?" or use poet nicknames
- ✅ **Mu'allaqat Information**: Ask "What are the Mu'allaqat?" for comprehensive overview
- ✅ **Friendly Responses**: Intelligently answers greetings and general questions

### 🎨 Interface
- ✅ **Heritage Design**: Authentic Arabic UI inspired by manuscripts
- ✅ **Landing Page**: Smooth user experience with attractive logo and title
- ✅ **Quick Examples**: Ready-to-try poetry verses and general questions

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
│  • Smart Chat → Hybrid Search → Pure Explanation           │
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
- Groq API Key (مجاني من [console.groq.com](https://console.groq.com/))

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
- **Groq API** - LLM provider (fast and free)

### Embeddings
- **multilingual-e5-base** - Embedding model

---

## 📖 الاستخدام | Usage

<div dir="rtl">

### 1️⃣ شرح الأبيات الشعرية

**المدخل:**
```
عفت الديار محلها فمقامها
```

**المخرج:**
- **الشاعر:** لبيد بن ربيعة
- **رقم البيت:** 3
- **البيت الكامل:** عَفَتِ الدِّيَار مَحَلُّهَا فَمُقَامُهَا بِمِنىً تَأَبَّد غَوْلُهَا فَرِجَامُها
- **الشرح:** [شرح الزوزني النقي]

### 2️⃣ معلومات عن الشعراء

**أمثلة:**
- `من هو امرؤ القيس؟` → نبذة كاملة + لماذا كتب "قفا نبك"
- `الفارس الشاعر` → معلومات عن عنترة بن شداد
- `شاعر الحكمة` → معلومات عن زهير بن أبي سلمى

### 3️⃣ معلومات عامة

**أمثلة:**
- `ما هي المعلقات؟` → تعريف + قائمة الشعراء السبعة
- `كيف حالك؟` → رد ودود
- `من أنت؟` → تعريف بالبوت

</div>

### 1️⃣ Explaining Poetry Verses

**Input:**
```
عفت الديار محلها فمقامها
```

**Output:**
- **Poet:** Labid ibn Rabi'ah
- **Verse Number:** 3
- **Full Verse:** عَفَتِ الدِّيَار مَحَلُّهَا فَمُقَامُهَا...
- **Explanation:** [Pure Al-Zawzani commentary]

### 2️⃣ Poet Information

**Examples:**
- `Who is Imru' al-Qais?` → Full biography + why he wrote "Qifa nabki"
- `The Warrior Poet` → Information about Antarah ibn Shaddad
- `Poet of Wisdom` → Information about Zuhayr

### 3️⃣ General Information

**Examples:**
- `What are the Mu'allaqat?` → Definition + list of seven poets
- `How are you?` → Friendly response
- `Who are you?` → Bot introduction

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
│   └── main.py            # Chat endpoint, poet info, search
├── src/retrieval/          # Search Engine
│   ├── hybrid_search.py   # BM25 + FAISS hybrid search
│   ├── sparse_search.py   # BM25 keyword search
│   ├── dense_search.py    # FAISS semantic search
│   └── embeddings.py      # Embedding model
├── data/
│   ├── raw/               # Source DOCX
│   ├── processed/         # JSON database (687 verses)
│   └── vectordb/          # ChromaDB
├── tarjuman-ui/           # Next.js Frontend
│   └── src/app/page.tsx   # Main chat interface
├── run_api.py             # API runner
├── rebuild_index.py       # Rebuild indices
└── process_docx_v2.py    # Process DOCX
```

---

## 🔐 المتغيرات البيئية | Environment Variables

```bash
GROQ_API_KEY=gsk_...  # Groq API key (get from console.groq.com)
```

**ملاحظة:** احصل على مفتاح مجاني من [console.groq.com](https://console.groq.com/)

**Note:** Get a free key from [console.groq.com](https://console.groq.com/)

---

## 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health check |
| POST | `/chat` | **New!** Intelligent chat (poetry + general questions) |
| POST | `/search` | Search for verses (legacy) |
| GET | `/poets` | List of poets with stats |
| GET | `/examples` | Example verses from Mu'allaqat |

**API Documentation:** http://localhost:8000/docs

<div dir="rtl">

### الفرق بين `/chat` و `/search`

- **`/chat`**: نقطة النهاية الجديدة الموحدة - تتعامل مع الأبيات الشعرية والأسئلة العامة
  - تكتشف الأسئلة العامة تلقائياً (معلومات الشعراء، المعلقات، التحيات)
  - تبحث عن الأبيات الشعرية في قاعدة البيانات
  - ترد بشكل ذكي عند عدم العثور على نتائج

- **`/search`**: نقطة النهاية القديمة - للبحث الشعري فقط

</div>

### Difference between `/chat` and `/search`

- **`/chat`**: New unified endpoint - handles both poetry and general questions
  - Automatically detects general questions (poet info, Mu'allaqat info, greetings)
  - Searches for poetry verses in database
  - Intelligently responds when no results found

- **`/search`**: Legacy endpoint - poetry search only

---

## 🎯 أمثلة للاختبار | Test Examples

<div dir="rtl">

### 📖 جرّب هذه الأبيات الشعرية:

1. `قِفا نبك من ذِكرى حبيبٍ ومنزل` - امرؤ القيس
2. `لخولة أطلال ببرقة ثهمد` - طرفة بن العبد
3. `أمن أم أوفى دمنة لم تكلم` - زهير بن أبي سلمى
4. `عفت الديار محلها فمقامها` - لبيد بن ربيعة
5. `ألا هبي بصحنك فاصبحينا` - عمرو بن كلثوم
6. `هل غادر الشعراء من متردم` - عنترة بن شداد
7. `آذنتنا ببينها أسماء` - الحارث بن حلزة

### 👤 جرّب السؤال عن الشعراء:

1. `من هو امرؤ القيس؟`
2. `الفارس الشاعر` (عنترة)
3. `شاعر الحكمة` (زهير)
4. `اخبرني عن لبيد`

### 📚 جرّب الأسئلة العامة:

1. `ما هي المعلقات؟`
2. `من أنت؟`
3. `كيف حالك؟`

</div>

### 📖 Try these poetry verses:

1. `قِفا نبك من ذِكرى حبيبٍ ومنزل` - Imru' al-Qais
2. `لخولة أطلال ببرقة ثهمد` - Tarafa
3. `أمن أم أوفى دمنة لم تكلم` - Zuhayr
4. `عفت الديار محلها فمقامها` - Labid
5. `ألا هبي بصحنك فاصبحينا` - Amr ibn Kulthum
6. `هل غادر الشعراء من متردم` - Antarah
7. `آذنتنا ببينها أسماء` - Al-Harith

### 👤 Try asking about poets:

1. `Who is Imru' al-Qais?`
2. `The Warrior Poet` (Antarah)
3. `Poet of Wisdom` (Zuhayr)
4. `Tell me about Labid`

### 📚 Try general questions:

1. `What are the Mu'allaqat?`
2. `Who are you?`
3. `How are you?`

---

<div dir="rtl" align="center">

**⭐ إذا أعجبك المشروع، لا تنسى إعطاءه Star! ⭐**

</div>

<div align="center">

**⭐ If you like this project, don't forget to give it a Star! ⭐**

</div>
