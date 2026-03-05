/**
 * AudioGraph - Builder Pattern & Factory Method
 * 
 * Encapsulates the complexity of the Web Audio API graph construction.
 * 
 * Design Patterns:
 * - Builder: Allows step-by-step construction of the audio graph.
 * - Factory Method: Creates specific node configurations.
 * - Observable (via callback): Notifies when audio data is ready.
 * 
 * SOLID:
 * - SRP: Only handles audio processing graph.
 * - OCP: Can add new nodes or processing steps easily.
 */

export interface AudioGraphConfig {
    sampleRate: number;
    fftSize: number;
    gain: number;
}

export class AudioGraph {
    private context: AudioContext | null = null;
    private stream: MediaStream | null = null;
    private analyser: AnalyserNode | null = null;
    private gainNode: GainNode | null = null;
    private scriptProcessor: ScriptProcessorNode | null = null;

    // PCM Accumulation
    private pcmAccumulator: Int16Array[] = [];
    private samplesAccumulated = 0;
    private readonly SAMPLES_PER_CHUNK = 8000; // ~500ms at 16kHz — enough for real-time VAD

    constructor(private onAudioData: (data: ArrayBuffer) => void) { }

    /**
     * Builder Step 1: Initialize AudioContext and Input Stream
     */
    async initialize(sampleRate: number = 16000): Promise<void> {
        this.stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                sampleRate,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true
            }
        });

        this.context = new AudioContext({ sampleRate });
    }

    /**
     * Builder Step 2: Create and connect nodes
     */
    createGraph(config: AudioGraphConfig): AnalyserNode {
        if (!this.context || !this.stream) {
            throw new Error("AudioGraph not initialized. Call initialize() first.");
        }

        const source = this.context.createMediaStreamSource(this.stream);

        // Factory Method for Gain
        this.gainNode = this.context.createGain();
        this.gainNode.gain.value = config.gain;

        // Factory Method for Analyser
        this.analyser = this.context.createAnalyser();
        this.analyser.fftSize = config.fftSize;

        // Legacy ScriptProcessor (kept for compatibility, could be upgraded to AudioWorklet)
        this.scriptProcessor = this.context.createScriptProcessor(4096, 1, 1);
        this.scriptProcessor.onaudioprocess = this.handleAudioProcess.bind(this);

        // Connect Graph: Source -> Gain -> Analyser -> Processor -> Destination
        source.connect(this.gainNode);
        this.gainNode.connect(this.analyser);
        this.analyser.connect(this.scriptProcessor);
        this.scriptProcessor.connect(this.context.destination);

        return this.analyser;
    }

    /**
     * Process audio buffer (Internal Logic)
     */
    private handleAudioProcess(event: AudioProcessingEvent) {
        const inputData = event.inputBuffer.getChannelData(0);

        // Convert Float32 to Int16 PCM
        const pcmData = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]));
            pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        this.pcmAccumulator.push(pcmData);
        this.samplesAccumulated += pcmData.length;

        // Check if we have enough data to emit (~4s)
        if (this.samplesAccumulated >= this.SAMPLES_PER_CHUNK) {
            this.flushAccumulator();
        }

        // Mute output
        const outputData = event.outputBuffer.getChannelData(0);
        outputData.fill(0);
    }

    private flushAccumulator() {
        if (this.pcmAccumulator.length === 0) return;

        const totalLength = this.pcmAccumulator.reduce((acc, arr) => acc + arr.length, 0);
        const combined = new Int16Array(totalLength);
        let offset = 0;
        for (const chunk of this.pcmAccumulator) {
            combined.set(chunk, offset);
            offset += chunk.length;
        }

        this.onAudioData(combined.buffer);

        this.pcmAccumulator = [];
        this.samplesAccumulated = 0;
    }

    /**
     * Update Gain dynamically
     */
    setGain(value: number) {
        if (this.gainNode) {
            this.gainNode.gain.value = value;
        }
    }

    /**
     * Cleanup resources
     */
    dispose() {
        // Flush any remaining buffered audio before cleanup
        if (this.samplesAccumulated > 0) {
            this.flushAccumulator();
        }

        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.context) {
            this.context.close();
            this.context = null;
        }
        if (this.scriptProcessor) {
            this.scriptProcessor.disconnect();
            this.scriptProcessor.onaudioprocess = null;
            this.scriptProcessor = null;
        }
        this.analyser = null;
        this.gainNode = null;
        this.pcmAccumulator = [];
        this.samplesAccumulated = 0;
    }
}
