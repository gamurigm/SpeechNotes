"""
Socket.IO Event Handlers with realtime.py Integration
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import wave
import struct
import math
import asyncio

load_dotenv()

from src.database import MongoManager
from src.agent.transcription_ingestor import TranscriptionIngestor
from src.agent.transcription_analyzer import TranscriptionAnalyzer
from src.agent.document_generator import DocumentGenerator

# Import realtime.py components
from src.core.environment_factory import TranscriptionEnvironmentFactoryProvider
from src.transcription import FormatterFactory, OutputWriter

# Store active sessions
active_sessions = {}

# Global transcriber instance
transcriber = None

def calculate_rms(audio_data: bytes) -> float:
    """
    Calculate RMS (Root Mean Square) amplitude of audio data
    Assumes 16-bit mono PCM
    """
    if not audio_data:
        return 0
        
    count = len(audio_data) // 2
    if count == 0:
        return 0
    
    try:
        # Unpack 16-bit integers (ensure exact buffer size)
        shorts = struct.unpack(f"{count}h", audio_data[:count*2])
        sum_squares = sum(s**2 for s in shorts)
        return math.sqrt(sum_squares / count)
    except Exception as e:
        print(f"[RMS] Error: {e}")
        return 0

def get_transcriber():
    """Get or create transcriber instance from realtime.py"""
    global transcriber
    if transcriber is None:
        try:
            environment_factory = TranscriptionEnvironmentFactoryProvider.get_riva_live()
            transcriber = environment_factory.create_transcriber()
            print(f"[Transcriber] Initialized with Riva server: {transcriber.config.server}")
        except Exception as e:
            print(f"[Transcriber] Error initializing: {e}")
            transcriber = None
    return transcriber

def save_audio_as_wav(audio_chunks: list, output_path: Path, sample_rate: int = 16000):
    """
    Save audio chunks as WAV file
    
    Args:
        audio_chunks: List of audio byte chunks
        output_path: Path to save WAV file
        sample_rate: Sample rate in Hz
    """
    try:
        # Combine all chunks
        audio_data = b''.join(audio_chunks)
        
        # Create WAV file
        with wave.open(str(output_path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)
        
        print(f"[Audio] Saved WAV file: {output_path} ({len(audio_data)} bytes)")
        return True
    except Exception as e:
        print(f"[Audio] Error saving WAV: {e}")
        return False

def transcribe_audio_chunk(audio_data: bytes, threshold: int = 50) -> str:
    """
    Transcribe audio chunk using realtime.py transcriber
    
    Args:
        audio_data: Raw audio bytes from browser
        threshold: RMS threshold for silence detection
    
    Returns:
        Transcribed text
    """
    # 1. Silence Detection (RMS Threshold)
    rms = calculate_rms(audio_data)
    
    # Log RMS occasionally for debugging
    if rms > 10:
        # print(f"[Audio] RMS: {rms:.2f} (Threshold: {threshold})")
        pass

    # If RMS is below threshold, treat as silence
    if rms < threshold:
        return ""
        
    trans = get_transcriber()
    
    if not trans:
        return ""
    
    try:
        # Transcribe using realtime.py
        transcript = trans.offline_transcribe(audio_data, language="es")
        
        if transcript:
            return transcript.strip()
        else:
            return ""
            
    except Exception as e:
        print(f"[Transcriber] Error: {e}")
        return ""

def register_socket_events(sio):
    """Register all Socket.IO event handlers"""
    
    @sio.event
    async def connect(sid, environ):
        """Client connected"""
        print(f"[Socket.IO] Client connected: {sid}")
        active_sessions[sid] = {
            "transcription_buffer": [],
            "start_time": datetime.now(),
            "audio_chunks": [],
            "full_audio": b"",
            "voice_threshold": 300,    # Default start threshold
            "silence_threshold": 150,  # Default stop threshold
            "is_speaking": False       # VAD state
        }
        
        # Initialize transcriber on first connection
        get_transcriber()
        
        await sio.emit('connected', {
            'message': 'Connected to transcription server',
            'transcriber': 'Riva Live' if get_transcriber() else 'Unavailable'
        }, room=sid)
    
    @sio.event
    async def disconnect(sid):
        """Client disconnected"""
        print(f"[Socket.IO] Client disconnected: {sid}")
        if sid in active_sessions:
            del active_sessions[sid]
    
    @sio.event
    async def start_recording(sid, *args):
        """Start recording session"""
        print(f"[Socket.IO] Start recording: {sid}")
        
        # Handle arguments (data might be the first arg in args)
        data = args[0] if args else None
        
        if sid in active_sessions:
            active_sessions[sid]["start_time"] = datetime.now()
            active_sessions[sid]["transcription_buffer"] = []
            active_sessions[sid]["audio_chunks"] = []
            active_sessions[sid]["full_audio"] = b""
            active_sessions[sid]["is_speaking"] = False
            
            # Update settings if provided
            if data and isinstance(data, dict):
                if 'voiceThreshold' in data:
                    active_sessions[sid]["voice_threshold"] = int(data['voiceThreshold'])
                if 'silenceThreshold' in data:
                    active_sessions[sid]["silence_threshold"] = int(data['silenceThreshold'])
                
                print(f"[Socket.IO] VAD Config - Voice: {active_sessions[sid].get('voice_threshold')}, Silence: {active_sessions[sid].get('silence_threshold')}")
            
            await sio.emit('recording_started', {
                'timestamp': datetime.now().isoformat()
            }, room=sid)
    
    @sio.event
    async def audio_chunk(sid, data):
        """Receive audio chunk from client and transcribe with realtime.py"""
        if sid not in active_sessions:
            return
        
        session = active_sessions[sid]
        
        # Store audio chunk
        session["audio_chunks"].append(data)
        session["full_audio"] += data
        
        # Calculate elapsed time
        elapsed = (datetime.now() - session["start_time"]).total_seconds()
        timestamp = format_timestamp(elapsed)
        
        # VAD Logic (Hysteresis)
        rms = calculate_rms(data)
        voice_thresh = session.get("voice_threshold", 300)
        silence_thresh = session.get("silence_threshold", 150)
        is_speaking = session.get("is_speaking", False)

        if not is_speaking:
            if rms > voice_thresh:
                session["is_speaking"] = True
                is_speaking = True
                # print(f"[VAD] Voice started (RMS: {rms:.0f} > {voice_thresh})")
        else:
            if rms < silence_thresh:
                session["is_speaking"] = False
                is_speaking = False
                # print(f"[VAD] Silence detected (RMS: {rms:.0f} < {silence_thresh})")

        # Transcribe with realtime.py if speaking
        if is_speaking:
            # Offload blocking transcription to a thread to avoid blocking the event loop
            try:
                text = await asyncio.to_thread(transcribe_audio_chunk, data, 0)

                if text and text.strip():
                    # Add to buffer
                    session["transcription_buffer"].append({
                        "timestamp": timestamp,
                        "text": text
                    })

                    # Send transcription back to client
                    try:
                        await sio.emit('transcription', {
                            "timestamp": timestamp,
                            "text": text
                        }, room=sid)
                    except Exception as e_emit:
                        print(f"[Socket.IO] emit error: {e_emit}")

                    print(f"[Socket.IO] Transcribed for {sid}: {text[:50]}...")

            except Exception as e:
                print(f"[Socket.IO] Error transcribing chunk: {e}")
                import traceback
                traceback.print_exc()
    
    @sio.event
    async def stop_recording(sid):
        """Stop recording: schedule post-processing in background to avoid blocking."""
        print(f"[Socket.IO] Stop recording: {sid}")

        if sid not in active_sessions:
            await sio.emit('error', {'message': 'No active session'}, room=sid)
            return

        # Schedule the heavy work in background so we don't block the Socket.IO event loop
        asyncio.create_task(_handle_stop_recording(sid))

        # Immediately acknowledge receipt to the client
        try:
            await sio.emit('recording_stopped', {
                'message': 'Transcription saved and processing started',
                'filename': None,
                'audio_file': None,
                'segments': len(active_sessions.get(sid, {}).get('transcription_buffer', []))
            }, room=sid)
        except Exception as e:
            print(f"[Socket.IO] emit ack error: {e}")


    async def _handle_stop_recording(sid: str):
        """Background worker to perform blocking post-processing steps."""
        session = active_sessions.get(sid)
        if not session:
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 1. Save audio as WAV (run in thread)
            audio_filename = f"audio_{timestamp}.wav"
            audio_path = Path(f"notas/{audio_filename}")
            audio_path.parent.mkdir(exist_ok=True)

            if session["audio_chunks"]:
                await asyncio.to_thread(save_audio_as_wav, session["audio_chunks"], audio_path)

            # 2. Create markdown transcription (use thread for blocking formatter/write)
            all_transcripts = [
                (datetime.now(), item['text'])
                for item in session["transcription_buffer"]
            ]

            formatter = FormatterFactory.create('segmented_markdown')
            metadata = {'title': 'Transcripción de Audio', 'method': 'Real-time VAD'}
            formatted_content = await asyncio.to_thread(formatter.format, all_transcripts, metadata)

            md_filename = f"transcripcion_{timestamp}.md"
            md_path = Path(f"notas/{md_filename}")
            writer = OutputWriter(Path("notas"))
            await asyncio.to_thread(writer.write, formatted_content, md_filename)

            print(f"[Socket.IO] Saved transcription: {md_filename}")
            print(f"[Socket.IO] Saved audio: {audio_filename}")

            # 3. Post-processing: ingest/analyze/generate (run in thread)
            try:
                def _postprocess():
                    db = MongoManager()
                    ingestor = TranscriptionIngestor()
                    ingestor._ingest_file(md_path)
                    analyzer = TranscriptionAnalyzer()
                    analyzer.analyze_pending()
                    generator = DocumentGenerator()
                    generator.generate_all()

                await asyncio.to_thread(_postprocess)
                print(f"[Socket.IO] Post-processing completed for {sid}")
            except Exception as e:
                print(f"[Socket.IO] Warning: Post-processing error: {e}")

            # Try to notify the client that processing finished (best-effort)
            try:
                await sio.emit('processing_complete', {
                    'message': 'Processing finished',
                    'filename': md_filename,
                    'audio_file': audio_filename,
                    'segments': len(session["transcription_buffer"])
                }, room=sid)
            except Exception as e_emit:
                print(f"[Socket.IO] emit processing_complete error: {e_emit}")

            print(f"[Socket.IO] Completed session for {sid}")

        except asyncio.CancelledError:
            # The application is shutting down or the task was cancelled.
            # Attempt a minimal, synchronous save of current state to avoid data loss.
            print(f"[Socket.IO] _handle_stop_recording cancelled for {sid}, performing minimal cleanup")
            try:
                # Attempt to persist what we have so far (sync via to_thread)
                if session and session.get("audio_chunks"):
                    await asyncio.to_thread(save_audio_as_wav, session["audio_chunks"], Path(f"notas/audio_cancelled_{timestamp}.wav"))

                if session and session.get("transcription_buffer"):
                    minimal_content = "\n\n".join(item['text'] for item in session.get("transcription_buffer", []))
                    minimal_md = f"# Partial transcription (task cancelled)\n\n{minimal_content}"
                    await asyncio.to_thread(OutputWriter(Path("notas")).write, minimal_md, f"transcripcion_cancelled_{timestamp}.md")
            except Exception as e_cancel:
                print(f"[Socket.IO] Error during cancellation cleanup: {e_cancel}")
            # Re-raise to allow proper task cancellation handling upstream
            raise

        except Exception as e:
            print(f"[Socket.IO] Error saving transcription: {e}")
            import traceback
            traceback.print_exc()
            try:
                await sio.emit('error', {'message': str(e)}, room=sid)
            except Exception:
                pass

def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
