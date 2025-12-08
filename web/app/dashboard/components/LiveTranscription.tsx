'use client';

import { useEffect, useRef } from 'react';
import { useRecording } from '@/hooks/useRecording';
import { Card, CardHeader, CardBody, Chip } from '@heroui/react';

export function LiveTranscription() {
    const { messages } = useRecording();
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <Card className="h-full shadow-lg border-none">
            <CardHeader className="flex gap-3 px-6 py-4">
                <div className="flex flex-col flex-1">
                    <h3 className="text-lg font-semibold text-gray-900">
                        Transcripción en Vivo
                    </h3>
                </div>
                <Chip color="primary" variant="flat" size="sm">
                    {messages.length} segmentos
                </Chip>
            </CardHeader>

            <CardBody className="px-6 py-4">
                <div
                    ref={scrollRef}
                    className="h-[400px] overflow-y-auto space-y-4"
                >
                    {messages.length === 0 ? (
                        <div className="flex items-center justify-center h-full text-gray-400">
                            <p className="text-center text-sm">
                                Presiona el botón de grabar<br />
                                para comenzar la transcripción
                            </p>
                        </div>
                    ) : (
                        messages.map((msg, i) => (
                            <div key={i} className="flex gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                                <Chip size="sm" variant="flat" color="default" className="font-mono">
                                    {msg.timestamp}
                                </Chip>
                                <p className="text-sm text-gray-700 flex-1">
                                    {msg.text}
                                </p>
                            </div>
                        ))
                    )}
                </div>
            </CardBody>
        </Card>
    );
}
