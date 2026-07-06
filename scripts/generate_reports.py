#!/usr/bin/env python3
import argparse, json, collections, datetime, subprocess
from common import ROOT, load_jsonish, total_score

def run(cmd):
    p=subprocess.run(cmd, shell=True, cwd=ROOT, text=True, capture_output=True, timeout=120)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def main():
    ap=argparse.ArgumentParser(description='Generate final delivery reports')
    ap.parse_args()
    now=datetime.date.today().isoformat(); reports=ROOT/'docs/reports'; reports.mkdir(parents=True, exist_ok=True)
    projects=load_jsonish('data/projects.yaml'); curated=load_jsonish('data/curated-projects.yaml'); rejected=load_jsonish('data/rejected-projects.yaml'); tools=load_jsonish('data/seed-tools.yaml')
    src=collections.Counter(p.get('source_type') for p in projects); kinds=collections.Counter(p.get('record_kind') for p in projects); scopes=collections.Counter(p.get('ranking_scope') for p in projects); tool_counts=collections.Counter(t for p in projects for t in p.get('target_tools',[])); cat_counts=collections.Counter(c for p in projects for c in p.get('category',[]))
    eco_top=sorted([p for p in projects if p.get('ranking_scope')=='ecosystem' and p.get('record_kind')!='official-tool' and p.get('review_state')!='rejected'], key=total_score, reverse=True)
    curated_top=sorted(curated, key=total_score, reverse=True)
    code,out,err=run('mcporter list 2>&1'); code2,out2,err2=run("mcporter call 'exa.web_search_exa(query: \"Claude Code ecosystem MCP skills\", count: 3)' 2>&1"); exa_ok=(code2==0)
    (reports/'exa-status-and-fallback.md').write_text(f"""# Exa Status and Fallback — {now}

## mcporter list

```text
{out or err}
```

## Exa probe

```bash
mcporter call 'exa.web_search_exa(query: "Claude Code ecosystem MCP skills", count: 3)'
```

Exit code: `{code2}`

```text
{out2 or err2}
```

## Status

{"Exa is available and can be used for semantic search." if exa_ok else "Exa is not configured in current mcporter environment. Existing non-GitHub web data is labeled fallback-web / fallback-not-exa and must not be treated as Exa results."}
""", encoding='utf-8')
    def bullets(counter): return '\n'.join([f'- {k}: {v}' for k,v in sorted(counter.items())])
    final=f"""# Final Delivery Report — {now}

## Status

Search in Coding final-delivery package is built with quality gates, curated data, final reports, upgraded site data, automation templates, and export packaging.

## Metrics

- Normalized records: {len(projects)}
- Curated records: {len(curated)}
- Rejected/noisy records: {len(rejected)}
- GitHub records: {src.get('github',0)}
- Fallback web records: {src.get('fallback-web',0)}
- Official seed records: {src.get('official-seed',0)}
- Exa records: {src.get('exa',0)}

## Source counts

{bullets(src)}

## Record kinds

{bullets(kinds)}

## Ranking scopes

{bullets(scopes)}

## Tool coverage

{bullets(tool_counts)}

## Category coverage

{bullets(cat_counts)}

## Top ecosystem projects (official tools excluded)

""" + '\n'.join([f"{i+1}. [{p['name']}]({p['url']}) — score {total_score(p)} — {', '.join(p.get('category',[]))}" for i,p in enumerate(eco_top[:20])]) + f"\n\n## Exa status\n\nSee `docs/reports/exa-status-and-fallback.md`. Current Exa availability: {'available' if exa_ok else 'blocked / not configured'}.\n"
    (reports/'final-delivery-report.md').write_text(final, encoding='utf-8')
    curated_md='# Curated Top Projects — '+now+'\n\nOfficial tools are excluded.\n\n| # | Name | Source | Level | Score | Categories | URL |\n|---:|---|---|---|---:|---|---|\n' + '\n'.join([f"| {i+1} | {p['name'].replace('|','/')} | {p.get('source_type')} | {p.get('recommendation_level','watch')} | {total_score(p)} | {', '.join(p.get('category',[]))} | {p['url']} |" for i,p in enumerate(curated_top[:80])])+'\n'
    (reports/'curated-top-projects.md').write_text(curated_md, encoding='utf-8')
    source_audit=f"""# Source Quality Audit — {now}

- Verified records: {sum(1 for p in projects if p.get('source_quality')=='verified')}
- Fallback records: {sum(1 for p in projects if p.get('source_quality')=='fallback')}
- Unverified records: {sum(1 for p in projects if p.get('source_quality')=='unverified')}
- Rejected/noisy records: {len(rejected)}

Fallback records are discovery leads, not Exa results. They are marked `fallback-web` and tagged `fallback-not-exa`.

## Rejected sample

""" + '\n'.join([f"- [{p['name']}]({p['url']}) — {p.get('rejection_reason','rejected/noisy')}" for p in rejected[:20]]) + '\n'
    (reports/'source-quality-audit.md').write_text(source_audit, encoding='utf-8')
    comparison=['# Tool Ecosystem Comparison — '+now+'\n']
    for t in tools:
        tid=t['id']; rel=[p for p in projects if tid in p.get('target_tools',[]) and p.get('review_state')!='rejected']; rel_cur=[p for p in curated if tid in p.get('target_tools',[])]; cats=collections.Counter(c for p in rel for c in p.get('category',[]))
        comparison += [f"\n## {t['name']}\n", f"- Total records: {len(rel)}", f"- Curated records: {len(rel_cur)}", f"- Extension points: {', '.join(t.get('extension_points',[]))}", f"- Main categories: {', '.join([f'{k}({v})' for k,v in cats.most_common(6)]) or 'N/A'}", "- Recommended records:"]
        for p in sorted(rel_cur, key=total_score, reverse=True)[:5]: comparison.append(f"  - [{p['name']}]({p['url']}) — {p.get('recommendation_level','watch')} — score {total_score(p)}")
    (reports/'tool-ecosystem-comparison.md').write_text('\n'.join(comparison)+'\n', encoding='utf-8')
    (reports/'trends-and-opportunities.md').write_text(f"""# Trends and Opportunities — {now}

## Strong trends

1. Cross-agent rules and instruction files are becoming a reusable asset layer: CLAUDE.md, AGENTS.md, Cursor rules, OpenCode commands.
2. MCP/ACP/A2A integrations are the most important connectivity layer for coding agents.
3. Context engineering is durable: repo maps, code graphs, memory, indexing, and documentation ingestion.
4. AI PR review and CI automation remain practical adoption paths.
5. Terminal agents and AI IDEs are converging.

## Opportunities

- Build a cross-tool rules/skills registry.
- Maintain a curated MCP-for-coding directory.
- Run real task benchmarks across Claude Code, Codex, OpenCode, Goose, Cursor, and Hermes.
- Produce Chinese-language practical guides for agentic coding workflows.

## Risks

- Fallback web search is lower-confidence than Exa.
- Star counts can be noisy and should not be the only ranking signal.
""", encoding='utf-8')
    (reports/'next-90-days-roadmap.md').write_text(f"""# Next 90 Days Roadmap — {now}

## Days 1-30

- Configure Exa in mcporter or document exact MCP setup procedure.
- Review the top 50 curated records manually.
- Add screenshots or live preview instructions for the static site.
- Schedule Hermes daily discovery and weekly report jobs.

## Days 31-60

- Add package/download metrics where available.
- Add changelog diffing for official tools.
- Add benchmark/evaluation records and task comparison templates.

## Days 61-90

- Publish the repository/site.
- Create contribution guidelines for submitting new projects.
- Build a monthly trend report archive.
- Expand Chinese community source coverage.
""", encoding='utf-8')
    print(json.dumps({'reports':7,'projects':len(projects),'curated':len(curated),'rejected':len(rejected),'exa_ok':exa_ok}, ensure_ascii=False))
if __name__=='__main__': main()
