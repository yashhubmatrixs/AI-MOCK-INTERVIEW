"""
Grounding: the glue between retrieval (rag_service) and the model (llm_service).

Two jobs, both aimed at stopping the model from making things up:

  plan_questions  Build numbered excerpts from the job description, resume and question
                  bank, let the model write questions from them, then CHECK each
                  question against the excerpts. A question is labelled with where it
                  came from (jd / resume / question_bank) only if an excerpt really
                  supports it; otherwise it is labelled 'llm_generated' (unsourced).

  grade_answer    Retrieve reference passages for the question and let the model judge
                  technical correctness only against them. Citations the model makes
                  are checked against what was actually retrieved - invented ones are
                  stripped. If nothing relevant was retrieved the answer is graded as
                  'general feedback' and marked ungrounded instead of pretending.

Both return plain dicts; the routes store them (Question.source + Evidence rows).
"""

import re
from typing import Optional

from services import dsa_service, llm_service, rag_service
from services.rag_service import Chunk

JD_BUDGET_CHARS = 2800
RESUME_BUDGET_CHARS = 2800
SNIPPET_CHARS = 240
REFERENCES_PER_ANSWER = 3

_SOURCE_BY_KIND = {"jd": "jd", "resume": "resume", "bank": "question_bank"}
BANK_EXAMPLES = 5  # how many previous-year-style questions the model sees as examples
EXTRA_REQUESTED = 2  # ask the model for a couple more than needed, in case some get dropped below


