#!/usr/bin/env python3
"""EcoRadar 访问统计：读 Nginx 日志，生成简洁中文 HTML 页面。

零外部依赖，输出单文件 HTML 到 stats 目录。
"""

from __future__ import annotations

import gzip
import html
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

LOG_DIR = Path("/var/log/nginx")
LOG_PREFIX = "ecoradar.lzpgood.online.access.log"
OUTPUT_PATH = Path("/var/www/ecoradar.lzpgood.online/stats/index.html")
SERVER_IP = "124.220.63.217"
OWN_HOSTS = {
    "ecoradar.lzpgood.online",
    "coding.lzpgood.online",
    "data.lzpgood.online",
    "www.ecoradar.lzpgood.online",
    "lzpgood.online",
    "www.lzpgood.online",
    SERVER_IP,
    f"{SERVER_IP}:443",
    f"{SERVER_IP}:80",
}

BOT_KEYWORDS = [
    "bot",
    "crawler",
    "spider",
    "googlebot",
    "bingbot",
    "baiduspider",
    "yandex",
    "slurp",
    "duckduckbot",
    "sogou",
    "exabot",
    "facebot",
    "ia_archiver",
    "go-http-client",
    "python-requests",
    "curl/",
    "semrush",
    "ahrefs",
    "mj12bot",
    "dotbot",
    "petalbot",
    "bytespider",
    "gptbot",
    "claudebot",
    "amazonbot",
]

STATIC_EXTS = {
    ".js",
    ".css",
    ".json",
    ".svg",
    ".ico",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".map",
    ".txt",
    ".xml",
    ".webmanifest",
}

# Nginx combined log format
LOG_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<request>[^"]*)" (?P<status>\d{3}) (?P<bytes>\S+) '
    r'"(?P<referer>[^"]*)" "(?P<ua>[^"]*)"'
)

TIME_FMT = "%d/%b/%Y:%H:%M:%S %z"


# ---------------------------------------------------------------------------
# 日志读取与解析
# ---------------------------------------------------------------------------

def open_log(path: Path):
    if not path.exists():
        return None
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "rt", encoding="utf-8", errors="replace")


def iter_log_paths(today: date) -> list[tuple[date, Path]]:
    """返回 (日志日期, 路径) 列表，覆盖最近 7 天。"""
    items: list[tuple[date, Path]] = []

    # 当天
    p0 = LOG_DIR / LOG_PREFIX
    if p0.exists():
        items.append((today, p0))

    # 昨天（logrotate 的 .1）
    p1 = LOG_DIR / f"{LOG_PREFIX}.1"
    if p1.exists():
        items.append((today - timedelta(days=1), p1))

    # 历史 .N.gz（N 从 2 起，按 logrotate 惯例）
    for n in range(2, 14):
        pg = LOG_DIR / f"{LOG_PREFIX}.{n}.gz"
        if pg.exists():
            # 粗略按序号回推日期；真正日期以行内时间戳为准
            items.append((today - timedelta(days=n), pg))

    return items


def parse_request(request: str) -> tuple[str, str]:
    """返回 (method, path)。异常请求返回 ('', '')。"""
    request = (request or "").strip()
    if not request:
        return "", ""
    parts = request.split()
    if len(parts) >= 2:
        method = parts[0]
        raw_path = parts[1]
    elif len(parts) == 1:
        method = "GET"
        raw_path = parts[0]
    else:
        return "", ""
    path = raw_path.split("?", 1)[0]
    if not path.startswith("/"):
        # 可能是完整 URL
        try:
            path = urlparse(path).path or "/"
        except Exception:
            path = "/"
    return method, path


def parse_line(line: str) -> dict | None:
    m = LOG_RE.match(line.rstrip("\n"))
    if not m:
        return None
    try:
        ts = datetime.strptime(m.group("time"), TIME_FMT)
    except ValueError:
        return None
    method, path = parse_request(m.group("request"))
    try:
        status = int(m.group("status"))
    except ValueError:
        return None
    return {
        "ip": m.group("ip"),
        "ts": ts,
        "method": method,
        "path": path or "/",
        "status": status,
        "referer": m.group("referer") or "-",
        "ua": m.group("ua") or "-",
    }


