# CareGuide Benefits Assistant

## Project Overview

CareGuide Benefits Assistant is a healthcare member support chatbot built as a real-world style member portal experience. A member can ask questions about coverage, benefits, providers, claims, dependents, account support, prior authorization, and healthcare glossary terms.

The app uses only synthetic data. It does not use real PHI, real member IDs, real claims, or real provider contracts.

## User-Facing App

The member-facing Streamlit app includes:

- Member Coverage Details
- Member status, plan, group ID, PCP, deductible, and out-of-pocket summary
- Header navigation for Find Care, Benefits, Claims, and Forms
- Ask CareGuide AI chatbot
- Plan Details tab with common benefits and recent claims

The evaluation metrics are intentionally not shown in the member-facing UI. In a real healthcare portal, evaluation details belong in internal documentation, QA reports, or admin dashboards.

## Architecture

```text
Streamlit UI
-> LangGraph workflow
-> safety check
-> OpenAI embedding
-> Pinecone vector retrieval
-> keyword/fuzzy reranking
-> confidence check
-> grounded answer or escalation
```

## Frameworks And Services

- Streamlit: member portal UI
- OpenAI: `text-embedding-3-small` embeddings and `gpt-4.1-mini` answer generation
- Pinecone: vector database for the RAG index
- LangGraph: workflow orchestration
- Python dotenv: local environment configuration

## LangGraph Workflow

```text
safety_check -> retrieve -> confidence_check -> grounded_answer
```

Fallback paths:

```text
safety_check -> END
confidence_check -> escalation_answer
```

This graph makes the assistant behavior easier to explain and audit.

## Retrieval

The retrieval design combines:

- Semantic search using OpenAI embeddings stored in Pinecone
- Keyword and fuzzy reranking for exact healthcare terms, names, claims, group ID, and typo handling
- Confidence-based fallback when retrieval is uncertain

## Safety Behavior

The assistant escalates instead of answering directly for:

- Medical emergencies
- Medical diagnosis or treatment advice
- Account/profile updates
- Claim payment guarantees
- Inactive coverage cost estimates
- Low-confidence retrieval results

## Evaluation Summary

Live Pinecone retrieval evaluation:

- Total queries: 20
- Resolved correctly: 20
- Incorrect or mismatched: 0
- First-contact resolution rate: 100%
- Hallucination count: 0
- Escalated or routed safely: 6

Detailed metrics are stored in:

```text
docs/evaluation_metrics_pinecone.md
```

## Healthcare UI Direction

The UI is intentionally restrained and readable:

- Clear member coverage summary
- Minimal background text
- Blue healthcare-oriented accent color
- White cards with light borders
- No technical retrieval or evaluation details in the member view
- Member Services visible for support fallback
