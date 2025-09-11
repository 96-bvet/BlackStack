"""
surgeon_v2 persona — Qwen-compatible entry point.
Scans Python modules for import‑time side effects and proposes safe refactoring steps.
"""

import ast
from pathlib import Path

def run_persona_logic(prompt: str, context: dict = None) -> dict:
    """
    Qwen-compatible entry point for surgeon_v2.
    """
    if "import-time side effects" in prompt.lower():
        return scan_for_import_side_effects(base_dir="runtime")
    return {
        "status": "ok",
        "message": f"[surgeon_v2] No specialized handler for prompt: {prompt}"
    }

def scan_for_import_side_effects(base_dir: str) -> dict:
    """
    Walks the given directory, parses each .py file, and flags
    top‑level executable statements that will run on import.
    """
    findings = []
    proposals = []

    for py_file in Path(base_dir).rglob("*.py"):
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError) as e:
            findings.append({
                "file": str(py_file),
                "issue": f"Parse error: {e}"
            })
            continue

        for node in tree.body:
            # Allowed at top level: imports, defs, class defs, docstrings
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                continue  # module docstring

            findings.append({
                "file": str(py_file),
                "issue": f"Top‑level {type(node).__name__} executes on import",
                "lineno": getattr(node, "lineno", None)
            })
            proposals.append({
                "file": str(py_file),
                "fix": "Move this logic into a function or `if __name__ == '__main__':` block."
            })

    return {
        "status": "ok",
        "findings": findings,
        "proposals": proposals
    }
