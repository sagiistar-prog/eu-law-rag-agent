# Agent Operating Rules

This repository is a public portfolio project for EU Law RAG Agent.

## Workspace Boundary

- Work only inside this repository.
- Do not access, scan, or modify parent directories.
- Do not read private accounts, messages, personal folders, or unrelated local files.

## Data Boundary

- Do not upload or add full legal corpora, large source files, private files, client files, partner files, or internal materials.
- Keep examples fictional, short, and sanitized.
- Do not introduce protected private company or project identifiers named in the user brief.
- Do not introduce real client names, real partner names, real operating loops, real pricing details, or private commercial information.

## Legal Boundary

- This project performs legal information retrieval and source-grounded summarization only.
- It does not provide legal advice, legal opinions, or professional services.
- Legal, tariff, compliance, import, export, and commercial decisions require human review.

## Answer Rules

- All answers must be grounded in retrieved sources.
- If no source is found, refuse to answer and request additional source material.
- Every answer must include `source_id`, `source_title`, `source_url`, `retrieved_at`, `confidence`, and `manual_review_required`.
- AI inference must be labeled as inference.
- High risk content must set `manual_review_required: true`.

## Commit And Release Rules

- Run `powershell -ExecutionPolicy Bypass -File scripts\portfolio_audit.ps1` after changes.
- If the audit result is FAIL, do not commit or push.
- Do not commit generated indexes, raw source dumps, private files, or large binary files.
