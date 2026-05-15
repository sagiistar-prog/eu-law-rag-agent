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
