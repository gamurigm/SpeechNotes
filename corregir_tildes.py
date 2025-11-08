#!/usr/bin/env python3
"""
Script para corregir tildes faltantes en transcripciones de Whisper
Uso: python corregir_tildes.py <archivo.md>
"""

import sys
import re
from pathlib import Path

# Diccionario de correcciones comunes (sin tilde -> con tilde)
CORRECCIONES = {
    # Palabras muy comunes
    'mas': 'más',
    'dia': 'día',
    'aca': 'acá',
    'alla': 'allá',
    'aqui': 'aquí',
    'ahi': 'ahí',
    'asi': 'así',
    'despues': 'después',
    'tambien': 'también',
    'acion': 'ación',
    'cion': 'ción',
    
    # Verbos comunes
    'esta': 'está',
    'estas': 'estás',
    'estan': 'están',
    'estaba': 'estaba',
    'este': 'esté',
    'estes': 'estés',
    'esten': 'estén',
    'fue': 'fue',
    'seria': 'sería',
    'podria': 'podría',
    'haria': 'haría',
    'tenia': 'tenía',
    'queria': 'quería',
    'decia': 'decía',
    'hacia': 'hacía',
    'habia': 'había',
    'sabia': 'sabía',
    'debia': 'debía',
    
    # Pronombres interrogativos y relativos
    'que': 'qué',
    'cual': 'cuál',
    'quien': 'quién',
    'como': 'cómo',
    'cuando': 'cuándo',
    'donde': 'dónde',
    'cuanto': 'cuánto',
    
    # Adjetivos y adverbios
    'facil': 'fácil',
    'dificil': 'difícil',
    'util': 'útil',
    'movil': 'móvil',
    'rapido': 'rápido',
    'ultimo': 'último',
    'unico': 'único',
    'basico': 'básico',
    'practico': 'práctico',
    'logico': 'lógico',
    'publico': 'público',
    'matematico': 'matemático',
    'cientifico': 'científico',
    'economico': 'económico',
    'politico': 'político',
    
    # Sustantivos comunes
    'razon': 'razón',
    'solucion': 'solución',
    'informacion': 'información',
    'situacion': 'situación',
    'educacion': 'educación',
    'leccion': 'lección',
    'atencion': 'atención',
    'opinion': 'opinión',
    'version': 'versión',
    'acion': 'acción',
    'ingl��s': 'inglés',
    'ingls': 'inglés',
    'espanol': 'español',
    'frances': 'francés',
    'aleman': 'alemán',
    'musica': 'música',
    'telefono': 'teléfono',
    'numero': 'número',
    'pagina': 'página',
    'metodo': 'método',
    'codigo': 'código',
    'titulo': 'título',
    'articulo': 'artículo',
    'capitulo': 'capítulo',
    'sabado': 'sábado',
    'miercoles': 'miércoles',
    
    # Expresiones específicas
    'dejame': 'déjame',
    'dime': 'dime',
    'dame': 'dame',
    'fjate': 'fíjate',
    'fijate': 'fíjate',
    'imaginate': 'imagínate',
    'acuerdate': 'acuérdate',
    'cuentame': 'cuéntame',
    
    # Palabras del texto específico
    'nez': 'núñez',
    'sper': 'súper',
    'super': 'súper',
    'cuestion': 'cuestión',
    'atrs': 'atrás',
    'atras': 'atrás',
    'estn': 'están',
    'estn': 'están',
    'contestrselo': 'contárselo',
    'reportrselo': 'reportárselo',
    'preocupis': 'preocupéis',
    'pongis': 'pongáis',
    'veais': 'veáis',
    'veis': 'veis',  # Esta no lleva tilde
    'acordis': 'acordáis',
    'sabis': 'sabéis',
    'tenis': 'tenéis',
    'queris': 'queréis',
    'dejis': 'dejéis',
    'habis': 'habéis',
    'estbamos': 'estábamos',
    'comamos': 'comíamos',
    'encontrrme': 'encontrarme',
    'encontrrmela': 'encontrármela',
    'suscrb': 'suscríbete',
    'hiplogo': 'hipólogo',
    'paps': 'papás',
    'prometi': 'prometió',
    'record': 'recordó',
    'admiti': 'admitió',
    'anunci': 'anunció',
    'confes': 'confesó',
    'inform': 'informó',
    'coment': 'comentó',
    'cont': 'contó',
    'pidi': 'pidió',
    'solt': 'soltó',
    'pregunt': 'preguntó',
    'vendra': 'vendría',
    'ira': 'iría',
    'podra': 'podría',
    'hara': 'haría',
    'dira': 'diría',
    
    # Negativos
    'no lo s': 'no lo sé',
    'no s': 'no sé',
    'si s': 'sí sé',
}

def corregir_texto(texto: str) -> str:
    """Corrige tildes faltantes en el texto"""
    
    # Aplicar correcciones palabra por palabra
    for sin_tilde, con_tilde in CORRECCIONES.items():
        # Usar expresiones regulares para respetar límites de palabra
        # Esto evita reemplazar partes de palabras más largas
        patron = r'\b' + re.escape(sin_tilde) + r'\b'
        texto = re.sub(patron, con_tilde, texto, flags=re.IGNORECASE)
    
    # Correcciones de patrones específicos
    # Palabras terminadas en -cion sin tilde
    texto = re.sub(r'\b(\w+)cion\b', r'\1ción', texto)
    
    # Palabras terminadas en -sion sin tilde
    texto = re.sub(r'\b(\w+)sion\b', r'\1sión', texto)
    
    # Corregir "ve�is" y similares (caracteres corruptos)
    texto = texto.replace('�', 'é')
    texto = texto.replace('��', 'ñ')
    
    return texto

def procesar_archivo(archivo_path: str):
    """Procesa un archivo markdown y corrige las tildes"""
    
    path = Path(archivo_path)
    
    if not path.exists():
        print(f"❌ Error: Archivo no encontrado: {archivo_path}")
        sys.exit(1)
    
    # Leer archivo
    print(f"📖 Leyendo: {path.name}")
    with open(path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Corregir tildes
    print("🔧 Corrigiendo tildes...")
    contenido_corregido = corregir_texto(contenido)
    
    # Crear backup
    backup_path = path.parent / f"{path.stem}_backup{path.suffix}"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(contenido)
    print(f"💾 Backup guardado: {backup_path.name}")
    
    # Guardar archivo corregido
    with open(path, 'w', encoding='utf-8') as f:
        f.write(contenido_corregido)
    
    print(f"✅ Archivo corregido: {path.name}")
    print(f"📊 Tamaño: {len(contenido_corregido)} caracteres")
    
    # Mostrar algunas correcciones realizadas
    diferencias = sum(1 for a, b in zip(contenido, contenido_corregido) if a != b)
    print(f"✏️  Caracteres modificados: {diferencias}")

def main():
    if len(sys.argv) < 2:
        print("Uso: python corregir_tildes.py <archivo.md>")
        print("\nEjemplo:")
        print("  python corregir_tildes.py notas/mi_audio_transcripcion.md")
        sys.exit(1)
    
    archivo = sys.argv[1]
    procesar_archivo(archivo)

if __name__ == "__main__":
    main()
