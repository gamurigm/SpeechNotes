'use client';

import { isValidElement, useState, useEffect, useRef, useMemo } from 'react';
import type { ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
    Edit, X, Download, ChevronLeft, ChevronRight, Type, Trash2, Sparkles,
    BookOpen, Copy, Maximize2, Minimize2, Check, Clock, List, AlignLeft,
} from 'lucide-react';
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

function makeSlug(text: string): string {
    return text.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
}

type Heading = { level: number; text: string; id: string };
type SelectionMenu = { x: number; y: number; text: string };
type ViewerNav = NonNullable<Props['nav']>;
type CopyMode = 'md' | 'plain';
type CopyStatus = CopyMode | null;

function extractNodeText(node: ReactNode): string {
    if (typeof node === 'string' || typeof node === 'number') return String(node);
    if (Array.isArray(node)) return node.map(extractNodeText).join('');
    if (isValidElement<{ children?: ReactNode }>(node)) return extractNodeText(node.props.children);
    return '';
}

function escapeRegExp(value: string): string {
    return value.replace(/[.*+?^${}()|[\]\\]/g, String.raw`\$&`);
}

function highlightText(text: ReactNode, searchQuery?: string): ReactNode {
    if (!searchQuery || typeof text !== 'string') return text;

    const result: ReactNode[] = [];
    const matcher = new RegExp(escapeRegExp(searchQuery), 'gi');
    let cursor = 0;
    let match = matcher.exec(text);

    while (match) {
        if (match.index > cursor) result.push(text.slice(cursor, match.index));
        result.push(
            <span key={`match-${match.index}`} className="bg-blue-500/30 text-blue-200 ring-1 ring-blue-400/50 rounded-sm px-0.5 animate-pulse-soft font-black">
                {match[0]}
            </span>,
        );
        cursor = match.index + match[0].length;
        match = matcher.exec(text);
    }

    if (cursor < text.length) result.push(text.slice(cursor));
    return result;
}

function extractIsoDate(value: string): string {
    const match = /(\d{4}-\d{2}-\d{2})/.exec(value);
    if (!match) return '';
    const date = new Date(match[1]);
    return Number.isNaN(date.getTime()) ? '' : date.toISOString().slice(0, 10);
}

function getThemeButtonTone(isLight: boolean): string {
    return isLight ? 'text-slate-900 hover:bg-slate-200' : 'text-slate-100 hover:bg-white/10';
}

function getOutlineHeadingTone(level: number): string {
    if (level === 1) return 'text-white/80';
    if (level === 2) return 'text-white/55';
    return 'text-white/35';
}

function createViewerMarkdownComponents(fontSize: number, zoomLevel: number, searchQuery?: string): Components {
    const scaledSize = fontSize * (zoomLevel / 100);
    return {
        h1: ({ children, ...props }) => {
            const id = makeSlug(extractNodeText(children));
            return <h1 id={`heading-${id}`} style={{ fontSize: `${Math.round(scaledSize * 1.7)}px` }} className="font-black mt-8 mb-4 text-[var(--foreground)] scroll-mt-20 border-b border-white/10 pb-2" {...props}>{highlightText(children, searchQuery)}</h1>;
        },
        h2: ({ children, ...props }) => {
            const id = makeSlug(extractNodeText(children));
            return <h2 id={`heading-${id}`} style={{ fontSize: `${Math.round(scaledSize * 1.35)}px` }} className="font-bold mt-7 mb-3 text-[var(--foreground)] scroll-mt-20" {...props}>{highlightText(children, searchQuery)}</h2>;
        },
        h3: ({ children, ...props }) => {
            const id = makeSlug(extractNodeText(children));
            return <h3 id={`heading-${id}`} style={{ fontSize: `${Math.round(scaledSize * 1.15)}px` }} className="font-semibold mt-5 mb-2 text-[var(--foreground)]/90 scroll-mt-20" {...props}>{highlightText(children, searchQuery)}</h3>;
        },
        p: ({ children, ...props }) => <p style={{ fontSize: `${scaledSize}px`, lineHeight: 1.75 }} className="text-[var(--foreground)]/70 mb-5 text-justify" {...props}>{highlightText(children, searchQuery)}</p>,
        ul: (props) => <ul style={{ fontSize: `${scaledSize}px` }} className="list-disc list-outside ml-5 space-y-2 mb-5 text-[var(--foreground)]/70" {...props} />,
        ol: (props) => <ol style={{ fontSize: `${scaledSize}px` }} className="list-decimal list-outside ml-5 space-y-2 mb-5 text-[var(--foreground)]/70" {...props} />,
        li: ({ children, ...props }) => <li className="pl-1 leading-relaxed" {...props}>{highlightText(children, searchQuery)}</li>,
        strong: ({ children, ...props }) => <strong className="font-bold text-[var(--foreground)]" {...props}>{highlightText(children, searchQuery)}</strong>,
        em: (props) => <em className="italic text-[var(--foreground)]/80" {...props} />,
        blockquote: ({ children, ...props }) => <blockquote className="border-l-[3px] border-indigo-500/40 pl-5 italic text-[var(--foreground)]/60 my-6 bg-indigo-500/5 py-3 rounded-r-xl pr-4" {...props}>{highlightText(children, searchQuery)}</blockquote>,
        code: ({ className, ...props }) => className?.includes('language-')
            ? <code className="block bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-sm font-mono text-[var(--foreground)]/80 overflow-x-auto my-4" {...props} />
            : <code className="bg-black/20 border border-white/10 rounded px-1.5 py-0.5 text-[0.85em] font-mono text-indigo-300/90" {...props} />,
        pre: (props) => <pre className="bg-black/30 border border-white/10 rounded-xl px-4 py-3 overflow-x-auto my-4 text-sm" {...props} />,
        table: (props) => <div className="overflow-x-auto my-6 rounded-xl border border-white/10"><table className="w-full text-sm" {...props} /></div>,
        thead: (props) => <thead className="bg-white/5 border-b border-white/10" {...props} />,
        th: (props) => <th className="px-4 py-2.5 text-left font-bold text-[var(--foreground)]/80 text-xs uppercase tracking-wide" {...props} />,
        td: (props) => <td className="px-4 py-2.5 border-b border-white/5 text-[var(--foreground)]/65" {...props} />,
        a: (props) => <a target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2 transition-colors" {...props} />,
        hr: () => <hr className="my-8 border-white/10" />,
    };
}

