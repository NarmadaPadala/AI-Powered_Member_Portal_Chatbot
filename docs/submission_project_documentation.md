# AI-Powered Member Portal Chatbot - Project Documentation

## Project Overview

This project is a healthcare member support chatbot built as a real-world style member portal experience. The idea is that a member logs into a secure portal and asks natural-language questions instead of searching across plan pages, benefit tables, provider directories, claim details, and support FAQs.

The assistant, CareGuide, can answer questions about plan status, group ID, deductible, copay, provider network status, MRI coverage, prior authorization, claim denial reasons, dependent access, enrollment rules, forms, and healthcare glossary terms. It also includes safety behavior for situations where the chatbot should not answer directly, such as medical emergencies, medical advice, profile changes, claim payment guarantees, inactive coverage cost estimates, or low-confidence retrieval.

The project was built for the Week 2 customer support knowledge base assignment. The handout asked for a support bot using hybrid retrieval over support tickets, FAQs, and product manuals, plus a confidence-based fallback that escalates instead of hallucinating. I adapted that into a healthcare member portal use case because healthcare support is a high-trust domain where incorrect answers can create member confusion and risk.

## What I Built

- A Streamlit member portal UI called Member Coverage Details.
- An Ask CareGuide chatbot embedded in the portal.
- Mock healthcare member, plan, provider, claim, benefit, FAQ, support ticket, enrollment, prior authorization, and glossary data.
- A Pinecone-backed vector database using OpenAI embeddings.
- Hybrid retrieval that combines semantic search with keyword and fuzzy reranking.
- A LangGraph workflow that routes questions through safety checks, retrieval, confidence checks, answer generation, and escalation.
- A confidence-based fallback to Member Services when the system should not answer.
- Evaluation over 20 real-world-style healthcare support queries.
- Deployment preparation for Streamlit Community Cloud using secrets instead of committed API keys.

## Datasets Used

All data is synthetic and safe for public demo use. The project does not include real PHI, real member IDs, real claims, or real provider contracts.

| Dataset | File | Purpose |
| --- | --- | --- |
| Members | `data/members.csv` | Mock logged-in member profiles with plan, status, group ID, PCP, deductible, out-of-pocket balance, and dependents. |
| Plans | `data/plans.csv` | Mock plan manuals for PPO, HMO, and HDHP plans. |
| Benefits | `data/benefits.csv` | Service-level cost shares such as copays, coinsurance, deductible rules, and prior authorization flags. |
| Providers | `data/providers.csv` | Provider directory with specialty, network, and accepting-new-patient information. |
| Claims | `data/claims.csv` | Mock processed and denied claims, including denial reasons and next-step guidance. |
| FAQs | `data/faqs.csv` | Customer support FAQ-style content for benefits, claims, profile updates, and portal help. |
| Support Tickets | `data/support_tickets.csv` | Real-world-style historical support ticket examples. |
| Enrollment Rules | `data/enrollment_rules.csv` | Open enrollment, special event, and dependent enrollment logic. |
| Prior Authorization | `data/prior_authorization.csv` | Services that require approval before care. |
| Glossary | `data/glossary.csv` | Healthcare terms such as deductible, copay, coinsurance, group ID, and prior authorization. |
| Retrieval Documents | `data/kb_documents.jsonl` | Pinecone-ready chunks combining member, plan, benefit, provider, claim, FAQ, and glossary content. |
| Evaluation Queries | `data/evaluation_queries.csv` | 20 test questions used to measure retrieval and safe escalation behavior. |

## Architecture

The app flow is:

```text
Streamlit UI
-> LangGraph workflow
-> safety check
-> OpenAI embedding
-> Pinecone vector retrieval
-> keyword and fuzzy reranking
-> confidence check
-> grounded answer or escalation
```

The main frameworks and services are:

- Streamlit for the member-facing app.
- OpenAI `text-embedding-3-small` for embeddings.
- OpenAI `gpt-4.1-mini` for grounded answer generation.
- Pinecone for vector database retrieval.
- LangGraph for workflow orchestration.
- Python dotenv locally and Streamlit secrets in deployment.

The graph has two main paths:

```text
safety_check -> retrieve -> confidence_check -> grounded_answer
```

and:

```text
safety_check -> END
safety_check -> retrieve -> confidence_check -> escalation_answer
```

This structure makes the system easier to explain in an interview because the chatbot is not just a single prompt. It has a workflow that decides whether to answer, retrieve, or escalate.

## Hybrid Retrieval Design

The retrieval design combines semantic and keyword behavior:

- Semantic retrieval helps when the user asks natural-language questions, such as "Does my plan cover MRI services?"
- Keyword matching helps with exact healthcare terms, provider names, claim terms, group IDs, and service categories.
- Fuzzy matching helps with spelling mistakes, such as "innetwrok" or "Dr Patell."
- Confidence scoring decides whether the assistant should answer or route the user to Member Services.

This matters because member support questions often mix natural language, insurance terms, names, and typos. Semantic search alone may miss exact identifiers, while keyword search alone may miss paraphrased questions. Hybrid retrieval gives better coverage for both.

## Safety and Escalation Design

The assistant does not answer every question directly. It routes high-risk or workflow-sensitive questions away from normal RAG answering.

Examples:

- Emergency symptoms: tell the user to call 911 or go to the nearest emergency room.
- Medical diagnosis or treatment advice: route to a licensed clinician.
- Profile changes such as phone, email, or address updates: route to a secure workflow.
- Claim payment guarantees: explain that final payment depends on eligibility, benefits, policy, billing, and review.
- Inactive coverage cost estimates: do not estimate current benefits.
- Low-confidence retrieval: route to Member Services.
- Casual acknowledgments such as "Cool": respond conversationally without exposing member details.

