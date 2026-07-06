# 简短启动提示词：最终交付版

请在 `/root/workspace/search in coding` 中继续执行 Search in Coding 项目，直到最终交付完成。

不要停在 MVP。请读取并执行：

```text
prompts/final-delivery-execution.md
```

最终完成标准见：

```text
.hermes/plans/2026-07-06_102845-final-delivery-plan.md
```

必须做到：

- 项目可发布
- 数据可复核
- curated dataset 完成
- rejected/noisy dataset 完成
- official tools 与 ecosystem projects 分榜
- Exa 成功或有精确 blocker 与 fallback 报告
- 静态站点可用
- 自动化和 Hermes cron prompts 完整
- 最终报告齐全
- 最终质量门禁全部通过
- 导出 `dist/search-in-coding-final.zip`

必须实际运行最终验证命令：

```bash
python3 scripts/validate_data.py
python3 scripts/quality_gate.py
python3 scripts/score.py
python3 scripts/generate_reports.py
python3 scripts/build_site.py
python3 scripts/export_pack.py --dry-run
python3 scripts/export_pack.py --output dist/search-in-coding-final.zip
```

如果任何命令失败，请修复并重跑。只有全部通过后才能停下。