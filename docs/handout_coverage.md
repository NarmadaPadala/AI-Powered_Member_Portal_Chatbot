# Project Handout Coverage Check

## Handout Requirement

Build a customer support bot that combines keyword search and semantic search over support tickets, FAQs, and product manuals. Implement confidence-based fallback so the system escalates to a human rather than hallucinating. Test with 20 real-world-style support queries and measure first-contact resolution rate.

## Our Project Mapping

- Customer support bot: healthcare member support assistant inside a mock secure member portal.
- Keyword search: lexical reranking over Pinecone semantic candidates; local evaluation uses token overlap and typo-tolerant fuzzy matching.
- Semantic search: OpenAI `text-embedding-3-small` vectors stored in Pinecone.
- Hybrid retrieval: `src/pinecone_hybrid.py` combines Pinecone semantic search with keyword reranking and alpha weighting.
- Workflow framework: `src/assistant_graph.py` uses LangGraph to orchestrate safety check, retrieval, confidence check, grounded answer, and escalation.
- Support tickets: `data/support_tickets.csv`.
- FAQs: `data/faqs.csv`.
- Product manuals: healthcare plan and benefit documents in `data/plans.csv`, `data/benefits.csv`, and Pinecone chunks in `data/kb_documents.jsonl`.
- Confidence fallback: low retrieval confidence routes to Member Services instead of guessing.
- Safety fallback: emergency and medical-advice queries route to 911/clinician guidance.
- 20 real-world-style support queries: `data/evaluation_queries.csv`.
- Resolution metrics: `scripts/evaluate_retrieval.py` writes `docs/evaluation_metrics.md`.

## No-PHI Product Safety

This project uses mock data only:

- No real member IDs.
- No real claims.
- No real provider contracts.
- No real phone numbers.
- Masked demo member IDs only.
- Demo email addresses only.

The chatbot should run inside a logged-in portal in the product story, so the user does not type sensitive identifiers into chat.

## Deployment Readiness Notes

- Keep `.env` out of GitHub.
- Store `PINECONE_API_KEY` as a deployment secret.
- Keep all demo data synthetic.
- Keep evaluation, source, and fallback implementation details in project documentation or admin views, not the member-facing UI.
- Do not let chat directly update profile data; route profile updates to secure workflows.
