'use client';
'use client';

import { useState, useEffect, useRef } from 'react';
import { Navbar, NavbarBrand, NavbarContent, NavbarItem, Link, Card, CardBody, Spinner, Slider, Button } from "@heroui/react";
import { RecordingPanel } from './components/RecordingPanel';
import LogoutButton from './components/LogoutButton';
import { LiveTranscription } from './components/LiveTranscription';
import { MarkdownViewer } from './components/MarkdownViewer';
import { MicTest } from './components/MicTest';
import { apiClient } from '@/utils/api-client';
import { useRecording } from '@/hooks/useRecording';
import { getSocket } from '@/utils/socket';
import { ZoomIn, Wand2, FileAudio2, SlidersHorizontal, Sparkles, Beaker, Rocket, Check, X } from 'lucide-react';

type ToolbarIconProps = {
    icon: React.ReactNode;
    tooltip: string;
    onClick?: () => void;
    isActive?: boolean;
    className?: string;
};

const ToolbarIcon = ({ icon, tooltip, onClick, isActive, className = '' }: ToolbarIconProps) => {
    const [showTooltip, setShowTooltip] = useState(false);
    return (
        <div className="relative group">
            <button
                onClick={onClick}
                className={`p-2 rounded-lg transition-all duration-300 transform hover:scale-110 hover:-translate-y-1 hover:rotate-3 active:scale-90 ${isActive ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-md hover:shadow-lg' : 'text-slate-500 hover:text-slate-700 hover:bg-gradient-to-br hover:from-slate-50 hover:to-slate-100 shadow-sm hover:shadow-md'} ${className}`}
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
            >
                {icon}
            </button>
            {showTooltip && (
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1.5 bg-slate-800 text-white text-xs font-semibold rounded-lg whitespace-nowrap pointer-events-none z-50 shadow-lg animate-in fade-in slide-in-from-bottom-1 duration-200">
                    {tooltip}
                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-slate-800"></div>
                </div>
            )}
        </div>
    );
};

