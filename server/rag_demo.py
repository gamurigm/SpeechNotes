"""RAG demo script

Construye un índice FAISS a partir de archivos `.md` en `notas/` o `data/` y ejecuta
una consulta RAG simple. Si existe la variable de entorno `OPENAI_API_KEY`, intentará
usar OpenAI para generar la respuesta final; en caso contrario, usará un pipeline
de `transformers` (si está disponible) para resumir extractivamente los snippets
recuperados. Si tampoco está disponible, devolverá la concatenación de snippets.

Ejemplo:
    python server/rag_demo.py --query "¿Cómo exporto una transcripción?"
"""
import os
import sys
import argparse
from pathlib import Path
import re
import json

try:
    from sentence_transformers import SentenceTransformer
except Exception as e:
    print("Error: requiere 'sentence-transformers'. Instala: pip install sentence-transformers")
    raise

try:
    import faiss
except Exception:
    print("Error: requiere 'faiss-cpu' (o faiss). Instala: pip install faiss-cpu")
    raise

try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except Exception:
    HAS_TRANSFORMERS = False

try:
    import openai
    HAS_OPENAI = True
except Exception:
    HAS_OPENAI = False

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def list_md_files(dirs=("notas", "data")):
    files = []
    for d in dirs:
        p = Path(d)
        if not p.exists():
            continue
        for f in p.rglob("*.md"):
            files.append(f)
    return files


def clean_md(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    return text.strip()


def chunk_text(text, max_chars=1000, overlap=200):
    text = text.replace("\n", " ")
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def build_corpus_and_index(model, files, max_docs=2000):
    texts = []
    meta = []
    for f in files:
        try:
            txt = f.read_text(encoding="utf-8")
        except Exception:
            continue
        txt = clean_md(txt)
        chunks = chunk_text(txt)
        for i, c in enumerate(chunks):
            texts.append(c)
            meta.append({"file": str(f), "chunk_index": i})
            if len(texts) >= max_docs:
                break
        if len(texts) >= max_docs:
            break

    if not texts:
        # fallback sample
        texts = [
            "Para exportar, usa la opción Exportar en la barra superior y elige Markdown o SRT.",
            "El sistema guarda automáticamente en la carpeta data/notes con metadata.",
            "Puedes detener la grabación con Stop y luego editar la transcripción en el panel de la izquierda."
        ]
        meta = [{"file": "__sample__", "chunk_index": i} for i in range(len(texts))]

    print(f"Calculando embeddings para {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    import numpy as np
    emb = np.array(embeddings).astype("float32")
    # normalize for cosine similarity with IndexFlatIP
    faiss.normalize_L2(emb)
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)
    return index, texts, meta


def rag_query(index, texts, meta, model, query, top_k=5):
    import numpy as np
    q_emb = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(q_emb)
    D, I = index.search(q_emb, top_k)
    results = []
    for score, idx in zip(D[0].tolist(), I[0].tolist()):
        results.append({"score": float(score), "snippet": texts[idx], **meta[idx]})
    return results


def generate_answer_with_openai(retrieved, query):
    if not HAS_OPENAI:
        raise RuntimeError("openai package no disponible")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no está definida en el entorno")
    openai.api_key = api_key
    prompt_chunks = "\n\n---\n\n".join([f"Source ({r['file']}): {r['snippet']}" for r in retrieved])
    system = "Eres un asistente que usa fragmentos de documentos para responder preguntas de forma concisa y referenciar las fuentes." 
    user_prompt = f"Pregunta: {query}\n\nDocumentos:\n{prompt_chunks}\n\nRespuesta:" 
    resp = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt}
    ], max_tokens=300)
    return resp.choices[0].message.content.strip()


def generate_answer_extractive(retrieved, query):
    # concat snippets and summarize if pipeline available
    concat = "\n\n".join([r["snippet"] for r in retrieved])
    if HAS_TRANSFORMERS:
        try:
            summarizer = pipeline("summarization")
            summary = summarizer(concat, max_length=150, min_length=30, do_sample=False)
            return summary[0]["summary_text"].strip()
        except Exception:
            pass
    # fallback: return concatenation trimmed
    return concat[:2000] + ("..." if len(concat) > 2000 else "")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", "-q", required=False, help="Consulta para RAG")
    parser.add_argument("--topk", type=int, default=5)
    args = parser.parse_args()

    model = SentenceTransformer(MODEL_NAME)

    files = list_md_files()
    print(f"Archivos encontrados: {len(files)}")
    index, texts, meta = build_corpus_and_index(model, files)

    if args.query:
        query = args.query
    else:
        query = input("Escribe la consulta RAG: ")

    retrieved = rag_query(index, texts, meta, model, query, top_k=args.topk)
    print("\nRecuperados:")
    for r in retrieved:
        print(f"- score={r['score']:.3f} file={r['file']}\n  {r['snippet'][:200].replace('\n',' ')}...\n")

    answer = None
    if HAS_OPENAI and os.environ.get("OPENAI_API_KEY"):
        try:
            print("Generando respuesta con OpenAI...")
            answer = generate_answer_with_openai(retrieved, query)
        except Exception as e:
            print(f"OpenAI failed: {e}")
            answer = generate_answer_extractive(retrieved, query)
    else:
        answer = generate_answer_extractive(retrieved, query)

    print("\n=== ANSWER ===\n")
    print(answer)


if __name__ == "__main__":
    main()
