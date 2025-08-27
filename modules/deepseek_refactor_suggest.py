import re, yaml
from pathlib import Path

manifest_path = Path.home() / "BlackStack/WachterEID/config/tool_manifest_array.yaml"
suggestions_path = Path.home() / "BlackStack/WachterEID/config/refactor_suggestions.yaml"

def suggest_split(tool):
    path = Path.home() / "cai" / tool["path"]
    if not path.exists(): return None

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.findall(r"(def\s+\w+\(.*?\):)", content)
    if len(blocks) > 5:
        return {
            "tool": tool["name"],
            "path": tool["path"],
            "suggested_split": len(blocks),
            "reason": "Monolithic logic detected"
        }

with open(manifest_path, "r") as f:
    tools = yaml.safe_load(f)

suggestions = [suggest_split(t) for t in tools if t.get("approved")]
suggestions = [s for s in suggestions if s]

with open(suggestions_path, "w") as f:
    yaml.dump(suggestions, f, sort_keys=False)

print(f"🧠 Refactor suggestions saved: {suggestions_path}")
