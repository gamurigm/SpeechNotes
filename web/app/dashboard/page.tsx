'use client';
'use client';

import { useState, useEffect } from 'react';
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
        <div className="h-screen flex flex-col bg-gray-100">
            <header className="bg-white shadow-sm p-4 border-b">
                <div className="max-w-7xl mx-auto">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900 mb-2">
                                SpeechNotes - Transcripción en Tiempo Real
                            </h1>
                            <nav className="flex gap-4 text-sm">
                                <a href="/dashboard" className="text-blue-600 font-semibold">
                                    📝 Transcribir
                                </a>
                                <a href="/dashboard/chat" className="text-gray-600 hover:text-blue-600">
                                    💬 Chat con Documentos
                                </a>
                            </nav>
                        </div>
                        <div className="flex items-center gap-2">
                            <RecordingPanel />
                            <LogoutButton />
                        </div>
                    </div>
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden max-w-7xl mx-auto w-full">
                {/* Sidebar izquierda */}
                <aside className="w-80 p-4 space-y-4 overflow-y-auto">
                    <MicTest />
                    <LiveTranscription />
                </aside>

                {/* Panel principal */}
                <main className="flex-1 p-4">
                    {isLoading ? (
                        <div className="h-full flex items-center justify-center">
                            <div className="text-center">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                                <p className="text-gray-500">Cargando...</p>
                            </div>
                        </div>
                    ) : (
                        <div className="h-full flex flex-col">
                            {isProcessing && (
                                <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                                    <div className="flex items-center gap-2">
                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
                                        <span className="text-sm text-yellow-800">
                                            Procesando con DeepSeek... Se actualizará automáticamente
                                        </span>
                                    </div>
                                </div>
                            )}
                            <MarkdownViewer content={latestContent} onSave={handleSave} />
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}
