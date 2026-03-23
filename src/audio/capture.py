"""
Audio Capture Module - Single Responsibility Principle
Handles microphone recording and Voice Activity Detection
"""
try:
    import pyaudio
except ImportError:
    class MockPyAudio:
        paInt16 = 8
        def PyAudio(self): return self
        def __init__(self, *args, **kwargs): pass
        def open(self, *args, **kwargs): return self
        def read(self, *args, **kwargs): return b''
        def stop_stream(self, *args, **kwargs): pass
        def close(self, *args, **kwargs): pass
        def terminate(self, *args, **kwargs): pass
        def get_sample_size(self, *args, **kwargs): return 2
    pyaudio = MockPyAudio()
import wave
import numpy as np
import tempfile
import threading
import os
from abc import ABC, abstractmethod
from typing import Optional, Generator
from dataclasses import dataclass


@dataclass
class AudioConfig:
    """Audio configuration settings"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    format: int = pyaudio.paInt16
    # Optional input device index (useful to capture loopback / stereo mix)
    input_device_index: int = None


class AudioRecorder(ABC):
    """
    Abstract base for audio recorders
    OCP: Open for extension, closed for modification
    """
    
    def __init__(self, config: AudioConfig = None):
        self.config = config or AudioConfig()
        self.audio = pyaudio.PyAudio()
    
    @abstractmethod
    def record(self) -> bytes:
        """Record audio and return WAV data"""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.audio.terminate()
    
    def _frames_to_wav(self, frames: list) -> bytes:
        """Convert audio frames to WAV bytes"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            with wave.open(tmp_path, 'wb') as wf:
                wf.setnchannels(self.config.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.config.format))
                wf.setframerate(self.config.sample_rate)
                wf.writeframes(b''.join(frames))
            
            with open(tmp_path, 'rb') as f:
                return f.read()
        finally:
            import os
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass


class MicrophoneStream(AudioRecorder):
    """
    Continuous microphone stream for real-time transcription
    SRP: Only responsible for providing audio stream
    """
    
    def __init__(self, config: AudioConfig = None):
        super().__init__(config)
        self.stream = None
    
    def record(self) -> Generator[bytes, None, None]:
        """
        Stream audio chunks from microphone
        
        Yields:
            Audio chunk bytes
        """
        open_kwargs = dict(
            format=self.config.format,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size,
        )
        if getattr(self.config, 'input_device_index', None) is not None:
            open_kwargs['input_device_index'] = self.config.input_device_index

        self.stream = self.audio.open(**open_kwargs)
        
        try:
            while True:
                yield self.stream.read(self.config.chunk_size)
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()


class ContinuousRecorder(AudioRecorder):
    """
    Records audio continuously until stopped
    SRP: Only responsible for continuous recording
    """
    
    def record(self, stop_callback=None) -> bytes:
        """
        Record continuously until interrupted or callback returns True
        
        Args:
            stop_callback: Optional callback to check if recording should stop
            
        Returns:
            Complete audio as WAV bytes
        """
        open_kwargs = dict(
            format=self.config.format,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size,
        )
        if getattr(self.config, 'input_device_index', None) is not None:
            open_kwargs['input_device_index'] = self.config.input_device_index

        stream = self.audio.open(**open_kwargs)
        
        frames = []
        
        try:
            while True:
                data = stream.read(self.config.chunk_size)
                frames.append(data)
                
                if stop_callback and stop_callback(len(frames)):
                    break
        
        finally:
            stream.stop_stream()
            stream.close()
        
        return self._frames_to_wav(frames)


