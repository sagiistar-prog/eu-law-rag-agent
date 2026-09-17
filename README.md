# EU Law Evidence Lab


[产品案例与指标](docs/product-case.md) | [能力证据](docs/capability-evidence.json) | [验收与边界](docs/validation.md)

## 面试官 30 秒版

用短来源文本演示可追溯检索与无依据拒答。把来源标识、引用预算与拒答作为可执行约束。资料不足时不以模型记忆补足，也不把相关性分数当作法律结论置信度。

当前能力：本地 BGE 英文向量编码、BM25、RRF 混合检索、来源核对和原文摘录。保留关键词基线便于对照。生成综述由插件宿主模型完成，必须引用证据；不把检索得分当法律判断。

[知识库运行与架构](knowledge/README.md) | [实际检索记录](docs/retrieval-smoke.json) | [插件使用与产品取舍](docs/plugin.md) | [输入示例](examples/plugin-input.json) | [输入契约](schemas/input.schema.json) | [维护记录](CHANGELOG.md)

```bash
python -m pip install -r requirements-plugin.txt
python scripts/plugin_run.py --input examples/plugin-input.json
```

## 运行真实向量检索

```sh
python -m pip install -r knowledge/requirements.txt
python scripts/plugin_run.py --input examples/hybrid-input.json
```

首次下载模型后在本机推理。持久化索引与可视化证据工作台见knowledge/README.md。默认英文模型，跨语言检索不在验收范围内。内置资料都是虚构片段，不是实际法规库。

## 兼容的关键词基线工作流


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
