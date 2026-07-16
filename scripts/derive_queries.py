#!/usr/bin/env python3
"""Derive GitHub search queries from active seed-tools.

This is the HARD GATE of Batch B: without derive_queries, "just edit yaml"
doesn't work because daily collection still uses the old static queries.

Flow:
  seed-tools.yaml (active only) -> per-tool queries -> dedup -> merge with manual -> queries.yaml

Query templates per tool:
  - "{alias} skills"          (if extension_points includes 'skills')
  - "{alias} mcp"             (if extension_points includes 'mcp')
  - "{alias} rules"           (if extension_points includes 'rules')
  - "{alias} hooks"           (if extension_points includes 'hooks')
  - "{alias} extension"       (generic, if extension_points non-empty)
  - "{alias} coding agent"    (generic, always)

Plus general ecosystem queries (always included).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_jsonish, save_jsonish
from seed_tools_schema import load_seed_tools, iter_active_tools

# ---- Constants ----

MAX_QUERIES_PER_TOOL = 6
MAX_TOTAL_QUERIES = 80

QUERIES_PATH = 'data/queries.yaml'
MANUAL_QUERIES_PATH = 'data/queries.manual.yaml'

# Extension point -> query suffix mapping
EXT_POINT_QUERIES = {
    'skills': '{alias} skills',
    'mcp': '{alias} mcp',
    'mcp extensions': '{alias} mcp',
    'rules': '{alias} rules',
    'hooks': '{alias} hooks',
    'slash-commands': '{alias} commands',
    'subagents': '{alias} subagent',
    'plugins': '{alias} plugin',
    'recipes': '{alias} recipes',
    'commands': '{alias} commands',
    'agents': '{alias} agent',
}

# General ecosystem queries (always included, not tool-specific)
GENERAL_QUERIES = [
    'AI coding agent context engineering',
    'mcp server coding agent',
    'AI PR review agent',
    'spec driven development AI coding',
    'codebase indexing AI coding agent',
    'agentic coding workflow',
]


def _generate_tool_queries(tool: dict) -> list[str]:
    """Generate queries for a single tool based on its aliases and extension points."""
    aliases = tool.get('aliases', [])
    if not aliases:
        return []

    # Use the primary alias (first one) for most queries to avoid explosion
    primary_alias = aliases[0]
    ext_points = tool.get('extension_points', [])

    queries: list[str] = []

    # Extension-point-specific queries
    seen_suffixes: set[str] = set()
    for ep in ext_points:
        template = EXT_POINT_QUERIES.get(ep)
        if template and template not in seen_suffixes:
            queries.append(template.format(alias=primary_alias))
            seen_suffixes.add(template)

    # Generic coding agent query (always)
    queries.append(f'{primary_alias} coding agent')

    # For closed tools, add an ecosystem query using alias
    if tool.get('tool_kind') == 'closed':
        queries.append(f'{primary_alias} ecosystem extensions')

    # Cap per-tool queries
    return queries[:MAX_QUERIES_PER_TOOL]


def derive_queries(tools: list[dict]) -> list[str]:
    """Generate GitHub search queries from active seed-tools.

    Args:
        tools: List of tool dicts (will be filtered to active only)

    Returns:
        Deduplicated list of query strings, capped at MAX_TOTAL_QUERIES
    """
    all_queries: list[str] = []

    for tool in iter_active_tools(tools):
        tool_queries = _generate_tool_queries(tool)
        all_queries.extend(tool_queries)

    # Add general ecosystem queries
    all_queries.extend(GENERAL_QUERIES)

    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for q in all_queries:
        key = q.lower().strip()
        if key not in seen:
            seen.add(key)
            deduped.append(q)

    return deduped[:MAX_TOTAL_QUERIES]


def merge_with_manual(derived: list[str], manual: list[str]) -> list[str]:
    """Merge derived queries with manual extras, deduplicating.

    Args:
        derived: Queries generated from seed-tools
        manual: Manually curated extra queries

    Returns:
        Merged deduplicated list (derived first, then manual extras)
    """
    seen: set[str] = set()
    result: list[str] = []

    for q in derived + manual:
        key = q.lower().strip()
        if key not in seen:
            seen.add(key)
            result.append(q)

    return result


def main():
    """CLI: derive queries and write to data/queries.yaml."""
    import argparse
    ap = argparse.ArgumentParser(description='Derive GitHub queries from active seed-tools')
    ap.add_argument('--dry-run', action='store_true', help='Print queries without writing')
    ap.add_argument('--merge-manual', action='store_true', default=True,
                    help='Merge with data/queries.manual.yaml if it exists (default: True)')
    args = ap.parse_args()

    tools = load_seed_tools(normalize=True)
    active = list(iter_active_tools(tools))
    print(f"Loaded {len(tools)} tools ({len(active)} active)")

    derived = derive_queries(tools)
    print(f"Derived {len(derived)} queries from active tools")

    # Merge with manual queries if available
    manual = []
    manual_path = ROOT / MANUAL_QUERIES_PATH
    if manual_path.exists():
        manual_data = load_jsonish(MANUAL_QUERIES_PATH)
        if isinstance(manual_data, dict):
            manual = manual_data.get('github', [])
        elif isinstance(manual_data, list):
            manual = manual_data

    if manual:
        merged = merge_with_manual(derived, manual)
        print(f"Merged with {len(manual)} manual queries -> {len(merged)} total")
    else:
        merged = derived

    output = {'github': merged}

    if args.dry_run:
        print("\nQueries:")
        for i, q in enumerate(merged, 1):
            print(f"  {i:3d}. {q}")
    else:
        save_jsonish(QUERIES_PATH, output)
        print(f"Wrote {len(merged)} queries to {QUERIES_PATH}")

    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
