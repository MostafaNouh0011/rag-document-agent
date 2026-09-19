import time
from typing import Any, Optional
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from rag_document_agent.prompts import RAG_WORKFLOW_INSTRUCTIONS, SUBAGENT_DELEGATION_INSTRUCTIONS, CHUNK_ANALYST_INSTRUCTIONS
from rag_document_agent.tools import search_documentation, backend
from rag_document_agent import config


def build_rag_agent():
    """Build and return the RAG coordinator agent with its sub-agents."""

    # Combine instructions
    instructions = (
        RAG_WORKFLOW_INSTRUCTIONS
        + "\n\n"
        + SUBAGENT_DELEGATION_INSTRUCTIONS.format(
            max_concurrent_analysts=config.MAX_CONCURRENT_ANALYSTS
        )
    )

    # Sub-agent definition
    analyst = {
        "name": "chunk-analyst",
        "description": "Analyze one retrieved document chunk for the user's question.",
        "system_prompt": CHUNK_ANALYST_INSTRUCTIONS,
    }

    # Create the coordinator agent
    agent = create_deep_agent(
        model=config.LLM_MODEL,
        tools=[search_documentation],
        backend=backend,
        system_prompt=instructions,
        subagents=[analyst],
    )

    # Wrap the agent's invoke method to handle rate limits (429) with exponential backoff
    original_invoke = agent.invoke

    def invoke_with_retry(*args, **kwargs):
        max_retries = 5
        base_delay = 2  # seconds
        for attempt in range(max_retries):
            try:
                return original_invoke(*args, **kwargs)
            except Exception as e:
                error_msg = str(e).upper()
                if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg) and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Rate limit hit. Retrying in {delay}s... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    raise e
        raise Exception("Max retries exceeded")

    agent.invoke = invoke_with_retry
    return agent

