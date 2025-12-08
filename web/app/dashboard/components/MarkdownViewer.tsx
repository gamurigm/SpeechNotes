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
    const [fontFamily, setFontFamily] = useState<string>('Times New Roman, Times, serif');
    const [fontSize, setFontSize] = useState<number>(16);

    // Title will use the app's global Geist sans variable for consistent appearance

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
                        // Create a sanitized copy of the preview to avoid layout issues caused by
                        // sticky/fixed elements or app-specific styles. We'll reset positioning
                        // and apply print-friendly CSS to avoid overlapping content in the PDF.
                        const temp = document.createElement('div');
                        temp.innerHTML = preview.innerHTML;

                        // Normalize any elements that are positioned (fixed/sticky) which can
                        // overlap when printed — force them to static and remove offsets.
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
                                } catch (e) {
                                        // ignore cross-origin or computed-style errors
                                }
                        });

                        // Remove top metadata blocks that include noisy info like 'original:', 'generado:', etc.
                        try {
                            const metaKeywords = [/original:/i, /generad/i, /generado:/i, /transcripci.n:/i, /palabras:/i, /duraci.n:/i];
                            // Remove any consecutive top nodes that match metadata patterns
                            const children = Array.from(temp.childNodes);
                            for (let i = 0; i < Math.min(children.length, 6); i++) {
                                const node = children[i];
                                if (node && node.textContent) {
                                    const txt = node.textContent.trim();
                                    if (!txt) continue;
                                    if (metaKeywords.some((re) => re.test(txt))) {
                                        // remove this node from temp
                                        node.parentNode?.removeChild(node);
                                    }
                                }
                            }
                        } catch (e) {
                            // ignore
                        }

                        const contentHtml = temp.innerHTML;

                        // Build a clean header for the PDF. Try to extract a date from the content (YYYY-MM-DD), fallback to today.
                        let titleDate = new Date();
                        try {
                            const dateMatch = contentHtml.match(/(\d{4}-\d{2}-\d{2})/);
                            if (dateMatch) titleDate = new Date(dateMatch[1]);
                        } catch (e) {}
                        const titleDateStr = titleDate.toISOString().slice(0,10);

                        const headerHtml = `
                            <div style="margin-bottom:12px; border-bottom:1px solid #e5e7eb; padding-bottom:8px;">
                              <h1 style="margin:0; font-size:22px;">Transcripción: ${titleDateStr}</h1>
                            </div>
                        `;

                        const html = `
                                <!doctype html>
                                <html>
                                <head>
                                    <meta charset="utf-8" />
                                    <title>Transcripción</title>
                                    <style>
                                        /* Reset and print-friendly defaults */
                                        html,body { height: auto; width: 100%; margin: 0; padding: 18px; }
                                        *, *::before, *::after { box-sizing: border-box; word-break: break-word; }
                                        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; color: #111827; line-height: 1.5; }
                                        h1,h2,h3,h4 { color: #0f172a; margin-top: 1rem; margin-bottom: .5rem; }
                                        p { margin: 0 0 0.75rem 0; }
                                        pre, code { background: #f3f4f6; padding: 8px; border-radius: 6px; display: block; white-space: pre-wrap; }
                                        table { width: 100%; border-collapse: collapse; }
                                        th, td { border: 1px solid #e5e7eb; padding: 8px; }
                                        blockquote { border-left: 4px solid #60a5fa; padding-left: 12px; color: #374151; margin: .5rem 0; }
                                        img { max-width: 100%; height: auto; display: block; }
                                        /* Prevent sticky/fixed headers or floats from overlapping */
                                        [style*="position:fixed"], [style*="position: sticky"] { position: static !important; top: auto !important; }
                                        .sticky, .fixed, .sticky-top, .header, header { position: static !important; }
                                        /* Ensure sections break cleanly across pages */
                                        h1, h2, h3, h4, p, pre, table, blockquote { page-break-inside: avoid; }
                                        /* Small tweak to avoid content starting too close to top */
                                        .pdf-root { padding-top: 8px; }
                                    </style>
                                </head>
                                <body>
                                    <div class="pdf-root">
                                        ${contentHtml}
                                    </div>
                                </body>
                                </html>
                        `;

            const newWin = window.open('', '_blank', 'noopener,noreferrer');
            if (newWin) {
                newWin.document.open();
                newWin.document.write(html);
                newWin.document.close();
                // Give the new window a moment to render styles, then trigger print
                setTimeout(() => {
                    try {
                        newWin.focus();
                        newWin.print();
                    } catch (e) {
                        console.error('Print in new window failed:', e);
                    }
                }, 500);
                return;
            }

            // Fallback: browser blocked pop-up — generate PDF client-side and trigger download
            // Dynamically load html2pdf bundle from CDN and use it to export the preview element.
            const loadScript = (src: string) => new Promise<void>((resolve, reject) => {
                const existing = document.querySelector(`script[src="${src}"]`);
                if (existing) return resolve();
                const s = document.createElement('script');
                s.src = src;
                s.onload = () => resolve();
                s.onerror = (err) => reject(err);
                document.head.appendChild(s);
            });

            const generatePdf = async () => {
                try {
                    // html2pdf will create the PDF and prompt download
                    // @ts-ignore
                    const opt = {
                        margin:       12,
                        filename:     'transcripcion.pdf',
                        image:        { type: 'jpeg', quality: 0.98 },
                        html2canvas:  { scale: 2 },
                        jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
                    };
                    // @ts-ignore
                    window.html2pdf().set(opt).from(preview).save();
                } catch (err) {
                    console.error('html2pdf generation error:', err);
                    alert('No se pudo generar el PDF automáticamente. Intenta permitir pop-ups o usa la opción de imprimir del navegador.');
                }
            };

            const cdn = 'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.9.3/html2pdf.bundle.min.js';
            loadScript(cdn)
                .then(() => generatePdf())
                .catch((err) => {
                    console.error('Failed loading html2pdf lib:', err);
                    alert('No se pudo cargar la librería de exportación. Permite pop-ups o revisa la consola.');
                });
        } catch (err) {
            console.error('Export PDF error:', err);
            alert('Error al exportar a PDF');
        }
    };

    // click outside to close style menu
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

    // Try to extract a date (YYYY-MM-DD) from the content to show as subtitle
    let extractedDate = '';
    try {
        const m = content && content.match(/(\d{4}-\d{2}-\d{2})/);
        if (m) {
            extractedDate = new Date(m[1]).toISOString().slice(0, 10);
        }
    } catch (e) {}

    const displayTitle = title || 'Última Clase';

    // compute scaled sizes per element type based on base fontSize
    const headingScale = {
        h1: 2.1,
        h2: 1.6,
        h3: 1.3,
        h4: 1.15,
        h5: 1.0,
        h6: 0.95,
    };

    return (
        <div className="h-full flex flex-col bg-white rounded-lg shadow" style={{ fontFamily: 'var(--font-geist-sans)', transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top left', width: `${100 * (100 / zoomLevel)}%`, height: `${100 * (100 / zoomLevel)}%` }}>
            <div className="flex justify-between items-center p-4 border-b bg-white sticky top-0 z-10">
                <div className="flex items-center gap-3">
                    <div className="flex items-start gap-2">
                        <div className="flex-none p-2 rounded-md bg-gradient-to-br from-indigo-500 to-sky-500 text-white shadow-md cursor-pointer" onClick={() => setShowStyleMenu((s) => !s)}>
                            <FileText size={18} />
                        </div>

                        {showStyleMenu && (
                            <div ref={menuRef} className="bg-white border border-slate-200 rounded-xl shadow-lg p-3 min-w-[200px]">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="text-sm font-semibold text-slate-800">Apariencia</div>
                                    <button onClick={() => setShowStyleMenu(false)} className="text-xs text-slate-500">Cerrar</button>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs text-slate-600">Fuente</label>
                                    <select value={fontFamily} onChange={(e) => setFontFamily(e.target.value)} className="w-full text-sm px-2 py-1 border rounded">
                                        <option value={'Times New Roman, Times, serif'}>Times New Roman</option>
                                        <option value={'Georgia, serif'}>Georgia</option>
                                        <option value={'Inter, system-ui, -apple-system, sans-serif'}>Inter (System)</option>
                                        <option value={'Arial, Helvetica, sans-serif'}>Arial</option>
                                        <option value={'Courier New, monospace'}>Courier New (Mono)</option>
                                    </select>

                                    <div>
                                        <label className="text-xs text-slate-600">Tamaño: <span className="font-medium">{fontSize}px</span></label>
                                        <input type="range" min={12} max={24} step={1} value={fontSize} onChange={(e) => setFontSize(parseInt(e.target.value))} className="w-full mt-1" />
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                    <div className="flex flex-col min-w-0">
                        <h2
                            className="text-2xl sm:text-3xl font-sans font-semibold text-slate-900 leading-tight break-words whitespace-pre-wrap max-w-prose"
                            style={{ fontFamily, letterSpacing: '0.2px', fontSize: `${Math.round(fontSize * 1.4)}px` }}
                        >
                            {displayTitle}
                        </h2>
                        <span className="text-sm text-slate-500 mt-0.5">{extractedDate ? `Fecha: ${extractedDate}` : 'Transcripción reciente'}</span>
                    </div>
                </div>
                <div className="flex gap-2">
                    {nav && (
                        <div className="flex items-center mr-4 gap-2">
                            <button
                                onClick={nav.onPrev}
                                disabled={!nav.hasPrev}
                                aria-label="Anterior"
                                className="p-2.5 rounded-full bg-gradient-to-br from-slate-300 to-slate-400 hover:from-slate-400 hover:to-slate-500 disabled:opacity-40 disabled:cursor-not-allowed shadow-md hover:shadow-lg transition-all transform hover:scale-110 duration-200"
                            >
                                <ChevronLeft size={20} className="text-white" />
                            </button>
                            <button
                                onClick={nav.onNext}
                                disabled={!nav.hasNext}
                                aria-label="Siguiente"
                                className="p-2.5 rounded-full bg-gradient-to-br from-slate-300 to-slate-400 hover:from-slate-400 hover:to-slate-500 disabled:opacity-40 disabled:cursor-not-allowed shadow-md hover:shadow-lg transition-all transform hover:scale-110 duration-200"
                            >
                                <ChevronRight size={20} className="text-white" />
                            </button>
                            {typeof nav.index === 'number' && typeof nav.total === 'number' && (
                                <span className="ml-2 px-3 py-1 text-sm font-semibold text-white bg-gradient-to-r from-slate-500 to-slate-600 rounded-full shadow-md">{nav.index + 1}/{nav.total}</span>
                            )}
                        </div>
                    )}
                    {isEditing ? (
                        <>
                            <button
                                onClick={handleCancel}
                                className="flex items-center gap-2 px-4 py-2.5 text-white bg-gradient-to-r from-gray-400 to-gray-500 rounded-lg hover:from-gray-500 hover:to-gray-600 transition-all shadow-md hover:shadow-lg transform hover:scale-105 duration-200 font-medium"
                            >
                                <X size={20} />
                                Cancelar
                            </button>
                            <button
                                onClick={handleSave}
                                disabled={isSaving}
                                className="flex items-center gap-2 px-4 py-2.5 text-white bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all shadow-md hover:shadow-lg transform hover:scale-105 duration-200 disabled:opacity-60 disabled:cursor-not-allowed font-medium"
                            >
                                <Save size={20} />
                                {isSaving ? 'Guardando...' : 'Guardar'}
                            </button>
                        </>
                    ) : (
                        <>
                            <button
                                onClick={() => setIsEditing(true)}
                                className="flex items-center gap-2 px-4 py-2.5 text-white bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all shadow-md hover:shadow-lg transform hover:scale-105 duration-200 font-medium"
                            >
                                <Edit size={20} />
                                Editar
                            </button>
                            <button
                                type="button"
                                onClick={handleExportPdf}
                                className="flex items-center gap-2 px-4 py-2.5 text-white bg-gradient-to-r from-orange-500 to-red-500 rounded-lg hover:from-orange-600 hover:to-red-600 transition-all shadow-md hover:shadow-lg transform hover:scale-105 duration-200 font-medium"
                                title="Exportar a PDF"
                            >
                                <Download size={20} />
                                PDF
                            </button>
                        </>
                    )}
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
                {isEditing ? (
                    <div data-color-mode="light" style={{ fontFamily }}>
                        <MDEditor
                            value={editedContent}
                            onChange={(val) => setEditedContent(val || '')}
                            height="100%"
                            preview="edit"
                            style={{ fontFamily, fontSize: `${fontSize}px` }}
                        />
                    </div>
                ) : (
                    <div className="markdown-content">
                        <div id="markdown-preview" style={{ fontFamily, fontSize: `${fontSize}px` }}>
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    h1: ({node, ...props}) => <h1 style={{ fontFamily, fontSize: `${Math.round(fontSize * 2.1)}px` }} className="font-bold mt-6 mb-4 text-gray-900" {...props} />,
                                    h2: ({node, ...props}) => <h2 style={{ fontFamily, fontSize: `${Math.round(fontSize * 1.6)}px` }} className="font-bold mt-5 mb-3 text-gray-900" {...props} />,
                                    h3: ({node, ...props}) => <h3 style={{ fontFamily, fontSize: `${Math.round(fontSize * 1.3)}px` }} className="font-bold mt-4 mb-2 text-gray-800" {...props} />,
                                    h4: ({node, ...props}) => <h4 style={{ fontFamily, fontSize: `${Math.round(fontSize * 1.15)}px` }} className="font-bold mt-3 mb-2 text-gray-800" {...props} />,
                                    h5: ({node, ...props}) => <h5 style={{ fontFamily, fontSize: `${Math.round(fontSize * 1.0)}px` }} className="font-bold mt-2 mb-1 text-gray-800" {...props} />,
                                    h6: ({node, ...props}) => <h6 style={{ fontFamily, fontSize: `${Math.round(fontSize * 0.95)}px` }} className="font-bold text-gray-800" {...props} />,
                                    p: ({node, ...props}) => <p style={{ fontFamily, fontSize: `${fontSize}px`, lineHeight: 1.6 }} className="text-gray-700 mb-4" {...props} />,
                                    ul: ({node, ...props}) => <ul className="list-disc list-inside text-gray-700 mb-4" {...props} />,
                                    ol: ({node, ...props}) => <ol className="list-decimal list-inside text-gray-700 mb-4" {...props} />,
                                    li: ({node, ...props}) => <li className="mb-1 ml-2" {...props} />,
                                    strong: ({node, ...props}) => <strong className="font-bold text-gray-900" {...props} />,
                                    em: ({node, ...props}) => <em className="italic text-gray-800" {...props} />,
                                    code: ({node, inline, ...props}: any) =>
                                        inline
                                            ? <code style={{ fontFamily }} className="bg-gray-100 px-2 py-1 rounded text-sm text-red-600 font-mono" {...props} />
                                            : <code style={{ fontFamily }} className="block bg-gray-100 p-4 rounded text-sm text-gray-900 font-mono overflow-x-auto mb-4" {...props} />,
                                    blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-700 my-4" {...props} />,
                                    hr: () => <hr className="my-6 border-gray-300" />,
                                    table: ({node, ...props}) => <table className="w-full border-collapse border border-gray-300 my-4" {...props} />,
                                    th: ({node, ...props}) => <th className="border border-gray-300 bg-gray-100 px-4 py-2 text-left font-bold" {...props} />,
                                    td: ({node, ...props}) => <td className="border border-gray-300 px-4 py-2" {...props} />,
                                    a: ({node, ...props}) => <a className="text-blue-600 hover:underline" {...props} />,
                                }}
                            >
                                {content}
                            </ReactMarkdown>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
