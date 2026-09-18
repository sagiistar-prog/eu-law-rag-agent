---
name: eu-law-rag-agent
description: Import selected official EU publication articles and prepare citation-linked source reviews using local BGE, hybrid retrieval and full-article verification. Use for evidence gathering, not current-law verdicts or legal advice.
---

# EU law source review

Resolve this plugin root two directories above this file. Work only inside it; never scan personal folders. The user supplies the question and authorizes the source collection. Bundled examples remain short and fictional; the official importer downloads selected public articles to local ignored output only.

## User task

Help a researcher locate an original provision, inspect its conditions, and hand a reviewer an evidence packet with explicit unresolved questions. A fluent answer alone does not complete this task.

## Workflow

1. Record the question, instrument, relevant date and scope. The official collection contains 30 selected original Official Journal articles across GDPR, DSA, DMA and AI Act. It does not establish current law or cover tariffs, case law or national implementation.
2. Read `../knowledge-indexing/SKILL.md` and the root `knowledge/README.md`. Build a versioned index once; reuse it for subsequent research. Never claim invented or keyword-only vectors are embeddings.
3. Read `schemas/research-input.schema.json`. Save the query as JSON under a fresh local output directory, or use the bundled `examples/research-request.json`. Do not interpolate user text into a shell command.
4. Run `python knowledge/research.py --index output/<snapshot>/index.json --request output/<request>/request.json --output output/<new-review> --cache-dir .cache/models` from the plugin root. The destination must be new. Parse `evidence.json` using `schemas/evidence-review.schema.json`; `review.md` is the human handoff. A nonzero exit means failure, never a completed review.
5. Inspect the complete selected article through the local web workbench or the official source URL. `source_verified` confirms origin/extraction only. It does not imply expert review, current applicability or that every returned passage answers the question.
6. Present supported extracts, version scope and unresolved points. Preserve source_id, source_title, source_url, retrieved_at, chunk_id, corpus_sha256, confidence and manual_review_required. Confidence is `unrated`. A score is not a probability of legal correctness.
7. Treat `review_candidates` as leads for manual review, never supporting evidence. When `insufficient_evidence` is returned, explain the next verification step. If the host writes a synthesis, attach a supporting chunk ID to every factual claim and label inference. Never fill gaps from model memory or issue a legal verdict.

## Failure and privacy

Preserve the question on model, network or database failure. Report the failure without silently switching retrieval mode. Indexes, complete article text, queries and exported reviews stay local and untracked. The plugin does not grant permission to read accounts or publish user material.

## Other interfaces

The workbench starts with `python knowledge/server.py --language en --index output/<snapshot>/index.json --cache-dir .cache/models --port 8892`. Default storage is local JSON; the optional database contract is documented in the knowledge README.

`scripts/plugin_run.py` and `schemas/input.schema.json` retain the short-document interface. `examples/plugin-input.json` is an explicit keyword baseline; `examples/hybrid-input.json` executes real BGE but rebuilds for each call. Use the persistent workflow above for repeated research.

Run tests and the repository portfolio audit before publication. A failed audit blocks commit and push. Outputs are legal information for human review, not legal advice.
