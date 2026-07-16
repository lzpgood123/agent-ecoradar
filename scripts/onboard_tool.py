#!/usr/bin/env python3
"""Onboard a tool: run the standard pipeline to integrate a new tool.

Standard onboarding pipeline (per tool):
1. Validate minimal fields (id, name, aliases)
2. Mark onboard_state=running in seed-tools.yaml
3. Specialized collection (NOT bulk): use tool aliases to generate queries
4. normalize.py --source github (merge into projects.yaml, preserving LLM fields)
5. score.py (update quantifiable scores)
6. Optional LLM: weekly_analysis.py --max-projects N (for this tool's projects)
7. finalize + generate_reports + build_site
8. deploy_site.py --dest /var/www/ecoradar.lzpgood.online (can skip)
9. Mark onboard_state=done or failed

NEVER calls initial_collection.py (bulk historical collection).
"""
import sys
import json
import subprocess
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, run
from seed_tools_schema import (
    load_seed_tools, save_seed_tools, normalize_tool_entry,
    validate_tools, iter_active_tools, VALID_ONBOARD_STATES,
)
from derive_queries import _generate_tool_queries
from detect_seed_tools_diff import detect_pending_onboard, update_snapshot, load_snapshot

DEPLOY_DEST = '/var/www/ecoradar.lzpgood.online'
DEFAULT_MAX_PROJECTS = 50
DEFAULT_GITHUB_LIMIT = 20


def _set_onboard_state(tools: list[dict], tool_id: str, state: str, error: str | None = None) -> list[dict]:
    """Update onboard_state for a tool in the tools list (in-place)."""
    for t in tools:
        if t.get('id') == tool_id:
            t['onboard_state'] = state
            if state == 'done':
                t['onboarded_at'] = datetime.datetime.now().isoformat()
                t.pop('onboard_error', None)
            if error:
                t['onboard_error'] = error
            break
    return tools


