class SpeechNotesPcmCaptureProcessor extends AudioWorkletProcessor {
    process(inputs, outputs) {
        const inputChannel = inputs[0]?.[0];
        if (inputChannel?.length) {
            this.port.postMessage(inputChannel.slice());
        }

        const outputChannel = outputs[0]?.[0];
        if (outputChannel) {
            outputChannel.fill(0);
        }
        return true;
    }
}

registerProcessor('speechnotes-pcm-capture', SpeechNotesPcmCaptureProcessor);
