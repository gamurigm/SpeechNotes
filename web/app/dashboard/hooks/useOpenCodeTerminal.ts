'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { Terminal } from '@xterm/xterm';
import type { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';

type Options = {
    isOpen: boolean;
    docId?: string;
    onDocument: (id: string, content: string) => void;
};
type Phase = 'idle' | 'starting' | 'running' | 'stopping';
type Session = { id: string; token: string; workspace: string; filename?: string; docId: string };

export function useOpenCodeTerminal({ isOpen, docId, onDocument }: Options) {
    const host = useRef<HTMLDivElement>(null);
    const terminal = useRef<Terminal | null>(null);
    const fit = useRef<FitAddon | null>(null);
    const socket = useRef<WebSocket | null>(null);
    const sessionRef = useRef<Session | null>(null);
    const abort = useRef<AbortController | null>(null);
    const mounted = useRef(false);
    const notify = useRef(onDocument);
    const [phase, setPhase] = useState<Phase>('idle');
    const [session, setSession] = useState<Session | null>(null);
    const [error, setError] = useState('');
    const [synced, setSynced] = useState(false);
    const [ready, setReady] = useState(false);

    useEffect(() => { notify.current = onDocument; }, [onDocument]);

    const resize = useCallback(() => {
        if (!host.current?.clientWidth || !host.current.clientHeight || !terminal.current) return;
        fit.current?.fit();
        if (socket.current?.readyState === WebSocket.OPEN) {
            socket.current.send(JSON.stringify({ type: 'resize', cols: terminal.current.cols, rows: terminal.current.rows }));
        }
    }, []);

    useEffect(() => {
        mounted.current = true;
        let disposed = false;
        let observer: ResizeObserver | undefined;
        let instance: Terminal | undefined;
        void Promise.all([import('@xterm/xterm'), import('@xterm/addon-fit')]).then(([xterm, addon]) => {
            if (disposed || !host.current) return;
            instance = new xterm.Terminal({
                fontFamily: 'Cascadia Code, Consolas, monospace', fontSize: 13,
                cursorBlink: true, screenReaderMode: true, scrollback: 4000,
                theme: { background: '#101419', foreground: '#d5dce5', cursor: '#6ee7b7', selectionBackground: '#334155' },
            });
            const fitAddon = new addon.FitAddon();
            instance.loadAddon(fitAddon);
            instance.open(host.current);
            terminal.current = instance;
            fit.current = fitAddon;
            instance.onData(data => {
                if (socket.current?.readyState === WebSocket.OPEN) socket.current.send(JSON.stringify({ type: 'input', data }));
            });
            observer = new ResizeObserver(resize);
            observer.observe(host.current);
            resize();
            setReady(true);
        }).catch(() => { if (!disposed) setError('No se pudo cargar la terminal. Recarga la página.'); });
        return () => {
            disposed = true;
            mounted.current = false;
            abort.current?.abort();
            socket.current?.close();
            const active = sessionRef.current;
            if (active) void fetch(`/api/opencode/sessions/${active.id}`, { method: 'DELETE', keepalive: true });
            observer?.disconnect();
            instance?.dispose();
            terminal.current = null;
            fit.current = null;
        };
    }, [resize]);

    useEffect(() => {
        if (!isOpen || !ready) return;
        const frame = requestAnimationFrame(() => { resize(); terminal.current?.focus(); });
        return () => cancelAnimationFrame(frame);
    }, [isOpen, ready, resize]);

    const start = async () => {
        if (!docId || !terminal.current || phase !== 'idle') return;
        setPhase('starting'); setError(''); setSynced(false);
        terminal.current.reset();
        const controller = new AbortController();
        abort.current = controller;
        try {
            const response = await fetch('/api/opencode/sessions', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ doc_id: docId }), signal: controller.signal,
            });
            const data = await response.json();
            if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'No se pudo abrir OpenCode.');
            const active: Session = { ...data, docId };
            if (!mounted.current || controller.signal.aborted) {
                void fetch(`/api/opencode/sessions/${active.id}`, { method: 'DELETE' });
                return;
            }
            setSession(active); sessionRef.current = active;
            const backendPort = process.env.NEXT_PUBLIC_TERMINAL_BACKEND_PORT || '9443';
            const ws = new WebSocket(`ws://${window.location.hostname}:${backendPort}/api/opencode/sessions/${active.id}/ws`);
            socket.current = ws;
            ws.onopen = () => {
                fit.current?.fit();
                // Authentication must be the first frame, ahead of resize/input.
                ws.send(JSON.stringify({ token: active.token, cols: terminal.current?.cols || 80, rows: terminal.current?.rows || 24 }));
                terminal.current?.focus();
            };
            ws.onmessage = event => {
                const message = JSON.parse(event.data);
                if (message.type === 'output') terminal.current?.write(message.data);
                if (message.type === 'ready') { setPhase('running'); resize(); }
                if (message.type === 'document') { notify.current(message.doc_id, message.content); setSynced(true); }
                if (message.type === 'error' || message.type === 'conflict') setError(message.message);
            };
            ws.onerror = () => setError('No se pudo conectar la terminal al backend local.');
            ws.onclose = () => {
                if (!mounted.current || socket.current !== ws) return;
                socket.current = null;
                sessionRef.current = null;
                setPhase('idle');
                terminal.current?.writeln('\r\n\x1b[90mSesión finalizada. Puedes volver a iniciar OpenCode.\x1b[0m');
            };
        } catch (failure) {
            if (!mounted.current) return;
            if (!controller.signal.aborted) setError(failure instanceof Error ? failure.message : 'No se pudo iniciar OpenCode.');
            setPhase('idle');
        }
    };

    const stop = () => {
        abort.current?.abort();
        const ws = socket.current;
        if (ws?.readyState === WebSocket.OPEN) {
            setPhase('stopping'); ws.send(JSON.stringify({ type: 'stop' }));
        } else {
            ws?.close(); setPhase('idle');
            const active = sessionRef.current;
            if (active) void fetch(`/api/opencode/sessions/${active.id}`, { method: 'DELETE' });
        }
    };

    return { host, phase, session, error, synced, ready, start, stop, resize };
}
