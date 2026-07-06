#!/usr/bin/env python3
import argparse, json
from common import load_jsonish, save_jsonish
DATASETS=['data/projects.yaml','data/curated-projects.yaml','data/rejected-projects.yaml']
def ensure(r):
    before=json.dumps(r.get('i18n',{}),ensure_ascii=False,sort_keys=True)
    name=str(r.get('name') or r.get('id') or '')
    summary=str(r.get('summary') or name)
    i=r.setdefault('i18n',{}); zh=i.setdefault('zh',{}); en=i.setdefault('en',{})
    zh.setdefault('name',name); zh.setdefault('summary',summary)
    en.setdefault('name',name); en.setdefault('summary',summary)
    return before!=json.dumps(r.get('i18n',{}),ensure_ascii=False,sort_keys=True)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--files',nargs='*',default=DATASETS); args=ap.parse_args()
    uf=seen=changed=missing=0
    for rel in args.files:
        rows=load_jsonish(rel)
        if not isinstance(rows,list): continue
        file_changed=False
        for r in rows:
            if not isinstance(r,dict): continue
            seen+=1
            if ensure(r): changed+=1; file_changed=True
            i=r.get('i18n') or {}
            if 'zh' not in i or 'en' not in i: missing+=1
        if file_changed: save_jsonish(rel,rows); uf+=1
    print(json.dumps({'updated_files':uf,'records_seen':seen,'records_changed':changed,'missing_after':missing},ensure_ascii=False))
    if missing: raise SystemExit(1)
if __name__=='__main__': main()
