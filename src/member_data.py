import csv
from pathlib import Path
from typing import Optional, Union


DATA_DIR = Path("data")


def read_csv(name: str) -> list[dict]:
    with (DATA_DIR / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def get_members() -> list[dict]:
    return read_csv("members.csv")


def get_member(member_id: str) -> dict:
    for member in get_members():
        if member["member_id"] == member_id:
            return member
    raise ValueError(f"Unknown member_id: {member_id}")


def get_plan(plan_id: str) -> dict:
    for plan in read_csv("plans.csv"):
        if plan["plan_id"] == plan_id:
            return plan
    raise ValueError(f"Unknown plan_id: {plan_id}")


def get_benefits(plan_id: str) -> list[dict]:
    return [row for row in read_csv("benefits.csv") if row["plan_id"] == plan_id]


def get_claims(member_id: str) -> list[dict]:
    return [row for row in read_csv("claims.csv") if row["member_id"] == member_id]


def get_providers() -> list[dict]:
    return read_csv("providers.csv")


def get_pcp(member: dict) -> Optional[dict]:
    pcp_id = member.get("pcp_id")
    if not pcp_id:
        return None

    for provider in read_csv("providers.csv"):
        if provider["provider_id"] == pcp_id:
            return provider
    return None


def money(value: Union[str, int, float]) -> str:
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)
