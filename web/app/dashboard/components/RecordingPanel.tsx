'use client';

import { useRecording } from '../providers/RecordingProvider';
import { Mic, Square, Settings2 } from 'lucide-react';
import { AudioVisualizer } from './AudioVisualizer';
import { useState } from 'react';
import { useBackground } from '../../providers';
import { Card, CardBody, Button, Slider, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure } from '@heroui/react';
import { AlertTriangle } from 'lucide-react';

function formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export function RecordingPanel() {
    const {
        isRecording,
        duration,
        startRecording,
        stopRecording,
        analyser,
        gainValue,
        setGainValue,
        voiceThreshold,
        setVoiceThreshold,
        silenceThreshold,
        setSilenceThreshold,
        language,
        setLanguage,
        diarization,
        setDiarization,
    } = useRecording();

    const { themeType } = useBackground();
    const isLight = themeType === 'light';

    const LANG_CYCLE: Array<'auto' | 'en' | 'es'> = ['auto', 'en', 'es'];
    const LANG_LABELS = { auto: '🌐 AUTO', en: '🇺🇸 EN', es: '🇪🇸 ES' };
    const LANG_TITLES = {
        auto: 'Auto-detectar idioma (transcribe en el idioma hablado)',
        en: 'Forzar inglés',
        es: 'Forzar español',
    };
    const LANG_STYLES = {
        auto: isLight ? 'bg-slate-50 border-slate-300 text-slate-700' : 'bg-white/10 border-white/30 text-slate-200',
        en:   isLight ? 'bg-blue-50 border-blue-300 text-blue-700'   : 'bg-blue-500/20 border-blue-500/50 text-blue-300',
        es:   isLight ? 'bg-amber-50 border-amber-300 text-amber-700' : 'bg-amber-500/20 border-amber-500/50 text-amber-300',
    };

    const [showSettings, setShowSettings] = useState(false);
    const [visualThreshold, setVisualThreshold] = useState(20); // Visual threshold
    const { isOpen, onOpen, onOpenChange } = useDisclosure();

    const handleStopPress = () => {
        onOpen();
    };

    const confirmStop = () => {
        stopRecording();
        onOpenChange();
    };

    return (
        <div className="flex flex-col gap-2">
            <Card className="shadow-lg border-none glass backdrop-blur-xl">
                <CardBody className="px-3 py-2">
                    <div className="flex items-center gap-2">
                        <Button
                            onPress={isRecording ? handleStopPress : startRecording}
                            isIconOnly
                            size="lg"
                            radius="full"
                            className={`min-w-14 h-14 font-bold shadow-lg transition-all duration-300 transform hover:scale-110 active:scale-90 ${isRecording
                                ? 'bg-gradient-to-br from-rose-500 to-red-700 text-white shadow-red-500/40'
                                : 'bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-700 text-white hover:shadow-blue-500/50 hover:from-blue-600 hover:to-indigo-800'
                                }`}
                        >
                            {isRecording ? <div className="relative flex items-center justify-center"><div className="absolute inset-0 bg-white/20 rounded-full animate-ping" /><Square size={24} className="relative z-10" /></div> : <Mic size={24} />}
                        </Button>

                        <div className="flex flex-col">
                            <span className="text-[10px] font-bold uppercase tracking-widest text-theme-secondary/80">
                                {isRecording ? '🔴 Grabando' : 'Listo para grabar'}
                            </span>
                            <span className="text-xl font-mono font-black bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent drop-shadow-sm">
                                {formatDuration(duration)}
                            </span>
                        </div>

                        {/* Visualizer */}
                        <div className="flex-1 flex justify-center max-w-xs">
                            <AudioVisualizer
                                analyser={analyser}
                                isRecording={isRecording}
                                threshold={visualThreshold}
                            />
                        </div>

                        {/* Language toggle — auto / en / es */}
                        <button
                            onClick={() => {
                                if (isRecording) return;
                                const idx = LANG_CYCLE.indexOf(language);
                                setLanguage(LANG_CYCLE[(idx + 1) % LANG_CYCLE.length]);
                            }}
                            disabled={isRecording}
                            title={isRecording ? 'Detén la grabación para cambiar idioma' : LANG_TITLES[language]}
                            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-black uppercase tracking-widest border transition-all duration-200
                                ${isRecording ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer hover:scale-105 active:scale-95'}
                                ${LANG_STYLES[language]}`}
                        >
                            <span>{LANG_LABELS[language]}</span>
                        </button>

                        <Button
                            onPress={() => setShowSettings(!showSettings)}
                            isIconOnly
                            size="md"
                            variant="light"
                            className={`transition-all duration-300 ${showSettings
                                ? 'bg-indigo-500/20 text-indigo-400 scale-110'
                                : isLight ? 'text-slate-600 hover:bg-slate-200/50 hover:text-indigo-600' : 'text-theme-primary hover:bg-white/10 hover:text-indigo-400'
                                }`}
                            title="Configuración de Audio"
                        >
                            <Settings2 size={20} className={showSettings ? 'animate-spin-slow' : ''} />
                            {!showSettings && <div className="absolute top-1 right-1 w-1.5 h-1.5 bg-indigo-500 rounded-full animate-soft-pulse" />}
                        </Button>
                    </div>
                </CardBody>
            </Card>

            {/* Settings Panel */}
            {showSettings && (
                <Card className="shadow-md border-none glass">
                    <CardBody className="p-4">
                        <h4 className="text-sm font-black mb-4 uppercase tracking-[0.1em] title-semi-neon">Configuración de Audio</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <Slider
                                    label="Ganancia (Volumen)"
                                    classNames={{
                                        label: "label-technical",
                                        value: "text-[10px] font-black tabular-nums text-violet-400 text-glow-contrast"
                                    }}
                                    size="sm"
                                    step={0.1}
                                    minValue={0.5}
                                    maxValue={10.0}
                                    value={gainValue}
                                    onChange={(value) => setGainValue(value as number)}
                                    className="max-w-md"
                                    color="primary"
                                    formatOptions={{ maximumFractionDigits: 1 }}
                                    showTooltip={true}
                                />
                                <p className="text-xs text-gray-500 mt-1">Aumenta si el audio se detecta muy bajo.</p>
                            </div>

                            <div className="space-y-2">
                                <Slider
                                    label="Umbral Visual"
                                    size="sm"
                                    step={1}
                                    minValue={0}
                                    maxValue={100}
                                    value={visualThreshold}
                                    onChange={(value) => setVisualThreshold(value as number)}
                                    className="max-w-md"
                                    color="danger"
                                    showTooltip={true}
                                />
                                <p className="text-xs text-gray-500 mt-1">Nivel mínimo para considerar "voz" (visual).</p>
                            </div>

                            <div className="space-y-2 col-span-1 md:col-span-2">
                                <div className="flex items-center justify-between bg-black/5 dark:bg-white/5 p-3 rounded-lg border border-black/10 dark:border-white/10">
                                    <div>
                                        <p className="text-sm font-bold title-semi-neon flex items-center gap-2">
                                            👥 Identificar Locutores (Diarización)
                                            <span className="px-1.5 py-0.5 text-[9px] bg-amber-500/20 text-amber-500 rounded border border-amber-500/30 uppercase tracking-widest font-black">Beta</span>
                                        </p>
                                        <p className="text-xs text-gray-500 mt-1">Separa el texto indicando [Locutor 1], [Locutor 2]. Requiere más recursos del servidor.</p>
                                    </div>
                                    <button
                                        onClick={() => setDiarization(!diarization)}
                                        disabled={isRecording}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-300 focus:outline-none ${isRecording ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${diarization ? 'bg-indigo-500' : 'bg-gray-400 dark:bg-gray-600'}`}
                                    >
                                        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-300 ${diarization ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </CardBody>
                </Card>
            )}

            {/* Confirmation Modal */}
            <Modal
                isOpen={isOpen}
                onOpenChange={onOpenChange}
                backdrop="blur"
                classNames={{
                    base: isLight ? "bg-white/95 border border-slate-200 backdrop-blur-xl shadow-2xl" : "bg-slate-900/95 border border-white/10 backdrop-blur-xl shadow-2xl",
                    header: isLight ? "border-b border-slate-100" : "border-b border-white/5",
                    footer: isLight ? "border-t border-slate-100" : "border-t border-white/5",
                    closeButton: "hover:bg-black/5 dark:hover:bg-white/10 active:bg-black/10 dark:active:bg-white/20",
                }}
            >
                <ModalContent>
                    {(onClose) => (
                        <>
                            <ModalHeader className="flex flex-col gap-1">
                                <div className="flex items-center gap-2 text-rose-400">
                                    <AlertTriangle size={20} />
                                    <span>¿Finalizar Grabación?</span>
                                </div>
                            </ModalHeader>
                            <ModalBody>
                                <p className={`${isLight ? 'text-slate-600' : 'text-slate-300'} text-sm`}>
                                    ¿Estás seguro de que deseas detener la grabación actual?
                                    La transcripción se guardará y procesará automáticamente.
                                </p>
                                <div className={`p-3 rounded-xl ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-white/5 border-white/10'} border flex items-center justify-between`}>
                                    <span className={`text-xs font-bold ${isLight ? 'text-slate-400' : 'text-slate-400'} uppercase tracking-widest`}>Duración acumulada:</span>
                                    <span className="text-lg font-mono font-bold text-indigo-400">{formatDuration(duration)}</span>
                                </div>
                            </ModalBody>
                            <ModalFooter>
                                <Button variant="light" onPress={onClose} className={`font-semibold ${isLight ? 'text-slate-500 hover:text-slate-900' : 'text-slate-300 hover:text-white'} transition-colors`}>
                                    Continuar grabación
                                </Button>
                                <Button
                                    className="bg-gradient-to-r from-rose-600 to-red-700 text-white font-bold shadow-lg shadow-rose-500/30"
                                    onPress={confirmStop}
                                >
                                    ¡Sí, detener ahora!
                                </Button>
                            </ModalFooter>
                        </>
                    )}
                </ModalContent>
            </Modal>
        </div>
    );
}