def load_entries(today: date) -> list[dict]:
    entries: list[dict] = []
    seen_paths: set[str] = set()
    for _approx_day, path in iter_log_paths(today):
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen_paths:
            continue
        seen_paths.add(key)
        fh = open_log(path)
        if fh is None:
            continue
        with fh:
            for line in fh:
                row = parse_line(line)
                if row is None:
                    continue
                entries.append(row)
    return entries


# ---------------------------------------------------------------------------
# 爬虫识别
# ---------------------------------------------------------------------------

def ua_is_bot(ua: str) -> bool:
    ua_l = (ua or "").lower()
    return any(kw in ua_l for kw in BOT_KEYWORDS)


def classify_bot_ua(ua: str) -> str | None:
    """识别常见搜索引擎爬虫名称，否则返回 None。"""
    ua_l = (ua or "").lower()
    if "googlebot" in ua_l or ("google" in ua_l and "bot" in ua_l):
        return "Google"
    if "bingbot" in ua_l or "bingpreview" in ua_l or "msnbot" in ua_l:
        return "Bing"
    if "baiduspider" in ua_l or ("baidu" in ua_l and "spider" in ua_l):
        return "Baidu"
    if "yandex" in ua_l:
        return "Yandex"
    if "duckduckbot" in ua_l:
        return "DuckDuckGo"
    if "sogou" in ua_l:
        return "Sogou"
    if "bytespider" in ua_l or "toutiao" in ua_l:
        return "字节"
    if "semrush" in ua_l:
        return "Semrush"
    if "ahrefs" in ua_l:
        return "Ahrefs"
    if "petalbot" in ua_l:
        return "Petal"
    if ua_is_bot(ua):
        return "其他爬虫"
    return None


def detect_behavior_bots(entries: list[dict]) -> set[str]:
    """同一 IP 在任意 1 分钟窗口内请求 >20 次 => 行为爬虫。

    服务器自身 IP 不参与行为判断。
    """
    by_ip: dict[str, list[datetime]] = defaultdict(list)
    for e in entries:
        ip = e["ip"]
        if ip == SERVER_IP:
            continue
        by_ip[ip].append(e["ts"])

    bots: set[str] = set()
    for ip, times in by_ip.items():
        times.sort()
        left = 0
        for right, t in enumerate(times):
            while t - times[left] > timedelta(minutes=1):
                left += 1
            if right - left + 1 > 20:
                bots.add(ip)
                break
    return bots


def mark_bots(entries: list[dict]) -> None:
    behavior_bots = detect_behavior_bots(entries)
    for e in entries:
        e["ua_bot"] = ua_is_bot(e["ua"])
        e["behavior_bot"] = e["ip"] in behavior_bots
        # 服务器 IP 不因行为模式被标为爬虫；UA 仍可标
        if e["ip"] == SERVER_IP:
            e["is_bot"] = e["ua_bot"]
        else:
            e["is_bot"] = e["ua_bot"] or e["behavior_bot"]
        e["bot_name"] = classify_bot_ua(e["ua"]) if e["is_bot"] else None


# ---------------------------------------------------------------------------
# 统计
# ---------------------------------------------------------------------------

def is_static(path: str) -> bool:
    lower = path.lower()
    # 去掉尾部斜杠再判扩展名
    base = lower.rstrip("/")
    _, ext = os.path.splitext(base)
    if ext in STATIC_EXTS:
        return True
    # 常见静态路径前缀
    if lower.startswith(("/assets/", "/static/", "/css/", "/js/", "/fonts/", "/images/")):
        return True
    return False


def referer_host(referer: str) -> str | None:
    if not referer or referer == "-":
        return None
    try:
        host = urlparse(referer).netloc.lower()
    except Exception:
        return None
    if not host:
        return None
    # 兼容纯 IP 或带端口的 referer
    if host.startswith("www."):
        host = host[4:]
    return host


def is_own_host(host: str | None) -> bool:
    if not host:
        return False
    if host in OWN_HOSTS:
        return True
    # 去掉端口后再比一次
    bare = host.split(":", 1)[0]
    return bare in OWN_HOSTS or bare == SERVER_IP


def day_of(ts: datetime) -> date:
    return ts.date()


