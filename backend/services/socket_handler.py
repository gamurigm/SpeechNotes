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

def transcribe_audio_chunk(audio_data: bytes) -> str:
    """
    Transcribe audio chunk using realtime.py transcriber
    
    Args:
        audio_data: Raw audio bytes from browser
    
    Returns:
        Transcribed text
    """
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
            "full_audio": b""
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
    async def start_recording(sid):
        """Start recording session"""
        print(f"[Socket.IO] Start recording: {sid}")
        if sid in active_sessions:
            active_sessions[sid]["start_time"] = datetime.now()
            active_sessions[sid]["transcription_buffer"] = []
            active_sessions[sid]["audio_chunks"] = []
            active_sessions[sid]["full_audio"] = b""
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
        
        # Transcribe with realtime.py
        try:
            text = transcribe_audio_chunk(data)
            
            if text and text.strip():
                # Add to buffer
                session["transcription_buffer"].append({
                    "timestamp": timestamp,
                    "text": text
                })
                
                # Send transcription back to client
                await sio.emit('transcription', {
                    "timestamp": timestamp,
                    "text": text
                }, room=sid)
                
                print(f"[Socket.IO] Transcribed for {sid}: {text[:50]}...")
                
        except Exception as e:
            print(f"[Socket.IO] Error transcribing chunk: {e}")
            import traceback
            traceback.print_exc()
    
    @sio.event
    async def stop_recording(sid):
        """Stop recording and save transcription (realtime.py workflow)"""
        print(f"[Socket.IO] Stop recording: {sid}")
        
        if sid not in active_sessions:
            await sio.emit('error', {'message': 'No active session'}, room=sid)
            return
        
        session = active_sessions[sid]
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. Save audio as WAV (like realtime.py does)
            audio_filename = f"audio_{timestamp}.wav"
            audio_path = Path(f"notas/{audio_filename}")
            audio_path.parent.mkdir(exist_ok=True)
            
            if session["audio_chunks"]:
                save_audio_as_wav(session["audio_chunks"], audio_path)
            
            # 2. Create markdown transcription (like realtime.py)
            all_transcripts = [
                (datetime.now(), item['text'])
                for item in session["transcription_buffer"]
            ]
            
            # Use realtime.py's formatter
            formatter = FormatterFactory.create_markdown_formatter()
            formatted_content = formatter.format(all_transcripts)
            
            # 3. Save markdown file to a temporary location
            md_filename = f"transcripcion_{timestamp}.md"
            temp_dir = Path("temporal_docs/raw_transcriptions")
            temp_dir.mkdir(parents=True, exist_ok=True)
            md_path = temp_dir / md_filename
            
            # Use realtime.py's OutputWriter
            writer = OutputWriter(str(md_path))
            writer.write(formatted_content)
            
            print(f"[Socket.IO] Saved transcription: {md_filename}")
            print(f"[Socket.IO] Saved audio: {audio_filename}")
            
            # 4. Ingest into MongoDB
            try:
                db = MongoManager()
                ingestor = TranscriptionIngestor()
                ingestor._ingest_file(md_path)
                print(f"[Socket.IO] Ingested to MongoDB")
                
                # 5. Analyze with LLM
                analyzer = TranscriptionAnalyzer()
                analyzer.analyze_pending()
                print(f"[Socket.IO] Analyzed with LLM")
                
                # 6. Generate formatted document
                generator = DocumentGenerator()
                generator.generate_all()
                print(f"[Socket.IO] Generated formatted document")
                
            except Exception as e:
                print(f"[Socket.IO] Warning: Post-processing error: {e}")
                # Continue anyway, files were saved
            
            await sio.emit('recording_stopped', {
                'message': 'Transcription saved and processed',
                'filename': md_filename,
                'audio_file': audio_filename,
                'segments': len(session["transcription_buffer"])
            }, room=sid)
            
            print(f"[Socket.IO] Completed session for {sid}")
            
        except Exception as e:
            print(f"[Socket.IO] Error saving transcription: {e}")
            import traceback
            traceback.print_exc()
            await sio.emit('error', {'message': str(e)}, room=sid)

def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


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

def transcribe_audio_chunk(audio_data: bytes) -> str:
    """
    Transcribe audio chunk using realtime.py transcriber
    
    Args:
        audio_data: Raw audio bytes from browser
    
    Returns:
        Transcribed text
    """
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
            "full_audio": b""
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
    async def start_recording(sid):
        """Start recording session"""
        print(f"[Socket.IO] Start recording: {sid}")
        if sid in active_sessions:
            active_sessions[sid]["start_time"] = datetime.now()
            active_sessions[sid]["transcription_buffer"] = []
            active_sessions[sid]["audio_chunks"] = []
            active_sessions[sid]["full_audio"] = b""
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
        
        # Transcribe with realtime.py
        try:
            text = transcribe_audio_chunk(data)
            
            if text and text.strip():
                # Add to buffer
                session["transcription_buffer"].append({
                    "timestamp": timestamp,
                    "text": text
                })
                
                # Send transcription back to client
                await sio.emit('transcription', {
                    "timestamp": timestamp,
                    "text": text
                }, room=sid)
                
                print(f"[Socket.IO] Transcribed for {sid}: {text[:50]}...")
                
        except Exception as e:
            print(f"[Socket.IO] Error transcribing chunk: {e}")
            import traceback
            traceback.print_exc()
    
    @sio.event
    async def stop_recording(sid):
        """Stop recording and save transcription"""
        print(f"[Socket.IO] Stop recording: {sid}")
        
        if sid not in active_sessions:
            await sio.emit('error', {'message': 'No active session'}, room=sid)
            return
        
        session = active_sessions[sid]
        
        try:
            # Combine all transcription chunks
            full_text = "\n\n".join([
                f"**{item['timestamp']}**\n{item['text']}" 
                for item in session["transcription_buffer"]
            ])
            
            if not full_text.strip():
                full_text = "[No se detectó audio o no se pudo transcribir]"
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcripcion_{timestamp}.md"
            file_path = Path(f"notas/{filename}")
            
            file_path.parent.mkdir(exist_ok=True)
            file_path.write_text(full_text, encoding='utf-8')
            
            print(f"[Socket.IO] Saved raw transcription: {filename}")
            
            # Ingest into MongoDB
            try:
                db = MongoManager()
                ingestor = TranscriptionIngestor()
                ingestor._ingest_file(file_path)
                print(f"[Socket.IO] Ingested to MongoDB")
                
                # Analyze with LLM
                analyzer = TranscriptionAnalyzer()
                analyzer.analyze_pending()
                print(f"[Socket.IO] Analyzed with LLM")
                
                # Generate document
                generator = DocumentGenerator()
                generator.generate_all()
                print(f"[Socket.IO] Generated formatted document")
                
            except Exception as e:
                print(f"[Socket.IO] Warning: Post-processing error: {e}")
                # Continue anyway, file was saved
            
            await sio.emit('recording_stopped', {
                'message': 'Transcription saved and processed',
                'filename': filename,
                'segments': len(session["transcription_buffer"])
            }, room=sid)
            
            print(f"[Socket.IO] Completed session for {sid}")
            
        except Exception as e:
            print(f"[Socket.IO] Error saving transcription: {e}")
            import traceback
            traceback.print_exc()
            await sio.emit('error', {'message': str(e)}, room=sid)

def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
