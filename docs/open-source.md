# 开源选择与贡献边界

FastEmbed/BGE：实际接入本地向量检索与插件接口。Web工作台为原生HTML，避免让小型证据工具承担大型前端框架。

| 项目 | 质量判断与用途 | 采用状态 |
|---|---|---|
| [Radix Primitives](https://github.com/radix-ui/primitives) | MIT，明确可访问组件语义；Dialog适合核对出处、关闭后继续阅读 | CareGuide实际使用，其他项目按需 |
| [Motion](https://github.com/motiondivision/motion) | MIT，成熟React动效；状态和reduced motion优先于装饰 | Where-to-live已有依赖 |
| [Sonner](https://github.com/emilkowalski/sonner) | MIT，适合短反馈；本轮原位状态已足够，不重复引入 | 参考，未接入 |
| [AI Elements](https://github.com/vercel/ai-elements) | Apache-2.0，任务与引用组件值得参考；不强行把证据工具改成聊天 | 参考，未复制代码 |
| [FastEmbed](https://github.com/qdrant/fastembed) | Apache-2.0，ONNX本地CPU推理，明确模型列表 | CareGuide与EU Law实际使用 |
| [FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding) | BGE模型MIT，区分语言、维数与查询指令 | CareGuide中文，EU Law英文 |
| [Haystack](https://github.com/deepset-ai/haystack) | Apache-2.0，清洗、检索、融合阶段边界清楚 | 架构参考，未声明整体框架接入 |
| [pgvector](https://github.com/pgvector/pgvector) | PostgreSQL License，复用已有数据库运维能力 | 可选持久化适配；本轮未连接数据库 |

依赖的实际版本以锁文件/requirements为准。选择依据是维护方式、许可证、接口清晰度、可测试性、部署成本与任务匹配，不仅是star数量。更新依赖先在独立分支运行构建、契约和关键任务测试，再升级。

原始参考图用于理解留白、蓝紫灰、光影和状态反馈，没有复制其图片、Logo或商业素材。Impeccable用于审查布局、交互与可访问性；技术注释与产品取舍留在文档中，产品界面不堆砌说明。