def run_pipeline(tool: dict, dry_run: bool = False, skip_llm: bool = False,
                 skip_deploy: bool = False, max_projects: int = DEFAULT_MAX_PROJECTS,
                 github_limit: int = DEFAULT_GITHUB_LIMIT) -> dict:
    """Run the standard onboarding pipeline for a single tool.

    Returns dict with 'ok' bool and 'steps' list of {step, status, detail}.
    """
    tool_id = tool.get('id', 'unknown')
    steps = []

    if dry_run:
        # In dry-run, just show what would happen
        queries = _generate_tool_queries(tool)
        steps.append({
            'step': 'validate',
            'status': 'ok',
            'detail': f'Tool {tool_id} valid: {len(tool.get("aliases", []))} aliases, kind={tool.get("tool_kind")}'
        })
        steps.append({
            'step': 'collect',
            'status': 'dry_run',
            'detail': f'Would run {len(queries)} queries with limit={github_limit}'
        })
        steps.append({
            'step': 'normalize',
            'status': 'dry_run',
            'detail': 'Would run normalize.py --source github'
        })
        steps.append({
            'step': 'score',
            'status': 'dry_run',
            'detail': 'Would run score.py'
        })
        if not skip_llm:
            steps.append({
                'step': 'llm',
                'status': 'dry_run',
                'detail': f'Would run weekly_analysis.py --max-projects {max_projects}'
            })
        steps.append({
            'step': 'build',
            'status': 'dry_run',
            'detail': 'Would run build_site.py'
        })
        if not skip_deploy:
            steps.append({
                'step': 'deploy',
                'status': 'dry_run',
                'detail': f'Would deploy to {DEPLOY_DEST}'
            })
        return {'ok': True, 'steps': steps}

    # Step 1: Validate
    errors = validate_tools([tool])
    if errors:
        steps.append({'step': 'validate', 'status': 'fail', 'detail': '; '.join(errors)})
        return {'ok': False, 'steps': steps}
    steps.append({'step': 'validate', 'status': 'ok', 'detail': f'Tool {tool_id} valid'})

    # Step 2: Specialized collection (NOT bulk)
    # Generate temporary queries for this tool and run collect_github
    queries = _generate_tool_queries(tool)
    if queries:
        # Write temporary queries file for this tool
        temp_queries = {'github': queries}
        from common import save_jsonish
        save_jsonish('data/queries.yaml', temp_queries)
        steps.append({'step': 'derive_queries', 'status': 'ok',
                       'detail': f'Generated {len(queries)} queries for {tool_id}'})

        # Run collect_github
        r = run(f'python3 scripts/collect_github.py --limit {github_limit}', timeout=600)
        if r.returncode != 0:
            steps.append({'step': 'collect', 'status': 'fail',
                          'detail': f'collect_github failed: {r.stderr[:200]}'})
            return {'ok': False, 'steps': steps}
        steps.append({'step': 'collect', 'status': 'ok', 'detail': f'Collect done: {r.stdout[:200]}'})
    else:
        steps.append({'step': 'collect', 'status': 'skip', 'detail': 'No queries generated (closed tool?)'})

    # Step 3: Normalize
    r = run('python3 scripts/normalize.py --source github', timeout=300)
    if r.returncode != 0:
        steps.append({'step': 'normalize', 'status': 'fail', 'detail': f'normalize failed: {r.stderr[:200]}'})
        return {'ok': False, 'steps': steps}
    steps.append({'step': 'normalize', 'status': 'ok', 'detail': r.stdout[:200]})

    # Step 4: Score
    r = run('python3 scripts/score.py', timeout=120)
    if r.returncode != 0:
        steps.append({'step': 'score', 'status': 'fail', 'detail': f'score failed: {r.stderr[:200]}'})
        return {'ok': False, 'steps': steps}
    steps.append({'step': 'score', 'status': 'ok', 'detail': r.stdout[:200]})

    # Step 5: Finalize
    r = run('python3 scripts/finalize_data.py', timeout=120)
    if r.returncode != 0:
        steps.append({'step': 'finalize', 'status': 'warn', 'detail': f'finalize warning: {r.stderr[:200]}'})
    else:
        steps.append({'step': 'finalize', 'status': 'ok', 'detail': r.stdout[:200]})

    # Step 6: Optional LLM
    if not skip_llm:
        cmd = f'python3 scripts/weekly_analysis.py --max-projects {max_projects} --skip-benchmarks'
        r = run(cmd, timeout=3600)
        if r.returncode != 0:
            steps.append({'step': 'llm', 'status': 'warn', 'detail': f'LLM partial: {r.stderr[:200]}'})
        else:
            steps.append({'step': 'llm', 'status': 'ok', 'detail': r.stdout[:200]})

    # Step 7: Generate reports
    r = run('python3 scripts/generate_reports.py', timeout=120)
    steps.append({'step': 'reports', 'status': 'ok' if r.returncode == 0 else 'warn',
                  'detail': r.stdout[:200] if r.returncode == 0 else r.stderr[:200]})

    # Step 8: Build site
    r = run('python3 scripts/build_site.py', timeout=300)
    if r.returncode != 0:
        steps.append({'step': 'build', 'status': 'fail', 'detail': f'build failed: {r.stderr[:200]}'})
        return {'ok': False, 'steps': steps}
    steps.append({'step': 'build', 'status': 'ok', 'detail': r.stdout[:200]})

    # Step 9: Deploy
    if not skip_deploy:
        r = run(f'python3 scripts/deploy_site.py --dest {DEPLOY_DEST}', timeout=120)
        steps.append({'step': 'deploy', 'status': 'ok' if r.returncode == 0 else 'fail',
                      'detail': r.stdout[:200] if r.returncode == 0 else r.stderr[:200]})

    # Restore derive_queries for all active tools
    run('python3 scripts/derive_queries.py', timeout=60)

    return {'ok': True, 'steps': steps}