function SelectionToolbar({ menu, onClose }: Readonly<{
    menu: SelectionMenu | null;
    onClose: () => void;
}>) {
    if (!menu) return null;

    const copySelection = async () => {
        await navigator.clipboard.writeText(menu.text);
        onClose();
    };

    return (
        <div
            data-sel-toolbar
            style={{ position: 'fixed', left: menu.x, top: menu.y - 56, transform: 'translateX(-50%)', zIndex: 200 }}
            className="flex items-center gap-0.5 px-1.5 py-1 bg-slate-900/97 backdrop-blur-xl border border-white/15 rounded-xl shadow-2xl text-white animate-in fade-in slide-in-from-bottom-1 duration-150 pointer-events-auto"
        >
            <button type="button" onClick={copySelection} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg hover:bg-white/10 text-xs font-medium transition-colors whitespace-nowrap">
                <Copy size={11} /> Copiar
            </button>
            <div className="w-px h-4 bg-white/15 mx-0.5" />
            <span className="text-[10px] text-white/30 px-2 font-mono tabular-nums">
                {menu.text.split(/\s+/).filter(Boolean).length}w
            </span>
            <div className="w-px h-4 bg-white/15 mx-0.5" />
            <button type="button" onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/10 text-white/40 transition-colors"><X size={10} /></button>
        </div>
    );
}

function OutlinePanel({ headings, isVisible, onClose, onSelect }: Readonly<{
    headings: Heading[];
    isVisible: boolean;
    onClose: () => void;
    onSelect: (id: string) => void;
}>) {
    if (!isVisible) return null;

    return (
        <div className="absolute left-0 bottom-0 w-60 z-20 bg-slate-950/95 backdrop-blur-xl border-r border-white/10 overflow-y-auto flex flex-col animate-in slide-in-from-left-2 duration-200" style={{ top: '73px' }}>
            <div className="p-3 border-b border-white/10 flex items-center justify-between sticky top-0 bg-slate-950/95">
                <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-white/40">
                    <List size={11} /> Esquema
                </div>
                <button type="button" onClick={onClose} className="p-1 rounded-lg hover:bg-white/10 text-white/40 transition-colors"><X size={12} /></button>
            </div>
            <nav className="p-2 space-y-0.5 flex-1">
                {headings.length === 0 ? (
                    <p className="text-xs text-white/25 text-center py-6">Sin encabezados</p>
                ) : headings.map((heading) => (
                    <button
                        type="button"
                        key={heading.id}
                        onClick={() => onSelect(heading.id)}
                        className="w-full text-left rounded-lg hover:bg-white/8 text-xs transition-all group py-1.5 pr-2"
                        style={{ paddingLeft: `${(heading.level - 1) * 12 + 10}px` }}
                    >
                        <span className={`block truncate font-medium group-hover:text-indigo-300 transition-colors ${getOutlineHeadingTone(heading.level)}`}>
                            {heading.level > 1 && <span className="opacity-30 mr-1">{'·'.repeat(heading.level - 1)}</span>}
                            {heading.text}
                        </span>
                    </button>
                ))}
            </nav>
        </div>
    );
}

