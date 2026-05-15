# Case Study

## Context

EU Law RAG Agent is a public portfolio prototype for source-grounded legal and compliance research. It demonstrates how a retrieval workflow can keep responses tied to source metadata and avoid unsupported claims.

## Challenge

Regulatory research can become unreliable when summaries are produced without clear evidence. A portfolio demo must also avoid private data and must be safe to publish.

## Approach

The project uses a small local pipeline:

1. Ingest short Markdown examples.
2. Preserve source metadata for each chunk.
3. Build a simple keyword index.
4. Retrieve relevant chunks for a query.
5. Produce a structured answer with limitations and review flags.

## Outcome

The demo produces a source-grounded answer that includes source identifiers, titles, URLs, retrieval dates, confidence, manual-review requirements, limitations, and a legal information disclaimer.

## Portfolio Boundary

The sample materials are fictional and minimal. They are not copied from internal documents or real client records.
