#!/usr/bin/env python3
import os
import sys
import hashlib
import difflib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# === CONFIG ===
LOG_PATH = "/home/blackhawk63/BlackStack/logs/mutator.log"
BLACKSTACK_DIR = Path(__file__).resolve().parent.parent  # BlackStack/BlackStack root

# VRAM-aware limits
TARGET_TOKENS_PER_BATCH = 6000       # ~input tokens per batch (tune for your GPU)
MAX_FILE_CHARS = 24000               # hard cap per file (~6k tokens)
MAP_HEAD_LINES = 5                   # lines per file in project map
MAP_MAX_BYTES = 120_000              # cap project map size (bytes)
OUTPUT_BUDGET_TOKENS = 800           # target per-file output budget

# === UTILS ===
def log_mutation(text, persona, source="qwen2.5-mutator"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, 'a') as log:
        log.write(f"[{timestamp}] {persona} ({source}): {text}\n")

def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def approx_tokens_from_text(s: str) -> int:
    # Fast heuristic: ~4 chars per token
    return max(1, len(s) // 4)

def output_budget_clause() -> str:
    return (
        f"Do not exceed approximately {OUTPUT_BUDGET_TOKENS} tokens of output per file. "
        f"Return ONLY updated files using this exact format for EACH file:\n"
        f"===FILE: <relative_path>===\n<updated code>\n===END_FILE===\n"
        f"No commentary outside these file sections."
    )

def build_project_map(root_dir: Path) -> str:
    """Slim project map: relative paths + first lines, with a global size cap."""
    entries, total = [], 0
    for path in sorted(root_dir.rglob("*.py")):
        rel = path.relative_to(root_dir)
        try:
            head = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:MAP_HEAD_LINES]
            block = f"{rel}:\n" + "\n".join(head) + "\n\n"
            b = block.encode("utf-8", errors="ignore")
            if total + len(b) > MAP_MAX_BYTES:
                entries.append("...[TRIMMED PROJECT MAP]...\n")
                break
            entries.append(block)
            total += len(b)
        except Exception as e:
            entries.append(f"{rel}: [ERROR reading file: {e}]\n")
    return "".join(entries)

# === DIFF + APPROVAL ===
def _show_diff_and_approve(rel_path: str, before: str, after: str, persona="DefaultOps") -> bool:
    diff = difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        fromfile=f"{rel_path} (before)",
        tofile=f"{rel_path} (after)",
        lineterm=""
    )
    print("\n".join(diff))
    ans = input(f"\nApply changes to {rel_path}? (y/yes to apply): ").strip().lower()
    ok = ans in ("y", "yes")
    log_mutation(f"Approval {'GRANTED' if ok else 'DENIED'} for {rel_path}", persona)
    return ok

# === SINGLE FILE ===
def mutate_code(file_path: str, instructions: str, persona="DefaultOps") -> str:
    target = BLACKSTACK_DIR / file_path
    if not target.exists():
        return f"[ERROR] File not found: {target}"

    original = target.read_text(encoding="utf-8")
    before_hash = file_hash(target)

    from sentinel import qwen_mutate
    prompt = (
        f"{output_budget_clause()}\n\n"
        f"Refactor the following Python file according to these instructions:\n"
        f"{instructions}\n\n"
        f"File: {file_path}\nCode:\n{original}"
    )
    updated = qwen_mutate(prompt)

    if not updated or updated.startswith("[ERROR]"):
        return updated if updated else "[ERROR] Empty response from daemon."

    if _show_diff_and_approve(file_path, original, updated, persona):
        target.write_text(updated, encoding="utf-8")
        after_hash = file_hash(target)
        log_mutation(f"Updated {file_path} | before={before_hash} | after={after_hash}", persona)
        return f"[OK] Updated {file_path}"
    else:
        return "[CANCELLED]"

# === TREE (file-by-file) ===
def mutate_tree(instructions: str, persona="DefaultOps"):
    project_map = build_project_map(BLACKSTACK_DIR)
    from sentinel import qwen_mutate

    for path in sorted(BLACKSTACK_DIR.rglob("*.py")):
        rel = str(path.relative_to(BLACKSTACK_DIR))
        original = path.read_text(encoding="utf-8")
        before_hash = file_hash(path)

        prompt = (
            f"{output_budget_clause()}\n\n"
            f"Project map:\n{project_map}\n\n"
            f"Refactor the file {rel} according to these instructions:\n{instructions}\n\n"
            f"Code:\n{original}"
        )
        updated = qwen_mutate(prompt)
        if not updated or updated.startswith("[ERROR]"):
            print(updated if updated else "[ERROR] Empty response from daemon.")
            continue

        if _show_diff_and_approve(rel, original, updated, persona):
            path.write_text(updated, encoding="utf-8")
            after_hash = file_hash(path)
            log_mutation(f"Updated {rel} | before={before_hash} | after={after_hash}", persona)
            print(f"[OK] Updated {rel}")
            # Refresh project map so subsequent files see latest contexts
            project_map = build_project_map(BLACKSTACK_DIR)
        else:
            print(f"[CANCELLED] {rel}")

