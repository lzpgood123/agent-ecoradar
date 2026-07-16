#!/usr/bin/env python3
"""Detect seed-tools changes: find tools that need onboarding.

Compares current seed-tools against a snapshot of previously onboarded tools.
Tools that are active but not yet onboarded (or previously failed) are flagged.

Rules:
  - status==active AND onboard_state in (missing, pending, failed) -> needs onboarding
  - id not in last snapshot's active_ids -> needs onboarding (even if onboard_state=done,
    to handle the case where a tool was added after last snapshot)
  - However, onboard_state=done AND id in snapshot -> skip (already done)
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_jsonish, save_jsonish
from seed_tools_schema import load_seed_tools, iter_active_tools

SNAPSHOT_PATH = 'data/seed-tools.snapshot.json'

# onboard states that indicate onboarding is needed
NEEDS_ONBOARD_STATES = {'pending', 'failed', None, ''}


def load_snapshot(path: str | None = None) -> dict:
    """Load the last snapshot of active tool ids.

    Returns {'active_ids': [...]} or empty if no snapshot exists.
    """
    p = Path(path) if path else (ROOT / SNAPSHOT_PATH)
    if not p.exists():
        return {'active_ids': []}
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
        if isinstance(data, dict) and 'active_ids' in data:
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {'active_ids': []}


def update_snapshot(tools: list[dict], path: str | None = None) -> None:
    """Write current active tool ids to snapshot file."""
    p = Path(path) if path else (ROOT / SNAPSHOT_PATH)
    active_ids = [t['id'] for t in tools if t.get('status') == 'active']
    snapshot = {'active_ids': active_ids}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snapshot, indent=2) + '\n', encoding='utf-8')


def detect_pending_onboard(tools: list[dict], snapshot: dict | None = None) -> list[str]:
    """Find tool ids that need onboarding.

    A tool needs onboarding if:
    - It is active
    - AND (onboard_state is pending/failed/missing) OR (id not in snapshot)

    Args:
        tools: Current seed-tools list
        snapshot: {'active_ids': [...]} from last run

    Returns:
        List of tool ids needing onboarding
    """
    if snapshot is None:
        snapshot = load_snapshot()

    snapshot_ids = set(snapshot.get('active_ids', []))
    pending: list[str] = []

    for tool in iter_active_tools(tools):
        tid = tool.get('id')
        if not tid:
            continue

        onboard_state = tool.get('onboard_state')

        # Done tools are never re-pending (even if not in snapshot)
        if onboard_state == 'done':
            continue

        # Currently running -> skip
        if onboard_state == 'running':
            continue

        # Needs onboarding if:
        # - onboard_state is pending/failed/missing
        # - OR id not in snapshot (new tool since last snapshot)
        if onboard_state in NEEDS_ONBOARD_STATES or tid not in snapshot_ids:
            pending.append(tid)

    return pending


def main():
    """CLI: detect pending onboard and optionally update snapshot."""
    import argparse
    ap = argparse.ArgumentParser(description='Detect seed-tools that need onboarding')
    ap.add_argument('--dry-run', action='store_true', help='Do not update snapshot')
    ap.add_argument('--update-snapshot', action='store_true',
                    help='Update snapshot after detection (only done tools)')
    args = ap.parse_args()

    tools = load_seed_tools(normalize=True)
    snapshot = load_snapshot()

    pending = detect_pending_onboard(tools, snapshot)

    print(f"Snapshot has {len(snapshot.get('active_ids', []))} active ids")
    print(f"Current active tools: {len(list(iter_active_tools(tools)))}")
    print(f"Pending onboarding: {len(pending)}")

    if pending:
        print("\nPending tool ids:")
        for tid in pending:
            print(f"  - {tid}")
    else:
        print("\nNo tools need onboarding.")

    if args.update_snapshot and not args.dry_run:
        update_snapshot(tools)
        print(f"\nSnapshot updated: {SNAPSHOT_PATH}")

    # Output as JSON for machine consumption
    result = {'pending': pending, 'snapshot_ids': snapshot.get('active_ids', [])}
    print(f"\n{json.dumps(result, ensure_ascii=False)}")

    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