def compute_stats(entries: list[dict], today: date) -> dict:
    week_start = today - timedelta(days=6)

    today_entries = [e for e in entries if day_of(e["ts"]) == today]
    week_entries = [e for e in entries if week_start <= day_of(e["ts"]) <= today]

    today_real = [e for e in today_entries if not e["is_bot"]]
    week_real = [e for e in week_entries if not e["is_bot"]]

    today_visitors = {e["ip"] for e in today_real}
    week_visitors = {e["ip"] for e in week_real}
    today_pageviews = len(today_entries)  # 含爬虫

    # 爬虫分类（今日）
    search_bot_counts: Counter[str] = Counter()
    other_bot_hits = 0
    for e in today_entries:
        if not e["is_bot"]:
            continue
        name = e["bot_name"] or "其他爬虫"
        if name in {"Google", "Bing", "Baidu"}:
            search_bot_counts[name] += 1
        else:
            # 仍归入爬虫统计展示；搜索引擎三大之外算其他
            if name in {"Yandex", "DuckDuckGo", "Sogou", "字节", "Semrush", "Ahrefs", "Petal"}:
                search_bot_counts[name] += 1
            else:
                other_bot_hits += 1
                search_bot_counts["其他爬虫"] += 1

    # 真实访客来源（今日）
    direct = 0
    external = 0
    github = 0
    external_hosts: Counter[str] = Counter()
    for e in today_real:
        host = referer_host(e["referer"])
        if host is None:
            direct += 1
            continue
        if is_own_host(host):
            # 站内跳转 / 本机探测，不计入外部来源，也不算直接访问
            continue
        if "github.com" in host or host.endswith(".github.io"):
            github += 1
            external_hosts[host] += 1
            external += 1
            continue
        external += 1
        external_hosts[host] += 1

    # 热门页面（今日真实访客，排除静态）
    page_hits: Counter[str] = Counter()
    for e in today_real:
        p = e["path"]
        if is_static(p):
            continue
        if e["method"] not in ("GET", "HEAD", ""):
            continue
        page_hits[p] += 1
    top_pages = page_hits.most_common(10)

    # 报错（今日，全部请求）
    not_found = [e for e in today_entries if e["status"] == 404]
    server_err = [e for e in today_entries if 500 <= e["status"] < 600]
    nf_paths: Counter[str] = Counter(e["path"] for e in not_found)

    # 7 天趋势：每天真实访客数（独立 IP）
    trend_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    trend: list[dict] = []
    for d in trend_days:
        ips = {e["ip"] for e in entries if day_of(e["ts"]) == d and not e["is_bot"]}
        trend.append({"date": d, "visitors": len(ips)})

    return {
        "today": today,
        "generated_at": datetime.now().astimezone(),
        "today_visitors": len(today_visitors),
        "today_pageviews": today_pageviews,
        "week_visitors": len(week_visitors),
        "search_bot_counts": search_bot_counts,
        "search_bot_total": sum(search_bot_counts.values()),
        "direct": direct,
        "external": external,
        "github": github,
        "external_hosts": external_hosts.most_common(5),
        "top_pages": top_pages,
        "nf_total": len(not_found),
        "nf_top": nf_paths.most_common(5),
        "server_err_total": len(server_err),
        "trend": trend,
        "total_parsed": len(entries),
        "today_bots": sum(1 for e in today_entries if e["is_bot"]),
        "today_real_hits": len(today_real),
    }


# ---------------------------------------------------------------------------
# HTML 渲染
# ---------------------------------------------------------------------------

WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", ",")


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def render_svg_trend(trend: list[dict]) -> str:
    width, height = 640, 220
    pad_l, pad_r, pad_t, pad_b = 44, 16, 20, 40
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    values = [t["visitors"] for t in trend]
    vmax = max(values) if values else 0
    if vmax <= 0:
        vmax = 1
    n = len(trend)
    if n <= 1:
        xs = [pad_l + plot_w / 2]
    else:
        xs = [pad_l + i * plot_w / (n - 1) for i in range(n)]
    ys = [pad_t + plot_h - (v / vmax) * plot_h for v in values]

    # 网格线
    grid_lines = []
    for i in range(4):
        y = pad_t + plot_h * i / 3
        val = int(round(vmax * (1 - i / 3)))
        grid_lines.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width-pad_r}" y2="{y:.1f}" '
            f'stroke="#44403c" stroke-width="1" stroke-dasharray="4 4"/>'
            f'<text x="{pad_l-8}" y="{y+4:.1f}" text-anchor="end" '
            f'fill="#a8a29e" font-size="11">{val}</text>'
        )

    points = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area_points = (
        f"{xs[0]:.1f},{pad_t+plot_h:.1f} " + points + f" {xs[-1]:.1f},{pad_t+plot_h:.1f}"
        if xs
        else ""
    )

    dots = []
    labels = []
    for i, (t, x, y, v) in enumerate(zip(trend, xs, ys, values)):
        d: date = t["date"]
        label = f"{d.month}/{d.day}"
        wd = WEEKDAY_CN[d.weekday()]
        dots.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#f59e0b" '
            f'stroke="#1c1917" stroke-width="2">'
            f'<title>{d.isoformat()} {wd}: {v} 人</title></circle>'
        )
        labels.append(
            f'<text x="{x:.1f}" y="{height-14}" text-anchor="middle" '
            f'fill="#a8a29e" font-size="11">{esc(label)}</text>'
            f'<text x="{x:.1f}" y="{height-2}" text-anchor="middle" '
            f'fill="#78716c" font-size="10">{esc(wd)}</text>'
        )
        # 数值标注
        dots.append(
            f'<text x="{x:.1f}" y="{y-10:.1f}" text-anchor="middle" '
            f'fill="#fbbf24" font-size="11" font-weight="600">{v}</text>'
        )

    polyline = (
        f'<polyline fill="none" stroke="#f59e0b" stroke-width="2.5" '
        f'stroke-linejoin="round" stroke-linecap="round" points="{points}"/>'
        if points
        else ""
    )
    area = (
        f'<polygon fill="url(#amberFade)" points="{area_points}"/>' if area_points else ""
    )

    return f"""
<svg viewBox="0 0 {width} {height}" width="100%" height="auto" role="img" aria-label="近7天访客趋势">
  <defs>
    <linearGradient id="amberFade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.28"/>
      <stop offset="100%" stop-color="#f59e0b" stop-opacity="0.02"/>
    </linearGradient>
  </defs>
  {''.join(grid_lines)}
  {area}
  {polyline}
  {''.join(dots)}
  {''.join(labels)}
</svg>
""".strip()


def render_list_rows(items: Iterable[tuple[str, int]], empty: str = "暂无数据") -> str:
    rows = list(items)
    if not rows:
        return f'<div class="empty">{esc(empty)}</div>'
    max_v = max(v for _, v in rows) or 1
    parts = []
    for name, count in rows:
        pct = max(4, int(count / max_v * 100))
        parts.append(
            f"""
<div class="row">
  <div class="row-label" title="{esc(name)}">{esc(name)}</div>
  <div class="row-bar-wrap"><div class="row-bar" style="width:{pct}%"></div></div>
  <div class="row-val">{fmt_int(count)}</div>
</div>"""
        )
    return "".join(parts)


