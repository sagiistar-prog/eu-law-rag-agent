# 面试演示路径

1. 用 README 的隐私告知问题启动，选择 GDPR，核对 Article 13 的完整原文，再导出包含版本、来源和待核对项的 Markdown。
2. 展示当前适用性提问、无资料问题和口语改写的不同反馈，说明为什么候选不等于支持证据。
3. 打开 official-source-acceptance.md：查看 5/6 无资料误输出的初始问题、修复后的开发集结果及额外探针失败。
4. 打开 import_official.py、pipeline.py、pg_store.py 和对应测试，解释来源清洗、JSONL、BGE token/position 表示、全文/向量融合和作用域隔离。
5. 展示 GitHub 的官方来源到浏览器数据库链路检查，同时明确没有律师评估或客户业务结果。

可归属的贡献是用户任务定义、边界与交互设计、开源能力集成、版本及数据契约、失败驱动迭代。BGE 和 pgvector 是外部成熟组件，不描述为自研基础模型或数据库。
