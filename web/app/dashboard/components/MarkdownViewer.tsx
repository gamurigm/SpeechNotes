'use client';

import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Edit, Save, X, Download, ChevronLeft, ChevronRight, FileText } from 'lucide-react';
import dynamic from 'next/dynamic';

const MDEditor = dynamic(
    () => import('@uiw/react-md-editor').then((mod) => mod.default),
    { ssr: false }
);

interface Props {
    content: string;
    onSave: (content: string) => Promise<void>;
    nav?: {
        onPrev?: () => void;
        onNext?: () => void;
        hasPrev?: boolean;
        hasNext?: boolean;
        index?: number;
        total?: number;
    };
    title?: string;
    zoomLevel?: number;
}

export function MarkdownViewer({ content, onSave, nav, title, zoomLevel = 100 }: Props) {
    const [isEditing, setIsEditing] = useState(false);
    const [editedContent, setEditedContent] = useState(content);
    const [isSaving, setIsSaving] = useState(false);
    const [showStyleMenu, setShowStyleMenu] = useState(false);
    const menuRef = useRef<HTMLDivElement | null>(null);

    // Font style state
    const [fontFamily, setFontFamily] = useState<string>('Inter, system-ui, -apple-system, sans-serif');
    const [fontSize, setFontSize] = useState<number>(14);

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
        <div className="h-full flex flex-col bg-white rounded-lg shadow relative overflow-hidden" style={{ fontFamily: 'var(--font-geist-sans)', transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top left', width: `${100 * (100 / zoomLevel)}%`, height: `${100 * (100 / zoomLevel)}%` }}>
            <div
                className="absolute top-3 left-3 z-[60] w-1.5 h-1.5 rounded-full bg-slate-200/50 hover:bg-indigo-500 hover:scale-[3] transition-all cursor-pointer shadow-sm group"
                onClick={() => setShowStyleMenu((s) => !s)}
            >
                <div className="absolute inset-0 rounded-full bg-indigo-400 animate-ping opacity-0 group-hover:opacity-20" />
            </div>

            {showStyleMenu && (
                <div ref={menuRef} className="fixed top-12 left-6 z-[70] bg-white/95 backdrop-blur-xl border border-slate-200 rounded-2xl shadow-2xl p-4 min-w-[220px] animate-in fade-in zoom-in duration-200">
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

            <div className="flex justify-between items-center p-4 border-b bg-white sticky top-0 z-10">
                <div className="flex flex-col min-w-0">
                    <h2
                        className="text-lg font-bold text-slate-900 leading-tight"
                        style={{ fontFamily, letterSpacing: '-0.02em', fontSize: `${Math.round(fontSize * 1.2)}px` }}
                    >
                        {displayTitle}
                    </h2>
                    <span className="text-[10px] uppercase tracking-wider font-bold text-slate-400 mt-1">
                        {extractedDate ? `Fecha: ${extractedDate}` : 'Transcripción reciente'}
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    {nav && (
                        <div className="flex items-center gap-1.5 mr-2">
                            <button onClick={nav.onPrev} disabled={!nav.hasPrev} className="p-2 rounded-full bg-slate-100 hover:bg-slate-200 disabled:opacity-30 transition-all">
                                <ChevronLeft size={16} />
                            </button>
                            <button onClick={nav.onNext} disabled={!nav.hasNext} className="p-2 rounded-full bg-slate-100 hover:bg-slate-200 disabled:opacity-30 transition-all">
                                <ChevronRight size={16} />
                            </button>
                            {typeof nav.index === 'number' && (
                                <span className="text-[10px] font-bold text-slate-500 ml-1">{nav.index + 1}/{nav.total}</span>
                            )}
                        </div>
                    )}
                    <div className="flex gap-1.5">
                        {isEditing ? (
                            <>
                                <button onClick={handleCancel} className="p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-all"><X size={18} /></button>
                                <button onClick={handleSave} disabled={isSaving} className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500 text-white rounded-lg text-xs font-bold shadow-sm">{isSaving ? '...' : 'Guardar'}</button>
                            </>
                        ) : (
                            <>
                                <button onClick={() => setIsEditing(true)} className="p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-all"><Edit size={18} /></button>
                                <button onClick={handleExportPdf} className="p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-all"><Download size={18} /></button>
                            </>
                        )}
                    </div>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
                {isEditing ? (
                    <div data-color-mode="light" style={{ fontFamily }}>
                        <MDEditor value={editedContent} onChange={(val) => setEditedContent(val || '')} height="100%" preview="edit" style={{ fontFamily, fontSize: `${fontSize}px` }} />
                    </div>
                ) : (
                    <div id="markdown-preview" style={{ fontFamily, fontSize: `${fontSize}px` }}>
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                h1: (p) => <h1 style={{ fontSize: `${Math.round(fontSize * 1.5)}px` }} className="font-bold mt-4 mb-2 text-slate-900" {...p} />,
                                h2: (p) => <h2 style={{ fontSize: `${Math.round(fontSize * 1.3)}px` }} className="font-bold mt-3 mb-2 text-slate-900" {...p} />,
                                h3: (p) => <h3 style={{ fontSize: `${Math.round(fontSize * 1.15)}px` }} className="font-bold mt-2 mb-1 text-slate-800" {...p} />,
                                p: (p) => <p style={{ fontSize: `${fontSize}px`, lineHeight: 1.5 }} className="text-slate-600 mb-3" {...p} />,
                                ul: (p) => <ul className="list-disc list-inside space-y-1 mb-3 text-slate-600" {...p} />,
                                ol: (p) => <ol className="list-decimal list-inside space-y-1 mb-3 text-slate-600" {...p} />,
                                li: (p) => <li className="ml-1" {...p} />,
                                strong: (p) => <strong className="font-bold text-slate-900" {...p} />,
                                blockquote: (p) => <blockquote className="border-l-4 border-slate-200 pl-4 italic text-slate-500 my-4" {...p} />,
                            }}
                        >
                            {content}
                        </ReactMarkdown>
                    </div>
                )}
            </div>
        </div>
    );
}