export default function DashboardPage() {
    const [latestContent, setLatestContent] = useState('');
    const [transcriptionId, setTranscriptionId] = useState<string | null>(null);
    const [transcriptions, setTranscriptions] = useState<Array<{id:string|null, filename?:string|null, date?:any}>>([]);
    const [selectedIndex, setSelectedIndex] = useState<number>(0);
    const [isLoading, setIsLoading] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false);
    const { messages, voiceThreshold, setVoiceThreshold, silenceThreshold, setSilenceThreshold } = useRecording();
    // mdZoom -> zoom applied only to MarkdownViewer (keyboard + Ctrl+Scroll)
    const [mdZoom, setMdZoom] = useState(100);
    // appZoom -> zoom applied to the whole app (controlled by toolbar slider)
    const [appZoom, setAppZoom] = useState(100);
    const [showAppZoomMenu, setShowAppZoomMenu] = useState(false);
    const [activeTool, setActiveTool] = useState<string | null>(null);

    const toggleTool = (tool: string) => {
        setActiveTool(current => current === tool ? null : tool);
    };

    const clampZoom = (v: number) => Math.max(50, Math.min(145, v));

    const handleMdZoom = (level: number) => setMdZoom(clampZoom(level));
    const handleMdZoomIn = () => handleMdZoom(mdZoom + 10);
    const handleMdZoomOut = () => handleMdZoom(mdZoom - 10);

    const handleAppZoom = (level: number) => setAppZoom(clampZoom(level));

    // Keyboard shortcuts: Ctrl/Cmd + +, -, 0, and wheel scroll
    useEffect(() => {
        const handleKeyPress = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && (e.key === '+' || e.key === '=')) {
                e.preventDefault();
                handleMdZoomIn();
            } else if ((e.ctrlKey || e.metaKey) && e.key === '-') {
                e.preventDefault();
                handleMdZoomOut();
            } else if ((e.ctrlKey || e.metaKey) && e.key === '0') {
                e.preventDefault();
                handleMdZoom(100);
            }
        };

        const handleWheel = (e: WheelEvent) => {
            if ((e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                if (e.deltaY < 0) handleMdZoomIn(); else handleMdZoomOut();
            }
        };

        window.addEventListener('keydown', handleKeyPress);
        window.addEventListener('wheel', handleWheel, { passive: false });
        return () => {
            window.removeEventListener('keydown', handleKeyPress);
            window.removeEventListener('wheel', handleWheel);
        };
    }, [mdZoom]);

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

    // Zoom control ref for click-outside
    const zoomRef = useRef<HTMLDivElement | null>(null);

    const currentTitle = extractTitleFromMarkdown(latestContent);

    // Inline ZoomControl: icon on left, panel on right (doesn't overlay)
    const ZoomControl = () => (
        <div ref={zoomRef} className="flex items-start gap-2">
            <button
                onClick={(e) => { e.stopPropagation(); setShowAppZoomMenu((s) => !s); }}
                className={`p-2 rounded-lg transition-all duration-200 ${showAppZoomMenu ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-md' : 'text-slate-500 hover:text-blue-600 hover:bg-slate-50 shadow-sm'}`}
                title="Zoom de la app"
            >
                <ZoomIn size={18} />
            </button>

            {showAppZoomMenu && (
                <div onMouseDown={(e) => e.stopPropagation()} className="bg-white border border-slate-200 rounded-xl shadow-lg p-2 flex flex-col gap-2 min-w-[160px] max-w-[260px]">
                    <div className="flex items-center gap-2 px-1">
                        <input
                            type="range"
                            min={50}
                            max={145}
                            step={1}
                            value={appZoom}
                            onChange={(e) => handleAppZoom(parseInt(e.target.value))}
                            className="w-36 h-2 appearance-none cursor-pointer"
                            style={{ background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((appZoom - 50) / 95) * 100}%, #dbeafe ${((appZoom - 50) / 95) * 100}%, #dbeafe 100%)` }}
                        />
                        <div className="text-sm font-semibold text-blue-600 w-10 text-right">{appZoom}%</div>
                    </div>
                    <div className="text-xs text-slate-500 px-1">Este slider escala toda la aplicación. Ctrl+Scroll controla solo el visor Markdown.</div>
                </div>
            )}
        </div>
    );

    // close AppZoom menu on click outside / Esc
    useEffect(() => {
        const onDocClick = (ev: MouseEvent) => {
            if (!showAppZoomMenu) return;
            if (zoomRef.current && !zoomRef.current.contains(ev.target as Node)) setShowAppZoomMenu(false);
        };
        const onEsc = (ev: KeyboardEvent) => { if (ev.key === 'Escape') setShowAppZoomMenu(false); };
        document.addEventListener('mousedown', onDocClick);
        document.addEventListener('keydown', onEsc);
        return () => {
            document.removeEventListener('mousedown', onDocClick);
            document.removeEventListener('keydown', onEsc);
        };
    }, [showAppZoomMenu]);

    return (
        <div className="h-screen flex flex-col bg-gradient-to-br from-gray-50 to-gray-100 overflow-hidden" style={{ transform: `scale(${appZoom/100})`, transformOrigin: 'top left', width: `${100*(100/appZoom)}%`, height: `${100*(100/appZoom)}%` }}>
            <div className="px-4 pt-4 pb-2 flex justify-center">
                <div className="max-w-7xl w-full flex items-center justify-center gap-6">
                    {/* Left Toolbar - Ultra Minimal */}
                    <div className="flex flex-col gap-2 items-start">
                        <div className="flex items-center gap-2">
                            {/* Zoom - Beautiful Icon */}
                            <div className="flex items-center gap-2">
                                {activeTool === null ? (
                                    <>
                                        <ZoomControl />
                                        <ToolbarIcon 
                                            icon={<Wand2 size={18} />} 
                                            tooltip="Format Markdown" 
                                            onClick={() => toggleTool('format')}
                                            isActive={activeTool === 'format'}
                                        />
                                        <ToolbarIcon 
                                            icon={<FileAudio2 size={18} />} 
                                            tooltip="Transcribe Audio File" 
                                            onClick={() => toggleTool('upload')}
                                            isActive={activeTool === 'upload'}
                                        />
                                        <ToolbarIcon
                                            icon={<SlidersHorizontal size={18} />}
                                            tooltip="Calibrate Audio"
                                            onClick={() => toggleTool('calibrate')}
                                            isActive={activeTool === 'calibrate'}
                                        />
                                    </>
                                ) : (
                                    <>
                                        {activeTool === 'format' && (
                                            <ToolbarIcon
                                                icon={<Wand2 size={18} />}
                                                tooltip="Formato Markdown"
                                                onClick={() => toggleTool('format')}
                                                isActive={true}
                                            />
                                        )}
                                        {activeTool === 'upload' && (
                                            <ToolbarIcon
                                                icon={<FileAudio2 size={18} />}
                                                tooltip="Transcribir Archivo"
                                                onClick={() => toggleTool('upload')}
                                                isActive={true}
                                            />
                                        )}
                                        {activeTool === 'calibrate' && (
                                            <ToolbarIcon
                                                icon={<SlidersHorizontal size={18} />}
                                                tooltip="Calibración"
                                                onClick={() => toggleTool('calibrate')}
                                                isActive={true}
                                            />
                                        )}
                                    </>
                                )}
                            </div>
                        </div>

                        {activeTool === 'calibrate' && (
                            <Card className="w-80 shadow-md border-none">
                                <CardBody className="p-4">
                                    <div className="flex items-center justify-between mb-4">
                                        <h4 className="text-base font-semibold text-gray-800">Calibración de Audio</h4>
                                        <div className="flex items-center gap-1">
                                            <Button 
                                                isIconOnly 
                                                size="sm" 
                                                variant="light" 
                                                className="text-green-600 hover:text-green-700 hover:bg-green-50"
                                                onClick={async () => {
                                                    const payload = { voice_threshold: voiceThreshold, silence_threshold: silenceThreshold };
                                                    const endpoints = ['/api/config/vad', 'http://localhost:8001/api/config/vad'];
                                                    let lastError: any = null;
                                                    let success = false;

                                                    for (const ep of endpoints) {
                                                        try {
                                                            const res = await fetch(ep, {
                                                                method: 'POST',
                                                                headers: { 'Content-Type': 'application/json' },
                                                                body: JSON.stringify(payload)
                                                            });
                                                            if (res.ok) {
                                                                success = true;
                                                                break;
                                                            } else {
                                                                lastError = `HTTP ${res.status} (${ep})`;
                                                            }
                                                        } catch (e) {
                                                            lastError = e;
                                                        }
                                                    }

                                                    if (!success) {
                                                        console.error('[Calibrator] Failed to save VAD config:', lastError);
                                                        alert('Error al guardar configuración de calibración: ' + String(lastError));
                                                        return;
                                                    }

                                                    setActiveTool(null);
                                                    alert('Umbrales guardados correctamente');
                                                }}
                                            >
                                                <Check size={18} />
                                            </Button>
                                            <Button 
                                                isIconOnly 
                                                size="sm" 
                                                variant="light" 
                                                className="text-red-500 hover:text-red-600 hover:bg-red-50"
                                                onClick={() => setActiveTool(null)}
                                            >
                                                <X size={18} />
                                            </Button>
                                        </div>
                                    </div>
                                    
                                    <div className="space-y-4">
                                        <div className="space-y-1">
                                            <Slider
                                                label="Umbral Voz (Inicio)"
                                                size="sm"
                                                step={50}
                                                minValue={100}
                                                maxValue={2000}
                                                value={voiceThreshold}
                                                onChange={(v) => setVoiceThreshold(v as number)}
                                                color="success"
                                                showTooltip={true}
                                            />
                                            <p className="text-xs text-slate-500">RMS para INICIAR grabación — {voiceThreshold} RMS</p>
                                        </div>

                                        <div className="space-y-1">
                                            <Slider
                                                label="Umbral Silencio (Fin)"
                                                size="sm"
                                                step={50}
                                                minValue={50}
                                                maxValue={1000}
                                                value={silenceThreshold}
                                                onChange={(v) => setSilenceThreshold(v as number)}
                                                color="secondary"
                                                showTooltip={true}
                                            />
                                            <p className="text-xs text-slate-500">RMS para DETENER grabación — {silenceThreshold} RMS</p>
                                        </div>
                                    </div>
                                </CardBody>
                            </Card>
                        )}
                    </div>

                    <div className="flex-none">
                        <RecordingPanel />
                    </div>

                    {activeTool === null && (
                        <div className="bg-white border border-slate-200 rounded-md p-1.5 flex gap-1.5 shadow-sm transition-opacity duration-200">
                            <ToolbarIcon icon={<Sparkles size={18} />} tooltip="Ideas" />
                            <ToolbarIcon icon={<Beaker size={18} />} tooltip="Labs" />
                            <ToolbarIcon icon={<Rocket size={18} />} tooltip="Launch" />
                            <ToolbarIcon icon={<Sparkles size={18} />} tooltip="Placeholder" />
                        </div>
                    )}
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
                                zoomLevel={mdZoom}
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
