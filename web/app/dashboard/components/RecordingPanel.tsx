'use client';

import { useRecording } from '@/hooks/useRecording';
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
        setSilenceThreshold
    } = useRecording();
    const { theme } = useBackground();
    const isLight = theme === 'pure-light';

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
                        <h4 className="text-base font-semibold mb-4 text-[var(--foreground)] text-glow-contrast">Configuración de Audio</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <Slider
                                    label="Ganancia (Volumen)"
                                    classNames={{
                                        label: "text-xs font-bold text-[var(--foreground)]/60 uppercase tracking-wider",
                                        value: "text-xs font-mono font-bold text-violet-400"
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

                            {/* Voice and silence thresholds moved to Calibrate Audio in dashboard toolbar */}
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
                    base: "bg-slate-900/95 border border-white/10 backdrop-blur-xl",
                    header: "border-b border-white/5",
                    footer: "border-t border-white/5",
                    closeButton: "hover:bg-white/10 active:bg-white/20",
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
                                <p className="text-slate-300 text-sm">
                                    ¿Estás seguro de que deseas detener la grabación actual?
                                    La transcripción se guardará y procesará automáticamente.
                                </p>
                                <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between">
                                    <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Duración acumulada:</span>
                                    <span className="text-lg font-mono font-bold text-indigo-400">{formatDuration(duration)}</span>
                                </div>
                            </ModalBody>
                            <ModalFooter>
                                <Button variant="light" color="default" onPress={onClose} className="font-semibold">
                                    Continuar grabacion
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
