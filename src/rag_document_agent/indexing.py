import os
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from rag_document_agent import config

def get_embeddings():
    """Initialize local HuggingFace embeddings to eliminate API rate limits."""
    return HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)

def create_index(documents: List[Document]) -> FAISS:
    """Create a FAISS vector index from documents using local embeddings."""
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )
        chunks = splitter.split_documents(documents)

        # This now runs entirely on your local CPU - no API calls, no 429 errors
        vector_store = FAISS.from_documents(chunks, get_embeddings())
        vector_store.save_local(config.VECTOR_STORE_PATH)
        return vector_store
    except Exception as e:
        print(f"Error during create_index: {e}")
        import traceback
        traceback.print_exc()
        raise e

def load_index() -> FAISS:
    """Load the FAISS vector index from local storage."""
    if not os.path.exists(config.VECTOR_STORE_PATH):
        raise FileNotFoundError("Vector store index not found. Please process documents first.")

    return FAISS.load_local(
        config.VECTOR_STORE_PATH,
        get_embeddings(),
        allow_dangerous_deserialization=True
    )
