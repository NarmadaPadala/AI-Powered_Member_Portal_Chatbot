# Healthcare Member Support Bot

This project is a safe demo version of a healthcare member portal chatbot. A member logs into a portal, then asks benefit, provider, claim, enrollment, dependent, prior authorization, and glossary questions. The retrieval layer uses OpenAI embeddings with Pinecone vector search plus keyword reranking for hybrid retrieval over mock healthcare support data.

## What is included

- Mock members, plans, benefits, providers, claims, FAQs, glossary terms, enrollment rules, prior authorization rules, support tickets, and 20 evaluation questions.
- Pinecone ingestion for dense + sparse vectors in one hybrid index.
- Pinecone hybrid retrieval with alpha weighting.
- Safety routing before retrieval for emergencies, medical advice, and secure account-change workflows.
- Low-confidence fallback path to Member Services.
- LangGraph workflow orchestration for safety check, retrieval, confidence check, grounded answer, and escalation.

## Data files

The data lives in `data/`:

- `members.csv`: mock authenticated portal members.
- `plans.csv`: PPO, HMO, and HDHP plan details.
- `benefits.csv`: copay, deductible, coinsurance, referral, and prior auth rules.
- `providers.csv`: provider directory with network status.
- `claims.csv`: mock processed, denied, and referral-review claims.
- `faqs.csv`: support knowledge base FAQs.
- `glossary.csv`: healthcare terms.
- `enrollment_rules.csv`: open enrollment, qualifying life event, and dependent rules.
- `prior_authorization.csv`: service-level prior authorization rules.
- `support_tickets.csv`: real-world-style historical support tickets.
- `evaluation_queries.csv`: 20 test questions for project metrics.
- `kb_documents.jsonl`: Pinecone-ready retrieval documents.

## Pinecone setup

1. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Create a `.env` file:

```bash
cp .env.demo .env
```

3. Add your OpenAI and Pinecone keys to `.env`:

```bash
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=healthcare-support-rag
```

4. Validate local data:

```bash
python3 scripts/check_data.py
```

5. Create the Pinecone index and ingest the knowledge base:

```bash
python3 scripts/ingest_pinecone.py
```

6. Try a hybrid search query:

```bash
python3 scripts/query_pinecone.py "Is Dr Patell in netwrok?" --member-id M001
```

Other useful test queries:

```bash
python3 scripts/query_pinecone.py "How much deductible do I have left?" --member-id M001
python3 scripts/query_pinecone.py "Do I need pre auto approval for an MRI?" --member-id M001
python3 scripts/query_pinecone.py "Why was my MRI claim denied?" --member-id M001
python3 scripts/query_pinecone.py "Can I change my phone number?" --member-id M001
python3 scripts/query_pinecone.py "I am having chest pain what should I do?" --member-id M001
```

## Evaluation

Run the local hybrid evaluation:

```bash
python3 scripts/evaluate_retrieval.py
```

This writes:

```bash
docs/evaluation_metrics.md
```

Run live Pinecone-backed evaluation after setting `PINECONE_API_KEY` and ingesting the KB:

```bash
python3 scripts/evaluate_retrieval.py --backend pinecone --output docs/evaluation_metrics_pinecone.md
```

## Hybrid search design

The Pinecone index stores 512-dimensional OpenAI `text-embedding-3-small` vectors with cosine similarity.

- Dense vector search: semantic meaning, useful for natural-language questions.
- Keyword reranking: exact and fuzzy lexical matching, useful for names, claim IDs, group IDs, provider names, and insurance terms.
- `alpha`: controls semantic vs keyword weight at query time. The default is `0.55`, a balanced starting point for mixed healthcare support questions.

## Safety and escalation

The assistant should not answer everything directly. The current routing logic escalates:

- Emergencies: tell the user to call `911`.
- Medical advice or diagnosis: route to a licensed clinician.
- Account changes: route to secure form or Member Services verification.
- Low retrieval confidence: route to Member Services at `1-800-555-0198`.

## LangGraph workflow

The chatbot path is orchestrated with LangGraph in `src/assistant_graph.py`:

```text
safety_check -> retrieve -> confidence_check -> grounded_answer
```

When the system should not answer directly, the graph routes to fallback paths:

```text
safety_check -> END
safety_check -> retrieve -> confidence_check -> escalation_answer
```

This makes the real-world support behavior easier to explain and audit.

## Deployment note

This repo is designed to be deployed safely because it uses only mock data. Do not add real PHI, real member IDs, real claims, or real provider contracts. For deployment, set `PINECONE_API_KEY` as a secret in the hosting platform rather than committing it to GitHub.

## Streamlit Community Cloud deployment

Use these settings when creating the Streamlit app:

- Repository: `NarmadaPadala/AI-Powered_Member_Portal_Chatbot`
- Branch: `main`
- Main file path: `app.py`

Add these values in Streamlit Cloud secrets:

```toml
OPENAI_API_KEY = "your-openai-api-key"
PINECONE_API_KEY = "your-pinecone-api-key"
PINECONE_INDEX_NAME = "healthcare-support-rag"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"
PINECONE_NAMESPACE = "demo-healthcare-support"
PINECONE_DIMENSION = "512"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_CHAT_MODEL = "gpt-4.1-mini"
```

## Installed package versions checked

- `langchain`: `0.3.30`
- `langchain-core`: `0.3.86`
- `langchain-community`: `0.3.31`
- `langgraph`: `0.6.11`
- `openai`: `2.41.1`
- `pinecone`: `7.3.0`
