'use client';

import { useState, useRef, useEffect } from 'react';
import { Mic, AlertCircle, CheckCircle, Volume2, Radio, X } from 'lucide-react';
import { Button } from "@heroui/react";

export function MicTest({ onClose }: { onClose?: () => void }) {
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
        return Math.round(rms * 1000);
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

    useEffect(() => {
        return () => {
            if (isTesting) {
                stopMicTest();
            }
        };
    }, [isTesting]);

    const getStatusColor = () => {
        if (rmsLevel > 300) return 'from-emerald-500 to-teal-500';
        if (rmsLevel > 150) return 'from-amber-500 to-orange-500';
        return 'from-slate-600 to-slate-700';
    };

    const getProgressColor = () => {
        if (rmsLevel > 300) return 'bg-emerald-500';
        if (rmsLevel > 150) return 'bg-amber-500';
        return 'bg-slate-600';
    };

    const getStatusText = () => {
        if (rmsLevel > 300) return 'Señal fuerte';
        if (rmsLevel > 150) return 'Señal media';
        return 'Débil/Silencio';
    };

    return (
        <div className="w-full relative overflow-hidden rounded-2xl glass transition-all duration-500">

            {/* Subtle ambient glow */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
                <div className={`absolute -top-20 -right-20 w-40 h-40 rounded-full blur-[80px] transition-all duration-700 ${isTesting ? 'bg-violet-500/20' : 'bg-slate-700/10'}`} />
                <div className={`absolute -bottom-20 -left-20 w-40 h-40 rounded-full blur-[80px] transition-all duration-700 ${isTesting ? 'bg-indigo-500/15' : 'bg-slate-700/10'}`} />
            </div>

            {/* Header */}
            <div className="relative z-10 flex items-center justify-between px-5 py-4 border-b border-slate-700/30">
                <div className="flex items-center gap-3">
                    <div className={`p-2.5 rounded-xl bg-gradient-to-br ${isTesting ? 'from-violet-500 to-indigo-600' : 'bg-white/5'} shadow-lg transition-all duration-500`}>
                        <Mic size={18} className={`text-white ${isTesting ? 'animate-pulse' : ''}`} />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-theme-primary">Prueba de Micrófono</h3>
                        <p className="text-[10px] text-theme-secondary font-medium">Verifica tu entrada de audio</p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {isTesting && (
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-violet-500/10 border border-violet-500/20">
                            <Radio size={10} className="text-violet-400 animate-pulse" />
                            <span className="text-[9px] font-bold text-violet-400 uppercase tracking-wide">Live</span>
                        </div>
                    )}
                    {onClose && (
                        <Button
                            isIconOnly
                            size="sm"
                            variant="light"
                            className="w-6 h-6 min-w-0 text-slate-500 hover:text-rose-500 transition-colors"
                            onClick={onClose}
                        >
                            <X size={14} />
                        </Button>
                    )}
                </div>
            </div>

            {/* Body */}
            <div className="relative z-10 p-5 space-y-4">

                {/* Status Message */}
                {message && (
                    <div className={`flex items-center gap-2.5 p-3 rounded-xl border backdrop-blur-sm ${status === 'success' ? 'bg-emerald-500/15 border-emerald-500/30' :
                        status === 'error' ? 'bg-rose-500/15 border-rose-500/30' :
                            'bg-content-glass border-white/5'
                        }`}>
                        {status === 'success' && <CheckCircle size={16} className="text-emerald-400" />}
                        {status === 'error' && <AlertCircle size={16} className="text-rose-400" />}
                        {status === 'testing' && <Mic size={16} className="text-violet-400 animate-pulse" />}
                        <span className="text-xs text-theme-primary font-medium">{message}</span>
                    </div>
                )}

                {/* Real-time Levels */}
                {isTesting && (
                    <div className="space-y-4">
                        {/* Current Level */}
                        <div className="space-y-2">
                            <div className="flex justify-between items-center">
                                <span className="text-xs font-medium text-theme-secondary">Nivel Actual</span>
                                <span className={`text-xs font-bold px-2 py-0.5 rounded-md ${rmsLevel > 300 ? 'bg-emerald-500/20 text-emerald-400' :
                                    rmsLevel > 150 ? 'bg-amber-500/20 text-amber-400' :
                                        'bg-theme-secondary/20 text-theme-secondary'
                                    }`}>
                                    {rmsLevel}
                                </span>
                            </div>
                            <div className="h-2 bg-slate-800/80 rounded-full overflow-hidden">
                                <div
                                    className={`h-full ${getProgressColor()} transition-all duration-75 rounded-full`}
                                    style={{ width: `${Math.min((rmsLevel / 500) * 100, 100)}%` }}
                                />
                            </div>
                            <p className="text-[10px] text-slate-500 font-medium">{getStatusText()}</p>
                        </div>

                        {/* Peak Level */}
                        <div className="space-y-2">
                            <div className="flex justify-between items-center">
                                <span className="text-xs font-medium text-theme-secondary">Pico Detectado</span>
                                <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-violet-500/20 text-violet-400">
                                    {peakLevel}
                                </span>
                            </div>
                            <div className="h-2 bg-slate-800/80 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-violet-500 transition-all duration-150 rounded-full"
                                    style={{ width: `${Math.min((peakLevel / 500) * 100, 100)}%` }}
                                />
                            </div>
                        </div>

                        {/* Threshold Info Card */}
                        <div className="p-3 rounded-xl bg-content-glass border border-white/5 space-y-1.5">
                            <div className="flex items-center gap-1.5">
                                <Volume2 size={12} className="text-theme-secondary" />
                                <span className="text-[10px] font-bold text-theme-secondary uppercase tracking-wide">Umbrales de Referencia</span>
                            </div>
                            <div className="text-[11px] text-theme-secondary space-y-0.5">
                                <p>🎙 <span className="text-theme-primary">Voz:</span> &gt; 300 (inicio)</p>
                                <p>🔇 <span className="text-theme-primary">Silencio:</span> &lt; 150 (detener)</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Action Button */}
                <button
                    onClick={isTesting ? stopMicTest : startMicTest}
                    className={`w-full py-3 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all duration-300 ${isTesting
                        ? 'bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white shadow-lg shadow-rose-500/25'
                        : 'bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white shadow-lg shadow-violet-500/25'
                        }`}
                >
                    <Mic size={16} />
                    {isTesting ? 'Detener Prueba' : 'Iniciar Prueba'}
                </button>
            </div>
        </div>
    );
}
