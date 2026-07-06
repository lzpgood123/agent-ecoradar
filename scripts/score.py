#!/usr/bin/env python3
import argparse, json
from common import load_jsonish, save_jsonish, score_from_stars, normalize_project_fields, total_score

def cfg():
    c=load_jsonish('config/scoring.yaml')
    return c if isinstance(c,dict) else {}
def adjust(p,c):
    sw=c.get('source_weights',{}).get(p.get('source_type'),0)
    cw=max([c.get('category_weights',{}).get(x,0) for x in (p.get('category') or [])] or [0])
    pen=0; ps=c.get('penalties',{})
    if p.get('source_quality')=='fallback': pen+=ps.get('fallback',0)
    if p.get('target_tools')==['general-ai-coding']: pen+=ps.get('generic_general_ai',0)
    if p.get('status')=='archived': pen+=ps.get('archived',0)
    return sw,cw,pen

def main():
    ap=argparse.ArgumentParser(description='Score normalized project records and separate official/ecosystem ranking'); ap.parse_args()
    c=cfg(); projects=load_jsonish('data/projects.yaml')
    for p in projects:
        normalize_project_fields(p); s=p.setdefault('score',{}); stars=p.get('stars')
        s.setdefault('activity',2 if p.get('source_type')=='github' else 1)
        s['adoption']=max(s.get('adoption',0),score_from_stars(stars))
        cats=p.get('category',[])
        if any(x in cats for x in ['mcp-acp-a2a','skills-prompts','rules-instructions','context-engineering']): s['ecosystem_value']=max(s.get('ecosystem_value',0),4)
        elif p.get('ranking_scope')=='ecosystem': s['ecosystem_value']=max(s.get('ecosystem_value',0),3)
        if p.get('record_kind')=='official-tool':
            s.update({'ecosystem_value':5,'activity':3,'adoption':3,'practicality':5,'novelty':3,'confidence':5}); p['ranking_scope']='official'
        else:
            if p.get('source_type')=='github': s['confidence']=max(s.get('confidence',0),4)
            if p.get('source_type')=='exa': s['confidence']=max(s.get('confidence',0),3)
            if p.get('source_type')=='fallback-web': s['confidence']=min(max(s.get('confidence',0),2),2)
            s.setdefault('practicality',3 if p.get('source_type')=='github' else 2); s.setdefault('novelty',2)
        base=total_score(p); sw,cw,pen=adjust(p,c)
        p['score_reason']={'base':base,'source_weight':sw,'category_weight':cw,'penalty':pen}
        p['total_score']=base+sw+cw+pen
    save_jsonish('data/projects.yaml',projects)
    save_jsonish('data/scores.yaml',[{'id':p['id'],'score':p.get('score',{}),'score_reason':p.get('score_reason',{}),'total_score':p.get('total_score',total_score(p)),'ranking_scope':p.get('ranking_scope')} for p in projects])
    print(json.dumps({'scored':len(projects),'official':sum(1 for p in projects if p.get('ranking_scope')=='official'),'ecosystem':sum(1 for p in projects if p.get('ranking_scope')=='ecosystem')},ensure_ascii=False))
if __name__=='__main__': main()
