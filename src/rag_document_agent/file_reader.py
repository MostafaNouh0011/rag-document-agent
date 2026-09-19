from pathlib import Path
from typing import List
import io

from langchain_core.documents import Document
from pypdf import PdfReader

def extract_text_from_file(uploaded_file) -> Document:
    """Extract text from a supported Streamlit UploadedFile and return a Document."""
    raw_data = uploaded_file.getvalue()
    suffix = uploaded_file.name.rsplit(".", 1)[-1].lower()

    if suffix == "pdf":
        reader = PdfReader(io.BytesIO(raw_data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        text = raw_data.decode("utf-8", errors="replace")

    if not text.strip():
        raise ValueError(f"No readable text was found in {uploaded_file.name}.")

    return Document(page_content=text, metadata={"source": uploaded_file.name})

def process_uploaded_files(uploaded_files) -> List[Document]:
    """Process a list of uploaded files into LangChain Documents."""
    documents = []
    for file in uploaded_files:
        try:
            documents.append(extract_text_from_file(file))
        except Exception as e:
            # In a production app, we might use logging here
            print(f"Error processing {file.name}: {e}")
            continue
    return documents
