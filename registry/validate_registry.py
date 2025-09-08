# registry/validate_registry.py

import yaml, json
from datetime import datetime
from registry import load_registry, sync_json_from_yaml
from registry.persona_loader import JSON_REGISTRY

def load_json_registry():
    with open(JSON_REGISTRY, "r") as f:
        return json.load(f)

def validate_registry():
    yaml_data = load_registry()
    json_data = load_json_registry()

    yaml_personas = yaml_data.get("personas", {})
    json_personas = json_data.get("personas", {})

    report = {
        "missing_in_json": [],
        "extra_in_json": [],
        "tone_mismatches": [],
        "module_desyncs": [],
        "status_conflicts": []
    }

    for name, ydata in yaml_personas.items():
        jdata = json_personas.get(name)
        if not jdata:
            report["missing_in_json"].append(name)
            continue

        if ydata.get("modules") != jdata.get("modules"):
            report["module_desyncs"].append(name)

        if ydata.get("tone_profile", {}) != jdata.get("tone_profile", {}):
            report["tone_mismatches"].append(name)

        if ydata.get("status") != jdata.get("status"):
            report["status_conflicts"].append(name)

    for name in json_personas:
        if name not in yaml_personas:
            report["extra_in_json"].append(name)

    log_validation_report(report)
    return report

def log_validation_report(report):
    with open("audit/registry_diff.md", "a") as log:
        log.write(f"# Registry Validation Report — {datetime.now().isoformat()}\n\n")
        for key, items in report.items():
            if items:
                log.write(f"## {key.replace('_', ' ').title()}\n")
                for item in items:
                    log.write(f"- {item}\n")
                log.write("\n")
        log.write("---\n\n")
