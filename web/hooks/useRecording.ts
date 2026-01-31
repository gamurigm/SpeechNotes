/**
 * useRecording Hook
 * Manages audio recording and Socket.IO communication
 */

'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { getSocket, connectSocket, disconnectSocket } from '@/utils/socket';

interface TranscriptionMessage {
    timestamp: string;
    text: string;
}

export function useRecording() {
    const [isRecording, setIsRecording] = useState(false);
    const [duration, setDuration] = useState(0);
    const [messages, setMessages] = useState<TranscriptionMessage[]>([]);
    const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);
    const [gainNode, setGainNode] = useState<GainNode | null>(null);
    const [gainValue, setGainValue] = useState(1.0);
    const [voiceThreshold, setVoiceThreshold] = useState(100);
    const [silenceThreshold, setSilenceThreshold] = useState(60);

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const streamRef = useRef<MediaStream | null>(null);

    useEffect(() => {
        const socket = getSocket();

        socket.on('connected', (data) => {
            console.log('[Socket.IO] Connected:', data);
        });

        socket.on('recording_started', (data) => {
            console.log('[Socket.IO] Recording started:', data);
        });

        socket.on('transcription', (data: TranscriptionMessage) => {
            console.log('[Socket.IO] Transcription:', data);
            setMessages(prev => [...prev, data]);
        });

        socket.on('recording_stopped', (data) => {
            console.log('[Socket.IO] Recording stopped:', data);
            setIsRecording(false);
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
            // Cleanup audio context
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
            }
            if (audioContextRef.current) {
                audioContextRef.current.close();
                audioContextRef.current = null;
            }
            setAnalyser(null);
        });

        socket.on('error', (data) => {
            console.error('[Socket.IO] Error:', data);
        });

        return () => {
            socket.off('connected');
            socket.off('recording_started');
            socket.off('transcription');
            socket.off('recording_stopped');
            socket.off('error');
        };
    }, []);

    // Update gain when state changes
    useEffect(() => {
        if (gainNode) {
            gainNode.gain.value = gainValue;
        }
    }, [gainValue, gainNode]);

    const startRecording = useCallback(async () => {
        try {
            connectSocket();
            const socket = getSocket();

            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            streamRef.current = stream;

            // Setup Audio Context at 16kHz for Riva compatibility
            const audioContext = new AudioContext({ sampleRate: 16000 });
            audioContextRef.current = audioContext;

            const source = audioContext.createMediaStreamSource(stream);
            const gain = audioContext.createGain();
            const analyserNode = audioContext.createAnalyser();

            // Configure Analyser
            analyserNode.fftSize = 256;

            // Configure Gain
            gain.gain.value = gainValue;

            // Connect graph: Source -> Gain -> Analyser
            source.connect(gain);
            gain.connect(analyserNode);

            setAnalyser(analyserNode);
            setGainNode(gain);

            // Use ScriptProcessorNode to capture raw PCM data
            // Buffer size of 4096 at 16kHz = ~256ms per chunk
            const bufferSize = 4096;
            const scriptProcessor = audioContext.createScriptProcessor(bufferSize, 1, 1);

            // Accumulator to send ~4 seconds of audio at a time
            let pcmAccumulator: Int16Array[] = [];
            let samplesAccumulated = 0;
            const samplesPerSecond = 64000;

            scriptProcessor.onaudioprocess = (event) => {
                if (!socket.connected) return;

                const inputData = event.inputBuffer.getChannelData(0);

                // Convert Float32 to Int16 PCM
                const pcmData = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    const s = Math.max(-1, Math.min(1, inputData[i]));
                    pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }

                pcmAccumulator.push(pcmData);
                samplesAccumulated += pcmData.length;

                // Send approximately every 4 seconds of audio
                if (samplesAccumulated >= samplesPerSecond) {
                    // Combine all accumulated chunks
                    const totalLength = pcmAccumulator.reduce((acc, arr) => acc + arr.length, 0);
                    const combined = new Int16Array(totalLength);
                    let offset = 0;
                    for (const chunk of pcmAccumulator) {
                        combined.set(chunk, offset);
                        offset += chunk.length;
                    }

                    // Send as ArrayBuffer
                    socket.emit('audio_chunk_pcm', combined.buffer);

                    // Reset accumulator
                    pcmAccumulator = [];
                    samplesAccumulated = 0;
                }

                // Pass through audio (required for ScriptProcessor to work)
                const outputData = event.outputBuffer.getChannelData(0);
                for (let i = 0; i < inputData.length; i++) {
                    outputData[i] = 0; // Mute output to avoid feedback
                }
            };

            // Connect script processor
            analyserNode.connect(scriptProcessor);
            scriptProcessor.connect(audioContext.destination);

            // Store reference for cleanup
            (audioContextRef.current as any)._scriptProcessor = scriptProcessor;

            setIsRecording(true);
            setMessages([]);
            setDuration(0);

            // Notify server with settings
            socket.emit('start_recording', {
                voiceThreshold: voiceThreshold,
                silenceThreshold: silenceThreshold
            });

            // Start duration timer
            intervalRef.current = setInterval(() => {
                setDuration(d => d + 1);
            }, 1000);

        } catch (error) {
            console.error('Error starting recording:', error);
            alert('Error al acceder al micrófono');
        }
    }, [gainValue, voiceThreshold, silenceThreshold]);

    const stopRecording = useCallback(() => {
        const socket = getSocket();

        socket.emit('stop_recording');

        // Immediate Cleanup
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
        }
        if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }

        setIsRecording(false);
        setMessages([]);
        setDuration(0);
        setAnalyser(null);
    }, []);

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
        setSilenceThreshold
    };
}
