"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, User, BookOpen, 
  Quote, Sparkles, 
  Compass, History,
  Feather, Layers, Hash, Send, Star,
  Menu, X, MessageSquare, Info, ArrowLeft
} from 'lucide-react';

// Design Tokens - Fortress & Heritage Palette
const COLORS = {
  bg: '#fffef8',
  gold: '#d4af37',
  goldLight: '#f4ece1',
  text: '#2c1810',
  textLight: '#8b7355',
  border: '#e6e9ef',
  cardBg: '#ffffff',
  botBubble: '#f8f6f1',
  userBubble: '#ffffff',
};

const EXAMPLES = [
  { text: "قفا نبك من ذكرى حبيب ومنزل", short: "قفا نبك..." },
  { text: "هل غادر الشعراء من متردم", short: "هل غادر الشعراء..." },
  { text: "من هو امرؤ القيس؟", short: "من هو امرؤ القيس؟" },
  { text: "ما هي المعلقات؟", short: "ما هي المعلقات؟" },
];

// API Configuration
const API_BASE_URL = "http://localhost:8000";

// Types
interface SearchResult {
  chunk_id: string;
  verse_text: string;
  poet_name: string;
  poem_name: string;
  verse_number: number;
  explanation: string;
  source_title: string;
  score: number;
}

interface Message {
  id: number;
  role: 'user' | 'bot';
  type: 'poetry' | 'chat';
  text: string;
  data?: SearchResult;
}

// API Adapter
const chatAPI = async (query: string): Promise<{ type: 'poetry' | 'chat'; data?: SearchResult; text?: string; error?: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    
    if (!response.ok) {
      // محاولة قراءة JSON من الخطأ
      let errorMessage = 'حدث خطأ في الاتصال بالخادم';
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        // إذا لم يكن JSON، استخدم رسالة الخطأ الافتراضية
        if (response.status === 404) {
          errorMessage = 'الخادم غير متاح. تأكد من تشغيل الـ API على http://localhost:8000';
        } else if (response.status === 500) {
          errorMessage = 'حدث خطأ في الخادم. يرجى المحاولة لاحقاً';
        }
      }
      return { type: 'chat', text: errorMessage, error: errorMessage };
    }
    
    const data = await response.json();
    
    if (data.type === 'poetry' && data.result) {
      return { type: 'poetry', data: data.result };
    } else if (data.type === 'chat' && data.response) {
      return { type: 'chat', text: data.response };
    }
    
    return { type: 'chat', text: 'لم أتمكن من فهم استفسارك. هل تريد البحث عن بيت شعري؟' };
  } catch (error: any) {
    // معالجة أخطاء الشبكة
    const errorMessage = error.message?.includes('fetch') 
      ? 'تأكد من تشغيل الـ API على http://localhost:8000'
      : 'حدث خطأ في الاتصال. تأكد من تشغيل الـ API';
    return { type: 'chat', text: errorMessage, error: errorMessage };
  }
};

