# Guía de Inicio Rápido - NVIDIA NIM + LangGraph Agent

## 🎯 Sistema Completado y Probado

✅ **Todos los tests pasaron**:
- Cliente NVIDIA NIM: 4/4 ✓
- Agente LangGraph: 3/3 ✓
- Demo interactivo: Funcionando ✓

---

## 🚀 Inicio Rápido (5 minutos)

### 1. Demo Interactivo

La forma más rápida de probar el sistema:

```bash
python scripts/run_agent_demo.py
```

**Prueba estas consultas**:
```
¿Qué es FAISS?
Explica qué es Python
¿Para qué sirve LangGraph?
Escribe un haiku sobre programación
```

**Comandos útiles**:
- `/docs` - Ver documentos indexados
- `/help` - Ayuda
- `/exit` - Salir

---

## 💻 Ejemplos de Código

### Ejemplo 1: Generación Simple

```python
from src.llm.nvidia_client import NvidiaInferenceClient

# Crear cliente (solo se crea una instancia - Singleton)
client = NvidiaInferenceClient()

# Generar respuesta
respuesta = client.generate("Explica qué es la inteligencia artificial en 2 oraciones")
print(respuesta)
```

**Salida esperada**:
```
La inteligencia artificial es la simulación de procesos de inteligencia 
humana por parte de máquinas, especialmente sistemas informáticos...
```

---

### Ejemplo 2: Búsqueda Semántica

```python
from src.agent.vector_store import VectorStore

# Crear vector store
vs = VectorStore()

# Indexar documentos
documentos = [
    "Python es un lenguaje de programación de alto nivel, interpretado y versátil.",
    "JavaScript es el lenguaje principal para desarrollo web frontend.",
    "SQL se utiliza para gestionar y consultar bases de datos relacionales."
]

metadatos = [
    {"lenguaje": "Python", "tipo": "General"},
    {"lenguaje": "JavaScript", "tipo": "Web"},
    {"lenguaje": "SQL", "tipo": "Database"}
]

vs.add_documents(documentos, metadatos)

# Buscar
resultados = vs.search("¿Qué lenguaje uso para web?", k=2)

for res in resultados:
    print(f"Score: {res['score']:.3f}")
    print(f"Lenguaje: {res['metadata']['lenguaje']}")
    print(f"Texto: {res['document'][:50]}...")
    print()
```

**Salida esperada**:
```
Score: 0.892
Lenguaje: JavaScript
Texto: JavaScript es el lenguaje principal para desar...

Score: 0.654
Lenguaje: Python
Texto: Python es un lenguaje de programación de alto...
```

---

### Ejemplo 3: Agente Completo

```python
from src.agent import create_agent_graph, AgentState
from src.agent.nodes import get_vector_store

# 1. Configurar base de conocimientos
vector_store = get_vector_store()

docs_python = [
    "Python fue creado por Guido van Rossum en 1991. Es conocido por su sintaxis clara.",
    "Python se usa en ciencia de datos, machine learning, desarrollo web y automatización.",
    "Las principales librerías de Python incluyen NumPy, Pandas, Django y Flask."
]

vector_store.add_documents(docs_python, [
    {"tema": "Historia"},
    {"tema": "Usos"},
    {"tema": "Librerías"}
])

# 2. Crear agente
app = create_agent_graph()

# 3. Hacer consulta con búsqueda
consulta = "¿Para qué se usa Python?"

estado_inicial = {
    "messages": [{"role": "user", "content": consulta}],
    "query": consulta,
    "search_results": None,
    "generated_text": None,
    "next_action": "",
    "context": None
}

resultado = app.invoke(estado_inicial)

# 4. Ver resultados
print("=== Resultados de Búsqueda ===")
for i, res in enumerate(resultado["search_results"], 1):
    print(f"{i}. Score: {res['score']:.3f} - {res['metadata']['tema']}")

print("\n=== Respuesta Generada ===")
print(resultado["generated_text"])
```

**Salida esperada**:
```
=== Resultados de Búsqueda ===
1. Score: 0.945 - Usos
2. Score: 0.723 - Librerías
3. Score: 0.612 - Historia

=== Respuesta Generada ===
Python se utiliza en una amplia variedad de aplicaciones, incluyendo:
- Ciencia de datos y análisis
- Machine learning e inteligencia artificial
- Desarrollo web (con frameworks como Django y Flask)
- Automatización de tareas y scripts
...
```

