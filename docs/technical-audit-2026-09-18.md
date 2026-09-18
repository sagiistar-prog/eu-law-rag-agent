# 技术验收 2026-09-18

修复 PostgreSQL 适配器未返回 keyword_score 导致证据门槛失败的问题；关键词由全词 AND 改为受限分词 OR 检索，再与向量排名 RRF 融合。新增真实数据库的幂等、语料隔离、非法向量事务回滚测试。默认依旧是检索证据，不宣称自动法律结论。

## 验收边界

真实数据库指本机独立 PostgreSQL 16 / pgvector 容器，不是线上客户数据库。没有真实试用参与者；未宣称用户效果、转化率或临床/法律正确率。模型评测记录与集成测试分别呈现。

## 可复现数据库测试

设置 KB_DB_PASSWORD 后运行 `docker compose -f compose.knowledge.yaml up -d`。设置 KB_TEST_DATABASE_URL 指向该一次性测试数据库，运行 `python -m unittest discover -s knowledge -v`。测试语料使用独立随机 ID 并在结束时清理自身记录。服务使用 KB_DATABASE_URL；未配置时采用本地 JSON 向量索引。PostgreSQL 使用 ts_rank_cd 全文排名，不能称作 BM25；本地 JSON 模式使用 BM25。
