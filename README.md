# EU Law RAG Agent

EU Law RAG Agent is a portfolio-safe Retrieval-Augmented Generation prototype for source-grounded research over European legal, tariff, product compliance, and public policy materials. It imports short Markdown sources, chunks them, builds a lightweight local keyword index, retrieves evidence, and produces a citation-first summary with confidence and manual-review flags.

This repository is a public demonstration. It contains no private company materials, no client materials, no partner materials, and no internal project documents.

## Interviewer 30-Second Version

EU Law RAG Agent shows how I would design a compliance-focused RAG assistant where every answer must be traceable to a source. The demo covers ingestion, chunking, indexing, retrieval, answer formatting, refusal when no source is found, confidence scoring, and manual review for legal or commercial decisions. It is intentionally lightweight: no vector database is required, so the workflow can be reviewed and run locally on Windows.

## What Problem It Solves

Legal and compliance research often fails when notes, public guidance, tariff explanations, and policy excerpts are scattered across documents. This project demonstrates a controlled retrieval layer that:

- keeps each answer tied to source metadata
- refuses unsupported answers
- separates source text from AI inference
- flags legal, compliance, tariff, and commercial decision points for human review
- avoids mixing portfolio examples with private or confidential material

## Why RAG Fits Regulation And Compliance Materials

RAG is useful for regulatory and compliance work because the answer should be grounded in retrieved evidence, not model memory. In this project, the agent stores source metadata at chunk level, retrieves only relevant chunks, and includes `source_id`, `source_title`, `source_url`, `retrieved_at`, `confidence`, and `manual_review_required` in the output.

## Inputs And Outputs

Inputs:

- short Markdown documents under `examples\docs`
- source metadata in front matter
- a user question in `examples\sample_query.md`
- rules in `configs\rag_rules.yaml` and `configs\source_policy.yaml`

Outputs:

- `examples\index\chunks.json` from ingestion
- `examples\index\index.json` from index building
- `examples\sample_answer.md` from retrieval and answer formatting

Each answer must include:

- `answer`
- `sources`
- `confidence`
- `manual_review_required`
- `limitations`
- `not_legal_advice`

## Workflow Stages

1. Ingest Markdown demo documents.
2. Parse source metadata.
3. Split documents into source-linked chunks.
4. Build a simple local keyword index.
5. Retrieve relevant chunks for the query.
6. Generate a source-grounded summary.
7. Attach source metadata, confidence, limitations, and manual-review flags.
8. Refuse to answer if no source is found.

## Safe Demo

Standard commands:

```powershell
python scripts\ingest_documents.py --input examples\docs --output examples\index\chunks.json
python scripts\build_index.py --chunks examples\index\chunks.json --output examples\index\index.json
python scripts\query_rag.py --query examples\sample_query.md --index examples\index\index.json --output examples\sample_answer.md --rules configs\rag_rules.yaml --dry-run
```

Windows launcher fallback:

```powershell
py -3 scripts\ingest_documents.py --input examples\docs --output examples\index\chunks.json
py -3 scripts\build_index.py --chunks examples\index\chunks.json --output examples\index\index.json
py -3 scripts\query_rag.py --query examples\sample_query.md --index examples\index\index.json --output examples\sample_answer.md --rules configs\rag_rules.yaml --dry-run
```

Portfolio audit:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\portfolio_audit.ps1
```

## Legal Boundary

This project provides legal information retrieval and source-grounded summaries only. It does not provide legal advice, legal opinions, or professional services. Any legal, tariff, product compliance, import, export, or commercial decision must be reviewed by a qualified human professional.

## Public Repository Privacy Statement

This repository is designed for public portfolio use. It does not contain real commercial documents, client records, partner records, internal paths, private policies, private datasets, or non-public operating details. The examples are short, fictional, and intentionally safe.

## Repository Layout

```text
README.md
AGENTS.md
configs/
docs/
examples/
scripts/
skills/
```
