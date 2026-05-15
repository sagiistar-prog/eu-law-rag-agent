# RAG Answer

answer: >
  Based only on the retrieved safe-demo sources, # Fictional Tariff Classification Note  This short sample is fictional and exists only for the safe demo. A tariff note should record the product description, material composition, declared use, and the classification basis used for the preliminary check. The note should not be treated as a final customs decision. A qualified reviewer should confirm the classification before an import or export action.
sources:
  - source_id: demo-tariff-001
    source_title: Fictional Tariff Classification Note
    source_url: https://example.org/fictional/tariff-classification-note
    retrieved_at: 2026-05-16
    chunk_id: demo-tariff-001::chunk-001
    confidence: medium
    manual_review_required: true
  - source_id: demo-reg-001
    source_title: Fictional EU Product Safety Excerpt
    source_url: https://example.org/fictional/eu-product-safety-excerpt
    retrieved_at: 2026-05-16
    chunk_id: demo-reg-001::chunk-001
    confidence: low
    manual_review_required: true
confidence: medium
manual_review_required: true
limitations:
  - This answer is generated from fictional short demo sources only.
  - It does not verify current law, official tariff status, or market access requirements.
  - AI inference is limited to summarizing the retrieved source text.
not_legal_advice: true
not_legal_advice_statement: >
  This output is legal information retrieval and source-grounded summarization only. It is not legal advice.
generated_at: 2026-05-16
