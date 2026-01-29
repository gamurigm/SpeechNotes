"""
Knowledge Base Ingestion Script
Loads markdown files from 'notas/', chunks them, and persists embeddings to ChromaDB.
"""

import os
import shutil
from pathlib import Path
from typing import List
from dotenv import load_dotenv

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Optional NVIDIA / OpenAI-compatible embeddings (preferred when available)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None


# Load environment variables
load_dotenv()

def load_and_process_markdown(data_dir: str):
    """
    Load all Markdown files from a directory and split them into text chunks.
    """
    # Initialize directory loader to find all .md files
    loader = DirectoryLoader(
        data_dir,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    
    print(f"Loading Markdown files from: {data_dir}")
    try:
        documents = loader.load()
        print(f"Loaded {len(documents)} documents")
    except Exception as e:
        print(f"Error loading documents: {e}")
        return []
    
    # Configure text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        add_start_index=True,
    )
    
    # Split documents into chunks
    print("Splitting documents into chunks...")
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} text chunks")
    
    return chunks

def create_vector_store(chunks, persist_directory: str):
    """
    Create a ChromaDB vector store from document chunks and persist it to disk.
    """
    # Clear existing vector store to ensure fresh data
    if os.path.exists(persist_directory):
        print(f"Clearing existing vector store at {persist_directory}")
        try:
            shutil.rmtree(persist_directory)
            print("Existing vector store cleared")
        except Exception as e:
            print(f"Warning: Could not clear directory: {e}")
    
    # Initialize embedding model: prefer NVIDIA/OpenAI-compatible if configured
    print("Initializing embedding model...")
    embeddings = None
    # Use NVIDIA/OpenAI-compatible embeddings if env var provided
    emb_api_key = os.getenv("NVIDIA_EMBEDDING_API_KEY") or os.getenv("NVIDIA_API_KEY")
    emb_model = os.getenv("EMBEDDING_MODEL")
    emb_base = os.getenv("NVIDIA_BASE_URL")

    if emb_api_key and emb_model and OpenAI is not None:
        print(f"Using NVIDIA/OpenAI-compatible embedding model: {emb_model}")

        class NvidiaEmbeddingsWrapper:
            def __init__(self, model, api_key, base_url):
                self.model = model
                self.client = OpenAI(api_key=api_key, base_url=base_url)

            def embed_documents(self, texts: list):
                resp = self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                    encoding_format="float",
                    extra_body={"input_type": "passage", "truncate": "NONE"},
                )
                return [item.embedding for item in resp.data]

            def embed_query(self, text: str):
                resp = self.client.embeddings.create(
                    model=self.model,
                    input=[text],
                    encoding_format="float",
                    extra_body={"input_type": "query", "truncate": "NONE"},
                )
                return resp.data[0].embedding

        embeddings = NvidiaEmbeddingsWrapper(model=emb_model, api_key=emb_api_key, base_url=emb_base)
    else:
        print("Falling back to HuggingFace embeddings (sentence-transformers/all-mpnet-base-v2)")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={'device': 'cpu'}
        )
    
    # Create ChromaDB vector store
    print("Creating vector embeddings and building database...")
    
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    print(f"Vector store created with {len(chunks)} embeddings")
    print(f"Database persisted to: {persist_directory}")
    
    return vectordb

def main():
    # Define directories
    # Assuming script is run from project root or scripts/ folder
    # We want to target 'notas/' in project root
    
    current_dir = Path(os.getcwd())
    
    # Determine project root
    if (current_dir / "notas").exists():
        project_root = current_dir
    elif (current_dir.parent / "notas").exists():
        project_root = current_dir.parent
    else:
        # Fallback to relative path assumption
        project_root = Path(__file__).parent.parent

    data_dir = project_root / "notas"
    db_dir = project_root / "knowledge_base" / "chroma_db_new"
    
    print("=" * 60)
    print("KNOWLEDGE BASE INGESTION PIPELINE")
    print("=" * 60)
    print(f"Input directory: {data_dir}")
    print(f"Output directory: {db_dir}")
    print()
    
    if not data_dir.exists():
        print(f"Error: Data directory '{data_dir}' does not exist!")
        return
    
    # Stage 1: Load and process Markdown files
    print("STAGE 1: Loading and processing Markdown files...")
    chunks = load_and_process_markdown(str(data_dir))
    
    if not chunks:
        print("No chunks created. Exiting.")
        return

    # Stage 2: Create vector database
    print("\nSTAGE 2: Creating vector database...")
    create_vector_store(chunks, str(db_dir))
    
    print("\n" + "=" * 60)
    print("INGESTION COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