class BackgroundRecorder(AudioRecorder):
    """
    Background recorder that captures audio until stop() is called.
    Useful to record everything that is playing (if input_device_index points
    to a loopback/stereo-mix device) or the default input otherwise.
    """

    def __init__(self, config: AudioConfig = None):
        super().__init__(config)
        self._frames = []
        self._thread = None
        self._stop_event = threading.Event()
        self._stream = None

    def _worker(self):
        open_kwargs = dict(
            format=self.config.format,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size,
        )
        if getattr(self.config, 'input_device_index', None) is not None:
            open_kwargs['input_device_index'] = self.config.input_device_index

        self._stream = self.audio.open(**open_kwargs)
        try:
            while not self._stop_event.is_set():
                try:
                    data = self._stream.read(self.config.chunk_size)
                except Exception:
                    # Ignore intermittent read errors (e.g., overflow)
                    continue
                self._frames.append(data)
        finally:
            if self._stream:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                except Exception:
                    pass

    def start(self):
        """Start background recording."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._frames = []
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop_and_save(self, out_path: str) -> None:
        """Stop recording and save WAV to out_path."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)

        # Write WAV file
        try:
            with wave.open(out_path, 'wb') as wf:
                wf.setnchannels(self.config.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.config.format))
                wf.setframerate(self.config.sample_rate)
                wf.writeframes(b''.join(self._frames))
        except Exception as e:
            raise

    def record(self) -> bytes:
        """
        Blocking record method to satisfy AudioRecorder abstract API.

        This will block until stop_event is set (i.e., until stop_and_save
        or an external setter calls stop). After stopping, it returns the WAV
        bytes of the recorded session.
        """
        # If not already recording, start
        if not (self._thread and self._thread.is_alive()):
            self.start()

        # Wait until stopped
        self._stop_event.wait()

        # Ensure thread joined
        if self._thread:
            self._thread.join(timeout=5.0)

        # Return WAV bytes using helper
        return self._frames_to_wav(self._frames)


@dataclass
class VADConfig:
    """Voice Activity Detection configuration"""
    voice_threshold: int = 400      # Lowered from 1200 for better sensitivity
    silence_threshold: int = 200    # Lowered from 800 for better sensitivity
    silence_duration: float = 2.0   # Reduced from 3.0s for faster response
    min_voice_duration: float = 0.5 # Reduced from 1.0s to capture shorter phrases
    max_duration: float = 30.0


