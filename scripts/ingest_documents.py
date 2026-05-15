from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

MAX_CHUNK_CHARS = 900


def parse_front_matter(text: str) -> Tuple[Dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text.strip()

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, text.strip()

    metadata: Dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")

    body = "\n".join(lines[end_index + 1 :]).strip()
    return metadata, body


def chunk_markdown(body: str, max_chars: int = MAX_CHUNK_CHARS) -> List[str]:
    paragraphs = [part.strip() for part in body.split("\n\n") if part.strip()]
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for paragraph in paragraphs:
        extra_len = len(paragraph) + (2 if current else 0)
        if current and current_len + extra_len > max_chars:
            chunks.append("\n\n".join(current))
            current = [paragraph]
            current_len = len(paragraph)
        else:
            current.append(paragraph)
            current_len += extra_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def ingest(input_dir: Path) -> List[Dict[str, str]]:
    markdown_files = sorted(input_dir.glob("*.md"))
    chunks: List[Dict[str, str]] = []

    for path in markdown_files:
        metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))
        source_id = metadata.get("source_id") or path.stem
        source_title = metadata.get("source_title") or path.stem.replace("_", " ").title()
        source_url = metadata.get("source_url") or "user-provided://local-demo"
        retrieved_at = metadata.get("retrieved_at") or date.today().isoformat()

        for number, chunk_text in enumerate(chunk_markdown(body), start=1):
            chunks.append(
                {
                    "source_id": source_id,
                    "source_title": source_title,
                    "source_url": source_url,
                    "retrieved_at": retrieved_at,
                    "chunk_id": f"{source_id}::chunk-{number:03d}",
                    "text": chunk_text,
                }
            )

    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest safe-demo Markdown documents into source-linked chunks.")
    parser.add_argument("--input", required=True, type=Path, help="Directory containing Markdown documents.")
    parser.add_argument("--output", required=True, type=Path, help="Output chunks.json path.")
    args = parser.parse_args()

    if not args.input.exists() or not args.input.is_dir():
        raise SystemExit(f"Input directory not found: {args.input}")

    chunks = ingest(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": date.today().isoformat(),
        "chunk_count": len(chunks),
        "chunks": chunks,
    }
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(chunks)} chunks to {args.output}")


if __name__ == "__main__":
    main()
