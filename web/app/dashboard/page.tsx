'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardBody, Spinner, Slider, Button, Divider } from "@heroui/react";
import { RecordingPanel } from './components/RecordingPanel';
import { LiveTranscription } from './components/LiveTranscription';
import { MarkdownViewer } from './components/MarkdownViewer';
import { MicTest } from './components/MicTest';
import { ChatSidebar } from './components/ChatSidebar';
import { RecordingProvider, useRecording } from './providers/RecordingProvider';
import { ZoomIn, Wand2, FileAudio2, SlidersHorizontal, Sparkles, Check, X, ChevronLeft, Loader2, FileText, Search, Mic, Palette, AudioLines, Music4, Waves } from 'lucide-react';
import Image from 'next/image';
import { useBackground } from '../providers';
import { BackgroundPicker, ThemeSettings } from "./components/BackgroundPicker";
import { Toast, ToastType } from './components/Toast';

// Hooks especializados (SRP / SOLID)
import { useTranscriptionService } from './hooks/useTranscriptionService';
import { useToolRegistry } from './hooks/useToolRegistry';

type ToolbarIconProps = {
    icon: React.ReactNode;
    tooltip: string;
    onClick?: () => void;
    isActive?: boolean;
    className?: string;
};

const ToolbarIcon = ({ icon, tooltip, onClick, isActive, className = '' }: ToolbarIconProps) => {
    const [showTooltip, setShowTooltip] = useState(false);
    const { themeType } = useBackground();
    const isLight = themeType === 'light';

    return (
        <div className="relative group">
            <button
                onClick={onClick}
                className={`p-2 rounded-lg transition-all duration-300 transform hover:scale-110 hover:-translate-y-1 hover:rotate-3 active:scale-90 backdrop-blur-md ${isActive
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-md hover:shadow-lg'
                    : isLight
                        ? 'text-slate-600 hover:text-black shadow-sm hover:shadow-md'
                        : 'text-slate-200 hover:text-white shadow-sm hover:shadow-md'
                    } ${className}`}
                style={{
                    background: isActive ? undefined : 'var(--theme-glass-bg)',
                    border: '1px solid var(--theme-glass-border)'
                }}
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
            >
                {icon}
            </button>
            {showTooltip && (
                <div className={`absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-1.5 ${isLight ? 'bg-slate-800 text-white' : 'bg-white text-slate-900'} text-xs font-semibold rounded-lg whitespace-nowrap pointer-events-none z-50 shadow-lg animate-in fade-in slide-in-from-bottom-1 duration-200`}>
                    {tooltip}
                    <div className={`absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent ${isLight ? 'border-t-slate-800' : 'border-t-white'}`}></div>
                </div>
            )}
        </div>
    );
};

export default function DashboardPage() {
    return (
        <RecordingProvider>
            <DashboardContent />
        </RecordingProvider>
    );
}