---

## 🎨 Casos de Uso Prácticos

### Caso 1: Asistente de Documentación Técnica

```python
# Indexar tu documentación
docs_api = [
    "GET /api/users - Obtiene lista de usuarios. Requiere autenticación.",
    "POST /api/users - Crea un nuevo usuario. Body: {name, email, password}",
    "DELETE /api/users/:id - Elimina un usuario. Requiere rol admin."
]

vector_store.add_documents(docs_api)

# Usuario pregunta
resultado = app.invoke({
    "query": "¿Cómo creo un usuario nuevo?",
    ...
})
```

---

### Caso 2: Chatbot de Soporte

```python
# Base de conocimientos de FAQs
faqs = [
    "Política de devoluciones: 30 días desde la compra con recibo.",
    "Envíos: Gratis en compras mayores a $50. Entrega en 3-5 días.",
    "Garantía: 1 año en todos los productos electrónicos."
]

vector_store.add_documents(faqs)

# Cliente pregunta
resultado = app.invoke({
    "query": "¿Cuánto tarda el envío?",
    ...
})
```

---

### Caso 3: Generador de Contenido

```python
# Sin búsqueda, generación directa
resultado = app.invoke({
    "query": "Escribe un email de bienvenida para nuevos empleados",
    ...
})

print(resultado["generated_text"])
```

---

## 🔧 Personalización

### Ajustar Parámetros del Modelo

Edita `.env`:

```env
# Más creativo (0.0 - 1.0)
TEMPERATURE=0.8

# Más diverso (0.0 - 1.0)
TOP_P=0.9

# Respuestas más largas
MAX_TOKENS=16384
```

O en código:

```python
client = NvidiaInferenceClient()
respuesta = client.generate(
    "Tu prompt",
    temperature=0.9,  # Más creativo
    max_tokens=2000   # Más largo
)
```

---

### Cambiar Modelo de Embeddings

En `.env`:

```env
# Opciones disponibles en NVIDIA NIM
EMBEDDING_MODEL=nvidia/nv-embedqa-e5-v5
# EMBEDDING_MODEL=nvidia/nv-embed-v1
```

---

## 📊 Monitoreo y Debugging

### Ver qué ruta tomó el agente

```python
resultado = app.invoke(estado_inicial)

# Ver el flujo
print("Acción tomada:", resultado["next_action"])
if resultado["search_results"]:
    print("Se realizó búsqueda semántica")
    print(f"Encontrados: {len(resultado['search_results'])} documentos")
else:
    print("Generación directa sin búsqueda")
```

---

### Verificar calidad de búsqueda

```python
resultados = vector_store.search("tu consulta", k=5)

for res in resultados:
    print(f"Score: {res['score']:.3f}")
    if res['score'] < 0.5:
        print("⚠️ Baja relevancia")
    elif res['score'] > 0.8:
        print("✅ Alta relevancia")
```

---

## 🎓 Próximos Pasos

### 1. Agregar tus propios documentos

```python
# Cargar desde archivos
import os

docs = []
for archivo in os.listdir("mi_documentacion/"):
    with open(f"mi_documentacion/{archivo}", 'r', encoding='utf-8') as f:
        docs.append(f.read())

vector_store.add_documents(docs)
```

### 2. Persistir el vector store

```python
import pickle

# Guardar
with open("vector_store.pkl", "wb") as f:
    pickle.dump(vector_store, f)

# Cargar
with open("vector_store.pkl", "rb") as f:
    vector_store = pickle.load(f)
```

### 3. Crear una API REST

```python
from fastapi import FastAPI

app_api = FastAPI()

@app_api.post("/query")
async def query(pregunta: str):
    resultado = app.invoke({"query": pregunta, ...})
    return {"respuesta": resultado["generated_text"]}
```

---

## 📞 Soporte

- **Documentación completa**: `docs/nvidia_nim_agent.md`
- **Resumen técnico**: `docs/RESUMEN_IMPLEMENTACION.md`
- **Tests**: `scripts/test_*.py`

---

## ✨ Resumen

**Tu sistema está listo para**:
- ✅ Responder preguntas basadas en documentos
- ✅ Generar contenido creativo
- ✅ Búsqueda semántica de alta calidad
- ✅ Combinar búsqueda + generación inteligentemente

**Comienza ahora**:
```bash
python scripts/run_agent_demo.py
```

¡Disfruta tu agente de IA! 🚀
