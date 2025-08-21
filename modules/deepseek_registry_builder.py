import yaml, hashlib, os, sys
from pathlib import Path

# Load manifest
manifest_path = Path.home() / "BlackStack/WachterEID/config/tool_manifest_array.yaml"
with open(manifest_path, "r") as f:
    tools = yaml.safe_load(f)

registry = {}

def analyze_tool(tool):
    path = Path.home() / "cai" / tool["path"]
    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Simulated DeepSeek logic
    persona = "blue_team" if "log" in content else "red_team" if "exploit" in content else "misc"
    tone = "clinical" if "audit" in content else "neutral"
    ethics = "audit-safe" if "trace" in content else "forensic" if "log" in content else "unclassified"
    hashval = hashlib.sha256(content.encode()).hexdigest()

    return {
        "id": tool["name"],
        "path": tool["path"],
        "hash": hashval,
        "tone": tone,
        "ethics": ethics
    }, persona

# Build registry
for tool in tools:
    if not tool.get("approved") or not tool.get("import"):
        continue

    result = analyze_tool(tool)
    if not result:
        continue

    entry, persona = result
    if persona not in registry:
        registry[persona] = []
    registry[persona].append(entry)

# Write registry
output_path = Path.home() / "BlackStack/WachterEID/config/persona_tool_registry.yaml"
with open(output_path, "w") as f:
    yaml.dump(registry, f, sort_keys=False)

print(f"✅ Persona registry built: {output_path}")
