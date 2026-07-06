#!/usr/bin/env python3
import argparse, json, subprocess, urllib.parse, re, datetime, xml.etree.ElementTree as ET
from pathlib import Path
from common import ROOT, load_jsonish, slug, today

def curl(url):
    cmd=['curl','-4','-L','--silent','--show-error','--max-time','30','-A','Mozilla/5.0',url]
    p=subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=45)
    return p.returncode, p.stdout, p.stderr

def bing_rss(query, limit):
    url='https://www.bing.com/search?format=rss&q='+urllib.parse.quote_plus(query)
    code,out,err=curl(url)
    items=[]
    if code==0 and out.strip():
        try:
            root=ET.fromstring(out)
            for item in root.findall('.//item')[:limit]:
                title=(item.findtext('title') or '').strip()
                link=(item.findtext('link') or '').strip()
                desc=(item.findtext('description') or '').strip()
                if link:
                    items.append({'title':title,'url':link,'snippet':desc,'source':'bing-rss-fallback'})
        except Exception:
            pass
    return {'query':query,'returncode':code,'stderr':err,'raw_sample':out[:2000],'results':items}

def main():
    ap=argparse.ArgumentParser(description='Fallback web collector using Bing RSS; use Exa first when available')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=5)
    ap.add_argument('--queries', type=int, default=0)
    args=ap.parse_args()
    tools=load_jsonish('data/seed-tools.yaml')
    base_queries=[]
    for t in tools:
        name=t['name']
        base_queries += [
          f'{name} ecosystem extensions plugins MCP skills rules best practices',
          f'{name} tutorial workflow agentic coding case study',
          f'{name} context engineering codebase indexing rules prompts',
          f'{name} changelog release new features agent coding',
        ]
    base_queries += [
      'AI coding agent context engineering best practices',
      'MCP servers for coding agents GitHub',
      'spec driven development AI coding agents',
      'terminal AI coding agents comparison',
      'Claude Code 使用经验 技巧 MCP skills',
      'Codex CLI 使用教程 AGENTS.md',
      'Cursor Rules 最佳实践 MCP',
      'AI 编程 Agent 生态 工具 对比',
    ]
    # de-dupe
    qs=[]
    for q in base_queries:
        if q not in qs: qs.append(q)
    if args.queries: qs=qs[:args.queries]
    if args.dry_run:
        print(json.dumps({'dry_run':True,'source':'bing-rss-fallback','queries':qs[:5], 'limit':args.limit}, ensure_ascii=False, indent=2)); return
    outdir=ROOT/'data/raw/web'/today(); outdir.mkdir(parents=True, exist_ok=True)
    total=0; failures=0
    for q in qs:
        res=bing_rss(q, args.limit)
        total += len(res.get('results',[]))
        if res.get('returncode')!=0: failures += 1
        (outdir/(slug(q)+'.json')).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'saved_dir':str(outdir),'queries':len(qs),'results':total,'failures':failures,'source':'bing-rss-fallback'}, ensure_ascii=False))
if __name__=='__main__': main()
