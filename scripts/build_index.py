from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
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
    "with",
}


def tokenize(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in STOPWORDS and len(token) > 1]


def load_chunks(path: Path) -> List[Dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return list(payload.get("chunks", []))
    if isinstance(payload, list):
        return payload
    raise ValueError("Unsupported chunks.json format")


def build_index(chunks: Iterable[Dict[str, str]]) -> Dict[str, object]:
    indexed_chunks = []
    inverted_index: Dict[str, List[str]] = defaultdict(list)

    for chunk in chunks:
        tokens = tokenize(chunk.get("text", ""))
        token_counts = Counter(tokens)
        chunk_id = chunk["chunk_id"]
        for token in sorted(token_counts):
            inverted_index[token].append(chunk_id)

        indexed_chunks.append(
            {
                **chunk,
                "tokens": sorted(token_counts),
                "token_counts": dict(sorted(token_counts.items())),
                "token_norm": round(math.sqrt(sum(count * count for count in token_counts.values())), 6),
            }
        )

    return {
        "created_at": date.today().isoformat(),
        "index_type": "keyword_overlap_v1",
        "chunk_count": len(indexed_chunks),
        "chunks": indexed_chunks,
        "inverted_index": dict(sorted(inverted_index.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a dependency-free keyword index for safe-demo chunks.")
    parser.add_argument("--chunks", required=True, type=Path, help="Input chunks.json path.")
    parser.add_argument("--output", required=True, type=Path, help="Output index.json path.")
    args = parser.parse_args()

    if not args.chunks.exists():
        raise SystemExit(f"Chunks file not found: {args.chunks}")

    index = build_index(load_chunks(args.chunks))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {index['chunk_count']} indexed chunks to {args.output}")


if __name__ == "__main__":
    main()
