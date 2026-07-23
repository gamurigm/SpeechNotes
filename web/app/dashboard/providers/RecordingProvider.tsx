'use client';

import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { useRecording as useRecordingHook } from '@/hooks/useRecording';

type RecordingContextType = ReturnType<typeof useRecordingHook>;

const RecordingContext = createContext<RecordingContextType | undefined>(undefined);

declare global {
    interface Window {
        __speechNotesTest?: {
            startRecording: () => Promise<void>;
            stopRecording: () => void;
        };
    }
}

export function RecordingProvider({ children }: Readonly<{ children: ReactNode }>) {
    const recording = useRecordingHook();

    useEffect(() => {
        window.__speechNotesTest = {
            startRecording: recording.startRecording,
            stopRecording: recording.stopRecording,
        };
    }, [recording.startRecording, recording.stopRecording]);

    return (
        <RecordingContext.Provider value={recording}>
            {children}
        </RecordingContext.Provider>
    );
}

export function useRecording() {
    const context = useContext(RecordingContext);
    if (context === undefined) {
        throw new Error('useRecording must be used within a RecordingProvider');
    }
    return context;
}
