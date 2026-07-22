import sys
from pathlib import Path
sys.path.append(str(Path('c:/Users/gamur/Documents/SpeechNotes/SpeechNotes')))

import asyncio
from backend.services.agents.formatter_agent import FormatterAgent

async def main():
    agent = FormatterAgent(Path('c:/Users/gamur/Documents/SpeechNotes/SpeechNotes'))
    
    # Simulate a big transcription (~36,000 chars ΓåÆ 3 chunks of 12k each)
    long_text = ("La clase de hoy trat├│ sobre los principios SOLID de programaci├│n orientada a objetos. "
                 "El profesor explic├│ que el principio de responsabilidad ├║nica establece que cada clase "
                 "debe tener una sola raz├│n para cambiar. Luego habl├│ del principio abierto/cerrado. ") * 200
    
    file_data = {
        'file_name': 'test_large.md',
        'metadata': {'fecha': '2026-07-21', 'temas': 'Programaci├│n OO'},
        'clean_content': long_text
    }
    
    print(f"Content length: {len(file_data['clean_content'])} chars")
    chunk_count = max(1, len(long_text) // 12000)
    print(f"Expected ~{chunk_count} chunk(s)")
    
    try:
        result = await agent._format_step(file_data, max_retries=0)
        print(f"\nSUCCESS -- output length: {len(result)} chars")
        print("--- First 400 chars ---")
        print(result[:400].encode('ascii', 'replace').decode('ascii'))
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
