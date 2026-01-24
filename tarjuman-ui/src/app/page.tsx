"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, User, BookOpen, 
  Quote, Sparkles, 
  Compass, History,
  Feather, Layers, Hash, Send, Star
} from 'lucide-react';

// Design Tokens
const COLORS = {
  bg: '#fffef8',
  gold: '#d4af37',
  goldDark: '#b8860b',
  text: '#2c1810',
  textLight: '#8b7355',
  border: '#e6e9ef',
  cardBg: '#ffffff',
  botBubble: '#f8f6f1',
};

const EXAMPLES = [
  { text: "قفا نبك من ذكرى حبيب ومنزل", short: "قفا نبك..." },
  { text: "هل غادر الشعراء من متردم", short: "هل غادر الشعراء..." },
  { text: "أمن أم أوفى دمنة لم تكلم", short: "أمن أم أوفى..." },
  { text: "عفت الديار محلها فمقامها", short: "عفت الديار..." },
  { text: "ألا هبي بصحنك فاصبحينا", short: "ألا هبي..." },
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
  text: string;
  isWelcome?: boolean;
  result?: SearchResult;
}

// Real API Adapter
const searchAPI = async (query: string): Promise<{ result: SearchResult | null; error: string | null }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      return { result: null, error: errorData.detail || 'حدث خطأ في البحث' };
    }
    
    const data = await response.json();
    if (data.results && data.results.length > 0) {
      return { result: data.results[0], error: null };
    }
    return { result: null, error: 'لم يتم العثور على نتائج' };
  } catch {
    return { result: null, error: 'تأكد من تشغيل الـ API' };
  }
};

