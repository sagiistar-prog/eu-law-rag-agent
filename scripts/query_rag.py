from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "the",
    "this",
    "to",
    "what",
    "with",
}
HIGH_REVIEW_TERMS = {
    "law",
    "legal",
    "tariff",
    "customs",
    "classification",
    "compliance",
    "import",
    "export",
    "product",
    "safety",
}


def tokenize(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in STOPWORDS and len(token) > 1]


def load_index(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def score_chunk(query_counts: Counter, chunk: Dict[str, object]) -> float:
    chunk_counts = Counter(chunk.get("token_counts", {}))
    if not query_counts or not chunk_counts:
        return 0.0

    overlap = sum(min(query_counts[token], chunk_counts.get(token, 0)) for token in query_counts)
    query_norm = math.sqrt(sum(count * count for count in query_counts.values()))
    chunk_norm = float(chunk.get("token_norm") or 1.0)
    if query_norm == 0 or chunk_norm == 0:
        return 0.0
    return overlap / (query_norm * chunk_norm)


def retrieve(query: str, chunks: Iterable[Dict[str, object]], top_k: int = 3) -> List[Tuple[float, Dict[str, object]]]:
    query_counts = Counter(tokenize(query))
    scored = []
    for chunk in chunks:
        score = score_chunk(query_counts, chunk)
        if score > 0:
            scored.append((score, chunk))
    return sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]


def extract_evidence_sentences(query: str, chunks: List[Dict[str, object]], max_words_per_source: int = 80) -> List[str]:
    query_terms = set(tokenize(query))
    sentences: List[str] = []
    seen = set()
    used_words: Dict[str, int] = {}

    for chunk in chunks:
        text = str(chunk.get("text", ""))
        for sentence in SENTENCE_RE.split(text.replace("\n", " ")):
            cleaned = sentence.strip()
            if not cleaned or cleaned in seen:
                continue
            sentence_terms = set(tokenize(cleaned))
            if query_terms.intersection(sentence_terms):
                source_id = str(chunk.get("source_id", "unknown"))
                remaining = max_words_per_source - used_words.get(source_id, 0)
                if remaining <= 0:
                    continue
                words = cleaned.split()
                excerpt = " ".join(words[:remaining])
                if len(words) > remaining:
                    excerpt += " […]"
                sentences.append(excerpt)
                used_words[source_id] = used_words.get(source_id, 0) + min(len(words), remaining)
                seen.add(cleaned)
            if len(sentences) >= 4:
                return sentences

    return sentences


def confidence_label(results: List[Tuple[float, Dict[str, object]]]) -> str:
    if not results:
        return "none"
    top_score = results[0][0]
    if len(results) >= 2 and top_score >= 0.2:
        return "medium"
    return "low"


def needs_manual_review(query: str, chunks: Iterable[Dict[str, object]]) -> bool:
    combined = " ".join([query] + [str(chunk.get("text", "")) for chunk in chunks]).lower()
    terms = set(tokenize(combined))
    return bool(terms.intersection(HIGH_REVIEW_TERMS))


def format_source(score: float, chunk: Dict[str, object], manual_review_required: bool) -> str:
    source_confidence = "medium" if score >= 0.2 else "low"
    return "\n".join(
        [
            "  - source_id: " + str(chunk.get("source_id", "")),
            "    source_title: " + str(chunk.get("source_title", "")),
            "    source_url: " + str(chunk.get("source_url", "")),
            "    retrieved_at: " + str(chunk.get("retrieved_at", "")),
            "    chunk_id: " + str(chunk.get("chunk_id", "")),
            "    confidence: " + source_confidence,
            "    manual_review_required: " + str(manual_review_required).lower(),
        ]
    )


def format_refusal(query: str) -> str:
    return "\n".join(
        [
            "# RAG Answer",
            "",
            "answer: >",
            "  No source was retrieved for the query, so the system cannot provide a source-grounded answer. Please add relevant source material and run ingestion and indexing again.",
            "sources: []",
            "confidence: none",
            "manual_review_required: true",
            "limitations:",
            "  - No answer is provided without retrieved evidence.",
            "  - The query was: " + query.replace("\n", " ").strip(),
            "not_legal_advice: true",
            "not_legal_advice_statement: >",
            "  This output is legal information retrieval and source-grounded summarization only. It is not legal advice.",
            "generated_at: " + date.today().isoformat(),
            "",
        ]
    )


def format_answer(query: str, results: List[Tuple[float, Dict[str, object]]], max_words_per_source: int = 80) -> str:
    chunks = [chunk for _, chunk in results]
    manual_review_required = True  # Information retrieval never authorizes legal decisions.
    confidence = confidence_label(results)
    evidence_sentences = extract_evidence_sentences(query, chunks, max_words_per_source)

    if evidence_sentences:
        summary = " ".join(evidence_sentences)
    else:
        summary = "The retrieved sources are relevant, but the evidence is too limited for a detailed summary. Manual review is required."

    source_blocks = [format_source(score, chunk, manual_review_required) for score, chunk in results]

    return "\n".join(
        [
            "# RAG Answer",
            "",
            "answer: >",
            "  Based only on the retrieved safe-demo sources, " + summary,
            "sources:",
            *source_blocks,
            "confidence: " + confidence,
            "manual_review_required: " + str(manual_review_required).lower(),
            "limitations:",
            "  - This answer is generated from fictional short demo sources only.",
            "  - It does not verify current law, official tariff status, or market access requirements.",
            "  - AI inference is limited to summarizing the retrieved source text.",
            "not_legal_advice: true",
            "not_legal_advice_statement: >",
            "  This output is legal information retrieval and source-grounded summarization only. It is not legal advice.",
            "generated_at: " + date.today().isoformat(),
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the safe-demo RAG index and write a source-grounded answer.")
    parser.add_argument("--query", required=True, type=Path, help="Path to a Markdown query file.")
    parser.add_argument("--index", required=True, type=Path, help="Path to index.json.")
    parser.add_argument("--output", required=True, type=Path, help="Path to write sample_answer.md.")
    parser.add_argument("--rules", required=True, type=Path, help="Path to RAG rules YAML.")
    parser.add_argument("--dry-run", action="store_true", help="Use deterministic local answer formatting.")
    args = parser.parse_args()

    if not args.query.exists():
        raise SystemExit(f"Query file not found: {args.query}")
    if not args.index.exists():
        raise SystemExit(f"Index file not found: {args.index}")
    if not args.rules.exists():
        raise SystemExit(f"Rules file not found: {args.rules}")

    query = args.query.read_text(encoding="utf-8").strip()
    index = load_index(args.index)
    # Only supported controls are loaded; invalid limits fail clearly.
    text = args.rules.read_text(encoding="utf-8")
    match = re.search(r"^\s*max_words_per_source:\s*(\d+)\s*$", text, re.MULTILINE)
    if not match or not 1 <= int(match.group(1)) <= 500:
        raise ValueError("rules require max_words_per_source between 1 and 500")
    budget = int(match.group(1))
    results = retrieve(query, index.get("chunks", []))
    output = format_answer(query, results, budget) if results else format_refusal(query)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote answer to {args.output}")


if __name__ == "__main__":
    main()
