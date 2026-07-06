#!/usr/bin/env python3
import argparse, json, collections, shutil, re
from common import ROOT, load_jsonish

ZH_HINTS = re.compile(r'[\u4e00-\u9fff]')

CATEGORY_LABELS = {
    'mcp-acp-a2a': {'zh': 'MCP / ACP / A2A 工具连接', 'en': 'MCP / ACP / A2A tool integrations'},
    'skills-prompts': {'zh': 'Skills / Prompts / 命令', 'en': 'Skills / prompts / commands'},
    'rules-instructions': {'zh': '规则 / 指令模板', 'en': 'Rules / instruction templates'},
    'context-engineering': {'zh': '上下文工程', 'en': 'Context engineering'},
    'agent-harness': {'zh': 'Agent 框架 / 编排', 'en': 'Agent harness / orchestration'},
    'testing-review-ci': {'zh': '测试 / Review / CI', 'en': 'Testing / review / CI'},
    'tutorial-case-study': {'zh': '教程 / 案例', 'en': 'Tutorials / case studies'},
    'benchmark-evaluation': {'zh': '评测 / Benchmark', 'en': 'Benchmarks / evaluation'},
    'terminal-agent': {'zh': '终端 Agent', 'en': 'Terminal agents'},
    'ai-ide': {'zh': 'AI IDE', 'en': 'AI IDE'},
    'official-tool': {'zh': '官方目标工具', 'en': 'Official target tool'},
}

def write_json(name, data):
    p = ROOT / 'site/data' / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def copy_reports():
    src = ROOT / 'docs/reports'
    dst = ROOT / 'site/reports'
    dst.mkdir(parents=True, exist_ok=True)
    for old in dst.glob('*.md'):
        old.unlink()
    for report in sorted(src.glob('*.md')):
        shutil.copy2(report, dst / report.name)

def bilingual_text(name, summary=''):
    # This is a display fallback, not machine translation. English records keep
    # original English in both fields until a translation pipeline is added;
    # Chinese records keep Chinese in zh and original in en for searchability.
    name = name or ''
    summary = summary or ''
    has_zh = bool(ZH_HINTS.search(name + summary))
    return {
        'zh': {'name': name, 'summary': summary},
        'en': {'name': name, 'summary': summary if not has_zh else summary},
    }

def enrich_project(p):
    q = dict(p)
    q['i18n'] = q.get('i18n') or bilingual_text(q.get('name'), q.get('summary'))
    return q

def enrich_tool(t):
    q = dict(t)
    q['i18n'] = q.get('i18n') or {'zh': {'name': q.get('name','')}, 'en': {'name': q.get('name','')}}
    return q

def main():
    ap = argparse.ArgumentParser(description='Build bilingual static site data from project datasets')
    ap.parse_args()
    projects = [enrich_project(p) for p in load_jsonish('data/projects.yaml')]
    curated = [enrich_project(p) for p in load_jsonish('data/curated-projects.yaml')]
    rejected = [enrich_project(p) for p in load_jsonish('data/rejected-projects.yaml')]
    tools = [enrich_tool(t) for t in load_jsonish('data/seed-tools.yaml')]
    concepts = load_jsonish('data/concepts.yaml')
    official = [p for p in projects if p.get('ranking_scope') == 'official']
    ecosystem = [p for p in projects if p.get('ranking_scope') == 'ecosystem' and p.get('review_state') not in ('rejected','auto-rejected')]
    metrics = {
        'projects': len(projects),
        'curated': len(curated),
        'rejected': len(rejected),
        'official_tools': len(official),
        'ecosystem_projects': len(ecosystem),
        'sources': dict(collections.Counter(p.get('source_type') for p in projects)),
        'record_kinds': dict(collections.Counter(p.get('record_kind') for p in projects)),
        'ranking_scopes': dict(collections.Counter(p.get('ranking_scope') for p in projects)),
        'tool_coverage': dict(collections.Counter(t for p in projects for t in p.get('target_tools', []))),
        'category_coverage': dict(collections.Counter(c for p in projects for c in p.get('category', []))),
        'languages': ['zh', 'en'],
    }
    i18n = {'languages': ['zh', 'en'], 'default': 'zh', 'categories': CATEGORY_LABELS}
    write_json('projects.json', projects)
    write_json('curated-projects.json', curated)
    write_json('rejected-projects.json', rejected)
    write_json('tools.json', tools)
    write_json('concepts.json', concepts)
    write_json('metrics.json', metrics)
    write_json('i18n.json', i18n)
    copy_reports()
    print(json.dumps({'site_data':'site/data','reports':'site/reports','projects':len(projects),'curated':len(curated),'tools':len(tools),'concepts':len(concepts),'languages':['zh','en']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
