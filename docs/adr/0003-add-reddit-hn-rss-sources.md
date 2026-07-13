# ADR-0003: 新增 Reddit、Hacker News、博客 RSS 三个采集来源

## Status: proposed

## Context

砍掉 fallback-web（ADR-0001）后，系统只剩 GitHub 和 Exa 两个采集来源。GitHub 偏重代码仓库，Exa 偏重网页内容，两者都缺少社区讨论和一手博客来源。AI coding agent 生态的重要讨论大量发生在 Reddit（r/ClaudeAI, r/cursor）、Hacker News 和各公司官方博客上。

替代方案是只依赖 Exa 的语义搜索来覆盖这些内容，但 Exa 的覆盖面有限且不可控，且 Exa 本身也有不可用的风险。

## Decision

新增三个采集来源：

- **Reddit**：通过 Reddit API 搜索相关 subreddit 的帖子，按 score > 阈值过滤
- **Hacker News**：通过 Algolia HN Search API 搜索相关帖子
- **博客 RSS**：通过 feedparser 订阅预定义的 AI 编程博客列表，存入 `data/blog-feeds.yaml`

三种来源的 `source_quality`：RSS=verified（官方博客一手信息），Reddit/HN=community（社区讨论，可信度中等）。

## Consequences

- 需要管理 Reddit API 凭证和 HN API 的速率限制
- 博客 RSS 列表需要持续维护（`data/blog-feeds.yaml`）
- 社区来源的 `record_kind` 需要新增 `discussion` 类型
- 数据量和多样性提升，但也带来新的去重需求（同一项目可能在 GitHub + Reddit + HN 三处出现）
