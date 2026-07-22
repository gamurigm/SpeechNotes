import { useState, useEffect, useRef, useCallback } from 'react';
import { ApiClient } from '@/services/ApiClient';
import { getSocket } from '@/utils/socket';

type TranscriptionSummary = {
    id: string | null;
    filename?: string | null;
    date?: string | null;
    is_formatted?: boolean;
};

type TranscriptionDocument = {
    id: string;
    content: string;
};

type TranscriptionsResponse = {
    items?: TranscriptionSummary[];
};

export function useTranscriptionService() {
    const [latestContent, setLatestContent] = useState('');
    const [transcriptionId, setTranscriptionId] = useState<string | null>(null);
    const [transcriptions, setTranscriptions] = useState<TranscriptionSummary[]>([]);
    const [selectedIndex, setSelectedIndex] = useState<number>(0);
    const [isLoading, setIsLoading] = useState(true);
    const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());
    const pendingRecordingJobIdRef = useRef<string | null>(null);

    const loadTranscriptionById = useCallback(async (id: string) => {
        setIsLoading(true);
        try {
            const data = await ApiClient.getInstance().getTranscription(id) as TranscriptionDocument;
            setLatestContent(data.content);
            setTranscriptionId(data.id);
        } catch (e) {
            console.error('Error loading transcription by id', e);
            setLatestContent('[Error cargando transcripcion - reintenta o revisa el backend]');
            setTranscriptionId(null);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const loadTranscriptionsList = useCallback(async () => {
        setIsLoading(true);
        try {
            const res = await ApiClient.getInstance().listTranscriptions() as TranscriptionsResponse;
            const items = res?.items || [];
            setTranscriptions(items);

            const savedId = localStorage.getItem('sn-last-doc-id');
            let targetId: string | null = null;
            if (savedId && items.some((item) => item.id === savedId)) {
                targetId = savedId;
            } else if (items.length > 0) {
                targetId = items[0].id;
            }

            if (targetId) {
                const index = items.findIndex((item) => item.id === targetId);
                setSelectedIndex(index >= 0 ? index : 0);
                await loadTranscriptionById(targetId);
            } else if (items.length === 0) {
                const latest = await ApiClient.getInstance().getLatestTranscription() as TranscriptionDocument | null;
                if (latest) {
                    setLatestContent(latest.content);
                    setTranscriptionId(latest.id);
                }
            }
        } catch (e) {
            console.error('Error loading transcriptions list', e);
        } finally {
            setIsLoading(false);
        }
    }, [loadTranscriptionById]);

    const handleSave = async (content: string) => {
        if (!transcriptionId) return;
        await ApiClient.getInstance().updateTranscription(transcriptionId, content);
        setLatestContent(content);
    };

    const handleDelete = async () => {
        if (!transcriptionId) return;
        try {
            await ApiClient.getInstance().deleteTranscription(transcriptionId);
            setTranscriptionId(null);
            setSelectedIndex(0);
            await loadTranscriptionsList();
            return { success: true, message: 'Clase eliminada correctamente' };
        } catch (e) {
            console.error('Error deleting transcription', e);
            return { success: false, message: 'Error al intentar eliminar la clase' };
        }
    };

    // Socket listeners for background updates
    useEffect(() => {
        const socket = getSocket();

        const handleRecordingStopped = () => {
            const jobFakeId = `temp-${Date.now()}`;
            pendingRecordingJobIdRef.current = jobFakeId;
            setProcessingIds(prev => new Set(prev).add(jobFakeId));
        };

        const handleProcessingComplete = async (data: unknown) => {
            console.log('[Socket.IO] Processing complete:', data);
            await loadTranscriptionsList();
            const pendingId = pendingRecordingJobIdRef.current;
            if (pendingId) {
                setProcessingIds(prev => {
                    const next = new Set(prev);
                    next.delete(pendingId);
                    return next;
                });
                pendingRecordingJobIdRef.current = null;
            }
        };
        const handleRecordingIssue = () => {
            const pendingId = pendingRecordingJobIdRef.current;
            if (!pendingId) return;
            setProcessingIds(prev => {
                const next = new Set(prev);
                next.delete(pendingId);
                return next;
            });
            pendingRecordingJobIdRef.current = null;
        };

        socket.on('recording_stopped', handleRecordingStopped);
        socket.on('processing_complete', handleProcessingComplete);
        socket.on('warning', handleRecordingIssue);
        socket.on('error', handleRecordingIssue);

        return () => {
            socket.off('recording_stopped', handleRecordingStopped);
            socket.off('processing_complete', handleProcessingComplete);
            socket.off('warning', handleRecordingIssue);
            socket.off('error', handleRecordingIssue);
        };
    }, [loadTranscriptionsList]);

    // Initial load
    useEffect(() => {
        const timer = window.setTimeout(() => {
            void loadTranscriptionsList();
        }, 0);
        return () => window.clearTimeout(timer);
    }, [loadTranscriptionsList]);

    // Persistence
    useEffect(() => {
        if (transcriptionId) {
            localStorage.setItem('sn-last-doc-id', transcriptionId);
        }
    }, [transcriptionId]);

    const navigateTo = useCallback(async (index: number) => {
        if (index >= 0 && index < transcriptions.length) {
            setSelectedIndex(index);
            const id = transcriptions[index].id;
            if (id) await loadTranscriptionById(id);
        }
    }, [transcriptions, loadTranscriptionById]);

    return {
        latestContent,
        setLatestContent,
        transcriptionId,
        transcriptions,
        selectedIndex,
        isLoading,
        processingIds,
        setProcessingIds,
        loadTranscriptionsList,
        loadTranscriptionById,
        handleSave,
        handleDelete,
        navigateTo,
        setSelectedIndex
    };
}
