import math
import re
from collections import Counter

from src.documents import KBDocument


TOKEN_RE = re.compile(r"[a-z0-9]+")

QUERY_EXPANSIONS = {
    "deductble": "deductible",
    "netwrok": "network",
    "near by": "nearby",
    "patell": "patel",
    "pre auto approval": "prior authorization",
    "pre approval": "prior authorization",
    "pcp": "primary care provider",
    "copay": "copayment",
}


def normalize_text(text: str) -> str:
    lowered = text.lower()
    provider_typos = {
        r"\bnear\s+by\s+pc\b": "nearby primary care provider",
        r"\bnearby\s+pc\b": "nearby primary care provider",
        r"\bsuggest\s+(a\s+)?pc\b": "suggest primary care provider",
        r"\bfind\s+(a\s+)?pc\b": "find primary care provider",
    }
    for pattern, replacement in provider_typos.items():
        lowered = re.sub(pattern, replacement, lowered)
    for typo, replacement in QUERY_EXPANSIONS.items():
        lowered = lowered.replace(typo, replacement)
    return lowered


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(normalize_text(text))


def char_ngrams(text: str, size: int = 3) -> Counter:
    clean = re.sub(r"[^a-z0-9]+", " ", normalize_text(text)).strip()
    compact = f" {clean} "
    if len(compact) < size:
        return Counter({compact: 1})
    return Counter(compact[index : index + size] for index in range(len(compact) - size + 1))


def cosine(left: Counter, right: Counter) -> float:
    if not left or not right:
        return 0.0

    overlap = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in overlap)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def lexical_score(query_tokens: list[str], doc_tokens: list[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0

    query_counts = Counter(query_tokens)
    doc_counts = Counter(doc_tokens)
    overlap = sum(min(query_counts[token], doc_counts[token]) for token in query_counts)
    return overlap / len(query_counts)


def source_boost(query: str, source_type: str) -> float:
    normalized = normalize_text(query)
    boosts = {
        "provider_directory": ["provider", "doctor", "dr ", "network", "pcp", "patel"],
        "member_profile": [
            "my group id",
            "my plan",
            "plan active",
            "deductible left",
            "deductible do i have left",
            "remaining",
            "estimate my",
        ],
        "benefits": [
            "cover",
            "copay",
            "emergency",
            "urgent care",
            "specialist",
            "referral",
            "out of network",
            "covered",
            "mri",
        ],
        "claims": ["claim", "denied", "denial"],
        "prior_authorization": ["prior authorization", "approval", "mri"],
        "eligibility": ["dependent", "spouse", "change my plan", "open enrollment"],
        "glossary": ["what is", "what does", "mean", "coinsurance"],
        "safety": ["chest pain", "diagnose", "guarantee"],
        "faq": ["phone", "change my"],
    }
    boost = 0.1 if any(term in normalized for term in boosts.get(source_type, [])) else 0.0
    personal_terms = [" my ", " i ", "me ", "do i", "have i"]
    coverage_question = any(term in normalized for term in ["cover", "covered", "coverage"])
    if source_type == "member_profile" and any(term in normalized for term in [" my ", " i ", "me "]):
        boost += 0.22
    if source_type == "member_profile" and any(
        term in normalized for term in ["group id", "deductible", "active", "remaining"]
    ):
        boost += 0.16
    if source_type == "member_profile" and coverage_question:
        boost -= 0.35
    if source_type == "benefits" and coverage_question:
        boost += 0.28
    if source_type == "benefits" and any(term in normalized for term in ["mri", "emergency"]):
        boost += 0.2
    if source_type == "prior_authorization" and "mri" in normalized:
        boost += 0.18
    if source_type == "glossary" and " my " in f" {normalized} ":
        boost -= 0.35
    if source_type == "glossary" and any(term in normalized for term in personal_terms):
        boost -= 0.15
    if source_type == "claims" and not any(term in normalized for term in ["claim", "denied", "denial"]):
        boost -= 0.3
    if source_type == "benefits" and any(term in normalized for term in ["referral", "specialist"]):
        boost += 0.18
    return boost


def local_hybrid_search(
    query: str,
    documents: list[KBDocument],
    member_id: str,
    plan_id: str,
    top_k: int = 5,
    alpha: float = 0.55,
) -> list[dict]:
    query_tokens = tokenize(query)
    query_chars = char_ngrams(query)
    matches = []

    for doc in documents:
        if doc.member_id not in {member_id, "ALL"}:
            continue
        if doc.plan_id not in {plan_id, "ALL"}:
            continue

        combined_text = f"{doc.title} {doc.source_type} {doc.text}"
        doc_tokens = tokenize(combined_text)
        sparse = lexical_score(query_tokens, doc_tokens)
        dense = cosine(query_chars, char_ngrams(combined_text))
        score = (alpha * dense) + ((1 - alpha) * sparse) + source_boost(query, doc.source_type)

        matches.append(
            {
                "id": doc.id,
                "score": round(score, 4),
                "metadata": doc.metadata,
            }
        )

    return sorted(matches, key=lambda item: item["score"], reverse=True)[:top_k]
