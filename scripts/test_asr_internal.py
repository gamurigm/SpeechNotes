"""Manual smoke check for the configured ASR client.

This script calls the external ASR service and is intentionally kept outside
the automated test suite. Run it manually only when valid NVIDIA credentials
are configured.
"""

import asyncio
import io
import struct
import sys
import wave
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "backend"))

from services.nim.registry import NIMRegistry


async def main():
    registry = NIMRegistry.instance()
    asr_client = registry.get_asr("es")
    print(f"ASR Client type: {type(asr_client)}")

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        for _ in range(16000):
            wav.writeframes(struct.pack("h", 0))

    print("Sending audio to ASR...")
    try:
        result = await asr_client.transcribe(
            buffer.getvalue(), sample_rate=16000, language="es"
        )
        print("Result:", result)
    except Exception as exc:
        print("Error during transcription:", exc)


if __name__ == "__main__":
    asyncio.run(main())
