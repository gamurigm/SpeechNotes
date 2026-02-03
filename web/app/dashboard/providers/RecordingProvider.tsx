'use client';

import React, { createContext, useContext, ReactNode } from 'react';
import { useRecording as useRecordingHook } from '@/hooks/useRecording';

type RecordingContextType = ReturnType<typeof useRecordingHook>;

const RecordingContext = createContext<RecordingContextType | undefined>(undefined);

export function RecordingProvider({ children }: { children: ReactNode }) {
    const recording = useRecordingHook();

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
