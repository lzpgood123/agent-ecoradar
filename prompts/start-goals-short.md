# 简短启动提示词

请在 `/root/workspace/search in coding` 中执行 Search in Coding 项目。

按顺序完成两个 Goal：

1. **Goal A：项目搭建打包与可复用化**
   详细要求见：`prompts/goal-a-project-packaging.md`

2. **Goal B：项目收集完成与初始生态分析**
   详细要求见：`prompts/goal-b-initial-collection.md`

执行时必须遵守：

- GitHub 搜索使用已配置好的 `gh`。
- Exa 语义搜索使用：

```bash
mcporter call 'exa.web_search_exa(query: "Claude Code ecosystem extensions plugins MCP skills rules best practices", count: 3)'
```

- 不要只检查 `exa` CLI。
- 不要伪造任何搜索结果或命令输出。
- 所有 raw 搜索结果必须保存。
- 完成后运行验证命令，并用中文汇报真实结果。

请持续执行，直到两个 Goal 完成并通过验证。