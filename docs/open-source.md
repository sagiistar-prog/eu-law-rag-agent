# 开源与官方来源的选择

选择依据是任务匹配、可检查接口、维护方式、许可、可测试性和部署成本。使用成熟模型与向量数据库，把本项目的贡献集中在来源治理、任务流程、门槛和验证。

| 来源 | 为什么采用 | 实际状态 |
|---|---|---|
| [FastEmbed](https://github.com/qdrant/fastembed) | Apache-2.0，CPU ONNX 推理、明确模型接口，适合本地研究资料 | 固定 0.7.4，真实下载及推理 |
| [BGE small English](https://huggingface.co/BAAI/bge-small-en-v1.5) | MIT，英文检索模型，384 维，查询指令清晰 | 默认编码器，真实 tokenizer 检查 |
| [MS MARCO MiniLM L6](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2) / [ONNX 转换](https://huggingface.co/Xenova/ms-marco-MiniLM-L-6-v2) | Apache-2.0，英文 query/passage 重排，CPU 成本可实测 | 显式实验模式，固定 revision 与五个制品 SHA256；未通过默认接入门槛 |
| [pgvector](https://github.com/pgvector/pgvector) | PostgreSQL License，可验证事务和语料隔离 | PostgreSQL 16 / pgvector 0.8.1 实际联调，另保留无数据库文件模式 |
| [Haystack](https://github.com/deepset-ai/haystack) | Apache-2.0，阶段式管线和检索融合边界可借鉴 | 架构参考，没有复制代码或接入完整框架 |
| [AI Elements](https://github.com/vercel/ai-elements) | Apache-2.0，引用与任务状态组件提供交互参考 | 参考，没有安装；小工具用原生 HTML 与 JavaScript |
| [Playwright](https://github.com/microsoft/playwright) / [axe-core](https://github.com/dequelabs/axe-core) | 浏览器真实任务及自动可访问性检测可复现 | 实际开发依赖，版本在 package-lock.json |

官方条文通过 [Cellar 出版物接口](https://op.europa.eu/en/web/cellar/cellar-data/publications) 下载，保留 CELEX 与 [EUR-Lex 原文链接](https://eur-lex.europa.eu/content/help/data-reuse/reuse-contents-eurlex-details.html?locale=en)。下载内容遵循其来源的 [欧盟法律声明](https://european-union.europa.eu/legal-notice_en)，仓库 MIT 许可不替代来源许可。全文和向量不随仓库再分发。

Impeccable 用于状态、留白、焦点、移动阅读与失败恢复的审查。采用用户给定的蓝紫灰方向，没有复制参考图中的图片、Logo 或商业素材。点阵只表示实际请求活动，不虚构模型思考或百分比。

维护时固定依赖并运行三路检索、真实数据库和浏览器回归。框架热度不是适用性证据；本轮没有证据证明混合检索比关键词在所有任务上更好。

重排使用 [FastEmbed 官方接口](https://qdrant.tech/documentation/fastembed/fastembed-rerankers/)，只对最多 40 个候选推理。MS MARCO 原始分数为未校准 logit，不能当作正确概率，参见 [Sentence Transformers 文档](https://sbert.net/docs/cross_encoder/usage/usage.html)。增加模型后仍保留原文核对和人工审核；实测收益与成本见[实验结果](reranker-experiment.md)。