def render_html(stats: dict) -> str:
    gen = stats["generated_at"]
    gen_str = gen.strftime("%Y-%m-%d %H:%M:%S")
    today_str = stats["today"].strftime("%Y年%m月%d日")

    bot_parts = []
    preferred_order = ["Google", "Bing", "Baidu", "Yandex", "DuckDuckGo", "Sogou", "字节", "Semrush", "Ahrefs", "Petal", "其他爬虫"]
    counts: Counter = stats["search_bot_counts"]
    ordered = [k for k in preferred_order if counts.get(k)]
    for k in counts:
        if k not in ordered:
            ordered.append(k)
    if ordered:
        detail = "、".join(f"{k} {fmt_int(counts[k])} 次" for k in ordered)
        bot_summary = f'{fmt_int(stats["search_bot_total"])} 次'
        bot_detail_html = f'<div class="muted detail">{esc(detail)}</div>'
    else:
        bot_summary = "0 次"
        bot_detail_html = '<div class="muted detail">今天还没检测到搜索引擎爬虫</div>'

    ext_hosts_html = render_list_rows(stats["external_hosts"], "暂无外部来源")
    pages_html = render_list_rows(stats["top_pages"], "今天还没有页面访问")
    nf_html = render_list_rows(stats["nf_top"], "今天没有 404")

    server_err_html = ""
    if stats["server_err_total"] > 0:
        server_err_html = f"""
<div class="stat-line warn">
  <span>服务器错误（5xx）</span>
  <strong>{fmt_int(stats["server_err_total"])} 次</strong>
</div>"""
    else:
        server_err_html = """
<div class="stat-line ok">
  <span>服务器错误（5xx）</span>
  <strong>0 次</strong>
</div>"""

    svg = render_svg_trend(stats["trend"])

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>EcoRadar 访问统计</title>
<style>
  :root {{
    --bg: #1c1917;
    --bg-card: #292524;
    --bg-soft: #1f1b18;
    --border: #44403c;
    --text: #f5f5f4;
    --muted: #a8a29e;
    --faint: #78716c;
    --amber: #f59e0b;
    --amber-soft: rgba(245, 158, 11, 0.14);
    --amber-strong: #fbbf24;
    --green: #34d399;
    --red: #f87171;
    --shadow: 0 10px 30px rgba(0,0,0,.28);
    --radius: 16px;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--text); }}
  body {{
    font-family: "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
                 "Noto Sans CJK SC", sans-serif;
    line-height: 1.55;
    min-height: 100vh;
  }}
  .wrap {{
    max-width: 980px;
    margin: 0 auto;
    padding: 28px 16px 48px;
  }}
  header {{
    margin-bottom: 22px;
  }}
  header h1 {{
    margin: 0 0 6px;
    font-size: 1.55rem;
    font-weight: 700;
    letter-spacing: .02em;
  }}
  header h1 span {{ color: var(--amber); }}
  .sub {{
    color: var(--muted);
    font-size: .92rem;
  }}
  .grid-3 {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 18px;
  }}
  .card {{
    background: linear-gradient(180deg, #2a2522 0%, var(--bg-card) 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 18px 16px;
    box-shadow: var(--shadow);
  }}
  .card h2 {{
    margin: 0 0 12px;
    font-size: 1rem;
    font-weight: 600;
    color: var(--amber-strong);
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .card h2::before {{
    content: "";
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--amber);
    box-shadow: 0 0 0 4px var(--amber-soft);
  }}
  .metric {{
    text-align: center;
    padding: 8px 6px 4px;
  }}
  .metric .num {{
    font-size: 2.25rem;
    font-weight: 750;
    color: var(--amber-strong);
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
  }}
  .metric .label {{
    margin-top: 8px;
    color: var(--muted);
    font-size: .92rem;
  }}
  .metric .hint {{
    margin-top: 4px;
    color: var(--faint);
    font-size: .78rem;
  }}
  .stack {{ display: grid; gap: 14px; }}
  .kv {{
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px dashed #3f3a36;
  }}
  .kv:last-child {{ border-bottom: 0; }}
  .kv .k {{ color: var(--muted); }}
  .kv .v {{ font-weight: 650; color: var(--text); white-space: nowrap; }}
  .muted {{ color: var(--muted); }}
  .detail {{ margin-top: 6px; font-size: .86rem; line-height: 1.5; }}
  .row {{
    display: grid;
    grid-template-columns: minmax(0, 1.4fr) minmax(80px, 1.2fr) auto;
    gap: 10px;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #3a3531;
  }}
  .row:last-child {{ border-bottom: 0; }}
  .row-label {{
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: .92rem;
    color: var(--text);
  }}
  .row-bar-wrap {{
    height: 8px;
    background: #1a1715;
    border-radius: 999px;
    overflow: hidden;
    border: 1px solid #3f3a36;
  }}
  .row-bar {{
    height: 100%;
    background: linear-gradient(90deg, #d97706, #f59e0b 60%, #fbbf24);
    border-radius: 999px;
  }}
  .row-val {{
    min-width: 42px;
    text-align: right;
    font-variant-numeric: tabular-nums;
    font-weight: 650;
    color: var(--amber-strong);
  }}
  .empty {{
    color: var(--faint);
    padding: 10px 0 4px;
    font-size: .92rem;
  }}
  .stat-line {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 12px;
    margin-bottom: 10px;
    background: var(--bg-soft);
    border: 1px solid var(--border);
  }}
  .stat-line.ok strong {{ color: var(--green); }}
  .stat-line.warn strong {{ color: var(--red); }}
  .stat-line span {{ color: var(--muted); }}
  .chart-box {{
    background: #1a1715;
    border: 1px solid #3f3a36;
    border-radius: 14px;
    padding: 10px 8px 4px;
    overflow-x: auto;
  }}
  footer {{
    margin-top: 22px;
    color: var(--faint);
    font-size: .8rem;
    text-align: center;
  }}
  @media (max-width: 720px) {{
    .grid-3 {{ grid-template-columns: 1fr; }}
    .metric .num {{ font-size: 2rem; }}
    .row {{ grid-template-columns: minmax(0, 1fr) 70px auto; }}
    .wrap {{ padding: 18px 12px 36px; }}
  }}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1><span>EcoRadar</span> 访问统计</h1>
      <div class="sub">统计日期：{esc(today_str)} · 最近刷新：{esc(gen_str)}</div>
    </header>

    <section class="grid-3" aria-label="今日概览">
      <div class="card metric">
        <div class="num">{fmt_int(stats["today_visitors"])}</div>
        <div class="label">今日访客</div>
        <div class="hint">真实访客，已排除爬虫</div>
      </div>
      <div class="card metric">
        <div class="num">{fmt_int(stats["today_pageviews"])}</div>
        <div class="label">今日浏览量</div>
        <div class="hint">全部请求，含爬虫</div>
      </div>
      <div class="card metric">
        <div class="num">{fmt_int(stats["week_visitors"])}</div>
        <div class="label">本周访客</div>
        <div class="hint">近 7 天真实访客</div>
      </div>
    </section>

    <div class="stack">
      <section class="card">
        <h2>访客来源</h2>
        <div class="kv">
          <div class="k">搜索引擎爬虫</div>
          <div class="v">{esc(bot_summary)}</div>
        </div>
        {bot_detail_html}
        <div class="kv" style="margin-top:10px">
          <div class="k">直接访问</div>
          <div class="v">{fmt_int(stats["direct"])} 次</div>
        </div>
        <div class="kv">
          <div class="k">外部链接</div>
          <div class="v">{fmt_int(stats["external"])} 次</div>
        </div>
        <div class="kv">
          <div class="k">从 GitHub 来</div>
          <div class="v">{fmt_int(stats["github"])} 次</div>
        </div>
        <div style="margin-top:8px" class="muted detail">外部来源网站（前 5）</div>
        {ext_hosts_html}
      </section>

      <section class="card">
        <h2>热门页面</h2>
        <div class="muted detail" style="margin-bottom:6px">按真实访客次数排序，已排除样式与脚本文件</div>
        {pages_html}
      </section>

      <section class="card">
        <h2>报错</h2>
        <div class="stat-line {'warn' if stats['nf_total'] else 'ok'}">
          <span>找不到页面（404）</span>
          <strong>{fmt_int(stats["nf_total"])} 次</strong>
        </div>
        <div class="muted detail" style="margin-bottom:6px">常见 404 路径（前 5）</div>
        {nf_html}
        {server_err_html}
      </section>

      <section class="card">
        <h2>近 7 天访客趋势</h2>
        <div class="muted detail" style="margin-bottom:8px">每天真实访客人数（已排除爬虫）</div>
        <div class="chart-box">
          {svg}
        </div>
      </section>
    </div>

    <footer>
      共解析 {fmt_int(stats["total_parsed"])} 条日志 ·
      今日真实访问 {fmt_int(stats["today_real_hits"])} 次 ·
      今日爬虫 {fmt_int(stats["today_bots"])} 次 ·
      每 5 分钟自动刷新
    </footer>
  </div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> int:
    today = date.today()
    entries = load_entries(today)
    mark_bots(entries)
    stats = compute_stats(entries, today)
    html_out = render_html(stats)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT_PATH.with_suffix(".html.tmp")
    tmp.write_text(html_out, encoding="utf-8")
    os.replace(tmp, OUTPUT_PATH)
    try:
        os.chmod(OUTPUT_PATH, 0o644)
    except OSError:
        pass

    print(
        f"[traffic_stats] wrote {OUTPUT_PATH} | "
        f"today_visitors={stats['today_visitors']} "
        f"pageviews={stats['today_pageviews']} "
        f"week_visitors={stats['week_visitors']} "
        f"bots={stats['today_bots']} "
        f"404={stats['nf_total']} "
        f"parsed={stats['total_parsed']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
