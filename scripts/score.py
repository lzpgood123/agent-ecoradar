#!/usr/bin/env python3
import argparse, json
from common import load_jsonish, save_jsonish, score_from_stars, normalize_project_fields, total_score

def main():
    ap=argparse.ArgumentParser(description='Score normalized project records and separate official/ecosystem ranking')
    ap.parse_args()
    projects=load_jsonish('data/projects.yaml')
    for p in projects:
        normalize_project_fields(p)
        s=p.setdefault('score',{})
        stars=p.get('stars')
        s.setdefault('activity', 2 if p.get('source_type')=='github' else 1)
        s['adoption']=max(s.get('adoption',0), score_from_stars(stars))
        cats=p.get('category',[])
        if any(c in cats for c in ['mcp-acp-a2a','skills-prompts','rules-instructions','context-engineering']):
            s['ecosystem_value']=max(s.get('ecosystem_value',0),4)
        elif p.get('ranking_scope')=='ecosystem':
            s['ecosystem_value']=max(s.get('ecosystem_value',0),3)
        if p.get('record_kind')=='official-tool':
            s.update({'ecosystem_value':5,'activity':3,'adoption':3,'practicality':5,'novelty':3,'confidence':5})
            p['ranking_scope']='official'
        else:
            if p.get('source_type')=='github': s['confidence']=max(s.get('confidence',0),4)
            if p.get('source_type')=='exa': s['confidence']=max(s.get('confidence',0),3)
            if p.get('source_type')=='fallback-web': s['confidence']=min(max(s.get('confidence',0),2),2)
            s.setdefault('practicality', 3 if p.get('source_type')=='github' else 2)
            s.setdefault('novelty', 2)
        p['total_score']=total_score(p)
    save_jsonish('data/projects.yaml', projects)
    save_jsonish('data/scores.yaml', [{'id':p['id'], 'score':p.get('score',{}), 'total_score':p.get('total_score', total_score(p)), 'ranking_scope':p.get('ranking_scope')} for p in projects])
    print(json.dumps({'scored':len(projects),'official':sum(1 for p in projects if p.get('ranking_scope')=='official'),'ecosystem':sum(1 for p in projects if p.get('ranking_scope')=='ecosystem')}, ensure_ascii=False))
if __name__=='__main__': main()
