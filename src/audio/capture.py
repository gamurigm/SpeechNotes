"""
Audio Capture Module - Single Responsibility Principle
Handles microphone recording and Voice Activity Detection
"""
import pyaudio
import wave
import numpy as np
import tempfile
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
        self.stream = self.audio.open(
            format=self.config.format,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size
        )
        
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
        stream = self.audio.open(
            format=self.config.format,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size
        )
        
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


@dataclass
class VADConfig:
    """Voice Activity Detection configuration"""
    voice_threshold: int = 1200
    silence_threshold: int = 800
    silence_duration: float = 3.0
    min_voice_duration: float = 1.0
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
        stream = self.audio.open(
            format=self.config.format,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size
        )
        
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
    
    def calibrate(self, duration: int = 5) -> VADConfig:
        """
        Calibrate microphone by measuring noise and voice levels
        
        Args:
            duration: Seconds for each phase (silence and voice)
            
        Returns:
            Recommended VAD configuration
        """
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=self.config.format,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            frames_per_buffer=self.config.chunk_size
        )
        
        try:
            # Measure noise
            noise_levels = self._measure_levels(stream, duration, "SILENCIO")
            
            # Measure voice
            voice_levels = self._measure_levels(stream, duration, "HABLA")
            
            # Calculate thresholds
            noise_avg = np.mean(noise_levels)
            noise_max = np.max(noise_levels)
            voice_min = np.min(voice_levels)
            
            voice_threshold = int(noise_max + (voice_min - noise_max) * 0.3)
            silence_threshold = int(noise_max * 1.5)
            
            return VADConfig(
                voice_threshold=voice_threshold,
                silence_threshold=silence_threshold
            )
        
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()
    
    def _measure_levels(self, stream, duration: int, phase_name: str) -> list:
        """Measure audio levels for a duration"""
        levels = []
        samples_per_second = 5
        total_samples = duration * samples_per_second
        
        for _ in range(total_samples):
            data = stream.read(self.config.chunk_size)
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_data).mean()
            levels.append(volume)
        
        return levels
