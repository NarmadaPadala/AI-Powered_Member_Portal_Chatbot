from openai import OpenAI
from typing import Optional

from src.documents import load_kb_documents
from src.local_hybrid import local_hybrid_search
from src.safety import classify_query
from src.settings import Settings


MEMBER_SERVICES_PHONE = "1-800-555-0198"


def inactive_cost_guardrail(member: dict, question: str) -> Optional[str]:
    if member.get("status") != "Inactive":
        return None
    normalized = question.lower()
    if any(term in normalized for term in ["cost", "pay", "copay", "estimate", "covered"]):
        return (
            "I cannot estimate current benefits because this sample member's coverage is "
            "inactive. Please contact Member Services if the coverage status looks incorrect."
        )
    return None


def fallback_answer(
    question: str,
    matches: list[dict],
    member: dict,
    plan: Optional[dict] = None,
) -> str:
    if not matches:
        return (
            "I am not confident enough to answer that accurately. Please contact "
            f"Member Services at {MEMBER_SERVICES_PHONE}."
        )

    top = matches[0]["metadata"]
    text = top.get("text", "")
    source_type = top.get("source_type", "source")
    normalized = question.lower()

    if source_type == "member_profile" and "group id" in normalized:
        return f"Your group ID is {member.get('group_id')}."
    if source_type == "member_profile" and "deductible" in normalized:
        deductible_met = float(member.get("deductible_met", 0))
        deductible_total = float((plan or {}).get("deductible_individual", 0) or 0)
        remaining = max(deductible_total - deductible_met, 0)
        return (
            f"You have ${remaining:,.0f} left toward your individual deductible. "
            f"You have met ${deductible_met:,.0f} so far."
        )
    if source_type == "member_profile" and "active" in normalized:
        return f"Your plan status is {member.get('status')}."
    if source_type == "claims":
        return (
            f"Based on the claim information I found: {text} For claim-specific disputes, "
            f"contact Member Services at {MEMBER_SERVICES_PHONE}."
        )
    if source_type == "eligibility":
        return f"Based on the eligibility rules: {text}"
    if source_type == "provider_directory":
        return f"Based on the provider directory: {text}"

    return f"Based on your plan information: {text}"


def offline_answer_question(question: str, member: dict, plan: dict) -> dict:
    safety = classify_query(question)
    if safety.route != "retrieval":
        return {
            "answer": safety.message or "",
            "route": safety.route,
            "confidence": 1.0,
            "matches": [],
            "escalated": safety.route != "small_talk",
            "graph_trace": ["offline_safety_check"],
        }

    inactive_message = inactive_cost_guardrail(member, question)
    if inactive_message:
        return {
            "answer": inactive_message,
            "route": "inactive_coverage",
            "confidence": 1.0,
            "matches": [],
            "escalated": True,
            "graph_trace": ["offline_safety_check"],
        }

    matches = local_hybrid_search(
        query=question,
        documents=load_kb_documents(),
        member_id=member["member_id"],
        plan_id=member["plan_id"],
        top_k=5,
    )
    best_score = matches[0]["score"] if matches else 0
    if best_score < 0.2:
        return {
            "answer": (
                "I am not confident enough to answer that accurately. Please contact "
                f"Member Services at {MEMBER_SERVICES_PHONE}."
            ),
            "route": "offline_low_confidence",
            "confidence": best_score,
            "matches": matches,
            "escalated": True,
            "graph_trace": ["offline_retrieve", "offline_confidence_check"],
        }

    return {
        "answer": fallback_answer(question, matches, member, plan),
        "route": "offline_answered",
        "confidence": best_score,
        "matches": matches,
        "escalated": False,
        "graph_trace": ["offline_retrieve", "offline_grounded_answer"],
    }


def generate_grounded_answer(
    question: str,
    member: dict,
    plan: dict,
    settings: Settings,
    top_matches: list[dict],
) -> str:
    context = "\n\n".join(
        f"Source: {match['metadata'].get('source_type')}\n"
        f"Title: {match['metadata'].get('title')}\n"
        f"Text: {match['metadata'].get('text')}"
        for match in top_matches[:4]
    )

    prompt = (
        "You are CareGuide, a healthcare insurance member support assistant inside a "
        "secure demo portal. Answer only from the provided context. Do not invent facts. "
        "Use plain language. If a question involves emergency symptoms, medical diagnosis, "
        "profile changes, guaranteed claim payment, or uncertainty, escalate instead of guessing. "
        "Do not expose unmasked member IDs.\n\n"
        f"Member display name: {member['display_name']}\n"
        f"Coverage status: {member['status']}\n"
        f"Plan: {plan['plan_name']}\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer in 2-5 concise sentences."
    )

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        response = client.responses.create(
            model=settings.chat_model,
            input=prompt,
            temperature=0.1,
        )
        text = getattr(response, "output_text", "").strip()
        return text or fallback_answer(question, top_matches, member, plan)
    except Exception:
        return fallback_answer(question, top_matches, member, plan)


def answer_question(question: str, member: dict, plan: dict, settings: Settings) -> dict:
    from src.assistant_graph import run_assistant_graph

    return run_assistant_graph(question, member, plan, settings)
