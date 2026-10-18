"""
Retrieval for the interview engine - the "R" in RAG.

Instead of letting the model answer from memory, the app first looks things up and
hands the model only the passages it is allowed to rely on:

  * knowledge base  - notes in backend/data/knowledge (OOP, DBMS, OS, ML, ...). Used to
                      check technical answers. Drop your own .md / .txt / .pdf notes in
                      that folder and restart to add more.
  * job description - split into chunks (J1, J2, ...)       } used to ground the
  * resume          - split into chunks (R1, R2, ...)       } generated questions
  * question bank   - data/question_bank.json (B1, B2, ...) }

Search is BM25 keyword search over LEMMATIZED words (no stemming anywhere): "scheduling",
"scheduled" and "schedules" are all reduced to the real word "schedule", "queries" to
"query", "was" to "be". If an embedding model is available it is blended in for better
recall on paraphrased questions: Ollama's 'nomic-embed-text' or OpenAI's
'text-embedding-3-small'. The knowledge-base vectors are stored on disk in ChromaDB
(backend/data/chroma, see vector_store.py), not held in memory. If embeddings or ChromaDB
aren't available (model not pulled, Ollama down) search quietly stays keyword-only.

A hit is only called "relevant" when it clears a threshold. Below that, callers are
told there is NO reference - and the model is told so too, instead of being left to
fill the gap with something plausible.
"""

from __future__ import annotations

import math
import os
import re
import threading
import time
from collections import Counter
from dataclasses import dataclass, replace
from functools import lru_cache
from typing import NamedTuple
from pathlib import Path
from typing import Optional, Sequence

from dotenv import load_dotenv

from services import llm_service, vector_store

try:
    import simplemma
except ImportError as _exc:  # pragma: no cover - only when requirements aren't installed
    raise ImportError(
        "The 'simplemma' package (the lemmatizer used for search) isn't installed. "
        "Run: pip install -r requirements.txt"
    ) from _exc

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge"

KB_CHUNK_CHARS = 700      # longest knowledge-base passage handed to the model
USER_CHUNK_CHARS = 450    # chunk size for the job description / resume


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Chunk:
    id: str       # label the model and the user see, e.g. "S1", "J2", "R1", "B3"
    text: str
    source: str   # where it came from, e.g. "OOP > Abstraction" or "Job description"
    kind: str     # knowledge | jd | resume | bank


@dataclass
class Hit:
    chunk: Chunk
    score: float                    # ranking score (higher = better)
    coverage: float                 # share of the query's information weight found in the chunk
    similarity: Optional[float]     # cosine similarity if embeddings were used
    relevant: bool                  # cleared the relevance threshold


# ---------------------------------------------------------------------------
# Text processing
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#.]*")

_STOP = frozenset("""
a about above after again all also an and any are as at be been being below between both but by can
could did do does doing down during each either else few for from further get give given had has have
having he her here hers him his how i if in into is it its itself just let like make many may me more
most my no nor not of off on once one only or other our ours out over own same she should so some such
than that the their theirs them then there these they this those through to too under until up us use
used using very was we were what when where which while who whom why will with would you your yours
explain describe difference differences tell example examples briefly please
add downside upside need want write implement find check determine complete debug provided partially written
""".split())

# Lemmatization, not stemming. A lemmatizer looks each word up in a dictionary and returns
# the real base form ("scheduling" -> "schedule", "queries" -> "query", "indices" ->
# "index", "overridden" -> "override"); a stemmer just chops letters off and leaves
# non-words like "schedul". simplemma is a pure-Python dictionary lookup: no model, no
# download, no extra setup.
#
# Tech vocabulary is not in an everyday-English dictionary, so a few words are handled
# by hand. The same function runs on the notes and on the question, so even an odd
# lemma still matches itself - these only keep the common ones tidy.
_ALIASES = {
    "oops": "oop", "apis": "api", "llms": "llm", "cnns": "cnn", "rnns": "rnn", "gans": "gan",
    "ides": "ide", "urls": "url", "dbs": "db", "gpus": "gpu", "cpus": "cpu", "vms": "vm",
    "jwts": "jwt", "sdks": "sdk", "orms": "orm", "csvs": "csv", "pdfs": "pdf", "kpis": "kpi",
    # The dictionary would turn these into "millileter", "cor", "aw" and "panda".
    "ml": "ml", "cors": "cors", "aws": "aws", "pandas": "pandas",
}


