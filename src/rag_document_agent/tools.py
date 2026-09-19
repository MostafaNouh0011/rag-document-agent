import uuid
from deepagents.backends import StateBackend
from langchain.tools import tool
from rag_document_agent.indexing import load_index
from rag_document_agent import config

# Shared backend for the agent to manage files
backend = StateBackend()

@tool(parse_docstring=True)
def search_documentation(query: str) -> str:
    """Search the uploaded knowledge base and save matching chunks to the agent filesystem.

    Args:
        query: Natural-language search query.

    Returns:
        File paths where retrieved chunks were saved under /retrieved/.
    """
    try:
        vector_store = load_index()
    except Exception as e:
        return f"Error loading index: {e}. Please upload documents first."

    # Retrieve top K documents
    retrieved_docs = vector_store.similarity_search(query, k=config.RETRIEVAL_K)

    batch_id = uuid.uuid4().hex[:8]
    uploads: list[tuple[str, bytes]] = []
    saved_paths: list[str] = []

    for index, doc in enumerate(retrieved_docs, start=1):
        path = f"/retrieved/{batch_id}/chunk_{index}.md"
        content = (
            f"# Source: {doc.metadata.get('source', 'unknown')}\n\n"
            f"{doc.page_content}"
        )
        uploads.append((path, content.encode("utf-8")))
        saved_paths.append(path)

    backend.upload_files(uploads)
    return f"Saved {len(saved_paths)} document chunks:\n" + "\n".join(saved_paths)
