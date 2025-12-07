#!/usr/bin/env python3
"""
Regenerate Markdown transcriptions from MongoDB and save into `notas/`.

This script will fetch processed transcriptions and their segments from MongoDB.
If `MINIMAX_API_KEY` is set and the `openai` package is available, it will ask Minimax
to format a professional Markdown document. Otherwise it will build a simple markdown
using the local builder.
"""
from pathlib import Path
from datetime import datetime
import os
import sys

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database.mongo_manager import MongoManager
from src.agent.document_generator import DocumentGenerator


def main():
    out_dir = Path("notas")
    out_dir.mkdir(parents=True, exist_ok=True)

    db = MongoManager()

    processed = list(db.transcriptions.find({"processed": True}))
    if not processed:
        print("No se encontraron transcripciones procesadas en MongoDB.")
        return

    gen = DocumentGenerator(output_dir=str(out_dir))

    print(f"Encontradas {len(processed)} transcripciones procesadas. Empezando regeneración...")

    for doc in processed:
        try:
            # load segments
            segments = list(db.segments.find({"transcription_id": doc["_id"]}).sort("sequence", 1))
            if not segments:
                print(f" - {doc.get('filename','(sin nombre)')}: No hay segmentos, omitiendo.")
                continue

            # Prefer Minimax if client available
            if gen.client:
                print(f" - {doc.get('filename')}: Formateando con Minimax...")
                md = gen._generate_with_minimax(doc, gen._group_by_topic(segments))
            else:
                print(f" - {doc.get('filename')}: Minimax no configurado, construyendo Markdown localmente...")
                md = gen._build_markdown(doc, gen._group_by_topic(segments))

            # Write to notas/transcription_<original>.md
            original = doc.get('filename', f"{doc.get('_id')}" )
            # sanitize
            fname = f"transcription_{original}"
            if not fname.lower().endswith('.md'):
                fname += '.md'

            out_path = out_dir / fname
            out_path.write_text(md, encoding='utf-8')
            print(f"   ✅ Guardado: {out_path}")

        except Exception as e:
            print(f"   ⚠️ Error regenerando {doc.get('filename','(sin nombre)')}: {e}")

    print("Regeneración completada.")


if __name__ == '__main__':
    main()
