"""
LLM integration for the interview engine.

The app only ever calls the three public functions in this file - question
generation, single-answer evaluation, and the end-of-interview report. Which
model answers them is chosen by LLM_PROVIDER in backend/.env:

  openai  (default)  OpenAI's hosted API. Needs OPENAI_API_KEY and prepaid credit.
  ollama             A model running on your own machine through Ollama
                     (https://ollama.com). No key, no per-call cost.

Routers never see the difference. Anything that goes wrong on the model side is
raised as LLMError, and its message is written to be shown to the user as-is
(main.py turns it into a 503 that the frontend displays).
"""

import json
import os
import re
from pathlib import Path
from typing import Sequence

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class LLMError(Exception):
    """The model backend couldn't give a usable answer. The message is safe to show to the user."""


class LLMOutputError(LLMError):
    """The model answered, but not in a shape we could read (for example broken JSON)."""


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _env_number(name: str, default, cast):
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    try:
        return cast(raw)
    except ValueError:
        raise LLMError(f"{name} in backend/.env must be a number (got '{raw}').")


def _provider() -> str:
    value = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if value not in ("openai", "ollama"):
        raise LLMError(
            f"LLM_PROVIDER in backend/.env must be 'openai' or 'ollama' (got '{value}')."
        )
    return value


def provider_name() -> str:
    """'openai' or 'ollama' (raises LLMError if LLM_PROVIDER is invalid)."""
    return _provider()


def _ollama_settings() -> dict:
    return {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
        "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
        "num_ctx": _env_number("OLLAMA_NUM_CTX", 4096, int),
        "timeout": _env_number("OLLAMA_TIMEOUT", 300.0, float),
        "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "30m"),
        # Cap on reply length so a model that rambles can't run into the timeout.
        "max_tokens": _env_number("OLLAMA_MAX_TOKENS", 1500, int),
    }


def describe_backend() -> str:
    """One-line description for the startup log and check_llm.py."""
    try:
        if _provider() == "ollama":
            s = _ollama_settings()
            return f"ollama - model '{s['model']}' at {s['base_url']}"
        return f"openai - model '{os.getenv('LLM_MODEL', 'gpt-4o-mini')}'"
    except LLMError as exc:
        return f"misconfigured - {exc}"


# ---------------------------------------------------------------------------
# Talking to the model
# ---------------------------------------------------------------------------

def _chat(system_prompt: str, user_prompt: str, temperature: float = 0.6) -> str:
    if _provider() == "ollama":
        return _chat_ollama(system_prompt, user_prompt, temperature)
    return _chat_openai(system_prompt, user_prompt, temperature)


def _ollama_error_text(response: httpx.Response) -> str:
    try:
        body = response.json()
        if isinstance(body, dict) and body.get("error"):
            return str(body["error"])
    except ValueError:
        pass
    return response.text[:200]


def _ollama_post(path: str, payload: dict, model: str):
    """POST to an Ollama endpoint and return the parsed JSON, turning every failure
    (not running, model missing, timeout) into an LLMError that says what to do."""
    s = _ollama_settings()
    try:
        response = httpx.post(
            f"{s['base_url']}{path}",
            json=payload,
            timeout=httpx.Timeout(s["timeout"], connect=5.0),
        )
    except httpx.ConnectError:
        raise LLMError(
            f"Can't reach Ollama at {s['base_url']}. Make sure it's running (open the "
            "Ollama app, or run 'ollama serve' in a terminal) and try again."
        )
    except httpx.TimeoutException:
        raise LLMError(
            f"Ollama didn't answer within {s['timeout']:.0f}s. The first request after "
            "startup is the slowest because the model has to load - try again, or switch "
            "to a smaller model (for example OLLAMA_MODEL=llama3.2 in backend/.env)."
        )
    except httpx.HTTPError as exc:
        raise LLMError(f"Couldn't talk to Ollama: {exc}")

    if response.status_code != 200:
        detail = _ollama_error_text(response)
        lowered = detail.lower()
        if "model" in lowered and "not found" in lowered:
            raise LLMError(
                f"Ollama doesn't have the model '{model}' yet. "
                f"Run this in a terminal, then try again:  ollama pull {model}"
            )
        raise LLMError(f"Ollama returned an error ({response.status_code}): {detail}")

    try:
        return response.json()
    except ValueError:
        raise LLMError("Ollama sent back a reply this app couldn't read.")


