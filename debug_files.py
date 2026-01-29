import os
from pathlib import Path

project_root = Path(r"C:\Users\gamur\OneDrive - UNIVERSIDAD DE LAS FUERZAS ARMADAS ESPE\ESPE VI NIVEL SII2025\Analisis y Diseño\p")
notes_dir = project_root / "notas"

if not notes_dir.exists():
    print(f"ERROR: La carpeta {notes_dir} no existe.")
else:
    files = list(notes_dir.glob("*.md"))
    print(f"Total de archivos .md encontrados: {len(files)}")
    for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
        size = f.stat().st_size
        print(f"- {f.name} ({size} bytes)")
