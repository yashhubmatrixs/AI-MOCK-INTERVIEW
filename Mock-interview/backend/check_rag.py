"""
Check that retrieval (RAG) works and see what it finds.

    python check_rag.py                      # run built-in sample questions
    python check_rag.py "Explain deadlock"   # see what a question of yours retrieves
    python check_rag.py --embeddings         # also build/use embeddings, stored in ChromaDB
                                             #   (needs the model: ollama pull nomic-embed-text)
    python check_rag.py --words "Scheduling APIs queries"   # see how words are lemmatized

Run from the backend/ folder with your environment active. No LLM call is made for the
keyword-only check, so it works even if Ollama isn't running.
"""

import sys

from services import rag_service, vector_store

# (question, a word that should appear in the topic of a relevant passage - or None when
# the knowledge base has nothing on it, so the right answer is "no reference").
PROBES = [
    ("Explain the difference between abstraction and encapsulation.", "OOP"),
    ("What is a deadlock and what are the conditions for it?", "Operating"),
    ("Explain ACID properties in a database.", "DBMS"),
    ("What is the difference between TCP and UDP?", "Network"),
    ("Given two strings, check if one is an anagram of the other.", "Data Structures"),
    ("What is overfitting and how do you reduce it?", "Machine Learning"),
    ("What is the GIL in Python?", "Python"),
    ("Tell me about a time you faced a conflict in your team.", "Behavioral"),
    ("Explain the CAP theorem with an example.", None),
    ("What are the key features of the Rust borrow checker?", None),
    ("What is the capital of France?", None),
]


def show(query: str, hits) -> None:
    print(f"\n  {query}")
    if not hits:
        print("    (nothing matched)")
    for h in hits:
        sim = f" similarity={h.similarity:.2f}" if h.similarity is not None else ""
        flag = "RELEVANT" if h.relevant else "weak    "
        print(f"    {flag} coverage={h.coverage:.2f}{sim}  {h.chunk.source}")


def main() -> int:
    if "--words" in sys.argv:
        text = " ".join(a for a in sys.argv[1:] if not a.startswith("--"))
        print("word -> lemma (what the search actually matches on)")
        for raw in text.split():
            print(f"  {raw} -> {' '.join(rag_service._terms(raw)) or '(ignored: filler word)'}")
        return 0

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    use_embeddings = "--embeddings" in sys.argv

    print(f"Knowledge base: {rag_service.describe()}")
    if use_embeddings:
        print("Building embeddings (first run can take a minute)...")
        print(f"Embeddings:     {rag_service.embedding_status(warm_up=True)}")
        try:
            model = rag_service.llm_service.embedding_model_name()
            print(f"ChromaDB:       {vector_store.count(model)} passages stored in {vector_store.store_path()}")
        except vector_store.VectorStoreError as exc:
            print(f"ChromaDB:       not usable - {exc}")

    if args:
        query = " ".join(args)
        show(query, rag_service.search_knowledge(query, k=5))
        return 0

    failures = 0
    for question, topic in PROBES:
        hits = rag_service.search_knowledge(question, k=3)
        relevant = [h for h in hits if h.relevant]
        if topic is None:
            ok = not relevant
        else:
            ok = any(topic.lower() in h.chunk.source.lower() for h in relevant)
        failures += not ok
        print(f"\n[{'PASS' if ok else 'FAIL'}] expected: {topic or 'no reference'}")
        show(question, hits)

    print(f"\n{len(PROBES) - failures}/{len(PROBES)} sample questions behaved as expected.")
    if rag_service.embedding_status().startswith("keyword search only - embeddings unavailable"):
        print("(Embeddings are optional. For better matching on rephrased questions: ollama pull nomic-embed-text)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
