# app/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import time, json, subprocess, hashlib, os

WORKSPACE = Path(os.getenv("WORKSPACE","/workspace"))
AUDIT_DIR = Path(os.getenv("AUDIT_DIR","/audit/logs"))
APPROVALS_DIR = Path(os.getenv("APPROVALS_DIR","/audit/approvals"))
MODE = os.getenv("MODE","ro")
PERSONA = os.getenv("SURGEON_PERSONA","qwen_surgeon")

app = FastAPI(title="Qwen Code Surgeon")

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    if p.is_file():
        h.update(p.read_bytes())
    else:
        for child in sorted([*p.rglob("*")]):
            if child.is_file():
                h.update(child.relative_to(WORKSPACE).as_posix().encode())
                h.update(child.read_bytes())
    return h.hexdigest()

class Proposal(BaseModel):
    target: str
    instructions: str
    id: str

@app.get("/status")
def status():
    return {"mode": MODE, "workspace": str(WORKSPACE), "persona": PERSONA}

@app.post("/propose")
def propose(p: Proposal):
    target_path = (WORKSPACE / p.target).resolve()
    if not str(target_path).startswith(str(WORKSPACE)):
        raise HTTPException(400, "Target outside workspace")

    # Snapshot pre-hash
    before_hash = sha256(target_path if target_path.exists() else WORKSPACE)

    # Here Qwen would generate a diff; we stub via `git diff --no-index`
    # Expect client to upload a temp modified copy into /tmp to compute diff
    tmp_mod = Path("/tmp")/f"{p.id}.mod"
    if not tmp_mod.exists():
        raise HTTPException(400, "Upload modified file to /tmp/<id>.mod first")

    # Write a copy of original for diff compare
    tmp_orig = Path("/tmp")/f"{p.id}.orig"
    if target_path.is_file():
        tmp_orig.write_bytes(target_path.read_bytes())
    else:
        raise HTTPException(400, "For simplicity, demo supports file targets")

    diff = subprocess.run(
        ["git","diff","--no-index","--","/tmp/"+p.id+".orig","/tmp/"+p.id+".mod"],
        capture_output=True,text=True
    ).stdout

    stamp = int(time.time()*1000)
    audit_file = AUDIT_DIR / f"{stamp}_{p.id}_proposal.json"
    audit_file.write_text(json.dumps({
        "persona": PERSONA,
        "id": p.id,
        "target": p.target,
        "instructions": p.instructions,
        "before_hash": before_hash,
        "diff": diff,
        "ts": stamp
    }, indent=2))
    return {"proposal_id": p.id, "audit": str(audit_file), "diff": diff}

class Approval(BaseModel):
    id: str
    approver: str

@app.post("/approve")
def approve(a: Approval):
    (APPROVALS_DIR / f"{a.id}.approved").write_text(json.dumps({
        "id": a.id, "approver": a.approver, "ts": int(time.time()*1000)
    }))
    return {"status":"approved","id":a.id}

class Apply(BaseModel):
    id: str
    target: str

@app.post("/apply")
def apply(ap: Apply):
    if MODE != "rw":
        raise HTTPException(403, "Container is read-only; set MODE=rw to allow writes")
    approval = APPROVALS_DIR / f"{ap.id}.approved"
    if not approval.exists():
        raise HTTPException(403, "No approval token found")

    target_path = (WORKSPACE / ap.target).resolve()
    if not str(target_path).startswith(str(WORKSPACE)):
        raise HTTPException(400, "Target outside workspace")
    if not target_path.is_file():
        raise HTTPException(400, "Target must be a file for this demo")

    before_hash = sha256(target_path)
    tmp_mod = Path("/tmp")/f"{ap.id}.mod"
    if not tmp_mod.exists():
        raise HTTPException(400, "Missing /tmp/<id>.mod content to apply")

    target_path.write_bytes(tmp_mod.read_bytes())
    after_hash = sha256(target_path)

    stamp = int(time.time()*1000)
    (AUDIT_DIR / f"{stamp}_{ap.id}_apply.json").write_text(json.dumps({
        "persona": PERSONA,
        "id": ap.id,
        "target": ap.target,
        "before_hash": before_hash,
        "after_hash": after_hash,
        "approved_by": json.loads(approval.read_text())["approver"],
        "ts": stamp
    }, indent=2))
    return {"status":"applied","id":ap.id,"before_hash":before_hash,"after_hash":after_hash}
