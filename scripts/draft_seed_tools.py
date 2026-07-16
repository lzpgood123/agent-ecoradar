#!/usr/bin/env python3
"""Draft missing seed-tools entries for the closed 31-tool list.

Compares the canonical 31 display names against existing data/seed-tools.yaml,
generates status=draft entries for missing tools, and writes a human review
report. Never runs onboard or bulk collection.

Usage:
  python3 scripts/draft_seed_tools.py --dry-run
  python3 scripts/draft_seed_tools.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_jsonish, save_jsonish
from seed_tools_schema import (
    SEED_TOOLS_PATH,
    load_seed_tools,
    normalize_tool_entry,
    save_seed_tools,
    validate_tools,
)

REVIEW_REPORT_PATH = ROOT / "docs" / "reports" / "seed-tools-draft-review.md"

# Closed list of 31 tools (display_name is the user-confirmed label).
# suggested_id is the stable id to use for NEW drafts; matching may still
# resolve to an existing different id (e.g. Codex -> codex-cli).
CANONICAL_31: list[dict[str, Any]] = [
    {
        "display_name": "Cursor",
        "suggested_id": "cursor",
        "aliases": ["Cursor", "Cursor AI", "Cursor rules"],
        "vendor": "Anysphere",
        "primary_type": "ai-ide",
        "repo": "getcursor/cursor",
        "website": "https://cursor.com",
        "docs": "https://docs.cursor.com",
        "match_names": ["cursor"],
    },
    {
        "display_name": "GitHub Copilot",
        "suggested_id": "github-copilot",
        "aliases": ["GitHub Copilot", "Copilot", "gh copilot", "copilot.vim"],
        "vendor": "GitHub / Microsoft",
        "primary_type": "ai-assistant",
        "repo": "github/copilot.vim",
        "website": "https://github.com/features/copilot",
        "docs": "https://docs.github.com/en/copilot",
        "match_names": ["github copilot", "copilot"],
        "notes": "Product is closed; repo points to open editor integration.",
    },
    {
        "display_name": "Codex",
        "suggested_id": "codex-cli",
        "aliases": ["Codex", "Codex CLI", "OpenAI Codex", "codex"],
        "vendor": "OpenAI",
        "primary_type": "terminal-agent",
        "repo": "openai/codex",
        "website": "https://chatgpt.com/codex",
        "docs": "https://developers.openai.com/codex",
        "match_names": ["codex", "openai codex", "codex cli"],
    },
    {
        "display_name": "Windsurf",
        "suggested_id": "windsurf",
        "aliases": ["Windsurf", "Codeium Windsurf", "windsurf editor"],
        "vendor": "Codeium / Exafunction",
        "primary_type": "ai-ide",
        "repo": "Exafunction/codeium",
        "website": "https://windsurf.com",
        "docs": "https://docs.windsurf.com",
        "match_names": ["windsurf", "codeium windsurf"],
        "notes": "Main product closed; codeium org has public integrations.",
    },
    {
        "display_name": "Trae",
        "suggested_id": "trae",
        "aliases": ["Trae", "Trae Agent", "Trae SOLO", "Trae Work"],
        "vendor": "ByteDance",
        "primary_type": "ai-ide",
        "repo": "bytedance/trae-agent",
        "website": "https://www.trae.ai",
        "docs": "https://www.trae.ai/docs",
        "match_names": ["trae", "trae agent", "trae work"],
    },
    {
        "display_name": "Kiro",
        "suggested_id": "kiro",
        "aliases": ["Kiro", "Kiro IDE", "AWS Kiro"],
        "vendor": "AWS",
        "primary_type": "ai-ide",
        "repo": None,
        "website": "https://kiro.dev",
        "docs": "https://kiro.dev/docs",
        "match_names": ["kiro", "aws kiro"],
        "notes": "Likely closed product; verify public repo before opening.",
    },
    {
        "display_name": "Zed",
        "suggested_id": "zed",
        "aliases": ["Zed", "Zed editor", "zed.dev"],
        "vendor": "Zed Industries",
        "primary_type": "ai-ide",
        "repo": "zed-industries/zed",
        "website": "https://zed.dev",
        "docs": "https://zed.dev/docs",
        "match_names": ["zed", "zed editor"],
    },
    {
        "display_name": "Antigravity",
        "suggested_id": "antigravity-cli",
        "aliases": ["Antigravity", "Antigravity CLI", "Gemini CLI", "agy"],
        "vendor": "Google",
        "primary_type": "terminal-agent",
        "repo": "google-gemini/gemini-cli",
        "website": "https://antigravity.google/",
        "docs": "https://antigravity.google/docs/cli-install",
        "match_names": ["antigravity", "gemini cli", "agy"],
    },
    {
        "display_name": "Qoder",
        "suggested_id": "qoder",
        "aliases": ["Qoder", "QoderWork", "Qoder CLI"],
        "vendor": "Alibaba",
        "primary_type": "ai-ide",
        "repo": "QoderAI/qoder-action",
        "website": "https://qoder.com",
        "docs": "https://qoder.com",
        "match_names": ["qoder", "qoderwork"],
    },
    {
        "display_name": "CodeBuddy",
        "suggested_id": "workbuddy-codebuddy",
        "aliases": ["CodeBuddy", "WorkBuddy", "Tencent Cloud CodeBuddy", "腾讯云代码助手"],
        "vendor": "Tencent",
        "primary_type": "ai-ide",
        "repo": None,
        "website": "https://www.workbuddy.ai",
        "docs": "https://www.workbuddy.ai/docs/zh/workbuddy/Overview",
        "match_names": ["codebuddy", "workbuddy", "腾讯云代码助手"],
        "notes": "MERGE: reuse existing id workbuddy-codebuddy; do NOT create codebuddy.",
    },
    {
        "display_name": "OpenCode",
        "suggested_id": "opencode",
        "aliases": ["OpenCode", "opencode ai", "opencode cli"],
        "vendor": "Anomaly",
        "primary_type": "terminal-agent",
        "repo": "sst/opencode",
        "website": "https://opencode.ai",
        "docs": "https://opencode.ai/docs",
        "match_names": ["opencode"],
    },
    {
        "display_name": "Warp",
        "suggested_id": "warp",
        "aliases": ["Warp", "Warp terminal", "Warp AI"],
        "vendor": "Warp",
        "primary_type": "terminal-agent",
        "repo": "warpdotdev/Warp",
        "website": "https://www.warp.dev",
        "docs": "https://docs.warp.dev",
        "match_names": ["warp", "warp terminal"],
        "notes": "Desktop app mostly closed; public repo may be sparse.",
    },
    {
        "display_name": "Goose",
        "suggested_id": "goose",
        "aliases": ["Goose", "Block Goose", "AAIF Goose"],
        "vendor": "AAIF / Block",
        "primary_type": "terminal-agent",
        "repo": "block/goose",
        "website": "https://goose-docs.ai/",
        "docs": "https://goose-docs.ai/",
        "match_names": ["goose", "block goose"],
    },
    {
        "display_name": "Aider",
        "suggested_id": "aider",
        "aliases": ["Aider", "aider-chat", "Aider AI"],
        "vendor": "Aider",
        "primary_type": "terminal-agent",
        "repo": "Aider-AI/aider",
        "website": "https://aider.chat",
        "docs": "https://aider.chat/docs",
        "match_names": ["aider", "aider-chat"],
    },
    {
        "display_name": "Claude Code",
        "suggested_id": "claude-code",
        "aliases": ["Claude Code", "claude-code", "anthropic claude code"],
        "vendor": "Anthropic",
        "primary_type": "terminal-agent",
        "repo": "anthropics/claude-code",
        "website": "https://code.claude.com",
        "docs": "https://code.claude.com",
        "match_names": ["claude code", "claude-code"],
    },
    {
        "display_name": "通义灵码",
        "suggested_id": "tongyi-lingma",
        "aliases": ["通义灵码", "Tongyi Lingma", "Lingma", "Alibaba Lingma"],
        "vendor": "Alibaba Cloud",
        "primary_type": "ai-assistant",
        "repo": None,
        "website": "https://lingma.aliyun.com",
        "docs": "https://help.aliyun.com/zh/lingma/",
        "match_names": ["通义灵码", "tongyi lingma", "lingma"],
        "notes": "Closed product; ecosystem search via aliases only.",
    },
    {
        "display_name": "Comate",
        "suggested_id": "comate",
        "aliases": ["Comate", "Baidu Comate", "文心快码"],
        "vendor": "Baidu",
        "primary_type": "ai-assistant",
        "repo": None,
        "website": "https://comate.baidu.com",
        "docs": "https://comate.baidu.com",
        "match_names": ["comate", "文心快码", "baidu comate"],
        "notes": "Closed product likely.",
    },
    {
        "display_name": "CodeGeeX",
        "suggested_id": "codegeex",
        "aliases": ["CodeGeeX", "codegeex", "智谱 CodeGeeX"],
        "vendor": "Zhipu AI",
        "primary_type": "ai-assistant",
        "repo": "THUDM/CodeGeeX",
        "website": "https://codegeex.cn",
        "docs": "https://codegeex.cn",
        "match_names": ["codegeex"],
    },
    {
        "display_name": "Cline",
        "suggested_id": "cline",
        "aliases": ["Cline", "Claude Dev", "cline.bot"],
        "vendor": "Cline",
        "primary_type": "ide-extension",
        "repo": "cline/cline",
        "website": "https://cline.bot",
        "docs": "https://docs.cline.bot",
        "match_names": ["cline", "claude dev"],
    },
    {
        "display_name": "Kilo Code",
        "suggested_id": "kilo-code",
        "aliases": ["Kilo Code", "KiloCode", "kilo-code"],
        "vendor": "Kilo",
        "primary_type": "ide-extension",
        "repo": "Kilo-Org/kilocode",
        "website": "https://kilo.ai",
        "docs": "https://kilo.ai",
        "match_names": ["kilo code", "kilocode", "kilo-code"],
    },
    {
        "display_name": "Junie",
        "suggested_id": "junie",
        "aliases": ["Junie", "JetBrains Junie"],
        "vendor": "JetBrains",
        "primary_type": "ai-assistant",
        "repo": None,
        "website": "https://www.jetbrains.com/junie/",
        "docs": "https://www.jetbrains.com/help/junie/",
        "match_names": ["junie", "jetbrains junie"],
        "notes": "Closed JetBrains product.",
    },
    {
        "display_name": "Continue",
        "suggested_id": "continue",
        "aliases": ["Continue", "Continue.dev", "continue-dev"],
        "vendor": "Continue",
        "primary_type": "ide-extension",
        "repo": "continuedev/continue",
        "website": "https://continue.dev",
        "docs": "https://docs.continue.dev",
        "match_names": ["continue", "continue.dev", "continuedev"],
    },
    {
        "display_name": "Augment Code",
        "suggested_id": "augment-code",
        "aliases": ["Augment Code", "Augment", "augmentcode"],
        "vendor": "Augment",
        "primary_type": "ai-assistant",
        "repo": None,
        "website": "https://www.augmentcode.com",
        "docs": "https://docs.augmentcode.com",
        "match_names": ["augment code", "augmentcode", "augment"],
        "notes": "Likely closed product.",
    },
    {
        "display_name": "Tabnine",
        "suggested_id": "tabnine",
        "aliases": ["Tabnine", "TabNine", "tabnine"],
        "vendor": "Tabnine",
        "primary_type": "ai-assistant",
        "repo": None,
        "website": "https://www.tabnine.com",
        "docs": "https://docs.tabnine.com",
        "match_names": ["tabnine", "tab nine"],
        "notes": "Closed product.",
    },
    {
        "display_name": "Manus",
        "suggested_id": "manus",
        "aliases": ["Manus", "Manus AI", "manus.im"],
        "vendor": "Manus",
        "primary_type": "agent-platform",
        "repo": None,
        "website": "https://manus.im",
        "docs": "https://manus.im",
        "match_names": ["manus", "manus ai"],
        "notes": "Closed agent product; ecosystem mentions only.",
    },
    {
        "display_name": "v0.dev",
        "suggested_id": "v0-dev",
        "aliases": ["v0.dev", "v0", "Vercel v0"],
        "vendor": "Vercel",
        "primary_type": "ai-builder",
        "repo": None,
        "website": "https://v0.dev",
        "docs": "https://v0.dev",
        "match_names": ["v0.dev", "v0", "vercel v0"],
        "notes": "Closed SaaS builder.",
    },
    {
        "display_name": "Lovable",
        "suggested_id": "lovable",
        "aliases": ["Lovable", "Lovable.dev", "GPT Engineer"],
        "vendor": "Lovable",
        "primary_type": "ai-builder",
        "repo": None,
        "website": "https://lovable.dev",
        "docs": "https://docs.lovable.dev",
        "match_names": ["lovable", "lovable.dev", "gpt engineer"],
        "notes": "Closed SaaS; formerly GPT Engineer ecosystem.",
    },
    {
        "display_name": "Replit",
        "suggested_id": "replit",
        "aliases": ["Replit", "Replit Agent", "Ghostwriter"],
        "vendor": "Replit",
        "primary_type": "ai-builder",
        "repo": None,
        "website": "https://replit.com",
        "docs": "https://docs.replit.com",
        "match_names": ["replit", "replit agent", "ghostwriter"],
        "notes": "Closed product platform.",
    },
    {
        "display_name": "Bolt.new",
        "suggested_id": "bolt-new",
        "aliases": ["Bolt.new", "Bolt", "StackBlitz Bolt"],
        "vendor": "StackBlitz",
        "primary_type": "ai-builder",
        "repo": "stackblitz/bolt.new",
        "website": "https://bolt.new",
        "docs": "https://bolt.new",
        "match_names": ["bolt.new", "bolt new", "stackblitz bolt"],
    },
    {
        "display_name": "OpenClaw",
        "suggested_id": "openclaw",
        "aliases": ["OpenClaw", "openclaw"],
        "vendor": "OpenClaw",
        "primary_type": "terminal-agent",
        "repo": None,
        "website": None,
        "docs": None,
        "match_names": ["openclaw"],
        "notes": "Uncertain product identity/repo — user should verify.",
    },
    {
        "display_name": "Hermes Agent",
        "suggested_id": "hermes-agent",
        "aliases": ["Hermes Agent", "Nous Hermes", "Hermes coding agent"],
        "vendor": "Nous Research",
        "primary_type": "persistent-agent",
        "repo": "NousResearch/hermes-agent",
        "website": "https://hermes-agent.nousresearch.com/docs/",
        "docs": "https://hermes-agent.nousresearch.com/docs/",
        "match_names": ["hermes agent", "nous hermes", "hermes-agent"],
    },
]


def _norm(s: str | None) -> str:
    return (s or "").strip().lower().replace("_", "-").replace(" ", "")


def _tool_name_keys(tool: dict) -> set[str]:
    keys = {_norm(tool.get("id")), _norm(tool.get("name"))}
    for a in tool.get("aliases") or []:
        keys.add(_norm(a))
    # also split "A / B" style names
    name = tool.get("name") or ""
    for part in name.replace("/", " ").split():
        keys.add(_norm(part))
    return {k for k in keys if k}


def match_existing_tool(canon: dict, existing: list[dict]) -> dict | None:
    """Return the existing tool that matches a canonical entry, or None."""
    want_id = canon["suggested_id"]
    for tool in existing:
        if tool.get("id") == want_id:
            return tool

    match_names = {_norm(n) for n in canon.get("match_names") or []}
    match_names.add(_norm(canon["display_name"]))
    match_names.add(_norm(want_id))
    # also aliases from canon
    for a in canon.get("aliases") or []:
        match_names.add(_norm(a))

    for tool in existing:
        keys = _tool_name_keys(tool)
        if keys & match_names:
            return tool
    return None


def build_draft_entry(canon: dict) -> dict:
    """Build a new draft seed-tools entry from a canonical definition."""
    repo = canon.get("repo") or None
    entry: dict[str, Any] = {
        "id": canon["suggested_id"],
        "name": canon["display_name"],
        "vendor": canon.get("vendor") or "",
        "primary_type": canon.get("primary_type") or "ai-assistant",
        "repo": repo,
        "website": canon.get("website"),
        "docs": canon.get("docs"),
        "aliases": list(canon.get("aliases") or [canon["display_name"]]),
        "config_files": [],
        "extension_points": [],
        "related_concepts": [],
        "tracking_priority": "medium",
        "status": "draft",
        "tool_kind": "open" if repo else "closed",
        "onboard_state": "pending",
    }
    # Drop empty optional urls for cleaner yaml
    for k in ("website", "docs"):
        if not entry.get(k):
            entry.pop(k, None)
    return normalize_tool_entry(entry)


def _uncertain_fields(entry: dict, canon: dict) -> list[str]:
    uncertain: list[str] = []
    if not entry.get("repo"):
        uncertain.append("repo")
    if not entry.get("website"):
        uncertain.append("website")
    if not entry.get("docs"):
        uncertain.append("docs")
    if not entry.get("vendor"):
        uncertain.append("vendor")
    if canon.get("notes"):
        uncertain.append(f"notes:{canon['notes']}")
    if entry.get("tool_kind") == "closed":
        uncertain.append("tool_kind=closed (confirm)")
    return uncertain


def plan_drafts(existing: list[dict]) -> dict:
    """Plan which canonical tools already match and which need draft inserts."""
    matched: list[dict] = []
    to_add: list[dict] = []
    match_rows: list[dict] = []

    for canon in CANONICAL_31:
        hit = match_existing_tool(canon, existing)
        if hit is not None:
            matched.append(hit)
            match_rows.append(
                {
                    "display_name": canon["display_name"],
                    "suggested_id": canon["suggested_id"],
                    "existing_id": hit.get("id"),
                    "existing_status": hit.get("status", "active"),
                    "action": "keep",
                    "notes": canon.get("notes") or "",
                }
            )
        else:
            draft = build_draft_entry(canon)
            to_add.append(draft)
            match_rows.append(
                {
                    "display_name": canon["display_name"],
                    "suggested_id": canon["suggested_id"],
                    "existing_id": None,
                    "existing_status": None,
                    "action": "add_draft",
                    "notes": canon.get("notes") or "",
                    "uncertain": _uncertain_fields(draft, canon),
                    "draft": draft,
                }
            )

    # Preserve existing order, append new drafts
    existing_ids = {t.get("id") for t in existing}
    merged = list(existing)
    for d in to_add:
        if d["id"] not in existing_ids:
            merged.append(d)
            existing_ids.add(d["id"])

    return {
        "matched": matched,
        "to_add": to_add,
        "merged": merged,
        "rows": match_rows,
        "existing_count": len(existing),
        "target_count": len(CANONICAL_31),
    }


def render_review_report(plan: dict) -> str:
    """Human-readable markdown review report."""
    lines: list[str] = []
    lines.append("# seed-tools draft review — 31 工具封闭名单")
    lines.append("")
    lines.append(f"> 生成自 `scripts/draft_seed_tools.py`。现有 **{plan['existing_count']}** 条，")
    lines.append(f"目标 **{plan['target_count']}**，本次新增草稿 **{len(plan['to_add'])}** 条。")
    lines.append("")
    lines.append("## 使用说明")
    lines.append("")
    lines.append("1. 审阅下方「新增草稿」与「不确定字段」")
    lines.append("2. 修正 `data/seed-tools.yaml` 中的 id / name / aliases / repo")
    lines.append("3. 确认项：`status: draft` → `status: active`")
    lines.append("4. **CodeBuddy** 必须复用已有 `workbuddy-codebuddy`，勿新建 `codebuddy`")
    lines.append("5. 确认后由执行 Agent 跑 `onboard_tool.py --all-pending`（勿在审前全量 active）")
    lines.append("")
    lines.append("## 已匹配（保留，不重复插入）")
    lines.append("")
    lines.append("| 展示名 | 建议 id | 现有 id | status | 备注 |")
    lines.append("|--------|---------|---------|--------|------|")
    for row in plan["rows"]:
        if row["action"] != "keep":
            continue
        notes = row.get("notes") or ""
        lines.append(
            f"| {row['display_name']} | `{row['suggested_id']}` | `{row['existing_id']}` | "
            f"{row['existing_status']} | {notes} |"
        )
    lines.append("")
    lines.append("## 新增草稿（status=draft）")
    lines.append("")
    if not plan["to_add"]:
        lines.append("_无新增项。_")
        lines.append("")
    else:
        lines.append("| 展示名 | id | tool_kind | repo | 不确定字段 |")
        lines.append("|--------|-----|-----------|------|------------|")
        for row in plan["rows"]:
            if row["action"] != "add_draft":
                continue
            draft = row["draft"]
            uncertain = ", ".join(row.get("uncertain") or []) or "—"
            repo = draft.get("repo") or "null"
            lines.append(
                f"| {row['display_name']} | `{draft['id']}` | {draft.get('tool_kind')} | "
                f"`{repo}` | {uncertain} |"
            )
        lines.append("")
        lines.append("### 草稿明细")
        lines.append("")
        for row in plan["rows"]:
            if row["action"] != "add_draft":
                continue
            draft = row["draft"]
            lines.append(f"#### {row['display_name']} (`{draft['id']}`)")
            lines.append("")
            lines.append(f"- **vendor:** {draft.get('vendor') or '—'}")
            lines.append(f"- **primary_type:** {draft.get('primary_type')}")
            lines.append(f"- **repo:** `{draft.get('repo')}`")
            lines.append(f"- **website:** {draft.get('website') or '—'}")
            lines.append(f"- **aliases:** {', '.join(draft.get('aliases') or [])}")
            lines.append(f"- **tool_kind:** {draft.get('tool_kind')}")
            lines.append(f"- **status:** draft / **onboard_state:** pending")
            uncertain = row.get("uncertain") or []
            if uncertain:
                lines.append(f"- **不确定字段:** {', '.join(uncertain)}")
            if row.get("notes"):
                lines.append(f"- **备注:** {row['notes']}")
            lines.append("")

    lines.append("## 合并策略提醒")
    lines.append("")
    lines.append("- **CodeBuddy** ↔ 现有 `workbuddy-codebuddy`（已匹配则本报告「已匹配」区可见）")
    lines.append("- **Codex** ↔ 现有 `codex-cli`")
    lines.append("- **Antigravity** ↔ 现有 `antigravity-cli`")
    lines.append("- 闭源/无主仓：`tool_kind=closed`，`repo: null`，仍用 aliases 做生态查询")
    lines.append("- 封闭名单：不自动发现第 32 个工具")
    lines.append("")
    lines.append("## 下一步")
    lines.append("")
    lines.append("```bash")
    lines.append("# 用户审改完成后：")
    lines.append("python3 scripts/seed_tools_schema.py --validate --list-active")
    lines.append("python3 scripts/derive_queries.py --dry-run")
    lines.append("python3 scripts/onboard_tool.py --all-pending --dry-run")
    lines.append("# 用户明确授权后再真实 onboard")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def apply_plan(plan: dict, dry_run: bool = True) -> dict:
    """Optionally write seed-tools + review report. Returns summary."""
    merged = plan["merged"]
    errors = validate_tools(merged)
    if errors:
        return {"ok": False, "errors": errors}

    report = render_review_report(plan)
    summary = {
        "ok": True,
        "existing": plan["existing_count"],
        "added": len(plan["to_add"]),
        "total": len(merged),
        "dry_run": dry_run,
        "report_path": str(REVIEW_REPORT_PATH.relative_to(ROOT)),
        "new_ids": [t["id"] for t in plan["to_add"]],
    }

    if dry_run:
        print(f"[dry-run] would keep {plan['existing_count']} existing tools")
        print(f"[dry-run] would add {len(plan['to_add'])} draft tools: {summary['new_ids']}")
        print(f"[dry-run] would write report to {summary['report_path']}")
        print(f"[dry-run] merged total would be {len(merged)}")
        return summary

    save_seed_tools(merged)
    REVIEW_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {SEED_TOOLS_PATH}: total={len(merged)}, added={len(plan['to_add'])}")
    print(f"Wrote {summary['report_path']}")
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Draft missing seed-tools for closed 31 list")
    ap.add_argument("--dry-run", action="store_true", help="Plan only, do not write files")
    ap.add_argument("--apply", action="store_true", help="Write seed-tools.yaml + review report")
    ap.add_argument(
        "--report-only",
        action="store_true",
        help="Write review report from current plan without modifying seed-tools",
    )
    args = ap.parse_args(argv)

    if not args.dry_run and not args.apply and not args.report_only:
        # default to dry-run for safety
        args.dry_run = True

    existing = load_seed_tools(normalize=True)
    plan = plan_drafts(existing)

    if args.report_only:
        report = render_review_report(plan)
        REVIEW_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REVIEW_REPORT_PATH.write_text(report, encoding="utf-8")
        print(f"Wrote report only: {REVIEW_REPORT_PATH.relative_to(ROOT)}")
        print(f"matched={len(plan['matched'])} to_add={len(plan['to_add'])}")
        return 0

    summary = apply_plan(plan, dry_run=not args.apply)
    if not summary.get("ok"):
        print("VALIDATION ERRORS:")
        for e in summary.get("errors") or []:
            print(f"  - {e}")
        return 1

    print(
        f"OK: existing={summary['existing']} added={summary['added']} "
        f"total={summary['total']} dry_run={summary['dry_run']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
