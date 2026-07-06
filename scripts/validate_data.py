#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
from common import ROOT, load_jsonish
REQUIRED = {
 'data/seed-tools.yaml': ['id','name','vendor','primary_type','aliases','tracking_priority'],
 'data/sources.yaml': ['id','name','type'],
 'data/concepts.yaml': ['id','name','description'],
}
PROJECT_REQUIRED=['id','name','url','source_type','category','target_tools','summary','review_state']

def check_list(path, fields):
    data=load_jsonish(path)
    if not isinstance(data, list): raise SystemExit(f'{path}: expected list')
    for i,item in enumerate(data):
        if not isinstance(item, dict): raise SystemExit(f'{path}[{i}]: expected object')
        missing=[f for f in fields if f not in item]
        if missing: raise SystemExit(f'{path}[{i}] missing {missing}')
    return len(data)

def main():
    ap=argparse.ArgumentParser(description='Validate Search in Coding data files')
    ap.add_argument('--section', choices=['all','tools','projects'], default='all')
    args=ap.parse_args()
    counts={}
    if args.section in ('all','tools'):
        counts['tools']=check_list('data/seed-tools.yaml', REQUIRED['data/seed-tools.yaml'])
    if args.section=='all':
        counts['sources']=check_list('data/sources.yaml', REQUIRED['data/sources.yaml'])
        counts['concepts']=check_list('data/concepts.yaml', REQUIRED['data/concepts.yaml'])
    if args.section in ('all','projects'):
        p=ROOT/'data/projects.yaml'
        if p.exists(): counts['projects']=check_list('data/projects.yaml', PROJECT_REQUIRED) if p.read_text().strip()!='[]' else 0
        else: counts['projects']=0
    print('VALID', json.dumps(counts, ensure_ascii=False, sort_keys=True))
if __name__=='__main__': main()
