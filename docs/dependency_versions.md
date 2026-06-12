# Dependency Version Check

Checked locally on 2026-06-10 after installing project requirements.

| Package | Installed version |
| --- | --- |
| langchain | 0.3.30 |
| langchain-core | 0.3.86 |
| langchain-community | 0.3.31 |
| langgraph | 0.6.11 |
| openai | 2.41.1 |
| pinecone | 7.3.0 |

These versions are new enough for the project direction:

- LangChain can support the later app/RAG orchestration layer.
- LangGraph now supports the app workflow: safety check, retrieval, confidence check, grounded answer, and escalation.
- OpenAI provides the 512-dimensional `text-embedding-3-small` embeddings used for the Pinecone index.
- Pinecone stores the dense RAG index used by `src/pinecone_hybrid.py`.
