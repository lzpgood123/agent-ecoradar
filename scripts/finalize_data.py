#!/usr/bin/env python3
import argparse, json, datetime
from common import load_jsonish, save_jsonish, normalize_project_fields, total_score

def main():
    ap=argparse.ArgumentParser(description='Finalize data model, create curated and rejected datasets')
    ap.parse_args()
    projects=load_jsonish('data/projects.yaml')
    tools=load_jsonish('data/seed-tools.yaml')
    by_id={p.get('id'):p for p in projects}
    now=datetime.date.today().isoformat()
    for t in tools:
        rid='official-'+t['id']
        if rid not in by_id:
            by_id[rid]={'id':rid,'name':t['name'],'url':t.get('website') or t.get('docs') or (f"https://github.com/{t['repo']}" if t.get('repo') else ''),'repo':t.get('repo'),'source_type':'official-seed','category':['official-tool',t.get('primary_type','official-tool')],'target_tools':[t['id']],'concepts':t.get('related_concepts',[]),'summary':f"Official seed profile for {t['name']}",'why_it_matters':'Primary target tool for the Search in Coding tracker.','status':'active','license':None,'stars':None,'forks':None,'last_updated':now,'first_seen':now,'last_seen':now,'maturity':'unknown','integration_surfaces':t.get('extension_points',[]),'languages':[],'tags':['target-tool','official-seed'],'score':{'ecosystem_value':5,'activity':3,'adoption':3,'practicality':5,'novelty':3,'confidence':5},'notes':'','review_state':'reviewed','record_kind':'official-tool','source_quality':'verified','ranking_scope':'official'}
    projects=list(by_id.values())
    for p in projects: normalize_project_fields(p)
    ecosystem=sorted([p for p in projects if p.get('ranking_scope')=='ecosystem' and p.get('record_kind')!='official-tool'], key=total_score, reverse=True)
    learning=sorted([p for p in projects if p.get('ranking_scope')=='learning-resource'], key=total_score, reverse=True)
    curated=[]; seen=set()
    def add(p, level):
        if p.get('id') in seen: return
        q=dict(p); q['review_state']='reviewed'; q['recommendation_level']=level
        q['curation_note']=q.get('why_it_matters') or 'Selected by final-delivery curation based on source quality, relevance, and score.'
        curated.append(q); seen.add(q.get('id'))
    for p in ecosystem:
        if p.get('source_type')=='github' and len([x for x in curated if x.get('source_type')=='github'])<40:
            add(p, 'try-now' if total_score(p)>=16 else 'watch')
    for p in learning:
        if len([x for x in curated if x.get('source_type')!='github'])<15:
            add(p, 'reference')
    for p in ecosystem+learning:
        if len(curated)>=60: break
        add(p, 'watch' if p.get('source_type')=='github' else 'reference')
    rejected=[]
    for p in sorted(projects, key=total_score):
        if len(rejected)>=25: break
        if p.get('record_kind')=='official-tool' or p.get('id') in seen: continue
        if p.get('source_type')=='fallback-web' or p.get('target_tools')==['general-ai-coding'] or total_score(p)<=8:
            q=dict(p); q['review_state']='rejected'; q['rejection_reason']='Low confidence, fallback/noisy, duplicate, or weak direct relevance for final curated set.'
            rejected.append(q)
    curated_ids={p['id'] for p in curated}; rejected_ids={p['id'] for p in rejected}
    for p in projects:
        if p['id'] in curated_ids: p['review_state']='reviewed'
        if p['id'] in rejected_ids:
            p['review_state']='rejected'; p['ranking_scope']='excluded'
    save_jsonish('data/projects.yaml', projects)
    save_jsonish('data/curated-projects.yaml', curated)
    save_jsonish('data/rejected-projects.yaml', rejected)
    print(json.dumps({'projects':len(projects),'curated':len(curated),'rejected':len(rejected),'curated_github':sum(1 for p in curated if p.get('source_type')=='github'),'curated_non_github':sum(1 for p in curated if p.get('source_type')!='github')}, ensure_ascii=False))
if __name__=='__main__': main()
