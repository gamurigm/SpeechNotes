/**
 * AudioGraph
 *
 * Captures microphone audio and emits deterministic 16 kHz mono Int16 PCM.
 * Browser AudioContext sampleRate is not guaranteed to be 16 kHz, so this
 * class explicitly downsamples before sending audio to the backend.
 */

export interface AudioGraphConfig {
    sampleRate: number;
    fftSize: number;
    gain: number;
}

export interface AudioGraphDebugInfo {
    inputSampleRate: number;
    outputSampleRate: number;
    chunkSamples: number;
}

const CHUNK_SECONDS = 0.5;
const INT16_MAX = 0x7FFF;
const INT16_MIN = -0x8000;
const PCM_PROCESSOR_NAME = 'speechnotes-pcm-capture';
const PCM_PROCESSOR_URL = '/audio-worklet-processor.js';

export class AudioGraph {
    private context: AudioContext | null = null;
    private stream: MediaStream | null = null;
    private analyser: AnalyserNode | null = null;
    private gainNode: GainNode | null = null;
    private workletNode: AudioWorkletNode | null = null;
    private targetSampleRate = 16000;
    private inputSampleRate = 16000;
    private samplesPerChunk = 8000;

    private pcmAccumulator: Int16Array[] = [];
    private samplesAccumulated = 0;

    constructor(private readonly onAudioData: (data: ArrayBuffer) => void) { }

    async initialize(sampleRate: number = 16000, deviceId?: string): Promise<void> {
        this.targetSampleRate = sampleRate;
        this.samplesPerChunk = Math.round(sampleRate * CHUNK_SECONDS);

        const audioConstraints: MediaTrackConstraints = {
            channelCount: { ideal: 1 },
            sampleRate: { ideal: sampleRate },
            echoCancellation: false,
            noiseSuppression: false,
            autoGainControl: true,
        };
        if (deviceId) {
            audioConstraints.deviceId = { exact: deviceId };
        }

        this.stream = await navigator.mediaDevices.getUserMedia({
            audio: audioConstraints,
        });

        this.context = new AudioContext();
        this.inputSampleRate = this.context.sampleRate;
        await this.context.audioWorklet.addModule(PCM_PROCESSOR_URL);
    }

    createGraph(config: AudioGraphConfig): AnalyserNode {
        if (!this.context || !this.stream) {
            throw new Error('AudioGraph not initialized. Call initialize() first.');
        }

        this.targetSampleRate = config.sampleRate;
        this.samplesPerChunk = Math.round(config.sampleRate * CHUNK_SECONDS);
        this.inputSampleRate = this.context.sampleRate;

        const source = this.context.createMediaStreamSource(this.stream);

        this.gainNode = this.context.createGain();
        this.gainNode.gain.value = config.gain;

        this.analyser = this.context.createAnalyser();
        this.analyser.fftSize = config.fftSize;

        this.workletNode = new AudioWorkletNode(this.context, PCM_PROCESSOR_NAME, {
            numberOfInputs: 1,
            numberOfOutputs: 1,
            outputChannelCount: [1],
        });
        this.workletNode.port.onmessage = (event: MessageEvent<Float32Array>) => {
            this.handleAudioSamples(event.data);
        };

        source.connect(this.gainNode);
        this.gainNode.connect(this.analyser);
        this.analyser.connect(this.workletNode);
        this.workletNode.connect(this.context.destination);

        if (this.context.state === 'suspended') {
            void this.context.resume();
        }

        console.info('[AudioGraph] capture sampleRate', {
            inputSampleRate: this.inputSampleRate,
            outputSampleRate: this.targetSampleRate,
            chunkSamples: this.samplesPerChunk,
        });

        return this.analyser;
    }

    getDebugInfo(): AudioGraphDebugInfo {
        return {
            inputSampleRate: this.inputSampleRate,
            outputSampleRate: this.targetSampleRate,
            chunkSamples: this.samplesPerChunk,
        };
    }

    private handleAudioSamples(inputData: Float32Array) {
        const resampled = this.downsample(inputData, this.inputSampleRate, this.targetSampleRate);
        const pcmData = this.floatToInt16(resampled);

        this.pcmAccumulator.push(pcmData);
        this.samplesAccumulated += pcmData.length;

        while (this.samplesAccumulated >= this.samplesPerChunk) {
            this.flushChunk(this.samplesPerChunk);
        }
    }

    private downsample(input: Float32Array, inputRate: number, outputRate: number): Float32Array {
        if (inputRate === outputRate) return input;
        if (inputRate < outputRate) return input;

        const ratio = inputRate / outputRate;
        const outputLength = Math.max(1, Math.floor(input.length / ratio));
        const output = new Float32Array(outputLength);

        for (let i = 0; i < outputLength; i++) {
            const start = Math.floor(i * ratio);
            const end = Math.min(input.length, Math.floor((i + 1) * ratio));
            let sum = 0;
            let count = 0;
            for (let j = start; j < end; j++) {
                sum += input[j];
                count += 1;
            }
            output[i] = count > 0 ? sum / count : input[start] || 0;
        }

        return output;
    }

    private floatToInt16(inputData: Float32Array): Int16Array {
        const pcmData = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
            const limited = Math.max(-0.98, Math.min(0.98, inputData[i]));
            pcmData[i] = limited < 0 ? Math.round(limited * -INT16_MIN) : Math.round(limited * INT16_MAX);
        }
        return pcmData;
    }

    private flushChunk(chunkSamples: number) {
        if (this.pcmAccumulator.length === 0) return;

        const combined = new Int16Array(this.samplesAccumulated);
        let offset = 0;
        for (const chunk of this.pcmAccumulator) {
            combined.set(chunk, offset);
            offset += chunk.length;
        }

        const chunkToSend = combined.slice(0, chunkSamples);
        this.onAudioData(chunkToSend.buffer);

        const remaining = combined.slice(chunkSamples);
        this.pcmAccumulator = remaining.length > 0 ? [remaining] : [];
        this.samplesAccumulated = remaining.length;
    }

    private flushAccumulator() {
        if (this.pcmAccumulator.length === 0) return;

        const combined = new Int16Array(this.samplesAccumulated);
        let offset = 0;
        for (const chunk of this.pcmAccumulator) {
            combined.set(chunk, offset);
            offset += chunk.length;
        }

        if (combined.length > 0) this.onAudioData(combined.buffer);
        this.pcmAccumulator = [];
        this.samplesAccumulated = 0;
    }

    setGain(value: number) {
        if (this.gainNode) {
            this.gainNode.gain.value = value;
        }
    }

    dispose() {
        if (this.samplesAccumulated > 0) {
            this.flushAccumulator();
        }

        if (this.workletNode) {
            this.workletNode.port.onmessage = null;
            this.workletNode.disconnect();
            this.workletNode = null;
        }
        if (this.gainNode) {
            this.gainNode.disconnect();
            this.gainNode = null;
        }
        if (this.analyser) {
            this.analyser.disconnect();
            this.analyser = null;
        }
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.context) {
            void this.context.close();
            this.context = null;
        }

        this.pcmAccumulator = [];
        this.samplesAccumulated = 0;
    }
}
