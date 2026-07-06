#!/usr/bin/env python3
import argparse, json, os, sys
from pathlib import Path
from common import ROOT, load_jsonish, save_jsonish, today, slug, run

def gh_search(query, limit):
    fields='fullName,description,stargazersCount,url,updatedAt,language'
    cmd=f"gh search repos {json.dumps(query)} --sort stars --limit {int(limit)} --json {fields}"
    r=run(cmd, timeout=180)
    if r.returncode!=0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return json.loads(r.stdout or '[]')

def repo_view(full_name):
    fields='nameWithOwner,description,url,homepageUrl,stargazerCount,forkCount,licenseInfo,repositoryTopics,primaryLanguage,pushedAt,createdAt,updatedAt,isArchived,latestRelease'
    cmd=f"gh repo view {full_name} --json {fields}"
    r=run(cmd, timeout=120)
    if r.returncode!=0:
        return {'nameWithOwner':full_name,'error':r.stderr.strip()}
    return json.loads(r.stdout or '{}')

def main():
    ap=argparse.ArgumentParser(description='Collect GitHub repos using authenticated gh')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=20)
    ap.add_argument('--queries', type=int, default=0, help='number of configured queries; 0 means all')
    args=ap.parse_args()
    queries=load_jsonish('data/queries.yaml').get('github', [])
    if args.queries: queries=queries[:args.queries]
    if args.dry_run:
        print(json.dumps({'dry_run':True,'queries':queries[:5], 'limit':args.limit}, ensure_ascii=False, indent=2)); return
    outdir=ROOT/'data/raw/github'/today(); outdir.mkdir(parents=True, exist_ok=True)
    all_results=[]
    for q in queries:
        try:
            results=gh_search(q, args.limit)
            (outdir/(slug(q)+'.json')).write_text(json.dumps({'query':q,'results':results}, ensure_ascii=False, indent=2), encoding='utf-8')
            all_results.extend(results)
        except Exception as e:
            (outdir/(slug(q)+'-error.json')).write_text(json.dumps({'query':q,'error':str(e)}, ensure_ascii=False, indent=2), encoding='utf-8')
    # enrich unique top repos
    seen=[]
    for r in all_results:
        fn=r.get('fullName')
        if fn and fn not in seen: seen.append(fn)
    details=[]
    for fn in seen[:max(args.limit*max(1,len(queries)), args.limit)]:
        details.append(repo_view(fn))
    (outdir/'repo-details.json').write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'saved':str(outdir),'queries':len(queries),'raw_results':len(all_results),'details':len(details)}, ensure_ascii=False))
if __name__=='__main__': main()
