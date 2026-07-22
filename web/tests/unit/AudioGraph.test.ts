import { AudioGraph } from '../../services/AudioGraph';

describe('AudioGraph', () => {
    let audioGraph: AudioGraph;
    let onAudioDataMock: jest.Mock;

    beforeEach(() => {
        onAudioDataMock = jest.fn();
        audioGraph = new AudioGraph(onAudioDataMock);

        // Mock Web Audio API
        const mockTrack = { stop: jest.fn() };
        const mockStream = {
            getTracks: jest.fn(() => [mockTrack]),
        };

        const mockGain = { value: 1 };
        const mockGainNode = {
            gain: mockGain,
            connect: jest.fn(),
            disconnect: jest.fn(),
        };

        const mockAnalyser = {
            fftSize: 2048,
            connect: jest.fn(),
            disconnect: jest.fn(),
        };

        const mockWorkletNode = {
            port: {
                onmessage: null as ((event: MessageEvent<Float32Array>) => void) | null,
            },
            connect: jest.fn(),
            disconnect: jest.fn(),
        };

        const mockSource = {
            connect: jest.fn(),
        };

        const mockAudioContext = {
            sampleRate: 44100,
            state: 'suspended',
            resume: jest.fn().mockResolvedValue(undefined),
            close: jest.fn().mockResolvedValue(undefined),
            createMediaStreamSource: jest.fn(() => mockSource),
            createGain: jest.fn(() => mockGainNode),
            createAnalyser: jest.fn(() => mockAnalyser),
            audioWorklet: { addModule: jest.fn().mockResolvedValue(undefined) },
            destination: {},
        };

        Object.defineProperty(global, 'navigator', {
            value: {
                mediaDevices: {
                    getUserMedia: jest.fn().mockResolvedValue(mockStream),
                },
            },
            writable: true,
        });

        Object.defineProperty(global, 'AudioContext', {
            value: jest.fn(() => mockAudioContext),
            writable: true,
        });
        Object.defineProperty(global, 'AudioWorkletNode', {
            value: jest.fn(() => mockWorkletNode),
            writable: true,
        });
    });

    test('getDebugInfo returns default or initialized rates', () => {
        const info = audioGraph.getDebugInfo();
        expect(info).toEqual({
            inputSampleRate: 16000,
            outputSampleRate: 16000,
            chunkSamples: 8000,
        });
    });

    test('initialize sets up media stream and audio context', async () => {
        await audioGraph.initialize(16000);
        expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
            audio: expect.objectContaining({
                channelCount: { ideal: 1 },
                sampleRate: { ideal: 16000 },
            }),
        });

        const debugInfo = audioGraph.getDebugInfo();
        expect(debugInfo.inputSampleRate).toBe(44100);
    });

    test('initialize accepts an explicit microphone device', async () => {
        await audioGraph.initialize(16000, 'mic-usb');
        expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
            audio: expect.objectContaining({ deviceId: { exact: 'mic-usb' } }),
        });
    });

    test('rejects graph creation before initialization', () => {
        expect(() => audioGraph.createGraph({ sampleRate: 16000, fftSize: 1024, gain: 1 })).toThrow(
            'AudioGraph not initialized'
        );
    });

    test('createGraph connects audio nodes and sets gain/fftSize', async () => {
        await audioGraph.initialize(16000);
        const analyser = audioGraph.createGraph({
            sampleRate: 16000,
            fftSize: 1024,
            gain: 2.0,
        });

        expect(analyser).toBeDefined();
        expect(audioGraph.getDebugInfo().outputSampleRate).toBe(16000);
    });

    test('setGain updates gain node value', async () => {
        await audioGraph.initialize(16000);
        audioGraph.createGraph({ sampleRate: 16000, fftSize: 1024, gain: 1.0 });

        expect(() => audioGraph.setGain(3.5)).not.toThrow();
    });

    test('dispose cleans up worklet, gain, analyser, tracks and context', async () => {
        await audioGraph.initialize(16000);
        audioGraph.createGraph({ sampleRate: 16000, fftSize: 1024, gain: 1.0 });

        audioGraph.dispose();
        expect(audioGraph.getDebugInfo()).toBeDefined();
    });

    test('processes a full PCM chunk received from the worklet', async () => {
        await audioGraph.initialize(16000);
        audioGraph.createGraph({ sampleRate: 16000, fftSize: 1024, gain: 1.0 });
        const graph = audioGraph as unknown as {
            workletNode: { port: { onmessage: (event: MessageEvent<Float32Array>) => void } };
        };
        const input = new Float32Array(44100).fill(0.25);
        graph.workletNode.port.onmessage({ data: input } as MessageEvent<Float32Array>);
        expect(onAudioDataMock).toHaveBeenCalledTimes(2);
    });
});
