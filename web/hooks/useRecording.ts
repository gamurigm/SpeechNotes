'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { AudioGraph } from '@/services/AudioGraph';
import { connectSocket, getSocket } from '@/utils/socket';

type Language = 'auto' | 'en' | 'es';

export interface AudioInputDevice {
    deviceId: string;
    label: string;
}

interface TranscriptionMessage {
    timestamp: string;
    text: string;
}

interface AudioLevelPayload {
    rms?: number;
    gain?: number;
    timestamp?: string;
}

interface TranscriptionStatusPayload {
    event?: string;
    rms?: number;
    buffer_seconds?: number;
    queue_size?: number;
    segment_id?: number;
    timestamp?: string;
    reason?: string;
    chars?: number;
    max_segment_seconds?: number;
}

export interface LiveTranscriptionStatus {
    event: string;
    label: string;
    rms?: number;
    bufferSeconds?: number;
    queueSize?: number;
    segmentId?: number;
    updatedAt: number;
}

type RecordingSocket = ReturnType<typeof getSocket>;

function toFiniteNumber(value: unknown): number | undefined {
    return typeof value === 'number' && Number.isFinite(value) ? value : undefined;
}

function waitForSocketConnection(socket: RecordingSocket, timeoutMs = 5000): Promise<void> {
    if (socket.connected) return Promise.resolve();

    return new Promise((resolve, reject) => {
        const timeout = window.setTimeout(() => {
            cleanup();
            reject(new Error('Timeout conectando al backend'));
        }, timeoutMs);

        const cleanup = () => {
            window.clearTimeout(timeout);
            socket.off('connect', handleConnect);
            socket.off('connect_error', handleError);
        };
        const handleConnect = () => {
            cleanup();
            resolve();
        };
        const handleError = (error: Error) => {
            cleanup();
            reject(error);
        };

        socket.once('connect', handleConnect);
        socket.once('connect_error', handleError);
    });
}

function waitForRecordingStarted(socket: RecordingSocket, timeoutMs = 7000): Promise<void> {
    return new Promise((resolve, reject) => {
        const timeout = window.setTimeout(() => {
            cleanup();
            reject(new Error('Timeout iniciando grabacion en backend'));
        }, timeoutMs);

        const cleanup = () => {
            window.clearTimeout(timeout);
            socket.off('recording_started', handleStarted);
            socket.off('error', handleError);
        };
        const handleStarted = () => {
            cleanup();
            resolve();
        };
        const handleError = (data: unknown) => {
            const message = typeof data === 'object' && data !== null && 'message' in data
                ? String((data as { message?: unknown }).message)
                : 'Error iniciando grabacion';
            cleanup();
            reject(new Error(message));
        };

        socket.once('recording_started', handleStarted);
        socket.once('error', handleError);
    });
}

function statusFromBackend(data: TranscriptionStatusPayload): LiveTranscriptionStatus {
    const event = data.event || 'status';
    const rms = toFiniteNumber(data.rms);
    const bufferSeconds = toFiniteNumber(data.buffer_seconds);
    const queueSize = toFiniteNumber(data.queue_size);
    const segmentId = toFiniteNumber(data.segment_id);
    const segmentText = segmentId ? ` #${segmentId}` : '';
    const rmsSuffix = rms !== undefined ? `, RMS ${rms}` : '';
    const capturingLabel = bufferSeconds && bufferSeconds > 0
        ? `Audio recibido: ${bufferSeconds.toFixed(1)}s acumulados${rmsSuffix}`
        : `Audio llegando${rmsSuffix}`;

    const labels: Record<string, string> = {
        recording_started: `Backend listo; corte maximo ${data.max_segment_seconds || 8}s`,
        capturing: capturingLabel,
        segment_queued: `Segmento${segmentText} en cola ASR`,
        asr_started: `ASR procesando segmento${segmentText}`,
        segment_discarded: `Segmento${segmentText} sin texto util`,
        transcription_received: `Texto recibido del segmento${segmentText}`,
    };

    return {
        event,
        label: labels[event] || 'Procesando audio',
        rms,
        bufferSeconds,
        queueSize,
        segmentId,
        updatedAt: Date.now(),
    };
}

