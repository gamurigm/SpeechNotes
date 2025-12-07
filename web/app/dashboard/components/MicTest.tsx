'use client';

import { useState, useRef, useEffect } from 'react';
import { Mic, AlertCircle, CheckCircle } from 'lucide-react';

export function MicTest() {
    const [isTesting, setIsTesting] = useState(false);
    const [rmsLevel, setRmsLevel] = useState(0);
    const [status, setStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
    const [message, setMessage] = useState('');
    const [peakLevel, setPeakLevel] = useState(0);
    
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const animationRef = useRef<number | null>(null);

    const calculateRMS = (dataArray: Uint8Array): number => {
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            const normalized = (dataArray[i] - 128) / 128;
            sum += normalized * normalized;
        }
        const rms = Math.sqrt(sum / dataArray.length);
        return Math.round(rms * 1000); // Scale to 0-1000 range
    };

    const startMicTest = async () => {
        try {
            setStatus('testing');
            setMessage('Iniciando prueba de micrófono...');
            setRmsLevel(0);
            setPeakLevel(0);

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;

            const audioContext = new AudioContext();
            audioContextRef.current = audioContext;

            const source = audioContext.createMediaStreamSource(stream);
            const analyser = audioContext.createAnalyser();
            analyserRef.current = analyser;
            analyser.fftSize = 256;

            source.connect(analyser);

            setIsTesting(true);
            setMessage('Micrófono activo - hable cerca del micrófono');

            const monitorAudio = () => {
                const dataArray = new Uint8Array(analyser.frequencyBinCount);
                analyser.getByteFrequencyData(dataArray);

                const rms = calculateRMS(dataArray);
                setRmsLevel(rms);

                if (rms > peakLevel) {
                    setPeakLevel(rms);
                }

                animationRef.current = requestAnimationFrame(monitorAudio);
            };

            monitorAudio();

        } catch (error) {
            setStatus('error');
            setMessage(`Error: ${error instanceof Error ? error.message : 'No se pudo acceder al micrófono'}`);
            setIsTesting(false);
        }
    };

    const stopMicTest = () => {
        setIsTesting(false);

        if (animationRef.current) {
            cancelAnimationFrame(animationRef.current);
        }

        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
        }

        if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }

        if (peakLevel > 300) {
            setStatus('success');
            setMessage(`✓ Micrófono funcionando bien (Pico: ${peakLevel})`);
        } else if (peakLevel > 100) {
            setStatus('success');
            setMessage(`⚠ Micrófono detectado pero débil (Pico: ${peakLevel}). Intenta aumentar la ganancia.`);
        } else {
            setStatus('error');
            setMessage(`✗ No se detectó audio (Pico: ${peakLevel}). Verifica tu micrófono.`);
        }
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (isTesting) {
                stopMicTest();
            }
        };
    }, [isTesting]);

    const getStatusColor = () => {
        if (rmsLevel > 300) return 'bg-green-500';
        if (rmsLevel > 150) return 'bg-yellow-500';
        return 'bg-gray-300';
    };

    const getStatusText = () => {
        if (rmsLevel > 300) return 'Fuerte';
        if (rmsLevel > 150) return 'Medio';
        return 'Débil/Silencio';
    };

    return (
        <div className="p-4 bg-white rounded-lg shadow-sm border">
            <div className="flex items-center gap-3 mb-4">
                <Mic size={24} className="text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-800">Prueba de Micrófono</h3>
            </div>

            {/* Status Indicator */}
            <div className="mb-4 p-3 bg-gray-50 rounded-lg flex items-center gap-2">
                {status === 'success' && <CheckCircle size={20} className="text-green-500" />}
                {status === 'error' && <AlertCircle size={20} className="text-red-500" />}
                {status === 'testing' && <div className="animate-spin"><Mic size={20} className="text-blue-500" /></div>}
                <span className="text-sm text-gray-700">{message}</span>
            </div>

            {/* Real-time Level Display */}
            {isTesting && (
                <div className="mb-4 space-y-3">
                    <div>
                        <div className="flex justify-between mb-2">
                            <span className="text-sm font-medium text-gray-700">Nivel Actual</span>
                            <span className="text-sm font-bold text-gray-900">{rmsLevel}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                            <div
                                className={`h-full transition-all duration-100 ${getStatusColor()}`}
                                style={{ width: `${Math.min((rmsLevel / 500) * 100, 100)}%` }}
                            />
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{getStatusText()}</p>
                    </div>

                    <div>
                        <div className="flex justify-between mb-2">
                            <span className="text-sm font-medium text-gray-700">Pico Detectado</span>
                            <span className="text-sm font-bold text-gray-900">{peakLevel}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                            <div
                                className="h-full bg-purple-500 transition-all duration-100"
                                style={{ width: `${Math.min((peakLevel / 500) * 100, 100)}%` }}
                            />
                        </div>
                    </div>

                    {/* Voice/Silence Threshold Indicators */}
                    <div className="bg-blue-50 p-2 rounded text-xs text-gray-600 space-y-1">
                        <p>🎙 <strong>Umbral Voz:</strong> &gt; 300 (para iniciar)</p>
                        <p>🔇 <strong>Umbral Silencio:</strong> &lt; 150 (para detener)</p>
                        <p>📊 <strong>Tu nivel:</strong> {rmsLevel}</p>
                    </div>
                </div>
            )}

            {/* Control Buttons */}
            <div className="flex gap-2">
                {!isTesting ? (
                    <button
                        onClick={startMicTest}
                        className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
                    >
                        Iniciar Prueba
                    </button>
                ) : (
                    <button
                        onClick={stopMicTest}
                        className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors"
                    >
                        Detener Prueba
                    </button>
                )}
            </div>

            
        </div>
    );
}
