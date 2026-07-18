#!/usr/bin/env python3
"""Build 10-theme comparison preview from the v2 architecture preview."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "ecoradar-redesign-preview.html"
OUT = ROOT / "ecoradar-10-styles-preview.html"
INDEX = ROOT / "index.html"

THEMES = {
    "soft-observatory": {
        "label": "01 Soft Observatory",
        "blurb": "深蓝夜空 + 薄荷绿/淡紫 · 你认可的 v2 方向",
        "mode": "dark",
        "vars": {
            "--bg": "#0B1020",
            "--bg-2": "#12182B",
            "--panel": "#171E35",
            "--panel-2": "#1D2642",
            "--card": "#1A223A",
            "--card-hover": "#222C4A",
            "--line": "rgba(232,236,247,0.10)",
            "--line-strong": "rgba(232,236,247,0.16)",
            "--text": "#EEF2FF",
            "--text-2": "#C4CCE3",
            "--muted": "#8E9AB8",
            "--accent": "#5EEAD4",
            "--accent-2": "#2DD4BF",
            "--accent-soft": "rgba(94,234,212,0.12)",
            "--secondary": "#A78BFA",
            "--secondary-soft": "rgba(167,139,250,0.12)",
            "--warm": "#F0C674",
            "--warm-soft": "rgba(240,198,116,0.12)",
            "--danger": "#FB7185",
            "--ok": "#6EE7B7",
            "--radius": "16px",
            "--radius-sm": "12px",
            "--shadow": "0 16px 40px rgba(3,7,18,0.35)",
            "--font": 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
            "--mono": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "--page-bg": "radial-gradient(900px 420px at 8% -10%, rgba(94,234,212,.08), transparent 55%), radial-gradient(800px 380px at 96% 0%, rgba(167,139,250,.08), transparent 50%), linear-gradient(180deg, #0D1324 0%, #0B1020 40%, #090E1A 100%)",
            "--header-bg": "linear-gradient(180deg, rgba(255,255,255,.02), transparent)",
            "--card-bg": "linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.015))",
            "--card-hover-bg": "linear-gradient(180deg, rgba(94,234,212,.06), rgba(255,255,255,.02))",
            "--accent-grad": "linear-gradient(90deg, #5EEAD4, #A78BFA)",
            "--score-grad": "linear-gradient(180deg, #8AF5E3, #57D9C5)",
            "--score-text": "#06201C",
            "--banner-bg": "rgba(18,16,10,.88)",
            "--banner-border": "rgba(240,198,116,.22)",
            "--banner-text": "#F8E7B8",
            "--detail-bg": "#12192E",
            "--modal-bg": "#12192E",
            "--table-head-bg": "rgba(17,24,42,.96)",
            "--input-bg": "rgba(0,0,0,.18)",
            "--chart-fill": "linear-gradient(180deg, rgba(94,234,212,.85), rgba(167,139,250,.35))",
            "--radius-pill": "999px",
            "--letter": "-0.02em",
            "--h1-weight": "750",
        },
    },
    "warm-paper": {
        "label": "02 Warm Paper Dark",
        "blurb": "现站琥珀暖纸深色 · 对照基线",
        "mode": "dark",
        "vars": {
            "--bg": "#1c1917",
            "--bg-2": "#24201c",
            "--panel": "#292524",
            "--panel-2": "#35302c",
            "--card": "#2c2825",
            "--card-hover": "#35302c",
            "--line": "rgba(255,248,240,0.10)",
            "--line-strong": "rgba(255,248,240,0.16)",
            "--text": "#faf7f2",
            "--text-2": "#e7e0d6",
            "--muted": "#b5aa9c",
            "--accent": "#f59e0b",
            "--accent-2": "#fbbf24",
            "--accent-soft": "rgba(245,158,11,0.14)",
            "--secondary": "#fbbf24",
            "--secondary-soft": "rgba(251,191,36,0.12)",
            "--warm": "#fcd34d",
            "--warm-soft": "rgba(252,211,77,0.12)",
            "--danger": "#f87171",
            "--ok": "#34d399",
            "--radius": "16px",
            "--radius-sm": "12px",
            "--shadow": "0 10px 30px rgba(0,0,0,0.28)",
            "--font": 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
            "--mono": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "--page-bg": "linear-gradient(180deg, #24201c 0%, #1c1917 100%)",
            "--header-bg": "linear-gradient(180deg, #24201c 0%, #1c1917 100%)",
            "--card-bg": "linear-gradient(180deg, #2f2a26, #2c2825)",
            "--card-hover-bg": "linear-gradient(180deg, #3a342f, #35302c)",
            "--accent-grad": "linear-gradient(135deg, #f59e0b, #fbbf24)",
            "--score-grad": "linear-gradient(180deg, #fbbf24, #f59e0b)",
            "--score-text": "#1c1405",
            "--banner-bg": "rgba(28,25,23,.9)",
            "--banner-border": "rgba(245,158,11,.25)",
            "--banner-text": "#fde68a",
            "--detail-bg": "#292524",
            "--modal-bg": "#292524",
            "--table-head-bg": "rgba(28,25,23,.96)",
            "--input-bg": "#1a1714",
            "--chart-fill": "linear-gradient(180deg, rgba(251,191,36,.85), rgba(245,158,11,.35))",
            "--radius-pill": "999px",
            "--letter": "-0.03em",
            "--h1-weight": "700",
        },
    },
    "linear-midnight": {
        "label": "03 Linear Midnight",
        "blurb": "近黑 + 靛紫强调 · 克制、锐利、产品工具感",
        "mode": "dark",
        "vars": {
            "--bg": "#0A0A0B",
            "--bg-2": "#111113",
            "--panel": "#161618",
            "--panel-2": "#1C1C1F",
            "--card": "#141416",
            "--card-hover": "#1A1A1D",
            "--line": "rgba(255,255,255,0.08)",
            "--line-strong": "rgba(255,255,255,0.12)",
            "--text": "#EDEDEF",
            "--text-2": "#B4B4BB",
            "--muted": "#8A8A93",
            "--accent": "#8B5CF6",
            "--accent-2": "#A78BFA",
            "--accent-soft": "rgba(139,92,246,0.14)",
            "--secondary": "#60A5FA",
            "--secondary-soft": "rgba(96,165,250,0.12)",
            "--warm": "#F5D0FE",
            "--warm-soft": "rgba(245,208,254,0.10)",
            "--danger": "#FB7185",
            "--ok": "#4ADE80",
            "--radius": "10px",
            "--radius-sm": "8px",
            "--shadow": "0 0 0 1px rgba(255,255,255,0.04), 0 12px 32px rgba(0,0,0,.45)",
            "--font": 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans SC", "PingFang SC", sans-serif',
            "--mono": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "--page-bg": "#0A0A0B",
            "--header-bg": "rgba(10,10,11,.9)",
            "--card-bg": "#141416",
            "--card-hover-bg": "#1A1A1D",
            "--accent-grad": "linear-gradient(90deg, #8B5CF6, #60A5FA)",
            "--score-grad": "linear-gradient(180deg, #A78BFA, #7C3AED)",
            "--score-text": "#12081f",
            "--banner-bg": "rgba(10,10,11,.92)",
            "--banner-border": "rgba(139,92,246,.28)",
            "--banner-text": "#DDD6FE",
            "--detail-bg": "#111113",
            "--modal-bg": "#111113",
            "--table-head-bg": "rgba(10,10,11,.96)",
            "--input-bg": "#0F0F10",
            "--chart-fill": "linear-gradient(180deg, rgba(139,92,246,.85), rgba(96,165,250,.3))",
            "--radius-pill": "8px",
            "--letter": "-0.04em",
            "--h1-weight": "650",
        },
    },
    "aurora-glass": {
        "label": "04 Aurora Glass",
        "blurb": "毛玻璃 + 青品红极光 · 更亮眼、氛围更强",
        "mode": "dark",
        "vars": {
            "--bg": "#07101F",
            "--bg-2": "#0B1730",
            "--panel": "rgba(18,30,58,.72)",
            "--panel-2": "rgba(28,44,80,.7)",
            "--card": "rgba(20,34,64,.55)",
            "--card-hover": "rgba(30,48,86,.7)",
            "--line": "rgba(186,230,253,0.14)",
            "--line-strong": "rgba(186,230,253,0.22)",
            "--text": "#F0F9FF",
            "--text-2": "#C7E7FF",
            "--muted": "#8FB4D6",
            "--accent": "#22D3EE",
            "--accent-2": "#67E8F9",
            "--accent-soft": "rgba(34,211,238,0.14)",
            "--secondary": "#F472B6",
            "--secondary-soft": "rgba(244,114,182,0.14)",
            "--warm": "#FDE68A",
            "--warm-soft": "rgba(253,230,138,0.12)",
            "--danger": "#FB7185",
            "--ok": "#4ADE80",
            "--radius": "20px",
            "--radius-sm": "14px",
            "--shadow": "0 20px 50px rgba(2,8,23,.45)",
            "--font": 'system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans SC", "PingFang SC", sans-serif',
            "--mono": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "--page-bg": "radial-gradient(700px 380px at 15% 0%, rgba(34,211,238,.18), transparent 55%), radial-gradient(700px 420px at 90% 10%, rgba(244,114,182,.16), transparent 50%), radial-gradient(600px 360px at 50% 100%, rgba(99,102,241,.12), transparent 55%), #07101F",
            "--header-bg": "linear-gradient(180deg, rgba(255,255,255,.04), transparent)",
            "--card-bg": "linear-gradient(160deg, rgba(255,255,255,.08), rgba(255,255,255,.02))",
            "--card-hover-bg": "linear-gradient(160deg, rgba(34,211,238,.12), rgba(244,114,182,.06))",
            "--accent-grad": "linear-gradient(90deg, #22D3EE, #F472B6)",
            "--score-grad": "linear-gradient(180deg, #67E8F9, #22D3EE)",
            "--score-text": "#042f2e",
            "--banner-bg": "rgba(7,16,31,.78)",
            "--banner-border": "rgba(34,211,238,.25)",
            "--banner-text": "#CFFAFE",
            "--detail-bg": "rgba(10,18,36,.92)",
            "--modal-bg": "rgba(10,18,36,.94)",
            "--table-head-bg": "rgba(8,15,30,.92)",
            "--input-bg": "rgba(3,10,22,.45)",
            "--chart-fill": "linear-gradient(180deg, rgba(34,211,238,.85), rgba(244,114,182,.35))",
            "--radius-pill": "999px",
            "--letter": "-0.02em",
            "--h1-weight": "750",
        },
    },
    "editorial-light": {
        "label": "05 Editorial Light",
        "blurb": "浅色纸感 + 墨色排版 · 长读友好、偏编辑部",
        "mode": "light",
        "vars": {
            "--bg": "#F6F1E8",
            "--bg-2": "#FFFDF8",
            "--panel": "#FFFFFF",
            "--panel-2": "#F3EEE4",
            "--card": "#FFFFFF",
            "--card-hover": "#FFF9F0",
            "--line": "rgba(28,25,23,0.10)",
            "--line-strong": "rgba(28,25,23,0.16)",
            "--text": "#1C1917",
            "--text-2": "#44403C",
            "--muted": "#78716C",
            "--accent": "#0F766E",
            "--accent-2": "#0D9488",
            "--accent-soft": "rgba(15,118,110,0.10)",
            "--secondary": "#9A3412",
            "--secondary-soft": "rgba(154,52,18,0.08)",
            "--warm": "#B45309",
            "--warm-soft": "rgba(180,83,9,0.08)",
            "--danger": "#DC2626",
            "--ok": "#15803D",
            "--radius": "14px",
            "--radius-sm": "10px",
            "--shadow": "0 10px 30px rgba(28,25,23,0.06)",
            "--font": 'Georgia, "Songti SC", "Noto Serif SC", "Times New Roman", serif',
            "--mono": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "--page-bg": "linear-gradient(180deg, #FBF7F0 0%, #F6F1E8 100%)",
            "--header-bg": "linear-gradient(180deg, #FFFDF8, #F6F1E8)",
            "--card-bg": "#FFFFFF",
            "--card-hover-bg": "#FFF9F0",
            "--accent-grad": "linear-gradient(90deg, #0F766E, #B45309)",
            "--score-grad": "linear-gradient(180deg, #14B8A6, #0F766E)",
            "--score-text": "#042f2e",
            "--banner-bg": "rgba(255,253,248,.92)",
            "--banner-border": "rgba(15,118,110,.2)",
            "--banner-text": "#44403C",
            "--detail-bg": "#FFFDF8",
            "--modal-bg": "#FFFDF8",
            "--table-head-bg": "rgba(246,241,232,.96)",
            "--input-bg": "#FFFDF8",
            "--chart-fill": "linear-gradient(180deg, rgba(15,118,110,.75), rgba(180,83,9,.25))",
            "--radius-pill": "999px",
            "--letter": "-0.01em",
            "--h1-weight": "700",
        },
    },
    "terminal-green": {
        "label": "06 Terminal Green",
        "blurb": "CRT 终端绿 · 编码工具原生气质",
        "mode": "dark",
        "vars": {
            "--bg": "#050805",
            "--bg-2": "#0A120C",
            "--panel": "#0D1610",
            "--panel-2": "#132018",
            "--card": "#0E1712",
            "--card-hover": "#14241A",
            "--line": "rgba(110,231,183,0.14)",
            "--line-strong": "rgba(110,231,183,0.22)",
            "--text": "#D1FAE5",
            "--text-2": "#A7F3D0",
            "--muted": "#6EE7B7",
            "--accent": "#34D399",
            "--accent-2": "#6EE7B7",
            "--accent-soft": "rgba(52,211,153,0.12)",
            "--secondary": "#86EFAC",
            "--secondary-soft": "rgba(134,239,172,0.10)",
            "--warm": "#FDE68A",
            "--warm-soft": "rgba(253,230,138,0.10)",
            "--danger": "#F87171",
            "--ok": "#4ADE80",
            "--radius": "8px",
            "--radius-sm": "6px",
            "--shadow": "0 0 0 1px rgba(52,211,153,.08), 0 12px 28px rgba(0,0,0,.5)",
            "--font": '"IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
            "--mono": '"IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
            "--page-bg": "radial-gradient(800px 400px at 50% -10%, rgba(52,211,153,.08), transparent 55%), #050805",
            "--header-bg": "linear-gradient(180deg, rgba(52,211,153,.05), transparent)",
            "--card-bg": "linear-gradient(180deg, rgba(52,211,153,.04), rgba(0,0,0,.15))",
            "--card-hover-bg": "linear-gradient(180deg, rgba(52,211,153,.08), rgba(0,0,0,.1))",
            "--accent-grad": "linear-gradient(90deg, #34D399, #86EFAC)",
            "--score-grad": "linear-gradient(180deg, #6EE7B7, #10B981)",
            "--score-text": "#022c22",
            "--banner-bg": "rgba(5,8,5,.92)",
            "--banner-border": "rgba(52,211,153,.28)",
            "--banner-text": "#A7F3D0",
            "--detail-bg": "#0A120C",
            "--modal-bg": "#0A120C",
            "--table-head-bg": "rgba(5,8,5,.96)",
            "--input-bg": "#040704",
            "--chart-fill": "linear-gradient(180deg, rgba(52,211,153,.85), rgba(16,185,129,.25))",
            "--radius-pill": "6px",
            "--letter": "0",
            "--h1-weight": "600",
        },
    },
    "coral-harbor": {
        "label": "07 Coral Harbor",
        "blurb": "海港蓝 + 珊瑚橙 · 柔和友好、不霓虹",
        "mode": "dark",
        "vars": {
            "--bg": "#0E1A24",
            "--bg-2": "#152433",
            "--panel": "#1A2B3C",
            "--panel-2": "#22374C",
            "--card": "#1B2D3F",
            "--card-hover": "#24384D",
            "--line": "rgba(207,226,240,0.12)",
            "--line-strong": "rgba(207,226,240,0.18)",
            "--text": "#F2F7FB",
            "--text-2": "#C9D9E6",
            "--muted": "#8FA8BB",
            "--accent": "#FF7A59",
            "--accent-2": "#FF9B82",
            "--accent-soft": "rgba(255,122,89,0.14)",
            "--secondary": "#5EC8E8",
            "--secondary-soft": "rgba(94,200,232,0.12)",
            "--warm": "#FFD29A",
            "--warm-soft": "rgba(255,210,154,0.12)",
            "--danger": "#FB7185",
            "--ok": "#4ADE80",
            "--radius": "18px",
            "--radius-sm": "12px",
            "--shadow": "0 16px 40px rgba(5,12,20,.4)",
            "--font": 'system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans SC", "PingFang SC", sans-serif',
            "--mono": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "--page-bg": "radial-gradient(800px 420px at 10% 0%, rgba(255,122,89,.10), transparent 55%), radial-gradient(700px 380px at 90% 10%, rgba(94,200,232,.10), transparent 50%), linear-gradient(180deg, #122131, #0E1A24 50%, #0B151E)",
            "--header-bg": "linear-gradient(180deg, rgba(255,255,255,.03), transparent)",
            "--card-bg": "linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.015))",
            "--card-hover-bg": "linear-gradient(180deg, rgba(255,122,89,.08), rgba(255,255,255,.02))",
            "--accent-grad": "linear-gradient(90deg, #FF7A59, #5EC8E8)",
            "--score-grad": "linear-gradient(180deg, #FF9B82, #FF7A59)",
            "--score-text": "#3b1208",
            "--banner-bg": "rgba(14,26,36,.9)",
            "--banner-border": "rgba(255,122,89,.25)",
            "--banner-text": "#FFD2C6",
            "--detail-bg": "#152433",
            "--modal-bg": "#152433",
            "--table-head-bg": "rgba(14,26,36,.96)",
            "--input-bg": "rgba(8,16,24,.45)",
            "--chart-fill": "linear-gradient(180deg, rgba(255,122,89,.8), rgba(94,200,232,.3))",
            "--radius-pill": "999px",
            "--letter": "-0.02em",
            "--h1-weight": "750",
        },
    },
    "slate-swiss": {
        "label": "08 Slate Swiss",
        "blurb": "浅灰瑞士风 · 高密度、冷静、信息优先",
        "mode": "light",
        "vars": {
            "--bg": "#EEF1F4",
            "--bg-2": "#F7F8FA",
            "--panel": "#FFFFFF",
            "--panel-2": "#E8ECF0",
            "--card": "#FFFFFF",
            "--card-hover": "#F8FAFC",
            "--line": "rgba(15,23,42,0.10)",
            "--line-strong": "rgba(15,23,42,0.16)",
            "--text": "#0F172A",
            "--text-2": "#334155",
            "--muted": "#64748B",
            "--accent": "#2563EB",
            "--accent-2": "#3B82F6",
            "--accent-soft": "rgba(37,99,235,0.10)",
            "--secondary": "#0F172A",
            "--secondary-soft": "rgba(15,23,42,0.06)",
            "--warm": "#EA580C",
            "--warm-soft": "rgba(234,88,12,0.08)",
            "--danger": "#DC2626",
            "--ok": "#16A34A",
            "--radius": "6px",
            "--radius-sm": "4px",
            "--shadow": "0 1px 0 rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.06)",
            "--font": 'Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans SC", "PingFang SC", sans-serif',
            "--mono": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "--page-bg": "#EEF1F4",
            "--header-bg": "#F7F8FA",
            "--card-bg": "#FFFFFF",
            "--card-hover-bg": "#F8FAFC",
            "--accent-grad": "linear-gradient(90deg, #2563EB, #0F172A)",
            "--score-grad": "linear-gradient(180deg, #60A5FA, #2563EB)",
            "--score-text": "#eff6ff",
            "--banner-bg": "rgba(247,248,250,.94)",
            "--banner-border": "rgba(37,99,235,.2)",
            "--banner-text": "#1E293B",
            "--detail-bg": "#FFFFFF",
            "--modal-bg": "#FFFFFF",
            "--table-head-bg": "rgba(238,241,244,.96)",
            "--input-bg": "#FFFFFF",
            "--chart-fill": "linear-gradient(180deg, rgba(37,99,235,.8), rgba(15,23,42,.2))",
            "--radius-pill": "4px",
            "--letter": "-0.03em",
            "--h1-weight": "700",
        },
    },
    "copper-instrument": {
        "label": "09 Copper Instrument",
        "blurb": "铜质仪表盘 · 深褐金属感、观测仪器气质",
        "mode": "dark",
        "vars": {
            "--bg": "#140F0C",
            "--bg-2": "#1C1612",
            "--panel": "#241C16",
            "--panel-2": "#2E241C",
            "--card": "#221B15",
            "--card-hover": "#2C231B",
            "--line": "rgba(245,210,170,0.12)",
            "--line-strong": "rgba(245,210,170,0.18)",
            "--text": "#F8EFE4",
            "--text-2": "#E4D2BC",
            "--muted": "#B59A7D",
            "--accent": "#D97706",
            "--accent-2": "#F59E0B",
            "--accent-soft": "rgba(217,119,6,0.14)",
            "--secondary": "#B45309",
            "--secondary-soft": "rgba(180,83,9,0.12)",
            "--warm": "#FBBF24",
            "--warm-soft": "rgba(251,191,36,0.12)",
            "--danger": "#F87171",
            "--ok": "#34D399",
            "--radius": "12px",
            "--radius-sm": "10px",
            "--shadow": "0 16px 40px rgba(0,0,0,.45)",
            "--font": 'system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans SC", "PingFang SC", sans-serif',
            "--mono": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "--page-bg": "radial-gradient(700px 360px at 20% 0%, rgba(217,119,6,.10), transparent 55%), linear-gradient(180deg, #1A1410, #140F0C 55%, #100C09)",
            "--header-bg": "linear-gradient(180deg, rgba(217,119,6,.05), transparent)",
            "--card-bg": "linear-gradient(180deg, rgba(245,210,170,.04), rgba(0,0,0,.12))",
            "--card-hover-bg": "linear-gradient(180deg, rgba(217,119,6,.08), rgba(0,0,0,.08))",
            "--accent-grad": "linear-gradient(90deg, #D97706, #FBBF24)",
            "--score-grad": "linear-gradient(180deg, #FBBF24, #D97706)",
            "--score-text": "#2a1703",
            "--banner-bg": "rgba(20,15,12,.92)",
            "--banner-border": "rgba(217,119,6,.28)",
            "--banner-text": "#FDE68A",
            "--detail-bg": "#1C1612",
            "--modal-bg": "#1C1612",
            "--table-head-bg": "rgba(20,15,12,.96)",
            "--input-bg": "rgba(8,6,4,.4)",
            "--chart-fill": "linear-gradient(180deg, rgba(251,191,36,.8), rgba(180,83,9,.3))",
            "--radius-pill": "999px",
            "--letter": "-0.02em",
            "--h1-weight": "750",
        },
    },
    "sakura-dusk": {
        "label": "10 Sakura Dusk",
        "blurb": "暮色粉紫 · 柔和、偏产品展示但不甜腻",
        "mode": "dark",
        "vars": {
            "--bg": "#17111A",
            "--bg-2": "#211728",
            "--panel": "#2A1D33",
            "--panel-2": "#352640",
            "--card": "#261C2F",
            "--card-hover": "#31243C",
            "--line": "rgba(244,214,232,0.12)",
            "--line-strong": "rgba(244,214,232,0.18)",
            "--text": "#FBF4F8",
            "--text-2": "#E8D5E1",
            "--muted": "#B79AAD",
            "--accent": "#F9A8D4",
            "--accent-2": "#FBCFE8",
            "--accent-soft": "rgba(249,168,212,0.14)",
            "--secondary": "#C4B5FD",
            "--secondary-soft": "rgba(196,181,253,0.12)",
            "--warm": "#FDE68A",
            "--warm-soft": "rgba(253,230,138,0.10)",
            "--danger": "#FB7185",
            "--ok": "#86EFAC",
            "--radius": "18px",
            "--radius-sm": "12px",
            "--shadow": "0 18px 42px rgba(10,5,14,.45)",
            "--font": 'system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans SC", "PingFang SC", sans-serif',
            "--mono": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "--page-bg": "radial-gradient(800px 420px at 12% 0%, rgba(249,168,212,.12), transparent 55%), radial-gradient(700px 380px at 90% 8%, rgba(196,181,253,.12), transparent 50%), linear-gradient(180deg, #1D1422, #17111A 50%, #120D16)",
            "--header-bg": "linear-gradient(180deg, rgba(249,168,212,.05), transparent)",
            "--card-bg": "linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.015))",
            "--card-hover-bg": "linear-gradient(180deg, rgba(249,168,212,.08), rgba(255,255,255,.02))",
            "--accent-grad": "linear-gradient(90deg, #F9A8D4, #C4B5FD)",
            "--score-grad": "linear-gradient(180deg, #FBCFE8, #F9A8D4)",
            "--score-text": "#4a044e",
            "--banner-bg": "rgba(23,17,26,.9)",
            "--banner-border": "rgba(249,168,212,.25)",
            "--banner-text": "#FCE7F3",
            "--detail-bg": "#211728",
            "--modal-bg": "#211728",
            "--table-head-bg": "rgba(23,17,26,.96)",
            "--input-bg": "rgba(12,8,14,.4)",
            "--chart-fill": "linear-gradient(180deg, rgba(249,168,212,.8), rgba(196,181,253,.3))",
            "--radius-pill": "999px",
            "--letter": "-0.02em",
            "--h1-weight": "750",
        },
    },
}

assert len(THEMES) == 10


def theme_blocks() -> str:
    chunks = []
    for tid, theme in THEMES.items():
        lines = [f'html[data-theme="{tid}"] {{']
        for key, value in theme["vars"].items():
            lines.append(f"  {key}: {value};")
        lines.append("}")
        chunks.append("\n".join(lines))
    return "\n\n".join(chunks)


COMMON_CSS = r"""
    :root {
      --max: 1320px;
      --ease: cubic-bezier(0.22, 1, 0.36, 1);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }
    body {
      font-family: var(--font);
      background: var(--page-bg);
      color: var(--text);
      font-size: 14px;
      line-height: 1.55;
      min-height: 100vh;
    }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    button, input, select { font: inherit; color: inherit; }
    button { cursor: pointer; }
    .wrap { width: min(var(--max), calc(100% - 40px)); margin: 0 auto; }

    .preview-banner {
      position: sticky; top: 0; z-index: 50;
      background: var(--banner-bg);
      border-bottom: 1px solid var(--banner-border);
      color: var(--banner-text);
      font-size: 12px;
      text-align: center;
      padding: 10px 14px;
      backdrop-filter: blur(10px);
    }
    .preview-banner strong { color: var(--warm); }

    .theme-dock {
      position: sticky; top: 41px; z-index: 49;
      background: color-mix(in srgb, var(--bg) 88%, transparent);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--line);
      padding: 10px 0;
    }
    .theme-dock-inner {
      width: min(var(--max), calc(100% - 40px));
      margin: 0 auto;
      display: grid;
      gap: 8px;
    }
    .theme-dock-label {
      font-size: 11px;
      color: var(--muted);
      letter-spacing: .06em;
      text-transform: uppercase;
    }
    .theme-tabs { display: flex; flex-wrap: wrap; gap: 6px; }
    .theme-tab {
      border: 1px solid var(--line);
      background: color-mix(in srgb, var(--panel) 80%, transparent);
      color: var(--text-2);
      border-radius: var(--radius-pill);
      padding: 7px 10px;
      font-size: 12px;
      font-weight: 650;
      transition: .15s var(--ease);
    }
    .theme-tab:hover { border-color: var(--line-strong); color: var(--text); }
    .theme-tab.active {
      color: var(--accent);
      border-color: color-mix(in srgb, var(--accent) 45%, transparent);
      background: var(--accent-soft);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 10%, transparent);
    }
    .theme-blurb { color: var(--muted); font-size: 12px; }

    header {
      padding: 28px 0 18px;
      border-bottom: 1px solid var(--line);
      background: var(--header-bg);
    }
    .topbar {
      display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; flex-wrap: wrap;
    }
    .brand-row { display: flex; gap: 14px; align-items: flex-start; min-width: 0; }
    .mark {
      width: 40px; height: 40px; border-radius: 12px; flex: 0 0 auto;
      border: 1px solid color-mix(in srgb, var(--accent) 40%, transparent);
      background:
        radial-gradient(circle at 50% 50%, color-mix(in srgb, var(--accent) 22%, transparent), transparent 58%),
        linear-gradient(145deg, var(--panel-2), var(--bg-2));
      position: relative;
      box-shadow: inset 0 0 16px color-mix(in srgb, var(--accent) 10%, transparent);
    }
    .mark::before, .mark::after {
      content: ""; position: absolute; left: 50%; top: 50%;
      transform: translate(-50%,-50%); border-radius: 50%;
      border: 1px solid color-mix(in srgb, var(--accent) 50%, transparent);
    }
    .mark::before { width: 18px; height: 18px; }
    .mark::after {
      width: 7px; height: 7px; background: var(--accent); border: 0;
      box-shadow: 0 0 10px color-mix(in srgb, var(--accent) 70%, transparent);
    }
    h1 {
      font-size: 25px; font-weight: var(--h1-weight); letter-spacing: var(--letter); margin-bottom: 6px;
    }
    .subtitle { color: var(--text-2); font-size: 13px; max-width: 56ch; }

    .lang-switch {
      display: inline-flex; gap: 4px; padding: 4px;
      background: color-mix(in srgb, var(--text) 3%, transparent); border: 1px solid var(--line);
      border-radius: var(--radius-pill);
    }
    .lang-switch button {
      border: 0; background: transparent; color: var(--muted);
      padding: 7px 12px; border-radius: var(--radius-pill); font-size: 12px; font-weight: 600;
    }
    .lang-switch button.active,
    .lang-switch button[aria-pressed="true"] {
      background: var(--accent-soft); color: var(--accent);
    }

    nav {
      margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center;
    }
    .fav-btn, .ghost-btn, .page-btn, .modal-close, .mode-toggle button {
      border: 1px solid var(--line-strong);
      background: color-mix(in srgb, var(--text) 3%, transparent);
      color: var(--text-2);
      border-radius: var(--radius-sm);
      padding: 9px 12px;
      transition: background .2s var(--ease), border-color .2s var(--ease), color .2s var(--ease), transform .2s var(--ease);
    }
    .fav-btn:hover, .ghost-btn:hover, .page-btn:hover, .mode-toggle button:hover {
      background: color-mix(in srgb, var(--text) 5%, transparent); color: var(--text);
    }
    .fav-btn:focus-visible, .ghost-btn:focus-visible, .page-btn:focus-visible, .tag:focus-visible,
    .tool-card:focus-visible, .disc-card:focus-visible, .mode-toggle button:focus-visible,
    .lang-switch button:focus-visible, .report-bar a:focus-visible, .modal-close:focus-visible,
    .sortable:focus-visible, .theme-tab:focus-visible {
      outline: none; box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 22%, transparent);
    }

    .report-bar {
      margin-top: 12px; padding: 10px 14px;
      background: color-mix(in srgb, var(--text) 2.5%, transparent);
      border: 1px solid var(--line);
      border-radius: var(--radius-sm);
      display: flex; gap: 8px; flex-wrap: wrap;
    }
    .report-bar a {
      display: inline-flex; align-items: center;
      padding: 8px 12px; border-radius: var(--radius-pill);
      color: var(--text-2); text-decoration: none;
      border: 1px solid transparent;
      background: color-mix(in srgb, var(--text) 2%, transparent);
      font-size: 13px; font-weight: 600;
    }
    .report-bar a:hover, .report-bar a.active {
      color: var(--accent);
      border-color: color-mix(in srgb, var(--accent) 35%, transparent);
      background: var(--accent-soft);
      text-decoration: none;
    }

    .hero-stats {
      margin-top: 18px;
      display: grid;
      grid-template-columns: repeat(5, minmax(0,1fr));
      gap: 10px;
    }
    .metric {
      padding: 14px 14px 12px;
      border-radius: var(--radius);
      background: var(--card-bg);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
    }
    .metric .k { font-size: 11px; color: var(--muted); letter-spacing: .04em; margin-bottom: 6px; }
    .metric .v { font-size: 24px; font-weight: 750; letter-spacing: -.03em; line-height: 1.1; }

    .charts-row {
      margin-top: 14px;
      display: grid;
      grid-template-columns: 1.15fr .85fr;
      gap: 12px;
    }
    .chart-card {
      background: color-mix(in srgb, var(--text) 2.5%, transparent);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 14px 14px 10px;
      min-height: 250px;
    }
    .chart-card-title { font-size: 14px; font-weight: 700; margin-bottom: 2px; }
    .chart-card-sub { color: var(--muted); font-size: 12px; margin-bottom: 12px; }
    .hbar, .vbar { display: grid; gap: 8px; }
    .hbar-row { display: grid; grid-template-columns: 118px 1fr 42px; gap: 8px; align-items: center; }
    .hbar-row .name { color: var(--text-2); font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .hbar-row .track, .vbar-col .track {
      height: 8px; border-radius: var(--radius-pill); background: color-mix(in srgb, var(--text) 6%, transparent); overflow: hidden;
    }
    .hbar-row .fill { display: block; height: 100%; border-radius: inherit; background: var(--accent-grad); }
    .hbar-row .n, .vbar-col .n { font-family: var(--mono); font-size: 11px; color: var(--muted); text-align: right; }
    .vbar {
      grid-template-columns: repeat(10, minmax(0,1fr));
      align-items: end; height: 160px; gap: 8px; padding-top: 8px;
    }
    .vbar-col { display: grid; gap: 6px; align-content: end; }
    .vbar-col .track { height: var(--h); min-height: 4px; background: transparent; }
    .vbar-col .fill {
      display: block; width: 100%; height: 100%; border-radius: 8px 8px 4px 4px;
      background: var(--chart-fill);
    }
    .vbar-col .label { text-align: center; color: var(--muted); font-size: 10px; font-family: var(--mono); }

    main { padding: 28px 0 48px; }
    section { margin-bottom: 34px; }
    section > h2, .section-head h2 {
      font-size: 18px; font-weight: 750; letter-spacing: var(--letter); margin-bottom: 4px;
    }
    .hint { color: var(--muted); font-size: 13px; margin-bottom: 14px; }
    .section-head {
      display: flex; justify-content: space-between; gap: 12px; align-items: end; flex-wrap: wrap; margin-bottom: 4px;
    }

    .discovery-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0,1fr));
      gap: 12px;
    }
    .disc-card, .tool-card, .table-wrapper, .toolbar, .detail-panel, .modal {
      background: var(--card-bg);
      border: 1px solid var(--line);
      border-radius: var(--radius);
    }
    .disc-card {
      padding: 14px; min-height: 148px; display: flex; flex-direction: column; gap: 8px;
      transition: transform .2s var(--ease), border-color .2s var(--ease), background .2s var(--ease);
      cursor: pointer;
    }
    .disc-card:hover, .tool-card:hover {
      transform: translateY(-2px);
      border-color: color-mix(in srgb, var(--accent) 35%, transparent);
      background: var(--card-hover-bg);
    }
    .disc-card h3, .tool-card h3 { font-size: 14px; font-weight: 700; letter-spacing: var(--letter); }
    .disc-card p { color: var(--muted); font-size: 12.5px; flex: 1; }
    .pills { display: flex; flex-wrap: wrap; gap: 6px; }
    .pill {
      font-size: 11px; padding: 3px 8px; border-radius: var(--radius-pill);
      border: 1px solid var(--line); color: var(--text-2); background: color-mix(in srgb, var(--text) 3%, transparent);
    }
    .pill.tool { color: var(--secondary); border-color: color-mix(in srgb, var(--secondary) 35%, transparent); background: var(--secondary-soft); }
    .pill.type { color: var(--warm); border-color: color-mix(in srgb, var(--warm) 30%, transparent); background: var(--warm-soft); }
    .pill.score {
      color: var(--score-text); background: var(--score-grad);
      border: 0; font-weight: 700; font-family: var(--mono);
    }
    .meta-row { display: flex; justify-content: space-between; gap: 8px; align-items: center; color: var(--muted); font-size: 12px; }

    .tool-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0,1fr));
      gap: 12px;
    }
    .tool-card {
      padding: 14px; min-height: 118px; cursor: pointer;
      transition: transform .2s var(--ease), border-color .2s var(--ease), background .2s var(--ease);
    }
    .tool-card .vendor { color: var(--muted); font-size: 11px; font-family: var(--mono); margin-bottom: 6px; }
    .tool-card .bar {
      height: 5px; border-radius: var(--radius-pill); background: color-mix(in srgb, var(--text) 6%, transparent); overflow: hidden; margin: 12px 0 8px;
    }
    .tool-card .bar i {
      display: block; height: 100%; width: var(--w); border-radius: inherit;
      background: var(--accent-grad);
    }
    .tool-card .foot { display: flex; justify-content: space-between; color: var(--muted); font-size: 12px; }
    .tool-card.active {
      border-color: color-mix(in srgb, var(--accent) 40%, transparent);
      background: var(--card-hover-bg);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 8%, transparent);
    }

    .toolbar { padding: 16px; }
    .controls { display: grid; gap: 14px; }
    .controls > input#q {
      width: 100%;
      background: var(--input-bg);
      border: 1px solid var(--line-strong);
      border-radius: var(--radius-sm);
      padding: 12px 14px;
      outline: none;
    }
    .controls > input#q:focus {
      border-color: color-mix(in srgb, var(--accent) 40%, transparent);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 12%, transparent);
    }
    .filter-block { display: grid; gap: 8px; }
    .filter-label { font-size: 12px; color: var(--muted); font-weight: 650; }
    .tool-filter-controls { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .tool-filter-controls input {
      flex: 1 1 180px;
      min-width: 160px;
      background: var(--input-bg);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 8px 10px;
      outline: none;
    }
    .tag-group { display: flex; flex-wrap: wrap; gap: 8px; }
    .tag {
      border: 1px solid var(--line);
      background: color-mix(in srgb, var(--text) 3%, transparent);
      color: var(--text-2);
      border-radius: var(--radius-pill);
      padding: 7px 11px;
      font-size: 12px;
    }
    .tag.active {
      color: var(--accent);
      border-color: color-mix(in srgb, var(--accent) 40%, transparent);
      background: var(--accent-soft);
    }
    .controls-row { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
    .mode-toggle {
      display: inline-flex; gap: 4px; padding: 4px;
      border: 1px solid var(--line); border-radius: var(--radius-sm);
      background: color-mix(in srgb, var(--bg) 50%, transparent);
    }
    .mode-toggle button {
      border: 0; background: transparent; padding: 7px 10px; border-radius: 9px; font-size: 12px;
    }
    .mode-toggle button.active { background: var(--accent-soft); color: var(--accent); border: 0; }
    select#sort {
      background: var(--input-bg);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 8px 10px;
      min-width: 120px;
    }
    .checks { display: flex; flex-wrap: wrap; gap: 12px; color: var(--text-2); font-size: 13px; }
    .checks label { display: inline-flex; gap: 6px; align-items: center; }

    .active-filters { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; min-height: 0; }
    .active-filters:empty { display: none; }
    .af-chip {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 6px 10px; border-radius: var(--radius-pill);
      background: var(--secondary-soft);
      border: 1px solid color-mix(in srgb, var(--secondary) 30%, transparent);
      color: var(--secondary); font-size: 12px;
    }
    .af-chip button {
      border: 0; background: transparent; color: inherit; font-size: 14px; line-height: 1; padding: 0 2px;
    }
    .result-count {
      display: flex; justify-content: space-between; align-items: center; gap: 10px;
      margin: 12px 0; color: var(--muted); font-size: 13px;
    }
    .clear-filters {
      border: 1px solid var(--line); background: transparent; color: var(--text-2);
      border-radius: var(--radius-pill); padding: 6px 10px; font-size: 12px;
    }

    .table-wrapper { overflow: auto; }
    table { width: 100%; border-collapse: collapse; min-width: 760px; }
    th, td { padding: 12px 14px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
    th {
      position: sticky; top: 0; background: var(--table-head-bg);
      color: var(--muted); font-size: 12px; font-weight: 650; z-index: 1;
    }
    th.sortable { cursor: pointer; user-select: none; }
    th.sortable:hover { color: var(--text); }
    td { color: var(--text-2); }
    td.name-cell { color: var(--text); font-weight: 650; }
    td.name-cell button {
      border: 0; background: transparent; color: inherit; font: inherit; font-weight: 650;
      text-align: left; cursor: pointer;
    }
    td.name-cell button:hover { color: var(--accent); }
    tr:hover td { background: color-mix(in srgb, var(--text) 2%, transparent); }
    .score-cell { font-family: var(--mono); color: var(--accent); font-weight: 700; }
    .fav-star {
      border: 0; background: transparent; color: var(--muted); font-size: 16px; line-height: 1; margin-right: 6px;
    }
    .fav-star.on { color: var(--warm); }

    .pagination {
      display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 14px;
    }
    .page-btn.active {
      background: var(--accent-soft);
      border-color: color-mix(in srgb, var(--accent) 35%, transparent);
      color: var(--accent);
    }

    footer {
      padding: 0 0 36px;
      color: var(--muted);
      font-size: 12px;
      display: flex; gap: 8px; flex-wrap: wrap;
    }

    .detail-overlay { position: fixed; inset: 0; z-index: 60; pointer-events: none; }
    .detail-overlay.open { pointer-events: auto; }
    .detail-scrim {
      position: absolute; inset: 0; background: rgba(4,8,18,.48);
      opacity: 0; transition: opacity .2s var(--ease);
    }
    html[data-mode="light"] .detail-scrim { background: rgba(15,23,42,.28); }
    .detail-overlay.open .detail-scrim { opacity: 1; }
    .detail-panel {
      position: absolute; top: 0; right: 0; height: 100%; width: min(420px, 100%);
      border-radius: 0; border-right: 0; border-top: 0; border-bottom: 0;
      transform: translateX(104%);
      transition: transform .28s var(--ease);
      background: var(--detail-bg);
      box-shadow: -20px 0 50px rgba(0,0,0,.35);
      overflow: auto;
      padding: 18px;
    }
    .detail-overlay.open .detail-panel { transform: none; }
    .detail-head { display: flex; justify-content: space-between; gap: 10px; align-items: start; margin-bottom: 12px; }
    .detail-head h2 { font-size: 18px; letter-spacing: var(--letter); }
    .detail-meta { color: var(--muted); font-size: 12px; margin: 8px 0 14px; }
    .detail-block { margin-bottom: 16px; }
    .detail-block h3 { font-size: 12px; color: var(--muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: .06em; }
    .score-bars { display: grid; gap: 8px; }
    .score-bars .row { display: grid; grid-template-columns: 72px 1fr 36px; gap: 8px; align-items: center; font-size: 12px; }
    .score-bars .track { height: 7px; border-radius: var(--radius-pill); background: color-mix(in srgb, var(--text) 6%, transparent); overflow: hidden; }
    .score-bars .fill { display:block; height:100%; background: var(--accent-grad); }

    .modal-backdrop { position: fixed; inset: 0; background: rgba(4,8,18,.55); z-index: 70; }
    html[data-mode="light"] .modal-backdrop { background: rgba(15,23,42,.28); }
    .modal {
      position: fixed; z-index: 71;
      left: 50%; top: 50%; transform: translate(-50%, -50%);
      width: min(820px, calc(100% - 28px));
      max-height: min(80vh, 760px);
      display: flex; flex-direction: column;
      background: var(--modal-bg);
      box-shadow: var(--shadow);
    }
    .modal[hidden], .modal-backdrop[hidden] { display: none !important; }
    .modal-head {
      display: flex; justify-content: space-between; gap: 12px; align-items: start;
      padding: 18px 18px 10px; border-bottom: 1px solid var(--line);
    }
    .modal-head h2 { font-size: 18px; }
    .modal-head .meta { color: var(--muted); font-size: 12px; margin-top: 2px; }
    .modal-close {
      width: 36px; height: 36px; border-radius: 10px; font-size: 20px; line-height: 1;
      display: grid; place-items: center; padding: 0;
    }
    .modal-tabs {
      display: flex; gap: 8px; flex-wrap: wrap; padding: 12px 18px; border-bottom: 1px solid var(--line);
    }
    .modal-tabs button {
      border: 1px solid var(--line); background: color-mix(in srgb, var(--text) 3%, transparent); color: var(--text-2);
      border-radius: var(--radius-pill); padding: 7px 12px; font-size: 12px; font-weight: 600;
    }
    .modal-tabs button.active {
      color: var(--accent); border-color: color-mix(in srgb, var(--accent) 35%, transparent); background: var(--accent-soft);
    }
    .modal-body { padding: 18px; overflow: auto; color: var(--text-2); font-size: 13.5px; }
    .modal-body h3 { color: var(--text); font-size: 15px; margin: 14px 0 8px; }
    .modal-body ul { padding-left: 18px; display: grid; gap: 6px; }
    .modal-body p { margin-bottom: 8px; }

    @media (max-width: 1100px) {
      .hero-stats { grid-template-columns: repeat(3, minmax(0,1fr)); }
      .charts-row, .discovery-grid { grid-template-columns: 1fr 1fr; }
      .tool-grid { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 720px) {
      .wrap, .theme-dock-inner { width: min(var(--max), calc(100% - 28px)); }
      .hero-stats, .charts-row, .discovery-grid, .tool-grid { grid-template-columns: 1fr; }
      .hbar-row { grid-template-columns: 90px 1fr 36px; }
    }
    @media (prefers-reduced-motion: reduce) {
      * { transition: none !important; animation: none !important; }
    }
"""


def main() -> None:
    src = SRC.read_text()
    body_m = re.search(r"<body>(.*)</body>", src, re.S)
    if not body_m:
        raise SystemExit("body not found")
    body = body_m.group(1)

    old_banner = """  <div class="preview-banner">
    <strong>设计预览 v2</strong>
    · 保留现有功能架构与产品文案
    · 未部署正式站
    · 交互为前端示意（mock 数据）
  </div>"""
    new_banner = """  <div class="preview-banner">
    <strong>10 风格对比预览</strong>
    · 同一套功能架构与产品文案
    · 顶部切换皮肤
    · 未部署正式站 · mock 数据
  </div>

  <div class="theme-dock">
    <div class="theme-dock-inner">
      <div class="theme-dock-label">Visual themes · 10 styles</div>
      <div class="theme-tabs" id="themeTabs" role="tablist" aria-label="Theme switcher"></div>
      <div class="theme-blurb" id="themeBlurb"></div>
    </div>
  </div>"""
    if old_banner not in body:
        raise SystemExit("banner block not found")
    body = body.replace(old_banner, new_banner)

    theme_meta = [
        {"id": tid, "label": t["label"], "blurb": t["blurb"], "mode": t["mode"]}
        for tid, t in THEMES.items()
    ]
    theme_js = f"""
    /* ===== Theme switcher ===== */
    const THEMES = {json.dumps(theme_meta, ensure_ascii=False)};
    function applyTheme(id) {{
      const meta = THEMES.find(t => t.id === id) || THEMES[0];
      document.documentElement.setAttribute('data-theme', meta.id);
      document.documentElement.setAttribute('data-mode', meta.mode);
      document.querySelectorAll('.theme-tab').forEach(btn => {{
        const on = btn.dataset.theme === meta.id;
        btn.classList.toggle('active', on);
        btn.setAttribute('aria-selected', on);
      }});
      const blurb = document.getElementById('themeBlurb');
      if (blurb) blurb.textContent = meta.label + ' — ' + meta.blurb;
      try {{ localStorage.setItem('ecoradar_preview_theme', meta.id); }} catch (e) {{}}
      const themeColor = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();
      const metaTheme = document.querySelector('meta[name="theme-color"]');
      if (metaTheme && themeColor) metaTheme.setAttribute('content', themeColor);
    }}
    function initThemes() {{
      const tabs = document.getElementById('themeTabs');
      if (!tabs) return;
      tabs.innerHTML = THEMES.map(t => `<button type="button" class="theme-tab" role="tab" data-theme="${{t.id}}">${{t.label}}</button>`).join('');
      tabs.addEventListener('click', (e) => {{
        const btn = e.target.closest('[data-theme]');
        if (!btn) return;
        applyTheme(btn.dataset.theme);
      }});
      let initial = 'soft-observatory';
      try {{ initial = localStorage.getItem('ecoradar_preview_theme') || initial; }} catch (e) {{}}
      if (!THEMES.some(t => t.id === initial)) initial = THEMES[0].id;
      const qs = new URLSearchParams(location.search).get('theme');
      if (qs && THEMES.some(t => t.id === qs)) initial = qs;
      applyTheme(initial);
    }}
    initThemes();
"""
    if "// init\n    applyLanguage();" not in body:
        raise SystemExit("init marker not found")
    body = body.replace("// init\n    applyLanguage();", theme_js + "\n    // init\n    applyLanguage();")

    html = f"""<!doctype html>
<html lang="zh-CN" data-theme="soft-observatory" data-mode="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent EcoRadar — 10 风格对比预览</title>
  <meta name="description" content="Agent EcoRadar 视觉重设计：同一功能架构，10 套皮肤对比。">
  <meta name="theme-color" content="#0B1020">
  <style>
{theme_blocks()}
{COMMON_CSS}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
    OUT.write_text(html)

    # compact index page for side-by-side jumping
    cards = []
    swatches = {
        "soft-observatory": ("#0B1020", "#5EEAD4", "#A78BFA"),
        "warm-paper": ("#1c1917", "#f59e0b", "#fbbf24"),
        "linear-midnight": ("#0A0A0B", "#8B5CF6", "#60A5FA"),
        "aurora-glass": ("#07101F", "#22D3EE", "#F472B6"),
        "editorial-light": ("#F6F1E8", "#0F766E", "#9A3412"),
        "terminal-green": ("#050805", "#34D399", "#86EFAC"),
        "coral-harbor": ("#0E1A24", "#FF7A59", "#5EC8E8"),
        "slate-swiss": ("#EEF1F4", "#2563EB", "#0F172A"),
        "copper-instrument": ("#140F0C", "#D97706", "#FBBF24"),
        "sakura-dusk": ("#17111A", "#F9A8D4", "#C4B5FD"),
    }
    for tid, theme in THEMES.items():
        a, b, c = swatches[tid]
        cards.append(
            f"""
      <a class="card" href="ecoradar-10-styles-preview.html?theme={tid}">
        <div class="swatch">
          <i style="background:{a}"></i><i style="background:{b}"></i><i style="background:{c}"></i>
        </div>
        <h2>{theme['label']}</h2>
        <p>{theme['blurb']}</p>
        <span class="mode">{theme['mode']}</span>
      </a>"""
        )

    index_html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent EcoRadar · 10 风格索引</title>
  <style>
    :root {{
      --bg: #0B1020; --text: #EEF2FF; --muted: #8E9AB8; --line: rgba(232,236,247,.12); --card: #171E35; --accent: #5EEAD4;
      --font: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans SC", "PingFang SC", sans-serif;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: var(--font);
      background:
        radial-gradient(800px 360px at 10% 0%, rgba(94,234,212,.10), transparent 55%),
        radial-gradient(700px 360px at 90% 0%, rgba(167,139,250,.10), transparent 50%),
        #0B1020;
      color: var(--text);
      min-height: 100vh;
      padding: 32px 20px 48px;
    }}
    .wrap {{ width: min(1100px, 100%); margin: 0 auto; }}
    h1 {{ font-size: 28px; letter-spacing: -.03em; margin-bottom: 8px; }}
    .lead {{ color: var(--muted); max-width: 60ch; margin-bottom: 22px; line-height: 1.6; }}
    .actions {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 22px; }}
    .actions a {{
      display: inline-flex; align-items: center; padding: 10px 14px; border-radius: 999px;
      text-decoration: none; border: 1px solid var(--line); color: var(--text); background: rgba(255,255,255,.03);
    }}
    .actions a.primary {{ background: rgba(94,234,212,.14); border-color: rgba(94,234,212,.35); color: var(--accent); font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 12px; }}
    .card {{
      display: block; text-decoration: none; color: inherit;
      background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.015));
      border: 1px solid var(--line); border-radius: 18px; padding: 16px;
      transition: transform .2s ease, border-color .2s ease;
    }}
    .card:hover {{ transform: translateY(-2px); border-color: rgba(94,234,212,.3); }}
    .swatch {{ display: grid; grid-template-columns: 1.4fr .8fr .8fr; height: 42px; border-radius: 12px; overflow: hidden; margin-bottom: 12px; }}
    .swatch i {{ display: block; }}
    h2 {{ font-size: 16px; margin-bottom: 6px; }}
    p {{ color: var(--muted); font-size: 13px; line-height: 1.5; min-height: 3.2em; }}
    .mode {{
      display: inline-block; margin-top: 10px; font-size: 11px; color: var(--accent);
      border: 1px solid rgba(94,234,212,.25); background: rgba(94,234,212,.08);
      border-radius: 999px; padding: 3px 8px;
    }}
    @media (max-width: 720px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Agent EcoRadar · 10 风格对比</h1>
    <p class="lead">同一套现站功能架构与产品文案，只换视觉皮肤。建议先打开主预览页顶部切换；也可从下方卡片直达某一风格。</p>
    <div class="actions">
      <a class="primary" href="ecoradar-10-styles-preview.html">打开 10 风格主预览</a>
      <a href="ecoradar-redesign-preview.html">打开 v2 单风格原稿</a>
    </div>
    <div class="grid">
      {''.join(cards)}
    </div>
  </div>
</body>
</html>
"""
    INDEX.write_text(index_html)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(f"wrote {INDEX} ({INDEX.stat().st_size} bytes)")
    for tid, theme in THEMES.items():
        print(f"- {tid}: {theme['label']}")


if __name__ == "__main__":
    main()