@lru_cache(maxsize=65536)
def _lemma(token: str) -> str:
    """Base form of one lower-case word."""
    alias = _ALIASES.get(token)
    if alias is not None:
        return alias
    if not token.isalpha():
        return token  # c++, c#, node.js, bm25, s3 ... are already names, not words
    # Run it until the word stops changing. The dictionary has no part-of-speech, so one
    # pass can leave "meetings" -> "meeting" while a plain "meeting" -> "meet"; a second pass
    # makes both end at the same word and the question matches the notes.
    lemma = token
    for _ in range(3):
        nxt = simplemma.lemmatize(lemma, lang="en").lower()
        if nxt == lemma:
            break
        lemma = nxt
    return lemma


def _terms(text: str) -> list[str]:
    out = []
    for raw in _TOKEN_RE.findall((text or "").lower()):
        raw = raw.rstrip(".")
        if not raw or raw in _STOP:
            continue
        if len(raw) == 1 and raw not in ("c", "r"):
            continue
        lemma = _lemma(raw)
        # "was" -> "be", "using" -> "use": drop anything that becomes a stop word.
        if lemma in _STOP:
            continue
        out.append(lemma)
    return out


# Words so common in job descriptions that sharing one proves nothing about a question.
_GENERIC = frozenset(_lemma(w) for w in """
experience years year work working role team skill skills strong knowledge ability good candidate
required requirement requirements responsibility responsibilities develop development project
projects company job position understanding include including preferred plus must should ensure
across within various related relevant etc excellent communication
""".split())


def _support_terms(text: str) -> set[str]:
    return {t for t in _terms(text) if t not in _GENERIC}


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def _split_long(line: str, max_chars: int) -> list[str]:
    """Break one very long line at sentence boundaries, then at spaces."""
    out: list[str] = []
    cur = ""
    for sentence in re.split(r"(?<=[.!?])\s+", line):
        while len(sentence) > max_chars:
            cut = sentence.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            if cur:
                out.append(cur)
                cur = ""
            out.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if cur and len(cur) + 1 + len(sentence) > max_chars:
            out.append(cur)
            cur = sentence
        else:
            cur = f"{cur} {sentence}".strip()
    if cur:
        out.append(cur)
    return out


def _pack(lines: Sequence[str], max_chars: int) -> list[str]:
    """Merge consecutive lines into chunks of at most max_chars (long lines are split)."""
    units: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        units.extend([line] if len(line) <= max_chars else _split_long(line, max_chars))
    chunks: list[str] = []
    cur = ""
    for unit in units:
        if cur and len(cur) + 1 + len(unit) > max_chars:
            chunks.append(cur)
            cur = unit
        else:
            cur = f"{cur}\n{unit}" if cur else unit
    if cur:
        chunks.append(cur)
    return chunks


def chunk_text(text: str, *, kind: str, source: str, prefix: str,
               max_chars: int = USER_CHUNK_CHARS) -> list[Chunk]:
    """Split free text (a job description, a resume) into labelled chunks."""
    pieces = _pack((text or "").splitlines(), max_chars)
    return [Chunk(f"{prefix}{i}", piece, source, kind) for i, piece in enumerate(pieces, start=1)]


# ---------------------------------------------------------------------------
# BM25 index
# ---------------------------------------------------------------------------

_K1, _B = 1.5, 0.75


class LexRow(NamedTuple):
    index: int         # position of the chunk in the index
    score: float       # BM25
    coverage: float    # share of the query's IDF weight the chunk contains
    rarity: float      # matched IDF relative to the rarest possible word (0-1), so it doesn't depend on corpus size
    terms: int         # how many distinct query terms matched
    query_terms: int   # how many distinct terms the query has
    unseen_share: float  # share of the query's IDF weight made of words the corpus never uses


