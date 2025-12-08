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
    const [isLoading, setIsLoading] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false);
    const { messages } = useRecording();

    useEffect(() => {
        loadLatestTranscription();

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

            // Wait a bit for processing, then reload
            setTimeout(() => {
                loadLatestTranscription();
                setIsProcessing(false);
            }, 3000);
        });

        return () => {
            socket.off('recording_stopped');
        };
    }, [messages]);

    const loadLatestTranscription = async () => {
        const maxRetries = 3;
        let attempt = 0;
        let lastErr: any = null;

        setIsLoading(true);
        while (attempt < maxRetries) {
            try {
                const data = await apiClient.getLatestTranscription();
                setLatestContent(data.content);
                setTranscriptionId(data.id);
                lastErr = null;
                break;
            } catch (error) {
                lastErr = error;
                console.warn(`loadLatestTranscription attempt ${attempt + 1} failed:`, error);
                attempt += 1;
                // exponential backoff
                await new Promise(res => setTimeout(res, 1000 * Math.pow(2, attempt)));
            }
        }

        if (lastErr) {
            console.error('Error loading transcription after retries:', lastErr);
            setLatestContent('[Error cargando transcripción — reintenta o revisa el backend]');
            setTranscriptionId(null);
        }

        setIsLoading(false);
    };

    const handleSave = async (content: string) => {
        if (!transcriptionId) {
            alert('No hay transcripción para guardar');
            return;
        }

        await apiClient.updateTranscription(transcriptionId, content);
        setLatestContent(content);
    };

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
                            <MarkdownViewer content={latestContent} onSave={handleSave} />
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}
