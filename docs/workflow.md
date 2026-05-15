# Workflow

## Stage 1: Source Intake

Sources are short Markdown files under `examples\docs`. Each file includes front matter with:

- `source_id`
- `source_title`
- `source_url`
- `retrieved_at`

## Stage 2: Chunking

`scripts\ingest_documents.py` reads Markdown files, removes front matter, splits body text into small chunks, and writes `examples\index\chunks.json`.

## Stage 3: Indexing

`scripts\build_index.py` tokenizes chunks and builds a local keyword index. This is intentionally simple so the retrieval logic can be reviewed without a vector database.

## Stage 4: Retrieval

`scripts\query_rag.py` reads the query and scores chunks by keyword overlap. It selects top matching chunks and refuses to answer when no source is retrieved.

## Stage 5: Answer Formatting

The answer is written to `examples\sample_answer.md` with:

- source-grounded answer
- source list
- confidence level
- manual-review flag
- limitations
- legal information disclaimer

## Stage 6: Audit

`scripts\portfolio_audit.ps1` checks repository safety before publication.
