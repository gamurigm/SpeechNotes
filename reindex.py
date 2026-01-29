import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from openai import OpenAI

# Definir la raíz del proyecto
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

load_dotenv()

# Configuración de NVIDIA
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nvidia/nv-embedqa-e5-v5")
LLM_API_KEY = os.getenv("NVIDIA_API_KEY")
EMBED_API_KEY = os.getenv("NVIDIA_EMBEDDING_API_KEY") or LLM_API_KEY

class NvidiaEmbeddings:
    def __init__(self, model, api_key, base_url):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def embed_documents(self, texts):
        print(f"Indexando {len(texts)} fragmentos...")
        all_embeddings = []
        # Lotes de 20 para estabilidad
        for i in range(0, len(texts), 20):
            batch = texts[i:i+20]
            resp = self.client.embeddings.create(
                model=self.model,
                input=batch,
                encoding_format="float",
                extra_body={"input_type": "passage", "truncate": "NONE"},
            )
            all_embeddings.extend([item.embedding for item in resp.data])
            print(f"  - Progreso: {len(all_embeddings)}/{len(texts)}", flush=True)
        return all_embeddings

    def embed_query(self, text):
        resp = self.client.embeddings.create(
            model=self.model,
            input=[text],
            encoding_format="float",
            extra_body={"input_type": "query", "truncate": "NONE"},
        )
        return resp.data[0].embedding

def main():
    if not EMBED_API_KEY:
        print("Error: No se encontró NVIDIA_API_KEY para embeddings.")
        return

    data_dir = project_root / "notas"
    db_dir = project_root / "knowledge_base" / "chroma_db_new"

    print(f"Buscando archivos .md en {data_dir}...")
    chunks = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    
    files = list(data_dir.glob("**/*.md"))
    for f in files:
        try:
            content = f.read_text(encoding='utf-8')
            if not content.strip(): continue
            print(f" - Cargando: {f.name}")
            doc_chunks = splitter.create_documents([content], metadatas=[{"source": f.name, "filename": f.name}])
            chunks.extend(doc_chunks)
        except Exception as e:
            print(f"   Error en {f.name}: {e}")

    if not chunks:
        print("No se encontraron documentos para indexar.")
        return

    print(f"Total de fragmentos a indexar: {len(chunks)}")
    embeddings = NvidiaEmbeddings(model=EMBEDDING_MODEL, api_key=EMBED_API_KEY, base_url=NVIDIA_BASE_URL)

    print(f"Guardando en {db_dir}...")
    import shutil
    if db_dir.exists():
        shutil.rmtree(db_dir, ignore_errors=True)

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(db_dir)
    )
    print("¡Base de datos regenerada con éxito!")

if __name__ == "__main__":
    main()
