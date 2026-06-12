import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.documents import load_kb_documents
from src.pinecone_hybrid import ensure_index, get_client, upsert_documents
from src.settings import get_settings


def main() -> None:
    settings = get_settings(require_api_key=True)
    docs = load_kb_documents()

    print(f"Loaded {len(docs)} knowledge-base documents.")
    pc = get_client(settings)
    ensure_index(pc, settings)

    count = upsert_documents(pc, settings, docs)
    print(
        f"Upserted {count} documents into {settings.index_name} "
        f"namespace {settings.namespace}."
    )


if __name__ == "__main__":
    main()
