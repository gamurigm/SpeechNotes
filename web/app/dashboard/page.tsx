'use client';
'use client';

import { useState, useEffect } from 'react';
import { Navbar, NavbarBrand, NavbarContent, NavbarItem, Link, Card, CardBody, Spinner } from "@heroui/react";
import { RecordingPanel } from './components/RecordingPanel';
import LogoutButton from './components/LogoutButton';
import { LiveTranscription } from './components/LiveTranscription';
import { MarkdownViewer } from './components/MarkdownViewer';
import { MicTest } from './components/MicTest';
import { apiClient } from '@/utils/api-client';
import { useRecording } from '@/hooks/useRecording';
import { getSocket } from '@/utils/socket';

export default function DashboardPage() {
    const [latestContent, setLatestContent] = useState('');
    const [transcriptionId, setTranscriptionId] = useState<string | null>(null);
    const [transcriptions, setTranscriptions] = useState<Array<{id:string|null, filename?:string|null, date?:any}>>([]);
    const [selectedIndex, setSelectedIndex] = useState<number>(0);
    const [isLoading, setIsLoading] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false);
    const { messages } = useRecording();

    useEffect(() => {
        // load list + latest selected transcription
        (async () => {
            await loadTranscriptionsList();
        })();

        // Listen for recording stopped event
        const socket = getSocket();
        socket.on('recording_stopped', (data) => {
            console.log('[Dashboard] Recording stopped:', data);

            // Show raw transcription immediately
            const rawContent = messages.map(msg =>
                `**${msg.timestamp}**\n${msg.text}`
            ).join('\n\n');

            setLatestContent(rawContent || '[Procesando transcripción...]');
            setIsProcessing(true);

            // Wait a bit for processing, then reload list and selected transcription
            setTimeout(async () => {
                await loadTranscriptionsList();
                setIsProcessing(false);
            }, 3000);
        });

        return () => {
            socket.off('recording_stopped');
        };
    }, [messages]);

    const loadTranscriptionsList = async () => {
        setIsLoading(true);
        try {
            const res = await apiClient.getTranscriptions();
            const items = res.items || [];
            setTranscriptions(items);

            if (items.length > 0) {
                // default to first (most recent)
                setSelectedIndex(0);
                const firstId = items[0].id;
                if (firstId) await loadTranscriptionById(firstId);
            } else {
                // fallback to latest endpoint
                const latest = await apiClient.getLatestTranscription();
                setLatestContent(latest.content);
                setTranscriptionId(latest.id);
            }
        } catch (e) {
            console.error('Error loading transcriptions list', e);
        } finally {
            setIsLoading(false);
        }
    };

    const loadTranscriptionById = async (id: string) => {
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
    };

    const handleSave = async (content: string) => {
        if (!transcriptionId) {
            alert('No hay transcripción para guardar');
            return;
        }

        await apiClient.updateTranscription(transcriptionId, content);
        setLatestContent(content);
    };

    const handlePrev = async () => {
        if (selectedIndex > 0) {
            const nextIndex = selectedIndex - 1;
            setSelectedIndex(nextIndex);
            const id = transcriptions[nextIndex].id;
            if (id) await loadTranscriptionById(id);
        }
    };

    const handleNext = async () => {
        if (selectedIndex < transcriptions.length - 1) {
            const nextIndex = selectedIndex + 1;
            setSelectedIndex(nextIndex);
            const id = transcriptions[nextIndex].id;
            if (id) await loadTranscriptionById(id);
        }
    };

    const extractTitleFromMarkdown = (md: string) => {
        if (!md) return 'Última Clase';
        // Try to find the first markdown heading (#, ##, ###)
        const headingMatch = md.match(/^#{1,3}\s*(.+)$/m);
        if (headingMatch && headingMatch[1]) {
            return headingMatch[1].trim();
        }
        // Fallback: look for "Transcripción: YYYY-MM-DD"
        const transMatch = md.match(/Transcripci[oó]n:\s*(\d{4}-\d{2}-\d{2})/i);
        if (transMatch && transMatch[1]) return `Transcripción: ${transMatch[1]}`;
        return 'Última Clase';
    };

    const currentTitle = extractTitleFromMarkdown(latestContent);

    return (
        <div className="h-screen flex flex-col bg-gradient-to-br from-gray-50 to-gray-100 overflow-hidden">
            <div className="px-4 pt-4 pb-2 flex justify-center">
                <div className="max-w-xl w-full">
                    <RecordingPanel />
                </div>
            </div>
            
            <div className="flex-1 flex overflow-hidden max-w-7xl mx-auto w-full">
                {/* Sidebar izquierda */}
                <aside className="w-80 p-4 space-y-4 overflow-y-auto">
                    <MicTest />
                    <LiveTranscription />
                </aside>

                {/* Panel principal */}
                <main className="flex-1 p-4 flex flex-col overflow-y-auto">
                    {isLoading ? (
                        <Card className="h-full shadow-lg">
                            <CardBody className="flex items-center justify-center">
                                <div className="text-center space-y-4">
                                    <Spinner size="lg" color="primary" />
                                    <p className="text-gray-500 font-medium">Cargando transcripción...</p>
                                </div>
                            </CardBody>
                        </Card>
                    ) : (
                        <div className="h-full flex flex-col">
                            {isProcessing && (
                                <Card className="mb-4 bg-gradient-to-r from-yellow-50 to-amber-50 border-yellow-200 shadow-md">
                                    <CardBody className="py-3">
                                        <div className="flex items-center gap-3">
                                            <Spinner size="sm" color="warning" />
                                            <span className="text-sm text-yellow-900 font-medium">
                                                Procesando con DeepSeek... Se actualizará automáticamente
                                            </span>
                                        </div>
                                    </CardBody>
                                </Card>
                            )}
                            <MarkdownViewer
                                title={currentTitle}
                                content={latestContent}
                                onSave={handleSave}
                                nav={{
                                    onPrev: handlePrev,
                                    onNext: handleNext,
                                    hasPrev: selectedIndex > 0,
                                    hasNext: selectedIndex < transcriptions.length - 1,
                                    index: selectedIndex,
                                    total: transcriptions.length
                                }}
                            />
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}
