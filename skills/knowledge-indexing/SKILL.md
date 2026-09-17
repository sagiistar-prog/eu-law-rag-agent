---
name: knowledge-indexing
description: Clean authorized source documents into provenance-preserving JSONL, encode them with local BGE and evaluate keyword, dense and hybrid retrieval. Use when building or reviewing this plugin's knowledge index.
---

# Knowledge indexing

Resolve the repository root two directories above this file. Read knowledge/README.md and knowledge/chunk.schema.json before work.

1. Confirm which user-provided or authorized documents belong to this task. Never scan unrelated folders. Preserve source ID, title, URL, retrieval date, section, page and review status.
2. Use knowledge/pipeline.py build to clean, chunk and embed. Install knowledge/requirements.txt in an isolated environment. Explain that initial model download uses the network; inference does not upload documents.
3. Use language en for the bundled example. A model change requires full rebuild. Token and position embeddings are internal to the pretrained encoder; do not substitute token counts or random vectors for semantic embeddings.
4. Run evaluate against a labeled set; report keyword, dense and hybrid separately. Record corpus/model versions. The included fictional set only verifies a small pipeline.
5. Search the index and return evidence with chunk IDs and source metadata. A nearest neighbor is only a candidate. Pending or unsupported sources cannot justify an answer.
6. When writing a synthesis, cite each claim, separate interpretation from quoted facts, and surface missing evidence. Do not infer medical/legal applicability or execute downstream decisions.

Write artifacts only to a fresh output/ directory; do not overwrite original documents or prior indexes. Keep raw corpora, vectors and models out of Git. Follow repository audit rules before publication.