class Index:
    """BM25 over a list of chunks. Besides the score it reports 'coverage': the share of
    the query's information weight (sum of IDF) that the chunk actually contains. A
    question about something the corpus has never mentioned gets low coverage however
    well it matches on filler words - which is how 'no reference' gets detected."""

    def __init__(self, chunks: Sequence[Chunk]):
        self.chunks = list(chunks)
        self._tf = [Counter(_terms(f"{c.source} {c.text}")) for c in self.chunks]
        self._len = [sum(tf.values()) for tf in self._tf]
        n = len(self.chunks)
        self._avg = (sum(self._len) / n) if n else 1.0
        df: Counter = Counter()
        for tf in self._tf:
            df.update(tf.keys())
        self._idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
        self._unseen_idf = math.log(1 + (n + 0.5) / 0.5)

    def lexical(self, query: str) -> list[LexRow]:
        """One row for every chunk sharing at least one term with the query."""
        q_terms = list(dict.fromkeys(_terms(query)))
        if not q_terms or not self.chunks:
            return []
        total = sum(self._idf.get(t, self._unseen_idf) for t in q_terms)
        unseen_share = sum(self._unseen_idf for t in q_terms if t not in self._idf) / total
        rows = []
        for i, tf in enumerate(self._tf):
            norm = _K1 * (1 - _B + _B * self._len[i] / (self._avg or 1.0))
            score = matched = 0.0
            hits = 0
            for t in q_terms:
                f = tf.get(t)
                if not f:
                    continue
                idf = self._idf[t]
                score += idf * f * (_K1 + 1) / (f + norm)
                matched += idf
                hits += 1
            if hits:
                rows.append(LexRow(i, score, matched / total, matched / self._unseen_idf, hits, len(q_terms), unseen_share))
        return rows


# ---------------------------------------------------------------------------
# Thresholds (all overridable in backend/.env)
# ---------------------------------------------------------------------------

def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    try:
        return float(raw) if raw not in (None, "") else default
    except ValueError:
        return default


def _min_coverage() -> float:
    return _float_env("RAG_MIN_COVERAGE", 0.35)


def _min_rarity() -> float:
    return _float_env("RAG_MIN_RARITY", 0.4)


def _min_similarity() -> float:
    # Cosine scores live on different scales per embedding model.
    default = 0.70 if llm_service.provider_name() == "ollama" else 0.45
    return _float_env("RAG_MIN_SIMILARITY", default)


def _lexically_relevant(row: Optional[LexRow]) -> bool:
    if row is None or row.coverage < _min_coverage() or row.rarity < _min_rarity():
        return False
    # A short question where a big part of what's being asked is a word the knowledge
    # base never mentions ("CAP theorem", "Redis vs Memcached") is about something we
    # have no notes on, even if one word happens to match a passage on another topic.
    if row.query_terms <= 4 and row.unseen_share >= 0.4:
        return False
    return True


# ---------------------------------------------------------------------------
# Knowledge base
# ---------------------------------------------------------------------------

_kb_lock = threading.Lock()
_kb_index: Optional[Index] = None
_kb_files = 0


def _pretty(stem: str) -> str:
    return stem.replace("_", " ").replace("-", " ").strip().title()


