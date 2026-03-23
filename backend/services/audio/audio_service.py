"""
Audio Service - Adapter Pattern (Structural)

Adapts different audio input formats (WebM, PCM, WAV) to a
unified internal representation (raw PCM 16-bit mono 16kHz).

Design Patterns:
    - Adapter (Structural): Converts incompatible audio interfaces
      into the PCM interface required by the transcription engine.
    - Template Method (Behavioral): `process()` defines the
      skeleton algorithm; subclasses override conversion steps.

SOLID Principles:
    - SRP: Only responsible for audio data transformation.
    - OCP: New formats can be added without modifying existing code.
    - DIP: Depends on the abstract `AudioProcessorPort` interface,
      not on concrete implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional
import struct
import math
import tempfile
import os
import wave
from pathlib import Path


# ──────────────────────────────────────────────
#  Port (Interface) – DIP: high-level modules
#  depend on this abstraction
# ──────────────────────────────────────────────

class AudioProcessorPort(ABC):
    """
    Abstract port for audio processing operations.
    
    Implements the **Adapter Pattern** interface so that any audio
    source (WebM from browser, WAV from file upload, raw PCM) can
    be adapted to the internal PCM format used by the transcriber.
    """

    @abstractmethod
    def to_pcm(self, raw_data: bytes) -> bytes:
        """Convert raw input bytes to PCM 16-bit mono 16kHz."""
        ...

    @abstractmethod
    def get_format_name(self) -> str:
        """Return human-readable name of the source format."""
        ...


# ──────────────────────────────────────────────
#  Concrete Adapters
# ──────────────────────────────────────────────

class PCMPassthroughAdapter(AudioProcessorPort):
    """
    Adapter for data that is already in PCM format.
    Acts as Identity/Null adapter (no conversion needed).
    """

    def to_pcm(self, raw_data: bytes) -> bytes:
        return raw_data

    def get_format_name(self) -> str:
        return "PCM-16bit-mono-16kHz"


class WebMAudioAdapter(AudioProcessorPort):
    """
    Adapter that converts WebM/Opus audio (from browser MediaRecorder)
    to raw PCM using FFmpeg via pydub.
    
    Adapter Pattern: Adapts the WebM interface to the PCM interface
    expected by NVIDIA Riva.
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def to_pcm(self, raw_data: bytes) -> bytes:
        if not raw_data or len(raw_data) < 100:
            return b""
        try:
            from pydub import AudioSegment
            import imageio_ffmpeg
            
            # Explicitly set the ffmpeg executable to the one bundled with imageio-ffmpeg.
            # This fixes the "Couldn't find ffmpeg" RuntimeWarning on Windows.
            AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()

            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(raw_data)
                tmp_path = tmp.name

            try:
                audio = AudioSegment.from_file(tmp_path, format="webm")
                audio = audio.set_channels(1).set_sample_width(2).set_frame_rate(self.sample_rate)
                return audio.raw_data
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
        except Exception as e:
            print(f"[WebMAdapter] Conversion error: {e}")
            return b""

    def get_format_name(self) -> str:
        return "WebM/Opus"


# ──────────────────────────────────────────────
#  Audio utility functions (SRP helpers)
# ──────────────────────────────────────────────

class AudioUtils:
    """
    Pure utility class with static helper methods for PCM operations.
    
    SRP: Only responsible for low-level PCM math; no I/O or state.
    """

    @staticmethod
    def calculate_rms(pcm_data: bytes) -> float:
        """
        Calculate RMS (Root Mean Square) amplitude of 16-bit PCM audio.
        
        Args:
            pcm_data: Raw 16-bit mono PCM bytes.
            
        Returns:
            RMS value as float (0 = silence).
        """
        if not pcm_data:
            return 0.0
        count = len(pcm_data) // 2
        if count == 0:
            return 0.0
        try:
            shorts = struct.unpack(f"{count}h", pcm_data[:count * 2])
            return math.sqrt(sum(s ** 2 for s in shorts) / count)
        except Exception:
            return 0.0

    @staticmethod
    def apply_gain(pcm_data: bytes, gain: float = 1.0) -> bytes:
        """
        Apply volume gain to PCM data with 16-bit clipping.
        
        Args:
            pcm_data: Raw 16-bit mono PCM bytes.
            gain: Multiplier (1.0 = no change, 2.0 = double volume).
            
        Returns:
            Amplified PCM bytes.
        """
        if not pcm_data or gain == 1.0:
            return pcm_data
        count = len(pcm_data) // 2
        if count == 0:
            return pcm_data
        try:
            shorts = struct.unpack(f"{count}h", pcm_data[:count * 2])
            amplified = [max(-32768, min(32767, int(s * gain))) for s in shorts]
            return struct.pack(f"{len(amplified)}h", *amplified)
        except Exception:
            return pcm_data

    @staticmethod
    def save_as_wav(pcm_data: bytes, output_path: Path, sample_rate: int = 16000) -> bool:
        """
        Persist PCM data as a standard WAV file.

        Args:
            pcm_data: Raw 16-bit mono PCM bytes.
            output_path: Destination file path.
            sample_rate: Audio sample rate in Hz.

        Returns:
            True on success.
        """
        if not pcm_data:
            return False
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(pcm_data)
            return True
        except Exception as e:
            print(f"[AudioUtils] WAV save error: {e}")
            return False
