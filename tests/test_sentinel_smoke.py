import py_compile
import pytest
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SCOPE_FILE = PROJECT_ROOT / "sentinel_scope.yaml"

with open(SCOPE_FILE, "r", encoding="utf-8") as f:
    scope = yaml.safe_load(f)

includes = scope.get("scope", {}).get("include", [])
excludes = set(scope.get("scope", {}).get("exclude", []))

def expand_targets(paths):
    files = []
    for p in paths:
        path_obj = PROJECT_ROOT / p
        if path_obj.is_dir():
            for py_file in path_obj.rglob("*.py"):
                if any(str(py_file).startswith(str(PROJECT_ROOT / ex)) for ex in excludes):
                    continue
                files.append(py_file)
        elif path_obj.is_file():
            files.append(path_obj)
    return files

target_files = expand_targets(includes)

@pytest.mark.parametrize("path", target_files)
def test_all_modules_compile(path):
    """Ensure all modules compile without syntax errors (no imports)."""
    py_compile.compile(path, doraise=True)
