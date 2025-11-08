#!/usr/bin/env python3
"""
Script para corregir tildes usando IA (OpenAI GPT)
Uso: python corregir_tildes_ia.py <archivo.md>
"""

import sys
import os
from pathlib import Path
from openai import OpenAI

def corregir_con_ia(texto: str) -> str:
    """Corrige tildes usando OpenAI GPT"""
    
    # Obtener API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY no configurada")
        print("Ejecuta: $env:OPENAI_API_KEY='tu-api-key'")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    print("🤖 Corrigiendo tildes con GPT-4...")
    
    # Dividir texto en chunks si es muy largo (max 4000 tokens aprox)
    max_chars = 15000
    chunks = []
    
    if len(texto) > max_chars:
        # Dividir por párrafos aproximadamente
        words = texto.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) > max_chars:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
    else:
        chunks = [texto]
    
    # Corregir cada chunk
    textos_corregidos = []
    
    for i, chunk in enumerate(chunks):
        print(f"   Procesando parte {i+1}/{len(chunks)}...")
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Más barato y rápido
            messages=[
                {
                    "role": "system",
                    "content": """Eres un corrector de texto en español. Tu tarea es:
1. Agregar TODAS las tildes faltantes en español
2. NO cambiar ninguna palabra
3. NO agregar ni quitar texto
4. NO agregar puntuación adicional
5. Mantener EXACTAMENTE el mismo formato y estructura
6. Solo corregir la ortografía de tildes (acentos)

Ejemplos:
- "dia" → "día"
- "mas" → "más" (cuando significa "more")
- "esta" → "está" (cuando es verbo)
- "que" → "qué" (cuando es interrogativo)
- "como" → "cómo" (cuando es interrogativo)

Devuelve ÚNICAMENTE el texto corregido, sin explicaciones."""
                },
                {
                    "role": "user",
                    "content": f"Corrige las tildes en este texto:\n\n{chunk}"
                }
            ],
            temperature=0.1,  # Baja temperatura para ser más conservador
            max_tokens=len(chunk.split()) * 2  # Espacio suficiente
        )
        
        texto_corregido = response.choices[0].message.content.strip()
        textos_corregidos.append(texto_corregido)
    
    return " ".join(textos_corregidos)

def procesar_archivo(archivo_path: str):
    """Procesa un archivo markdown y corrige las tildes con IA"""
    
    path = Path(archivo_path)
    
    if not path.exists():
        print(f"❌ Error: Archivo no encontrado: {archivo_path}")
        sys.exit(1)
    
    # Leer archivo
    print(f"📖 Leyendo: {path.name}")
    with open(path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Extraer solo la transcripción (entre ## 📝 Transcripción Completa y ---)
    import re
    match = re.search(r'## 📝 Transcripción Completa\n\n(.*?)\n\n---', contenido, re.DOTALL)
    
    if not match:
        print("❌ Error: No se encontró la sección de transcripción")
        sys.exit(1)
    
    texto_original = match.group(1)
    print(f"📏 Longitud del texto: {len(texto_original)} caracteres")
    
    # Corregir con IA
    texto_corregido = corregir_con_ia(texto_original)
    
    # Reemplazar en el contenido
    contenido_corregido = contenido.replace(texto_original, texto_corregido)
    
    # Crear backup
    backup_path = path.parent / f"{path.stem}_backup{path.suffix}"
    if not backup_path.exists():
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"💾 Backup guardado: {backup_path.name}")
    
    # Guardar archivo corregido
    with open(path, 'w', encoding='utf-8') as f:
        f.write(contenido_corregido)
    
    print(f"✅ Archivo corregido: {path.name}")
    print(f"📊 Tamaño final: {len(contenido_corregido)} caracteres")

def main():
    if len(sys.argv) < 2:
        print("Uso: python corregir_tildes_ia.py <archivo.md>")
        print("\nEjemplo:")
        print("  python corregir_tildes_ia.py notas/mi_audio_transcripcion.md")
        print("\nRequiere:")
        print("  - pip install openai")
        print("  - $env:OPENAI_API_KEY='tu-api-key'")
        sys.exit(1)
    
    archivo = sys.argv[1]
    procesar_archivo(archivo)

if __name__ == "__main__":
    main()
