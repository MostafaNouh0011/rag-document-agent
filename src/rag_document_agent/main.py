"""Streamlit interface for asking questions about uploaded documents."""

from __future__ import annotations

import hashlib
import streamlit as st
import traceback
from langchain.messages import HumanMessage

from rag_document_agent.file_reader import process_uploaded_files
from rag_document_agent.indexing import create_index
from rag_document_agent.agent import build_rag_agent
from rag_document_agent import config

def apply_dashboard_theme() -> None:
    """Apply the modern slate and indigo AI SaaS styling."""
    st.markdown(
        """
        <style>
        :root {
            --indigo: #6366f1;
            --indigo-bright: #818cf8;
            --indigo-dark: #4338ca;
            --surface: #0f172a;
            --surface-raised: #1e293b;
            --border: #334155;
            --muted: #94a3b8;
            --text-main: #f8fafc;
        }

        .stApp {
            color: var(--text-main);
            background:
                radial-gradient(circle at 0% 0%, rgba(99, 102, 241, 0.15), transparent 40%),
                radial-gradient(circle at 100% 100%, rgba(79, 70, 229, 0.1), transparent 40%),
                var(--surface);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background: var(--surface-raised);
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label {
            color: var(--muted);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2.2rem;
            padding-bottom: 4rem;
        }

        .rag-hero {
            position: relative;
            overflow: hidden;
            margin-bottom: 1.5rem;
            padding: 1.7rem 2rem;
            border: 1px solid var(--border);
            border-radius: 24px;
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }

        .rag-hero::after {
            content: "";
            position: absolute;
            width: 300px;
            height: 300px;
            right: -100px;
            top: -150px;
            border-radius: 50%;
            background: rgba(99, 102, 241, 0.15);
            filter: blur(40px);
        }

        .rag-eyebrow {
            margin-bottom: .45rem;
            color: var(--indigo-bright);
            font-size: .76rem;
            font-weight: 800;
            letter-spacing: .16em;
            text-transform: uppercase;
        }

        .rag-title {
            margin: 0;
            color: #ffffff;
            font-size: clamp(2rem, 4vw, 3.25rem);
            font-weight: 850;
            letter-spacing: -.045em;
            line-height: 1;
        }

        .rag-title span { color: var(--indigo-bright); }

        .rag-subtitle {
            max-width: 690px;
            margin: .85rem 0 0;
            color: var(--muted);
            font-size: 1rem;
        }

        [data-testid="stFileUploaderDropzone"],
        [data-testid="stChatMessage"],
        div[data-testid="stAlert"] {
            border: 1px solid var(--border);
            border-radius: 16px;
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(4px);
        }

        [data-testid="stChatMessage"] {
            margin-bottom: .7rem;
            padding: .5rem .75rem;
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            border-left: 3px solid var(--indigo);
        }

        .stButton > button[kind="primary"] {
            border: 1px solid var(--indigo-bright);
            background: linear-gradient(135deg, var(--indigo), var(--indigo-dark));
            color: white;
            font-weight: 600;
            box-shadow: 0 8px 20px rgba(99, 102, 241, 0.25);
            border-radius: 12px;
            transition: all 0.2s ease;
        }

        .stButton > button[kind="primary"]:hover {
            border-color: var(--indigo-bright);
            transform: translateY(-1px);
            box-shadow: 0 12px 24px rgba(99, 102, 241, 0.35);
        }

        .stButton > button[kind="secondary"] {
            border-color: var(--border);
            background: var(--surface-raised);
            color: var(--text-main);
            border-radius: 12px;
        }

        [data-testid="stChatInput"] {
            border: 1px solid var(--border);
            border-radius: 16px;
            background: #1e293b;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        [data-testid="stChatInput"]:focus-within {
            border-color: var(--indigo);
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
        }

        [data-testid="stFileUploaderDropzone"] button {
            border-color: var(--border);
            background: var(--surface-raised);
            color: var(--text-main);
        }

        h1, h2, h3 { letter-spacing: -.025em; }
        a { color: var(--indigo-bright) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def file_set_id(uploaded_files) -> str:
    """Return a stable identifier for the currently uploaded file contents."""
    digest = hashlib.sha256()
    for uploaded_file in uploaded_files:
        digest.update(uploaded_file.name.encode("utf-8"))
        digest.update(uploaded_file.getvalue())
    return digest.hexdigest()

def final_text(result: dict) -> str:
    """Extract the last readable model message from an agent result."""
    for message in reversed(result.get("messages", [])):
        text = getattr(message, "text", "")
        if text:
            return text
    return "The agent completed the request but did not return a text response."

def main() -> None:
    st.set_page_config(page_title="Document Q&A", page_icon="📚", layout="wide")
    apply_dashboard_theme()

    st.markdown(
        """
        <section class="rag-hero">
            <div class="rag-eyebrow">AI RAG Agent</div>
            <h1 class="rag-title">Chat with your <span>knowledge</span></h1>
            <p class="rag-subtitle">
                Upload your documents, build a semantic index, and get grounded answers
                from an agent that searches and analyzes before it speaks.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.markdown("### ◈ Knowledge base")
        uploaded_files = st.file_uploader(
            "Upload one or more files",
            type=config.SUPPORTED_EXTENSIONS,
            accept_multiple_files=True,
        )
        process_clicked = st.button(
            "Process documents",
            type="primary",
            disabled=not uploaded_files,
            use_container_width=True,
        )

        if process_clicked:
            try:
                current_file_set = file_set_id(uploaded_files)
                with st.spinner("Analyzing and indexing documents..."):
                    documents = process_uploaded_files(uploaded_files)
                    if not documents:
                        st.error("No readable text could be extracted from the uploaded files. Please check your documents.")
                        # Use a flag to skip the rest of the processing
                        st.session_state.processing_failed = True
                    else:
                        st.session_state.processing_failed = False
                        create_index(documents)
                        agent = build_rag_agent()

                if not st.session_state.get("processing_failed", False):
                    st.session_state.agent = agent
                    st.session_state.file_set_id = current_file_set
                    st.session_state.messages = []
                    st.success(f"Indexed {len(documents)} files successfully.")

            except Exception as exc:
                error_traceback = traceback.format_exc()
                print(error_traceback)
                st.error(f"Could not process the documents: {exc}")
                st.expander("View technical details").code(error_traceback)
                

        if uploaded_files and "file_set_id" in st.session_state:
            if file_set_id(uploaded_files) != st.session_state.file_set_id:
                st.warning("The selected files changed. Process them before asking questions.")

        if st.button("Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input(
        "Ask a question about your documents",
        disabled="agent" not in st.session_state,
    )
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.status("Searching and analyzing your documents...", expanded=True) as status:
                try:
                    result = st.session_state.agent.invoke(
                        {"messages": [HumanMessage(content=question)]}
                    )
                    answer = final_text(result)
                    status.update(label="Analysis complete!", state="complete", expanded=False)
                except Exception as exc:
                    answer = f"I couldn't answer that question: {exc}"
                    status.update(label="Analysis failed", state="error", expanded=True)
            st.markdown(answer)


        st.session_state.messages.append({"role": "assistant", "content": answer})

    if "agent" not in st.session_state:
        st.info("Upload and process at least one document to begin.")

if __name__ == "__main__":
    main()