# === BATCH HELPERS ===
def split_batch_to_budget(batch_files: List[str], root: Path) -> List[List[str]]:
    sub_batches, cur, cur_tokens = [], [], 0
    for rel in batch_files:
        p = root / rel
        if not p.exists():
            continue
        code = p.read_text(encoding="utf-8", errors="ignore")[:MAX_FILE_CHARS]
        t = approx_tokens_from_text(code)
        if cur and cur_tokens + t > TARGET_TOKENS_PER_BATCH:
            sub_batches.append(cur)
            cur, cur_tokens = [], 0
        cur.append(rel)
        cur_tokens += t
    if cur:
        sub_batches.append(cur)
    return sub_batches

def enforce_budget_on_batches(batches: List[List[str]], root: Path) -> List[List[str]]:
    final = []
    for batch in batches:
        final.extend(split_batch_to_budget(batch, root))
    return final

# === BATCH PROMPT/RESPONSE ===
def _format_batch_prompt(project_map: str, batch_files: List[str], instructions: str) -> str:
    sections = [
        "You are performing a coordinated, multi-file refactor.",
        output_budget_clause(),
        "\nGlobal goal:\n" + instructions,
        "\nProject map (for context, do not rewrite this section):\n" + project_map,
        "\nFiles to refactor in this batch:"
    ]
    for rel in batch_files:
        code = (BLACKSTACK_DIR / rel).read_text(encoding="utf-8", errors="ignore")[:MAX_FILE_CHARS]
        sections.append(f"\n===FILE: {rel}===\n{code}\n===END_FILE===")
    return "\n".join(sections)

def _parse_batch_response(text: str) -> Dict[str, str]:
    results: Dict[str, str] = {}
    rel = None
    buf: List[str] = []

    def flush():
        if rel is not None:
            results[rel] = "\n".join(buf).rstrip("\n")

    for line in text.splitlines():
        if line.startswith("===FILE:") and line.endswith("==="):
            flush()
            rel = line[len("===FILE:"):-len("===")].strip()
            buf = []
        elif line.strip() == "===END_FILE===":
            flush()
            rel, buf = None, []
        else:
            if rel is not None:
                buf.append(line)
    if rel is not None:
        flush()
    return results

def _apply_batch(batch_updates: Dict[str, str], persona="DefaultOps"):
    if not batch_updates:
        print("[INFO] No parsable file sections returned; skipping batch.")
        return

    pending: List[Tuple[Path, str, str, str]] = []
    for rel, updated in batch_updates.items():
        path = BLACKSTACK_DIR / rel
        if not path.exists():
            print(f"[WARN] Skipping non-existent path: {rel}")
            continue
        original = path.read_text(encoding="utf-8", errors="ignore")
        diff = "\n".join(difflib.unified_diff(
            original.splitlines(),
            updated.splitlines(),
            fromfile=f"{rel} (before)",
            tofile=f"{rel} (after)",
            lineterm=""
        ))
        print(diff)
        pending.append((path, rel, original, updated))

    if not pending:
        print("[INFO] Nothing to apply in this batch.")
        return

    ans = input("\nApply ALL changes in this batch? (y/yes to apply): ").strip().lower()
    if ans not in ("y", "yes"):
        for _, rel, _, _ in pending:
            log_mutation(f"Batch change DENIED for {rel}", persona)
        print("[CANCELLED] Batch not applied.")
        return

    for path, rel, original, updated in pending:
        before_hash = file_hash(path)
        path.write_text(updated, encoding="utf-8")
        after_hash = file_hash(path)
        log_mutation(f"Batch update {rel} | before={before_hash} | after={after_hash}", persona)
    print("[OK] Batch applied.")

