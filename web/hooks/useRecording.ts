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
    const [voiceThreshold, setVoiceThreshold] = useState(300);
    const [silenceThreshold, setSilenceThreshold] = useState(150);
    
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

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;

            // Setup Audio Context for Analysis and Gain
            const audioContext = new AudioContext();
            audioContextRef.current = audioContext;
            
            const source = audioContext.createMediaStreamSource(stream);
            const gain = audioContext.createGain();
            const analyserNode = audioContext.createAnalyser();
            const destination = audioContext.createMediaStreamDestination();

            // Configure Analyser
            analyserNode.fftSize = 256;
            
            // Configure Gain
            gain.gain.value = gainValue;

            // Connect graph: Source -> Gain -> Analyser and Destination
            source.connect(gain);
            gain.connect(analyserNode);
            analyserNode.connect(destination);  // IMPORTANT: Connect analyzer to destination so audio flows

            setAnalyser(analyserNode);
            setGainNode(gain);

            // Use the processed stream for recording
            const mediaRecorder = new MediaRecorder(destination.stream, {
                mimeType: 'audio/webm'
            });

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0 && socket.connected) {
                    // Convert Blob to ArrayBuffer and send
                    event.data.arrayBuffer().then(buffer => {
                        socket.emit('audio_chunk', buffer);
                    });
                }
            };

            mediaRecorder.start(1000); // Send chunks every 1 second
            mediaRecorderRef.current = mediaRecorder;
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

        if (mediaRecorderRef.current) {
            mediaRecorderRef.current.stop();
        }

        if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }

        socket.emit('stop_recording');
        setDuration(0);
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
