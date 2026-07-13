"""Tests for normalize.py field mapping and resource_type classification.

Covers batch A3 (field mapping) and A4 (resource_type misclassification).
"""
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


# ============================================================
# A3: github_record() field mapping tests
# ============================================================

def test_github_record_stars_from_stargazerCount():
    """stars should be extracted from stargazerCount (repo view API)."""
    normalize = load_module('normalize')
    item = {
        'nameWithOwner': 'test/repo',
        'url': 'https://github.com/test/repo',
        'description': 'test',
        'stargazerCount': 1234,
        'forkCount': 10,
    }
    rec = normalize.github_record(item, [])
    assert rec['stars'] == 1234, f"stars={rec['stars']}"


def test_github_record_stars_from_stargazersCount():
    """stars should fall back to stargazersCount (search API)."""
    normalize = load_module('normalize')
    item = {
        'fullName': 'test/search-repo',
        'url': 'https://github.com/test/search-repo',
        'description': 'test',
        'stargazersCount': 100,
    }
    rec = normalize.github_record(item, [])
    assert rec['stars'] == 100, f"stars={rec['stars']}"


def test_github_record_forks_from_forkCount():
    """forks should be extracted from forkCount."""
    normalize = load_module('normalize')
    item = {
        'nameWithOwner': 'test/repo',
        'url': 'https://github.com/test/repo',
        'stargazerCount': 100,
        'forkCount': 56,
    }
    rec = normalize.github_record(item, [])
    assert rec['forks'] == 56, f"forks={rec['forks']}"


def test_github_record_license_from_spdxId():
    """license should be extracted from licenseInfo.spdxId."""
    normalize = load_module('normalize')
    item = {
        'nameWithOwner': 'test/repo',
        'url': 'https://github.com/test/repo',
        'stargazerCount': 100,
        'forkCount': 10,
        'licenseInfo': {'spdxId': 'MIT'},
    }
    rec = normalize.github_record(item, [])
    assert rec['license'] == 'MIT', f"license={rec['license']}"


def test_github_record_license_null_when_no_license():
    """license should be None when licenseInfo is null."""
    normalize = load_module('normalize')
    item = {
        'nameWithOwner': 'test/repo',
        'url': 'https://github.com/test/repo',
        'stargazerCount': 100,
        'forkCount': 10,
        'licenseInfo': None,
    }
    rec = normalize.github_record(item, [])
    assert rec['license'] is None, f"license={rec['license']}"


def test_github_record_license_noassertion_becomes_null():
    """NOASSERTION license should become None."""
    normalize = load_module('normalize')
    item = {
        'nameWithOwner': 'test/repo',
        'url': 'https://github.com/test/repo',
        'stargazerCount': 100,
        'forkCount': 10,
        'licenseInfo': {'spdxId': 'NOASSERTION'},
    }
    rec = normalize.github_record(item, [])
    assert rec['license'] is None, f"license={rec['license']}"


def test_github_record_license_from_key_fallback():
    """When spdxId is None, license should fall back to 'key' field (gh repo view behavior)."""
    normalize = load_module('normalize')
    item = {
        'nameWithOwner': 'test/repo',
        'url': 'https://github.com/test/repo',
        'stargazerCount': 100,
        'forkCount': 10,
        'licenseInfo': {'key': 'mit', 'name': 'MIT License', 'spdxId': None},
    }
    rec = normalize.github_record(item, [])
    assert rec['license'] == 'mit', f"license={rec['license']}"


def test_github_record_languages_from_primaryLanguage():
    """languages should be extracted from primaryLanguage.name."""
    normalize = load_module('normalize')
    item = {
        'nameWithOwner': 'test/repo',
        'url': 'https://github.com/test/repo',
        'stargazerCount': 100,
        'forkCount': 10,
        'primaryLanguage': {'name': 'Python'},
    }
    rec = normalize.github_record(item, [])
    assert rec['languages'] == ['Python'], f"languages={rec['languages']}"


def test_github_record_languages_from_language_string():
    """languages should fall back to 'language' string field (search API)."""
    normalize = load_module('normalize')
    item = {
        'fullName': 'test/search-repo',
        'url': 'https://github.com/test/search-repo',
        'stargazersCount': 100,
        'language': 'JavaScript',
    }
    rec = normalize.github_record(item, [])
    assert rec['languages'] == ['JavaScript'], f"languages={rec['languages']}"


def test_github_record_languages_empty_when_null():
    """languages should be empty list when primaryLanguage is null."""
    normalize = load_module('normalize')
    item = {
        'nameWithOwner': 'test/repo',
        'url': 'https://github.com/test/repo',
        'stargazerCount': 100,
        'forkCount': 10,
        'primaryLanguage': None,
    }
    rec = normalize.github_record(item, [])
    assert rec['languages'] == [], f"languages={rec['languages']}"


