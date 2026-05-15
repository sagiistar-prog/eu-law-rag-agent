# Safe Demo

The safe demo uses only fictional short Markdown sources.

## Run With Python

```powershell
python scripts\ingest_documents.py --input examples\docs --output examples\index\chunks.json
python scripts\build_index.py --chunks examples\index\chunks.json --output examples\index\index.json
python scripts\query_rag.py --query examples\sample_query.md --index examples\index\index.json --output examples\sample_answer.md --rules configs\rag_rules.yaml --dry-run
```

## Run With Windows Launcher

```powershell
py -3 scripts\ingest_documents.py --input examples\docs --output examples\index\chunks.json
py -3 scripts\build_index.py --chunks examples\index\chunks.json --output examples\index\index.json
py -3 scripts\query_rag.py --query examples\sample_query.md --index examples\index\index.json --output examples\sample_answer.md --rules configs\rag_rules.yaml --dry-run
```

## Audit

```powershell
powershell -ExecutionPolicy Bypass -File scripts\portfolio_audit.ps1
```

The expected result is `AUDIT RESULT: PASS`.
