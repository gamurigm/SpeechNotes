"""
VAD Service - Strategy + State Pattern (Behavioral)

Encapsulates Voice Activity Detection logic, decoupled from
the Socket.IO transport layer.

Design Patterns:
    - Strategy (Behavioral): Different VAD strategies can be
      swapped at runtime (e.g., threshold-based, ML-based).
    - State (Behavioral): The VAD session transitions between
      IDLE → SPEAKING → SILENCE states with defined rules.

SOLID Principles:
    - SRP: Only responsible for determining speech boundaries.
    - OCP: New VAD algorithms can be added via new Strategy classes.
    - DIP: `SocketHandler` depends on the abstract `VADStrategy`,
      not on this concrete implementation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from backend.services.audio.audio_service import AudioUtils


# ──────────────────────────────────────────────
#  VAD State Machine
# ──────────────────────────────────────────────

class VADState(Enum):
    """Possible states for the VAD state machine."""
    IDLE = auto()
    SPEAKING = auto()
    SILENCE_AFTER_SPEECH = auto()


@dataclass
class VADConfig:
    """
    Configuration for the VAD strategy.
    
    Attributes:
        voice_threshold: RMS level above which we consider speech started.
        silence_threshold: RMS level below which we consider silence.
        silence_chunks_to_end: How many consecutive silent chunks to
            wait before ending a phrase.
    """
    voice_threshold: int = 80
    silence_threshold: int = 40
    silence_chunks_to_end: int = 1


@dataclass
class VADResult:
    """
    Result of processing a single audio chunk through VAD.
    
    Attributes:
        state: Current VAD state after processing.
        rms: RMS level of the chunk.
        should_buffer: Whether the chunk should be added to the speech buffer.
        phrase_ended: Whether a complete phrase just ended (trigger transcription).
    """
    state: VADState
    rms: float
    should_buffer: bool
    phrase_ended: bool


# ──────────────────────────────────────────────
#  Abstract Strategy
# ──────────────────────────────────────────────

class VADStrategy(ABC):
    """
    Abstract Strategy for Voice Activity Detection.
    
    Strategy Pattern: Defines the interface for VAD algorithms.
    Different implementations can be swapped at runtime.
    """

    @abstractmethod
    def process_chunk(self, pcm_data: bytes) -> VADResult:
        """
        Process a single audio chunk and return VAD decision.
        
        Args:
            pcm_data: Raw 16-bit mono PCM audio chunk.
            
        Returns:
            VADResult with the detection outcome.
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset the VAD state machine to initial state."""
        ...


# ──────────────────────────────────────────────
#  Concrete Strategy: Threshold-based VAD
# ──────────────────────────────────────────────

class ThresholdVADStrategy(VADStrategy):
    """
    Threshold-based VAD using RMS hysteresis.
    
    State Pattern: Manages transitions between IDLE, SPEAKING, and
    SILENCE_AFTER_SPEECH states based on audio energy levels.
    
    Hysteresis prevents rapid toggling between states by using
    different thresholds for onset (voice_threshold) and offset
    (silence_threshold).
    """

    def __init__(self, config: Optional[VADConfig] = None):
        self.config = config or VADConfig()
        self._state = VADState.IDLE
        self._silence_counter = 0

    @property
    def state(self) -> VADState:
        return self._state

    def process_chunk(self, pcm_data: bytes) -> VADResult:
        """
        Process an audio chunk using threshold-based hysteresis.
        
        State transitions:
            IDLE → SPEAKING:  when RMS > voice_threshold
            SPEAKING → SILENCE_AFTER_SPEECH: when RMS < silence_threshold
            SILENCE_AFTER_SPEECH → IDLE: after N consecutive silent chunks
            SILENCE_AFTER_SPEECH → SPEAKING: if speech resumes
        """
        rms = AudioUtils.calculate_rms(pcm_data)
        should_buffer = False
        phrase_ended = False

        if self._state == VADState.IDLE:
            if rms > self.config.voice_threshold:
                self._state = VADState.SPEAKING
                self._silence_counter = 0
                should_buffer = True

        elif self._state == VADState.SPEAKING:
            should_buffer = True
            if rms < self.config.silence_threshold:
                self._state = VADState.SILENCE_AFTER_SPEECH
                self._silence_counter = 1
            else:
                self._silence_counter = 0

        elif self._state == VADState.SILENCE_AFTER_SPEECH:
            should_buffer = True  # Include trailing silence in phrase
            if rms > self.config.voice_threshold:
                # Speech resumed
                self._state = VADState.SPEAKING
                self._silence_counter = 0
            elif rms < self.config.silence_threshold:
                self._silence_counter += 1
                if self._silence_counter >= self.config.silence_chunks_to_end:
                    # Phrase ended
                    phrase_ended = True
                    self._state = VADState.IDLE
                    self._silence_counter = 0
            else:
                # RMS is between silence_threshold and voice_threshold (Ambiguous zone)
                # Treat as silence to prevent getting permanently stuck
                self._silence_counter += 1
                if self._silence_counter >= self.config.silence_chunks_to_end:
                    phrase_ended = True
                    self._state = VADState.IDLE
                    self._silence_counter = 0

        return VADResult(
            state=self._state,
            rms=rms,
            should_buffer=should_buffer,
            phrase_ended=phrase_ended,
        )

    def reset(self) -> None:
        """Reset state machine to IDLE."""
        self._state = VADState.IDLE
        self._silence_counter = 0
