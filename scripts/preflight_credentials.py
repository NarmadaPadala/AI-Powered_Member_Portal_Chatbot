import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.settings import get_settings


def mask_status(value: str, placeholder: str) -> str:
    if not value:
        return "missing"
    if value == placeholder or placeholder in value:
        return "placeholder"
    return "set"


def main() -> None:
    settings = get_settings(require_api_key=False)
    checks = {
        "OPENAI_API_KEY": mask_status(settings.openai_api_key, "your-openai-api-key"),
        "PINECONE_API_KEY": mask_status(settings.pinecone_api_key, "your-pinecone-api-key"),
        "PINECONE_INDEX_NAME": mask_status(settings.index_name, "your-index-name"),
    }

    for name, status in checks.items():
        print(f"{name}: {status}")

    bad = [name for name, status in checks.items() if status != "set"]
    if bad:
        raise SystemExit(f"Credential preflight failed: {', '.join(bad)}")

    print("Credential preflight passed. Values are present and not placeholders.")


if __name__ == "__main__":
    main()
