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

from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import asyncio
import traceback
import logfire
from typing import Any

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
from src.transcription import FormatterFactory, OutputWriter

# ── NIM ASR import (Parakeet TDT 0.6B v2) ──
from backend.services.audio.asr import ASRService, ASRRequest

# ──────────────────────────────────────────────
#  Module-level singletons (Creational)
# ──────────────────────────────────────────────
active_sessions: dict[str, dict] = {}

# Adapter instances (Structural – Adapter Pattern)
_webm_adapter: AudioProcessorPort = WebMAudioAdapter()
_pcm_adapter: AudioProcessorPort = PCMPassthroughAdapter()


async def _parakeet_transcribe(pcm_bytes: bytes, language: str = "en") -> str:
    """
    Transcribe raw 16kHz mono 16-bit PCM via NVIDIA Parakeet TDT 0.6B v2 NIM.

    Wraps the raw PCM buffer in a WAV container before sending to ASRService,
    which normalises and forwards to the NIM endpoint.
    """
    import io
    import wave

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
        ))
        return result.text.strip() if result.text else ""
    except Exception as e:
        print(f"[Parakeet] Transcription error: {e}")
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
      - Transcription      →  Parakeet TDT NIM     (async, per-call)
      - Persistence        →  TranscriptionRepository (Repository)
    """

    # ── Observer: connect ──

    @sio.event
    async def connect(sid, environ):
        """Client connected – initialise session with VAD strategy."""
        print(f"[Socket.IO] Client connected: {sid}")

        # Each session gets its own VAD strategy instance (Strategy Pattern)
        vad_strategy: VADStrategy = ThresholdVADStrategy(
            ServiceVADConfig(voice_threshold=80, silence_threshold=40, silence_chunks_to_end=1)
        )

        active_sessions[sid] = {
            "transcription_buffer": [],
            "start_time": datetime.now(),
            "audio_chunks": [],       # Original WebM chunks
            "pcm_audio": b"",         # Converted PCM audio
            "speech_buffer": b"",     # Accumulated speech
            "vad_strategy": vad_strategy,  # Injected strategy
            "mic_gain": 1.5,
            "active": False,
            "language": "en",         # Default: English (Parakeet is English-native)
        }

        try:
            await sio.emit('connected', {
                'message': 'Connected to transcription server',
                'transcriber': 'Parakeet TDT 0.6B v2 (NVIDIA NIM)'
            }, room=sid)
        except Exception as e:
            print(f"[Socket.IO] emit connected error: {e}")
            traceback.print_exc()

    # ── Observer: disconnect ──

    @sio.event
    async def disconnect(sid):
        """Client disconnected – cleanup."""
        print(f"[Socket.IO] Client disconnected: {sid}")
        active_sessions.pop(sid, None)

    # ── Observer: start_recording ──

    @sio.event
    async def start_recording(sid, *args):
        """Start recording session with optional VAD config override."""
        print(f"[Socket.IO] Start recording: {sid}")
        data = args[0] if args else None

        if sid in active_sessions:
            session = active_sessions[sid]
            session.update({
                "start_time": datetime.now(),
                "transcription_buffer": [],
                "audio_chunks": [],
                "pcm_audio": b"",
                "speech_buffer": b"",
                "active": True,
            })

            # Reconfigure VAD if client sends thresholds
            if data and isinstance(data, dict):
                # Allow client to override transcription language
                if "language" in data:
                    session["language"] = str(data["language"])
                    print(f"[Socket.IO] Language set to '{session['language']}' for {sid}")
                vad_cfg = ServiceVADConfig(
                    voice_threshold=int(data.get('voiceThreshold', 80)),
                    silence_threshold=int(data.get('silenceThreshold', 40)),
                    silence_chunks_to_end=1,
                )
                session["vad_strategy"] = ThresholdVADStrategy(vad_cfg)
                print(f"[Socket.IO] VAD Config - Voice: {vad_cfg.voice_threshold}, Silence: {vad_cfg.silence_threshold}")

            # Reset VAD state machine
            session["vad_strategy"].reset()

            try:
                await sio.emit('recording_started', {
                    'timestamp': datetime.now().isoformat()
                }, room=sid)
            except Exception as e:
                print(f"[Socket.IO] emit recording_started error: {e}")
                traceback.print_exc()

    # ── Observer: set_mic_gain ──

    @sio.event
    async def set_mic_gain(sid, data):
        """Set microphone gain level."""
        if sid not in active_sessions:
            return

        gain = 1.5
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
        session["audio_chunks"].append(data)

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

    async def _process_pcm_chunk(sio_inst, sid: str, pcm_data: bytes, session: dict):
        """
        Common PCM processing pipeline.
        
        1. Apply gain   →  AudioUtils  (SRP helper)
        2. VAD decision →  VADStrategy (Strategy Pattern)
        3. Buffer logic →  local state
        4. Transcribe   →  Parakeet NIM
        """
        # 1. Gain
        mic_gain = session.get("mic_gain", 1.5)
        if mic_gain != 1.0:
            pcm_data = AudioUtils.apply_gain(pcm_data, mic_gain)

        session["pcm_audio"] += pcm_data

        # Timestamp
        elapsed = (datetime.now() - session["start_time"]).total_seconds()
        timestamp = format_timestamp(elapsed)

        # 2. VAD (Strategy Pattern delegation)
        vad: VADStrategy = session["vad_strategy"]
        result = vad.process_chunk(pcm_data)

        # Emit audio level (Observer feedback to client)
        try:
            await sio_inst.emit('audio_level', {
                'rms': round(result.rms, 1),
                'gain': mic_gain,
                'timestamp': timestamp,
            }, room=sid)
        except Exception:
            pass

        print(f"[Audio Level] RMS: {result.rms:.0f} | Gain: {mic_gain:.1f}x")

        # 3. Buffer logic
        if result.should_buffer:
            session["speech_buffer"] += pcm_data

        buffer_len_sec = len(session.get("speech_buffer", b"")) / (16000 * 2)

        should_transcribe = False
        if result.phrase_ended and session.get("speech_buffer"):
            should_transcribe = True
        elif buffer_len_sec >= 4.0:
            should_transcribe = True
            print("[BUFFER] Periodic trigger: 4s reached")

        if should_transcribe:
            buffer_to_send = session["speech_buffer"]
            session["speech_buffer"] = b""

            try:
                lang = session.get("language", "en")
                text = await _parakeet_transcribe(buffer_to_send, lang)

                if text and text.strip():
                    session["transcription_buffer"].append({
                        "timestamp": timestamp,
                        "text": text,
                    })

                    try:
                        await sio_inst.emit('transcription', {
                            "timestamp": timestamp,
                            "text": text,
                        }, room=sid)
                    except Exception as e_emit:
                        print(f"[Socket.IO] emit error: {e_emit}")

                    print(f"[Socket.IO] Full Phrase for {sid}: {text[:100]}...")

            except Exception as e:
                print(f"[Socket.IO] Error transcribing buffered segment: {e}")
                traceback.print_exc()

    # ── Observer: stop_recording ──

    @sio.event
    @logfire.instrument
    async def stop_recording(sid):
        """Stop recording: schedule post-processing in background."""
        print(f"[Socket.IO] Stop recording: {sid}")

        if sid not in active_sessions:
            await sio.emit('error', {'message': 'No active session'}, room=sid)
            return

        active_sessions[sid]["active"] = False
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
        """Background worker – Repository Pattern for persistence."""
        session = active_sessions.get(sid)
        if not session:
            return

        from backend.repositories.transcription_repository import TranscriptionRepository
        repo = TranscriptionRepository()

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 1. Save audio as WAV via AudioUtils
            audio_filename = f"audio_{timestamp}.wav"
            if session.get("pcm_audio"):
                await asyncio.to_thread(repo.save_audio, session["pcm_audio"], audio_filename)

            # 2. Transcribe remaining speech buffer
            if session.get("speech_buffer"):
                try:
                    lang = session.get("language", "en")
                    text = await _parakeet_transcribe(session["speech_buffer"], lang)
                    if text and text.strip():
                        session["transcription_buffer"].append({
                            "timestamp": format_timestamp(
                                (datetime.now() - session["start_time"]).total_seconds()
                            ),
                            "text": text,
                        })
                except Exception as e:
                    print(f"[Socket.IO] Error transcribing remaining buffer: {e}")

            # 3. Persist only if we have content
            if not session["transcription_buffer"]:
                print(f"[Socket.IO] Skipping save for {sid}: No text transcribed.")
                try:
                    await sio.emit('error', {
                        'message': 'No se detectó voz o contenido para transcribir.'
                    }, room=sid)
                except Exception:
                    pass
                return

            all_transcripts = [
                (datetime.now(), item['text'])
                for item in session["transcription_buffer"]
            ]
            metadata = {'title': 'Transcripción de Audio', 'method': 'Real-time VAD'}

            formatter = FormatterFactory.create('segmented_markdown')
            formatted_content = await asyncio.to_thread(formatter.format, all_transcripts, metadata)

            md_filename = f"transcripcion_{timestamp}.md"
            md_path = await asyncio.to_thread(repo.save_transcription_file, formatted_content, md_filename)

            # 4. Post-processing
            try:
                await asyncio.to_thread(repo.post_process_file, md_path)
                print(f"[Socket.IO] Post-processing completed for {sid}")
            except Exception as e:
                print(f"[Socket.IO] Warning: Post-processing error: {e}")

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