class VADRecorder(AudioRecorder):
    """
    Voice Activity Detection recorder
    Records only when voice is detected, stops on silence
    SRP: Only responsible for VAD-based recording
    """
    
    def __init__(self, audio_config: AudioConfig = None, vad_config: VADConfig = None):
        super().__init__(audio_config)
        self.vad_config = vad_config or VADConfig()
    
    def record(self, on_voice_detected=None, on_recording=None) -> Optional[bytes]:
        """
        Record with voice activity detection
        
        Args:
            on_voice_detected: Callback when voice is first detected
            on_recording: Callback during recording with elapsed time
            
        Returns:
            Recorded audio as WAV bytes, or None if no voice detected
        """
        open_kwargs = dict(
            format=self.config.format,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size,
        )
        if getattr(self.config, 'input_device_index', None) is not None:
            open_kwargs['input_device_index'] = self.config.input_device_index

        stream = self.audio.open(**open_kwargs)
        
        try:
            # Wait for voice
            if not self._wait_for_voice(stream):
                return None
            
            if on_voice_detected:
                on_voice_detected()
            
            # Record while voice present
            frames = self._record_until_silence(stream, on_recording)
            
            if not frames:
                return None
            
            return self._frames_to_wav(frames)
        
        finally:
            stream.stop_stream()
            stream.close()
    
    def _wait_for_voice(self, stream, max_wait_seconds: float = 60.0) -> bool:
        """Wait for voice activity"""
        max_chunks = int(
            self.config.sample_rate / self.config.chunk_size * max_wait_seconds
        )
        
        for _ in range(max_chunks):
            data = stream.read(self.config.chunk_size)
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_data).mean()
            
            if volume > self.vad_config.voice_threshold:
                return True
        
        return False
    
    def _record_until_silence(self, stream, on_recording=None) -> list:
        """Record until silence detected"""
        frames = []
        max_chunks = int(
            self.config.sample_rate / self.config.chunk_size * 
            self.vad_config.max_duration
        )
        silence_chunks_needed = int(
            self.config.sample_rate / self.config.chunk_size * 
            self.vad_config.silence_duration
        )
        min_voice_chunks = int(
            self.config.sample_rate / self.config.chunk_size * 
            self.vad_config.min_voice_duration
        )
        
        silence_chunks_count = 0
        
        for i in range(max_chunks):
            data = stream.read(self.config.chunk_size)
            frames.append(data)
            
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_data).mean()
            
            if on_recording and i % (self.config.sample_rate // self.config.chunk_size) == 0:
                elapsed = len(frames) * self.config.chunk_size / self.config.sample_rate
                on_recording(elapsed)
            
            # Check for silence
            if volume < self.vad_config.silence_threshold:
                silence_chunks_count += 1
                if silence_chunks_count >= silence_chunks_needed and len(frames) >= min_voice_chunks:
                    break
            else:
                silence_chunks_count = 0
        
        return frames if len(frames) >= min_voice_chunks else []


class MicrophoneCalibrator:
    """
    Calibrates microphone for optimal VAD thresholds
    SRP: Only responsible for microphone calibration
    """
    
    def __init__(self, config: AudioConfig = None):
        self.config = config or AudioConfig()
        self.audio = pyaudio.PyAudio()
        self.stream = None

    def __enter__(self):
        open_kwargs = dict(
            format=self.config.format,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size,
        )
        if getattr(self.config, 'input_device_index', None) is not None:
            open_kwargs['input_device_index'] = self.config.input_device_index

        self.stream = self.audio.open(**open_kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

    def calibrate(self, duration: int = 5) -> VADConfig:
        """
        Calibrate microphone by measuring noise and voice levels
        
        Args:
            duration: Seconds for each phase (silence and voice)
            
        Returns:
            Recommended VAD configuration
        """
        with self as calibrator:
            # Measure noise
            print("Por favor, guarda silencio para medir el ruido de fondo...")
            noise_levels = calibrator._measure_levels(duration, "SILENCIO")
            print(f"Nivel de ruido medido (promedio): {np.mean(noise_levels):.2f}\n")
            
            # Measure voice
            print("Ahora, por favor, habla con normalidad...")
            voice_levels = calibrator._measure_levels(duration, "HABLA")
            print(f"Nivel de voz medido (promedio): {np.mean(voice_levels):.2f}\n")
            
            return self.calculate_thresholds(noise_levels, voice_levels)

    def calculate_thresholds(self, noise_levels: list, voice_levels: list) -> VADConfig:
        """Calculates VAD thresholds from measured levels."""
        noise_avg = np.mean(noise_levels)
        noise_max = np.max(noise_levels)
        # Ensure voice_levels is not empty and contains valid numbers
        if not voice_levels or not all(isinstance(x, (int, float)) for x in voice_levels):
            print("Advertencia: No se detectaron niveles de voz válidos; usando fallback heurístico.")
            voice_min = noise_max * 3  # Fallback estimate
        else:
            voice_min = np.min(voice_levels)

        # Heuristics for raw thresholds
        raw_voice_threshold = int(noise_max + (voice_min - noise_max) * 0.25)
        raw_silence_threshold = int(noise_avg + (noise_max - noise_avg) * 1.5)

        # Apply sensible minimums so tiny numeric readings from certain devices
        # don't produce extremely low thresholds (e.g., 4 or 54).
        MIN_SILENCE_THRESHOLD = 150
        MIN_VOICE_THRESHOLD = 300

        silence_threshold = max(raw_silence_threshold, MIN_SILENCE_THRESHOLD)
        voice_threshold = max(raw_voice_threshold, MIN_VOICE_THRESHOLD)

        # Ensure voice_threshold is comfortably higher than silence_threshold
        if voice_threshold <= silence_threshold + 40:
            voice_threshold = silence_threshold + 80

        # Final safety: make values integers and non-negative
        silence_threshold = int(max(0, silence_threshold))
        voice_threshold = int(max(0, voice_threshold))

        # Debug info for the user
        print(f"Calibración -> ruido_promedio={noise_avg:.2f}, ruido_max={noise_max:.2f}, voz_min={voice_min:.2f}")
        print(f"Umbrales (raw): voice={raw_voice_threshold}, silence={raw_silence_threshold}")
        print(f"Umbrales (finales): voice={voice_threshold}, silence={silence_threshold}")

        return VADConfig(
            voice_threshold=voice_threshold,
            silence_threshold=silence_threshold
        )

    def _measure_levels(self, duration: int, phase_name: str) -> list:
        """Measure audio levels for a duration"""
        if not self.stream:
            raise RuntimeError("El stream de audio no está abierto. Usa 'with MicrophoneCalibrator() as c:'")

        levels = []
        chunks_to_read = int(duration * self.config.sample_rate / self.config.chunk_size)
        
        print(f"Iniciando fase: {phase_name} ({duration}s)")
        for i in range(chunks_to_read):
            data = self.stream.read(self.config.chunk_size)
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_data).mean()
            levels.append(volume)
            # Simple progress indicator
            print(f"\r   Progreso: [{'#' * int(20 * (i+1)/chunks_to_read):<20}]", end="")
        print("\n")
        
        return levels
