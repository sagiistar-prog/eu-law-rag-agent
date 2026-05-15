# EU Law RAG Agent Skill

Use this skill when working on the EU Law RAG Agent portfolio project.

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

## Required Commands

```powershell
py -3 scripts\ingest_documents.py --input examples\docs --output examples\index\chunks.json
py -3 scripts\build_index.py --chunks examples\index\chunks.json --output examples\index\index.json
py -3 scripts\query_rag.py --query examples\sample_query.md --index examples\index\index.json --output examples\sample_answer.md --rules configs\rag_rules.yaml --dry-run
powershell -ExecutionPolicy Bypass -File scripts\portfolio_audit.ps1
```

## Publication Rule

Do not commit or push when the portfolio audit fails.
