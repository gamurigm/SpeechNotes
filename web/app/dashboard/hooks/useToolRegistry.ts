import { useState, useRef } from 'react';
import { ToastType } from '../components/Toast';

interface ToolRegistryProps {
    transcriptionId: string | null;
    transcriptions: any[];
    selectedIndex: number;
    setProcessingIds: (updater: (prev: Set<string>) => Set<string>) => void;
    loadTranscriptionById: (id: string) => Promise<void>;
    loadTranscriptionsList: () => Promise<void>;
    setNotification: (notif: { message: string, type: ToastType } | null) => void;
}

export function useToolRegistry({
    transcriptionId,
    transcriptions,
    selectedIndex,
    setProcessingIds,
    loadTranscriptionById,
    loadTranscriptionsList,
    setNotification
}: ToolRegistryProps) {
    const [activeTool, setActiveTool] = useState<string | null>(null);
    const [uploadFileName, setUploadFileName] = useState<string | null>(null);
    const uploadInputRef = useRef<HTMLInputElement | null>(null);

    const toggleTool = (tool: string) => {
        setActiveTool(current => current === tool ? null : tool);
    };

    const handleAutoFormat = async () => {
        if (!transcriptionId || !transcriptions[selectedIndex]?.filename) return;

        const currentId = transcriptionId;
        setProcessingIds(prev => new Set(prev).add(currentId));

        try {
            const filename = transcriptions[selectedIndex].filename;
            const res = await fetch('/api/format/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': 'dev-secret-api-key'
                },
                body: JSON.stringify({
                    files: [`notas/${filename}`],
                    output_dir: 'notas'
                })
            });

            if (!res.ok) throw new Error('Failed to start formatting');
            const { job_id, ws_url } = await res.json();

            const ws = new WebSocket(`ws://127.0.0.1:9443/api/format${ws_url}`);
            ws.onmessage = async (event) => {
                const data = JSON.parse(event.data);
                if (data.status === 'job_completed' || data.status === 'completed') {
                    setNotification({ message: 'Formateo completado con éxito', type: 'success' });
                    if (transcriptionId === currentId) await loadTranscriptionById(currentId);
                    await loadTranscriptionsList();
                    setProcessingIds(prev => {
                        const next = new Set(prev);
                        next.delete(currentId);
                        return next;
                    });
                    if (activeTool === 'format') setActiveTool(null);
                    ws.close();
                } else if (data.status === 'error') {
                    setNotification({ message: `Error: ${data.error}`, type: 'error' });
                    setProcessingIds(prev => {
                        const next = new Set(prev);
                        next.delete(currentId);
                        return next;
                    });
                    ws.close();
                }
            };
        } catch (e) {
            console.error('Error in auto-format:', e);
            setNotification({ message: 'Error al iniciar el formateo', type: 'error' });
            setProcessingIds(prev => {
                const next = new Set(prev);
                next.delete(currentId);
                return next;
            });
        }
    };

    const handleUpload = async () => {
        const file = uploadInputRef.current?.files?.[0];
        if (!file) return;

        const fd = new FormData();
        fd.append('file', file);
        const uploadJobId = `upload-${file.name}`;
        setProcessingIds(prev => new Set(prev).add(uploadJobId));

        try {
            await fetch('/api/transcribe-file', { method: 'POST', body: fd, headers: { 'x-api-key': 'dev-secret-api-key' } });
            setTimeout(async () => {
                await loadTranscriptionsList();
                setProcessingIds(prev => {
                    const next = new Set(prev);
                    next.delete(uploadJobId);
                    return next;
                });
                setActiveTool(null);
                setUploadFileName(null);
            }, 2000);
        } catch (e) {
            console.error("Upload failed", e);
            setProcessingIds(prev => {
                const next = new Set(prev);
                next.delete(uploadJobId);
                return next;
            });
        }
    };

    return {
        activeTool,
        setActiveTool,
        toggleTool,
        handleAutoFormat,
        handleUpload,
        uploadFileName,
        setUploadFileName,
        uploadInputRef
    };
}
