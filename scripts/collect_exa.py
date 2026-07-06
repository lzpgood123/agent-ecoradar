#!/usr/bin/env python3
import argparse, json, os, subprocess, re
from pathlib import Path
from common import ROOT, load_jsonish, today, slug, run

def call_exa(query, count):
    # Agent Reach venv activation plus mcporter call. Query is escaped as JSON string inside the mcporter expression.
    expr = "exa.web_search_exa(query: " + json.dumps(query) + f", count: {int(count)})"
    cmd = "bash -lc " + json.dumps("source ~/.agent-reach-venv/bin/activate 2>/dev/null || true; mcporter call " + json.dumps(expr))
    r = run(cmd, timeout=120)
    return {'query':query,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}

def main():
    ap=argparse.ArgumentParser(description='Collect semantic web search results from Exa via mcporter')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=5)
    ap.add_argument('--queries', type=int, default=0)
    args=ap.parse_args()
    cfg=load_jsonish('data/queries.yaml')
    tools=load_jsonish('data/seed-tools.yaml')
    templates=cfg.get('exa', [])
    queries=[]
    for t in tools:
        for tmpl in templates[:4]:
            queries.append(tmpl.replace('{tool}', t['name']))
    queries += templates[4:]
    # de-dupe preserving order
    ded=[]
    for q in queries:
        if q not in ded: ded.append(q)
    queries=ded
    if args.queries: queries=queries[:args.queries]
    if args.dry_run:
        probe=call_exa(queries[0] if queries else 'AI coding agent', min(args.limit,3))
        ok=probe['returncode']==0
        print(json.dumps({'dry_run':True,'mcporter_ok':ok,'probe_query':probe['query'],'stderr':probe['stderr'][-500:], 'stdout_sample':probe['stdout'][:500]}, ensure_ascii=False, indent=2))
        return
    outdir=ROOT/'data/raw/exa'/today(); outdir.mkdir(parents=True, exist_ok=True)
    saved=0; failures=0
    for q in queries:
        res=call_exa(q, args.limit)
        (outdir/(slug(q)+'.json')).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
        saved += 1
        if res['returncode']!=0: failures += 1
    print(json.dumps({'saved_dir':str(outdir),'queries':saved,'failures':failures}, ensure_ascii=False))
if __name__=='__main__': main()
