import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Union


@dataclass(frozen=True)
class KBDocument:
    id: str
    source_type: str
    title: str
    member_id: str
    plan_id: str
    text: str

    @property
    def metadata(self) -> dict:
        return {
            "source_type": self.source_type,
            "title": self.title,
            "member_id": self.member_id,
            "plan_id": self.plan_id,
            "text": self.text,
        }


def load_kb_documents(path: Union[str, Path] = "data/kb_documents.jsonl") -> list[KBDocument]:
    kb_path = Path(path)
    docs: list[KBDocument] = []

    with kb_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            try:
                docs.append(KBDocument(**payload))
            except TypeError as exc:
                raise ValueError(f"Invalid KB document at line {line_number}: {exc}") from exc

    return docs


def batches(items: list[KBDocument], size: int) -> Iterable[list[KBDocument]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]