function StyleMenu({ fontFamily, fontSize, isVisible, menuRef, onClose, onFontFamilyChange, onFontSizeChange }: Readonly<{
    fontFamily: string;
    fontSize: number;
    isVisible: boolean;
    menuRef: React.RefObject<HTMLDivElement>;
    onClose: () => void;
    onFontFamilyChange: (fontFamily: string) => void;
    onFontSizeChange: (fontSize: number) => void;
}>) {
    if (!isVisible) return null;

    return (
        <div ref={menuRef} className="fixed top-14 right-10 z-[70] bg-white/95 backdrop-blur-xl border border-slate-200 rounded-2xl shadow-2xl p-4 min-w-[220px] animate-in fade-in slide-in-from-top-2 duration-200">
            <div className="flex items-center justify-between mb-3">
                <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">Tipografía</div>
                <button type="button" onClick={onClose} className="p-1 hover:bg-slate-100 rounded-lg text-slate-400"><X size={14} /></button>
            </div>
            <div className="space-y-4">
                <div className="space-y-1.5">
                    <label htmlFor="markdown-font-family" className="text-[10px] font-bold text-slate-500">Familia</label>
                    <select id="markdown-font-family" value={fontFamily} onChange={(event) => onFontFamilyChange(event.target.value)} className="w-full text-xs px-3 py-2 bg-slate-50 border-none rounded-xl">
                        <option value="Times New Roman, Times, serif">Times New Roman</option>
                        <option value="Georgia, serif">Georgia</option>
                        <option value="Inter, system-ui, -apple-system, sans-serif">Inter (System)</option>
                        <option value="Arial, Helvetica, sans-serif">Arial</option>
                        <option value="Courier New, monospace">Courier New (Mono)</option>
                    </select>
                </div>
                <div className="space-y-1.5">
                    <div className="flex justify-between">
                        <label htmlFor="markdown-font-size" className="text-[10px] font-bold text-slate-500">Tamaño</label>
                        <span className="text-[10px] font-black text-indigo-600">{fontSize}px</span>
                    </div>
                    <input id="markdown-font-size" type="range" min={12} max={24} value={fontSize} onChange={(event) => onFontSizeChange(Number.parseInt(event.target.value, 10))} className="w-full accent-indigo-500" />
                </div>
            </div>
        </div>
    );
}

function DocumentMetadata({ date, isFormatted, readingTime, title, wordCount, fontFamily, titleFontSize }: Readonly<{
    date: string;
    fontFamily: string;
    isFormatted?: boolean;
    readingTime: number;
    title: string;
    titleFontSize: number;
    wordCount: number;
}>) {
    return (
        <div className="flex flex-col min-w-[300px] flex-1">
            <h2 className="text-2xl font-black tracking-tighter leading-tight title-semi-neon truncate" style={{ fontFamily, fontSize: `${titleFontSize}px` }} title={title}>
                {title}
            </h2>
            <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                <span className="text-[10px] uppercase tracking-[0.2em] font-black text-[var(--foreground)]/50 block whitespace-nowrap">
                    {date ? `• ${date} •` : '• Transcripción Reciente •'}
                </span>
                {isFormatted && (
                    <div className="flex-shrink-0 flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-violet-500/10 border border-violet-500/20 shadow-[0_0_15px_rgba(139,92,246,0.1)]">
                        <Sparkles size={10} className="text-violet-400 animate-pulse" />
                        <span className="text-[9px] font-black text-violet-300 uppercase tracking-widest">AI Formatted</span>
                    </div>
                )}
                <div className="flex items-center gap-1.5 text-[10px] text-[var(--foreground)]/30 font-medium">
                    <AlignLeft size={9} />
                    <span>{wordCount.toLocaleString()}&nbsp;palabras</span>
                    <span className="opacity-50">·</span>
                    <Clock size={9} />
                    <span>~{readingTime}&nbsp;min</span>
                </div>
            </div>
        </div>
    );
}

