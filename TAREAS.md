1. [x] actualizar la ui para usar componentes de 
https://www.heroui.com/docs/frameworks/nextjs
estudia a profundidad la documentacion para implementarlo 

2. usa este ejemplo para hacer el retrival: (nosotros manejaremos .md

)
```
"""
PDF Document Ingestion Script for DeepSeek R1 Distill RAG System

This module handles the preprocessing and ingestion of PDF documents into a vector
database for the RAG (Retrieval Augmented Generation) system. It performs the
following key operations:

1. **Document Loading**: Recursively loads all PDF files from the data directory
2. **Text Splitting**: Breaks documents into manageable chunks with overlap
3. **Embedding Generation**: Converts text chunks into vector embeddings
4. **Vector Store Creation**: Stores embeddings in ChromaDB for fast similarity search

The resulting vector database enables semantic search over document content,
allowing the RAG system to retrieve relevant context for user queries.

Technical Details:
- Uses LangChain for document processing pipeline
- HuggingFace sentence-transformers for embeddings (all-mpnet-base-v2)
- ChromaDB as the vector database backend
- Configurable chunk size and overlap for optimal retrieval

Author: AI-CIS Project
Dependencies: langchain, chromadb, sentence-transformers, PyPDF2
"""

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import os
import shutil

# Load environment variables from .env file
load_dotenv()

def load_and_process_pdfs(data_dir: str):
    """
    Load all PDF files from a directory and split them into text chunks.
    
    This function performs the first stage of the document ingestion pipeline:
    1. Recursively searches for PDF files in the specified directory
    2. Loads and extracts text content from each PDF
    3. Splits the extracted text into smaller, manageable chunks
    
    The chunking strategy uses recursive character splitting with overlap to:
    - Ensure chunks fit within model context windows
    - Maintain semantic coherence across chunk boundaries
    - Provide context overlap for better retrieval accuracy
    
    Args:
        data_dir (str): Path to the directory containing PDF files
        
    Returns:
        list: List of Document objects containing text chunks with metadata
        
    Chunking Configuration:
        - chunk_size=1000: Maximum characters per chunk (balance between context and speed)
        - chunk_overlap=200: Characters shared between adjacent chunks (maintains context)
        - length_function=len: Uses character count for chunk size measurement
    """
    # Initialize directory loader to find all PDF files recursively
    loader = DirectoryLoader(
        data_dir,
        glob="**/*.pdf",  # Recursive pattern to find PDFs in subdirectories
        loader_cls=PyPDFLoader  # Specific loader for PDF files
    )
    
    # Load all PDF documents and extract text content
    print(f"Loading PDF files from: {data_dir}")
    documents = loader.load()
    print(f"Loaded {len(documents)} document pages")
    
    # Configure text splitter for optimal chunk creation
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # Target size per chunk (characters)
        chunk_overlap=200,    # Overlap between chunks (preserves context)
        length_function=len,  # Function to measure chunk length
    )
    
    # Split all documents into chunks
    print("Splitting documents into chunks...")
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} text chunks")
    
    return chunks

def create_vector_store(chunks, persist_directory: str):
    """
    Create a ChromaDB vector store from document chunks and persist it to disk.
    
    This function performs the second stage of the document ingestion pipeline:
    1. Clears any existing vector database to ensure fresh start
    2. Initializes HuggingFace embeddings model for text vectorization
    3. Converts text chunks into high-dimensional vector embeddings
    4. Creates and persists a ChromaDB vector store for fast similarity search
    
    The embedding model (all-mpnet-base-v2) is specifically chosen for:
    - High-quality semantic representations
    - Good performance on diverse text types
    - Balanced trade-off between accuracy and speed
    - CPU-friendly inference (no GPU required)
    
    Args:
        chunks (list): List of Document objects containing text chunks
        persist_directory (str): Directory path where vector store will be saved
        
    Returns:
        Chroma: The created ChromaDB vector store instance
        
    Vector Store Features:
        - Semantic similarity search using cosine distance
        - Persistent storage for reuse across sessions
        - Metadata preservation for source document tracking
        - Efficient indexing with HNSW algorithm
    """
    # Clear existing vector store to prevent conflicts and ensure fresh data
    if os.path.exists(persist_directory):
        print(f"Clearing existing vector store at {persist_directory}")
        shutil.rmtree(persist_directory)
        print("Existing vector store cleared")
    
    # Initialize HuggingFace embeddings model
    print("Initializing embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",  # High-quality general-purpose model
        model_kwargs={'device': 'cpu'}  # Use CPU for broader compatibility
    )
    print("Embedding model loaded successfully")
    
    # Create ChromaDB vector store from document chunks
    print("Creating vector embeddings and building database...")
    print(f"Processing {len(chunks)} chunks...")
    
    vectordb = Chroma.from_documents(
        documents=chunks,           # Text chunks to embed
        embedding=embeddings,       # Embedding function
        persist_directory=persist_directory  # Where to save the database
    )
    
    print(f"Vector store created with {len(chunks)} embeddings")
    print(f"Database persisted to: {persist_directory}")
    
    return vectordb

def main():
    """
    Main function that orchestrates the complete PDF ingestion pipeline.
    
    This function coordinates the entire document processing workflow:
    1. Sets up directory paths for input PDFs and output vector database
    2. Loads and processes PDF documents into text chunks
    3. Creates a vector database for semantic search
    4. Provides progress feedback and completion status
    
    Directory Structure:
        - data/: Contains input PDF files (any subdirectory structure)
        - chroma_db/: Output directory for the vector database
    
    Prerequisites:
        - PDF files must be placed in the 'data' directory
        - Sufficient disk space for vector database storage
        - Internet connection for downloading embedding model (first run only)
        
    Post-Processing:
        - Vector database is ready for use by the RAG system
        - Database persists across sessions and can be reused
        - Re-running this script will recreate the database from scratch
    """
    # Define input and output directories relative to script location
    script_dir = os.path.dirname(__file__)
    data_dir = os.path.join(script_dir, "data")
    db_dir = os.path.join(script_dir, "chroma_db")
    
    print("=" * 60)
    print("PDF INGESTION PIPELINE FOR DEEPSEEK R1 RAG SYSTEM")
    print("=" * 60)
    print(f"Input directory: {data_dir}")
    print(f"Output directory: {db_dir}")
    print()
    
    # Validate that the data directory exists and contains files
    if not os.path.exists(data_dir):
        print(f"Error: Data directory '{data_dir}' does not exist!")
        print("Please create the directory and add PDF files before running this script.")
        return
    
    pdf_files = [f for f in os.listdir(data_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"Warning: No PDF files found in '{data_dir}'")
        print("Please add PDF files to the data directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file}")
    print()
    
    # Stage 1: Load and process PDFs into chunks
    print("STAGE 1: Loading and processing PDFs...")
    print("-" * 40)
    chunks = load_and_process_pdfs(data_dir)
    print(f"✅ Successfully created {len(chunks)} text chunks")
    print()
    
    # Stage 2: Create vector database
    print("STAGE 2: Creating vector database...")
    print("-" * 40)
    vectordb = create_vector_store(chunks, db_dir)
    print("✅ Vector database created and persisted successfully")
    print()
    
    # Completion summary
    print("=" * 60)
    print("INGESTION PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📊 Documents processed: {len(pdf_files)} PDF files")
    print(f"📝 Text chunks created: {len(chunks)} chunks")
    print(f"💾 Vector database location: {db_dir}")
    print()
    print("🚀 The RAG system is now ready to use!")
    print("   Run 'python r1_smolagent_rag.py' to start the Gradio interface")
    print("   Or run 'streamlit run streamlit.py' for the Streamlit interface")
    print("=" * 60)

if __name__ == "__main__":
    """
    Entry point for the PDF ingestion script.
    
    This script should be run before using the RAG system to prepare the
    document database. It only needs to be run once, or when documents
    are added/changed.
    
    Usage:
        python ingest_pdfs.py
        
    Prerequisites:
        1. Install dependencies: pip install -r requirements.txt
        2. Place PDF files in the 'data' directory
        3. Ensure sufficient disk space for vector database
        
    Output:
        - Creates 'chroma_db' directory with vector database
        - Database contains embeddings for all PDF content
        - Ready for use by r1_smolagent_rag.py or streamlit.py
        
    Performance Notes:
        - Processing time depends on number and size of PDFs
        - First run downloads embedding model (~400MB)
        - Subsequent runs reuse cached model
        - Vector database size ~1-5MB per PDF page
    """
    main()
```

