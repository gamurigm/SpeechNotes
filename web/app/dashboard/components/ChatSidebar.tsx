'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, Sparkles, Bot, User, Loader2, FileText, Maximize2, Minimize2, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useBackground } from '../../providers';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

interface ChatSidebarProps {
    activeDocId?: string;    // MongoDB ObjectId - preferred
    activeDocName?: string;  // Display name (filename)
    activeFile?: string;     // DEPRECATED: kept for backwards compat
    isExpanded?: boolean;
    isFormatted?: boolean;
    onToggleExpand?: () => void;
    onClose?: () => void;
}

export function ChatSidebar({ activeDocId, activeDocName, activeFile, isExpanded, isFormatted, onToggleExpand, onClose }: ChatSidebarProps) {
    const { theme, themeType } = useBackground();
    const isLight = themeType === 'light';
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [currentDoc, setCurrentDoc] = useState<string | null>(null);
    const [useThinking, setUseThinking] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Track document changes
    useEffect(() => {
        const newDocId = activeDocId || activeFile || null;
        if (newDocId !== currentDoc) {
            setCurrentDoc(newDocId);
        }
    }, [activeDocId, activeFile, currentDoc]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({
                top: scrollRef.current.scrollHeight,
                behavior: 'smooth'
            });
        }
    }, [messages]);

    const displayName = activeDocName
        ? activeDocName.replace('transcription_', '').replace('.md', '').replace('_formatted', '')
        : activeFile
            ? activeFile.replace('transcription_', '').replace('.md', '').replace('_formatted', '')
            : null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input.trim(),
            timestamp: new Date()
        };

        const assistantMessageId = (Date.now() + 1).toString();
        const initialAssistantMessage: Message = {
            id: assistantMessageId,
            role: 'assistant',
            content: '',
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage, initialAssistantMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: [...messages, userMessage].map(m => ({
                        role: m.role,
                        content: m.content
                    })),
                    doc_id: activeDocId,
                    active_file: activeFile,
                    thinking: useThinking
                })
            });

            if (!response.ok) throw new Error('Chat failed');
            if (!response.body) throw new Error('No response body');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let done = false;

            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;
                const chunkValue = decoder.decode(value, { stream: !done });

                const lines = chunkValue.split('\n\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6);
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.content) {
                                setMessages(prev => prev.map(msg =>
                                    msg.id === assistantMessageId
                                        ? { ...msg, content: msg.content + data.content }
                                        : msg
                                ));
                            }
                            if (data.error) throw new Error(data.error);
                        } catch (e) { }
                    }
                }
            }
        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => prev.map(msg =>
                msg.id === assistantMessageId
                    ? { ...msg, content: msg.content + '\n\nError: No se pudo obtener respuesta.' }
                    : msg
            ));
        } finally {
            setIsLoading(false);
            inputRef.current?.focus();
        }
    };

    return (
        <div className={`h-full flex flex-col relative overflow-hidden rounded-[2.5rem] shadow-[0_30px_100px_-20px_rgba(0,0,0,0.4)] transition-all duration-700 glass border-white/10 border`}>

            {/* Premium background effects */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className={`absolute -top-[20%] -right-[10%] w-[60%] h-[60%] ${isLight ? 'bg-violet-400/10' : 'bg-violet-600/10'} rounded-full blur-[120px] animate-pulse`} />
                <div className={`absolute top-[20%] -left-[10%] w-[50%] h-[50%] ${isLight ? 'bg-indigo-400/10' : 'bg-indigo-600/10'} rounded-full blur-[100px]`} />
                <div className={`absolute bottom-0 inset-x-0 h-px ${isLight ? 'bg-black/5' : 'bg-white/10'}`} />
            </div>

            {/* Header */}
            <div className="relative z-10 px-8 pt-8 pb-4">
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                        <div className="relative">
                            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                                <MessageCircle size={24} className="text-white" />
                            </div>
                            <div className={`absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-4 ${isLight ? 'border-white' : 'border-slate-950'} shadow-sm`} />
                        </div>
                        <div>
                            <h3 className={`text-[19px] font-bold tracking-tight flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
                                Intelligence Hub
                                <Sparkles size={14} className={isLight ? 'text-indigo-600' : 'text-violet-400'} />
                            </h3>
                            <div className="flex items-center gap-2 mt-0.5">
                                <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500/80" />
                                <span className={`text-[11px] uppercase tracking-widest font-black ${isLight ? 'text-slate-500' : 'text-slate-300'}`}>Active Context</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        {/* Thinking Pill Toggle */}
                        <button
                            onClick={() => setUseThinking(!useThinking)}
                            className={`flex items-center gap-1.5 px-3 py-1 rounded-full border transition-all duration-500 ${useThinking
                                ? (isLight ? 'bg-violet-100 border-violet-200 text-violet-700' : 'bg-[var(--theme-neon-color)]/20 border-[var(--theme-neon-color)]/40 text-[var(--theme-neon-color)]')
                                : (isLight ? 'bg-slate-100 border-slate-200 text-slate-500' : 'bg-white/5 border-white/10 text-slate-400')
                                } hover:scale-105 active:scale-95 shadow-sm`}
                            title={useThinking ? "Desactivar análisis profundo (Más rápido)" : "Activar análisis profundo (Más inteligente)"}
                        >
                            <Sparkles
                                size={12}
                                className={useThinking ? 'animate-pulse' : 'text-slate-400'}
                                style={{ color: useThinking ? 'var(--theme-neon-color)' : undefined }}
                            />
                            <span className="text-[11px] font-bold uppercase tracking-wider">{useThinking ? 'Thinking' : 'Fast'}</span>
                        </button>

                        <div className="w-px h-4 bg-white/5 mx-1" />

                        {/* Expand Toggle */}
                        <button
                            onClick={onToggleExpand}
                            className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-all duration-300 border border-white/5"
                            title={isExpanded ? "Contraer" : "Expandir"}
                        >
                            {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                        </button>

                        {/* Subtle Close Button */}
                        <button
                            onClick={onClose}
                            className={`p-2.5 rounded-xl transition-all duration-300 border ${isLight
                                ? 'bg-black/5 hover:bg-black/10 text-slate-600 hover:text-rose-600 border-black/5'
                                : 'bg-white/5 hover:bg-white/10 text-slate-300 hover:text-rose-400 border-white/5'
                                }`}
                        >
                            <X size={16} />
                        </button>
                    </div>
                </div>

                {/* Context Badge */}
                <div className="mt-4 flex items-center gap-3 py-2 px-4 rounded-xl bg-white/[0.03] border border-white/[0.05] backdrop-blur-md">
                    <FileText size={16} className={activeDocId ? "text-violet-400" : "text-slate-600"} />
                    <div className="flex-1 overflow-hidden">
                        <p className={`text-[15px] font-bold truncate ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>
                            {displayName || 'Selecciona un documento'}
                        </p>
                    </div>
                    {activeDocId && (
                        <div className={`px-1.5 py-0.5 rounded-md ${isFormatted ? 'bg-violet-500/10 border-violet-500/20' : 'bg-emerald-500/5 border-emerald-500/10'}`}>
                            <span className={`text-[12px] font-black uppercase tracking-tighter ${isFormatted ? 'text-violet-400' : 'text-emerald-500/80'}`}>
                                {isFormatted ? 'AI Formatted' : 'Verified'}
                            </span>
                        </div>
                    )}
                </div>
            </div>

            {/* Messages Area */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto px-6 py-4 space-y-6 scroll-smooth custom-scrollbar"
            >
                {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center px-10">
                        <div className="w-20 h-20 rounded-[2rem] bg-gradient-to-tr from-slate-900 to-slate-800 border border-white/5 flex items-center justify-center mb-6 shadow-2xl relative group-hover:scale-105 transition-transform duration-500">
                            <Bot size={40} className="text-violet-400/80" />
                            <div className="absolute inset-0 rounded-[2rem] bg-violet-500/10 blur-2xl animate-pulse" />
                        </div>
                        <h4 className={`font-bold text-[21px] mb-2 title-semi-neon`}>Asistente de Clase</h4>
                        <p className={`text-[15px] leading-relaxed max-w-[250px] ${isLight ? 'text-slate-600' : 'text-slate-300'} font-medium text-glow-contrast`}>
                            {activeDocId
                                ? "Estoy listo para responder preguntas sobre la clase seleccionada."
                                : "Selecciona una transcripción para comenzar el análisis inteligente."
                            }
                        </p>
                    </div>
                ) : (
                    messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''} group/msg`}
                        >
                            <div className={`w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg ${msg.role === 'user'
                                ? 'bg-gradient-to-br from-indigo-500 to-blue-600'
                                : 'bg-gradient-to-br from-violet-500 to-fuchsia-600'
                                }`}>
                                {msg.role === 'user' ? <User size={18} className="text-white" /> : <Bot size={18} className="text-white" />}
                            </div>

                            <div className={`max-w-[90%] relative ${msg.role === 'user' ? 'text-right' : ''}`}>
                                <div className={`px-5 py-4 rounded-[1.5rem] text-[15px] leading-relaxed ${msg.role === 'user'
                                    ? 'bg-violet-600/30 border border-violet-400/30 text-white'
                                    : 'glass text-[var(--foreground)]'
                                    } shadow-sm chat-markdown font-medium`}>

                                    {/* Handle [Analizando: ...] prefix */}
                                    {msg.content.includes('[Analizando:') && msg.role === 'assistant' && (
                                        <div className="mb-4 flex items-center gap-2 px-3 py-1.5 rounded-xl bg-violet-500/10 border border-violet-500/20 w-fit">
                                            <div className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
                                            <span className="text-[10px] font-black uppercase tracking-widest text-violet-400">Analizando Documento</span>
                                        </div>
                                    )}

                                    {(() => {
                                        const content = msg.content.replace(/\[Analizando:.*?\]/, '').trim();
                                        const thinkMatch = content.match(/<think>([\s\S]*?)(?:<\/think>|$)/);
                                        const hasThinking = !!thinkMatch;
                                        const thinkingContent = thinkMatch ? thinkMatch[1].trim() : '';
                                        const restContent = content.replace(/<think>[\s\S]*?(?:<\/think>|$)/, '').trim();

                                        return (
                                            <>
                                                {hasThinking && (
                                                    <div className="mb-4 p-4 rounded-xl bg-white/[0.03] border border-white/10 border-l-4 border-l-violet-500/50 italic text-[13px] text-[var(--foreground)]/60 leading-relaxed">
                                                        <div className="flex items-center gap-2 mb-2 opacity-60">
                                                            <Sparkles size={12} className="text-violet-400" />
                                                            <span className="text-[10px] font-black uppercase tracking-widest">Razonamiento Interno</span>
                                                        </div>
                                                        {thinkingContent}
                                                        {!content.includes('</think>') && <span className="animate-pulse ml-1 inline-block">...</span>}
                                                    </div>
                                                )}
                                                <ReactMarkdown
                                                    remarkPlugins={[remarkGfm]}
                                                    components={{
                                                        h1: ({ node, ...props }) => <h1 className={`text-2xl font-black mb-4 border-b ${isLight ? 'border-slate-300 text-slate-900' : 'border-white/10 text-white title-semi-neon'} pb-2`} {...props} />,
                                                        h2: ({ node, ...props }) => <h2 className={`text-xl font-bold mb-3 mt-6 ${isLight ? 'text-slate-900' : 'text-white title-semi-neon'}`} {...props} />,
                                                        h3: ({ node, ...props }) => <h3 className={`text-lg font-bold mb-3 mt-6 px-3 py-1 rounded-lg border-l-4 border-violet-500 shadow-sm ${isLight ? 'text-violet-950 bg-violet-100' : 'text-violet-200 bg-violet-500/10'}`} {...props} />,
                                                        p: ({ node, ...props }) => <p className={`mb-4 last:mb-0 leading-[1.8] ${isLight ? 'text-slate-900' : 'text-slate-200'} font-medium`} {...props} />,
                                                        ul: ({ node, ...props }) => <ul className="space-y-3 mb-4 mt-2" {...props} />,
                                                        ol: ({ node, ...props }) => <ol className="space-y-3 mb-4 mt-2 list-decimal list-inside" {...props} />,
                                                        li: ({ node, ...props }) => (
                                                            <li className="flex items-start gap-3">
                                                                <span className={`mt-2.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${isLight ? 'bg-violet-600 shadow-[0_0_5px_rgba(124,58,237,0.3)]' : 'bg-violet-400 shadow-[0_0_8px_rgba(139,92,246,0.8)]'}`} />
                                                                <span className={`flex-1 text-[15px] ${isLight ? 'text-slate-900' : 'text-slate-200'}`}>{props.children}</span>
                                                            </li>
                                                        ),
                                                        strong: ({ node, ...props }) => (
                                                            <strong className={`font-black ${isLight ? 'text-indigo-950 bg-indigo-100 underline decoration-indigo-200 decoration-1 underline-offset-2' : 'text-white text-glow-contrast bg-white/10'} px-1.5 py-0.5 rounded-md`} {...props} />
                                                        ),
                                                        blockquote: ({ node, ...props }) => (
                                                            <blockquote className={`my-6 p-5 rounded-2xl border-l-4 border-l-indigo-500 shadow-sm ${isLight ? 'bg-slate-100 border-slate-200 text-slate-700 italic' : 'bg-indigo-500/5 border-indigo-500/10 text-slate-400 italic shadow-inner'}`} {...props} />
                                                        ),
                                                        code: ({ node, ...props }) => <code className={`px-2 py-0.5 rounded-lg font-mono text-[0.85em] border ${isLight ? 'bg-slate-200 text-indigo-700 border-indigo-200' : 'bg-violet-500/10 text-violet-300 border-violet-500/20'}`} {...props} />,
                                                        hr: () => <hr className={`my-8 border-none h-px ${isLight ? 'bg-slate-300' : 'bg-gradient-to-r from-transparent via-white/10 to-transparent'}`} />,
                                                    }}
                                                >
                                                    {restContent}
                                                </ReactMarkdown>
                                            </>
                                        );
                                    })()}
                                </div>
                                <span className="block mt-1 text-[9px] font-bold uppercase text-slate-700 tracking-widest opacity-0 group-hover/msg:opacity-100 transition-opacity">
                                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            </div>
                        </div>
                    ))
                )}

                {isLoading && (
                    <div className="flex gap-4 animate-pulse">
                        <div className="w-10 h-10 rounded-2xl bg-slate-800 flex items-center justify-center">
                            <Bot size={18} className="text-slate-500" />
                        </div>
                        <div className="flex-1 py-4 px-5 rounded-3xl bg-white/[0.02] border border-white/[0.04] flex items-center gap-3">
                            <Loader2 size={16} className="text-violet-500 animate-spin" />
                            <span className={`text-[13px] font-black ${isLight ? 'text-slate-600' : 'text-slate-200'} uppercase tracking-widest text-glow-contrast`}>Generating context...</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Input Footer */}
            <div className="relative z-10 px-8 py-8">
                <form onSubmit={handleSubmit} className="flex gap-3 items-center">
                    <div className="flex-1 relative">
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={isLoading}
                            placeholder={activeDocId ? "Analizar documentos..." : "Esperando documento..."}
                            className="w-full h-14 pl-6 pr-14 glass rounded-[1.25rem] text-[15px] text-[var(--foreground)] placeholder:text-[var(--foreground)]/40 focus:outline-none focus:border-violet-500/50 focus:ring-4 focus:ring-violet-500/5 transition-all disabled:opacity-30 shadow-inner shadow-black/20"
                        />
                        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                            <Sparkles size={14} className={input ? "text-violet-400 animate-pulse" : "text-slate-700"} />
                        </div>
                    </div>
                    <button
                        type="submit"
                        disabled={!input.trim() || isLoading}
                        className="w-14 h-14 rounded-[1.25rem] bg-gradient-to-br from-violet-600 to-indigo-700 hover:from-violet-500 hover:to-indigo-600 disabled:from-slate-800 disabled:to-slate-900 text-white flex items-center justify-center transition-all duration-500 shadow-xl shadow-indigo-900/40 hover:scale-105 active:scale-95 disabled:scale-100 disabled:opacity-50"
                    >
                        {isLoading ? <Loader2 size={24} className="animate-spin" /> : <Send size={24} />}
                    </button>
                </form>
            </div>

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: rgba(139, 92, 246, 0.3);
                }

                :global(.chat-markdown) {
                    word-break: break-word;
                }
                :global(.chat-markdown p) {
                    margin-bottom: 0.75rem;
                }
                :global(.chat-markdown p:last-child) {
                    margin-bottom: 0;
                }
                :global(.chat-markdown ul), :global(.chat-markdown ol) {
                    margin-bottom: 0.75rem;
                    padding-left: 1.25rem;
                }
                :global(.chat-markdown li) {
                    margin-bottom: 0.25rem;
                }
                :global(.chat-markdown ul) {
                    list-style-type: disc;
                }
                :global(.chat-markdown ol) {
                    list-style-type: decimal;
                }
                :global(.chat-markdown code) {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 0.2rem 0.4rem;
                    border-radius: 0.375rem;
                    font-family: inherit;
                    font-size: 0.9em;
                }
                :global(.chat-markdown pre) {
                    background: rgba(0, 0, 0, 0.3);
                    padding: 1rem;
                    border-radius: 0.75rem;
                    margin-bottom: 0.75rem;
                    overflow-x: auto;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                }
                :global(.chat-markdown blockquote) {
                    border-left: 2px solid rgba(139, 92, 246, 0.5);
                    padding-left: 1rem;
                    color: rgba(255, 255, 255, 0.6);
                    font-style: italic;
                    margin-bottom: 0.75rem;
                }
                :global(.chat-markdown strong) {
                    color: #fff;
                    font-weight: 700;
                }
                :global(.chat-markdown a) {
                    color: #8b5cf6;
                    text-decoration: underline;
                }
            `}</style>
        </div>
    );
}