// Result Card Component
const ResultCard = ({ data }: { data: SearchResult }) => {
  return (
    <div className="bg-white border border-[#d4af37]/20 rounded-2xl overflow-hidden shadow-lg">
      <div className="p-6 lg:p-8 space-y-6">
        {/* Verse Display */}
        <div className="relative text-center py-6 px-4">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-2">
            <div className="w-12 h-1 bg-gradient-to-r from-transparent via-[#d4af37] to-transparent"></div>
          </div>
          <Quote className="absolute top-4 right-4 text-[#d4af37]/10 w-12 h-12 rotate-180" />
          <p className="font-amiri text-2xl lg:text-3xl leading-loose text-[#2c1810] relative z-10">
            {data.verse_text.split('...').map((part, i) => (
              <span key={i} className={i === 1 ? 'block mt-3' : ''}>{part.trim()}</span>
            ))}
          </p>
          <Quote className="absolute bottom-4 left-4 text-[#d4af37]/10 w-12 h-12" />
        </div>

        {/* Metadata */}
        <div className="flex flex-wrap justify-center gap-3 py-4 border-y border-[#d4af37]/10">
          <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#d4af37]/5 to-transparent rounded-full">
            <User size={14} className="text-[#d4af37]" />
            <span className="text-sm font-medium">{data.poet_name}</span>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#d4af37]/5 to-transparent rounded-full">
            <BookOpen size={14} className="text-[#d4af37]" />
            <span className="text-sm font-medium">{data.poem_name}</span>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#d4af37]/5 to-transparent rounded-full">
            <Hash size={14} className="text-[#d4af37]" />
            <span className="text-sm font-medium">البيت {data.verse_number}</span>
          </div>
        </div>

        {/* Explanation */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-[#d4af37]">
            <Sparkles size={16} />
            <span className="text-sm font-bold">الشرح</span>
          </div>
          <div className="bg-gradient-to-br from-[#fdfbf7] to-[#f8f6f1] rounded-xl p-5 border border-[#d4af37]/10">
            <p className="text-lg leading-relaxed text-[#2c1810]/85 font-amiri text-justify">
              {data.explanation}
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gradient-to-r from-[#f8f6f1] to-[#fdfbf7] px-6 py-3 flex justify-between items-center text-xs text-[#8b7355]">
        <div className="flex items-center gap-2">
          <Layers size={12} />
          <span>{data.source_title}</span>
        </div>
        <div className="flex items-center gap-1">
          <Star size={12} className="text-[#d4af37]" />
          <span>دقة {Math.round(data.score * 100)}%</span>
        </div>
      </div>
    </div>
  );
};

// Hero Section (Welcome Screen)
const HeroSection = ({ onExampleClick }: { onExampleClick: (text: string) => void }) => {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
      {/* Logo */}
      <div className="mb-8">
        <div className="w-24 h-24 mx-auto bg-gradient-to-br from-[#d4af37] to-[#b8860b] rounded-3xl flex items-center justify-center shadow-xl shadow-[#d4af37]/20 mb-6">
          <Feather size={48} className="text-white" />
        </div>
        <h1 className="text-5xl font-bold text-[#2c1810] mb-3 font-amiri">ترجمان</h1>
        <p className="text-xl text-[#8b7355]">مساعدك الذكي لشرح الأبيات الشعرية</p>
      </div>

      {/* Decorative Line */}
      <div className="flex items-center gap-4 mb-8">
        <div className="w-16 h-px bg-gradient-to-r from-transparent to-[#d4af37]/50"></div>
        <span className="text-[#d4af37] text-2xl">✦</span>
        <div className="w-16 h-px bg-gradient-to-l from-transparent to-[#d4af37]/50"></div>
      </div>

      {/* Description */}
      <p className="text-lg text-[#8b7355] max-w-lg mb-10 leading-relaxed">
        اكتب بيتاً شعرياً من المعلقات السبع وسأقدم لك شرحاً وافياً من أمهات كتب الشروح
      </p>

      {/* Example Chips */}
      <div className="space-y-4">
        <p className="text-sm text-[#8b7355] font-medium">جرّب أحد هذه الأبيات:</p>
        <div className="flex flex-wrap justify-center gap-3 max-w-2xl">
          {EXAMPLES.map((ex, i) => (
            <button 
              key={i}
              onClick={() => onExampleClick(ex.text)}
              className="px-5 py-3 bg-white border-2 border-[#d4af37]/20 rounded-xl text-sm hover:border-[#d4af37] hover:bg-[#d4af37]/5 transition-all duration-300 group"
            >
              <span className="text-[#2c1810] group-hover:text-[#d4af37]">{ex.short}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

// Main App Component
export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (text?: string) => {
    const queryText = text || input;
    if (!queryText.trim()) return;

    if (!hasStarted) setHasStarted(true);

    const userMsg: Message = { id: Date.now(), role: 'user', text: queryText };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    const { result, error } = await searchAPI(queryText);
    
    const botMsg: Message = { 
      id: Date.now() + 1, 
      role: 'bot', 
      text: error ? `⚠️ ${error}` : 'وجدت لك هذا البيت:',
      result: result || undefined
    };
    
    setMessages(prev => [...prev, botMsg]);
    setLoading(false);
  };

  return (
    <div dir="rtl" className="h-screen flex flex-col" style={{ backgroundColor: COLORS.bg, color: COLORS.text }}>
      {/* Subtle Pattern */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.02]" 
           style={{ backgroundImage: `url('https://www.transparenttextures.com/patterns/cream-paper.png')` }}></div>

      {/* Header */}
      <header className="z-40 bg-white/90 backdrop-blur-lg border-b border-[#d4af37]/10 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-[#d4af37] to-[#b8860b] rounded-xl flex items-center justify-center shadow-lg shadow-[#d4af37]/20">
            <Feather size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[#2c1810]">ترجمان</h1>
            <p className="text-[10px] text-[#8b7355] tracking-wider">مساعد الشعر الذكي</p>
          </div>
        </div>
        
        {hasStarted && (
          <button 
            onClick={() => { setMessages([]); setHasStarted(false); }}
            className="text-sm text-[#8b7355] hover:text-[#d4af37] transition-colors"
          >
            محادثة جديدة
          </button>
        )}
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat/Hero Area */}
        <main className="flex-1 flex flex-col relative overflow-hidden">
          {!hasStarted ? (
            <HeroSection onExampleClick={handleSend} />
          ) : (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 lg:p-8 space-y-6">
                <div className="max-w-3xl mx-auto space-y-6">
                  {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-start' : 'justify-end'}`}>
                      <div className="max-w-[90%] space-y-3">
                        {/* Avatar & Name */}
                        <div className={`flex items-center gap-2 ${msg.role === 'user' ? '' : 'flex-row-reverse'}`}>
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            msg.role === 'user' 
                              ? 'bg-gradient-to-br from-[#d4af37] to-[#b8860b] text-white' 
                              : 'bg-[#f8f6f1] text-[#8b7355] border border-[#d4af37]/20'
                          }`}>
                            {msg.role === 'user' ? <User size={14} /> : <Compass size={14} />}
                          </div>
                          <span className="text-xs font-medium text-[#8b7355]">
                            {msg.role === 'user' ? 'أنت' : 'ترجمان'}
                          </span>
                        </div>

                        {/* Message Bubble */}
                        <div className={`p-4 rounded-2xl ${
                          msg.role === 'user' 
                            ? 'bg-white border border-[#e6e9ef] shadow-sm' 
                            : 'bg-[#f8f6f1] border border-[#d4af37]/10'
                        }`}>
                          <p className="text-base leading-relaxed">{msg.text}</p>
                        </div>

                        {/* Result Card */}
                        {msg.result && (
                          <div className="mt-4">
                            <ResultCard data={msg.result} />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  
                  {/* Loading */}
                  {loading && (
                    <div className="flex justify-end">
                      <div className="bg-[#f8f6f1] p-4 rounded-2xl border border-[#d4af37]/10 flex items-center gap-3">
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-[#d4af37] rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-[#d4af37] rounded-full animate-bounce" style={{ animationDelay: '-0.15s' }}></div>
                          <div className="w-2 h-2 bg-[#d4af37] rounded-full animate-bounce" style={{ animationDelay: '-0.3s' }}></div>
                        </div>
                        <span className="text-sm text-[#8b7355]">جاري البحث...</span>
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>
              </div>
            </>
          )}

          {/* Input */}
          <div className="p-4 lg:p-6 bg-white/80 backdrop-blur-lg border-t border-[#d4af37]/10">
            <div className="max-w-3xl mx-auto">
              <div className="relative">
                <input 
                  type="text" 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="اكتب بيتاً شعرياً..."
                  className="w-full bg-[#fdfbf7] border-2 border-[#d4af37]/20 rounded-2xl py-4 pr-14 pl-16 text-lg outline-none focus:border-[#d4af37]/50 focus:bg-white transition-all placeholder:text-[#8b7355]/50"
                />
                <Search size={22} className="absolute right-5 top-1/2 -translate-y-1/2 text-[#8b7355]/50" />
                <button 
                  onClick={() => handleSend()}
                  disabled={!input.trim() || loading}
                  className={`absolute left-3 top-1/2 -translate-y-1/2 w-11 h-11 rounded-xl flex items-center justify-center transition-all ${
                    input.trim() && !loading 
                      ? 'bg-gradient-to-br from-[#d4af37] to-[#b8860b] text-white shadow-lg shadow-[#d4af37]/30 hover:scale-105' 
                      : 'bg-[#e6e9ef] text-[#8b7355]/50 cursor-not-allowed'
                  }`}
                >
                  <Send size={20} />
                </button>
              </div>
              <p className="text-center text-xs text-[#8b7355]/60 mt-3">
                المعلقات السبع • شرح الزوزني
              </p>
            </div>
        </div>
      </main>

        {/* Sidebar - Only when chatting */}
        {hasStarted && (
          <aside className="hidden lg:block w-72 bg-[#fdfbf7] border-l border-[#d4af37]/10 p-6">
            <div className="space-y-6">
              {/* Quick Examples */}
              <div>
                <p className="text-sm font-bold text-[#2c1810] mb-4 flex items-center gap-2">
                  <Sparkles size={14} className="text-[#d4af37]" />
                  أبيات للتجربة
                </p>
                <div className="space-y-2">
                  {EXAMPLES.slice(0, 4).map((ex, i) => (
                    <button 
                      key={i}
                      onClick={() => handleSend(ex.text)}
                      className="w-full text-right p-3 text-sm bg-white hover:bg-[#d4af37]/5 border border-[#d4af37]/10 rounded-xl transition-all truncate"
                    >
                      {ex.short}
                    </button>
                  ))}
                </div>
              </div>

              {/* History */}
              {messages.filter(m => m.role === 'user').length > 0 && (
                <div>
                  <p className="text-sm font-bold text-[#2c1810] mb-4 flex items-center gap-2">
                    <History size={14} className="text-[#d4af37]" />
                    سجل البحث
                  </p>
                  <div className="space-y-2">
                    {messages.filter(m => m.role === 'user').slice(-4).map((m, i) => (
                      <button 
                        key={i}
                        onClick={() => handleSend(m.text)}
                        className="w-full text-right p-3 text-xs bg-white hover:bg-[#d4af37]/5 border border-[#d4af37]/10 rounded-xl transition-all truncate"
                      >
                        {m.text}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="absolute bottom-6 left-6 right-6 text-center">
              <div className="flex justify-center gap-2 mb-2 text-[#d4af37]/40">
                <span>✦</span>
                <span>⁂</span>
                <span>✦</span>
              </div>
              <p className="text-[10px] text-[#8b7355]/60">ترجمان © {new Date().getFullYear()}</p>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
