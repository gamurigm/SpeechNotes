"""
Socket Handler - Facade Pattern (Structural) + Observer Pattern (Behavioral)

Acts as a **Facade** that hides the complexity of the audio-processing
subsystem (AudioService, VADService, TranscriberProxy) behind a clean
Socket.IO event interface.

The Socket.IO event registration itself follows the **Observer** pattern:
clients emit events and this module dispatches them to the appropriate
handler.

Design Patterns:
    - Facade (Structural): `register_socket_events()` is a single entry
      point for all real-time transcription operations.
    - Observer (Behavioral): Socket.IO events act as observable subjects;
      handler functions are observers.
    - Dependency Injection (DIP): Audio processing and VAD are delegated
      to injected service objects, not hard-coded.

SOLID Principles:
    - SRP: This file only handles Socket.IO event routing. Audio
      conversion lives in `audio_service.py`, VAD in `vad_service.py`.
    - DIP: Depends on abstract ports (`AudioProcessorPort`, `VADStrategy`),
      not on concrete implementations.
    - OCP: New events can be added without touching existing handlers.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from dotenv import load_dotenv
import asyncio
import re
import traceback
import unicodedata
import wave
import logfire

load_dotenv()

# ── Service imports (DIP: depend on abstractions) ──
from backend.services.audio.audio_service import (
    AudioProcessorPort,
    WebMAudioAdapter,
    PCMPassthroughAdapter,
    AudioUtils,
)
from backend.services.audio.vad_service import (
    ThresholdVADStrategy,
    VADConfig as ServiceVADConfig,
    VADStrategy,
)

# ── Domain imports ──
from src.transcription import FormatterFactory

# NIM ASR import (Canary/Whisper via Riva gRPC)
from backend.services.audio.asr import ASRService, ASRRequest

# ──────────────────────────────────────────────
#  Module-level singletons (Creational)
# ──────────────────────────────────────────────
active_sessions: dict[str, dict] = {}

# Adapter instances (Structural – Adapter Pattern)
_webm_adapter: AudioProcessorPort = WebMAudioAdapter()
_pcm_adapter: AudioProcessorPort = PCMPassthroughAdapter()

SAMPLE_RATE = 16000
SAMPLE_WIDTH_BYTES = 2
BYTES_PER_SECOND = SAMPLE_RATE * SAMPLE_WIDTH_BYTES
MAX_SEGMENT_SECONDS = 10.0
MIN_SEGMENT_SECONDS = 1.0
OVERLAP_SECONDS = 1.0
ASR_QUEUE_MAXSIZE = 6
STATUS_EMIT_SECONDS = 1.0
MIN_BUFFER_RMS = 35.0
FALLBACK_VOICE_THRESHOLD = 80.0
LOW_ENERGY_DROP_RMS = 20.0

@dataclass
class ASRSegment:
    segment_id: int
    pcm_bytes: bytes
    language: str
    timestamp: str
    start_seconds: float
    end_seconds: float
    avg_rms: float
    voiced_ratio: float
    diarize: bool
    reason: str

    @property
    def duration_seconds(self) -> float:
        return len(self.pcm_bytes) / BYTES_PER_SECOND if self.pcm_bytes else 0.0


class IncrementalWavWriter:
    """Small WAV writer that keeps long recordings off the Python heap."""

    def __init__(self, filename: str, sample_rate: int = SAMPLE_RATE):
        self.filename = filename
        self.path = Path("notas") / filename
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._wav = wave.open(str(self.path), "wb")
        self._wav.setnchannels(1)
        self._wav.setsampwidth(SAMPLE_WIDTH_BYTES)
        self._wav.setframerate(sample_rate)
        self._closed = False

    def write(self, pcm_data: bytes) -> None:
        if not self._closed and pcm_data:
            self._wav.writeframes(pcm_data)

    def close(self) -> None:
        if not self._closed:
            self._wav.close()
            self._closed = True


def _seconds_from_pcm(pcm_data: bytes) -> float:
    return len(pcm_data) / BYTES_PER_SECOND if pcm_data else 0.0


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


_HALLUCINATION_PHRASES = {
    _normalize_text(text)
    for text in (
        "gracias",
        "muchas gracias",
        "gracias por ver",
        "gracias por ver el video",
        "gracias por escuchar",
        "gracias por su atencion",
        "suscribete",
        "suscribete al canal",
        "dale like",
        "subtitulos",
        "subtitulos por",
        "subtitulos realizados por",
        "traducido por",
        "traduccion por",
        "amara org",
        "todos los derechos reservados",
        "thank you",
        "thank you for watching",
        "thanks for watching",
        "subscribe",
        "subtitles",
        "captions by",
        "all rights reserved",
        "amen",
    )
}


def _is_known_hallucination(normalized: str) -> bool:
    if not normalized:
        return True
    if normalized in _HALLUCINATION_PHRASES:
        return True
    for phrase in _HALLUCINATION_PHRASES:
        if len(phrase) >= 10 and phrase in normalized and len(normalized) <= len(phrase) + 20:
            return True
    return False


def _is_repetitive_text(normalized: str) -> bool:
    words = normalized.split()
    if len(words) < 4:
        return False

    _most_common_word, count = Counter(words).most_common(1)[0]
    if count / len(words) >= 0.70:
        return True

    if len(words) >= 10 and len(set(words)) / len(words) <= 0.25:
        return True

    for gram_size in range(2, min(6, len(words) // 2 + 1)):
        grams = [
            " ".join(words[i:i + gram_size])
            for i in range(0, len(words) - gram_size + 1)
        ]
        _gram, gram_count = Counter(grams).most_common(1)[0]
        if gram_count >= 3 and (gram_count * gram_size) / len(words) >= 0.60:
            return True

    return False


def _trim_overlap(text: str, recent_texts: deque[str]) -> str:
    current_words = text.split()
    current_norm_words = _normalize_text(text).split()
    if not current_words or not current_norm_words:
        return ""

    for previous in reversed(recent_texts):
        previous_words = _normalize_text(previous).split()
        max_overlap = min(len(previous_words), len(current_norm_words), 12)
        for size in range(max_overlap, 2, -1):
            if previous_words[-size:] == current_norm_words[:size]:
                return " ".join(current_words[size:]).strip()

    return text.strip()


def _is_duplicate_text(normalized: str, recent_texts: deque[str]) -> bool:
    if len(normalized) < 12:
        return False

    for previous in recent_texts:
        previous_norm = _normalize_text(previous)
        if not previous_norm:
            continue
        if normalized == previous_norm:
            return True
        if len(normalized) > 25 and SequenceMatcher(None, normalized, previous_norm).ratio() >= 0.92:
            return True

    return False


def _sanitize_asr_text(text: str, session: dict, segment: ASRSegment) -> str:
    text = (text or "").strip()
    normalized = _normalize_text(text)
    if _is_known_hallucination(normalized) or _is_repetitive_text(normalized):
        print(f"[ASR Filter] Dropping hallucinated/repetitive segment {segment.segment_id}: '{text}'")
        session["dropped_segments"] = session.get("dropped_segments", 0) + 1
        return ""
    words = normalized.split()
    if len(words) == 1 and (len(words[0]) <= 3 or words[0] in {"si", "sí", "no", "ah", "eh", "ok", "okay", "es"}):
        print(f"[ASR Filter] Dropping low-information single word {segment.segment_id}: '{text}'")
        session["dropped_segments"] = session.get("dropped_segments", 0) + 1
        return ""
    if 1 < len(words) <= 6 and len(set(words)) <= 2:
        print(f"[ASR Filter] Dropping low-information repeated segment {segment.segment_id}: '{text}'")
        session["dropped_segments"] = session.get("dropped_segments", 0) + 1
        return ""

    # Near-silence is risky, but weak microphone speech can still be valid.
    # Keep non-repetitive text unless the segment is effectively silent.
    if segment.duration_seconds < MIN_SEGMENT_SECONDS:
        print(f"[ASR Filter] Dropping short segment {segment.segment_id}: {segment.duration_seconds:.2f}s")
        session["dropped_segments"] = session.get("dropped_segments", 0) + 1
        return ""
    if segment.duration_seconds < 4.0 and segment.avg_rms < 220:
        print(
            f"[ASR Filter] Dropping short low-energy tail {segment.segment_id}: "
            f"duration={segment.duration_seconds:.2f}s, rms={segment.avg_rms:.1f}"
        )
        session["dropped_segments"] = session.get("dropped_segments", 0) + 1
        return ""
    if segment.avg_rms < LOW_ENERGY_DROP_RMS and segment.voiced_ratio < 0.05:
        print(
            f"[ASR Filter] Dropping near-silent segment {segment.segment_id}: "
            f"rms={segment.avg_rms:.1f}, voice_ratio={segment.voiced_ratio:.2f}"
        )
        session["dropped_segments"] = session.get("dropped_segments", 0) + 1
        return ""

    recent_texts: deque[str] = session.setdefault("recent_transcripts", deque(maxlen=6))
    text = _trim_overlap(text, recent_texts)
    normalized = _normalize_text(text)
    if _is_known_hallucination(normalized) or _is_repetitive_text(normalized):
        print(f"[ASR Filter] Dropping filtered overlap segment {segment.segment_id}: '{text}'")
        session["dropped_segments"] = session.get("dropped_segments", 0) + 1
        return ""
    if _is_duplicate_text(normalized, recent_texts):
        print(f"[ASR Filter] Dropping duplicate segment {segment.segment_id}: '{text}'")
        session["dropped_segments"] = session.get("dropped_segments", 0) + 1
        return ""

    return text


def _close_audio_writer(session: dict) -> str | None:
    writer: IncrementalWavWriter | None = session.get("audio_writer")
    if not writer:
        return session.get("audio_filename")
    try:
        writer.close()
    except Exception as e:
        print(f"[Audio] Error closing WAV writer: {e}")
    session["audio_writer"] = None
    return writer.filename


async def _emit_transcription_status(sio_inst, sid: str, event: str, **payload) -> None:
    try:
        await sio_inst.emit('transcription_status', {"event": event, **payload}, room=sid)
    except Exception as e:
        print(f"[Socket.IO] emit transcription_status error: {e}")


async def _asr_transcribe(pcm_bytes: bytes, language: str = "en", diarize: bool = False) -> str:
    """
    Transcribe raw 16kHz mono 16-bit PCM via the configured NVIDIA ASR NIM.

    Wraps the raw PCM buffer in a WAV container before sending to ASRService,
    which normalises and forwards to the NIM endpoint.
    """
    import io
    import wave

    rms = AudioUtils.calculate_rms(pcm_bytes)
    if 0 < rms < 180:
        gain = min(4.0, 180 / rms)
        pcm_bytes = AudioUtils.apply_gain(pcm_bytes, gain)
        print(f"[ASR] Applied normalization gain {gain:.1f}x (rms={rms:.1f})")

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)   # 16-bit
        wf.setframerate(16000)
        wf.writeframes(pcm_bytes)
    wav_bytes = buf.getvalue()

    try:
        svc = ASRService()
        result = await svc.transcribe(ASRRequest(
            audio_bytes=wav_bytes,
            sample_rate=16000,
            language=language,
            diarize=diarize
        ))
        return result.text.strip() if result.text else ""
    except Exception as e:
        print(f"[ASR] Transcription error: {e}")
        return ""


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# ──────────────────────────────────────────────
#  Facade: register_socket_events
# ──────────────────────────────────────────────

def register_socket_events(sio):
    """
    Facade Pattern entry point.
    
    Registers all Socket.IO event handlers.  Internally delegates:
      - Audio conversion  →  AudioProcessorPort (Adapter)
      - VAD logic          →  VADStrategy          (Strategy / State)
      - Transcription      →  NVIDIA ASR NIM      (async, per-call)
      - Persistence        →  TranscriptionRepository (Repository)
    """

    # ── Observer: connect ──

    @sio.event
    async def connect(sid, environ):
        """Client connected – initialise session with VAD strategy."""
        print(f"[Socket.IO] Client connected: {sid}")

        # Each session gets its own VAD strategy instance (Strategy Pattern)
        vad_strategy: VADStrategy = ThresholdVADStrategy(
            ServiceVADConfig(voice_threshold=500, silence_threshold=200, silence_chunks_to_end=4)
        )

        active_sessions[sid] = {
            "transcription_buffer": [],
            "start_time": datetime.now(),
            "speech_buffer": b"",
            "speech_start_seconds": None,
            "speech_rms_sum": 0.0,
            "speech_chunk_count": 0,
            "speech_voice_chunks": 0,
            "vad_strategy": vad_strategy,
            "mic_gain": 1.0,
            "active": False,
            "language": "es",
            "diarization": False,
            "recent_transcripts": deque(maxlen=6),
            "dropped_segments": 0,
            "next_segment_id": 1,
            "asr_queue": None,
            "asr_worker_task": None,
            "audio_writer": None,
            "audio_filename": None,
            "last_level_log": 0.0,
            "last_status_emit": 0.0,
            "stopping": False,
            "disconnected": False,
        }

        try:
            await sio.emit('connected', {
                'message': 'Connected to transcription server',
                'transcriber': 'Canary 1B ASR (NVIDIA NIM)'
            }, room=sid)
        except Exception as e:
            print(f"[Socket.IO] emit connected error: {e}")
            traceback.print_exc()

    # ── Observer: disconnect ──

    @sio.event
    async def disconnect(sid):
        """Client disconnected - cleanup runtime resources."""
        print(f"[Socket.IO] Client disconnected: {sid}")
        session = active_sessions.get(sid)
        if not session:
            return

        session["active"] = False
        session["disconnected"] = True
        if session.get("stopping"):
            return

        active_sessions.pop(sid, None)
        _close_audio_writer(session)
        worker = session.get("asr_worker_task")
        if worker and not worker.done():
            worker.cancel()

    # ── Observer: start_recording ──

    @sio.event
    async def start_recording(sid, *args):
        """Start recording session with optional VAD config override."""
        print(f"[Socket.IO] Start recording: {sid}")
        data = args[0] if args else None

        if sid in active_sessions:
            session = active_sessions[sid]
            _close_audio_writer(session)
            old_worker = session.get("asr_worker_task")
            if old_worker and not old_worker.done():
                old_worker.cancel()

            recording_started_at = datetime.now()
            recording_stamp = recording_started_at.strftime("%Y%m%d_%H%M%S")
            audio_filename = f"audio_{recording_stamp}.wav"
            try:
                audio_writer = IncrementalWavWriter(audio_filename)
            except Exception as e:
                print(f"[Audio] Could not open WAV writer: {e}")
                audio_writer = None
                audio_filename = None

            session.update({
                "start_time": recording_started_at,
                "transcription_buffer": [],
                "speech_buffer": b"",
                "speech_start_seconds": None,
                "speech_rms_sum": 0.0,
                "speech_chunk_count": 0,
                "speech_voice_chunks": 0,
                "active": True,
                "recent_transcripts": deque(maxlen=6),
                "dropped_segments": 0,
                "next_segment_id": 1,
                "asr_queue": asyncio.Queue(maxsize=ASR_QUEUE_MAXSIZE),
                "audio_writer": audio_writer,
                "audio_filename": audio_filename,
                "last_level_log": 0.0,
            "last_status_emit": 0.0,
                "stopping": False,
                "disconnected": False,
            })
            session["asr_worker_task"] = asyncio.create_task(_asr_worker(sio, sid, session))

            # Reconfigure VAD if client sends thresholds
            if data and isinstance(data, dict):
                # Allow client to override transcription language
                if "language" in data:
                    session["language"] = str(data["language"])
                    print(f"[Socket.IO] Language set to '{session['language']}' for {sid}")
                
                # Extract diarization flag
                if "diarization" in data:
                    session["diarization"] = bool(data["diarization"])
                    print(f"[Socket.IO] Diarization Enabled: {session['diarization']} for {sid}")

                vad_cfg = ServiceVADConfig(
                    voice_threshold=int(data.get('voiceThreshold', 500)),
                    silence_threshold=int(data.get('silenceThreshold', 200)),
                    silence_chunks_to_end=4,
                )
                session["vad_strategy"] = ThresholdVADStrategy(vad_cfg)
                print(f"[Socket.IO] VAD Config - Voice: {vad_cfg.voice_threshold}, Silence: {vad_cfg.silence_threshold}")

            # Reset VAD state machine
            session["vad_strategy"].reset()

            try:
                await sio.emit('recording_started', {
                    'timestamp': datetime.now().isoformat()
                }, room=sid)
                await _emit_transcription_status(
                    sio,
                    sid,
                    "recording_started",
                    voice_threshold=getattr(getattr(session["vad_strategy"], "config", None), "voice_threshold", None),
                    silence_threshold=getattr(getattr(session["vad_strategy"], "config", None), "silence_threshold", None),
                    max_segment_seconds=MAX_SEGMENT_SECONDS,
                )
            except Exception as e:
                print(f"[Socket.IO] emit recording_started error: {e}")
                traceback.print_exc()
            return {"ok": True, "max_segment_seconds": MAX_SEGMENT_SECONDS}

    # ── Observer: set_mic_gain ──

    @sio.event
    async def set_mic_gain(sid, data):
        """Set microphone gain level."""
        if sid not in active_sessions:
            return

        gain = 1.0
        if isinstance(data, dict) and 'gain' in data:
            gain = float(data['gain'])
        elif isinstance(data, (int, float)):
            gain = float(data)

        gain = max(0.5, min(5.0, gain))
        active_sessions[sid]["mic_gain"] = gain
        print(f"[Socket.IO] Mic gain set to {gain:.2f} for {sid}")

        try:
            await sio.emit('mic_gain_updated', {'gain': gain}, room=sid)
        except Exception as e:
            print(f"[Socket.IO] emit mic_gain_updated error: {e}")

    # ── Observer: audio_chunk (WebM) ──

    @sio.event
    @logfire.instrument
    async def audio_chunk(sid, data):
        """Receive WebM audio → Adapter → PCM pipeline."""
        if sid not in active_sessions or not active_sessions[sid].get("active"):
            return

        session = active_sessions[sid]

        # Adapter Pattern: convert WebM → PCM
        try:
            pcm_data = await asyncio.to_thread(_webm_adapter.to_pcm, data)
        except Exception as e:
            print(f"[Audio] Conversion error: {e}")
            pcm_data = b""

        if not pcm_data:
            return

        await _process_pcm_chunk(sio, sid, pcm_data, session)

    # ── Observer: audio_chunk_pcm ──

    @sio.event
    @logfire.instrument
    async def audio_chunk_pcm(sid, data):
        """Receive raw PCM audio (identity adapter)."""
        if sid not in active_sessions or not active_sessions[sid].get("active"):
            return

        session = active_sessions[sid]
        pcm_data = bytes(data) if not isinstance(data, bytes) else data

        if not pcm_data or len(pcm_data) < 100:
            return

        await _process_pcm_chunk(sio, sid, pcm_data, session)

    # ──────────────────────────────────────
    #  Internal pipeline (hidden by Facade)
    # ──────────────────────────────────────

    def _reset_speech_stats(session: dict) -> None:
        session["speech_rms_sum"] = 0.0
        session["speech_chunk_count"] = 0
        session["speech_voice_chunks"] = 0

    async def _queue_speech_segment(
        sio_inst,
        sid: str,
        session: dict,
        *,
        end_seconds: float,
        reason: str,
        keep_overlap: bool,
        force: bool = False,
    ) -> None:
        buffer_to_send = session.get("speech_buffer", b"")
        if not buffer_to_send:
            return

        duration = _seconds_from_pcm(buffer_to_send)
        start_seconds = session.get("speech_start_seconds")
        if start_seconds is None:
            start_seconds = max(0.0, end_seconds - duration)

        if duration < MIN_SEGMENT_SECONDS and not force:
            print(f"[ASR Queue] Dropping tiny {reason} segment: {duration:.2f}s")
            session["speech_buffer"] = b""
            session["speech_start_seconds"] = None
            _reset_speech_stats(session)
            return

        chunk_count = session.get("speech_chunk_count", 0)
        avg_rms = (
            session.get("speech_rms_sum", 0.0) / chunk_count
            if chunk_count
            else AudioUtils.calculate_rms(buffer_to_send)
        )
        voiced_ratio = (
            session.get("speech_voice_chunks", 0) / chunk_count
            if chunk_count
            else 0.0
        )

        segment_id = session.get("next_segment_id", 1)
        session["next_segment_id"] = segment_id + 1
        segment = ASRSegment(
            segment_id=segment_id,
            pcm_bytes=buffer_to_send,
            language=session.get("language", "es"),
            timestamp=format_timestamp(start_seconds),
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            avg_rms=avg_rms,
            voiced_ratio=voiced_ratio,
            diarize=session.get("diarization", False),
            reason=reason,
        )

        queue: asyncio.Queue | None = session.get("asr_queue")
        if queue is None:
            return
        if queue.full():
            print(f"[ASR Queue] Backpressure for segment {segment_id}; waiting for ASR worker")
        await queue.put(segment)
        print(
            f"[ASR Queue] Queued segment {segment_id}: "
            f"{duration:.1f}s, rms={avg_rms:.0f}, voice_ratio={voiced_ratio:.2f}, reason={reason}"
        )
        await _emit_transcription_status(
            sio_inst,
            sid,
            "segment_queued",
            segment_id=segment_id,
            duration=round(duration, 2),
            rms=round(avg_rms, 1),
            voiced_ratio=round(voiced_ratio, 2),
            reason=reason,
            queue_size=queue.qsize(),
        )

        overlap_bytes = int(OVERLAP_SECONDS * BYTES_PER_SECOND)
        if keep_overlap and len(buffer_to_send) > overlap_bytes:
            session["speech_buffer"] = buffer_to_send[-overlap_bytes:]
            session["speech_start_seconds"] = max(
                0.0,
                end_seconds - _seconds_from_pcm(session["speech_buffer"]),
            )
        else:
            session["speech_buffer"] = b""
            session["speech_start_seconds"] = None
        _reset_speech_stats(session)

    async def _asr_worker(sio_inst, sid: str, session: dict):
        queue: asyncio.Queue = session["asr_queue"]
        while True:
            segment = await queue.get()
            try:
                if segment is None:
                    return

                await _emit_transcription_status(
                    sio_inst,
                    sid,
                    "asr_started",
                    segment_id=segment.segment_id,
                    timestamp=segment.timestamp,
                    queue_size=queue.qsize(),
                )

                text = await _asr_transcribe(
                    segment.pcm_bytes,
                    segment.language,
                    diarize=segment.diarize,
                )
                text = _sanitize_asr_text(text, session, segment)

                if not text:
                    await _emit_transcription_status(
                        sio_inst,
                        sid,
                        "segment_discarded",
                        segment_id=segment.segment_id,
                        timestamp=segment.timestamp,
                        rms=round(segment.avg_rms, 1),
                        voiced_ratio=round(segment.voiced_ratio, 2),
                    )
                    if session.get("dropped_segments", 0) >= 3:
                        vad: VADStrategy = session["vad_strategy"]
                        vad.reset()
                        session["speech_buffer"] = b""
                        session["speech_start_seconds"] = None
                        _reset_speech_stats(session)
                        session["dropped_segments"] = 0
                        print(f"[ASR Filter] Reset VAD after repeated dropped segments for {sid}")
                    continue

                session["dropped_segments"] = 0
                session.setdefault("recent_transcripts", deque(maxlen=6)).append(text)
                timestamp_dt = session["start_time"] + timedelta(seconds=segment.start_seconds)
                session["transcription_buffer"].append({
                    "timestamp": segment.timestamp,
                    "timestamp_dt": timestamp_dt,
                    "start_seconds": segment.start_seconds,
                    "text": text,
                })

                await _emit_transcription_status(
                    sio_inst,
                    sid,
                    "transcription_received",
                    segment_id=segment.segment_id,
                    timestamp=segment.timestamp,
                    chars=len(text),
                )

                try:
                    await sio_inst.emit('transcription', {
                        "timestamp": segment.timestamp,
                        "text": text,
                    }, room=sid)
                except Exception as e_emit:
                    print(f"[Socket.IO] emit error: {e_emit}")

                print(f"[Socket.IO] Segment {segment.segment_id} for {sid}: {text[:100]}...")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"[Socket.IO] Error transcribing segment for {sid}: {e}")
                traceback.print_exc()
            finally:
                queue.task_done()

    async def _process_pcm_chunk(sio_inst, sid: str, pcm_data: bytes, session: dict):
        """Process bounded PCM chunks and enqueue stable ASR segments."""
        mic_gain = session.get("mic_gain", 1.0)
        if mic_gain != 1.0:
            pcm_data = AudioUtils.apply_gain(pcm_data, mic_gain)

        writer: IncrementalWavWriter | None = session.get("audio_writer")
        if writer:
            try:
                writer.write(pcm_data)
            except Exception as e:
                print(f"[Audio] WAV write error: {e}")

        elapsed = (datetime.now() - session["start_time"]).total_seconds()
        timestamp = format_timestamp(elapsed)
        chunk_seconds = _seconds_from_pcm(pcm_data)

        vad: VADStrategy = session["vad_strategy"]
        result = vad.process_chunk(pcm_data)

        try:
            await sio_inst.emit('audio_level', {
                'rms': round(result.rms, 1),
                'gain': mic_gain,
                'timestamp': timestamp,
            }, room=sid)
        except Exception:
            pass

        last_level_log = session.get("last_level_log", 0.0)
        if elapsed - last_level_log >= 5.0:
            session["last_level_log"] = elapsed
            print(f"[Audio Level] RMS: {result.rms:.0f} | Gain: {mic_gain:.1f}x | t={timestamp}")

        vad_config = getattr(vad, "config", None)
        configured_voice_threshold = float(getattr(vad_config, "voice_threshold", 500))
        possible_voice_threshold = max(MIN_BUFFER_RMS, min(configured_voice_threshold, FALLBACK_VOICE_THRESHOLD))
        has_possible_voice = result.rms >= possible_voice_threshold
        should_buffer = result.should_buffer or has_possible_voice or bool(session.get("speech_buffer"))

        if should_buffer:
            if not session.get("speech_buffer"):
                session["speech_start_seconds"] = max(0.0, elapsed - chunk_seconds)
            session["speech_buffer"] += pcm_data
            session["speech_rms_sum"] = session.get("speech_rms_sum", 0.0) + result.rms
            session["speech_chunk_count"] = session.get("speech_chunk_count", 0) + 1
            if has_possible_voice:
                session["speech_voice_chunks"] = session.get("speech_voice_chunks", 0) + 1

        buffer_len_sec = _seconds_from_pcm(session.get("speech_buffer", b""))
        last_status_emit = session.get("last_status_emit", 0.0)
        if elapsed - last_status_emit >= STATUS_EMIT_SECONDS:
            session["last_status_emit"] = elapsed
            queue: asyncio.Queue | None = session.get("asr_queue")
            await _emit_transcription_status(
                sio_inst,
                sid,
                "capturing",
                rms=round(result.rms, 1),
                buffer_seconds=round(buffer_len_sec, 1),
                vad_state=getattr(result.state, "name", str(result.state)),
                queue_size=queue.qsize() if queue else 0,
            )
        if result.phrase_ended and session.get("speech_buffer"):
            await _queue_speech_segment(
                sio_inst,
                sid,
                session,
                end_seconds=elapsed,
                reason="phrase_end",
                keep_overlap=False,
            )
        elif buffer_len_sec >= MAX_SEGMENT_SECONDS:
            await _queue_speech_segment(
                sio_inst,
                sid,
                session,
                end_seconds=elapsed,
                reason="max_duration",
                keep_overlap=True,
            )
            vad.reset()

    @sio.event
    @logfire.instrument
    async def stop_recording(sid):
        """Stop recording: schedule post-processing in background."""
        print(f"[Socket.IO] Stop recording: {sid}")

        if sid not in active_sessions:
            await sio.emit('error', {'message': 'No active session'}, room=sid)
            return

        active_sessions[sid]["active"] = False
        active_sessions[sid]["stopping"] = True
        asyncio.create_task(_handle_stop_recording(sid))

        try:
            await sio.emit('recording_stopped', {
                'message': 'Transcription saved and processing started',
                'filename': None,
                'audio_file': None,
                'segments': len(active_sessions.get(sid, {}).get('transcription_buffer', []))
            }, room=sid)
        except Exception as e:
            print(f"[Socket.IO] emit ack error: {e}")

    @logfire.instrument
    async def _handle_stop_recording(sid: str):
        """Drain ASR queue, close audio, and persist the completed recording."""
        session = active_sessions.get(sid)
        if not session:
            return

        from backend.repositories.transcription_repository import TranscriptionRepository
        repo = TranscriptionRepository()

        try:
            stop_elapsed = (datetime.now() - session["start_time"]).total_seconds()

            if session.get("speech_buffer"):
                await _queue_speech_segment(
                    sio,
                    sid,
                    session,
                    end_seconds=stop_elapsed,
                    reason="stop",
                    keep_overlap=False,
                    force=True,
                )

            audio_filename = _close_audio_writer(session)

            queue: asyncio.Queue | None = session.get("asr_queue")
            worker: asyncio.Task | None = session.get("asr_worker_task")
            if queue:
                await queue.join()
                if worker and not worker.done():
                    await queue.put(None)
                    try:
                        await asyncio.wait_for(worker, timeout=30.0)
                    except asyncio.TimeoutError:
                        print(f"[ASR Queue] Worker did not stop cleanly for {sid}; cancelling")
                        worker.cancel()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if not session["transcription_buffer"]:
                print(f"[Socket.IO] Skipping save for {sid}: No text transcribed.")
                try:
                    await sio.emit('warning', {
                        'message': 'No se detecto voz o contenido para transcribir.'
                    }, room=sid)
                except Exception:
                    pass
                return

            ordered_segments = sorted(
                session["transcription_buffer"],
                key=lambda item: item.get("start_seconds", 0.0),
            )
            all_transcripts = [
                (
                    item.get("timestamp_dt")
                    or session["start_time"] + timedelta(seconds=item.get("start_seconds", 0.0)),
                    item["text"],
                )
                for item in ordered_segments
            ]
            metadata = {
                'title': 'Transcripcion de Audio',
                'method': 'Long-form realtime VAD',
                'audio_file': audio_filename or 'N/A',
                'duration_seconds': stop_elapsed,
                'language': session.get("language", "es"),
            }

            formatter = FormatterFactory.create('segmented_markdown')
            raw_content = await asyncio.to_thread(formatter.format, all_transcripts, metadata)

            md_filename = f"transcripcion_{timestamp}.md"

            # Insert directly into database (no file I/O)
            try:
                from src.database.mongo_manager import MongoManager
                from src.agent.transcription_analyzer import TranscriptionAnalyzer
                from src.agent.document_generator import DocumentGenerator

                db = MongoManager()
                doc = {
                    "filename": md_filename,
                    "raw_content": raw_content,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "word_count": len(raw_content.split()),
                    "source_type": "live_recording",
                    "processed": False,
                    "ingested_at": datetime.now(),
                    "audio_file": audio_filename or "N/A",
                    "duration_seconds": stop_elapsed,
                    "language": session.get("language", "es"),
                }
                result = db.transcriptions.insert_one(doc)
                print(f"[Socket.IO] Inserted transcription {result.inserted_id} into DB")

                # Post-processing: analyze and generate
                try:
                    analyzer = TranscriptionAnalyzer()
                    analyzer.analyze_pending()
                    generator = DocumentGenerator()
                    generator.generate_all()
                    print(f"[Socket.IO] Post-processing completed for {sid}")
                except Exception as e:
                    print(f"[Socket.IO] Warning: Post-processing error: {e}")
            except Exception as e:
                print(f"[Socket.IO] Error during DB insert: {e}")

            try:
                await sio.emit('processing_complete', {
                    'message': 'Processing finished',
                    'filename': md_filename,
                    'audio_file': audio_filename,
                    'segments': len(session["transcription_buffer"]),
                }, room=sid)
            except Exception as e_emit:
                print(f"[Socket.IO] emit processing_complete error: {e_emit}")

            print(f"[Socket.IO] Completed session for {sid}")

        except asyncio.CancelledError:
            print(f"[Socket.IO] _handle_stop_recording cancelled for {sid}")
            raise
        except Exception as e:
            print(f"[Socket.IO] Error saving transcription: {e}")
            traceback.print_exc()
            try:
                await sio.emit('error', {'message': str(e)}, room=sid)
            except Exception:
                pass
        finally:
            session["stopping"] = False
            if session.get("disconnected"):
                active_sessions.pop(sid, None)
