---
name: knowledge-indexing
description: Import selected official EU articles, clean and chunk provenance-preserving JSONL, encode with pretrained BGE and evaluate keyword, dense and hybrid retrieval. Use to build or audit this plugin's local knowledge index.
---

# Knowledge indexing

Resolve the plugin root two directories above this file. Read `knowledge/README.md`, `knowledge/chunk.schema.json` and `knowledge/official-sources.json` before running commands.

1. Confirm the authorized collection. For the supported public snapshot run `python knowledge/import_official.py --output output/<new-snapshot>`. Download is restricted to official hosts; the importer checks instrument identity, article IDs and text coverage. Do not bypass challenges or fabricate missing text.
2. Inspect `coverage.json` before indexing. Missing selected articles or unparsed content must fail the import. Preserve source URLs, CELEX, dates, original-publication version, download hashes and extraction coverage. `source_verified` means origin/extraction checked, not legal review.
3. Install `knowledge/requirements.txt` in an isolated Python environment. Initial model and source downloads need a network; model inference stays local. Run `python knowledge/pipeline.py build --language en --documents output/<snapshot>/documents.jsonl --index output/<snapshot>/index.json --cache-dir .cache/models`.
4. Use the pretrained BGE encoder for token embeddings, position embeddings, Transformer layers and pooling. Do not implement random vectors or token counts as semantic vectors. The tokenizer rejects inputs above 512 tokens. Model changes require a full rebuild; never mix embedding spaces.
5. Inspect chunk JSONL and the manifest. Complete cleaned selected articles remain in the local index for source review. Keep raw text, models, vectors and exports out of Git; commit only small sanitized evaluation records.
6. Run `knowledge/evaluate.py` with `knowledge/evaluation/official-cases.json`. Report keyword, dense and hybrid separately, including the negative-case denominator. This is an authored development set, not an independent legal benchmark. Preserve failed paraphrases and compare against keyword retrieval before claiming improvement.
7. If using PostgreSQL, set the local database URL according to the README. Validate transaction rollback, corpus isolation, instrument filtering before candidate limits, and actual HTTP/browser use. A running database process alone is not acceptance.

Fixtures under knowledge/examples are fictional and test pipeline mechanics. New real sources require provenance and scope review. Always preserve originals and prior snapshots, write to a fresh output location, and run the portfolio audit before publication.