def onboard_single(tool_id: str, dry_run: bool = False, skip_llm: bool = False,
                   skip_deploy: bool = False, max_projects: int = DEFAULT_MAX_PROJECTS,
                   force: bool = False) -> dict:
    """Onboard a single tool by id.

    Returns dict with 'tool_id', 'state', and optional 'error'/'reason'/'steps'.
    """
    tools = load_seed_tools(normalize=True)

    # Find the tool
    tool = None
    for t in tools:
        if t.get('id') == tool_id:
            tool = t
            break

    if tool is None:
        return {'tool_id': tool_id, 'state': 'error', 'error': f'Tool "{tool_id}" not found in seed-tools'}

    # Check if active
    if tool.get('status', 'active') != 'active':
        return {'tool_id': tool_id, 'state': 'skipped', 'reason': f'Tool is not active (status={tool.get("status")})'}

    # Check if already done
    if tool.get('onboard_state') == 'done' and not force:
        return {'tool_id': tool_id, 'state': 'skipped', 'reason': 'Tool already onboarded (onboard_state=done). Use --force to re-onboard.'}

    if dry_run:
        result = run_pipeline(tool, dry_run=True, skip_llm=skip_llm,
                              skip_deploy=skip_deploy, max_projects=max_projects)
        return {'tool_id': tool_id, 'state': 'dry_run', 'steps': result.get('steps', [])}

    # Mark running
    tools = _set_onboard_state(tools, tool_id, 'running')
    save_seed_tools(tools)

    try:
        result = run_pipeline(tool, dry_run=False, skip_llm=skip_llm,
                              skip_deploy=skip_deploy, max_projects=max_projects)
        if result['ok']:
            tools = _set_onboard_state(tools, tool_id, 'done')
            save_seed_tools(tools)
            return {'tool_id': tool_id, 'state': 'done', 'steps': result.get('steps', [])}
        else:
            error_msg = '; '.join(s.get('detail', '') for s in result.get('steps', []) if s.get('status') == 'fail')
            tools = _set_onboard_state(tools, tool_id, 'failed', error=error_msg or 'Pipeline failed')
            save_seed_tools(tools)
            return {'tool_id': tool_id, 'state': 'failed', 'error': error_msg, 'steps': result.get('steps', [])}
    except Exception as e:
        tools = _set_onboard_state(tools, tool_id, 'failed', error=str(e))
        save_seed_tools(tools)
        return {'tool_id': tool_id, 'state': 'failed', 'error': str(e)}


def onboard_all_pending(dry_run: bool = False, skip_llm: bool = False,
                        skip_deploy: bool = False, max_projects: int = DEFAULT_MAX_PROJECTS) -> list[dict]:
    """Onboard all pending tools sequentially.

    Single tool failure does not stop the batch.
    """
    tools = load_seed_tools(normalize=True)
    snapshot = load_snapshot()
    pending_ids = detect_pending_onboard(tools, snapshot)

    if not pending_ids:
        return []

    results = []
    for tid in pending_ids:
        result = onboard_single(tid, dry_run=dry_run, skip_llm=skip_llm,
                                skip_deploy=skip_deploy, max_projects=max_projects)
        results.append(result)

    # Update snapshot after batch
    if not dry_run:
        tools = load_seed_tools(normalize=True)
        update_snapshot(tools)

    return results


def main():
    """CLI entry point."""
    import argparse
    ap = argparse.ArgumentParser(description='Onboard a tool into Agent EcoRadar')
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--id', type=str, help='Tool id to onboard')
    group.add_argument('--all-pending', action='store_true', help='Onboard all pending tools')
    ap.add_argument('--dry-run', action='store_true', help='Show what would happen without making changes')
    ap.add_argument('--skip-llm', action='store_true', help='Skip LLM analysis step')
    ap.add_argument('--skip-deploy', action='store_true', help='Skip deployment')
    ap.add_argument('--max-projects', type=int, default=DEFAULT_MAX_PROJECTS,
                    help=f'Max projects for LLM analysis (default: {DEFAULT_MAX_PROJECTS})')
    ap.add_argument('--force', action='store_true', help='Re-onboard even if already done')
    ap.add_argument('--github-limit', type=int, default=DEFAULT_GITHUB_LIMIT,
                    help=f'GitHub search results per query (default: {DEFAULT_GITHUB_LIMIT})')
    args = ap.parse_args()

    if args.all_pending:
        results = onboard_all_pending(
            dry_run=args.dry_run, skip_llm=args.skip_llm,
            skip_deploy=args.skip_deploy, max_projects=args.max_projects
        )
        print(json.dumps({'results': results, 'total': len(results),
                          'done': sum(1 for r in results if r.get('state') == 'done'),
                          'failed': sum(1 for r in results if r.get('state') == 'failed'),
                          }, ensure_ascii=False, indent=2))
    else:
        result = onboard_single(
            args.id, dry_run=args.dry_run, skip_llm=args.skip_llm,
            skip_deploy=args.skip_deploy, max_projects=args.max_projects,
            force=args.force
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
