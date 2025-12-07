'use client';

import { useRecording } from '@/hooks/useRecording';
import { Mic, Square, Settings2 } from 'lucide-react';
import { AudioVisualizer } from './AudioVisualizer';
import { useState } from 'react';

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
            <div className="flex items-center gap-4 p-4 bg-white rounded-lg shadow-sm border">
                <button
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`p-4 rounded-full transition-all ${isRecording
                            ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                            : 'bg-blue-500 hover:bg-blue-600'
                        } text-white shadow-lg`}
                >
                    {isRecording ? <Square size={24} /> : <Mic size={24} />}
                </button>

                <div className="flex flex-col min-w-[120px]">
                    <span className="text-sm font-medium text-gray-600">
                        {isRecording ? '🔴 Grabando...' : 'Listo para grabar'}
                    </span>
                    <span className="text-2xl font-mono font-bold text-gray-900">
                        {formatDuration(duration)}
                    </span>
                </div>

                {/* Visualizer */}
                <div className="flex-1 flex justify-center">
                    <AudioVisualizer 
                        analyser={analyser} 
                        isRecording={isRecording} 
                        threshold={visualThreshold}
                    />
                </div>

                <button 
                    onClick={() => setShowSettings(!showSettings)}
                    className={`p-2 rounded-full hover:bg-gray-100 ${showSettings ? 'bg-gray-100 text-blue-500' : 'text-gray-500'}`}
                    title="Configuración de Audio"
                >
                    <Settings2 size={20} />
                </button>

                {isRecording && (
                    <div className="ml-auto flex items-center gap-2 text-sm text-gray-500">
                        <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                        En vivo
                    </div>
                )}
            </div>

            {/* Settings Panel */}
            {showSettings && (
                <div className="p-4 bg-gray-50 rounded-lg border text-sm animate-in slide-in-from-top-2">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        <div className="flex flex-col gap-2">
                            <label className="font-medium text-gray-700 flex justify-between">
                                Ganancia (Volumen)
                                <span className="text-blue-600">{gainValue.toFixed(1)}x</span>
                            </label>
                            <input 
                                type="range" 
                                min="0.5" 
                                max="10.0" 
                                step="0.1"
                                value={gainValue}
                                onChange={(e) => setGainValue(parseFloat(e.target.value))}
                                className="w-full accent-blue-500"
                            />
                            <p className="text-xs text-gray-500">Aumenta si el audio se detecta muy bajo.</p>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="font-medium text-gray-700 flex justify-between">
                                Umbral Visual
                                <span className="text-blue-600">{visualThreshold}</span>
                            </label>
                            <input 
                                type="range" 
                                min="0" 
                                max="100" 
                                step="1"
                                value={visualThreshold}
                                onChange={(e) => setVisualThreshold(parseInt(e.target.value))}
                                className="w-full accent-red-500"
                            />
                            <p className="text-xs text-gray-500">Nivel mínimo para considerar "voz" (visual).</p>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="font-medium text-gray-700 flex justify-between">
                                Umbral Voz (Inicio)
                                <span className="text-blue-600">{voiceThreshold}</span>
                            </label>
                            <input 
                                type="range" 
                                min="100" 
                                max="2000" 
                                step="50"
                                value={voiceThreshold}
                                onChange={(e) => setVoiceThreshold(parseInt(e.target.value))}
                                className="w-full accent-green-500"
                            />
                            <p className="text-xs text-gray-500">RMS para INICIAR grabación.</p>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="font-medium text-gray-700 flex justify-between">
                                Umbral Silencio (Fin)
                                <span className="text-blue-600">{silenceThreshold}</span>
                            </label>
                            <input 
                                type="range" 
                                min="50" 
                                max="1000" 
                                step="50"
                                value={silenceThreshold}
                                onChange={(e) => setSilenceThreshold(parseInt(e.target.value))}
                                className="w-full accent-purple-500"
                            />
                            <p className="text-xs text-gray-500">RMS para DETENER grabación.</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
