import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from services.nim.registry import NIMRegistry

async def main():
    registry = NIMRegistry.instance()
    # "asr" is the Riva ASR client
    asr_client = registry.get_asr("es")
    print(f"ASR Client type: {type(asr_client)}")
    
    # Let's generate a 1-second dummy wav file in memory
    import wave
    import io
    import struct
    
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        # 16000 frames of silence
        for _ in range(16000):
            wav.writeframes(struct.pack('h', 0))
    
    audio_bytes = buf.getvalue()
    
    print("Sending audio to ASR...")
    try:
        res = await asr_client.transcribe(audio_bytes, sample_rate=16000, language="es")
        print("Result:", res)
    except Exception as e:
        print("Error during transcription:", e)

if __name__ == "__main__":
    asyncio.run(main())