def _load_markdown(path: Path) -> list[tuple[str, str]]:
    """Return [(source_label, text)] - one entry per '## ' section."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    title = _pretty(path.stem)
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip() or title
            break
    sections: list[tuple[str, list[str]]] = []
    for line in lines:
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif line.startswith("# "):
            continue
        elif sections:
            sections[-1][1].append(line)
        elif line.strip():
            sections.append((title, [line]))
    out = []
    for heading, body in sections:
        label = title if heading == title else f"{title} > {heading}"
        for piece in _pack(body, KB_CHUNK_CHARS):
            out.append((label, piece))
    return out


def _load_plain(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [(_pretty(path.stem), piece) for piece in _pack(text.splitlines(), KB_CHUNK_CHARS)]


def _load_pdf(path: Path) -> list[tuple[str, str]]:
    import pdfplumber  # already a dependency (resume parsing)

    out = []
    with pdfplumber.open(str(path)) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            for piece in _pack(text.splitlines(), KB_CHUNK_CHARS):
                out.append((f"{_pretty(path.stem)} (page {number})", piece))
    return out


def _load_knowledge() -> tuple[list[Chunk], int]:
    entries: list[tuple[str, str]] = []
    files = 0
    if KNOWLEDGE_DIR.is_dir():
        for path in sorted(KNOWLEDGE_DIR.rglob("*")):
            if not path.is_file() or path.name.startswith(("_", ".")) or path.stem.lower() == "readme":
                continue
            try:
                if path.suffix.lower() == ".md":
                    entries.extend(_load_markdown(path))
                elif path.suffix.lower() == ".txt":
                    entries.extend(_load_plain(path))
                elif path.suffix.lower() == ".pdf":
                    entries.extend(_load_pdf(path))
                else:
                    continue
                files += 1
            except Exception as exc:  # one unreadable file must not take the app down
                print(f"[rag] skipped {path.name}: {exc}")
    chunks = [Chunk(f"K{i}", text, source, "knowledge") for i, (source, text) in enumerate(entries, start=1)]
    return chunks, files


def knowledge_index() -> Index:
    global _kb_index, _kb_files
    with _kb_lock:
        if _kb_index is None:
            chunks, _kb_files = _load_knowledge()
            _kb_index = Index(chunks)
        return _kb_index


def reload_knowledge() -> None:
    """Re-read data/knowledge. The vectors in ChromaDB are kept: on the next search only
    passages that are new or edited get embedded, and removed ones are deleted."""
    global _kb_index
    with _kb_lock:
        _kb_index = None
    with _emb_lock:
        _emb.update(ready_for=None, keys={}, disabled_until=0.0)


# ---------------------------------------------------------------------------
# Embeddings (optional) - kept on disk in ChromaDB, not in memory
# ---------------------------------------------------------------------------
#
# What lives where:
#   RAM     the BM25 index and the Chunk objects. They are rebuilt from the notes on
#           every start (milliseconds, no model involved).
#   ChromaDB  each passage's text + its embedding vector (backend/data/chroma). Only
#           built once per passage: unchanged passages are never embedded again.

_emb_lock = threading.RLock()
_emb: dict = {
    "ready_for": None,   # (model, id(index)) that the Chroma collection is up to date for
    "keys": {},          # Chroma key -> position of that passage in the index
    "disabled_until": 0.0,
    "last_error": None,
    "warned": set(),
}
_RETRY_AFTER_SECONDS = 300
_NEAREST = 20  # how many closest passages ChromaDB returns per question


def _embeddings_enabled() -> bool:
    return os.getenv("RAG_EMBEDDINGS", "auto").strip().lower() not in ("off", "false", "0", "no")


def _embed_text(chunk: Chunk) -> str:
    return f"{chunk.source}\n{chunk.text}"


def _note_embedding_failure(exc: Exception) -> None:
    _emb.update(ready_for=None, keys={}, disabled_until=time.time() + _RETRY_AFTER_SECONDS, last_error=str(exc))
    if str(exc) not in _emb["warned"]:
        _emb["warned"].add(str(exc))
        print(f"[rag] embeddings unavailable - using keyword search only. {exc}")


def _kb_store_ready(idx: Index) -> Optional[tuple[str, dict[str, int]]]:
    """Make sure ChromaDB holds an embedding for every knowledge passage.

    Returns (model, {chroma key: position in idx}), or None if embeddings or ChromaDB
    aren't usable right now (callers then search by keyword only)."""
    if not _embeddings_enabled() or not idx.chunks:
        return None
    with _emb_lock:
        model = llm_service.embedding_model_name()
        if _emb["ready_for"] == (model, id(idx)):
            return model, _emb["keys"]
        if time.time() < _emb["disabled_until"]:
            return None
        try:
            entries = []
            keys: dict[str, int] = {}
            for position, chunk in enumerate(idx.chunks):
                text = _embed_text(chunk)
                entry = vector_store.Entry(
                    key=vector_store.entry_key(model, text),
                    text=text,
                    document=chunk.text,
                    metadata={"source": chunk.source, "kind": chunk.kind},
                )
                entries.append(entry)
                keys.setdefault(entry.key, position)
            vector_store.sync(model, entries, lambda texts: llm_service.embed_texts(texts, role="document"))
            _emb.update(ready_for=(model, id(idx)), keys=keys, last_error=None)
            return model, keys
        except (llm_service.LLMError, vector_store.VectorStoreError) as exc:
            _note_embedding_failure(exc)
            return None


def embedding_status(warm_up: bool = False) -> str:
    """One line for logs / check_rag.py. warm_up=True fills ChromaDB now."""
    if not _embeddings_enabled():
        return "keyword search only (RAG_EMBEDDINGS=off)"
    if warm_up:
        with _emb_lock:
            _emb["disabled_until"] = 0.0
        _kb_store_ready(knowledge_index())
    with _emb_lock:
        if _emb["ready_for"] is not None:
            return (
                f"keyword + embeddings ({llm_service.embedding_model_name()}), "
                f"vectors stored in ChromaDB at {vector_store.store_path()}"
            )
        if _emb["last_error"]:
            return f"keyword search only - embeddings unavailable: {_emb['last_error']}"
    return f"keyword search; embeddings ({llm_service.embedding_model_name()}) are tried on first use"


def describe() -> str:
    idx = knowledge_index()
    sources = len({c.source.split(" > ")[0] for c in idx.chunks})
    return f"{len(idx.chunks)} knowledge passages from {sources} topics in data/knowledge; {embedding_status()}"


# ---------------------------------------------------------------------------
# Searching the knowledge base
# ---------------------------------------------------------------------------

