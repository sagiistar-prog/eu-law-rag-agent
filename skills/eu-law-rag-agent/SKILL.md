---
name: eu-law-rag-agent
description: Retrieve and synthesize source-grounded legal research evidence using local BGE embeddings, BM25 and hybrid retrieval. Use to prepare citation-linked evidence for human review, not legal advice.
---

# EU Law RAG Agent Skill

Use this skill to prepare a source-linked evidence brief for a legal researcher who needs to verify a question against an authorized document collection.

## Purpose

Maintain a public, source-grounded RAG demo for European legal, tariff, product compliance, and public policy materials.

## Required Behavior

- Work only inside this repository.
- Use only short, fictional, sanitized examples.
- Preserve source metadata through all stages.
- Refuse unsupported answers.
- Label AI inference.
- Include confidence and manual-review fields in every answer.
- State that outputs are legal information only and not legal advice.

## Primary workflow

1. Confirm the research question, jurisdiction, relevant date and authorized source set. Record missing context instead of inventing it. This repository's bundled fixtures are fictional and cannot answer real legal questions.
2. Read `../knowledge-indexing/SKILL.md` and the repository's `knowledge/README.md`. Clean and structure the selected sources as JSONL, retaining source URLs, collection dates, section/page and review status.
3. Install both `requirements-plugin.txt` and `knowledge/requirements.txt` in an isolated environment. The primary mode executes the pretrained English BGE encoder, BM25 and RRF locally. Token and positional representations are internal model steps, not hand-written vectors.
4. Pass the JSON contract to `scripts/plugin_run.py`. Use `examples/hybrid-input.json` for a real embedding smoke run. The result includes evidence excerpts, source identifiers, warnings and review status. If the model is unavailable, report that failure; do not silently substitute keyword retrieval.
5. Present the question, supported evidence, unresolved points and next verification step. If drafting a synthesis with the host model, cite each supported claim by chunk ID and distinguish inference from source text. Do not turn similarity into a calibrated confidence percentage.
6. Evaluate against labeled questions and no-answer cases before expanding scope. Preserve the corpus/model manifest for reproducibility. Run the portfolio audit before publication.

## Legacy keyword baseline

These commands remain available for comparison and do not execute embeddings. The explicit keyword plugin fixture is `examples/plugin-input.json`.

```powershell
py -3 scripts\ingest_documents.py --input examples\docs --output examples\index\chunks.json
py -3 scripts\build_index.py --chunks examples\index\chunks.json --output examples\index\index.json
py -3 scripts\query_rag.py --query examples\sample_query.md --index examples\index\index.json --output examples\sample_answer.md --rules configs\rag_rules.yaml --dry-run
powershell -ExecutionPolicy Bypass -File scripts\portfolio_audit.ps1
```

## Publication Rule

Do not commit or push when the portfolio audit fails.

## Versioned plugin interface

Use the repository root as the working directory. For an installed plugin, resolve the root as two directories above this SKILL.md; never assume the user's project contains the bundled scripts.

1. Read `schemas/input.schema.json` before constructing input. Use `examples/plugin-input.json` for an offline demonstration.
2. Install `requirements-plugin.txt` into the user's chosen Python environment when needed.
3. Run `python scripts/plugin_run.py --input examples/plugin-input.json` from the plugin root. For user text, pass a JSON object through stdin; do not interpolate it into a shell command.
4. Parse stdout as one JSON object; exit 0 means success, exit 2 means an input/output/dependency error. Show the error and preserve the input rather than retrying indefinitely.
5. Present the Markdown result and material warnings. When the user asks to save artifacts, add `--output-dir output/<new-run-name>`. This creates files; an existing directory is never overwritten.

The plugin does not grant permission to read unrelated files, publish content, run rendering or access accounts. The original CLI remains available. See `docs/plugin.md` for the capability boundary and the structured error contract.
