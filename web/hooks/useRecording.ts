/**
 * useRecording Hook - Facade & Observer Pattern
 * 
 * Orchestrates the recording process by coordinating:
 * 1. AudioGraph (Builder/Adapter): Handles Web Audio API complexity.
 * 2. Socket.IO (Observer): Handles real-time communication.
 * 3. React State (Observer): Updates UI based on events.
 * 
 * Refactoring:
 * - Extracted low-level audio logic to AudioGraph.
 * - simplified component state management.
 */

'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { getSocket, connectSocket } from '@/utils/socket';
import { AudioGraph } from '@/services/AudioGraph';

interface TranscriptionMessage {
    timestamp: string;
    text: string;
}

export function useRecording() {
    // UI State
    const [isRecording, setIsRecording] = useState(false);
    const [duration, setDuration] = useState(0);
    const [messages, setMessages] = useState<TranscriptionMessage[]>([]);

    // Audio Visualization
    const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);

    // Settings
    const [gainValue, setGainValue] = useState(1.0);
    const [voiceThreshold, setVoiceThreshold] = useState(50);
    const [silenceThreshold, setSilenceThreshold] = useState(25);
    const [language, setLanguage] = useState<'auto' | 'en' | 'es'>('auto');

    // Refs for cleanup and persistence
    const audioGraphRef = useRef<AudioGraph | null>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    // ──────────────────────────────────────────────
    //  Socket.IO Observer Setup
    // ──────────────────────────────────────────────
    useEffect(() => {
        const socket = getSocket();

        const handleConnected = (data: any) => console.log('[Socket] Connected:', data);
        const handleStarted = (data: any) => console.log('[Socket] Started:', data);
        const handleStopped = (data: any) => {
            console.log('[Socket] Stopped:', data);
            stopRecordingInternal(); // Ensure local state is consistent
        };
        const handleTranscription = (data: TranscriptionMessage) => {
            console.log('[Socket] Transcription:', data);
            setMessages(prev => [...prev, data]);
        };
        const handleError = (data: any) => {
            // Log as warning to prevent triggering Next.js dev overlay for business logic 'errors'
            console.warn('[Socket] Backend Error:', data?.message || JSON.stringify(data));
            if (data instanceof Error) {
                console.warn('[Socket] Error details:', data.message, data.stack);
            }
        };

        socket.on('connected', handleConnected);
        socket.on('recording_started', handleStarted);
        socket.on('transcription', handleTranscription);
        socket.on('recording_stopped', handleStopped);
        socket.on('error', handleError);

        return () => {
            socket.off('connected', handleConnected);
            socket.off('recording_started', handleStarted);
            socket.off('transcription', handleTranscription);
            socket.off('recording_stopped', handleStopped);
            socket.off('error', handleError);
        };
    }, []);

    // ──────────────────────────────────────────────
    //  Gain Control (Observer)
    // ──────────────────────────────────────────────
    useEffect(() => {
        if (audioGraphRef.current) {
            audioGraphRef.current.setGain(gainValue);
        }
    }, [gainValue]);

    // ──────────────────────────────────────────────
    //  Actions (Facade)
    // ──────────────────────────────────────────────

    const startRecording = useCallback(async () => {
        try {
            connectSocket();
            const socket = getSocket();

            // Initialize AudioGraph (Adapter/Builder)
            // Pass a callback to emit data (Observer)
            const graph = new AudioGraph((audioData) => {
                // socket.io buffers emits automatically when not yet connected
                socket.emit('audio_chunk_pcm', audioData);
            });

            await graph.initialize();

            // Build the graph and get analyser for visualization
            const analyserNode = graph.createGraph({
                sampleRate: 16000,
                fftSize: 256,
                gain: gainValue
            });

            audioGraphRef.current = graph;
            setAnalyser(analyserNode);
            setIsRecording(true);
            setMessages([]);
            setDuration(0);

            // Notify server with VAD settings and language
            socket.emit('start_recording', {
                voiceThreshold,
                silenceThreshold,
                language,
            });

            // Start timer
            if (intervalRef.current) clearInterval(intervalRef.current);
            intervalRef.current = setInterval(() => {
                setDuration(d => d + 1);
            }, 1000);

        } catch (error) {
            console.error('Error starting recording:', error);
            alert('Error al acceder al micrófono. Verifique los permisos.');
        }
    }, [gainValue, voiceThreshold, silenceThreshold, language]);

    const stopRecordingInternal = useCallback(() => {
        // Cleanup AudioGraph
        if (audioGraphRef.current) {
            audioGraphRef.current.dispose();
            audioGraphRef.current = null;
        }

        // Cleanup Timer
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }

        setIsRecording(false);
        setAnalyser(null);
        setDuration(0);
    }, []);

    const stopRecording = useCallback(() => {
        const socket = getSocket();
        socket.emit('stop_recording');
        // We wait for 'recording_stopped' event to call stopRecordingInternal
        // But we can also force it locally to be responsive
        stopRecordingInternal();
    }, [stopRecordingInternal]);

    return {
        isRecording,
        duration,
        messages,
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
    };
}