// Verse Card Component
const VerseCard = ({ data }: { data: SearchResult }) => (
  <div className="bg-white border border-[#d4af37]/20 rounded-2xl overflow-hidden shadow-xl animate-in fade-in slide-in-from-bottom-4 duration-500">
    <div className="p-6 lg:p-8 space-y-6">
      <div className="relative text-center py-6 px-4">
        <Quote className="absolute top-0 right-0 text-[#d4af37]/10 w-12 h-12 rotate-180" />
        <p className="font-amiri text-2xl lg:text-3xl leading-loose text-[#2c1810] relative z-10">
          {data.verse_text.split('...').map((part, i) => (
            <span key={i} className={i === 1 ? 'block mt-2' : ''}>{part.trim()}</span>
          ))}
        </p>
        <Quote className="absolute bottom-0 left-0 text-[#d4af37]/10 w-12 h-12" />
      </div>

      <div className="flex flex-wrap justify-center gap-3 py-4 border-y border-[#d4af37]/10">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-[#fdfbf7] rounded-full text-xs font-bold border border-[#d4af37]/10">
          <User size={14} className="text-[#d4af37]" />
          <span>الشاعر: {data.poet_name}</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-[#fdfbf7] rounded-full text-xs font-bold border border-[#d4af37]/10">
          <BookOpen size={14} className="text-[#d4af37]" />
          <span>{data.poem_name}</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-[#fdfbf7] rounded-full text-xs font-bold border border-[#d4af37]/10">
          <Hash size={14} className="text-[#d4af37]" />
          <span>البيت {data.verse_number}</span>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-2 text-[#d4af37] font-bold text-sm">
          <Sparkles size={16} />
          <span>الشرح والبيان</span>
        </div>
        <p className="text-lg leading-relaxed text-[#2c1810]/90 text-justify font-amiri bg-[#fdfbf7] p-5 rounded-xl border border-[#d4af37]/5">
          {data.explanation}
        </p>
      </div>
    </div>
    <div className="bg-[#f8f6f1] px-6 py-3 flex justify-between items-center text-[10px] text-[#8b7355] border-t border-[#d4af37]/10">
      <span>المصدر: {data.source_title}</span>
      <span>دقة التحليل: {Math.round(data.score * 100)}%</span>
    </div>
  </div>
);

// Main App Component
export default function Home() {
  const [showLanding, setShowLanding] = useState(true);
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, role: 'bot', type: 'chat', text: 'أنا ترجمان، مساعدك المتخصص في شرح الشعر العربي القديم والمعلقات. أنا هنا لمساعدتك في فهم الأبيات الشعرية من خلال شروحات موثوقة من أمهات الكتب.\n\nجرّب الأمثلة أدناه' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (text?: string) => {
    const query = text || input;
    if (!query.trim()) return;

    const userMsg: Message = { id: Date.now(), role: 'user', type: 'chat', text: query };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    const response = await chatAPI(query);
    
    const botMsg: Message = { 
      id: Date.now() + 1, 
      role: 'bot', 
      type: response.type,
      text: response.type === 'chat' ? (response.text || '') : 'وجدت لك هذا البيت في الدواوين:',
      data: response.type === 'poetry' ? response.data : undefined
    };
    
    setMessages(prev => [...prev, botMsg]);
    setLoading(false);
  };

  // Landing Page
  if (showLanding) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ fontFamily: 'Amiri, serif', background: 'linear-gradient(135deg, #fdfbf7 0%, #f8f6f1 100%)' }}>
        <div className="max-w-4xl mx-auto px-6 py-12 text-center">
          <div className="mb-8 inline-block">
            <div style={{ width: '96px', height: '96px', background: 'linear-gradient(135deg, #d4af37 0%, #b8860b 100%)', borderRadius: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 20px 50px rgba(212, 175, 55, 0.3)', margin: '0 auto 1rem' }}>
              <Feather size={48} style={{ color: 'white' }} />
            </div>
            <h1 style={{ fontSize: '3rem', fontWeight: 'bold', color: '#2d2416', marginBottom: '1rem' }}>ترجمان</h1>
          </div>

          <div className="mb-12 max-w-2xl mx-auto">
            <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#2d2416', marginBottom: '1rem' }}>
              رفيقك الذكي في رحاب الشعر العربي الفصيح
            </h2>
            <p style={{ fontSize: '1.125rem', color: '#5c5042', lineHeight: '1.75', marginBottom: '1.5rem' }}>
              مساعد متخصص في تحليل وشرح الشعر العربي القديم باستخدام تقنيات الذكاء الاصطناعي، 
              مع الاستناد إلى أمهات الكتب التراثية كشرح المعلقات السبع للزوزني.
            </p>
          </div>

          <button
            onClick={() => setShowLanding(false)}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.75rem', background: 'linear-gradient(135deg, #d4af37 0%, #b8860b 100%)', color: 'white', padding: '1rem 2rem', borderRadius: '1rem', fontWeight: 'bold', fontSize: '1.125rem', boxShadow: '0 20px 50px rgba(212, 175, 55, 0.4)', cursor: 'pointer', border: 'none', transition: 'all 0.3s' }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            <span>ابدأ الآن</span>
            <ArrowLeft size={24} />
          </button>

          <div style={{ marginTop: '3rem', fontSize: '0.875rem', color: '#8b7355' }}>
            <p>المعلقات السبع • امرؤ القيس • طرفة • زهير • لبيد • عمرو بن كلثوم • عنترة • الحارث</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div dir="rtl" className="h-screen flex flex-col font-sans" style={{ backgroundColor: COLORS.bg, color: COLORS.text }}>
      {/* Background Texture */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03]" 
           style={{ backgroundImage: `url('https://www.transparenttextures.com/patterns/cream-paper.png')` }}></div>

      {/* Header */}
      <header className="z-40 bg-white/80 backdrop-blur-md border-b border-[#d4af37]/10 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-4">
          <button onClick={() => setIsSidebarOpen(true)} className="lg:hidden p-2 hover:bg-black/5 rounded-full transition-colors">
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-[#d4af37] to-[#b8860b] rounded-xl flex items-center justify-center shadow-lg shadow-[#d4af37]/20">
              <Feather size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold leading-none tracking-tight">ترجمان</h1>
              <p className="text-[10px] text-[#8b7355] mt-1 uppercase font-bold tracking-widest">الفصيح — المساعد الذكي</p>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
           <div className="hidden md:flex items-center gap-1 text-[10px] text-[#8b7355] bg-[#f8f6f1] px-3 py-1 rounded-full border border-[#d4af37]/10">
             <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
             متصل بالدواوين
           </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden relative">
        {/* Sidebar - Fortress Style */}
        <aside className={`fixed inset-y-0 right-0 z-50 w-72 transform transition-transform duration-300 bg-[#fdfbf7] border-l border-[#d4af37]/10 lg:relative lg:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}`}>
          <div className="h-full flex flex-col p-6">
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <History size={18} className="text-[#d4af37]" />
                سجل المطارحات
              </h3>
              <button onClick={() => setIsSidebarOpen(false)} className="lg:hidden">
                <X size={20} />
              </button>
            </div>
            
            <div className="flex-1 space-y-6 overflow-y-auto">
              <section>
                <p className="text-[10px] font-bold text-[#8b7355] uppercase tracking-widest mb-4">أمثلة سريعة</p>
                <div className="space-y-2">
                  {EXAMPLES.map((ex, i) => (
                    <button 
                      key={i} 
                      onClick={() => { handleSend(ex.text); setIsSidebarOpen(false); }}
                      className="w-full text-right p-3 text-sm bg-white hover:bg-[#d4af37]/5 border border-[#d4af37]/10 rounded-xl transition-all truncate"
                    >
                      {ex.short}
                    </button>
                  ))}
                </div>
              </section>

              <section className="bg-[#795548] text-[#f4ece1] p-4 rounded-2xl relative overflow-hidden group">
                <Compass className="absolute -bottom-4 -left-4 w-20 h-20 opacity-10 group-hover:scale-110 transition-transform" />
                <h4 className="text-sm font-bold mb-2 flex items-center gap-2">
                  <Info size={14} /> عن ترجمان
                </h4>
                <p className="text-[10px] leading-relaxed opacity-80">
                  مساعد متخصص في تحليل الشعر الفصيح باستخدام تقنيات الذكاء الاصطناعي وربطها بأمهات الكتب التراثية.
                </p>
              </section>
            </div>
          </div>
        </aside>

        {/* Chat Window */}
        <main className="flex-1 flex flex-col relative overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4 lg:p-10 space-y-8 custom-scrollbar">
            <div className="max-w-3xl mx-auto space-y-8">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-start' : 'justify-end'}`}>
                  <div className={`max-w-[90%] md:max-w-[85%] space-y-3`}>
                    
                    {/* Message Bubble */}
                    <div className={`p-5 rounded-2xl shadow-sm border leading-relaxed text-lg ${
                      msg.role === 'user' 
                        ? 'bg-white border-gray-100' 
                        : 'bg-[#f8f6f1] border-[#d4af37]/10'
                    }`}>
                      {msg.text}
                    </div>

                    {/* Conditional Output: Verse Card */}
                    {msg.type === 'poetry' && msg.data && (
                      <VerseCard data={msg.data} />
                    )}

                    <div className={`flex items-center gap-2 px-1 text-[10px] font-bold text-[#8b7355] uppercase ${msg.role === 'user' ? 'justify-start' : 'justify-end flex-row-reverse'}`}>
                      {msg.role === 'user' ? <User size={12} /> : <Compass size={12} />}
                      <span>{msg.role === 'user' ? 'أنت' : 'ترجمان'}</span>
                    </div>
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="flex justify-end">
                  <div className="bg-[#f8f6f1] p-4 rounded-2xl border border-[#d4af37]/10 flex items-center gap-3">
                    <div className="flex gap-1">
                      <div className="w-1.5 h-1.5 bg-[#d4af37] rounded-full animate-bounce"></div>
                      <div className="w-1.5 h-1.5 bg-[#d4af37] rounded-full animate-bounce [animation-delay:-.3s]"></div>
                      <div className="w-1.5 h-1.5 bg-[#d4af37] rounded-full animate-bounce [animation-delay:-.5s]"></div>
                    </div>
                    <span className="text-xs text-[#8b7355] font-bold">جاري استحضار المعنى...</span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          </div>

          {/* Chat Input */}
          <div className="p-4 lg:p-8 bg-white/80 backdrop-blur-md border-t border-[#d4af37]/10">
            <div className="max-w-3xl mx-auto">
              <div className="relative flex items-center group">
                <input 
                  type="text" 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="ألقِ بيت الشعر هنا، أو اسألني عما بدا لك..."
                  className="w-full bg-[#fdfbf7] border-2 border-[#d4af37]/10 rounded-2xl py-5 pr-14 pl-16 text-lg outline-none focus:border-[#d4af37]/40 focus:bg-white transition-all shadow-inner placeholder:text-[#8b7355]/40"
                />
                <div className="absolute right-5 top-1/2 -translate-y-1/2 text-[#d4af37]/40 group-focus-within:text-[#d4af37]">
                  <MessageSquare size={22} />
                </div>
                <button 
                  onClick={() => handleSend()}
                  disabled={!input.trim() || loading}
                  className={`absolute left-3 top-1/2 -translate-y-1/2 w-11 h-11 rounded-xl flex items-center justify-center transition-all ${
                    input.trim() && !loading 
                      ? 'bg-gradient-to-br from-[#d4af37] to-[#b8860b] text-white shadow-lg shadow-[#d4af37]/30 hover:scale-105' 
                      : 'bg-[#e6e9ef] text-[#8b7355]/40'
                  }`}
                >
                  <Send size={20} />
                </button>
              </div>
              <p className="text-center text-[9px] text-[#8b7355] mt-4 uppercase tracking-[0.2em] font-bold opacity-50">
                 The Bastion of Arabic Literature • Tarjuman AI ⁂
              </p>
            </div>
        </div>
      </main>
      </div>

      <style dangerouslySetInnerHTML={{ __html: `
        @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap');
        
        .font-amiri { font-family: 'Amiri', serif; }

        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #d4af3733; border-radius: 10px; }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-in { animation: fadeIn 0.4s ease-out forwards; }
      ` }} />
    </div>
  );
}
