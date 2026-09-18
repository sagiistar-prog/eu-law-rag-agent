# 一次没有更换默认方案的检索实验

2026-09-18，版本 0.3.1。目标是让研究者用普通英文找到相关条文。实验确有局部改善，但没有达到预设接入门槛，因此默认仍是 hybrid，MiniLM 重排只通过 `--ranking rerank` 显式启用。

## 问题、假设与取舍

0.3 的词项和余弦门槛避免了已知缺失资料问题误给证据，却在 3 道口语改写中漏掉全部目标摘录。直接放宽门槛可能同时增加误引。此次假设是：先召回候选，再联合编码问题与完整一点的上下文，会改善表达差异。

采用 FastEmbed 支持的 `Xenova/ms-marco-MiniLM-L-6-v2`，Apache-2.0，权重约 91 MB。固定 revision `a09144355adeed5f58c8ed011d209bf8ee5a1fec`；模型和四个配置/tokenizer 文件均在推理前验证 SHA256。实现和全部哈希见[reranker.py](../knowledge/reranker.py)，来源选择见[开源记录](open-source.md)。

它是通用英文段落重排模型，并非法律蕴含模型。评分为未校准 logit；非负分也不表示问题已被完整回答。置信度继续为 unrated。

## 实验设计

同一份 30 条官方原始公报快照、350 个 BGE 片段；不新增来源，也不调用生成模型。语料哈希为 `e619518fe1569053cfe02c16f65011c1abba4eed35894b3a869ba71896d26535`。

基线为 12 个 BGE/BM25/RRF 候选、条文去重及原词项/余弦门槛。实验取最多 40 个融合候选，添加用户所选法规名称作为问题上下文，取匹配位置周围最多 1600 个字符，重排后保留不同条文。最低 logit 为 0，与最高分差距不超过 2。没有针对单道问题写改写词典。

这是一组组合改动，最终差异不能归因于重排模型单一因素。开发探针先比较短块、邻近上下文、再加入法规范围；前两种仍未找回已知三题，最终组合找回两题。原始探针记录保留在[开发对照](evaluation/rerank-development-ablation.json)。

查询、标题与原文一起经过真实 tokenizer 检查，上限 512 token。上下文太长时缩短原文窗口；无法同时保留查询与最小匹配窗口时明确失败，不静默截断问题。派生片段保留 matched_chunk_id、原文 char_start/context_char_end、内容哈希；导出内容是实际评分的原文窗口。pending 来源不因高分变为支持证据。

## 在看结果之前冻结什么

[预设方案](../knowledge/evaluation/reranker-protocol.md)要求：原 24 道正向题全部保留，6 道负向题无误给证据；已知改写至少 2/3；留出正向至少 12/16，负向不劣于基线且最多 2/8。记录延迟，但没有事后增加延迟硬门槛。

留出 24 题于 12:57 UTC 冻结，SHA256 为 `f64af861461131d534116d82601b5ca542bffce39d52e3899d18784977b49125`。16 道相关条文题、8 道具体资料缺失题。[模型策略](../knowledge/evaluation/reranker-policy-v1.json)在运行留出集前选定；留出结果未参与阈值调整。Git 对该文件禁用换行转换，保留冻结时的原始字节，保证跨系统校验一致。

所有标签由实现者编写，不是独立专家盲评。标签只表示相关条文；命中同一条文不证明段落完整、法律适用或引用正确。现在这组题已被观察，后续调优只能把它视作回归集，需另建独立评测。

## 配对结果

每一行使用同一批问题、相同语料和本机 CPU，模型预先载入，先运行基线。下面不是 HTTP、数据库、冷启动或生产延迟。

| 数据集 | 基线目标证据命中 | 实验目标证据命中 | 基线/实验负向误给证据 | 基线/实验 P50 |
|---|---:|---:|---:|---:|
| 原开发题 | 24/24 | 24/24 | 0/6、0/6 | 51.8 ms、2645.4 ms |
| 已知改写 | 0/3 | 2/3 | 0/2、0/2 | 以完整报告为准 |
| 冻结留出 | 8/16 | 10/16 | 0/8、0/8 | 50.3 ms、2673.1 ms |

