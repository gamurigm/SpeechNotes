'use client';

import { useEffect, useRef } from 'react';
import { useRecording } from '@/hooks/useRecording';

export function LiveTranscription() {
    const { messages } = useRecording();
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <div className="h-full flex flex-col bg-gray-50 rounded-lg border">
            <div className="p-4 border-b bg-white rounded-t-lg">
                <h3 className="text-lg font-semibold text-gray-900">
                    Transcripción en Vivo
                </h3>
                <p className="text-sm text-gray-500">
                    {messages.length} segmentos
                </p>
            </div>

            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-4 space-y-3"
            >
                {messages.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-gray-400">
                        <p className="text-center">
                            Presiona el botón de grabar<br />
                            para comenzar la transcripción
                        </p>
                    </div>
                ) : (
                    messages.map((msg, i) => (
                        <div key={i} className="flex gap-3 animate-fade-in">
                            <span className="text-xs font-mono text-gray-500 mt-1 flex-shrink-0">
                                {msg.timestamp}
                            </span>
                            <p className="text-sm text-gray-700 flex-1">
                                {msg.text}
                            </p>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
