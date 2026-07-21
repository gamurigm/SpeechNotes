import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RecordingPanel } from '@/app/dashboard/components/RecordingPanel';
import { useRecording } from '@/app/dashboard/providers/RecordingProvider';

jest.mock('@heroui/react', () => {
    const React = jest.requireActual<typeof import('react')>('react');
    const Container = ({ children }: { children?: React.ReactNode }) => <div>{children}</div>;

    return {
        Button: ({ children, disabled, onPress, ...props }: {
            children?: React.ReactNode;
            disabled?: boolean;
            onPress?: () => void;
            [key: string]: unknown;
        }) => {
            const { isIconOnly, radius, size, variant, ...domProps } = props;
            void isIconOnly;
            void radius;
            void size;
            void variant;
            return <button disabled={disabled} onClick={onPress} {...domProps}>{children}</button>;
        },
        Card: Container,
        CardBody: Container,
        Modal: ({ children, isOpen }: { children?: React.ReactNode; isOpen?: boolean }) => (
            isOpen ? <div role="dialog">{children}</div> : null
        ),
        ModalBody: Container,
        ModalContent: ({ children }: { children?: React.ReactNode | ((onClose: () => void) => React.ReactNode) }) => (
            <div>{typeof children === 'function' ? children(jest.fn()) : children}</div>
        ),
        ModalFooter: Container,
        ModalHeader: Container,
        Slider: () => <input aria-label="slider simulado" type="range" />,
        useDisclosure: () => {
            const [isOpen, setIsOpen] = React.useState(false);
            return {
                isOpen,
                onOpen: () => setIsOpen(true),
                onOpenChange: setIsOpen,
            };
        },
    };
});

jest.mock('@/app/dashboard/providers/RecordingProvider', () => ({
    useRecording: jest.fn(),
}));

jest.mock('@/app/providers', () => ({
    useBackground: () => ({ themeType: 'dark' }),
}));

jest.mock('@/app/dashboard/components/AudioVisualizer', () => ({
    AudioVisualizer: () => <div data-testid="audio-visualizer" />,
}));

const mockedUseRecording = jest.mocked(useRecording);

function recordingState(overrides: Record<string, unknown> = {}) {
    return {
        analyser: null,
        audioDevices: [],
        diarization: false,
        duration: 0,
        gainValue: 1,
        isRecording: false,
        language: 'es',
        refreshAudioDevices: jest.fn(),
        selectedDeviceId: '',
        setDiarization: jest.fn(),
        setGainValue: jest.fn(),
        setLanguage: jest.fn(),
        setSelectedDeviceId: jest.fn(),
        startRecording: jest.fn(),
        stopRecording: jest.fn(),
        ...overrides,
    };
}

describe('RecordingPanel', () => {
    it('inicia la simulación de grabación desde el control principal', async () => {
        const state = recordingState();
        mockedUseRecording.mockReturnValue(state as ReturnType<typeof useRecording>);

        render(<RecordingPanel />);
        await userEvent.click(screen.getByRole('button', { name: 'Iniciar grabación' }));

        expect(state.startRecording).toHaveBeenCalledTimes(1);
        expect(screen.getByText('Listo para grabar')).toBeInTheDocument();
    });

    it('solicita confirmación antes de detener una grabación', async () => {
        const state = recordingState({ isRecording: true, duration: 12 });
        mockedUseRecording.mockReturnValue(state as ReturnType<typeof useRecording>);

        render(<RecordingPanel />);
        await userEvent.click(screen.getByRole('button', { name: 'Detener grabación' }));
        await userEvent.click(await screen.findByRole('button', { name: 'Si, detener ahora' }));

        expect(state.stopRecording).toHaveBeenCalledTimes(1);
    });
});
