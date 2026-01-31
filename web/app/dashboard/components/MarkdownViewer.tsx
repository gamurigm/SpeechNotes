'use client';

import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Edit, Save, X, Download, ChevronLeft, ChevronRight, FileText, Type, Trash2, Sparkles } from 'lucide-react';
import { useBackground } from '../../providers';
import dynamic from 'next/dynamic';

const MDEditor = dynamic(
    () => import('@uiw/react-md-editor').then((mod) => mod.default),
    { ssr: false }
);

interface Props {
    content: string;
    onSave: (content: string) => Promise<void>;
    onDelete?: () => Promise<void>;
    nav?: {
        onPrev?: () => void;
        onNext?: () => void;
        hasPrev?: boolean;
        hasNext?: boolean;
        index?: number;
        total?: number;
        onJump?: (index: number) => void;
    };
    title?: string;
    zoomLevel?: number;
    isFormatted?: boolean;
    onFormatProfessional?: () => Promise<void>;
    searchQuery?: string;
}

export function MarkdownViewer({ content, onSave, onDelete, onFormatProfessional, nav, title, zoomLevel = 100, isFormatted, searchQuery }: Props) {
    const { themeType } = useBackground();
    const isLight = themeType === 'light';
    const [isEditing, setIsEditing] = useState(false);
    const [editedContent, setEditedContent] = useState(content);
    const [isSaving, setIsSaving] = useState(false);
    const [showStyleMenu, setShowStyleMenu] = useState(false);
    const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);
    const menuRef = useRef<HTMLDivElement | null>(null);

    // Font style state
    const [fontFamily, setFontFamily] = useState<string>('Inter, system-ui, -apple-system, sans-serif');
    const [fontSize, setFontSize] = useState<number>(14);

    const highlightText = (text: any) => {
        if (!searchQuery || typeof text !== 'string') return text;
        const parts = text.split(new RegExp(`(${searchQuery})`, 'gi'));
        return (
            <>
                {parts.map((part, i) => (
                    part.toLowerCase() === searchQuery.toLowerCase()
                        ? <span key={i} className="bg-blue-500/30 text-blue-200 ring-1 ring-blue-400/50 rounded-sm px-0.5 animate-pulse-soft font-black">{part}</span>
                        : part
                ))}
            </>
        );
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await onSave(editedContent);
            setIsEditing(false);
        } catch (error) {
            console.error('Error saving:', error);
            alert('Error al guardar');
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        setEditedContent(content);
        setIsEditing(false);
    };

    const handleDelete = async () => {
        if (!onDelete) return;
        if (!isConfirmingDelete) {
            setIsConfirmingDelete(true);
            setTimeout(() => setIsConfirmingDelete(false), 3000);
            return;
        }
        await onDelete();
        setIsConfirmingDelete(false);
    };

    const handleExportPdf = () => {
        try {
            const preview = document.getElementById('markdown-preview');
            if (!preview) {
                alert('Vista previa no disponible para exportar');
                return;
            }
            const temp = document.createElement('div');
            temp.innerHTML = preview.innerHTML;

            const positioned = temp.querySelectorAll('*');
            positioned.forEach((el) => {
                try {
                    const cs = window.getComputedStyle(el as Element);
                    if (cs && (cs.position === 'fixed' || cs.position === 'sticky')) {
                        (el as HTMLElement).style.position = 'static';
                        (el as HTMLElement).style.top = 'auto';
                        (el as HTMLElement).style.left = 'auto';
                        (el as HTMLElement).style.right = 'auto';
                        (el as HTMLElement).style.bottom = 'auto';
                    }
                } catch (e) { }
            });

            try {
                const metaKeywords = [/original:/i, /generad/i, /generado:/i, /transcripci.n:/i, /palabras:/i, /duraci.n:/i];
                const children = Array.from(temp.childNodes);
                for (let i = 0; i < Math.min(children.length, 6); i++) {
                    const node = children[i];
                    if (node && node.textContent) {
                        const txt = node.textContent.trim();
                        if (!txt) continue;
                        if (metaKeywords.some((re) => re.test(txt))) {
                            node.parentNode?.removeChild(node);
                        }
                    }
                }
            } catch (e) { }

            const contentHtml = temp.innerHTML;
            let titleDate = new Date();
            try {
                const dateMatch = contentHtml.match(/(\d{4}-\d{2}-\d{2})/);
                if (dateMatch) titleDate = new Date(dateMatch[1]);
            } catch (e) { }
            const titleDateStr = titleDate.toISOString().slice(0, 10);

            const html = `
                <!doctype html>
                <html>
                <head>
                    <meta charset="utf-8" />
                    <title>Transcripción</title>
                    <style>
                        html,body { height: auto; width: 100%; margin: 0; padding: 18px; }
                        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111827; line-height: 1.5; }
                        h1,h2,h3,h4 { color: #0f172a; margin-top: 1rem; margin-bottom: .5rem; }
                        pre, code { background: #f3f4f6; padding: 8px; border-radius: 6px; display: block; white-space: pre-wrap; }
                        table { width: 100%; border-collapse: collapse; }
                        th, td { border: 1px solid #e5e7eb; padding: 8px; }
                        blockquote { border-left: 4px solid #60a5fa; padding-left: 12px; color: #374151; margin: .5rem 0; }
                    </style>
                </head>
                <body><div class="pdf-root">${contentHtml}</div></body>
                </html>
            `;

            const newWin = window.open('', '_blank', 'noopener,noreferrer');
            if (newWin) {
                newWin.document.open();
                newWin.document.write(html);
                newWin.document.close();
                setTimeout(() => {
                    try {
                        newWin.focus();
                        newWin.print();
                    } catch (e) { }
                }, 500);
            }
        } catch (err) {
            console.error('Export PDF error:', err);
        }
    };

    useEffect(() => {
        const onKeyDown = (e: KeyboardEvent) => {
            if (isEditing) return;

            // Ignore if the focus is on an input, textarea or contenteditable
            const target = e.target as HTMLElement;
            const isInput = target.tagName === 'INPUT' ||
                target.tagName === 'TEXTAREA' ||
                target.isContentEditable;
            if (isInput) return;

            if (e.key === 'ArrowLeft' && nav?.onPrev && nav.hasPrev) nav.onPrev();
            if (e.key === 'ArrowRight' && nav?.onNext && nav.hasNext) nav.hasNext && nav.onNext();
        };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [nav, isEditing]);

    useEffect(() => {
        const onDocClick = (ev: MouseEvent) => {
            if (!showStyleMenu) return;
            if (menuRef.current && !menuRef.current.contains(ev.target as Node)) setShowStyleMenu(false);
        };
        const onEsc = (ev: KeyboardEvent) => { if (ev.key === 'Escape') setShowStyleMenu(false); };
        document.addEventListener('mousedown', onDocClick);
        document.addEventListener('keydown', onEsc);
        return () => {
            document.removeEventListener('mousedown', onDocClick);
            document.removeEventListener('keydown', onEsc);
        };
    }, [showStyleMenu]);

    let extractedDate = '';
    try {
        const m = content && content.match(/(\d{4}-\d{2}-\d{2})/);
        if (m) extractedDate = new Date(m[1]).toISOString().slice(0, 10);
    } catch (e) { }

    const displayTitle = title || 'Última Clase';

    return (
        <div
            className="h-full flex flex-col glass backdrop-blur-xl rounded-[2rem] border border-white/10 shadow-2xl relative overflow-hidden"
            style={{
                fontFamily: 'var(--font-geist-sans)',
                '--zoom-factor': zoomLevel / 100
            } as any}
        >
            {showStyleMenu && (
                <div ref={menuRef} className="fixed top-14 right-10 z-[70] bg-white/95 backdrop-blur-xl border border-slate-200 rounded-2xl shadow-2xl p-4 min-w-[220px] animate-in fade-in slide-in-from-top-2 duration-200">
                    <div className="flex items-center justify-between mb-3">
                        <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">Tipografía</div>
                        <button onClick={() => setShowStyleMenu(false)} className="p-1 hover:bg-slate-100 rounded-lg text-slate-400"><X size={14} /></button>
                    </div>
                    <div className="space-y-4">
                        <div className="space-y-1.5">
                            <label className="text-[10px] font-bold text-slate-500">Familia</label>
                            <select value={fontFamily} onChange={(e) => setFontFamily(e.target.value)} className="w-full text-xs px-3 py-2 bg-slate-50 border-none rounded-xl">
                                <option value={'Times New Roman, Times, serif'}>Times New Roman</option>
                                <option value={'Georgia, serif'}>Georgia</option>
                                <option value={'Inter, system-ui, -apple-system, sans-serif'}>Inter (System)</option>
                                <option value={'Arial, Helvetica, sans-serif'}>Arial</option>
                                <option value={'Courier New, monospace'}>Courier New (Mono)</option>
                            </select>
                        </div>
                        <div className="space-y-1.5">
                            <div className="flex justify-between">
                                <label className="text-[10px] font-bold text-slate-500">Tamaño</label>
                                <span className="text-[10px] font-black text-indigo-600">{fontSize}px</span>
                            </div>
                            <input type="range" min={12} max={24} value={fontSize} onChange={(e) => setFontSize(parseInt(e.target.value))} className="w-full accent-indigo-500" />
                        </div>
                    </div>
                </div>
            )}

            <div className="flex justify-between items-center p-4 border-b border-white/10 sticky top-0 z-10">
                <div className="flex flex-col min-w-0">
                    <div className="flex items-center gap-2">
                        <h2
                            className="text-lg font-black tracking-tighter leading-tight title-semi-neon"
                            style={{ fontFamily, fontSize: `${Math.round(fontSize * 1.3 * (zoomLevel / 100))}px` }}
                        >
                            {displayTitle}
                        </h2>
                        {isFormatted && (
                            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 shadow-[0_0_15px_rgba(139,92,246,0.1)]">
                                <Sparkles size={11} className="text-violet-400 animate-pulse" />
                                <span className="text-[10px] font-black text-violet-300 uppercase tracking-widest">AI Formatted</span>
                            </div>
                        )}
                    </div>
                    <span className="text-[10px] uppercase tracking-[0.2em] font-black text-[var(--foreground)]/50 mt-1.5 block">
                        {extractedDate ? `• ${extractedDate} •` : '• Transcripción Reciente •'}
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    {nav && (
                        <div className="flex items-center gap-1.5 mr-2">
                            <button onClick={nav.onPrev} disabled={!nav.hasPrev} className="p-2 rounded-full bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 disabled:opacity-30 transition-all text-[var(--foreground)]">
                                <ChevronLeft size={16} />
                            </button>
                            <button onClick={nav.onNext} disabled={!nav.hasNext} className="p-2 rounded-full bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20 disabled:opacity-30 transition-all text-[var(--foreground)]">
                                <ChevronRight size={16} />
                            </button>
                            {typeof nav.index === 'number' && (
                                <span className="text-[10px] font-bold text-[var(--foreground)]/60 ml-1">{nav.index + 1}/{nav.total}</span>
                            )}
                        </div>
                    )}
                    <div className="flex gap-1.5">
                        {isEditing ? (
                            <>
                                <button onClick={handleCancel} className="p-2 text-[var(--foreground)]/70 hover:bg-black/5 dark:hover:bg-white/10 rounded-lg transition-all"><X size={18} /></button>
                                <button onClick={handleSave} disabled={isSaving} className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500 text-white rounded-lg text-xs font-bold shadow-sm">{isSaving ? '...' : 'Guardar'}</button>
                            </>
                        ) : (
                            <>
                                <div className="relative group">
                                    <button
                                        onClick={() => setShowStyleMenu(!showStyleMenu)}
                                        className={`p-2 rounded-lg transition-all relative ${showStyleMenu ? 'bg-indigo-600 text-white shadow-lg' : isLight ? 'text-slate-900 hover:bg-slate-200' : 'text-slate-100 hover:bg-white/10'}`}
                                    >
                                        <Type size={18} />
                                        {!showStyleMenu && <div className={`absolute -top-0.5 -right-0.5 w-2 h-2 bg-indigo-500 rounded-full border-2 ${isLight ? 'border-white' : 'border-slate-800'} animate-soft-pulse`} />}
                                    </button>
                                </div>
                                {onFormatProfessional && !isFormatted && (
                                    <button
                                        onClick={onFormatProfessional}
                                        className={`flex items-center gap-2 px-3 py-1 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white rounded-lg text-xs font-bold shadow-lg shadow-indigo-500/20 transition-all transform hover:scale-105 active:scale-95 group/prof`}
                                        title="Formatear Profesionalmente (Thinking Model)"
                                    >
                                        <Sparkles size={14} className="group-hover/prof:animate-pulse" />
                                        <span className="hidden sm:inline">Pro Format</span>
                                    </button>
                                )}
                                <button onClick={() => setIsEditing(true)} className={`p-2 rounded-lg transition-all ${isLight ? 'text-slate-900 hover:bg-slate-200' : 'text-slate-100 hover:bg-white/10'}`}><Edit size={18} /></button>
                                {onDelete && (
                                    <div className={`flex items-center transition-all duration-300 ${isConfirmingDelete ? 'gap-1 bg-rose-500/10 p-1 rounded-xl border border-rose-500/20' : 'gap-0'}`}>
                                        {isConfirmingDelete && (
                                            <button
                                                onClick={() => setIsConfirmingDelete(false)}
                                                className="p-1.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-lg text-slate-400 transition-colors"
                                                title="Cancelar"
                                            >
                                                <X size={16} />
                                            </button>
                                        )}
                                        <button
                                            onClick={handleDelete}
                                            className={`p-2 rounded-lg transition-all ${isConfirmingDelete
                                                ? 'bg-rose-500 text-white shadow-lg'
                                                : 'text-rose-500/70 hover:text-rose-500 hover:bg-rose-500/10'
                                                }`}
                                            title={isConfirmingDelete ? "Confirmar eliminación" : "Eliminar clase"}
                                        >
                                            <Trash2 size={isConfirmingDelete ? 16 : 18} />
                                        </button>
                                    </div>
                                )}
                                <button onClick={handleExportPdf} className={`p-2 rounded-lg transition-all ${isLight ? 'text-slate-900 hover:bg-slate-200' : 'text-slate-100 hover:bg-white/10'}`}><Download size={18} /></button>
                            </>
                        )}
                    </div>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
                {isEditing ? (
                    <div data-color-mode="light" style={{ fontFamily }} className="h-full">
                        <style jsx global>{`
                            .w-md-editor {
                                background-color: transparent !important;
                                border: none !important;
                            }
                            .w-md-editor-toolbar {
                                background-color: rgba(0, 0, 0, 0.1) !important;
                                border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
                            }
                            .w-md-editor-content {
                                background-color: transparent !important;
                            }
                            .w-md-editor-area {
                                background-color: transparent !important;
                                color: var(--foreground) !important;
                            }
                        `}</style>
                        <MDEditor value={editedContent} onChange={(val) => setEditedContent(val || '')} height="100%" preview="edit" style={{ fontFamily, fontSize: `${fontSize * (zoomLevel / 100)}px` }} />
                    </div>
                ) : (
                    <div id="markdown-preview" style={{ fontFamily, fontSize: `${fontSize * (zoomLevel / 100)}px` }} className="max-w-4xl mx-auto">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                h1: ({ children, ...p }) => <h1 style={{ fontSize: `${Math.round(fontSize * 1.5 * (zoomLevel / 100))}px` }} className="font-bold mt-6 mb-4 text-[var(--foreground)]" {...p}>{highlightText(children)}</h1>,
                                h2: ({ children, ...p }) => <h2 style={{ fontSize: `${Math.round(fontSize * 1.3 * (zoomLevel / 100))}px` }} className="font-bold mt-5 mb-3 text-[var(--foreground)]" {...p}>{highlightText(children)}</h2>,
                                h3: ({ children, ...p }) => <h3 style={{ fontSize: `${Math.round(fontSize * 1.15 * (zoomLevel / 100))}px` }} className="font-bold mt-4 mb-2 text-[var(--foreground)]/90" {...p}>{highlightText(children)}</h3>,
                                p: ({ children, ...p }) => <p style={{ fontSize: `${fontSize * (zoomLevel / 100)}px`, lineHeight: 1.6 }} className="text-[var(--foreground)]/70 mb-4 text-justify" {...p}>{highlightText(children)}</p>,
                                ul: (p) => <ul style={{ fontSize: `${fontSize * (zoomLevel / 100)}px` }} className="list-disc list-inside space-y-2 mb-4 text-[var(--foreground)]/70" {...p} />,
                                ol: (p) => <ol style={{ fontSize: `${fontSize * (zoomLevel / 100)}px` }} className="list-decimal list-inside space-y-2 mb-4 text-[var(--foreground)]/70" {...p} />,
                                li: ({ children, ...p }) => <li className="ml-1" {...p}>{highlightText(children)}</li>,
                                strong: ({ children, ...p }) => <strong className="font-bold text-[var(--foreground)]" {...p}>{highlightText(children)}</strong>,
                                blockquote: ({ children, ...p }) => <blockquote className="border-l-4 border-indigo-500/30 pl-6 italic text-[var(--foreground)]/60 my-6 bg-indigo-500/5 py-4 rounded-r-xl" {...p}>{highlightText(children)}</blockquote>,
                            }}
                        >
                            {content}
                        </ReactMarkdown>
                    </div>
                )}
            </div>

            {/* Premium Minimal Navigator Scrubber */}
            {!isEditing && nav && nav.total && nav.total > 1 && (
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-1 px-3 py-1.5 glass rounded-full border border-white/10 shadow-lg scale-90 hover:scale-100 transition-all duration-300 opacity-40 hover:opacity-100 group/nav">
                    {Array.from({ length: nav.total }).map((_, i) => (
                        <button
                            key={i}
                            onClick={() => nav.onJump?.(i)}
                            className={`h-1 rounded-full transition-all duration-300 ${i === nav.index
                                ? 'w-6 bg-[var(--theme-neon-color)] shadow-[0_0_8px_var(--theme-neon-color)]'
                                : 'w-2 bg-white/20 hover:bg-white/40'
                                }`}
                            title={`Clase ${i + 1}`}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
