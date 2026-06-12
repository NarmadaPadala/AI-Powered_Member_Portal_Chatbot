from dataclasses import dataclass
import re
from typing import Optional


EMERGENCY_TERMS = {
    "chest pain",
    "can't breathe",
    "cannot breathe",
    "stroke",
    "suicide",
    "overdose",
    "unconscious",
    "severe bleeding",
}

MEDICAL_ADVICE_TERMS = {
    "diagnose",
    "diagnosis",
    "treat my",
    "what medicine",
    "dosage",
    "rash",
    "symptoms",
}

ACCOUNT_CHANGE_ACTIONS = {"change", "correct", "edit", "replace", "update"}
ACCOUNT_CHANGE_FIELDS = {"address", "email", "mailing", "phone", "telephone"}

GUARANTEE_TERMS = {
    "guarantee this claim",
    "guarantee claim",
    "guarantee paid",
    "will be paid",
    "will this claim be paid",
    "will my claim be paid",
    "will insurance pay",
    "will the plan pay",
}

SMALL_TALK_TERMS = {
    "ok",
    "okay",
    "cool",
    "got it",
    "great",
    "nice",
    "sounds good",
    "thanks",
    "thank you",
    "hello",
    "hi",
    "hey",
    "how are you",
    "what's up",
    "whats up",
    "yes",
    "no",
}

HEALTHCARE_INTENT_TERMS = {
    "active",
    "approval",
    "authorization",
    "benefit",
    "benefits",
    "bill",
    "claim",
    "claims",
    "coinsurance",
    "copay",
    "copayment",
    "coverage",
    "covered",
    "deductible",
    "denied",
    "dependent",
    "dependents",
    "doctor",
    "form",
    "forms",
    "group",
    "hmo",
    "id",
    "in network",
    "innetwork",
    "mri",
    "network",
    "out of network",
    "out-of-network",
    "pcp",
    "plan",
    "ppo",
    "preauth",
    "pre auth",
    "prior authorization",
    "provider",
    "referral",
    "specialist",
    "urgent",
}


@dataclass(frozen=True)
class SafetyDecision:
    route: str
    message: Optional[str] = None


def classify_query(query: str) -> SafetyDecision:
    normalized = query.lower().strip()
    normalized_text = re.sub(r"[^a-z0-9\s-]", " ", normalized)
    normalized_text = re.sub(r"\s+", " ", normalized_text).strip()

    has_healthcare_intent = any(term in normalized_text for term in HEALTHCARE_INTENT_TERMS)
    if normalized_text in SMALL_TALK_TERMS and not has_healthcare_intent:
        return SafetyDecision(
            route="small_talk",
            message=(
                "Got it. What would you like help with next? You can ask about benefits, "
                "claims, providers, coverage, or account support."
            ),
        )

    if any(term in normalized for term in EMERGENCY_TERMS):
        return SafetyDecision(
            route="emergency",
            message=(
                "If this may be a medical emergency, call 911 immediately or go to "
                "the nearest emergency room. I can help with coverage questions after "
                "you are safe."
            ),
        )

    if any(term in normalized for term in MEDICAL_ADVICE_TERMS):
        return SafetyDecision(
            route="medical_advice",
            message=(
                "I cannot diagnose symptoms or provide medical advice. Please contact "
                "a licensed clinician. If symptoms feel urgent or severe, call 911."
            ),
        )

    words = set(normalized_text.split())
    has_account_change_action = bool(words & ACCOUNT_CHANGE_ACTIONS)
    has_account_change_field = bool(words & ACCOUNT_CHANGE_FIELDS)
    if has_account_change_action and has_account_change_field:
        return SafetyDecision(
            route="secure_workflow",
            message=(
                "For security, profile changes must be completed through the secure "
                "profile update form or Member Services verification. I can explain "
                "the steps, but I should not update personal details in chat."
            ),
        )

    if any(term in normalized for term in GUARANTEE_TERMS):
        return SafetyDecision(
            route="coverage_guarantee",
            message=(
                "I cannot guarantee claim payment in chat. Final payment depends on "
                "eligibility, benefits, medical policy, provider billing, and claim "
                "review. Please contact Member Services for a formal review."
            ),
        )

    return SafetyDecision(route="retrieval")