function DashboardContent() {
    // 1. Estados de UI y Navegación
    const { themeType } = useBackground();
    const isLight = themeType === 'light';
    const { voiceThreshold, setVoiceThreshold, silenceThreshold, setSilenceThreshold } = useRecording();

    const [mdZoom, setMdZoom] = useState(100);
    const [appZoom, setAppZoom] = useState(100);
    const [showChat, setShowChat] = useState(false);
    const [isChatExpanded, setIsChatExpanded] = useState(false);
    const [showSidebar, setShowSidebar] = useState(true);
    const [showMicTest, setShowMicTest] = useState(true);
    const [notification, setNotification] = useState<{ message: string, type: ToastType } | null>(null);

    // 2. Búsqueda y Navegación Global
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [activeSearchTerm, setActiveSearchTerm] = useState('');
    const [showSearchPalette, setShowSearchPalette] = useState(false);

    // 3. Servicios y Lógica de Negocio (SOLID: SCP/DIP)
    const transcriptionService = useTranscriptionService();
    const tools = useToolRegistry({
        transcriptionId: transcriptionService.transcriptionId,
        transcriptions: transcriptionService.transcriptions,
        selectedIndex: transcriptionService.selectedIndex,
        setProcessingIds: transcriptionService.setProcessingIds,
        loadTranscriptionById: transcriptionService.loadTranscriptionById,
        loadTranscriptionsList: transcriptionService.loadTranscriptionsList,
        setNotification
    });

    // --- Helpers de UI ---
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
            } else if ((e.ctrlKey || e.metaKey) && (e.key === 'f' || e.key === 'F')) {
                e.preventDefault(); setShowSearchPalette(prev => !prev);
            } else if (e.key === 'Escape') {
                setShowSearchPalette(false);
            }
        };
        window.addEventListener('keydown', handleKeyPress);
        return () => window.removeEventListener('keydown', handleKeyPress);
    }, [mdZoom]);

    const handleSearch = async (val: string) => {
        setSearchQuery(val);
        if (val.length < 2) {
            setSearchResults([]);
            setIsSearching(false);
            return;
        }
        setIsSearching(true);
        try {
            const res = await fetch(`/api/transcriptions/search?q=${encodeURIComponent(val)}`, {
                headers: { 'x-api-key': 'dev-secret-api-key' }
            });
            const data = await res.json();
            setSearchResults(data.items || []);
        } catch (e) {
            console.error("Search failed", e);
        } finally {
            setIsSearching(false);
        }
    };

    const handleSelectSearchResult = async (result: any) => {
        setActiveSearchTerm(searchQuery);
        setShowSearchPalette(false);
        await transcriptionService.loadTranscriptionById(result.id);
        const idx = transcriptionService.transcriptions.findIndex(t => t.id === result.id);
        if (idx !== -1) transcriptionService.setSelectedIndex(idx);
    };

    const extractTitleFromMarkdown = (md: string) => {
        if (!md) return 'Última Clase';
        const headingMatch = md.match(/^#{1,3}\s*(.+)$/m);
        if (headingMatch && headingMatch[1]) return headingMatch[1].trim();
        const transMatch = md.match(/Transcripci[oó]n:\s*(\d{4}-\d{2}-\d{2})/i);
        if (transMatch && transMatch[1]) return `Transcripción: ${transMatch[1]}`;
        return 'Última Clase';
    };

    const currentTitle = extractTitleFromMarkdown(transcriptionService.latestContent);


    return (
        <div className="bg-transparent min-h-screen overflow-hidden relative">
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-violet-600/[0.03] rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-indigo-600/[0.03] rounded-full blur-[120px]" />
            </div>

            <main className={`flex h-screen relative z-10 transition-all duration-700 ease-[cubic-bezier(0.23,1,0.32,1)] ${showChat ? 'p-4 gap-4' : 'p-0'}`}>
                <div className={`flex-1 flex flex-col transition-all duration-700 ease-[cubic-bezier(0.23,1,0.32,1)] overflow-x-hidden ${showChat ? 'rounded-[2.5rem] shadow-2xl' : 'w-full'}`}>
                    <div className="h-full w-full flex flex-col" style={{ transform: `scale(${appZoom / 100})`, transformOrigin: 'top left', width: `${100 * (100 / appZoom)}%`, height: `${100 * (100 / appZoom)}%` }}>
                        <div className="px-6 pt-6 pb-2 flex justify-center">
                            <div className="max-w-7xl w-full flex items-center justify-center gap-6">
                                <div className="flex flex-col gap-2 items-start">
                                    <div className="flex items-center gap-2">
                                        <ToolbarIcon
                                            icon={<Palette size={18} />}
                                            tooltip="Temas"
                                            onClick={() => {
                                                setShowMicTest(false);
                                                tools.toggleTool('themes');
                                            }}
                                            isActive={tools.activeTool === 'themes'}
                                        />
                                        <div className="w-px h-6 bg-slate-200/50 mx-1" />
                                        <ToolbarIcon
                                            icon={<ZoomIn size={18} />}
                                            tooltip="Zoom"
                                            onClick={() => {
                                                setShowMicTest(false);
                                                tools.toggleTool('zoom');
                                            }}
                                            isActive={tools.activeTool === 'zoom'}
                                        />
                                        <ToolbarIcon
                                            icon={<AudioLines size={18} />}
                                            tooltip="FFMPEG Audio"
                                            onClick={() => {
                                                setShowMicTest(false);
                                                tools.toggleTool('audio_process');
                                            }}
                                            isActive={tools.activeTool === 'audio_process'}
                                        />
                                        <ToolbarIcon
                                            icon={<FileAudio2 size={18} />}
                                            tooltip="Upload"
                                            onClick={() => {
                                                setShowMicTest(false);
                                                tools.toggleTool('upload');
                                            }}
                                            isActive={tools.activeTool === 'upload'}
                                        />
                                        <ToolbarIcon
                                            icon={<SlidersHorizontal size={18} />}
                                            tooltip="VAD"
                                            onClick={() => {
                                                setShowMicTest(false);
                                                tools.toggleTool('calibrate');
                                            }}
                                            isActive={tools.activeTool === 'calibrate'}
                                        />
                                        <ToolbarIcon
                                            icon={<Mic size={18} />}
                                            tooltip="Mic Test"
                                            onClick={() => {
                                                if (!showMicTest) tools.setActiveTool(null);
                                                setShowMicTest(!showMicTest);
                                            }}
                                            isActive={showMicTest}
                                        />
                                    </div>

                                    {/* Componentes de Herramientas Dinámicas movidos a la barra lateral */}
                                </div>
                                <RecordingPanel />
                            </div>
                        </div>

                        <div className="flex-1 flex overflow-hidden w-full px-4 relative">
                            {/* Panel Toggle Sidebar */}
                            <div className="fixed left-0 top-1/2 -translate-y-1/2 z-[100] flex items-center group/nav">
                                <button
                                    onClick={() => setShowSidebar(!showSidebar)}
                                    className="relative flex items-center justify-center w-6 h-28 group/btn transition-all duration-700 ease-[cubic-bezier(0.23,1,0.32,1)]"
                                >
                                    <div
                                        className="absolute inset-0 rounded-r-2xl border-y border-r transition-all duration-500 backdrop-blur-xl"
                                        style={{
                                            background: showSidebar ? 'var(--theme-glass-bg)' : 'var(--theme-glass-bg)',
                                            borderColor: showSidebar ? 'var(--theme-glass-border)' : 'rgba(99, 102, 241, 0.3)',
                                            opacity: showSidebar ? '0.4' : '1',
                                            transform: showSidebar ? 'translateX(-12px)' : 'translateX(0)'
                                        }}
                                    />
                                    <div className={`absolute left-0 w-[4px] h-14 rounded-full transition-all duration-500 ${showSidebar ? 'bg-white/5' : 'bg-gradient-to-b from-blue-400 via-indigo-500 to-violet-600 shadow-[2px_0_20px_rgba(99,102,241,1)]'}`} />
                                    <div className={`relative z-10 transition-all duration-700 transform flex items-center justify-center ${showSidebar ? 'opacity-0' : 'rotate-180 opacity-100 font-bold'}`}><ChevronLeft size={16} className="text-white" /></div>
                                </button>
                            </div>

                            <aside className={`flex-shrink-0 transition-all duration-500 ease-in-out modern-scrollbar ${showSidebar ? 'w-[420px] opacity-100' : 'w-0 opacity-0 pointer-events-none overflow-hidden'}`}>
                                <div className="h-full flex flex-col p-4 gap-4">
                                    {showMicTest && (
                                        <div className="flex-shrink-0 animate-in slide-in-from-top-2 fade-in duration-300">
                                            <MicTest onClose={() => setShowMicTest(false)} />
                                        </div>
                                    )}

                                    {tools.activeTool === 'calibrate' && (
                                        <div className="flex-shrink-0 animate-in slide-in-from-top-2 fade-in duration-300">
                                            <Card className="w-full shadow-xl border-none glass overflow-hidden rounded-2xl">
                                                <CardBody className="p-5 space-y-4">
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-center gap-3">
                                                            <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg">
                                                                <SlidersHorizontal size={18} className="text-white" />
                                                            </div>
                                                            <div>
                                                                <h3 className="text-sm font-semibold text-theme-primary">Calibración VAD</h3>
                                                                <p className="text-[10px] text-theme-secondary font-medium">Ajusta los umbrales de voz</p>
                                                            </div>
                                                        </div>
                                                        <div className="flex gap-2">
                                                            <Button isIconOnly size="sm" variant="light" className="w-6 h-6 min-w-0 text-slate-500 hover:text-rose-500" onClick={() => tools.setActiveTool(null)}>
                                                                <X size={14} />
                                                            </Button>
                                                            <Button
                                                                isIconOnly
                                                                size="sm"
                                                                variant="light"
                                                                className="w-6 h-6 min-w-0 text-emerald-500 hover:bg-emerald-500/10"
                                                                onClick={async () => {
                                                                    await fetch('/api/config/vad', {
                                                                        method: 'POST',
                                                                        headers: { 'Content-Type': 'application/json' },
                                                                        body: JSON.stringify({ voice_threshold: voiceThreshold, silence_threshold: silenceThreshold })
                                                                    });
                                                                    tools.setActiveTool(null);
                                                                }}
                                                            >
                                                                <Check size={14} />
                                                            </Button>
                                                        </div>
                                                    </div>
                                                    <div className="space-y-6 py-2">
                                                        <Slider
                                                            label="Sensibilidad Voz"
                                                            size="sm"
                                                            step={5}
                                                            minValue={20}
                                                            maxValue={1000}
                                                            value={voiceThreshold}
                                                            onChange={(v) => setVoiceThreshold(v as number)}
                                                            color="success"
                                                            classNames={{
                                                                label: "text-xs font-semibold text-theme-secondary",
                                                                value: "text-xs font-bold text-emerald-500"
                                                            }}
                                                        />
                                                        <Slider
                                                            label="Umbral de Silencio"
                                                            size="sm"
                                                            step={5}
                                                            minValue={10}
                                                            maxValue={800}
                                                            value={silenceThreshold}
                                                            onChange={(v) => setSilenceThreshold(v as number)}
                                                            color="danger"
                                                            classNames={{
                                                                label: "text-xs font-semibold text-theme-secondary",
                                                                value: "text-xs font-bold text-rose-500"
                                                            }}
                                                        />
                                                    </div>
                                                </CardBody>
                                            </Card>
                                        </div>
                                    )}

                                    {tools.activeTool === 'audio_process' && (
                                        <div className="flex-shrink-0 animate-in slide-in-from-top-2 fade-in duration-300">
                                            <Card className="w-full shadow-2xl border-none glass overflow-hidden rounded-2xl">
                                                <CardBody className="p-6 space-y-5">
                                                    {/* Header */}
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-center gap-3">
                                                            <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 via-indigo-600 to-violet-600 shadow-lg shadow-blue-500/30">
                                                                <Waves size={20} className="text-white" />
                                                            </div>
                                                            <div>
                                                                <h3 className="text-base font-bold text-white drop-shadow-lg">Transformación de Audio</h3>
                                                                <p className="text-xs text-white/70 font-semibold">Motor FFmpeg • Alta Velocidad</p>
                                                            </div>
                                                        </div>
                                                        <Button
                                                            isIconOnly
                                                            size="sm"
                                                            variant="light"
                                                            className="w-8 h-8 min-w-0 text-white/60 hover:text-rose-400 hover:bg-rose-500/10"
                                                            onClick={() => tools.setActiveTool(null)}
                                                        >
                                                            <X size={16} />
                                                        </Button>
                                                    </div>

                                                    {/* File Upload Zone */}
                                                    <div className="space-y-2">
                                                        <label className="text-xs font-bold text-white/90 uppercase tracking-wide flex items-center gap-2">
                                                            <FileAudio2 size={14} className="text-blue-400" />
                                                            Cargar Audio
                                                        </label>
                                                        <input
                                                            ref={tools.uploadInputRef}
                                                            type="file"
                                                            accept="audio/*"
                                                            className="hidden"
                                                            onChange={(e) => tools.setUploadFileName(e.target.files?.[0]?.name || null)}
                                                        />
                                                        <div
                                                            className="relative border-2 border-dashed border-white/20 rounded-xl p-6 flex flex-col items-center justify-center gap-3 cursor-pointer hover:border-blue-400/50 hover:bg-blue-500/5 transition-all duration-300 group"
                                                            onClick={() => tools.uploadInputRef.current?.click()}
                                                        >
                                                            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-violet-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                                                            <div className="relative z-10 flex flex-col items-center gap-2">
                                                                <div className="p-3 rounded-full bg-blue-500/10 group-hover:bg-blue-500/20 transition-colors">
                                                                    <FileAudio2 size={24} className="text-blue-400" />
                                                                </div>
                                                                <p className="text-sm font-bold text-white/80 truncate max-w-full px-2">
                                                                    {tools.uploadFileName || 'Click para seleccionar archivo'}
                                                                </p>
                                                                <p className="text-[10px] text-white/40 font-semibold">MP3, WAV, M4A, OGG, WebM</p>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <Divider className="opacity-20" />

                                                    {/* Conversion Profiles */}
                                                    <div className="space-y-2">
                                                        <label className="text-xs font-bold text-white/90 uppercase tracking-wide flex items-center gap-2">
                                                            <Sparkles size={14} className="text-violet-400" />
                                                            Perfiles de Conversión
                                                        </label>
                                                        <div className="grid grid-cols-3 gap-2">
                                                            <Button
                                                                size="sm"
                                                                className="h-auto py-3 px-2 flex flex-col items-center gap-1 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 hover:from-emerald-500/30 hover:to-teal-500/30 border border-emerald-500/30 text-white rounded-xl"
                                                                onClick={() => setNotification({ message: 'Perfil Transcripción: 16kHz, Mono, WAV', type: 'info' })}
                                                            >
                                                                <Mic size={16} className="text-emerald-400" />
                                                                <span className="text-[10px] font-bold">Transcripción</span>
                                                            </Button>
                                                            <Button
                                                                size="sm"
                                                                className="h-auto py-3 px-2 flex flex-col items-center gap-1 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 hover:from-blue-500/30 hover:to-cyan-500/30 border border-blue-500/30 text-white rounded-xl"
                                                                onClick={() => setNotification({ message: 'Perfil Alta Calidad: FLAC, 48kHz', type: 'info' })}
                                                            >
                                                                <Music4 size={16} className="text-blue-400" />
                                                                <span className="text-[10px] font-bold">Alta Calidad</span>
                                                            </Button>
                                                            <Button
                                                                size="sm"
                                                                className="h-auto py-3 px-2 flex flex-col items-center gap-1 bg-gradient-to-br from-orange-500/20 to-red-500/20 hover:from-orange-500/30 hover:to-red-500/30 border border-orange-500/30 text-white rounded-xl"
                                                                onClick={() => setNotification({ message: 'Perfil Almacenamiento: MP3, 64kbps', type: 'info' })}
                                                            >
                                                                <FileAudio2 size={16} className="text-orange-400" />
                                                                <span className="text-[10px] font-bold">Almacenar</span>
                                                            </Button>
                                                        </div>
                                                    </div>

                                                    <Divider className="opacity-20" />

                                                    {/* Advanced Functions */}
                                                    <div className="space-y-2">
                                                        <label className="text-xs font-bold text-white/90 uppercase tracking-wide flex items-center gap-2">
                                                            <SlidersHorizontal size={14} className="text-pink-400" />
                                                            Funciones Avanzadas
                                                        </label>
                                                        <div className="grid grid-cols-2 gap-2">
                                                            <Button
                                                                size="sm"
                                                                variant="flat"
                                                                className="rounded-xl font-bold bg-white/10 hover:bg-white/20 text-white text-xs border border-white/10"
                                                                onClick={() => setNotification({ message: '🔊 Normalizando volumen a -16dB...', type: 'info' })}
                                                            >
                                                                <Music4 size={14} />
                                                                Normalizar
                                                            </Button>
                                                            <Button
                                                                size="sm"
                                                                variant="flat"
                                                                className="rounded-xl font-bold bg-white/10 hover:bg-white/20 text-white text-xs border border-white/10"
                                                                onClick={() => setNotification({ message: '✂️ Eliminando silencios...', type: 'info' })}
                                                            >
                                                                <Sparkles size={14} />
                                                                Quitar Silencio
                                                            </Button>
                                                            <Button
                                                                size="sm"
                                                                variant="flat"
                                                                className="rounded-xl font-bold bg-white/10 hover:bg-white/20 text-white text-xs border border-white/10"
                                                                onClick={() => setNotification({ message: '⏱️ Extrayendo segmento...', type: 'info' })}
                                                            >
                                                                <ZoomIn size={14} />
                                                                Extraer
                                                            </Button>
                                                            <Button
                                                                size="sm"
                                                                variant="flat"
                                                                className="rounded-xl font-bold bg-white/10 hover:bg-white/20 text-white text-xs border border-white/10"
                                                                onClick={() => setNotification({ message: '🔗 Uniendo archivos...', type: 'info' })}
                                                            >
                                                                <Waves size={14} />
                                                                Unir
                                                            </Button>
                                                            <Button
                                                                size="sm"
                                                                variant="flat"
                                                                className="rounded-xl font-bold bg-white/10 hover:bg-white/20 text-white text-xs border border-white/10"
                                                                onClick={() => setNotification({ message: '⚡ Cambiando velocidad a 1.5x...', type: 'info' })}
                                                            >
                                                                <AudioLines size={14} />
                                                                Velocidad
                                                            </Button>
                                                            <Button
                                                                size="sm"
                                                                variant="flat"
                                                                className="rounded-xl font-bold bg-white/10 hover:bg-white/20 text-white text-xs border border-white/10"
                                                                onClick={() => setNotification({ message: '🎯 Detectando formato...', type: 'info' })}
                                                            >
                                                                <FileText size={14} />
                                                                Detectar
                                                            </Button>
                                                        </div>
                                                    </div>

                                                    <Divider className="opacity-20" />

                                                    {/* Action Buttons */}
                                                    <div className="grid grid-cols-2 gap-3">
                                                        <Button
                                                            size="md"
                                                            variant="flat"
                                                            className="rounded-xl font-bold bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 hover:from-violet-500/30 hover:to-fuchsia-500/30 text-white border border-violet-500/30"
                                                            disabled={!tools.uploadFileName}
                                                            onClick={() => setNotification({ message: '📥 Procesando y descargando...', type: 'success' })}
                                                        >
                                                            <FileAudio2 size={16} />
                                                            Descargar
                                                        </Button>
                                                        <Button
                                                            size="md"
                                                            className="rounded-xl font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 shadow-lg shadow-blue-500/30 text-white"
                                                            disabled={!tools.uploadFileName}
                                                            onClick={() => setNotification({ message: '🚀 Ejecutando pipeline FFmpeg...', type: 'success' })}
                                                        >
                                                            <Wand2 size={16} />
                                                            Procesar
                                                        </Button>
                                                    </div>
                                                </CardBody>
                                            </Card>
                                        </div>
                                    )}

                                    {tools.activeTool === 'upload' && (
                                        <div className="flex-shrink-0 animate-in slide-in-from-top-2 fade-in duration-300">
                                            <Card className="w-full shadow-xl border-none glass overflow-hidden rounded-2xl">
                                                <CardBody className="p-5 space-y-4">
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-center gap-3">
                                                            <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg">
                                                                <FileAudio2 size={18} className="text-white" />
                                                            </div>
                                                            <div>
                                                                <h3 className="text-sm font-semibold text-theme-primary">Subir Audio</h3>
                                                                <p className="text-[10px] text-theme-secondary font-medium">Transcribe archivos locales</p>
                                                            </div>
                                                        </div>
                                                        <Button isIconOnly size="sm" variant="light" className="w-6 h-6 min-w-0 text-slate-500 hover:text-rose-500" onClick={() => tools.setActiveTool(null)}>
                                                            <X size={14} />
                                                        </Button>
                                                    </div>
                                                    <input ref={tools.uploadInputRef} type="file" accept="audio/*" className="hidden" onChange={(e) => tools.setUploadFileName(e.target.files?.[0]?.name || null)} />
                                                    <div
                                                        className="border-2 border-dashed border-white/10 rounded-xl p-4 flex flex-col items-center justify-center gap-2 cursor-pointer hover:bg-white/5 transition-all"
                                                        onClick={() => tools.uploadInputRef.current?.click()}
                                                    >
                                                        <FileAudio2 size={24} className="text-blue-400 opacity-50" />
                                                        <p className="text-[10px] text-slate-400 font-bold truncate max-w-full px-2">
                                                            {tools.uploadFileName || 'Haz clic para seleccionar'}
                                                        </p>
                                                    </div>
                                                    <Button
                                                        size="md"
                                                        color="primary"
                                                        className="w-full rounded-xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 shadow-lg shadow-blue-500/25"
                                                        onClick={tools.handleUpload}
                                                        disabled={!tools.uploadFileName}
                                                    >
                                                        Iniciar Transcripción
                                                    </Button>
                                                </CardBody>
                                            </Card>
                                        </div>
                                    )}

                                    {tools.activeTool === 'zoom' && (
                                        <div className="flex-shrink-0 animate-in slide-in-from-top-2 fade-in duration-300">
                                            <Card className="w-full shadow-xl border-none glass overflow-hidden rounded-2xl">
                                                <CardBody className="p-5 space-y-4">
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-center gap-3">
                                                            <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg">
                                                                <ZoomIn size={18} className="text-white" />
                                                            </div>
                                                            <div>
                                                                <h3 className="text-sm font-semibold text-theme-primary">Zoom de Interfaz</h3>
                                                                <p className="text-[10px] text-theme-secondary font-medium">Ajusta el tamaño global</p>
                                                            </div>
                                                        </div>
                                                        <Button isIconOnly size="sm" variant="light" className="w-6 h-6 min-w-0 text-slate-500 hover:text-rose-500" onClick={() => tools.setActiveTool(null)}>
                                                            <X size={14} />
                                                        </Button>
                                                    </div>
                                                    <div className="space-y-3">
                                                        <div className="flex items-center justify-between">
                                                            <span className="text-[10px] font-black uppercase tracking-widest text-theme-secondary">Escala</span>
                                                            <span className="text-xs font-bold text-blue-500">{appZoom}%</span>
                                                        </div>
                                                        <Slider
                                                            size="sm"
                                                            step={1}
                                                            minValue={50}
                                                            maxValue={145}
                                                            value={appZoom}
                                                            onChange={(v) => handleAppZoom(v as number)}
                                                            color="primary"
                                                            className="max-w-md"
                                                            hideValue
                                                        />
                                                    </div>
                                                </CardBody>
                                            </Card>
                                        </div>
                                    )}

                                    {tools.activeTool === 'themes' && (
                                        <div className="flex-shrink-0 animate-in slide-in-from-top-2 fade-in duration-300">
                                            <Card className="w-full shadow-xl border-none glass overflow-hidden rounded-2xl">
                                                <CardBody className="p-5 space-y-4">
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-center gap-3">
                                                            <div className="p-2.5 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-600 shadow-lg">
                                                                <Palette size={18} className="text-white" />
                                                            </div>
                                                            <div>
                                                                <h3 className="text-sm font-semibold text-theme-primary">Temas y Fondo</h3>
                                                                <p className="text-[10px] text-theme-secondary font-medium">Personaliza tu espacio</p>
                                                            </div>
                                                        </div>
                                                        <Button isIconOnly size="sm" variant="light" className="w-6 h-6 min-w-0 text-slate-500 hover:text-rose-500" onClick={() => tools.setActiveTool(null)}>
                                                            <X size={14} />
                                                        </Button>
                                                    </div>
                                                    <ThemeSettings />
                                                </CardBody>
                                            </Card>
                                        </div>
                                    )}
                                    {/* Background Tasks - Integrated into sidebar flow to avoid overlap */}
                                    {transcriptionService.processingIds.size > 0 && (
                                        <div className="flex-shrink-0 animate-in slide-in-from-top-2 fade-in duration-300">
                                            <Card className="w-full glass border-indigo-500/20 shadow-xl overflow-hidden rounded-2xl">
                                                <CardBody className="p-4">
                                                    <div className="flex items-center gap-3 mb-4">
                                                        <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-500">
                                                            <Sparkles size={16} className="animate-pulse" />
                                                        </div>
                                                        <div>
                                                            <h4 className="text-[10px] font-black uppercase tracking-widest text-indigo-500">Background Tasks</h4>
                                                            <p className="text-[9px] text-theme-secondary font-bold">{transcriptionService.processingIds.size} procesos activos</p>
                                                        </div>
                                                    </div>
                                                    <div className="space-y-2">
                                                        {Array.from(transcriptionService.processingIds).map(id => (
                                                            <div key={id} className="flex items-center justify-between p-2 rounded-xl bg-white/5 border border-white/5">
                                                                <div className="flex items-center gap-2 overflow-hidden">
                                                                    <Loader2 size={10} className="text-indigo-400 animate-spin flex-shrink-0" />
                                                                    <span className="text-[10px] font-bold truncate opacity-80">
                                                                        {id.startsWith('upload-') ? 'Sincronizando Audio...' : id.startsWith('temp-') ? 'Finalizando grabación...' : 'Formateo Inteligente...'}
                                                                    </span>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </CardBody>
                                            </Card>
                                        </div>
                                    )}
                                    <div className="flex-1 min-h-0 mt-auto"><LiveTranscription /></div>
                                </div>
                            </aside>

                            <main className="flex-1 p-4 flex flex-col overflow-y-auto">
                                {transcriptionService.isLoading ? (
                                    <Card className="h-full flex items-center justify-center border-none bg-transparent shadow-none"><Spinner size="lg" color="primary" /></Card>
                                ) : (
                                    <div className="h-full flex flex-col">
                                        {transcriptionService.transcriptionId && transcriptionService.processingIds.has(transcriptionService.transcriptionId) && (
                                            <Card className="mb-4 bg-indigo-50/50 border-none backdrop-blur-md shadow-sm animate-pulse">
                                                <CardBody className="py-2 text-[11px] font-bold text-indigo-600 uppercase tracking-widest text-center">Synthesizing with Kimi Intelligence...</CardBody>
                                            </Card>
                                        )}
                                        <MarkdownViewer
                                            title={currentTitle}
                                            content={transcriptionService.latestContent}
                                            onSave={transcriptionService.handleSave}
                                            onDelete={async () => {
                                                const res = await transcriptionService.handleDelete();
                                                if (res) setNotification({ message: res.message, type: res.success ? 'success' : 'error' });
                                            }}
                                            onFormatProfessional={tools.handleAutoFormat}
                                            zoomLevel={mdZoom}
                                            isFormatted={transcriptionService.transcriptions[transcriptionService.selectedIndex]?.is_formatted}
                                            searchQuery={activeSearchTerm}
                                            nav={{
                                                onPrev: () => transcriptionService.navigateTo(transcriptionService.selectedIndex - 1),
                                                onNext: () => transcriptionService.navigateTo(transcriptionService.selectedIndex + 1),
                                                onJump: transcriptionService.navigateTo,
                                                hasPrev: transcriptionService.selectedIndex > 0,
                                                hasNext: transcriptionService.selectedIndex < transcriptionService.transcriptions.length - 1,
                                                index: transcriptionService.selectedIndex,
                                                total: transcriptionService.transcriptions.length
                                            }}
                                        />
                                    </div>
                                )}
                            </main>
                        </div>
                    </div>
                </div>

                {/* Sidebar Chat */}
                <div className={`h-full transition-all duration-700 ease-[cubic-bezier(0.23,1,0.32,1)] flex-shrink-0 relative ${showChat ? (isChatExpanded ? 'w-[850px] opacity-100' : 'w-[480px] opacity-100') : 'w-0 opacity-0 pointer-events-none'}`}>
                    <ChatSidebar
                        activeDocId={transcriptionService.transcriptions[transcriptionService.selectedIndex]?.id || undefined}
                        activeDocName={transcriptionService.transcriptions[transcriptionService.selectedIndex]?.filename || undefined}
                        activeDocContent={transcriptionService.latestContent || undefined}
                        isFormatted={transcriptionService.transcriptions[transcriptionService.selectedIndex]?.is_formatted}
                        isExpanded={isChatExpanded}
                        onToggleExpand={() => setIsChatExpanded(!isChatExpanded)}
                        onClose={() => setShowChat(false)}
                    />
                </div>
            </main>

            {/* Floating Chat Toggle */}
            <button
                onClick={() => setShowChat(!showChat)}
                className={`fixed top-10 right-10 z-[100] transition-all duration-500 hover:rotate-12 active:scale-90 group ${showChat ? 'opacity-0 scale-50 pointer-events-none' : 'opacity-100 rotate-0 scale-100'}`}
            >
                <div className="relative">
                    <div className="absolute -inset-4 bg-violet-500/20 rounded-full blur-2xl group-hover:bg-violet-500/30 transition-all" />
                    <div
                        className="relative w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-500 backdrop-blur-md"
                        style={{
                            background: 'var(--theme-glass-bg)',
                            border: '1px solid var(--theme-glass-border)',
                            boxShadow: isLight ? '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)' : '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
                        }}
                    >
                        <Image src="/chat-icons/chat-ai2.png" alt="Chat" width={36} height={36} className={`object-contain ${!isLight ? 'brightness-0 invert' : ''}`} />
                        <div
                            className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full border-[3px]"
                            style={{ borderColor: 'var(--background)' }}
                        />
                    </div>
                </div>
            </button>

            {/* Global Styles */}
            <style jsx global>{`
                html, body { max-width: 100vw; overflow-x: hidden; }
                * { scrollbar-width: thin; scrollbar-color: rgba(0, 0, 0, 0.1) transparent; }
                *::-webkit-scrollbar { width: 5px; height: 5px; }
                *::-webkit-scrollbar-track { background: transparent; }
                *::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.05); border-radius: 20px; }
                *:hover::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.12); }
                .modern-scrollbar { scrollbar-gutter: stable; }
            `}</style>


            {/* Command Palette Search */}
            {showSearchPalette && (
                <div className="fixed inset-0 z-[200] flex items-start justify-center pt-[15vh] px-4 backdrop-blur-sm bg-black/40 animate-in fade-in duration-300">
                    <div className="absolute inset-0" onClick={() => setShowSearchPalette(false)} />
                    <div className="w-full max-w-2xl glass border border-white/20 shadow-2xl rounded-3xl overflow-hidden relative animate-in zoom-in-95 slide-in-from-top-4 duration-300">
                        <div className="p-6 flex items-center gap-4 border-b border-white/10">
                            <Search className="text-blue-500 animate-pulse" size={24} />
                            <input autoFocus type="text" placeholder="Escribe para buscar en tus clases (Ctrl+F)..." className="w-full bg-transparent text-xl font-bold outline-none placeholder:text-white/20 text-white" value={searchQuery} onChange={(e) => handleSearch(e.target.value)} />
                            <div className="px-2 py-1 rounded-md bg-white/5 border border-white/10"><span className="text-[10px] font-black opacity-40">ESC</span></div>
                        </div>
                        <div className="max-h-[50vh] overflow-y-auto modern-scrollbar">
                            {isSearching ? (
                                <div className="p-12 text-center"><Loader2 className="animate-spin mx-auto text-blue-500 mb-4" size={32} /><p className="text-sm font-bold opacity-40 uppercase tracking-widest">Buscando...</p></div>
                            ) : searchQuery.length >= 2 ? (
                                <div className="p-4 space-y-2">
                                    {searchResults.length > 0 ? searchResults.map((item, i) => (
                                        <Card key={i} isPressable onPress={() => handleSelectSearchResult(item)} className="w-full bg-white/5 hover:bg-white/10 border-none transition-all group p-1">
                                            <CardBody className="p-4 flex flex-col gap-2">
                                                <div className="flex justify-between items-center">
                                                    <div className="flex items-center gap-3">
                                                        <div className="p-2 rounded-xl bg-blue-500/20 text-blue-400"><FileText size={18} /></div>
                                                        <span className="text-lg font-black group-hover:text-blue-400 transition-colors">{item.filename}</span>
                                                    </div>
                                                    <span className="text-[10px] font-mono text-white/30">{item.date}</span>
                                                </div>
                                                <p className="text-sm opacity-50 italic line-clamp-2 leading-relaxed pl-11 border-l-2 border-white/5">"{item.snippet}"</p>
                                            </CardBody>
                                        </Card>
                                    )) : <div className="p-12 text-center opacity-30"><p className="text-lg font-black uppercase tracking-widest">Sin coincidencias</p></div>}
                                </div>
                            ) : <div className="p-12 text-center opacity-20"><p className="text-sm font-bold uppercase tracking-[0.3em]">Busca términos o temas grabados</p></div>}
                        </div>
                    </div>
                </div>
            )}

            {notification && <Toast message={notification.message} type={notification.type} onClose={() => setNotification(null)} />}
        </div>
    );
}
