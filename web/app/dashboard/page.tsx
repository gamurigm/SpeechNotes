'use client';

import { useState, useEffect, useRef } from 'react';
import { Navbar, NavbarBrand, NavbarContent, NavbarItem, Link, Card, CardBody, Spinner, Slider, Button } from "@heroui/react";
import { RecordingPanel } from './components/RecordingPanel';
import LogoutButton from './components/LogoutButton';
import { LiveTranscription } from './components/LiveTranscription';
import { MarkdownViewer } from './components/MarkdownViewer';
import { MicTest } from './components/MicTest';
import { ChatSidebar } from './components/ChatSidebar';
import { apiClient } from '@/utils/api-client';
import { useRecording } from '@/hooks/useRecording';
import { getSocket } from '@/utils/socket';
import { ZoomIn, Wand2, FileAudio2, SlidersHorizontal, Sparkles, Beaker, Rocket, Check, X, MessageCircle, PanelRightClose, PanelRightOpen } from 'lucide-react';

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
    const [transcriptions, setTranscriptions] = useState<Array<{ id: string | null, filename?: string | null, date?: any }>>([]);
    const [selectedIndex, setSelectedIndex] = useState<number>(0);
    const [isLoading, setIsLoading] = useState(true);
    const [isProcessing, setIsProcessing] = useState(false);
    const { messages, voiceThreshold, setVoiceThreshold, silenceThreshold, setSilenceThreshold } = useRecording();
    const [mdZoom, setMdZoom] = useState(100);
    const [appZoom, setAppZoom] = useState(100);
    const [showAppZoomMenu, setShowAppZoomMenu] = useState(false);
    const [activeTool, setActiveTool] = useState<string | null>(null);
    const [showChat, setShowChat] = useState(false);
    const [isChatExpanded, setIsChatExpanded] = useState(false);
    const [showSidebar, setShowSidebar] = useState(true);

    const toggleTool = (tool: string) => {
        setActiveTool(current => current === tool ? null : tool);
    };

    const clampZoom = (v: number) => Math.max(50, Math.min(145, v));
    const handleMdZoom = (level: number) => setMdZoom(clampZoom(level));
    const handleMdZoomIn = () => handleMdZoom(mdZoom + 10);
    const handleMdZoomOut = () => handleMdZoom(mdZoom - 10);
    const handleAppZoom = (level: number) => setAppZoom(clampZoom(level));

    useEffect(() => {
        const handleKeyPress = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && (e.key === '+' || e.key === '=')) {
                e.preventDefault(); handleMdZoomIn();
            } else if ((e.ctrlKey || e.metaKey) && e.key === '-') {
                e.preventDefault(); handleMdZoomOut();
            } else if ((e.ctrlKey || e.metaKey) && e.key === '0') {
                e.preventDefault(); handleMdZoom(100);
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
        loadTranscriptionsList();
        const socket = getSocket();
        socket.on('recording_stopped', (data) => {
            const rawContent = messages.map(msg => `**${msg.timestamp}**\n${msg.text}`).join('\n\n');
            setLatestContent(rawContent || '[Procesando transcripción...]');
            setIsProcessing(true);
            setTimeout(async () => {
                await loadTranscriptionsList();
                setIsProcessing(false);
            }, 3000);
        });
        return () => { socket.off('recording_stopped'); };
    }, [messages]);

    const loadTranscriptionsList = async () => {
        setIsLoading(true);
        try {
            const res = await apiClient.getTranscriptions();
            const items = res.items || [];
            setTranscriptions(items);
            if (items.length > 0) {
                setSelectedIndex(0);
                const firstId = items[0].id;
                if (firstId) await loadTranscriptionById(firstId);
            } else {
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
        if (!transcriptionId) return;
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
        const headingMatch = md.match(/^#{1,3}\s*(.+)$/m);
        if (headingMatch && headingMatch[1]) return headingMatch[1].trim();
        const transMatch = md.match(/Transcripci[oó]n:\s*(\d{4}-\d{2}-\d{2})/i);
        if (transMatch && transMatch[1]) return `Transcripción: ${transMatch[1]}`;
        return 'Última Clase';
    };

    const zoomRef = useRef<HTMLDivElement | null>(null);
    const uploadInputRef = useRef<HTMLInputElement | null>(null);
    const [uploadFileName, setUploadFileName] = useState<string | null>(null);
    const currentTitle = extractTitleFromMarkdown(latestContent);

    const ZoomControl = () => (
        <div ref={zoomRef} className="flex items-start gap-2">
            <button
                onClick={(e) => { e.stopPropagation(); setShowAppZoomMenu((s) => !s); }}
                className={`p-2 rounded-lg transition-all duration-200 ${showAppZoomMenu ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-md' : 'text-slate-500 hover:text-blue-600 hover:bg-slate-50 shadow-sm'}`}
            >
                <ZoomIn size={18} />
            </button>
            {showAppZoomMenu && (
                <div onMouseDown={(e) => e.stopPropagation()} className="bg-white border border-slate-200 rounded-xl shadow-lg p-2 flex flex-col gap-2 min-w-[160px]">
                    <div className="flex items-center gap-2 px-1">
                        <input
                            type="range" min={50} max={145} step={1}
                            value={appZoom}
                            onChange={(e) => handleAppZoom(parseInt(e.target.value))}
                            className="w-36 h-2 appearance-none cursor-pointer"
                            style={{ background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((appZoom - 50) / 95) * 100}%, #dbeafe ${((appZoom - 50) / 95) * 100}%, #dbeafe 100%)` }}
                        />
                        <div className="text-sm font-semibold text-blue-600 w-10 text-right">{appZoom}%</div>
                    </div>
                </div>
            )}
        </div>
    );

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
        <div className="bg-[#08080a] min-h-screen overflow-hidden relative selection:bg-violet-500/30">
            {/* Soft Ambient Background */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-violet-600/[0.03] rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-indigo-600/[0.03] rounded-full blur-[120px]" />
            </div>

            <main className={`flex h-screen relative z-10 transition-all duration-700 ease-[cubic-bezier(0.23,1,0.32,1)] ${showChat ? 'p-4 gap-4' : 'p-0'}`}>

                {/* Editor Container - Resizes to make room for chat */}
                <div
                    className={`flex-1 flex flex-col bg-slate-50 border border-slate-200 transition-all duration-700 ease-[cubic-bezier(0.23,1,0.32,1)] overflow-x-hidden ${showChat ? 'rounded-[2.5rem] shadow-2xl' : 'w-full'
                        }`}
                >
                    {/* Inner scaled content */}
                    <div
                        className="h-full w-full flex flex-col"
                        style={{ transform: `scale(${appZoom / 100})`, transformOrigin: 'top left', width: `${100 * (100 / appZoom)}%`, height: `${100 * (100 / appZoom)}%` }}
                    >
                        <div className="px-6 pt-6 pb-2 flex justify-center">
                            <div className="max-w-7xl w-full flex items-center justify-center gap-6">
                                <div className="flex flex-col gap-2 items-start">
                                    <div className="flex items-center gap-2">
                                        <ZoomControl />
                                        {activeTool === null ? (
                                            <>
                                                <ToolbarIcon icon={<Wand2 size={18} />} tooltip="Format" onClick={() => toggleTool('format')} isActive={activeTool === 'format'} />
                                                <ToolbarIcon icon={<FileAudio2 size={18} />} tooltip="Upload" onClick={() => toggleTool('upload')} isActive={activeTool === 'upload'} />
                                                <ToolbarIcon icon={<SlidersHorizontal size={18} />} tooltip="VAD" onClick={() => toggleTool('calibrate')} isActive={activeTool === 'calibrate'} />
                                            </>
                                        ) : (
                                            <ToolbarIcon icon={<X size={18} />} tooltip="Close Tool" onClick={() => setActiveTool(null)} />
                                        )}
                                    </div>
                                    {activeTool === 'calibrate' && (
                                        <Card className="w-80 shadow-xl border-none"><CardBody className="p-4">
                                            <div className="flex items-center justify-between mb-4">
                                                <h4 className="text-xs font-bold uppercase tracking-widest text-slate-400">Audio Setup</h4>
                                                <Button isIconOnly size="sm" variant="flat" color="success" onClick={async () => {
                                                    await fetch('/api/config/vad', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ voice_threshold: voiceThreshold, silence_threshold: silenceThreshold }) });
                                                    setActiveTool(null);
                                                }}><Check size={16} /></Button>
                                            </div>
                                            <Slider label="Voice Start" size="sm" step={50} minValue={100} maxValue={2000} value={voiceThreshold} onChange={(v) => setVoiceThreshold(v as number)} color="success" />
                                            <Slider label="Silence Stop" size="sm" step={50} minValue={50} maxValue={1000} value={silenceThreshold} onChange={(v) => setSilenceThreshold(v as number)} color="danger" />
                                        </CardBody></Card>
                                    )}
                                    {activeTool === 'format' && (
                                        <Card className="w-64 shadow-xl border-none"><CardBody className="p-4">
                                            <h5 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3">Refinement</h5>
                                            <div className="flex gap-2">
                                                <Button size="sm" color="primary" className="flex-1 rounded-xl">Auto-Format</Button>
                                                <Button size="sm" variant="bordered" className="rounded-xl" onClick={() => setActiveTool(null)}>Close</Button>
                                            </div>
                                        </CardBody></Card>
                                    )}
                                    {activeTool === 'upload' && (
                                        <Card className="w-64 shadow-xl border-none"><CardBody className="p-4">
                                            <input ref={uploadInputRef} type="file" accept="audio/*" className="hidden" onChange={(e) => setUploadFileName(e.target.files?.[0]?.name || null)} />
                                            <Button size="sm" variant="flat" className="w-full mb-3 rounded-xl" onClick={() => uploadInputRef.current?.click()}>Choose File</Button>
                                            <p className="text-[10px] text-slate-500 mb-3 truncate font-medium">{uploadFileName || 'No file selected'}</p>
                                            <Button size="sm" color="primary" className="w-full rounded-xl" onClick={async () => {
                                                const file = uploadInputRef.current?.files?.[0]; if (!file) return;
                                                const fd = new FormData(); fd.append('file', file);
                                                setIsProcessing(true); await fetch('/api/transcribe-file', { method: 'POST', body: fd });
                                                setIsProcessing(false); setActiveTool(null);
                                            }}>Start Transcription</Button>
                                        </CardBody></Card>
                                    )}
                                </div>
                                <RecordingPanel />
                            </div>
                        </div>

                        <div className="flex-1 flex overflow-hidden w-full px-4 relative">
                            {/* Toggleable tools panel */}
                            <button
                                onClick={() => setShowSidebar(!showSidebar)}
                                className="absolute left-6 top-6 z-[60] p-2.5 rounded-2xl bg-white border border-slate-200 shadow-sm text-slate-400 hover:text-indigo-600 transition-all duration-300 hover:shadow-md"
                            >
                                {showSidebar ? <PanelRightClose size={18} className="rotate-180" /> : <PanelRightOpen size={18} />}
                            </button>

                            <aside className={`flex-shrink-0 space-y-4 overflow-y-auto overflow-x-hidden transition-all duration-500 ease-in-out modern-scrollbar ${showSidebar ? 'w-[420px] p-4 opacity-100' : 'w-0 p-0 opacity-0 pointer-events-none'}`}>
                                <div className="w-[388px]"> {/* 420px - p-4(32px) = 388px to avoid overflow */}
                                    <MicTest />
                                    <div className="h-4" />
                                    <LiveTranscription />
                                </div>
                            </aside>

                            <main className="flex-1 p-4 flex flex-col overflow-y-auto">
                                {isLoading ? (
                                    <Card className="h-full flex items-center justify-center border-none bg-transparent shadow-none"><Spinner size="lg" color="primary" /></Card>
                                ) : (
                                    <div className="h-full flex flex-col">
                                        {isProcessing && <Card className="mb-4 bg-indigo-50/50 border-none backdrop-blur-md shadow-sm animate-pulse"><CardBody className="py-2 text-[11px] font-bold text-indigo-600 uppercase tracking-widest text-center">Processing with DeepSeek Intel...</CardBody></Card>}
                                        <MarkdownViewer title={currentTitle} content={latestContent} onSave={handleSave} zoomLevel={mdZoom} nav={{ onPrev: handlePrev, onNext: handleNext, hasPrev: selectedIndex > 0, hasNext: selectedIndex < transcriptions.length - 1, index: selectedIndex, total: transcriptions.length }} />
                                    </div>
                                )}
                            </main>
                        </div>
                    </div>
                </div>

                {/* Sidebar Chat - Slides in and pushes content */}
                <div
                    className={`h-full transition-all duration-700 ease-[cubic-bezier(0.23,1,0.32,1)] flex-shrink-0 relative ${showChat ? (isChatExpanded ? 'w-[850px] opacity-100' : 'w-[480px] opacity-100') : 'w-0 opacity-0 pointer-events-none'
                        }`}
                >
                    <ChatSidebar
                        activeDocId={transcriptions[selectedIndex]?.id || undefined}
                        activeDocName={transcriptions[selectedIndex]?.filename || undefined}
                        isExpanded={isChatExpanded}
                        onToggleExpand={() => setIsChatExpanded(!isChatExpanded)}
                        onClose={() => setShowChat(false)}
                    />
                </div>
            </main>

            {/* Minimal High-Contrast Floating Toggle */}
            <button
                onClick={() => setShowChat(!showChat)}
                className={`fixed top-10 right-10 z-[100] transition-all duration-500 hover:rotate-12 active:scale-90 group ${showChat ? 'opacity-0 scale-50 pointer-events-none' : 'opacity-100 rotate-0 scale-100'}`}
            >
                <div className="relative">
                    <div className="absolute -inset-4 bg-violet-500/10 rounded-full blur-2xl group-hover:bg-violet-500/20 transition-all" />
                    <div className="relative w-14 h-14 rounded-2xl bg-black border border-white/10 flex items-center justify-center shadow-[0_20px_50px_rgba(0,0,0,0.5)] transition-all group-hover:bg-slate-900">
                        <MessageCircle size={26} className="text-violet-400 group-hover:text-white" />
                        <div className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full border-[3px] border-black" />
                    </div>
                </div>
            </button>

            {/* Global Modern Styles */}
            <style jsx global>{`
                /* Prevent horizontal scroll app-wide */
                html, body {
                    max-width: 100vw;
                    overflow-x: hidden;
                }

                /* Modern Scrollbar System */
                * {
                    scrollbar-width: thin;
                    scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
                }

                *::-webkit-scrollbar {
                    width: 5px;
                    height: 5px;
                }

                *::-webkit-scrollbar-track {
                    background: transparent;
                }

                *::-webkit-scrollbar-thumb {
                    background: rgba(0, 0, 0, 0.05);
                    border-radius: 20px;
                    transition: all 0.3s;
                }

                *:hover::-webkit-scrollbar-thumb {
                    background: rgba(0, 0, 0, 0.12);
                }

                *::-webkit-scrollbar-thumb:hover {
                    background: rgba(139, 92, 246, 0.5) !important;
                }

                /* Dark context scrollbars */
                .bg-\[\#08080a\] *::-webkit-scrollbar-thumb {
                    background: rgba(255, 255, 255, 0.03);
                }
                .bg-\[\#08080a\] *::-webkit-scrollbar-thumb:hover {
                    background: rgba(139, 92, 246, 0.4) !important;
                }

                .modern-scrollbar {
                    scrollbar-gutter: stable;
                }
            `}</style>
        </div>
    );
}
