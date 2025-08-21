import yaml, hashlib
from pathlib import Path

manifest_path = Path.home() / "BlackStack/WachterEID/config/tool_manifest_array.yaml"
output_path = Path.home() / "BlackStack/WachterEID/config/deepseek_scan_output.yaml"

def scan_tool(tool):
    path = Path.home() / "cai" / tool["path"]
    if not path.exists(): return None

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    persona = "blue_team" if "log" in content else "red_team" if "exploit" in content else "misc"
    cluster = "audit" if "trace" in content else "ops"
    confidence = 0.9 if "verify" in content else 0.6
    hashval = hashlib.sha256(content.encode()).hexdigest()

    return {
        "id": tool["name"],
        "path": tool["path"],
        "persona": persona,
        "cluster": cluster,
        "confidence": round(confidence, 2),
        "hash": hashval
    }

with open(manifest_path, "r") as f:
    tools = yaml.safe_load(f)

scan_results = [scan_tool(t) for t in tools if t.get("approved") and t.get("import")]
scan_results = [r for r in scan_results if r]

with open(output_path, "w") as f:
    yaml.dump(scan_results, f, sort_keys=False)

print(f"✅ DeepSeek scan complete: {output_path}")