def _snippet(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= SNIPPET_CHARS else text[: SNIPPET_CHARS - 1].rstrip() + "…"


def _evidence(chunk: Chunk) -> dict:
    return {
        "kind": chunk.kind,
        "ref_id": chunk.id,
        "source": chunk.source,
        "snippet": _snippet(chunk.text),
    }


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------

def _question_record(text: str, qtype: str, chunk: Optional[Chunk]) -> dict:
    return {
        "question_text": text,
        "question_type": qtype,
        "source": _SOURCE_BY_KIND.get(chunk.kind, "llm_generated") if chunk else "llm_generated",
        "evidence": [_evidence(chunk)] if chunk else [],
    }


# A small model sometimes writes a coding task and labels it "essay" or "verbal" anyway
# ("Write a Python function for the gesture classifier in your project", "Debug or complete
# this partially-written function"). Coding questions may only come from the DSA list, so
# anything that is asking for code is dropped, whatever label it carries.
_POLITE_START = re.compile(
    r"^(?:(?:please|now|next|also|then|so|okay|ok|let'?s|can you|could you|would you|will you|"
    r"i(?:'d| would) like you to|i want you to|you should|you need to|try to)\b[\s,:-]*)+",
    re.IGNORECASE,
)
_CODING_TASK_NOUNS = r"(?:function|program|script|code|class|method|algorithm|snippet|implementation|query|module|api|endpoint|loop|pseudocode)"
_CODING_STYLE = [
    # "Write a Python function ...", "Implement the classifier ... function", "Debug this code"
    re.compile(
        r"^(?:write|implement|code|program|develop|create|build|complete|finish|fix|debug|refactor|"
        r"modify|extend|optimi[sz]e|rewrite)\b[^.?!]{0,80}?\b" + _CODING_TASK_NOUNS + r"\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bwrite\s+(?:an?|the|some)?\s*(?:\w+\s+){0,3}" + _CODING_TASK_NOUNS + r"\b", re.IGNORECASE),
    # "Implement the gesture classifier ...", "Code a LRU cache" - always a coding ask
    re.compile(r"^(?:implement|code)\b", re.IGNORECASE),
    # "Write / build / create ... in Python (Java, C++, SQL ...)"
    re.compile(
        r"^(?:write|build|create|develop|program)\b[^.?!]{0,80}?\b(?:in|using|with)\s+"
        r"(?:python|java|javascript|c\+\+|c#|sql|rust|kotlin|typescript)(?![\w-])",
        re.IGNORECASE,
    ),
    re.compile(r"\bpartially[- ]written\b|\bspot and fix\b|\bfind (?:and fix )?the (?:bug|error)s?\b", re.IGNORECASE),
    re.compile(r"\b(?:following|given|below|this|these) (?:code|function|snippet|program|script)\b", re.IGNORECASE),
    re.compile(r"\bcomplete (?:the|this|a) (?:code|function|program)\b", re.IGNORECASE),
]


def looks_like_coding_question(text: str) -> bool:
    """True if the question asks the candidate to write, complete or debug code."""
    cleaned = _POLITE_START.sub("", " ".join((text or "").split()))
    return any(pattern.search(cleaned) for pattern in _CODING_STYLE)


def _dsa_record(q: "dsa_service.DsaQuestion") -> dict:
    """A coding question taken verbatim from the fixed DSA list."""
    return {
        "question_text": q.text,
        "question_type": "code",
        "source": "dsa_list",
        "evidence": [
            {
                "kind": "dsa",
                "ref_id": q.id,
                "source": f"DSA list > {q.category}",
                "snippet": f"Question {q.number} of the DSA practice list ({q.category}).",
            }
        ],
    }


def plan_questions(
    resume_text: str,
    job_description: str,
    company_name: str,
    seed_questions: list[dict],
    num_questions: int = 6,
    rng=None,
) -> list[dict]:
    """Return [{question_text, question_type, source, evidence: [..]}, ...].

    Coding questions come ONLY from the fixed DSA list (about a third of the interview);
    the model is never asked for them. The rest are essay / spoken questions grounded in
    the job description, resume and question bank."""
    code_count = dsa_service.count_for(num_questions)
    other_count = num_questions - code_count
    dsa_questions = [_dsa_record(q) for q in dsa_service.pick(code_count, rng)]

    others = _plan_other_questions(
        resume_text, job_description, company_name, seed_questions, other_count
    ) if other_count > 0 else []
    return dsa_service.spread(others, dsa_questions)


def _plan_other_questions(
    resume_text: str,
    job_description: str,
    company_name: str,
    seed_questions: list[dict],
    num_questions: int,
) -> list[dict]:
    """Essay / spoken questions from the job description, resume and question bank."""
    jd_chunks = rag_service.chunk_text(
        job_description, kind="jd", source="Job description", prefix="J"
    )
    resume_chunks = rag_service.chunk_text(
        resume_text, kind="resume", source="Your resume", prefix="R"
    )
    # If either document is too long for the model's context window, keep the parts
    # most relevant to the other one instead of cutting off the end.
    jd_used = rag_service.select_within_budget(
        jd_chunks,
        f"{resume_text} skills requirements responsibilities",
        JD_BUDGET_CHARS,
    )
    resume_used = rag_service.select_within_budget(resume_chunks, job_description, RESUME_BUDGET_CHARS)

    # Previous-year coding questions are not used: coding comes from the DSA list.
    non_code_seeds = [q for q in seed_questions if q.get("type") != "code"][:BANK_EXAMPLES]
    bank_chunks = [
        Chunk(f"B{n}", q["question"], "Question bank", "bank")
        for n, q in enumerate(non_code_seeds, start=1)
    ]
    bank_types = {c.id: q["type"] for c, q in zip(bank_chunks, non_code_seeds)}

    generated = llm_service.generate_questions(
        company_name=company_name,
        num_questions=num_questions + EXTRA_REQUESTED,
        jd_excerpts=[{"id": c.id, "text": c.text} for c in jd_used],
        resume_excerpts=[{"id": c.id, "text": c.text} for c in resume_used],
        bank_excerpts=[
            {"id": c.id, "text": c.text, "type": bank_types[c.id]} for c in bank_chunks
        ],
        allowed_types=("essay", "verbal"),
    )

    support_pool = jd_used + resume_used + bank_chunks
    planned, seen = [], set()
    for item in generated:
        if looks_like_coding_question(item["question_text"]):
            continue  # coding questions come from the DSA list only
        key = " ".join(item["question_text"].lower().split())
        if key in seen:
            continue
        seen.add(key)
        chunk = rag_service.attribute_question(item["question_text"], support_pool, item.get("based_on"))
        planned.append(_question_record(item["question_text"], item["question_type"], chunk))

    if planned:
        return planned[:num_questions]

    # The model gave nothing usable: fall back to the (non-coding) question bank itself,
    # which is real source material, rather than anything generated.
    return [
        _question_record(c.text, bank_types[c.id], c)
        for c in bank_chunks
        if not looks_like_coding_question(c.text)
    ][:num_questions]


# ---------------------------------------------------------------------------
# Answers
# ---------------------------------------------------------------------------

_CITATION_GROUP = re.compile(r"(\s*)\[\s*(S\d+(?:\s*[,;/]\s*S\d+)*)\s*\]", re.IGNORECASE)


def _strip_invalid_citations(text: str, valid_ids: set[str]) -> str:
    """Keep [S1]-style markers that point at a retrieved passage; remove the rest."""
    def fix(match: re.Match) -> str:
        ids = [i.upper() for i in re.findall(r"S\d+", match.group(2), re.IGNORECASE)]
        kept = [i for i in ids if i in valid_ids]
        return match.group(1) + "".join(f"[{i}]" for i in kept) if kept else ""

    return _CITATION_GROUP.sub(fix, text or "").strip()


def grade_answer(
    question_text: str,
    question_type: str,
    answer_text: str,
    job_description: str,
) -> dict:
    """Return {score, feedback, strengths, weaknesses, grounded, evidence: [..], invalid_citations}."""
    if not (answer_text or "").strip():
        # Nothing to check - don't dress an empty answer up with sources.
        result = llm_service.evaluate_answer(question_text, question_type, answer_text, job_description)
        return {**result, "grounded": False, "evidence": [], "invalid_citations": 0}

    hits = [
        h for h in rag_service.search_knowledge(question_text, k=REFERENCES_PER_ANSWER) if h.relevant
    ]
    references = rag_service.relabel(hits)

    result = llm_service.evaluate_answer(
        question_text=question_text,
        question_type=question_type,
        answer_text=answer_text,
        job_description=job_description,
        references=[{"id": c.id, "source": c.source, "text": c.text} for c in references],
    )

    # The model gets the last word on relevance too: if it says the passages don't
    # relate to the question, don't present them as the basis for the feedback.
    grounded = bool(references) and result["reference_relevant"] is not False
    valid_ids = {c.id for c in references} if grounded else set()
    invalid = [c for c in result["sources_used"] if c not in valid_ids]

    return {
        "score": result["score"],
        "feedback": _strip_invalid_citations(result["feedback"], valid_ids),
        "strengths": [_strip_invalid_citations(s, valid_ids) for s in result["strengths"]],
        "weaknesses": [_strip_invalid_citations(w, valid_ids) for w in result["weaknesses"]],
        "grounded": grounded,
        "evidence": [_evidence(c) for c in references] if grounded else [],
        "invalid_citations": len(invalid),
    }
