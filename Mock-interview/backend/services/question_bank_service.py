import json
import os

_BANK_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "question_bank.json")

with open(_BANK_PATH, "r", encoding="utf-8") as f:
    _BANK = json.load(f)


def get_seed_questions(company_name: str, limit: int = 5) -> list[dict]:
    """Return a handful of example previous-year-style questions for a company.

    Matches case-insensitively on substring (e.g. "Zensar Technologies" matches
    the "zensar" bucket). Falls back to the generic bucket if nothing matches.
    """
    company_key = (company_name or "").strip().lower()
    matched: list[dict] = []

    for key, questions in _BANK.items():
        if key == "_readme":
            continue
        if key in company_key or company_key in key:
            matched = questions
            break

    if not matched:
        matched = _BANK.get("generic", [])

    return matched[:limit]