def search_knowledge(query: str, k: int = 3) -> list[Hit]:
    """Top-k knowledge passages for a query, relevant ones first. Check Hit.relevant:
    when nothing is relevant the caller must say there's no reference."""
    idx = knowledge_index()
    if not idx.chunks or not (query or "").strip():
        return []

    lex = {row.index: row for row in idx.lexical(query)}

    # Meaning-based side: ChromaDB returns the closest passages to the question's vector.
    sims: dict[int, float] = {}
    ready = _kb_store_ready(idx)
    if ready is not None:
        model, keys = ready
        try:
            qvec = llm_service.embed_texts([query], role="query")[0]
            for key, similarity in vector_store.query(model, qvec, _NEAREST):
                position = keys.get(key)
                if position is not None:
                    sims[position] = similarity
        except (llm_service.LLMError, vector_store.VectorStoreError) as exc:
            _note_embedding_failure(exc)
            sims = {}

    lex_rank = {row.index: r for r, row in enumerate(sorted(lex.values(), key=lambda row: -row.score))}
    sim_rank = {i: r for r, i in enumerate(sorted(sims, key=lambda i: -sims[i]))}

    lexical_ok = {i for i, row in lex.items() if _lexically_relevant(row)}
    best_coverage = max((lex[i].coverage for i in lexical_ok), default=0.0)

    hits: list[Hit] = []
    for i in set(lex_rank) | set(sim_rank):
        row = lex.get(i)
        coverage = row.coverage if row else 0.0
        sim = sims.get(i)
        fused = (1 / (60 + lex_rank[i]) if i in lex_rank else 0.0) + (1 / (60 + sim_rank[i]) if i in sim_rank else 0.0)
        # Keyword matches must also be close to the best keyword match: this drops the
        # tail of passages that merely share one or two words with a good answer.
        keyword_ok = i in lexical_ok and coverage >= 0.5 * best_coverage
        relevant = keyword_ok or (sim is not None and sim >= _min_similarity())
        hits.append(Hit(idx.chunks[i], fused, coverage, sim, relevant))

    hits.sort(key=lambda h: (h.relevant, h.score), reverse=True)
    return hits[:k]


def relabel(hits: Sequence[Hit], prefix: str = "S") -> list[Chunk]:
    """Give the chosen passages short per-request labels (S1, S2, ...) for the prompt."""
    return [replace(h.chunk, id=f"{prefix}{n}") for n, h in enumerate(hits, start=1)]


# ---------------------------------------------------------------------------
# Fitting long inputs into the model's context window
# ---------------------------------------------------------------------------

def select_within_budget(chunks: Sequence[Chunk], query: str, budget_chars: int) -> list[Chunk]:
    """Keep everything if it fits. Otherwise keep the chunks most relevant to `query`
    until the budget is used, and return them in their original order - so nothing is
    silently cut off from the end the way plain truncation would do."""
    chunks = list(chunks)
    if sum(len(c.text) for c in chunks) <= budget_chars:
        return chunks
    scores = {row.index: row.score for row in Index(chunks).lexical(query)}
    order = sorted(range(len(chunks)), key=lambda i: (-scores.get(i, 0.0), i))
    kept, used = [], 0
    for i in order:
        size = len(chunks[i].text)
        if used + size <= budget_chars:
            kept.append(i)
            used += size
    return [chunks[i] for i in sorted(kept)]


# ---------------------------------------------------------------------------
# Checking where a generated question came from
# ---------------------------------------------------------------------------

def _normalise_label(label) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", str(label or "")).upper()


def attribute_question(question_text: str, chunks: Sequence[Chunk], cited: object = None) -> Optional[Chunk]:
    """Find the passage a question is really based on, or None.

    The model's own claim ('based_on': 'J2') is accepted only if that passage exists
    AND shares a meaningful term with the question. Otherwise the best-matching
    passage is found by search. If nothing supports the question it is reported as
    unsourced rather than being presented as grounded."""
    q_support = _support_terms(question_text)
    if not q_support:
        return None

    by_id = {_normalise_label(c.id): c for c in chunks}
    claimed = by_id.get(_normalise_label(cited))
    if claimed and q_support & _support_terms(f"{claimed.source} {claimed.text}"):
        return claimed

    candidates = [c for c in chunks if q_support & _support_terms(c.text)]
    if not candidates:
        return None
    ranked = Index(candidates).lexical(question_text)
    if not ranked:
        return None
    best = max(ranked, key=lambda row: row.score)
    return candidates[best.index]
