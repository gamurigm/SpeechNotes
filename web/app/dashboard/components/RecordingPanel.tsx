'use client';

import { useRecording } from '@/hooks/useRecording';
import { Mic, Square } from 'lucide-react';

function formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export function RecordingPanel() {
    const { isRecording, duration, startRecording, stopRecording } = useRecording();

    return (
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

            <div className="flex flex-col">
                <span className="text-sm font-medium text-gray-600">
                    {isRecording ? '🔴 Grabando...' : 'Listo para grabar'}
                </span>
                <span className="text-2xl font-mono font-bold text-gray-900">
                    {formatDuration(duration)}
                </span>
            </div>

            {isRecording && (
                <div className="ml-auto flex items-center gap-2 text-sm text-gray-500">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                    En vivo
                </div>
            )}
        </div>
    );
}
