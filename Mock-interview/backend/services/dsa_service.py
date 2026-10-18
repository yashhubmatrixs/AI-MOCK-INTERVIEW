"""
The fixed DSA question list (data/dsa_questions.json).

Every CODING question in an interview is picked from this list. The resume and the job
description are never used to invent coding questions - they only drive the essay and
spoken ones (see grounding_service.plan_questions).

Edit data/dsa_questions.json to add, remove or reword questions (keep each "number" unique)
and restart the backend.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

_PATH = Path(__file__).resolve().parent.parent / "data" / "dsa_questions.json"


@dataclass(frozen=True)
class DsaQuestion:
    number: int
    category: str
    text: str

    @property
    def id(self) -> str:
        return f"D{self.number}"


_cache: Optional[list[DsaQuestion]] = None


def load() -> list[DsaQuestion]:
    """All questions in the list, in file order."""
    global _cache
    if _cache is None:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        questions = []
        for category in data.get("categories", []):
            for item in category.get("questions", []):
                text = str(item.get("text", "")).strip()
                if text:
                    questions.append(DsaQuestion(int(item["number"]), str(category["name"]), text))
        _cache = questions
    return list(_cache)


def reload() -> None:
    global _cache
    _cache = None


def count_for(total_questions: int) -> int:
    """How many of an interview's questions are coding questions: about a third (at least
    one), and none when the interview has a single question."""
    if total_questions < 2:
        return 0
    return max(1, total_questions // 3)


def pick(count: int, rng: Optional[random.Random] = None) -> list[DsaQuestion]:
    """`count` different questions, spread over as many topics as possible (arrays, strings,
    trees ...) so one interview doesn't ask three array questions in a row."""
    rng = rng or random.Random()
    pools: dict[str, list[DsaQuestion]] = {}
    for q in load():
        pools.setdefault(q.category, []).append(q)
    for pool in pools.values():
        rng.shuffle(pool)
    names = list(pools)
    rng.shuffle(names)

    chosen: list[DsaQuestion] = []
    while len(chosen) < count and any(pools.values()):
        for name in names:
            if pools[name] and len(chosen) < count:
                chosen.append(pools[name].pop())
    return chosen


def spread(others: Sequence, codes: Sequence) -> list:
    """Place the coding questions at even intervals among the other questions, instead of
    all at the start or the end."""
    result = list(others)
    total = len(result) + len(codes)
    for k, item in enumerate(codes):
        position = ((k + 1) * total) // (len(codes) + 1)
        result.insert(min(position, len(result)), item)
    return result
