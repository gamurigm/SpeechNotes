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
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

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

    const startRecording = useCallback(async () => {
        try {
            connectSocket();
            const socket = getSocket();

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream, {
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

            // Notify server
            socket.emit('start_recording');

            // Start duration timer
            intervalRef.current = setInterval(() => {
                setDuration(d => d + 1);
            }, 1000);

        } catch (error) {
            console.error('Error starting recording:', error);
            alert('Error al acceder al micrófono');
        }
    }, []);

    const stopRecording = useCallback(() => {
        const socket = getSocket();

        if (mediaRecorderRef.current) {
            mediaRecorderRef.current.stop();
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
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
        stopRecording
    };
}
