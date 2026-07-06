#!/usr/bin/env python3
import argparse, json, collections, shutil
from common import ROOT, load_jsonish

def write_json(name, data):
    p=ROOT/'site/data'/name; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def copy_reports():
    src=ROOT/'docs/reports'
    dst=ROOT/'site/reports'
    dst.mkdir(parents=True, exist_ok=True)
    for old in dst.glob('*.md'):
        old.unlink()
    for report in sorted(src.glob('*.md')):
        shutil.copy2(report, dst/report.name)

def main():
    ap=argparse.ArgumentParser(description='Build static site data from project datasets')
    ap.parse_args()
    projects=load_jsonish('data/projects.yaml')
    curated=load_jsonish('data/curated-projects.yaml')
    rejected=load_jsonish('data/rejected-projects.yaml')
    tools=load_jsonish('data/seed-tools.yaml')
    concepts=load_jsonish('data/concepts.yaml')
    official=[p for p in projects if p.get('ranking_scope')=='official']
    ecosystem=[p for p in projects if p.get('ranking_scope')=='ecosystem' and p.get('review_state')!='rejected']
    metrics={'projects':len(projects),'curated':len(curated),'rejected':len(rejected),'official_tools':len(official),'ecosystem_projects':len(ecosystem),'sources':dict(collections.Counter(p.get('source_type') for p in projects)),'record_kinds':dict(collections.Counter(p.get('record_kind') for p in projects)),'ranking_scopes':dict(collections.Counter(p.get('ranking_scope') for p in projects)),'tool_coverage':dict(collections.Counter(t for p in projects for t in p.get('target_tools',[]))),'category_coverage':dict(collections.Counter(c for p in projects for c in p.get('category',[])))}
    write_json('projects.json', projects); write_json('curated-projects.json', curated); write_json('rejected-projects.json', rejected)
    write_json('tools.json', tools); write_json('concepts.json', concepts); write_json('metrics.json', metrics)
    copy_reports()
    print(json.dumps({'site_data':'site/data','reports':'site/reports','projects':len(projects),'curated':len(curated),'tools':len(tools),'concepts':len(concepts)}, ensure_ascii=False))
if __name__=='__main__': main()
