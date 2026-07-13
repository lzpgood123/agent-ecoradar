import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_normalize_resource_types_do_not_false_match():
    normalize = load_module('normalize')
    assert 'mcp-server' not in normalize.resource_types_for('campus demo unrelated')
    assert 'rules' not in normalize.resource_types_for('overrules nothing')
    assert 'mcp-server' in normalize.resource_types_for('Claude Code MCP server integration')

def test_finalize_weak_record_helper():
    finalize = load_module('finalize_data')
    ranking = finalize.DEFAULT_RANKING
    assert finalize.is_weak_record({'total_score': 1}, ranking)
    assert finalize.is_weak_record({'total_score': 10, 'status': 'archived'}, ranking)
    assert not finalize.is_weak_record({'total_score': 50, 'source_type': 'github', 'target_tools': ['claude-code']}, ranking)
