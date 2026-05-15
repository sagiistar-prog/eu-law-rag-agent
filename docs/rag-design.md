# RAG Design

## Design Goals

- Keep every answer source-grounded.
- Preserve source metadata through ingestion, indexing, retrieval, and answer generation.
- Refuse unsupported answers.
- Make high risk topics visible for human review.
- Keep the demo small enough for a public repository.

## Retrieval Model

The demo uses keyword overlap instead of embeddings. This keeps the project dependency-free while still showing the core RAG control loop:

1. Normalize query and chunk text.
2. Tokenize into comparable terms.
3. Score chunks by overlap.
4. Return the best source-grounded chunks.
5. Generate a constrained summary from retrieved evidence.

## Source Metadata Contract

Each chunk carries:

- `source_id`
- `source_title`
- `source_url`
- `retrieved_at`
- `chunk_id`
- `text`

The answer must carry the same source metadata forward.

## Refusal Rule

If retrieval returns no relevant chunk, the system must not answer from memory. It must request additional source material.

## Confidence

Confidence is based on retrieval coverage, source count, and score strength. It is not a legal certainty rating.
