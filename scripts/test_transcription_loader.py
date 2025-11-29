"""
Simple test for transcription loader
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent import TranscriptionLoader

def main():
    print("\n" + "=" * 60)
    print("TEST: Transcription Loader")
    print("=" * 60 + "\n")
    
    # Create loader
    loader = TranscriptionLoader()
    
    # Load files
    print("1. Cargando archivos de transcripción...")
    files = loader.load_from_directory()
    print(f"   ✓ Encontrados {len(files)} archivos\n")
    
    if not files:
        print("⚠️ No hay archivos para procesar")
        return
    
    # Test with first file
    test_file = files[0]
    print(f"2. Probando con: {test_file.name}")
    
    # Extract metadata
    print("   Extrayendo metadata...")
    metadata = loader.extract_metadata(test_file)
    print(f"   ✓ Fecha: {metadata['date']}")
    print(f"   ✓ Palabras: {metadata['word_count']:,}")
    print(f"   ✓ Segmentos: {metadata['segment_count']}\n")
    
    # Read content
    print("3. Leyendo contenido...")
    content = test_file.read_text(encoding='utf-8')
    print(f"   ✓ Caracteres: {len(content):,}\n")
    
    # Detect topics (fallback only, no AI)
    print("4. Detectando temas (modo fallback)...")
    topics = loader._fallback_segmentation(content)
    print(f"   ✓ Temas detectados: {len(topics)}")
    for i, topic in enumerate(topics[:3], 1):
        print(f"      {i}. {topic['title']} ({topic['timestamp_start']})")
    print()
    
    # Format markdown
    print("5. Formateando markdown...")
    formatted = loader.format_professional_md(metadata, topics, test_file)
    print(f"   ✓ Markdown generado: {len(formatted):,} caracteres\n")
    
    # Save
    print("6. Guardando archivo procesado...")
    output_path = loader.save_processed(formatted, test_file.name)
    print(f"   ✓ Guardado en: {output_path}\n")
    
    print("=" * 60)
    print("✅ Test completado exitosamente")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
