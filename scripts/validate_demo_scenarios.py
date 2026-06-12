import argparse
import sys
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.member_data import get_member, get_plan
from src.rag_answer import answer_question, offline_answer_question
from src.settings import get_settings


DEMO_CASES = [
    {
        "query": "dogs and cat",
        "expected_substrings": ["healthcare coverage", "plan-related question"],
        "forbidden_substrings": ["Dr.", "provider directory", "Member Alex Morgan", "GRP-CA-2048"],
        "allowed_routes": {"out_of_scope"},
    },
    {
        "query": "whats up",
        "expected_substrings": ["What would you like help with next"],
        "forbidden_substrings": ["Member Alex Morgan", "GRP-CA-2048", "deductible"],
        "allowed_routes": {"small_talk"},
    },
    {
        "query": "what is my group ID",
        "expected_substrings": ["GRP-CA-2048"],
        "forbidden_substrings": ["Member Alex Morgan", "Dependents on file"],
        "allowed_routes": {"answered", "offline_answered"},
    },
    {
        "query": "what is my grou pID",
        "expected_substrings": ["GRP-CA-2048"],
        "forbidden_substrings": ["Member Alex Morgan", "Dependents on file"],
        "allowed_routes": {"answered", "offline_answered"},
    },
    {
        "query": "Can you suggest near by PC",
        "expected_substrings": ["Dr. Anika Patel", "primary care provider"],
        "forbidden_substrings": ["Member Alex Morgan", "not confident enough"],
        "allowed_routes": {"answered", "offline_answered"},
    },
    {
        "query": "Does my plan cover MRI services?",
        "expected_substrings": ["MRI", "Prior authorization"],
        "forbidden_substrings": ["Member Alex Morgan", "Dependents on file"],
        "allowed_routes": {"answered", "offline_answered"},
    },
    {
        "query": "Does my plan cover emergency?",
        "expected_substrings": ["emergency", "covered"],
        "forbidden_substrings": ["Member Alex Morgan", "Dependents on file"],
        "allowed_routes": {"answered", "offline_answered"},
    },
    {
        "query": "copay",
        "expected_substrings": ["Copay"],
        "forbidden_substrings": ["Member Alex Morgan", "not confident enough"],
        "allowed_routes": {"answered", "offline_answered"},
    },
    {
        "query": "deductible",
        "expected_substrings": ["Deductible"],
        "forbidden_substrings": ["Member Alex Morgan", "not confident enough"],
        "allowed_routes": {"answered", "offline_answered"},
    },
    {
        "query": "I am having chest pain what should I do?",
        "expected_substrings": ["911", "emergency"],
        "forbidden_substrings": ["Member Alex Morgan", "provider directory"],
        "allowed_routes": {"emergency"},
    },
]


def validate_result(case: dict, result: dict) -> list[str]:
    answer = result.get("answer", "")
    route = result.get("route", "")
    failures = []

    if route not in case["allowed_routes"]:
        failures.append(f"route {route!r} not in {sorted(case['allowed_routes'])}")

    answer_lower = answer.lower()
    for expected in case["expected_substrings"]:
        if expected.lower() not in answer_lower:
            failures.append(f"missing expected text {expected!r}")

    for forbidden in case["forbidden_substrings"]:
        if forbidden.lower() in answer_lower:
            failures.append(f"contains forbidden text {forbidden!r}")

    return failures


def run_validation(backend: str) -> int:
    member = get_member("M001")
    plan = get_plan(member["plan_id"])
    settings = get_settings(require_api_key=True) if backend == "live" else None
    failed = 0

    for index, case in enumerate(DEMO_CASES, start=1):
        if backend == "live":
            result = answer_question(case["query"], member, plan, settings)
        else:
            result = offline_answer_question(case["query"], member, plan)

        failures = validate_result(case, result)
        status = "PASS" if not failures else "FAIL"
        print(f"{index:02d}. {status} | {case['query']}")
        print(f"    route={result.get('route')} escalated={result.get('escalated')}")
        print(f"    answer={result.get('answer')}")
        if failures:
            failed += 1
            for failure in failures:
                print(f"    - {failure}")
        print()

    print(f"Demo validation result: {len(DEMO_CASES) - failed}/{len(DEMO_CASES)} passed ({backend})")
    return 1 if failed else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate final demo chatbot scenarios.")
    parser.add_argument("--backend", choices=["offline", "live"], default="offline")
    args = parser.parse_args()
    raise SystemExit(run_validation(args.backend))


if __name__ == "__main__":
    main()
