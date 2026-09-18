# Maintenance log

## 0.3.1 — 2026-09-18

- Added an explicit opt-in, checksum-pinned MiniLM cross-encoder experiment with bounded source context and token checks.
- Retained hybrid retrieval as the default: the frozen paraphrase set reached 10/16 target evidence hits, below the predeclared 12/16 adoption gate, with a substantial latency cost.
- Preserved paired development/holdout reports, failed cases and a machine-readable adoption decision. No threshold changes after inspecting the holdout.
- Added real PostgreSQL and browser acceptance for both modes, JSON export verification and reproducible CI experiment artifacts.

## 0.3.0 — 2026-09-18

- Added official Cellar ingestion for 30 selected original-publication articles, provenance checks and extraction coverage.
- Added a persistent BGE source-review workflow, typed JSON contracts, complete selected-article view and Markdown/JSON export.
- Added instrument filtering before ranking, article diversity and an explicit candidate-versus-evidence boundary.
- Fixed PostgreSQL lexical candidates outside the dense shortlist missing their semantic score.
- Added real official-source, database and browser CI, including negative cases. Preserved failed paraphrase probes and current-law limitations.
- Retained the fictional short-document plugin interface and no-database local startup.

## 0.2.0 — 2026-09-17

- Added a versioned Codex plugin manifest with the existing Skill.
- Added validated JSON input/output, a fictional input fixture and an explicit artifact export path.
- Documented the actual offline capability and its limitations.
- Added executable contract and regression checks; see `tests/`.
- Product decision: 把来源标识、引用预算与拒答作为可执行约束。资料不足时不以模型记忆补足，也不把相关性分数当作法律结论置信度。

The version labels a repository iteration, not a hosted product launch or a marketplace release.

## 2026-09-17 Product reliability release

可核对的法律研究证据。补齐产品案例、能力证据、指标契约、开源取舍与持续检查。验证范围和未验收项见 docs/validation.md。
