# Knowledge Base

Este directorio contiene las versiones procesadas de las transcripciones y otros documentos indexados para búsqueda semántica.

## Estructura

```
knowledge_base/
├── transcriptions/     # Transcripciones procesadas en formato markdown profesional
│   ├── processed_*.md  # Archivos procesados con temas y timestamps
│   └── index_metadata.json  # Metadata del índice
└── documents/          # Otros documentos indexados
```

## Transcripciones

Las transcripciones originales en `notas/` se procesan automáticamente y se guardan aquí en formato markdown profesional con:

- ✅ Detección automática de temas
- ✅ Timestamps por sección
- ✅ Tabla de contenidos
- ✅ Puntos clave
- ✅ Metadata estructurada

## Indexación

Para indexar transcripciones:

```bash
# Indexar nuevas/actualizadas
python scripts/index_transcriptions.py

# Indexar todas
python scripts/index_transcriptions.py --all

# Listar indexadas
python scripts/index_transcriptions.py --list
```

## Nota

Los archivos en este directorio se generan automáticamente y pueden ser regenerados en cualquier momento desde los originales en `notas/`.