This was one of the most important product decisions because healthcare chatbots must be careful not to over-answer.

## Prompts Used During Vibe Coding

The project was built through iterative prompting and refinement. Some representative prompts and prompt themes were:

- "Let's brainstorm a healthcare app before we build code. A user logs into a portal and asks questions about benefits, insurance, PCP network status, copay, deductible, and claims."
- "Does this app idea satisfy the project handout for a customer support knowledge base with hybrid search?"
- "Let's start with data creation for members, embeddings, loading into Pinecone vector DB, and retrieval with hybrid search."
- "Run it through proper evaluation, hybrid retrieval, and check LangGraph and LangChain versions."
- "Make sure we need to have a real-world product with no PHI data."
- "Make the UI more readable and realistic like a real healthcare portal."
- "Remove backend information from the member-facing screen."
- "Should we keep evaluation in the real-world app UI or only in documentation?"
- "If I type 'Cool,' it should not answer with member coverage details."
- "Remove the separate Next Step block and keep escalation guidance inside the answer."
- "Check the final version before pushing to GitHub."
- "Prepare the app for Streamlit Community Cloud and make sure API keys are secrets."

These prompts helped move the project from a generic RAG assignment into a more realistic healthcare product prototype.

## Iterations Tried

| Iteration | What changed | Why it mattered |
| --- | --- | --- |
| Initial scope | Started from the assignment: customer support bot with hybrid search and fallback. | Established the required project goals. |
| Healthcare framing | Reframed the support bot as a healthcare member portal assistant. | Made the project more domain-specific and interview-friendly. |
| Synthetic data creation | Built mock members, claims, benefits, providers, FAQs, tickets, glossary, and plan rules. | Avoided PHI while still creating a realistic dataset. |
| Pinecone ingestion | Loaded 32 retrieval documents into Pinecone. | Created the semantic retrieval layer. |
| Hybrid retrieval | Added keyword and fuzzy reranking on top of semantic search. | Improved handling of exact terms, names, and spelling mistakes. |
| LangGraph workflow | Added graph routing for safety, retrieval, confidence, answering, and escalation. | Made the system easier to audit and explain. |
| Safety guardrails | Added emergency, medical advice, secure workflow, guarantee, inactive coverage, and small-talk handling. | Reduced hallucination and unsafe over-answering. |
| UI refinement | Removed internal source/confidence/evaluation details from member view. | Made the UI feel like a real healthcare portal instead of a developer demo. |
| Chat wording cleanup | Removed separate "Next Step" UI block and kept guidance inside the answer. | Made responses feel more natural and less like backend workflow output. |
| Deployment prep | Added Streamlit secrets support and pushed the repo to GitHub. | Made the project ready for Streamlit Community Cloud without exposing API keys. |

## Evaluation Results

The live Pinecone-backed evaluation tested 20 real-world-style support questions.

- Total queries: 20
- Resolved correctly: 20
- Incorrect or mismatched: 0
- Escalated or routed to workflow: 6
- First-contact resolution rate: 100%
- Hallucination count: 0, because unsupported or high-risk questions route to fallback instead of fabricated answers.

Example evaluation questions included:

- "Is my plan active?"
- "What is my group ID?"
- "How much deductible do I have left?"
- "What is my copay for urgent care?"
- "Is Dr Patell in netwrok?"
- "Do I need pre auto approval for an MRI?"
- "Why was my MRI claim denied?"
- "Can I change my phone number?"
- "Can I access my dependent's account?"
- "I am having chest pain what should I do?"
- "Can you guarantee this claim will be paid?"

The detailed metrics are stored in `docs/evaluation_metrics_pinecone.md`.

## Learnings and Observations

One major learning is that a healthcare support chatbot needs more than a good answer prompt. The workflow around the model is just as important as the model itself. Safety routing, retrieval confidence, member context, and escalation rules all shape whether the assistant feels trustworthy.

Another observation is that hybrid retrieval is very useful for healthcare support. Members may ask natural-language questions, but they also use exact terms like copay, deductible, group ID, PCP, MRI, referral, claim denied, and in network. They also make spelling mistakes. Combining semantic search with keyword and fuzzy reranking made the assistant more reliable.

The UI also changed the product quality. Early versions exposed too much technical information, such as source details and evaluation behavior. In a real member portal, those details belong in internal documentation, not in the member-facing chatbot. Removing backend information made the app feel more realistic.

Small-talk handling was an important edge case. When the user typed "Cool," the assistant originally answered with unrelated member coverage details because retrieval still ran. Adding a small-talk guardrail prevented unnecessary exposure of member information and made the chatbot behavior safer.

The project also reinforced the importance of secrets management. API keys should never be committed to GitHub. The final app reads local credentials from `.env` and deployment credentials from Streamlit Cloud secrets.

## Final Deliverables

- GitHub repository: `NarmadaPadala/AI-Powered_Member_Portal_Chatbot`
- Streamlit app: member portal UI with Ask CareGuide chatbot
- Pinecone-backed hybrid retrieval
- LangGraph safety and answer workflow
- Synthetic healthcare knowledge base
- Evaluation metrics document with 20 tested queries
- Deployment-ready configuration for Streamlit Community Cloud

## Future Improvements

- Add authenticated login instead of the current demo member selector.
- Add a secure profile update workflow instead of only explaining the next step.
- Add admin-only evaluation dashboards.
- Add audit logging for escalated conversations.
- Add provider search filters by location, specialty, accepting-new-patient status, and network.
- Add claim detail drilldowns with clearer explanation of denial codes and appeal steps.
- Add automated regression tests for safety and retrieval behavior.
