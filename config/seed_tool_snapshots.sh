#!/bin/bash

ROOT="$HOME/cai"
MANIFEST_YAML="$HOME/BlackStack/WachterEID/config/tool_manifest.yaml"
SNAPSHOT_ROOT="$HOME/snapshots/cai"
mkdir -p "$SNAPSHOT_ROOT"

echo "[📦] Seeding rollback snapshots from manifest..."

yq -o=json '.[]' "$MANIFEST_YAML" | jq -c '.[]' | while read entry; do
  path=$(echo "$entry" | jq -r '.path')
  full_path="$ROOT/$path"
  snapshot_path="$SNAPSHOT_ROOT/$path"

  [[ -f "$full_path" ]] || { echo "⚠️ Missing: $full_path"; continue; }

  mkdir -p "$(dirname "$snapshot_path")"
  cp "$full_path" "$snapshot_path"
  echo "✅ Snapshot seeded: $snapshot_path"
done

echo "[✓] Snapshot initialization complete."
