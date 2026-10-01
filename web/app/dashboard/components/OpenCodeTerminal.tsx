'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { TerminalSquare, Play, Square, Minus, Maximize2, Minimize2, Copy, Check, Loader2 } from 'lucide-react';
import { useOpenCodeTerminal } from '../hooks/useOpenCodeTerminal';

type Props = {
    isOpen: boolean;
    activeDocId?: string;
    activeDocName?: string;
    onDocument: (id: string, content: string) => void;
    onClose: () => void;
};

export function OpenCodeTerminal({ isOpen, activeDocId, activeDocName, onDocument, onClose }: Props) {
    const [expanded, setExpanded] = useState(false);
    const [width, setWidth] = useState(560);
    const [copied, setCopied] = useState(false);
    const drag = useRef<{ x: number; width: number } | null>(null);
    const copyTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const { host, phase, session, error, synced, ready, start, stop } = useOpenCodeTerminal({ isOpen, docId: activeDocId, onDocument });
    const busy = phase !== 'idle';
    const label = busy ? session?.filename || activeDocName : activeDocName;
    const maxWidth = useCallback(() => Math.max(360, Math.min(1000, window.innerWidth - 480)), []);
    const clampWidth = useCallback((value: number) => Math.min(maxWidth(), Math.max(360, value)), [maxWidth]);

    useEffect(() => {
        const adjust = () => setWidth(current => clampWidth(current));
        window.addEventListener('resize', adjust);
        return () => { window.removeEventListener('resize', adjust); if (copyTimer.current) clearTimeout(copyTimer.current); };
    }, [clampWidth]);

    const copyPath = async () => {
        if (!session) return;
        try {
            await navigator.clipboard.writeText(session.workspace);
            setCopied(true);
            if (copyTimer.current) clearTimeout(copyTimer.current);
            copyTimer.current = setTimeout(() => setCopied(false), 2000);
        } catch { setCopied(false); }
    };

    return (
        <aside
            aria-label="Terminal OpenCode"
            aria-hidden={!isOpen}
            className={`opencode-terminal ${!isOpen ? 'hidden' : 'flex'} ${expanded ? 'fixed inset-3 z-[140]' : 'fixed inset-3 z-[120] xl:relative xl:inset-auto xl:z-10 xl:h-full xl:shrink-0 xl:w-[var(--terminal-width)]'} min-h-0 min-w-0 flex-col overflow-hidden rounded-2xl border border-slate-700/70 bg-[#101419] text-slate-200 shadow-xl`}
            style={{ '--terminal-width': `${width}px` } as React.CSSProperties}
        >
            {!expanded && <div
                role="separator" tabIndex={isOpen ? 0 : -1} aria-label="Ajustar ancho de la terminal"
                aria-orientation="vertical" aria-valuemin={360} aria-valuemax={1000} aria-valuenow={width}
                className="absolute inset-y-0 left-0 z-20 hidden w-2 cursor-col-resize touch-none hover:bg-emerald-400/20 focus-visible:bg-emerald-400/30 xl:block"
                onPointerDown={event => { drag.current = { x: event.clientX, width }; event.currentTarget.setPointerCapture(event.pointerId); }}
                onPointerMove={event => { if (drag.current) setWidth(clampWidth(drag.current.width + drag.current.x - event.clientX)); }}
                onPointerUp={event => { drag.current = null; event.currentTarget.releasePointerCapture(event.pointerId); }}
                onPointerCancel={() => { drag.current = null; }}
                onKeyDown={event => {
                    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
                    event.preventDefault();
                    setWidth(current => clampWidth(event.key === 'Home' ? 360 : event.key === 'End' ? maxWidth() : current + (event.key === 'ArrowLeft' ? 24 : -24)));
                }}
            />}
            <header className="flex flex-wrap items-center gap-2 border-b border-slate-700/60 px-4 py-3">
                <TerminalSquare size={18} className="shrink-0 text-emerald-300" />
                <div className="min-w-0 flex-1">
                    <h2 className="text-sm font-semibold">OpenCode</h2>
                    <p className="truncate text-xs text-slate-400" title={label || ''}>{label || 'Selecciona una nota para comenzar'}</p>
                </div>
                <div className="flex shrink-0 items-center gap-1">
                    {busy ? <button type="button" onClick={stop} disabled={phase === 'stopping'} aria-label="Detener OpenCode" title="Detener OpenCode" className="terminal-control hover:text-rose-300"><Square size={15} /></button>
                        : <button type="button" onClick={() => void start()} disabled={!activeDocId || !ready} aria-label="Iniciar OpenCode" title="Iniciar OpenCode" className="terminal-control"><Play size={16} /></button>}
                    <button type="button" onClick={() => setExpanded(value => !value)} aria-label={expanded ? 'Restaurar tamaño' : 'Ampliar terminal'} title={expanded ? 'Restaurar tamaño' : 'Ampliar terminal'} className="terminal-control">{expanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}</button>
                    <button type="button" onClick={onClose} aria-label="Ocultar terminal" title="Ocultar; OpenCode continúa activo" className="terminal-control"><Minus size={17} /></button>
                </div>
            </header>
            <div className="relative min-h-0 flex-1">
                <div ref={host} className="absolute inset-0 p-3" />
                {!busy && !session && <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-[#101419] px-6 text-center">
                    <TerminalSquare size={32} className="text-slate-500" />
                    <div className="max-w-sm space-y-2">
                        <p className="text-sm font-medium">Trabaja directamente sobre tu nota</p>
                        <p className="text-sm leading-relaxed text-slate-400">Pide a OpenCode que edite <span className="font-mono text-emerald-200">@document.md</span>. Los cambios aparecerán en el visor.</p>
                    </div>
                    <button type="button" onClick={() => void start()} disabled={!activeDocId || !ready} className="flex min-h-10 items-center gap-2 rounded-lg bg-emerald-300 px-4 text-sm font-semibold text-slate-950 transition hover:bg-emerald-200 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-emerald-300 disabled:cursor-not-allowed disabled:opacity-40"><Play size={16} /> Iniciar OpenCode</button>
                </div>}
                {phase === 'starting' && <div role="status" className="absolute right-3 top-3 flex items-center gap-2 rounded-md bg-slate-800/90 px-3 py-2 text-xs"><Loader2 size={14} className="animate-spin" /> Abriendo OpenCode…</div>}
            </div>
            {error && <p role="alert" className="border-t border-amber-300/20 bg-amber-300/5 px-4 py-3 text-xs leading-relaxed text-amber-200">{error}</p>}
            <footer className="flex min-h-10 flex-wrap items-center gap-2 border-t border-slate-700/60 px-4 py-2 text-[11px] text-slate-400">
                <span role="status" className="flex flex-1 items-center gap-1.5">
                    {synced && <Check size={12} className="text-emerald-300" />}
                    {phase === 'running' ? (synced ? 'Nota sincronizada' : 'Conectado · document.md') : phase === 'starting' ? 'Conectando…' : phase === 'stopping' ? 'Deteniendo…' : 'Terminal detenida'}
                </span>
                {busy && session?.docId !== activeDocId && <span>Detén la sesión para cambiar de nota</span>}
                {session && <button type="button" onClick={() => void copyPath()} title={session.workspace} aria-label="Copiar carpeta de la nota y su respaldo" className="flex items-center gap-1.5 rounded px-2 py-1 hover:bg-slate-800 hover:text-white focus-visible:outline-2 focus-visible:outline-emerald-300">{copied ? <Check size={12} /> : <Copy size={12} />} {copied ? 'Copiado' : 'Carpeta'}</button>}
            </footer>
            <style jsx>{`
                .terminal-control { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 6px; color: #94a3b8; }
                .terminal-control:hover { background: #1e293b; color: #f1f5f9; }
                .terminal-control:focus-visible { outline: 2px solid #6ee7b7; outline-offset: 2px; }
                .terminal-control:disabled { opacity: .35; cursor: not-allowed; }
            `}</style>
        </aside>
    );
}