function DocumentNavigation({ nav }: Readonly<{ nav?: ViewerNav }>) {
    if (!nav) return null;

    const handleJump = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key !== 'Enter') return;
        const value = Number.parseInt(event.currentTarget.value, 10);
        if (Number.isNaN(value) || value <= 0 || value > (nav.total ?? 0)) return;
        nav.onJump?.(value - 1);
        event.currentTarget.value = '';
        event.currentTarget.blur();
    };

    return (
        <div className="flex items-center gap-2 p-1 bg-white/5 dark:bg-black/30 rounded-2xl border border-white/10 shadow-lg group/nav transition-all duration-500">
            <div className="flex items-center gap-1 bg-white/5 rounded-xl p-1 border border-white/5">
                <button type="button" onClick={nav.onPrev} disabled={!nav.hasPrev} className={`p-1.5 rounded-lg transition-all duration-300 ${nav.hasPrev ? 'hover:bg-indigo-500/20 text-[var(--foreground)] hover:scale-110 active:scale-95' : 'opacity-10 cursor-not-allowed'}`}>
                    <ChevronLeft size={16} />
                </button>
                <div className="px-3 flex flex-col items-center justify-center min-w-[64px]">
                    <div className="flex items-baseline gap-1">
                        <span className="text-lg font-black bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent" key={nav.index}>{(nav.index ?? 0) + 1}</span>
                        <span className="text-xs font-bold opacity-10 text-[var(--foreground)]">/</span>
                        <span className="text-[10px] font-black opacity-30 text-[var(--foreground)] font-mono">{nav.total}</span>
                    </div>
                </div>
                <button type="button" onClick={nav.onNext} disabled={!nav.hasNext} className={`p-1.5 rounded-lg transition-all duration-300 ${nav.hasNext ? 'hover:bg-indigo-500/20 text-[var(--foreground)] hover:scale-110 active:scale-95' : 'opacity-10 cursor-not-allowed'}`}>
                    <ChevronRight size={16} />
                </button>
            </div>
            <div className="flex items-center bg-indigo-500/5 border border-indigo-500/10 rounded-full p-0.5 group/jump">
                <input type="text" aria-label="Ir a transcripción" placeholder="GO" className="w-9 h-9 bg-black/40 border border-white/5 rounded-full text-[9px] font-black text-center text-white focus:outline-none focus:border-indigo-500 transition-all duration-300 placeholder:text-white/20" onKeyDown={handleJump} />
            </div>
        </div>
    );
}

function CopyControl({ copied, isLight, mode, onCopy }: Readonly<{
    copied: CopyStatus;
    isLight: boolean;
    mode: CopyMode;
    onCopy: (mode: CopyMode) => void;
}>) {
    const isCopied = copied === mode;
    const label = mode === 'md' ? 'MD' : 'TXT';
    const title = mode === 'md' ? 'Copiar como Markdown' : 'Copiar como texto plano';
    const tone = isCopied ? 'bg-emerald-500/20 text-emerald-400' : getThemeButtonTone(isLight);

    return (
        <button type="button" onClick={() => onCopy(mode)} className={`flex items-center gap-1 px-2 py-2 rounded-xl transition-all text-[10px] font-black ${tone}`} title={title}>
            {isCopied ? <Check size={13} /> : <Copy size={13} />}<span>{label}</span>
        </button>
    );
}

function ProfessionalFormatControl({ isFormatted, onFormat }: Readonly<{
    isFormatted?: boolean;
    onFormat?: () => Promise<void>;
}>) {
    if (!onFormat) return null;
    const gradient = isFormatted ? 'from-slate-600 to-slate-700' : 'from-violet-600 to-indigo-600';
    const shadow = isFormatted ? 'shadow-slate-500/10' : 'shadow-indigo-500/20';

    return (
        <button type="button" onClick={onFormat} className={`flex items-center gap-2 px-3 py-2 bg-gradient-to-r ${gradient} hover:from-violet-500 hover:to-indigo-500 text-white rounded-xl text-[10px] font-black shadow-lg ${shadow} transition-all transform hover:scale-105 active:scale-95 group/prof`} title={isFormatted ? 'Volver a refinar con IA' : 'Refinar contenido con Inteligencia Artificial'}>
            <Sparkles size={12} className={`${isFormatted ? 'text-violet-300' : 'text-white'} group-hover/prof:rotate-12 transition-transform`} />
            <span>IA</span>
        </button>
    );
}

