#!/bin/bash

ROOT="$HOME/cai"
MANIFEST_YAML="$HOME/BlackStack/WachterEID/config/tool_manifest.yaml"
AUDIT_DIR="$ROOT/audit"
TREE_MANIFEST="$AUDIT_DIR/tree_manifest.txt"
mkdir -p "$AUDIT_DIR"

echo "[📥] Parsing tool entries from $MANIFEST_YAML..."
> "$TREE_MANIFEST"

# Use yq to extract structured entries
yq -o=json '.[]' "$MANIFEST_YAML" | jq -c '.[]' | while read entry; do
  name=$(echo "$entry" | jq -r '.name')
  path=$(echo "$entry" | jq -r '.path')
  hash=$(echo "$entry" | jq -r '.hash')
  approved=$(echo "$entry" | jq -r '.approved')
  category=$(echo "$entry" | jq -r '.category')

  IFS='/' read -ra parts <<< "$path"
  indent=""
  for ((i=0; i<${#parts[@]}-1; i++)); do
    indent+="  "
    echo "$indent📁 ${parts[i]}" >> "$TREE_MANIFEST"
  done

  indent+="  "
  status="❌"
  [[ "$approved" == "true" ]] && status="✅"

  echo "$indent📄 ${parts[-1]} — $hash [$status] ($category)" >> "$TREE_MANIFEST"
  echo "" >> "$TREE_MANIFEST"
done

echo "[✓] Tree manifest created: $TREE_MANIFEST"
