'use client';

import { useState, useRef, useEffect } from 'react';
import { Mic, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, CardHeader, CardBody, Button, Progress, Chip } from '@heroui/react';

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
        <Card className="shadow-lg border-none">
            <CardHeader className="flex gap-3 px-6 py-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                        <Mic size={24} className="text-blue-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-800">Prueba de Micrófono</h3>
                </div>
            </CardHeader>

            <CardBody className="px-6 py-4 space-y-4">
                {/* Status Indicator */}
                {message && (
                    <div className="p-3 bg-gray-50 rounded-lg flex items-center gap-2">
                        {status === 'success' && <CheckCircle size={20} className="text-green-500" />}
                        {status === 'error' && <AlertCircle size={20} className="text-red-500" />}
                        {status === 'testing' && <div className="animate-spin"><Mic size={20} className="text-blue-500" /></div>}
                        <span className="text-sm text-gray-700">{message}</span>
                    </div>
                )}

                {/* Real-time Level Display */}
                {isTesting && (
                    <div className="space-y-4">
                        <div>
                            <div className="flex justify-between mb-2">
                                <span className="text-sm font-medium text-gray-700">Nivel Actual</span>
                                <Chip size="sm" variant="flat" color={rmsLevel > 300 ? "success" : rmsLevel > 150 ? "warning" : "default"}>
                                    {rmsLevel}
                                </Chip>
                            </div>
                            <Progress 
                                value={Math.min((rmsLevel / 500) * 100, 100)}
                                color={rmsLevel > 300 ? "success" : rmsLevel > 150 ? "warning" : "default"}
                                className="max-w-md"
                            />
                            <p className="text-xs text-gray-500 mt-1">{getStatusText()}</p>
                        </div>

                        <div>
                            <div className="flex justify-between mb-2">
                                <span className="text-sm font-medium text-gray-700">Pico Detectado</span>
                                <Chip size="sm" variant="flat" color="secondary">
                                    {peakLevel}
                                </Chip>
                            </div>
                            <Progress 
                                value={Math.min((peakLevel / 500) * 100, 100)}
                                color="secondary"
                                className="max-w-md"
                            />
                        </div>

                        {/* Voice/Silence Threshold Indicators */}
                        <Card className="bg-blue-50">
                            <CardBody className="py-3 px-4">
                                <div className="text-xs text-gray-700 space-y-1">
                                    <p>🎙 <strong>Umbral Voz:</strong> &gt; 300 (para iniciar)</p>
                                    <p>🔇 <strong>Umbral Silencio:</strong> &lt; 150 (para detener)</p>
                                    <p>📊 <strong>Tu nivel:</strong> {rmsLevel}</p>
                                </div>
                            </CardBody>
                        </Card>
                    </div>
                )}

                {/* Control Buttons */}
                <div className="flex gap-2 pt-2">
                    {!isTesting ? (
                        <Button
                            onPress={startMicTest}
                            color="primary"
                            variant="shadow"
                            className="w-full font-semibold"
                            startContent={<Mic size={18} />}
                        >
                            Iniciar Prueba
                        </Button>
                    ) : (
                        <Button
                            onPress={stopMicTest}
                            color="danger"
                            variant="shadow"
                            className="w-full font-semibold"
                        >
                            Detener Prueba
                        </Button>
                    )}
                </div>
            </CardBody>
        </Card>
    );
}
