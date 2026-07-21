import { render, screen } from '@testing-library/react';
import { LiveTranscription } from '@/app/dashboard/components/LiveTranscription';
import { useRecording } from '@/app/dashboard/providers/RecordingProvider';

jest.mock('@/app/dashboard/providers/RecordingProvider', () => ({
    useRecording: jest.fn(),
}));

jest.mock('@/app/providers', () => ({
    useBackground: () => ({ themeType: 'dark' }),
}));

const mockedUseRecording = jest.mocked(useRecording);

describe('LiveTranscription', () => {
    it('muestra el estado vacío antes de grabar', () => {
        mockedUseRecording.mockReturnValue({
            isRecording: false,
            liveStatus: null,
            messages: [],
        } as ReturnType<typeof useRecording>);

        render(<LiveTranscription />);

        expect(screen.getByText('Listo para transcribir')).toBeInTheDocument();
        expect(screen.getByText('Standby')).toBeInTheDocument();
    });

    it('presenta los segmentos recibidos durante la grabación', () => {
        mockedUseRecording.mockReturnValue({
            isRecording: true,
            liveStatus: { event: 'transcription_received', label: 'Texto recibido', updatedAt: 1 },
            messages: [{ timestamp: '00:01', text: 'Primera transcripción simulada.' }],
        } as ReturnType<typeof useRecording>);

        render(<LiveTranscription />);

        expect(screen.getByText('Live')).toBeInTheDocument();
        expect(screen.getByText('00:01')).toBeInTheDocument();
        expect(screen.getByText('Primera transcripción simulada.')).toBeInTheDocument();
    });
});
