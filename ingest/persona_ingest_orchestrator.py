from modules.manifest_parser import parse_manifest
from modules.persona_router import match_persona
from modules.approval_gate import trigger_approval
from modules.snapshot_logger import log_snapshot
from modules.refactor_engine import suggest_split
from modules.registry_updater import update_registry

def ingest_tool(manifest_path):
    tool_data = parse_manifest(manifest_path)
    if not tool_data:
        print("Manifest parsing failed. Tool skipped.")
        return

    persona = match_persona(tool_data)
    approved = trigger_approval(tool_data, persona)

    if not approved:
        print("Approval denied. Tool not ingested.")
        return

    refactored_list = suggest_split(tool_data)

    for entry in refactored_list:
        update_registry(entry, persona)
        log_snapshot(entry, persona)

if __name__ == "__main__":
    ingest_tool("path/to/new_tool.yaml")
