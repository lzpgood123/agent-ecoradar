# ADR-0004: 引入 relevance_score 字段和负向关键词一票否决机制

## Status: proposed

## Context

当前系统无内容相关性过滤，导致 fallback-web 采集的无关内容（狗狗买卖、Google 表格函数）直接进入数据集。即使砍掉 fallback-web 采集器（ADR-0001），其他来源也可能返回不相关结果（如 Exa 搜索 "cursor mcp" 返回鼠标光标相关的文章）。

现有的 `negative_keywords` 配置只用于采集阶段过滤，不用于已采集数据的事后校验。

## Decision

1. 新增 `relevance_score` 字段（0-1 浮点数），基于正向关键词匹配度 + 负向关键词扣分计算
2. 正向关键词列表（至少匹配 1 个）：AI coding, coding agent, MCP, model context protocol, skills, hooks, cursor rules, claude code, codex, agentic, codebase, prompt engineering, context engineering
3. 负向关键词一票否决：puppies, dogs, rehoming, pets, crypto, airdrop, 免费chatgpt, AI工具箱, 文心一言
4. `relevance_score < 0.3` 的记录自动 reject，不进入 curated 候选池
5. 新增 `relevance_penalty` 评分调整：relevance < 0.5 扣 3 分，< 0.3 扣 5 分

## Consequences

- 所有已有数据需要一次性回溯计算 relevance_score
- 关键词列表需要持续维护，避免误杀有效项目
- 为未来语义相关性评估（embedding）留接口，TF-IDF baseline 可以作为 relevance_score 的增强
