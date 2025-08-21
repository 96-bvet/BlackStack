#!/bin/bash

ROOT="$HOME/cai"
MANIFEST_YAML="$HOME/BlackStack/WachterEID/config/tool_manifest.yaml"
SNAPSHOT_ROOT="$HOME/snapshots/cai"
AUDIT_DIR="$ROOT/audit"
DIFF_LOG="$AUDIT_DIR/snapshot_diffs.log"
mkdir -p "$AUDIT_DIR"

echo "[🔍] Validating tool integrity against snapshots..."
> "$DIFF_LOG"

yq -o=json '.[]' "$MANIFEST_YAML" | jq -c '.[]' | while read entry; do
  path=$(echo "$entry" | jq -r '.path')
  expected_hash=$(echo "$entry" | jq -r '.hash')
  full_path="$ROOT/$path"
  snapshot_path="$SNAPSHOT_ROOT/$path"

  [[ -f "$full_path" && -f "$snapshot_path" ]] || {
    echo "⚠️ Missing file or snapshot: $path" >> "$DIFF_LOG"
    continue
  }

  actual_hash=$(sha256sum "$full_path" | awk '{print $1}')
  if [[ "$actual_hash" != "$expected_hash" ]]; then
    echo "❌ Hash mismatch: $path" >> "$DIFF_LOG"
    echo "→ Manifest:  $expected_hash" >> "$DIFF_LOG"
    echo "→ Live:      $actual_hash" >> "$DIFF_LOG"
    echo "" >> "$DIFF_LOG"
  else
    echo "✅ Verified: $path" >> "$DIFF_LOG"
  fi
done

echo "[✓] Snapshot validation complete."
echo "→ Log: $DIFF_LOG"