function DeleteControl({ isConfirming, onCancel, onDelete }: Readonly<{
    isConfirming: boolean;
    onCancel: () => void;
    onDelete?: () => void;
}>) {
    if (!onDelete) return null;
    const containerTone = isConfirming ? 'gap-1 bg-rose-500/10 p-0.5 rounded-lg border border-rose-500/20' : 'gap-0';
    const buttonTone = isConfirming ? 'bg-rose-500 text-white shadow-lg' : 'text-rose-500/70 hover:text-rose-500 hover:bg-rose-500/10';

    return (
        <>
            <div className="w-px h-4 bg-white/10 mx-0.5" />
            <div className={`flex items-center transition-all duration-300 ${containerTone}`}>
                {isConfirming && <button type="button" onClick={onCancel} className="p-1 hover:bg-black/5 dark:hover:bg-white/10 rounded-md text-slate-400 transition-colors" title="Cancelar"><X size={14} /></button>}
                <button type="button" onClick={onDelete} className={`p-2 rounded-lg transition-all ${buttonTone}`} title={isConfirming ? 'Confirmar eliminación' : 'Eliminar clase'}>
                    <Trash2 size={isConfirming ? 14 : 16} />
                </button>
            </div>
        </>
    );
}

function EditingControls({ isEditing, isSaving, onCancel, onSave }: Readonly<{
    isEditing: boolean;
    isSaving: boolean;
    onCancel: () => void;
    onSave: () => void;
}>) {
    if (!isEditing) return null;
    return (
        <div className="flex items-center gap-2">
            <button type="button" onClick={onCancel} className="p-2 text-[var(--foreground)]/70 hover:bg-black/5 dark:hover:bg-white/10 rounded-lg transition-all"><X size={18} /></button>
            <button type="button" onClick={onSave} disabled={isSaving} className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-500/20">{isSaving ? '...' : 'Guardar Cambios'}</button>
        </div>
    );
}

