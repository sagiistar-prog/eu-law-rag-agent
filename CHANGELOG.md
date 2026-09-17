# Maintenance log

## 0.2.0 — 2026-09-17

- Added a versioned Codex plugin manifest with the existing Skill.
- Added validated JSON input/output, a fictional input fixture and an explicit artifact export path.
- Documented the actual offline capability and its limitations.
- Added executable contract and regression checks; see `tests/`.
- Product decision: 把来源标识、引用预算与拒答作为可执行约束。资料不足时不以模型记忆补足，也不把相关性分数当作法律结论置信度。

The version labels a repository iteration, not a hosted product launch or a marketplace release.

## 2026-09-17 Product reliability release

可核对的法律研究证据。补齐产品案例、能力证据、指标契约、开源取舍与持续检查。验证范围和未验收项见 docs/validation.md。