function statusFromAudioLevel(data: AudioLevelPayload): LiveTranscriptionStatus {
    const rms = toFiniteNumber(data.rms);
    const rmsLabel = rms === undefined ? '' : `, RMS ${rms}`;
    return {
        event: 'audio_level',
        label: `Audio recibido${rmsLabel}`,
        rms,
        updatedAt: Date.now(),
    };
}

export function useRecording() {
    const [isRecording, setIsRecording] = useState(false);
    const [duration, setDuration] = useState(0);
    const [messages, setMessages] = useState<TranscriptionMessage[]>([]);
    const [liveStatus, setLiveStatus] = useState<LiveTranscriptionStatus | null>(null);
    const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);
    const [gainValue, setGainValue] = useState(1.0);
    const [voiceThreshold, setVoiceThreshold] = useState(500);
    const [silenceThreshold, setSilenceThreshold] = useState(200);
    const [language, setLanguage] = useState<Language>('es');
    const [diarization, setDiarization] = useState(false);
    const [audioDevices, setAudioDevices] = useState<AudioInputDevice[]>([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState('');

    const audioGraphRef = useRef<AudioGraph | null>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    const setStatus = useCallback((event: string, label: string) => {
        setLiveStatus({ event, label, updatedAt: Date.now() });
    }, []);
    const refreshAudioDevices = useCallback(async () => {
        if (!navigator.mediaDevices?.enumerateDevices) return;
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const inputs = devices
                .filter(device => device.kind === 'audioinput')
                .map((device, index) => ({
                    deviceId: device.deviceId,
                    label: device.label || `Microfono ${index + 1}`,
                }));
            setAudioDevices(inputs);
            setSelectedDeviceId(current => (
                current && inputs.some(device => device.deviceId === current) ? current : ''
            ));
        } catch (error) {
            console.warn('[Audio] Could not enumerate input devices:', error);
        }
    }, []);


    const stopRecordingInternal = useCallback(() => {
        if (audioGraphRef.current) {
            audioGraphRef.current.dispose();
            audioGraphRef.current = null;
        }

        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }

        setIsRecording(false);
        setAnalyser(null);
        setDuration(0);
    }, []);

    useEffect(() => {
        const socket = getSocket() as typeof getSocket extends () => infer R ? R & { __recordingListenersInstalled?: boolean } : never;

        if (socket.__recordingListenersInstalled) {
            return;
        }
        socket.__recordingListenersInstalled = true;

        const handleConnected = (data: unknown) => {
            console.log('[Socket] Connected:', data);
            setStatus('connected', 'Socket conectado');
        };
        const handleStarted = (data: unknown) => {
            console.log('[Socket] Started:', data);
            setStatus('recording_started', 'Backend listo; capturando audio');
        };
        const handleStopped = (data: unknown) => {
            console.log('[Socket] Stopped:', data);
            setStatus('recording_stopped', 'Grabacion detenida; esperando cierre del ASR');
            stopRecordingInternal();
        };
        const handleAudioLevel = (data: AudioLevelPayload) => {
            setLiveStatus(statusFromAudioLevel(data));
        };
        const handleTranscriptionStatus = (data: TranscriptionStatusPayload) => {
            setLiveStatus(statusFromBackend(data));
        };
        const handleTranscription = (data: TranscriptionMessage) => {
            console.log('[Socket] Transcription:', data);
            setMessages(prev => [...prev, data]);
            setStatus('transcription_received', 'Texto recibido');
        };
        const handleError = (data: unknown) => {
            const message = typeof data === 'object' && data !== null && 'message' in data
                ? String((data as { message?: unknown }).message)
                : JSON.stringify(data);
            console.warn('[Socket] Backend Error:', message);
            setStatus('error', message || 'Error del backend');
        };

        socket.on('connected', handleConnected);
        socket.on('recording_started', handleStarted);
        socket.on('audio_level', handleAudioLevel);
        socket.on('transcription_status', handleTranscriptionStatus);
        socket.on('transcription', handleTranscription);
        socket.on('recording_stopped', handleStopped);
        socket.on('error', handleError);
        // Nota: no se desregistran en el cleanup porque el socket es un singleton
        // de módulo con la misma vida útil que la página. Registrarlos una sola
        // vez evita la doble suscripción que React 18 Strict Mode produciría al
        // desmontar/remontar el efecto, y que duplicaba los eventos entrantes
        // (p. ej. warning "Encountered two children with the same key").
    }, [setStatus, stopRecordingInternal]);

    useEffect(() => {
        const refreshSoon = () => window.setTimeout(() => void refreshAudioDevices(), 0);
        const timeoutIds = new Set<number>();
        const scheduleRefresh = () => {
            const timeoutId = refreshSoon();
            timeoutIds.add(timeoutId);
        };

        scheduleRefresh();
        const mediaDevices = navigator.mediaDevices;
        if (!mediaDevices?.addEventListener) {
            return () => timeoutIds.forEach(timeoutId => window.clearTimeout(timeoutId));
        }

        const handleDeviceChange = () => scheduleRefresh();
        mediaDevices.addEventListener('devicechange', handleDeviceChange);
        return () => {
            timeoutIds.forEach(timeoutId => window.clearTimeout(timeoutId));
            mediaDevices.removeEventListener('devicechange', handleDeviceChange);
        };
    }, [refreshAudioDevices]);
    useEffect(() => {
        let cancelled = false;

        fetch('/api/config/vad')
            .then(res => (res.ok ? res.json() : null))
            .then(data => {
                if (cancelled || !data) return;
                if (typeof data.voice_threshold === 'number') setVoiceThreshold(data.voice_threshold);
                if (typeof data.silence_threshold === 'number') setSilenceThreshold(data.silence_threshold);
            })
            .catch(error => console.warn('[VAD] Could not load saved config:', error));

        return () => {
            cancelled = true;
        };
    }, []);

    useEffect(() => {
        if (audioGraphRef.current) audioGraphRef.current.setGain(gainValue);
    }, [gainValue]);

    const startRecording = useCallback(async () => {
        let graph: AudioGraph | null = null;

        try {
            const socket = getSocket();
            setMessages([]);
            setDuration(0);
            setStatus('connecting', 'Conectando al backend');
            connectSocket();
            await waitForSocketConnection(socket);

            graph = new AudioGraph((audioData) => {
                socket.emit('audio_chunk_pcm', audioData);
            });

            setStatus('microphone', 'Solicitando microfono');
            await graph.initialize(16000, selectedDeviceId || undefined);
            await refreshAudioDevices();

            setStatus('starting_backend', 'Iniciando ASR en backend');
            const recordingStarted = waitForRecordingStarted(socket);
            socket.emit('start_recording', {
                voiceThreshold,
                silenceThreshold,
                language,
                diarization,
            });
            await recordingStarted;

            const analyserNode = graph.createGraph({
                sampleRate: 16000,
                fftSize: 256,
                gain: gainValue,
            });

            audioGraphRef.current = graph;
            setAnalyser(analyserNode);
            setIsRecording(true);
            setStatus('recording', 'Grabando; esperando audio');

            if (intervalRef.current) clearInterval(intervalRef.current);
            intervalRef.current = setInterval(() => {
                setDuration(current => current + 1);
            }, 1000);
        } catch (error) {
            if (graph) graph.dispose();
            console.error('Error starting recording:', error);
            const message = error instanceof Error ? error.message : 'Error al acceder al microfono';
            setStatus('error', message);
            alert(`${message}. Verifique permisos y conexion del backend.`);
        }
    }, [diarization, gainValue, language, refreshAudioDevices, selectedDeviceId, setStatus, silenceThreshold, voiceThreshold]);

    const stopRecording = useCallback(() => {
        const socket = getSocket();
        setStatus('stopping', 'Enviando ultimo audio al backend');
        stopRecordingInternal();
        socket.emit('stop_recording');
    }, [setStatus, stopRecordingInternal]);

    return {
        isRecording,
        duration,
        messages,
        liveStatus,
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
        audioDevices,
        selectedDeviceId,
        setSelectedDeviceId,
        refreshAudioDevices,
    };
}
