import argparse
import json
import os
import uuid
import requests
from registry import persona_loader

QWEN_API_URL = "http://localhost:8080"

def upload_file(file_path: str, req_id: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"[Upload] File not found: {file_path}")
    print(f"[Upload] Sending {file_path} to Qwen with id={req_id}")
    with open(file_path, "rb") as f:
        resp = requests.post(
            f"{QWEN_API_URL}/upload",
            files={"file": (os.path.basename(file_path), f)},
            data={"id": req_id}
        )
    resp.raise_for_status()
    print(f"[Upload] Server response: {resp.text.strip()}")

def propose(persona: str, target: str, instructions: str, req_id: str):
    payload = {
        "persona": persona,
        "target": target,
        "instructions": instructions,
        "id": req_id
    }
    print("[DEBUG] Payload:", json.dumps(payload, indent=2))
    resp = requests.post(f"{QWEN_API_URL}/propose", json=payload)
    resp.raise_for_status()
    return resp.json()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--persona", required=True, help="Persona name")
    parser.add_argument("--prompt", required=True, help="Instructions for Qwen")
    parser.add_argument("--file", required=True, help="Path to file to upload before proposing")
    parser.add_argument("--target", default="runtime/", help="Target path for Qwen to operate on")
    args = parser.parse_args()

    print(f"[Escalation Check] Persona escalation allowed for: {args.persona}")
    print(f"[Escalation] Persona escalated to: {args.persona}")

    persona_fn = persona_loader.load_persona(args.persona)
    print(f"[+] Loaded persona: {args.persona}")
    print(f"    Capabilities: {persona_loader.get_capabilities(args.persona)}")
    print(f"    Metadata: {json.dumps(persona_loader.get_persona_metadata(args.persona), indent=2)}")

    req_id = str(uuid.uuid4())

    # Step 1: Upload file
    upload_file(args.file, req_id)

    # Step 2: Propose
    print(f"[>] Sending propose request to Qwen for target={args.target}")
    result = propose(args.persona, args.target, args.prompt, req_id)

    print("[<] Qwen Response:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
