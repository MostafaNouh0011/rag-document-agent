import os
from dotenv import load_dotenv

load_dotenv()

# Model Configurations
# Using HuggingFace local embeddings to avoid API rate limits (Option 2)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "groq:openai/gpt-oss-120b"  # Trying Llama 3.1 70B which is widely available


# RAG Settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVAL_K = 4
MAX_CONCURRENT_ANALYSTS = 3

# Storage
VECTOR_STORE_PATH = "faiss_index_local"

# File settings
SUPPORTED_EXTENSIONS = ["pdf", "txt", "md"]
