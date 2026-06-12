import csv
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.documents import load_kb_documents


DATA_DIR = Path("data")


def count_csv(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def validate_jsonl(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                json.loads(line)
                count += 1
    return count


def main() -> None:
    print("Healthcare Support Data Inventory")
    print("---------------------------------")

    for path in sorted(DATA_DIR.glob("*.csv")):
        print(f"{path.name}: {count_csv(path)} rows")

    kb_count = validate_jsonl(DATA_DIR / "kb_documents.jsonl")
    docs = load_kb_documents(DATA_DIR / "kb_documents.jsonl")
    if kb_count != len(docs):
        raise RuntimeError("KB document count mismatch")

    print(f"kb_documents.jsonl: {kb_count} rows")


if __name__ == "__main__":
    main()