def test_github_record_topics_from_repositoryTopics():
    """topics should be extracted from repositoryTopics list."""
    normalize = load_module('normalize')
    item = {
        'nameWithOwner': 'test/repo',
        'url': 'https://github.com/test/repo',
        'stargazerCount': 100,
        'forkCount': 10,
        'repositoryTopics': [{'name': 'claude'}, {'name': 'skill'}],
    }
    rec = normalize.github_record(item, [])
    assert rec['topics'] == ['claude', 'skill'], f"topics={rec['topics']}"


def test_github_record_topics_empty_when_missing():
    """topics should be empty list when repositoryTopics is missing."""
    normalize = load_module('normalize')
    item = {
        'nameWithOwner': 'test/repo',
        'url': 'https://github.com/test/repo',
        'stargazerCount': 100,
        'forkCount': 10,
    }
    rec = normalize.github_record(item, [])
    assert rec['topics'] == [], f"topics={rec['topics']}"


def test_github_record_readme_preview():
    """readme_preview should be first 500 chars of readme."""
    normalize = load_module('normalize')
    item = {
        'nameWithOwner': 'test/repo',
        'url': 'https://github.com/test/repo',
        'stargazerCount': 100,
        'forkCount': 10,
        'readme': '# Test\n\nThis is a test readme.' + 'x' * 600,
    }
    rec = normalize.github_record(item, [])
    assert len(rec['readme_preview']) == 500, f"readme_preview len={len(rec['readme_preview'])}"


def test_github_record_readme_preview_empty_when_missing():
    """readme_preview should be empty string when readme is missing."""
    normalize = load_module('normalize')
    item = {
        'nameWithOwner': 'test/repo',
        'url': 'https://github.com/test/repo',
        'stargazerCount': 100,
        'forkCount': 10,
    }
    rec = normalize.github_record(item, [])
    assert rec['readme_preview'] == '', f"readme_preview={rec['readme_preview']!r}"


# ============================================================
# A4: resource_types_for() classification tests
# ============================================================

def test_skill_not_misclassified_as_tutorial_caveman():
    """'Claude Code skill' should be classified as 'skills', not just 'tutorial'."""
    normalize = load_module('normalize')
    types = normalize.resource_types_for('caveman Claude Code skill that cuts 65% of tokens')
    assert 'skills' in types, f"caveman types={types}"


def test_skill_not_misclassified_as_tutorial_humanizer():
    normalize = load_module('normalize')
    types = normalize.resource_types_for('humanizer Claude Code skill that removes signs of AI-generated writing')
    assert 'skills' in types, f"humanizer types={types}"


def test_skill_not_misclassified_as_tutorial_book_to_skill():
    normalize = load_module('normalize')
    types = normalize.resource_types_for('Turn any technical book PDF into a Claude Code skill')
    assert 'skills' in types, f"book-to-skill types={types}"


def test_extension_detected():
    """'extension' keyword should be classified as 'extension' type."""
    normalize = load_module('normalize')
    types = normalize.resource_types_for('Conductor is a Gemini CLI extension that allows you to specify')
    assert 'extension' in types, f"conductor types={types}"


def test_tutorial_still_detected():
    """Tutorial keywords should still be detected when no concrete type matches."""
    normalize = load_module('normalize')
    types = normalize.resource_types_for('Best practices for AI coding agents tutorial')
    assert 'tutorial' in types, f"tutorial types={types}"


def test_mcp_server_detected():
    normalize = load_module('normalize')
    types = normalize.resource_types_for('Claude Code as one-shot MCP server')
    assert 'mcp-server' in types, f"mcp types={types}"


def test_rules_detected():
    normalize = load_module('normalize')
    types = normalize.resource_types_for('Curated list of awesome Cursor Rules .mdc files')
    assert 'rules' in types, f"rules types={types}"


def test_agent_framework_detected():
    normalize = load_module('normalize')
    types = normalize.resource_types_for('Multi-agent orchestration framework')
    assert 'agent-framework' in types, f"framework types={types}"


def test_rules_not_false_match_overrules():
    """'overrules' should not match 'rules' keyword (substring issue)."""
    normalize = load_module('normalize')
    assert 'rules' not in normalize.resource_types_for('overrules nothing')


def test_mcp_not_false_match_campus():
    normalize = load_module('normalize')
    assert 'mcp-server' not in normalize.resource_types_for('campus demo unrelated')


def test_default_tutorial_when_nothing_matches():
    """When nothing matches, default to ['tutorial']."""
    normalize = load_module('normalize')
    types = normalize.resource_types_for('some random project about coding')
    assert types == ['tutorial'], f"default types={types}"
