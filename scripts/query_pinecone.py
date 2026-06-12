import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.safety import classify_query


MEMBER_PLAN_MAP = {
    "M001": "PLAN-PPO-GOLD",
    "M002": "PLAN-HMO-SILVER",
    "M003": "PLAN-HDHP-BRONZE",
}

def main() -> None:
    parser = argparse.ArgumentParser(description="Query Pinecone with hybrid retrieval.")
    parser.add_argument("query", help="Member support question")
    parser.add_argument("--member-id", default="M001", choices=MEMBER_PLAN_MAP.keys())
    parser.add_argument("--top-k", default=5, type=int)
    parser.add_argument("--alpha", default=0.55, type=float, help="Dense weight from 0 to 1")
    args = parser.parse_args()

    safety = classify_query(args.query)
    if safety.route != "retrieval":
        print(f"Safety route: {safety.route}")
        print(safety.message)
        return

    from src.pinecone_hybrid import get_client, query_hybrid, summarize_matches
    from src.settings import get_settings

    settings = get_settings(require_api_key=True)
    pc = get_client(settings)
    result = query_hybrid(
        pc=pc,
        settings=settings,
        query=args.query,
        member_id=args.member_id,
        plan_id=MEMBER_PLAN_MAP[args.member_id],
        top_k=args.top_k,
        alpha=args.alpha,
    )
    summary = summarize_matches(result)

    if summary["should_escalate"]:
        print(
            "Low confidence fallback: I am not confident "
            "enough to answer this accurately. Please contact Member Services at "
            "1-800-555-0198."
        )

    print(f"\nHybrid search matches | score={summary['best_score']:.3f}")
    for rank, match in enumerate(summary["matches"], start=1):
        metadata = match["metadata"]
        print(f"\n{rank}. {metadata.get('title', '')}")
        print(f"   score: {match['score']:.3f}")
        print(f"   source: {metadata.get('source_type', '')}")
        print(f"   text: {metadata.get('text', '')[:220]}...")


if __name__ == "__main__":
    main()
