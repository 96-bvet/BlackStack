from pathlib import Path
import hashlib
import yaml
import re

HOME = Path.home()
SCAN_PATHS = [
    HOME / "cai" / "tools",
    HOME / "cai" / "src" / "cai" / "agents",
    HOME / "cai"
]

TOOL_MANIFEST = HOME / "BlackStack" / "WachterEID" / "config" / "tool_manifest.yaml"
LICENSE_MANIFEST = HOME / "BlackStack" / "WachterEID" / "config" / "license_manifest.yaml"

VALID_SUFFIXES = [".py", ".sh", ".pl", ".bash", ".ps1"]
SKIP_PATTERNS = ["__init__.py", "test_", "legacy_", "deprecated_"]

def hash_file(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def extract_license_header(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [next(f) for _ in range(20)]
        license_line = next((l for l in lines if "license" in l.lower()), None)
        if license_line:
            match = re.search(r"(MIT|GPL|Apache|BSD|Creative Commons)", license_line, re.IGNORECASE)
            return match.group(1) if match else None
    except Exception:
        pass
    return None

def categorize(name):
    name = name.lower()
    if "dfir" in name or "memory" in name or "reverse" in name:
        return "forensic"
    if "wifi" in name or "sast" in name or "red" in name:
        return "cybersecurity"
    return "misc"

def scan_all():
    tools = []
    licenses = []
    for scan_path in SCAN_PATHS:
        for file in scan_path.rglob("*"):
            if file.is_file() and file.suffix in VALID_SUFFIXES:
                if file.name in SKIP_PATTERNS or any(file.name.startswith(p) for p in SKIP_PATTERNS):
                    continue

                rel_path = str(file.relative_to(HOME / "cai"))
                hash_val = hash_file(file)
                license_type = extract_license_header(file)
                category = categorize(file.stem)

                tools.append({
                    "name": file.stem,
                    "path": rel_path,
                    "type": file.suffix[1:],
                    "category": category,
                    "hash": hash_val,
                    "approved": False,
                    "import": True,
                    "license_stub": license_type is None
                })

                if license_type:
                    licenses.append({
                        "file": rel_path,
                        "license": license_type,
                        "attribution_required": True,
                        "hash": hash_val
                    })

    return tools, licenses

def write_manifests(tools, licenses):
    with TOOL_MANIFEST.open("w") as f:
        yaml.dump({"tools": tools}, f, sort_keys=False)
    with LICENSE_MANIFEST.open("w") as f:
        yaml.dump({"licenses": licenses}, f, sort_keys=False)
    print(f"[✓] tool_manifest.yaml written with {len(tools)} entries.")
    print(f"[✓] license_manifest.yaml written with {len(licenses)} entries.")

if __name__ == "__main__":
    tools, licenses = scan_all()
    write_manifests(tools, licenses)
