# 验收记录

日期：2026-09-17。范围：本轮作品集迭代。

## 已运行

3 项插件契约测试；8 项知识库单元测试；英文 BGE 384 维真实推理、混合检索与评估；桌面/手机及延迟响应期间的输入锁定测试。

## 尚未证明

样本为虚构材料；不证明真实法律问题的正确率。Postgres 适配未连接数据库验收。默认是证据摘录，宿主模型综述仍需逐条来源审查。

没有进行真实用户访谈或客户效果实验。产品案例中的研究方案、指标目标和迭代假设不冒充已取得的结果。

## 复现入口

运行命令见 README、docs/plugin.md（插件仓库）及 knowledge/README.md（知识库仓库）。自动检查见 .github/workflows/quality.yml。依赖版本以锁文件为准。

真实模型的微型合成语料结果见 [retrieval-smoke.json](retrieval-smoke.json)。每个语料只有 5 条文档、3 个问题，只用于检验链路，不用于宣传准确率。

## 界面记录

[桌面](screenshots/desktop.png) | [手机](screenshots/mobile.png)

Impeccable 检查后的设计事实记录在 DESIGN.md。HTML 检测器以降级模式运行，没有宣称完整无障碍认证；截图不等于全部交互自动验收。
