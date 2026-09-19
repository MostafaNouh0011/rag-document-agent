from rag_document_agent.indexing import create_index, get_embeddings
from langchain_core.documents import Document

def test():
    try:
        docs = [Document(page_content="Test content", metadata={"source": "test.txt"})]
        print("Creating index...")
        create_index(docs)
        print("Index created successfully!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
