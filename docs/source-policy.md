# 0.3 原始公报快照规则

当前下载清单仅含 30 条选定原始公报条文。`original_oj` 不是当前合并文本。必须保留 CELEX、publication_date、retrieved_at、document_version 和 version_notice；采集时间不是生效日期。

`source_verified` 表示官方下载身份及条文提取覆盖检查通过，不代表专家审核、现行适用性或法律结论。`confidence: unrated` 和 `manual_review_required: true` 保留在结果中。候选不等于支持证据；无充分摘录时请求补充来源或核对完整原文。

全文仅存于本地 ignored output。宿主综述须逐项引用，未被原文支持的推论明确标注。法律时效关键词提示是有限启发式，不应作为完整风险分类器。


# Source Policy

## Evidence Levels

1. Official source
   - Laws, regulations, decisions, official notices, customs guidance, or regulator publications from the competent authority.

2. Public institutional source
   - Public materials from recognized public institutions, courts, agencies, standards bodies, universities, or intergovernmental organizations.

3. User provided document
   - A document supplied by the user for analysis. The system must identify it as user supplied and avoid assuming it is authoritative.

4. Secondary public source
   - Public commentary, summaries, articles, or explainers. These can help with context but should not override higher evidence levels.

5. AI inference
   - Reasoned synthesis produced from retrieved evidence. It must be labeled as inference and must not be presented as a source.

## Mandatory Rules

- No source, no answer.
- AI inference must be clearly labeled.
- Commercial decisions and legal judgments must be manually reviewed.
- High risk legal, tariff, customs, import, export, product compliance, or enforcement topics require manual review.
- Source metadata must include `source_id`, `source_title`, `source_url`, and `retrieved_at`.
- Every answer must include `confidence` and `manual_review_required`.

## Source Preference

When multiple sources are available, prefer official sources over institutional sources, user supplied documents, secondary sources, and inference.
