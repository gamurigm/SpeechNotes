'use client';

import { useEffect, useRef, useState } from 'react';
import { useRecording } from '@/hooks/useRecording';
import { Mic, Waves, Sparkles, Volume2, Zap } from 'lucide-react';

export function LiveTranscription() {
    const { messages, isRecording } = useRecording();
    const scrollRef = useRef<HTMLDivElement>(null);
    const [animatedCount, setAnimatedCount] = useState(0);
    const [showWave, setShowWave] = useState(false);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({
                top: scrollRef.current.scrollHeight,
                behavior: 'smooth'
            });
        }
    }, [messages]);

    // Animate counter with wave effect
    useEffect(() => {
        if (messages.length > animatedCount) {
            setShowWave(true);
            const timer = setTimeout(() => {
                setAnimatedCount(messages.length);
                setShowWave(false);
            }, 150);
            return () => clearTimeout(timer);
        }
    }, [messages.length, animatedCount]);

    // Particle animation for recording state
    const particles = Array.from({ length: 8 }, (_, i) => i);

    return (
        <div className="w-full h-full relative overflow-hidden rounded-3xl glass transition-all duration-500">

            {/* Animated mesh gradient background */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                {/* Primary glow */}
                <div className={`absolute -top-32 -left-32 w-96 h-96 bg-gradient-to-br from-cyan-500/30 via-blue-500/20 to-transparent rounded-full blur-[100px] transition-all duration-1000 ${isRecording ? 'opacity-100 scale-110' : 'opacity-30 scale-100'}`} />
                <div className={`absolute -bottom-32 -right-32 w-96 h-96 bg-gradient-to-tl from-violet-500/30 via-purple-500/20 to-transparent rounded-full blur-[100px] transition-all duration-1000 ${isRecording ? 'opacity-100 scale-110' : 'opacity-30 scale-100'}`} />
                <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-gradient-to-r from-pink-500/10 to-rose-500/10 rounded-full blur-[80px] transition-all duration-1000 ${isRecording ? 'opacity-100 animate-pulse' : 'opacity-0'}`} />

                {/* Floating particles when recording */}
                {isRecording && particles.map((i) => (
                    <div
                        key={i}
                        className="absolute w-1 h-1 bg-cyan-400/60 rounded-full animate-float"
                        style={{
                            left: `${10 + i * 12}%`,
                            top: `${20 + (i % 3) * 25}%`,
                            animationDelay: `${i * 0.3}s`,
                            animationDuration: `${2 + i * 0.5}s`
                        }}
                    />
                ))}

                {/* Grid pattern overlay */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:32px_32px] opacity-50" />
            </div>

            {/* Header */}
            <div className="relative z-10 flex items-center justify-between px-6 py-5 border-b border-white/5">
                <div className="flex items-center gap-4">
                    {/* Animated icon container */}
                    <div className="relative">
                        <div className={`p-3 rounded-2xl bg-gradient-to-br ${isRecording ? 'from-rose-500 via-pink-500 to-fuchsia-600' : 'from-cyan-500 via-blue-500 to-indigo-600'} shadow-lg ${isRecording ? 'shadow-rose-500/30' : 'shadow-cyan-500/30'} transition-all duration-500`}>
                            {isRecording ? <Waves size={22} className="text-white animate-pulse" /> : <Mic size={22} className="text-white" />}
                        </div>
                        {/* Ripple effect when recording */}
                        {isRecording && (
                            <>
                                <div className="absolute inset-0 rounded-2xl bg-rose-500/30 animate-ping" />
                                <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-rose-500/20 to-fuchsia-500/20 blur-md animate-pulse" />
                            </>
                        )}
                    </div>

                    <div>
                        <h3 className="text-lg font-bold text-theme-primary tracking-tight flex items-center gap-2">
                            Transcripción en Vivo
                            {isRecording && <Zap size={14} className="text-yellow-400 animate-pulse" />}
                        </h3>
                        <div className="flex items-center gap-2 mt-0.5">
                            <div className={`w-2 h-2 rounded-full ${isRecording ? 'bg-rose-500 animate-pulse shadow-lg shadow-rose-500/50' : 'bg-slate-600'}`} />
                            <p className={`text-sm font-medium ${isRecording ? 'text-rose-400' : 'text-slate-500'}`}>
                                {isRecording ? 'Escuchando activamente...' : 'En espera'}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Segment counter with animation */}
                <div className="flex items-center gap-3">
                    {isRecording && (
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/10 border border-rose-500/20">
                            <Volume2 size={14} className="text-rose-400 animate-pulse" />
                            <span className="text-xs font-semibold text-rose-400">REC</span>
                        </div>
                    )}

                    <div className={`relative px-4 py-2 rounded-2xl bg-gradient-to-r ${messages.length > 0 ? 'from-emerald-500/15 via-teal-500/15 to-cyan-500/15 border-emerald-500/25' : 'bg-white/5 border-white/10'} border backdrop-blur-sm transition-all duration-300 ${showWave ? 'scale-110' : 'scale-100'}`}>
                        <span className={`text-xl font-bold tabular-nums ${messages.length > 0 ? 'text-emerald-400' : 'text-theme-secondary'}`}>
                            {animatedCount}
                        </span>
                        <span className="text-sm text-theme-secondary ml-1.5 font-medium">segmentos</span>

                        {/* Glow effect on new message */}
                        {showWave && (
                            <div className="absolute inset-0 rounded-2xl bg-emerald-400/20 animate-ping" />
                        )}
                    </div>
                </div>
            </div>

            {/* Custom scrollbar styles injected */}
            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 8px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                    margin: 8px 0;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: linear-gradient(180deg, rgba(99, 102, 241, 0.4), rgba(139, 92, 246, 0.4));
                    border-radius: 10px;
                    border: 2px solid transparent;
                    background-clip: padding-box;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: linear-gradient(180deg, rgba(99, 102, 241, 0.7), rgba(139, 92, 246, 0.7));
                    background-clip: padding-box;
                }
                @keyframes float {
                    0%, 100% { transform: translateY(0px) scale(1); opacity: 0.6; }
                    50% { transform: translateY(-20px) scale(1.2); opacity: 1; }
                }
                .animate-float {
                    animation: float 3s ease-in-out infinite;
                }
            `}</style>

            {/* Messages area with custom scrollbar */}
            <div
                ref={scrollRef}
                className="custom-scrollbar relative z-10 h-[calc(100%-88px)] min-h-[400px] overflow-y-auto px-5 py-4 space-y-3"
            >
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center gap-6 py-12">
                        {/* Animated empty state */}
                        <div className="relative">
                            <div className="p-6 rounded-3xl bg-content-glass border border-white/10 shadow-2xl backdrop-blur-md">
                                <Sparkles size={48} className="text-theme-secondary/80" />
                            </div>
                            <div className="absolute -inset-2 rounded-3xl bg-gradient-to-r from-indigo-500/20 via-purple-500/20 to-pink-500/20 blur-xl -z-10 animate-pulse" />
                        </div>
                        <div className="space-y-2">
                            <p className="text-theme-primary text-lg font-semibold">
                                Listo para transcribir
                            </p>
                            <p className="text-theme-secondary text-sm max-w-xs">
                                Presiona el botón de grabación para comenzar a capturar audio en tiempo real
                            </p>
                        </div>
                        <div className="flex gap-2 mt-2">
                            <div className="w-2 h-2 rounded-full bg-cyan-500/50 animate-bounce" style={{ animationDelay: '0s' }} />
                            <div className="w-2 h-2 rounded-full bg-purple-500/50 animate-bounce" style={{ animationDelay: '0.1s' }} />
                            <div className="w-2 h-2 rounded-full bg-pink-500/50 animate-bounce" style={{ animationDelay: '0.2s' }} />
                        </div>
                    </div>
                ) : (
                    messages.map((msg, i) => (
                        <div
                            key={i}
                            className="group relative flex items-start gap-4 p-4 rounded-2xl bg-white/[0.02] hover:bg-white/5 border border-white/5 transition-all duration-300 backdrop-blur-sm animate-in slide-in-from-bottom-3 fade-in"
                            style={{
                                animationDelay: `${Math.min(i * 30, 300)}ms`,
                                animationDuration: '400ms'
                            }}
                        >
                            {/* Glow effect on hover */}
                            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-cyan-500/5 via-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

                            {/* Timestamp badge */}
                            <div className="flex-shrink-0 relative">
                                <div className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600/25 via-blue-600/25 to-cyan-600/25 border border-indigo-500/30 shadow-lg shadow-indigo-500/10">
                                    <span className="text-sm font-mono font-bold text-cyan-300 tracking-wide">
                                        {msg.timestamp}
                                    </span>
                                </div>
                            </div>

                            {/* Text content */}
                            <p className="flex-1 text-base text-[var(--foreground)] leading-relaxed group-hover:text-[var(--foreground)] transition-colors duration-200 text-glow-contrast">
                                {msg.text}
                            </p>

                            {/* Latest message indicator */}
                            {i === messages.length - 1 && (
                                <div className="flex-shrink-0 flex items-center gap-2">
                                    <span className="text-xs font-medium text-emerald-400/70">nuevo</span>
                                    <div className="relative">
                                        <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50" />
                                        <div className="absolute inset-0 rounded-full bg-emerald-400 animate-ping" />
                                    </div>
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>

            {/* Bottom gradient fade - Dynamic based on theme */}
            <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-[var(--bg-color-1)] via-[var(--bg-color-1)]/80 to-transparent pointer-events-none z-20" />

            {/* Top subtle shadow for depth */}
            <div className="absolute top-[88px] left-0 right-0 h-4 bg-gradient-to-b from-black/5 to-transparent pointer-events-none z-10" />
        </div>
    );
}
