# 新对话 Agent 启动提示词：自运行可靠性修复

> 将以下全部内容复制粘贴到新对话中作为第一条消息。

---

## 你的任务

你是"Search in Coding"项目的运维 Agent。项目已完成所有功能开发，进入自运行阶段。发现 3 个影响自运行可靠性的问题需要修复。

## 决策背景

- **daily cron 不 deploy**：这是刻意设计，不是 bug。每天采集的新数据等到 LLM cron（Tue-Sat 或周一）分析后才 deploy 上线。保持原始设计不变。
- **LLM cron 负责 deploy**：daily LLM（Tue-Sat）和 weekly LLM（周一）都在分析后 deploy。

## 问题清单

### 问题 1（High）：daily cron 脚本没有 source venv

**现状：** `~/.hermes/scripts/search-in-coding-daily.sh` 直接 `/usr/bin/python3 scripts/update_tracker.py`，没有 `source .venv/bin/activate`。如果 update_tracker.py 依赖 PyYAML（在 venv 中），可能失败。7/15 运行成功可能是因为系统 Python 恰好有 PyYAML，但不可靠。

**修复：** 脚本加 `source .venv/bin/activate`。

修改 `~/.hermes/scripts/search-in-coding-daily.sh`：
```bash
#!/bin/bash
# Wrapper: Run Search in Coding daily pipeline via update_tracker.py
cd /root/workspace/search\ in\ coding || { echo "ERROR: workdir not found"; exit 1; }
source .venv/bin/activate
/usr/bin/python3 scripts/update_tracker.py 2>&1
exit $?
```

注意：**不加 `--deploy`**，保持原始设计。

### 问题 2（Medium）：GitHub Actions Update Data 失败

**现状：** 7/15 的 Update Data Action 失败（3m37s）。

**修复：** 检查失败原因并修复。

```bash
cd "/root/workspace/search in coding"
gh run view 29390014048 --log-failed 2>/dev/null | tail -30
```

常见原因：
- PyYAML 未安装（GitHub Actions 环境需要 `pip install pyyaml`）
- GitHub CLI 认证问题
- 脚本路径问题

### 问题 3（High）：03:00 采集和 03:30 LLM 时间冲突

**现状：** daily 采集 cron 03:00 运行，daily LLM cron 03:30 运行。如果采集跑超过 30 分钟（5165 条数据），两个脚本会同时写 projects.yaml，可能导致数据损坏。

**修复：** 将 daily LLM cron 从 03:30 改到 04:30，给采集留出 1.5 小时窗口。

```bash
# 查看当前 daily LLM cron 的 job_id
hermes cron list
# 找到 "Search in Coding daily LLM incremental" 的 job_id
# 更新 schedule 或删除重建
```

## 执行步骤

### 步骤 1：修复 daily cron 脚本（加 venv）

```bash
cat > ~/.hermes/scripts/search-in-coding-daily.sh << 'EOF'
#!/bin/bash
# Wrapper: Run Search in Coding daily pipeline via update_tracker.py
cd /root/workspace/search\ in\ coding || { echo "ERROR: workdir not found"; exit 1; }
source .venv/bin/activate
/usr/bin/python3 scripts/update_tracker.py 2>&1
exit $?
EOF
chmod +x ~/.hermes/scripts/search-in-coding-daily.sh
```

### 步骤 2：调整 daily LLM cron 时间

```bash
hermes cron list
# 找到 daily LLM incremental 的 job_id
# 更新 schedule 为 04:30（"30 4 * * 2-6"）
# 如果不支持 update schedule，删除旧 job 重建：
hermes cron remove --job-id <old_job_id>
hermes cron create \
  --name "Search in Coding daily LLM incremental" \
  --schedule "30 4 * * 2-6" \
  --no-agent \
  --script "search-in-coding-llm-daily.sh" \
  --workdir "/root/workspace/search in coding"
```

### 步骤 3：检查 GitHub Actions 失败原因

```bash
cd "/root/workspace/search in coding"
gh run view 29390014048 --log-failed 2>/dev/null | tail -30
# 根据错误信息修复 .github/workflows/update-data.yml
```

### 步骤 4：验证

```bash
# 1. 验证 daily cron 脚本
cat ~/.hermes/scripts/search-in-coding-daily.sh

# 2. 验证 cron 时间（daily 03:00, LLM 04:30, weekly 03:30 Mon）
hermes cron list | grep -E "daily|LLM|weekly"

# 3. 验证 daily cron 能正常运行（不 deploy）
cd "/root/workspace/search in coding"
source .venv/bin/activate
python3 scripts/update_tracker.py 2>&1 | tail -5

# 4. 验证 GitHub Actions
gh run list --limit 3
```

### 步骤 5：Commit

```bash
cd "/root/workspace/search in coding"
git add .github/workflows/update-data.yml  # 如果修改了
git commit -m "fix: daily cron venv + LLM cron time adjustment + GitHub Actions fix"
```

## 关键约束

1. **daily cron 不加 --deploy**：保持原始设计，LLM cron 负责 deploy
2. **不修改 projects.yaml 数据**：只改脚本和配置
3. **不修改前端代码**：只改运维脚本
4. **不修改评分逻辑**：只改 cron 调度
5. **修改后验证**：每个改动都要验证生效

## 项目环境信息

- 工作目录：`/root/workspace/search in coding`
- Python：3.12.3（用 python3，需要 venv）
- Hermes cron：4 个 job（daily collect 03:00、daily LLM、weekly LLM Mon 03:30、weekly release Mon 09:00）
- 站点：https://coding.lzpgood.online/（Nginx）
- GitHub Actions：3 个 workflow（update-data、publish-site、release）

## 修复后的自运行时间线

```
03:00  daily 采集 + 评分 + 构建（不 deploy）（每日）
04:30  daily LLM 增量 200 条 + deploy（Tue-Sat）
03:30  weekly LLM 全量重评 + 报告 + deploy（周一）
09:00  weekly GitHub Release（周一）
push   GitHub Actions Publish Site（实时）
```

采集和 LLM 错开 1.5 小时，避免 projects.yaml 写冲突。deploy 只在 LLM 分析后执行，确保上线数据质量。
