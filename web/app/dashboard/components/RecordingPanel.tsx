'use client';

import { useRecording } from '@/hooks/useRecording';
import { Mic, Square, Settings2 } from 'lucide-react';
import { AudioVisualizer } from './AudioVisualizer';
import { useState } from 'react';
import { Card, CardBody, Button, Slider } from '@heroui/react';

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

    const [showSettings, setShowSettings] = useState(false);
    const [visualThreshold, setVisualThreshold] = useState(20); // Visual threshold

    return (
        <div className="flex flex-col gap-2">
            <Card className="shadow-sm border-none glass">
                <CardBody className="px-3 py-2">
                    <div className="flex items-center gap-2">
                        <Button
                            onPress={isRecording ? stopRecording : startRecording}
                            isIconOnly
                            size="lg"
                            radius="full"
                            className={`min-w-14 h-14 font-bold shadow-lg transition-all duration-300 transform hover:scale-110 ${isRecording
                                ? 'bg-gradient-to-br from-red-500 to-red-700 text-white animate-pulse shadow-red-400/50 hover:shadow-red-500/70'
                                : 'bg-gradient-to-br from-blue-500 via-blue-600 to-purple-700 text-white hover:shadow-blue-500/50 hover:from-blue-600 hover:to-purple-800'
                                }`}
                        >
                            {isRecording ? <Square size={24} /> : <Mic size={24} />}
                        </Button>

                        <div className="flex flex-col">
                            <span className="text-xs text-gray-500">
                                {isRecording ? '🔴 Grabando' : 'Listo para grabar'}
                            </span>
                            <span className="text-lg font-mono font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
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
                            size="sm"
                            variant="light"
                            color={showSettings ? "primary" : "default"}
                            title="Configuración de Audio"
                        >
                            <Settings2 size={14} />
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
        </div>
    );
}