2.a

```
from smolagents import OpenAIServerModel, CodeAgent, ToolCallingAgent, HfApiModel, tool, GradioUI
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os

load_dotenv()

reasoning_model_id = os.getenv("REASONING_MODEL_ID")
tool_model_id = os.getenv("TOOL_MODEL_ID")
huggingface_api_token = os.getenv("HUGGINGFACE_API_TOKEN")

def get_model(model_id):
    using_huggingface = os.getenv("USE_HUGGINGFACE", "yes").lower() == "yes"
    if using_huggingface:
        return HfApiModel(model_id=model_id, token=huggingface_api_token)
    else:
        return OpenAIServerModel(
            model_id=model_id,
            api_base="http://localhost:11434/v1",
            api_key="ollama"
        )

# Create the reasoner for better RAG
reasoning_model = get_model(reasoning_model_id)
reasoner = CodeAgent(tools=[], model=reasoning_model, add_base_tools=False, max_steps=2)

# Initialize vector store and embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2",
    model_kwargs={'device': 'cpu'}
)
db_dir = os.path.join(os.path.dirname(__file__), "chroma_db")
vectordb = Chroma(persist_directory=db_dir, embedding_function=embeddings)

@tool
def rag_with_reasoner(user_query: str) -> str:
    """
    This is a RAG tool that takes in a user query and searches for relevant content from the vector database.
    The result of the search is given to a reasoning LLM to generate a response, so what you'll get back
    from this tool is a short answer to the user's question based on RAG context.

    Args:
        user_query: The user's question to query the vector database with.
    """
    # Search for relevant documents
    docs = vectordb.similarity_search(user_query, k=3)
    
    # Combine document contents
    context = "\n\n".join(doc.page_content for doc in docs)
    
    # Create prompt with context
    prompt = f"""Based on the following context, answer the user's question. Be concise and specific.
    If there isn't sufficient information, give as your answer a better query to perform RAG with.
    
Context:
{context}

Question: {user_query}

Answer:"""
    
    # Get response from reasoning model
    response = reasoner.run(prompt, reset=False)
    return response

# Create the primary agent to direct the conversation
tool_model = get_model(tool_model_id)
primary_agent = ToolCallingAgent(tools=[rag_with_reasoner], model=tool_model, add_base_tools=False, max_steps=3)

# Example prompt: Compare and contrast the services offered by RankBoost and Omni Marketing
def main():
    GradioUI(primary_agent).launch()

if __name__ == "__main__":
    main()
```