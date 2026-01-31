import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient } from '@/utils/api-client';
import { getSocket } from '@/utils/socket';

export function useTranscriptionService() {
    const [latestContent, setLatestContent] = useState('');
    const [transcriptionId, setTranscriptionId] = useState<string | null>(null);
    const [transcriptions, setTranscriptions] = useState<Array<{ id: string | null, filename?: string | null, date?: any, is_formatted?: boolean }>>([]);
    const [selectedIndex, setSelectedIndex] = useState<number>(0);
    const [isLoading, setIsLoading] = useState(true);
    const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());

    const loadTranscriptionById = useCallback(async (id: string) => {
        setIsLoading(true);
        try {
            const data = await apiClient.getTranscription(id);
            setLatestContent(data.content);
            setTranscriptionId(data.id);
        } catch (e) {
            console.error('Error loading transcription by id', e);
            setLatestContent('[Error cargando transcripción — reintenta o revisa el backend]');
            setTranscriptionId(null);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const loadTranscriptionsList = useCallback(async () => {
        setIsLoading(true);
        try {
            const res = await apiClient.getTranscriptions();
            const items = res.items || [];
            setTranscriptions(items);

            const savedId = localStorage.getItem('sn-last-doc-id');
            const targetId = savedId && items.find((item: any) => item.id === savedId)
                ? savedId
                : (items.length > 0 ? items[0].id : null);

            if (targetId) {
                const index = items.findIndex((item: any) => item.id === targetId);
                setSelectedIndex(index >= 0 ? index : 0);
                await loadTranscriptionById(targetId);
            } else if (items.length === 0) {
                const latest = await apiClient.getLatestTranscription();
                setLatestContent(latest.content);
                setTranscriptionId(latest.id);
            }
        } catch (e) {
            console.error('Error loading transcriptions list', e);
        } finally {
            setIsLoading(false);
        }
    }, [loadTranscriptionById]);

    const handleSave = async (content: string) => {
        if (!transcriptionId) return;
        await apiClient.updateTranscription(transcriptionId, content);
        setLatestContent(content);
    };

    const handleDelete = async () => {
        if (!transcriptionId) return;
        try {
            await apiClient.deleteTranscription(transcriptionId);
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
            setProcessingIds(prev => new Set(prev).add(jobFakeId));
            setTimeout(async () => {
                await loadTranscriptionsList();
                setProcessingIds(prev => {
                    const next = new Set(prev);
                    next.delete(jobFakeId);
                    return next;
                });
            }, 3000);
        };

        socket.on('recording_stopped', handleRecordingStopped);
        return () => { socket.off('recording_stopped', handleRecordingStopped); };
    }, [loadTranscriptionsList]);

    // Initial load
    useEffect(() => {
        loadTranscriptionsList();
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
