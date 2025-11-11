# 下一阶段路线图（RAG + 中断/恢复 + 运维）

本文档描述接下来 2–3 周的开发计划与验收目标。

## 目标
- 上线“RAG + 中断/恢复”的端到端体验（在线模型）
- 提升叙事一致性与可控性（检索注入、可视化、可回溯）
- 完成运维观测、容量与安全底线

## 工作流 A：硬中断 + 恢复（LangGraph 定制图）
- 自定义 StateGraph（process → maybe_interrupt → end），节点内原生 interrupt
- WS 协议 v2：interrupt 返回 `checkpoint_id` + `prompt`/`options`；前端 `resume` 携带 `checkpoint_id` 精准续跑
- 极简前端交互：弹窗展示 prompt/options，点击调用 resume
- 验收
  - 中断后重启进程还能 resume
  - 连续两次中断的线程恢复正确

## 工作流 B：RAG 质量与一致性
- 复合检索：基于“位置/NPC 名称 + 玩家行动”的组合 query
- 事实标注：在系统块中明确“检索事实 vs 模型推断”提示
- 索引维护：重建索引 API、批量/增量索引、去重/截断
- 性能：批量异步 embeddings、缓存热点 query、统一向量归一策略
- 验收
  - 索引重建可控（时间与进度日志）
  - 注入“事实段”覆盖率>80%，幻觉显著下降

## 工作流 C：前端与交互
- 中断 UI：prompt/options 展示、resume 提交、错误提示
- RAG 透明度：在 DM 面板中以“参考条目”折叠显示检索到的事实（可开关）
- 回合/工具事件流水：narration/tool_call/interrupt/complete 分段显示
- 验收
  - 10 次中断/恢复无卡死；RAG 展示可手动关闭不影响生成

## 工作流 D：可观测性与运维
- 指标：回合耗时、工具调用次数/失败率、RAG 命中率、embeddings 延迟
- 日志：线程 id、checkpoint_id、世界 id、错误码标准化
- 健康：/metrics（Prometheus）、/health 扩展、/config 概览
- 验收
  - 并发 20 会话压测，超时/错误率可控；关键指标可视化

## 工作流 E：容量与安全
- SQLite：WAL、busy_timeout、连接池复用（已启用）、热点查询缓存
- 限流：WS /action、/resume 速率限制、输入长度限额
- 权限：本地开发白名单、生产鉴权开关（预留）
- 验收
  - 恶意输入/高频请求不致崩溃；限流可控

## 里程碑（建议）
- 里程碑 1（本周）：定制 StateGraph + WS v2 + 基本前端中断 UI；复合检索注入与“事实/推断”标注；单会话多中断重启续跑
- 里程碑 2（下周）：重建索引 API + 批量 embeddings + 缓存；/metrics 导出 + 日志结构化；运维页
- 里程碑 3（第 3 周）：压测与调优；限流/鉴权/回退策略

## 当前状态小结
- 在线嵌入：默认 `qwen/qwen3-embedding-8b`（OpenRouter），可在 `.env` 以 `EMBEDDING_MODEL` 覆盖
- RAG 注入：LangGraph/LangChain 两版 DM 均已在回合前自动注入“世界检索结果”
- 中断：支持工具触发中断与 resume；最小“硬中断”带 `checkpoint_id`，WS 已支持携带恢复
- 存储：RAG 索引位于 SQLite 表 `world_kb`（路径见 `settings.database_path`）

