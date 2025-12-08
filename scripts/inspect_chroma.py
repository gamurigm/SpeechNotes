import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def inspect_knowledge_base():
    # Initialize embeddings (must match ingestion)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'cpu'}
    )

    # Initialize Vector Store
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_dir = os.path.join(project_root, "knowledge_base", "chroma_db")
    
    print(f"Inspecting ChromaDB at: {db_dir}")

    if not os.path.exists(db_dir):
        print("Database directory does not exist!")
        return

    vectordb = Chroma(
        persist_directory=db_dir,
        embedding_function=embeddings
    )

    # Get all documents (this might be slow if DB is huge, but we have ~72 chunks)
    # Chroma's get() method returns a dict with ids, embeddings, metadatas, documents
    collection_data = vectordb.get()
    
    ids = collection_data['ids']
    metadatas = collection_data['metadatas']
    documents = collection_data['documents']
    
    print(f"\nTotal documents found: {len(ids)}")
    
    if len(ids) == 0:
        print("The database is empty.")
        return

    print("\n--- Sample Documents ---")
    # Print first 5 documents
    for i in range(min(5, len(ids))):
        print(f"\nDocument {i+1}:")
        print(f"ID: {ids[i]}")
        print(f"Metadata: {metadatas[i]}")
        print(f"Content Preview: {documents[i][:200]}...")
        print("-" * 50)

    # List unique sources
    sources = set()
    for meta in metadatas:
        if meta and 'source' in meta:
            sources.add(meta['source'])
            
    print("\n--- Unique Sources ---")
    for source in sources:
        print(f"- {source}")

if __name__ == "__main__":
    inspect_knowledge_base()