# === BATCH ORCHESTRATION ===
def plan_batches(project_map: str, instructions: str) -> List[List[str]]:
    from sentinel import qwen_mutate
    prompt = (
        "You are planning a coordinated refactor.\n"
        "Given the following project map, group related files into batches for refactoring.\n"
        "Constraints:\n"
        "- Keep batches small enough to fit in a single LLM prompt (recommended 3-6 files per batch).\n"
        "- Group files by feature or tight coupling (imports, shared types, shared config).\n"
        "- Output plain text, one batch per line, with relative paths separated by commas.\n"
        "- Only include files that actually exist in the project.\n\n"
        f"High-level goal:\n{instructions}\n\n"
        f"Project map:\n{project_map}"
    )
    plan = qwen_mutate(prompt) or ""
    batches: List[List[str]] = []
    for line in plan.splitlines():
        if ".py" not in line:
            continue
        parts = [p.strip() for p in line.split(",") if ".py" in p]
        parts = [p for p in parts if (BLACKSTACK_DIR / p).exists()]
        if parts:
            batches.append(parts)

    # Fallback: if nothing planned, just chunk all .py files
    if not batches:
        all_files = [str(p.relative_to(BLACKSTACK_DIR)) for p in BLACKSTACK_DIR.rglob("*.py")]
        for i in range(0, len(all_files), 4):  # 4 files per batch
            batches.append(all_files[i:i+4])

    return batches

    plan = qwen_mutate(prompt)
    batches: List[List[str]] = []
    for line in (plan or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",") if p.strip()]
        parts = [p for p in parts if p.endswith(".py")]
        if parts:
            batches.append(parts)
    return batches

def mutate_tree_batched(instructions: str, persona="DefaultOps"):
    """Batched refactor with global context + adaptive splitting + final integration pass."""
    from sentinel import qwen_mutate

    # Phase 1: Build global context and plan batches
    project_map = build_project_map(BLACKSTACK_DIR)
    batches = plan_batches(project_map, instructions)
    if not batches:
        print("[WARN] No batches planned; falling back to file-by-file.")
        return mutate_tree(instructions, persona)

    # Enforce VRAM-aware budgets
    batches = enforce_budget_on_batches(batches, BLACKSTACK_DIR)
    print(f"[INFO] Planned {len(batches)} budgeted batches.")
    for i, batch in enumerate(batches, 1):
        print(f"  - Batch {i}: {', '.join(batch)}")

    # Phase 2: Process each batch with retries if needed
    for i, batch in enumerate(batches, 1):
        print(f"\n[INFO] Processing Batch {i}/{len(batches)}")
        valid = [rel for rel in batch if (BLACKSTACK_DIR / rel).exists()]
        if not valid:
            print("[WARN] Batch contained no valid files; skipping.")
            continue

        prompt = _format_batch_prompt(project_map, valid, instructions)
        response = qwen_mutate(prompt)

        if not response or response.startswith("[ERROR]"):
            print("[WARN] Batch failed or timed out; splitting and retrying...")
            sub_batches = split_batch_to_budget(valid, BLACKSTACK_DIR)
            for sb in sub_batches:
                sprompt = _format_batch_prompt(project_map, sb, instructions)
                sresp = qwen_mutate(sprompt)
                if not sresp or sresp.startswith("[ERROR]"):
                    print("[WARN] Sub-batch still failed; splitting into single files.")
                    for single in sb:
                        sprompt2 = _format_batch_prompt(project_map, [single], instructions)
                        sresp2 = qwen_mutate(sprompt2)
                        if not sresp2 or sresp2.startswith("[ERROR]"):
                            print(f"[ERROR] Could not process {single}; skipping.")
                            continue
                        updates2 = _parse_batch_response(sresp2)
                        _apply_batch(updates2, persona)
                else:
                    updates = _parse_batch_response(sresp)
                    _apply_batch(updates, persona)
        else:
            updates = _parse_batch_response(response)
            _apply_batch(updates, persona)

        # Refresh global context after any applied changes
        project_map = build_project_map(BLACKSTACK_DIR)

    # Phase 3: Cross-batch integration pass
    print("\n[INFO] Running cross-batch integration pass...")
    project_map = build_project_map(BLACKSTACK_DIR)
    integration_prompt = (
        "You are finalizing a multi-batch refactor. Using the updated project map, "
        "identify and fix cross-batch inconsistencies (imports, shared constants, "
        "audit hooks, logging schemas, config paths). " + output_budget_clause() + "\n\n"
        f"Project map:\n{project_map}"
    )
    integration_resp = qwen_mutate(integration_prompt)
    if integration_resp and not integration_resp.startswith("[ERROR]"):
        updates = _parse_batch_response(integration_resp)
        if updates:
            _apply_batch(updates, persona)
        else:
            print("[INFO] Integration pass produced no file changes.")
    else:
        print("[WARN] Integration pass skipped or errored.")