def _chat_ollama(system_prompt: str, user_prompt: str, temperature: float) -> str:
    """Call Ollama's native /api/chat endpoint (not its OpenAI-compatible one) so we
    can set the context size, keep the model loaded between calls, and force JSON."""
    s = _ollama_settings()
    payload = {
        "model": s["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": "json",
        "keep_alive": s["keep_alive"],
        "options": {
            "temperature": temperature,
            "num_ctx": s["num_ctx"],
            "num_predict": s["max_tokens"],
        },
    }
    body = _ollama_post("/api/chat", payload, s["model"])
    try:
        return body["message"]["content"] or ""
    except (KeyError, TypeError):
        raise LLMError("Ollama sent back a reply this app couldn't read.")


_openai_client = None


def _get_openai():
    """Return (openai module, shared client). Imported lazily so running purely on
    Ollama never depends on the OpenAI SDK."""
    global _openai_client
    try:
        import openai
    except ImportError:
        raise LLMError("The 'openai' package isn't installed. Run: pip install -r requirements.txt")

    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMError(
                "OPENAI_API_KEY isn't set in backend/.env. Add one, or run a local model "
                "instead by setting LLM_PROVIDER=ollama."
            )
        _openai_client = openai.OpenAI(api_key=api_key)
    return openai, _openai_client


def _openai_failure(openai, exc: Exception) -> LLMError:
    """Translate an OpenAI SDK error into a message the user can act on."""
    if isinstance(exc, openai.RateLimitError):
        if "insufficient_quota" in str(exc):
            return LLMError(
                "OpenAI says this API key has no credit left (insufficient_quota). Add "
                "credit in the OpenAI billing page, or run a local model instead by "
                "setting LLM_PROVIDER=ollama in backend/.env."
            )
        return LLMError("OpenAI is rate-limiting requests right now. Wait a few seconds and try again.")
    if isinstance(exc, openai.AuthenticationError):
        return LLMError("OpenAI rejected the API key. Check OPENAI_API_KEY in backend/.env.")
    if isinstance(exc, openai.APIConnectionError):
        return LLMError("Couldn't reach OpenAI. Check your internet connection.")
    return LLMError(f"OpenAI error: {exc}")


def _chat_openai(system_prompt: str, user_prompt: str, temperature: float) -> str:
    openai, client = _get_openai()
    try:
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
    except openai.OpenAIError as exc:
        raise _openai_failure(openai, exc)
    return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Embeddings (used by rag_service for semantic search; optional)
# ---------------------------------------------------------------------------

def embedding_model_name() -> str:
    if _provider() == "ollama":
        return os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    return os.getenv("EMBED_MODEL", "text-embedding-3-small")


def embed_texts(texts: list[str], role: str = "document") -> list[list[float]]:
    """Embed texts with the configured provider. role is 'document' or 'query' - the
    nomic models are trained to expect a matching prefix on each."""
    model = embedding_model_name()
    if _provider() == "ollama":
        prefix = ""
        if model.startswith("nomic-embed-text"):
            prefix = "search_query: " if role == "query" else "search_document: "
        body = _ollama_post(
            "/api/embed",
            {
                "model": model,
                "input": [prefix + t for t in texts],
                "keep_alive": _ollama_settings()["keep_alive"],
            },
            model,
        )
        vectors = body.get("embeddings") if isinstance(body, dict) else None
    else:
        openai, client = _get_openai()
        try:
            response = client.embeddings.create(model=model, input=texts)
        except openai.OpenAIError as exc:
            raise _openai_failure(openai, exc)
        vectors = [item.embedding for item in response.data]

    if (
        not isinstance(vectors, list)
        or len(vectors) != len(texts)
        or not all(isinstance(v, list) and v for v in vectors)
    ):
        raise LLMError(f"The embedding model '{model}' returned something this app couldn't read.")
    return vectors


# ---------------------------------------------------------------------------
# Reading the model's JSON (local models are sloppier than hosted ones)
# ---------------------------------------------------------------------------

def _extract_json(raw_text: str):
    """Parse JSON out of a model reply, tolerating ```json fences and chatty
    wrappers like 'Sure! Here is the JSON: {...}'. Raises ValueError if none."""
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[A-Za-z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fall back to the outermost {...} or [...] block, whichever starts first.
    candidates = []
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        if start != -1:
            candidates.append((start, closer))
    for start, closer in sorted(candidates):
        end = text.rfind(closer)
        if end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("no JSON found in model output")


def _chat_json(system_prompt: str, user_prompt: str, temperature: float = 0.6):
    """Ask for JSON; if the reply can't be parsed, ask once more before giving up."""
    for _ in range(2):
        raw = _chat(system_prompt, user_prompt, temperature)
        try:
            return _extract_json(raw)
        except ValueError:
            continue
    raise LLMOutputError(
        "The model replied twice without valid JSON, so its answer couldn't be read. "
        "Try again - if it keeps happening, switch to a stronger model in backend/.env."
    )


def _as_str_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def ping() -> str:
    """Tiny round trip used by check_llm.py. Returns the model's parsed reply as text."""
    data = _chat_json(
        "You are a health check. Reply with JSON only.",
        'Reply with exactly this JSON and nothing else: {"ok": true}',
        temperature=0,
    )
    return json.dumps(data)


# ---------------------------------------------------------------------------
# Question generation
#
# The model never sees "everything" - it is handed numbered excerpts (J1.. from the
# job description, R1.. from the resume, B1.. from the question bank) and told to
# ask only about what those excerpts contain. grounding_service checks afterwards
# that each question really is supported by an excerpt.
# ---------------------------------------------------------------------------

_TYPE_ALIASES = {
    "essay": "essay", "written": "essay",
    "code": "code", "coding": "code",
    "verbal": "verbal", "spoken": "verbal", "oral": "verbal",
}


def _parse_questions(data) -> list[dict]:
    """Accept {"questions": [...]}, a bare list, or any dict holding a list, and
    tolerate the model using 'question'/'type' instead of 'question_text'/'question_type'."""
    if isinstance(data, dict):
        items = data.get("questions")
        if not isinstance(items, list):
            items = next((v for v in data.values() if isinstance(v, list)), [])
    else:
        items = data
    if not isinstance(items, list):
        return []

    parsed = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = item.get("question_text") or item.get("question")
        qtype = _TYPE_ALIASES.get(
            str(item.get("question_type") or item.get("type") or "").strip().lower()
        )
        based_on = item.get("based_on") or item.get("source") or item.get("source_id")
        if isinstance(based_on, list):
            based_on = based_on[0] if based_on else None
        if isinstance(text, str) and text.strip() and qtype:
            parsed.append(
                {
                    "question_text": text.strip(),
                    "question_type": qtype,
                    "based_on": str(based_on).strip() if based_on else None,
                }
            )
    return parsed


def _excerpt_block(excerpts: list[dict], empty: str) -> str:
    if not excerpts:
        return empty
    return "\n".join(f"[{e['id']}] {e['text']}" for e in excerpts)


_TYPE_DESCRIPTIONS = {
    "essay": '"essay" (written conceptual or behavioural)',
    "code": '"code" (a hands-on coding or debugging problem solvable in a text editor)',
    "verbal": '"verbal" (meant to be answered out loud)',
}


def generate_questions(
    company_name: str,
    num_questions: int,
    jd_excerpts: list[dict],
    resume_excerpts: list[dict],
    bank_excerpts: list[dict],
    allowed_types: Sequence[str] = ("essay", "code", "verbal"),
) -> list[dict]:
    """Return [{question_text, question_type, based_on}, ...]; [] if the model's
    output was unusable (the caller then falls back to the question bank).

    Each excerpt is {"id": "J1", "text": "..."}; bank excerpts also carry "type".
    allowed_types limits what the model may ask. The app asks for ("essay", "verbal") only,
    because coding questions come from the fixed DSA list (dsa_service), not from the model;
    anything outside allowed_types is dropped before the list is cut to num_questions.
    """
    allowed = [t for t in ("essay", "code", "verbal") if t in allowed_types] or ["essay"]
    bank_block = "\n".join(
        f"[{b['id']}] ({b.get('type', 'essay')}) {b['text']}" for b in bank_excerpts
    ) or "(none for this company)"

    no_code_rule = (
        "\n- Do NOT ask coding, programming, algorithm or data-structure problems, and do not ask the candidate to write or debug code: those are asked separately from a fixed list."
        if "code" not in allowed
        else ""
    )

    system_prompt = (
        "You are an experienced technical interviewer creating a mock interview. "
        "You only use the excerpts you are given and never invent facts. "
        "You always respond with STRICT JSON only - no markdown fences, no commentary."
    )
    user_prompt = f"""
Create {num_questions} interview questions for a candidate interviewing at "{company_name}".

Use ONLY the excerpts below as your source of facts.

JOB DESCRIPTION EXCERPTS:
{_excerpt_block(jd_excerpts, "(none)")}

CANDIDATE RESUME EXCERPTS:
{_excerpt_block(resume_excerpts, "(none)")}

EXAMPLE QUESTIONS FROM THE QUESTION BANK (use their style and difficulty; adapt, don't copy):
{bank_block}

Rules:
- Ask only about skills, tools, topics, projects and experience that appear in the excerpts. Never invent a project, employer, technology or achievement for the candidate, and never state facts about the company.
- Do not say a question was "asked by" the company or in a previous year.
- Every question must include "based_on": the id of the single excerpt it comes from (for example "J2", "R1" or "B3").
- Mix question types: {", ".join(_TYPE_DESCRIPTIONS[t] for t in allowed)}.{no_code_rule}

Respond with ONLY a JSON object like:
{{"questions": [{{"question_text": "...", "question_type": "{allowed[0]}", "based_on": "J1"}}]}}
question_type must be exactly one of: {", ".join(allowed)}.
"""
    try:
        questions = _parse_questions(_chat_json(system_prompt, user_prompt))
    except LLMOutputError:
        return []
    return [q for q in questions if q["question_type"] in allowed][:num_questions]


# ---------------------------------------------------------------------------
# Per-answer evaluation
# ---------------------------------------------------------------------------

_CITATION_RE = re.compile(r"S\d+", re.IGNORECASE)


def _parse_flag(value) -> bool | None:
    """True/False for an explicit yes/no from the model, None if it didn't say."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "yes"):
            return True
        if lowered in ("false", "no"):
            return False
    return None


def evaluate_answer(
    question_text: str,
    question_type: str,
    answer_text: str,
    job_description: str,
    references: list[dict] | None = None,
) -> dict:
    """Return {score (0-10), feedback, strengths, weaknesses, sources_used, reference_relevant}.

    references: [{"id": "S1", "source": "...", "text": "..."}] - the only material the
    model may use to judge whether technical statements are correct. Pass an empty
    list when nothing relevant was found: the model is then told it has nothing to
    check facts against and must not rule on correctness.
    """
    references = references or []
    if not answer_text or not answer_text.strip():
        return {
            "score": 0,
            "feedback": "No answer was submitted for this question.",
            "strengths": [],
            "weaknesses": ["No response given"],
            "sources_used": [],
            "reference_relevant": None,
        }

    system_prompt = (
        "You are a fair, constructive technical interviewer scoring one answer. "
        "You judge only from the material you are given and never invent facts or quotes. "
        "You always respond with STRICT JSON only - no markdown fences, no commentary."
    )

    if references:
        reference_block = "\n".join(f"[{r['id']}] ({r['source']}) {r['text']}" for r in references)
        rules = f"""REFERENCE MATERIAL (your only source of truth for whether technical statements are correct):
{reference_block}

Rules:
- Judge technical correctness ONLY against the reference material. Do not use outside knowledge to call a statement right or wrong.
- If the candidate says something the reference does not cover, do not penalise or praise it; leave it out of the feedback or call it "not verified".
- When you rely on the reference, cite it right after the claim like [S1]. Cite only ids listed above - never invent a source or a quote.
- If none of the reference material actually relates to this question, set "reference_relevant" to false and judge only structure, clarity and completeness.
- Refer only to what is really in the candidate's answer; do not make up things they said."""
        json_shape = (
            '{"score": <0-10 number>, "feedback": "<2-3 sentences>", "strengths": ["..."], '
            '"weaknesses": ["..."], "sources_used": ["S1"], "reference_relevant": true}'
        )
    else:
        rules = """REFERENCE MATERIAL: none was found for this question.

Rules:
- You have nothing to check technical facts against, so do NOT say whether technical statements are right or wrong.
- Judge only how well the answer addresses what was asked: structure, clarity, completeness and relevance.
- State in the feedback that technical accuracy could not be checked against a reference.
- Refer only to what is really in the candidate's answer; do not make up things they said."""
        json_shape = (
            '{"score": <0-10 number>, "feedback": "<2-3 sentences>", '
            '"strengths": ["..."], "weaknesses": ["..."]}'
        )

    if question_type == "code":
        rules += (
            "\n- For code you may reason about what the code itself does, but never claim it was "
            "compiled, run or tested, and do not state its output as fact."
        )

    user_prompt = f"""
Role context (job description excerpt):
{job_description[:800]}

Question ({question_type}): {question_text}

Candidate's answer:
{answer_text[:3500]}

{rules}

Score the answer from 0-10 and explain briefly. Respond with ONLY JSON:
{json_shape}
"""
    data = _chat_json(system_prompt, user_prompt, temperature=0.2)
    if not isinstance(data, dict):
        raise LLMOutputError("The model's evaluation wasn't in the expected format. Try submitting again.")

    # Local models sometimes write the score as "7/10" - take the first number.
    match = re.search(r"\d+(?:\.\d+)?", str(data.get("score", "")))
    if not match:
        raise LLMOutputError("The model didn't give a numeric score. Try submitting again.")

    cited = data.get("sources_used")
    cited_ids = []
    for item in cited if isinstance(cited, list) else [cited]:
        found = _CITATION_RE.search(str(item or ""))
        if found:
            cited_ids.append(found.group().upper())

    return {
        "score": max(0.0, min(10.0, float(match.group()))),
        "feedback": str(data.get("feedback", "")).strip(),
        "strengths": _as_str_list(data.get("strengths")),
        "weaknesses": _as_str_list(data.get("weaknesses")),
        "sources_used": list(dict.fromkeys(cited_ids)),
        "reference_relevant": _parse_flag(data.get("reference_relevant")),
    }


# ---------------------------------------------------------------------------
# End-of-interview report
# ---------------------------------------------------------------------------

def generate_overall_report(qa_pairs: list[dict]) -> dict:
    """qa_pairs: [{question, question_type, answer, score, feedback}, ...]

    Returns {overall_score, positive_points: [...], negative_points: [...], summary}.
    The score is a plain average computed here, never by the model.
    """
    scored = [qa for qa in qa_pairs if qa.get("score") is not None]
    overall_score = (
        round(sum(qa["score"] for qa in scored) / len(scored), 1) if scored else 0.0
    )

    transcript = "\n\n".join(
        f"Q ({qa['question_type']}): {qa['question']}\n"
        f"A: {qa['answer'] or '(no answer)'}\n"
        f"Score: {qa.get('score', 'n/a')} - {qa.get('feedback', '')}"
        for qa in qa_pairs
    )

    system_prompt = (
        "You are summarizing a completed mock interview for the candidate, using only the "
        "transcript you are given. "
        "You always respond with STRICT JSON only - no markdown fences, no commentary."
    )
    user_prompt = f"""
Here is the full transcript with per-question scores and the feedback already given:

{transcript[:8000]}

Write an overall summary.
Rules:
- Use only what is in the transcript. Do not mention topics, skills or answers that are not in it, and do not invent quotes.
- Base every point on the scores and feedback above; where a question had no answer, say it was unanswered rather than guessing.
- Do not state a new technical fact that the feedback above did not contain.
- If there is little to go on, give fewer points rather than padding.

Respond with ONLY JSON:
{{
  "positive_points": ["up to 5 concrete things the candidate did well"],
  "negative_points": ["up to 5 concrete areas to improve"],
  "summary": "2-4 sentence overall summary in a supportive but honest tone"
}}
"""
    try:
        data = _chat_json(system_prompt, user_prompt, temperature=0.2)
    except LLMOutputError:
        data = None

    if not isinstance(data, dict):
        return {
            "overall_score": overall_score,
            "positive_points": [],
            "negative_points": [],
            "summary": "Report summary unavailable - raw evaluations are still saved per question.",
        }
    return {
        "overall_score": overall_score,
        "positive_points": _as_str_list(data.get("positive_points")),
        "negative_points": _as_str_list(data.get("negative_points")),
        "summary": str(data.get("summary", "")).strip(),
    }
