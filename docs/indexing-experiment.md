# 分块实验与引用完整性

研究者需要找到能核对条件和例外的条文。假设是：给片段补充来源标题、章节，或沿段落切分，可以改善日常表达的检索。先冻结[协议](../knowledge/evaluation/indexing-protocol.md)，固定 30 条原始公报和 BGE small English，再比较。三组题均已观察，不能当作独立留出或法律正确性评测。

## 实验结果

| 策略 | 原有正向题 | 已知改写 | 改写回归 | 负向误给证据 | 改写 P50 |
|---|---:|---:|---:|---:|---:|
| 320 字符正文 | 24/24 | 0/3 | 8/16 | 0/16 | 49.79 ms |
| 320 字符加标题/章节 | 23/24 | 0/3 | 9/16 | 0/16 | 52.10 ms |
| 段落优先加标题/章节 | 23/24 | 0/3 | 11/16 | 0/16 | 45.48 ms |

负向分母分别为 6、2、8。段落策略的原有题平均来源精确率由 0.4021 降至 0.3944。两种候选都没有保住原 24 题，也未达到改写至少 12/16 的门槛，因此不替换默认。门槛代码另逐组检查精确率、误给证据和不超过基线 4 倍的 P50；不会用某组收益抵消另一组退步。

延迟为本机热模型 CPU，包含查询编码，不包含 HTTP/数据库；基线先运行，不能据此宣称段落方案性能更好。[逐题记录](evaluation/indexing-comparison.json)与[机器判定](evaluation/indexing-adoption.json)均保留。必要技术门槛全部通过也不等于有真实用户价值。

## 同时修复的出处问题

字符窗口去掉首部空白后，旧记录的起始位置未跟随移动。350 块中修正 65 处；新 descriptor 为 `characters-320-overlap-40-v2`。真实 BGE 重建确认所有正文和全部向量与旧索引相同，59 道回归题的候选、证据逐题相同。[完整复核记录](evaluation/citation-integrity.json)。

短摘录原先通过单空格连接词，改变了原始换行，且保留完整片段哈希。现在按词边界截取原文精确前缀，给实际摘录重新计算哈希、结束位置和派生 ID；原片段 ID/哈希/范围保留在 `excerpt_of`。界面和 Markdown 明示截短，提供完整条文入口。JSON 的字符范围指清洗后来源中的 Unicode 码点，不是原下载文件的字节位置。

旧 v1 索引仅在其 320 字符窗口去空白后与片段完全相同的情况下修正位置。其他文字、位置或哈希不一致直接失败，不能搜索一个相似字符串来伪造准确出处。

## 复现

先按 README 导入到新的 `output/official-v1`，安装实际模型依赖。下列命令不会覆盖既有索引：

```sh
python knowledge/pipeline.py build --language en --documents output/official-v1/documents.jsonl --index output/indexing/base.json --cache-dir .cache/models
python knowledge/pipeline.py build --language en --documents output/official-v1/documents.jsonl --index output/indexing/context.json --document-context source-section --cache-dir .cache/models
python knowledge/pipeline.py build --language en --documents output/official-v1/documents.jsonl --index output/indexing/paragraphs.json --chunker paragraphs --document-context source-section --cache-dir .cache/models
python knowledge/evaluate_indexing.py --index output/indexing/base.json --index output/indexing/context.json --index output/indexing/paragraphs.json --cases knowledge/evaluation/official-cases.json --cases knowledge/evaluation/known-paraphrase-cases.json --cases knowledge/evaluation/paraphrase-holdout-v1.json --cache-dir .cache/models --output output/indexing/comparison.json
python knowledge/assess_indexing.py --comparison output/indexing/comparison.json --baseline base --output output/indexing/adoption.json --require-ready
```

`--require-ready` 在所有候选未达标时返回 2；不加此参数只记录决定，不代表通过。校验会拒绝缺失分母、改动问题或标签、无效延迟以及和逐题记录不一致的汇总。重新下载可能产生不同快照，不能将新结果冒充已记录的旧运行。

## 产品取舍

引用准确是核对工具的最低要求，应直接修复；检索效果变化需要比较后再决定。此次保留默认，原因是用户已有能完成的任务不应为了少量改写收益而退步。下一步需收集新的研究任务、独立标注相关条文及证据充分性，再决定分块或召回改进。当前没有专业审核、团队任务时长或客户收益数据。