原开发集平均来源精确率从 0.4021 到 0.9306；留出集从 0.2000 到 0.3906，未返回证据按 0 计。留出 Top5 候选目标命中由 14/16 到 15/16。候选命中与支持证据命中分开计数，不能用前者掩盖后者的不足。

完整[原开发集](evaluation/rerank-canonical.json)、[已知改写](evaluation/rerank-known.json)、[留出集](evaluation/rerank-holdout.json)含逐题来源、分数与计时；[机器判定](evaluation/rerank-adoption.json)的 ready_for_default 为 false，失败项是 holdout_target_hits。

6 道未命中题都来自 GDPR：照片迁移、无人参与的自动决定、地址泄露通知、注册时信息告知、设计阶段隐私保护、为诉讼保留资料的删除例外。最后一道目标条文排第一但低于支持门槛；照片迁移题未进入最终前五。不能统一解释为“库里没数据”，也不能因为问题有答案就把候选直接升级为证据。

## 工程验收与发布边界

本机 40 项知识库测试和 3 项插件测试通过，知识库测试中 4 项连接真实隔离 PostgreSQL。两种模式分别通过 30/30 道官方资料 HTTP 回归；它们不是额外独立样本。浏览器分别在 1440、390 宽度验证真实数据库结果、完整条文、Markdown/JSON 导出、版本拒答、缺失资料和故障恢复，未发现页面错误、横向溢出或 axe A/AA 规则命中。实验额外验证 DSA 口语申诉查询及导出原文哈希；故障由明确的 503 模拟。

见[默认 HTTP](evaluation/rerank-default-http.json)、[实验 HTTP](evaluation/rerank-http.json)、[默认浏览器](evaluation/rerank-default-browser.json)、[实验浏览器](evaluation/rerank-browser.json)。这证明本次本地工作流可执行，不是完整法律、生产或真实用户验收。

CI 同时保留默认模式回归和显式实验模式。assess_reranker 成功执行会保存“不采用”的决定，不能把 CI 绿色解释为采用门槛通过；要将门槛用于发布阻断，显式使用 `--require-ready`，当前记录返回 2。

## 复现

先按[知识库说明](../knowledge/README.md)导入 official-v1 并构建索引，然后运行下列命令。输出文件必须全新。

```sh
python knowledge/evaluate_review.py --index output/official-v1/index.json --cases knowledge/evaluation/official-cases.json --cache-dir .cache/models --output output/official-v1/rerank-canonical.json
python knowledge/evaluate_review.py --index output/official-v1/index.json --cases knowledge/evaluation/known-paraphrase-cases.json --cache-dir .cache/models --output output/official-v1/rerank-known.json
python knowledge/evaluate_review.py --index output/official-v1/index.json --cases knowledge/evaluation/paraphrase-holdout-v1.json --frozen-manifest knowledge/evaluation/paraphrase-holdout-v1.manifest.json --cache-dir .cache/models --output output/official-v1/rerank-holdout.json
python knowledge/assess_reranker.py --canonical output/official-v1/rerank-canonical.json --known output/official-v1/rerank-known.json --holdout output/official-v1/rerank-holdout.json --output output/official-v1/rerank-adoption.json
python knowledge/server.py --language en --index output/official-v1/index.json --cache-dir .cache/models --port 8893 --ranking rerank
```

打开 http://127.0.0.1:8893 。数据库仍是可选项；未设置数据库地址时使用本地索引。模型缓存齐全后可离线运行，校验失败需重新取得正确制品，不能忽略哈希或自动切换模式。

下一次迭代先定位首轮召回和分块是否保留法规条件，再比较领域表达与专家标注。真实研究者的核对时间、错引率与审核接受率尚未测量。