function ReadingControls({ copied, focusMode, isConfirmingDelete, isEditing, isFormatted, isLight, onCancelDelete, onCopy, onDelete, onEdit, onExport, onFormatProfessional, onToggleFocus, onToggleOutline, onToggleStyleMenu, showOutline, showStyleMenu }: Readonly<{
    copied: CopyStatus;
    focusMode: boolean;
    isConfirmingDelete: boolean;
    isEditing: boolean;
    isFormatted?: boolean;
    isLight: boolean;
    onCancelDelete: () => void;
    onCopy: (mode: CopyMode) => void;
    onDelete?: () => void;
    onEdit: () => void;
    onExport: () => void;
    onFormatProfessional?: () => Promise<void>;
    onToggleFocus: () => void;
    onToggleOutline: () => void;
    onToggleStyleMenu: () => void;
    showOutline: boolean;
    showStyleMenu: boolean;
}>) {
    if (isEditing) return null;
    const outlineTone = showOutline ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20' : getThemeButtonTone(isLight);
    const focusTone = focusMode ? 'bg-amber-500/20 text-amber-400' : getThemeButtonTone(isLight);
    const styleTone = showStyleMenu ? 'bg-indigo-600 text-white shadow-lg' : getThemeButtonTone(isLight);

    return (
        <div className="flex items-center gap-1.5 px-2 py-1.5 bg-white/5 rounded-2xl border border-white/10 shadow-sm">
            <button type="button" onClick={onToggleOutline} className={`p-2 rounded-xl transition-all ${outlineTone}`} title="Esquema del documento"><BookOpen size={16} /></button>
            <CopyControl copied={copied} isLight={isLight} mode="md" onCopy={onCopy} />
            <CopyControl copied={copied} isLight={isLight} mode="plain" onCopy={onCopy} />
            <button type="button" onClick={onToggleFocus} className={`p-2 rounded-xl transition-all ${focusTone}`} title={focusMode ? 'Salir del modo lectura (Esc)' : 'Modo lectura sin distracciones'}>
                {focusMode ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </button>
            <div className="w-px h-4 bg-white/10 mx-0.5" />
            <ProfessionalFormatControl isFormatted={isFormatted} onFormat={onFormatProfessional} />
            <button type="button" onClick={onEdit} className={`p-2 rounded-xl transition-all ${getThemeButtonTone(isLight)}`} title="Editar"><Edit size={16} /></button>
            <div className="w-px h-4 bg-white/10 mx-0.5" />
            <button type="button" onClick={onExport} className={`p-2 rounded-xl transition-all ${getThemeButtonTone(isLight)}`} title="Exportar / Imprimir PDF"><Download size={16} /></button>
            <button type="button" onClick={onToggleStyleMenu} className={`p-2 rounded-xl transition-all relative ${styleTone}`} title="Personalizar Tipografía"><Type size={16} /></button>
            <DeleteControl isConfirming={isConfirmingDelete} onCancel={onCancelDelete} onDelete={onDelete} />
        </div>
    );
}

function ViewerHeader({ copied, date, focusMode, fontFamily, fontSize, isConfirmingDelete, isEditing, isFormatted, isLight, isSaving, nav, onCancel, onCancelDelete, onCopy, onDelete, onEdit, onExport, onFormatProfessional, onSave, onToggleFocus, onToggleOutline, onToggleStyleMenu, readingTime, showOutline, showStyleMenu, title, wordCount, zoomLevel }: Readonly<{
    copied: CopyStatus;
    date: string;
    focusMode: boolean;
    fontFamily: string;
    fontSize: number;
    isConfirmingDelete: boolean;
    isEditing: boolean;
    isFormatted?: boolean;
    isLight: boolean;
    isSaving: boolean;
    nav?: ViewerNav;
    onCancel: () => void;
    onCancelDelete: () => void;
    onCopy: (mode: CopyMode) => void;
    onDelete?: () => void;
    onEdit: () => void;
    onExport: () => void;
    onFormatProfessional?: () => Promise<void>;
    onSave: () => void;
    onToggleFocus: () => void;
    onToggleOutline: () => void;
    onToggleStyleMenu: () => void;
    readingTime: number;
    showOutline: boolean;
    showStyleMenu: boolean;
    title: string;
    wordCount: number;
    zoomLevel: number;
}>) {
    return (
        <div className="flex flex-wrap items-center justify-between p-4 gap-x-8 gap-y-4 border-b border-white/10 sticky top-0 z-20 bg-inherit backdrop-blur-md">
            <DocumentMetadata date={date} fontFamily={fontFamily} isFormatted={isFormatted} readingTime={readingTime} title={title} titleFontSize={Math.round(fontSize * 1.8 * (zoomLevel / 100))} wordCount={wordCount} />
            <div className="flex flex-wrap items-center gap-4 flex-shrink-0 ml-auto">
                <DocumentNavigation nav={nav} />
                <EditingControls isEditing={isEditing} isSaving={isSaving} onCancel={onCancel} onSave={onSave} />
                <ReadingControls
                    copied={copied}
                    focusMode={focusMode}
                    isConfirmingDelete={isConfirmingDelete}
                    isEditing={isEditing}
                    isFormatted={isFormatted}
                    isLight={isLight}
                    onCancelDelete={onCancelDelete}
                    onCopy={onCopy}
                    onDelete={onDelete}
                    onEdit={onEdit}
                    onExport={onExport}
                    onFormatProfessional={onFormatProfessional}
                    onToggleFocus={onToggleFocus}
                    onToggleOutline={onToggleOutline}
                    onToggleStyleMenu={onToggleStyleMenu}
                    showOutline={showOutline}
                    showStyleMenu={showStyleMenu}
                />
            </div>
        </div>
    );
}

function ViewerContent({ content, editedContent, fontFamily, fontSize, isEditing, onEditedContentChange, onScroll, scrollRef, searchQuery, showOutline, zoomLevel }: Readonly<{
    content: string;
    editedContent: string;
    fontFamily: string;
    fontSize: number;
    isEditing: boolean;
    onEditedContentChange: (content: string) => void;
    onScroll: () => void;
    scrollRef: React.RefObject<HTMLElement>;
    searchQuery?: string;
    showOutline: boolean;
    zoomLevel: number;
}>) {
    return (
        <section ref={scrollRef} aria-label="Contenido de la transcripción" onScroll={onScroll} className="flex-1 overflow-y-auto">
            {isEditing ? (
                <div data-color-mode="light" style={{ fontFamily }} className="h-full p-4">
                    <style jsx global>{`
                        .w-md-editor { background-color: transparent !important; border: none !important; }
                        .w-md-editor-toolbar { background-color: rgba(0, 0, 0, 0.1) !important; border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important; }
                        .w-md-editor-content { background-color: transparent !important; }
                        .w-md-editor-area { background-color: transparent !important; color: var(--foreground) !important; }
                    `}</style>
                    <MDEditor value={editedContent} onChange={(value) => onEditedContentChange(value || '')} height="100%" preview="edit" style={{ fontFamily, fontSize: `${fontSize * (zoomLevel / 100)}px` }} />
                </div>
            ) : (
                <div id="markdown-preview" style={{ fontFamily, fontSize: `${fontSize * (zoomLevel / 100)}px` }} className={`max-w-3xl mx-auto px-8 py-8 transition-all duration-300 ${showOutline ? 'ml-64' : ''}`}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={createViewerMarkdownComponents(fontSize, zoomLevel, searchQuery)}>{content}</ReactMarkdown>
                </div>
            )}
        </section>
    );
}

export function MarkdownViewer({ content, onSave, onDelete, onFormatProfessional, nav, title, zoomLevel = 100, isFormatted, searchQuery }: Readonly<Props>) {
    const { themeType } = useBackground();
    const isLight = themeType === 'light';

    // ── Existing state ─────────────────────────────────────────
    const [isEditing, setIsEditing] = useState(false);
    const [editedContent, setEditedContent] = useState(content);
    const [isSaving, setIsSaving] = useState(false);
    const [showStyleMenu, setShowStyleMenu] = useState(false);
    const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);
    const [fontFamily, setFontFamily] = useState<string>('Inter, system-ui, -apple-system, sans-serif');
    const [fontSize, setFontSize] = useState<number>(16);

    // ── New state ──────────────────────────────────────────────
    const [readingProgress, setReadingProgress] = useState(0);
    const [showOutline, setShowOutline] = useState(false);
    const [focusMode, setFocusMode] = useState(false);
    const [copied, setCopied] = useState<CopyStatus>(null);
    const [selMenu, setSelMenu] = useState<SelectionMenu | null>(null);
    const scrollRef = useRef<HTMLElement>(null);

    // Sync editor when navigating between documents
    useEffect(() => { setEditedContent(content); }, [content]);

    // ── Derived data ───────────────────────────────────────────
    const wordCount = useMemo(() => {
        return content
            .replace(/```[\s\S]*?```/g, '')
            .replace(/[#*`>_~[\]!]/g, '')
            .split(/\s+/)
            .filter(Boolean).length;
    }, [content]);

    const readingTime = Math.max(1, Math.ceil(wordCount / 200));

    const headings = useMemo(() => {
        const result: { level: number; text: string; id: string }[] = [];
        content.split('\n').forEach((line) => {
            const m = /^(#{1,3})\s+(.+)/.exec(line);
            if (m) {
                const text = m[2].replace(/[*_`]/g, '').trim();
                result.push({ level: m[1].length, text, id: makeSlug(text) });
            }
        });
        return result;
    }, [content]);

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
                const computedStyle = window.getComputedStyle(el);
                if (computedStyle.position === 'fixed' || computedStyle.position === 'sticky') {
                    const htmlElement = el as HTMLElement;
                    htmlElement.style.position = 'static';
                    htmlElement.style.top = 'auto';
                    htmlElement.style.left = 'auto';
                    htmlElement.style.right = 'auto';
                    htmlElement.style.bottom = 'auto';
                }
            });

            const metaKeywords = [/original:/i, /generad/i, /generado:/i, /transcripci.n:/i, /palabras:/i, /duraci.n:/i];
            const children = Array.from(temp.childNodes);
            for (let index = 0; index < Math.min(children.length, 6); index++) {
                const node = children[index];
                if (node.textContent) {
                    const text = node.textContent.trim();
                    if (text && metaKeywords.some((pattern) => pattern.test(text))) {
                        node.remove();
                    }
                }
            }

            const contentHtml = temp.innerHTML;

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
                const parsedDocument = new DOMParser().parseFromString(html, 'text/html');
                const importedRoot = newWin.document.importNode(parsedDocument.documentElement, true);
                newWin.document.replaceChild(importedRoot, newWin.document.documentElement);
                setTimeout(() => {
                    try {
                        newWin.focus();
                        newWin.print();
                    } catch (error) {
                        console.error('Unable to print the exported document', error);
                    }
                }, 500);
            }
        } catch (err) {
            console.error('Export PDF error:', err);
        }
    };

    // ── New handlers ────────────────────────────────────────────
    const handleScroll = () => {
        if (!scrollRef.current) return;
        const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
        const total = scrollHeight - clientHeight;
        setReadingProgress(total > 0 ? (scrollTop / total) * 100 : 100);
    };

    const copyContent = async (mode: CopyMode) => {
        const text = mode === 'md'
            ? content
            : content
                .replace(/```[\s\S]*?```/g, '')
                .replace(/`[^`]+`/g, '')
                .replace(/[#*_~>`[\]!]/g, '')
                .replace(/\n{3,}/g, '\n\n')
                .trim();
        await navigator.clipboard.writeText(text);
        setCopied(mode);
        setTimeout(() => setCopied(null), 2000);
    };

    const scrollToHeading = (id: string) => {
        document.getElementById(`heading-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    // ── Effects ──────────────────────────────────────────────────
    useEffect(() => {
        const onDown = (e: MouseEvent) => {
            if (!(e.target as HTMLElement).closest('[data-sel-toolbar]')) setSelMenu(null);
        };
        document.addEventListener('mousedown', onDown);
        return () => document.removeEventListener('mousedown', onDown);
    }, []);

    useEffect(() => {
        const scrollContainer = scrollRef.current;
        if (!scrollContainer) return;

        const onSelectionEnd = () => {
            if (isEditing) {
                setSelMenu(null);
                return;
            }
            const selection = window.getSelection();
            const text = selection?.toString().trim() ?? '';
            if (text.length <= 2 || !selection?.rangeCount) {
                setSelMenu(null);
                return;
            }
            const rect = selection.getRangeAt(0).getBoundingClientRect();
            setSelMenu({ x: rect.left + rect.width / 2, y: rect.top, text });
        };

        scrollContainer.addEventListener('mouseup', onSelectionEnd);
        return () => scrollContainer.removeEventListener('mouseup', onSelectionEnd);
    }, [isEditing]);

    useEffect(() => {
        const onKeyDown = (e: KeyboardEvent) => {
            if (isEditing) return;
            const target = e.target as HTMLElement;
            const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;
            if (isInput) return;
            if (e.key === 'ArrowLeft' && nav?.onPrev && nav.hasPrev) nav.onPrev();
            if (e.key === 'ArrowRight' && nav?.onNext && nav.hasNext) nav.onNext?.();
        };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [nav, isEditing]);

    useEffect(() => {
        const onDocClick = (ev: MouseEvent) => {
            if (!showStyleMenu) return;
            if (menuRef.current && !menuRef.current.contains(ev.target as Node)) setShowStyleMenu(false);
        };
        const onEsc = (ev: KeyboardEvent) => {
            if (ev.key === 'Escape') { setShowStyleMenu(false); setShowOutline(false); setFocusMode(false); setSelMenu(null); }
        };
        document.addEventListener('mousedown', onDocClick);
        document.addEventListener('keydown', onEsc);
        return () => {
            document.removeEventListener('mousedown', onDocClick);
            document.removeEventListener('keydown', onEsc);
        };
    }, [showStyleMenu]);

    const extractedDate = extractIsoDate(content);

    const displayTitle = title || 'Última Clase';

    return (
        <div
            className={`flex flex-col glass backdrop-blur-xl border border-white/10 shadow-2xl relative overflow-hidden transition-all duration-300 ${focusMode ? 'fixed inset-2 z-[90] rounded-[1.5rem]' : 'h-full rounded-[2rem]'}`}
            style={{ fontFamily: 'var(--font-geist-sans)', '--zoom-factor': zoomLevel / 100 } as React.CSSProperties}
        >
            {/* ── Reading progress bar ──────────────────────────── */}
            <div className="absolute top-0 left-0 right-0 h-[2px] z-30 bg-white/5 overflow-hidden">
                <div
                    className="h-full bg-gradient-to-r from-indigo-500 via-violet-500 to-pink-500 transition-[width] duration-100"
                    style={{ width: `${readingProgress}%` }}
                />
            </div>

            <SelectionToolbar menu={selMenu} onClose={() => setSelMenu(null)} />
            <OutlinePanel
                headings={headings}
                isVisible={showOutline && !isEditing}
                onClose={() => setShowOutline(false)}
                onSelect={scrollToHeading}
            />
            <StyleMenu
                fontFamily={fontFamily}
                fontSize={fontSize}
                isVisible={showStyleMenu}
                menuRef={menuRef}
                onClose={() => setShowStyleMenu(false)}
                onFontFamilyChange={setFontFamily}
                onFontSizeChange={setFontSize}
            />

            <ViewerHeader
                copied={copied}
                date={extractedDate}
                focusMode={focusMode}
                fontFamily={fontFamily}
                fontSize={fontSize}
                isConfirmingDelete={isConfirmingDelete}
                isEditing={isEditing}
                isFormatted={isFormatted}
                isLight={isLight}
                isSaving={isSaving}
                nav={nav}
                onCancel={handleCancel}
                onCancelDelete={() => setIsConfirmingDelete(false)}
                onCopy={copyContent}
                onDelete={onDelete ? handleDelete : undefined}
                onEdit={() => setIsEditing(true)}
                onExport={handleExportPdf}
                onFormatProfessional={onFormatProfessional}
                onSave={handleSave}
                onToggleFocus={() => setFocusMode(previous => !previous)}
                onToggleOutline={() => setShowOutline(previous => !previous)}
                onToggleStyleMenu={() => setShowStyleMenu(previous => !previous)}
                readingTime={readingTime}
                showOutline={showOutline}
                showStyleMenu={showStyleMenu}
                title={displayTitle}
                wordCount={wordCount}
                zoomLevel={zoomLevel}
            />
            <ViewerContent
                content={content}
                editedContent={editedContent}
                fontFamily={fontFamily}
                fontSize={fontSize}
                isEditing={isEditing}
                onEditedContentChange={setEditedContent}
                onScroll={handleScroll}
                scrollRef={scrollRef}
                searchQuery={searchQuery}
                showOutline={showOutline}
                zoomLevel={zoomLevel}
            />


        </div>
    );
}
