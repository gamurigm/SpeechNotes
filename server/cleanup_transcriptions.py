"""Cleanup transcriptions script

Detecta transcripciones inválidas (contenido muy corto o duración 0s) en `notas/`
y las mueve a `notas/invalid/` por seguridad. Opcionalmente puede borrar definitivamente
si se pasa `--delete`.

Uso:
  python server/cleanup_transcriptions.py       # solo mueve archivos inválidos a notas/invalid/
  python server/cleanup_transcriptions.py --delete  # borra archivos inválidos
"""
from pathlib import Path
import re
import shutil
import argparse


NOTAS_DIR = Path("notas")
INVALID_DIR = NOTAS_DIR / "invalid"


def extract_transcription_text(text: str) -> str:
    """Extrae la sección de transcripción del markdown."""
    # Buscar encabezados comunes
    patterns = [r"## 📝 Transcripción Completa\n(.*?)(?:\n---|$)",
                r"## 📝 Transcripción\n(.*?)(?:\n---|$)",
                r"## 🕐 Transcripción por Segmentos\n(.*?)(?:\n---|$)",
                r"## 📝 Transcripción(.*)",
                r"# Transcripción.*?\n(.*)"]

    for pat in patterns:
        m = re.search(pat, text, flags=re.S)
        if m:
            return m.group(1).strip()

    # Fallback: remove frontmatter and headers
    # Remove YAML frontmatter
    text = re.sub(r"^---.*?---", "", text, flags=re.S)
    # Remove markdown headers
    text = re.sub(r"#+\s.*", "", text)
    return text.strip()


def word_count(s: str) -> int:
    words = re.findall(r"\w+", s, flags=re.UNICODE)
    return len(words)


def duration_is_zero(text: str) -> bool:
    m = re.search(r"Duración:\s*([0-9]+)m\s*([0-9]+)s", text)
    if m:
        minutes = int(m.group(1))
        seconds = int(m.group(2))
        return minutes == 0 and seconds == 0
    # Also check for explicit 0s
    return False


def is_invalid_transcription(file_path: Path, min_words: int = 6) -> bool:
    try:
        txt = file_path.read_text(encoding='utf-8')
    except Exception:
        return True

    body = extract_transcription_text(txt)
    wc = word_count(body)
    if wc < min_words:
        return True

    if duration_is_zero(txt):
        # If duration zero and very short, mark invalid
        if wc < (min_words * 2):
            return True

    # Heuristic: if body contains only one repeated token (e.g., 'amén' or repeated punctuation)
    tokens = re.findall(r"\w+", body.lower())
    if tokens:
        unique = set(tokens)
        if len(unique) == 1 and len(tokens) < 20:
            return True

    return False


def cleanup(delete: bool = False):
    if not NOTAS_DIR.exists():
        print(f"No se encontró el directorio {NOTAS_DIR}")
        return

    INVALID_DIR.mkdir(parents=True, exist_ok=True)

    md_files = list(NOTAS_DIR.glob("*.md"))
    moved = []
    deleted = []

    for f in md_files:
        # Skip files already in invalid folder
        if f.parent == INVALID_DIR:
            continue

        if is_invalid_transcription(f):
            if delete:
                f.unlink()
                deleted.append(f.name)
            else:
                dest = INVALID_DIR / f.name
                shutil.move(str(f), str(dest))
                moved.append(f.name)

    print("Cleanup complete.")
    if moved:
        print(f"Moved {len(moved)} files to {INVALID_DIR}:")
        for n in moved:
            print(" - ", n)
    if deleted:
        print(f"Deleted {len(deleted)} files:")
        for n in deleted:
            print(" - ", n)
    if not moved and not deleted:
        print("No invalid transcriptions found.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--delete', action='store_true', help='Eliminar archivos inválidos en lugar de moverlos')
    parser.add_argument('--min-words', type=int, default=6, help='Mínimo de palabras para considerar válida una transcripción')
    args = parser.parse_args()

    cleanup(delete=args.delete)
