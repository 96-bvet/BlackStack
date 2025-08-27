#!/bin/bash

MANIFEST="$HOME/BlackStack/WachterEID/config/tool_manifest.yaml"
TOOLROOT="$HOME/cai"
REGISTRY="$HOME/BlackStack/WachterEID/config/persona_tool_registry.yaml"
CLUSTERS="$HOME/BlackStack/WachterEID/config/tool_clusters.yaml"
PENDING="$HOME/BlackStack/WachterEID/config/persona_pending.yaml"
TMP="/tmp/deepseek_analysis.jsonl"

> "$TMP"
mkdir -p "$(dirname "$REGISTRY")"

yq -o=json '.tools[]' "$MANIFEST" | jq -c 'select(.approved == true and .import == true)' | while read entry; do
  name=$(echo "$entry" | jq -r '.name')
  path=$(echo "$entry" | jq -r '.path')
  full_path="$TOOLROOT/$path"

  [[ ! -f "$full_path" ]] && continue

  # Simulated DeepSeek logic pass
  python3 deepseek_scan.py "$full_path" >> "$TMP"
done

jq -s '.' "$TMP" > /tmp/deepseek_results.json

# Write persona registry
jq -r '.[] | select(.confidence >= 0.85) | [.persona, {name: .name, path: .path, hash: .hash}] | @yaml' /tmp/deepseek_results.json > "$REGISTRY"

# Write cluster map
jq -s 'group_by(.cluster) | map({(.[0].cluster): map({name, path})}) | add' /tmp/deepseek_results.json | yq -P > "$CLUSTERS"

# Write pending assignments
jq -r '.[] | select(.confidence < 0.85) | {name, path, suggested_personas: .persona_candidates, confidence}' /tmp/deepseek_results.json | yq -P > "$PENDING"

echo "✅ DeepSeek persona routing complete."
