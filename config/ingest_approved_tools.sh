#!/bin/bash

ROOT="$HOME/cai"
MANIFEST="$HOME/BlackStack/WachterEID/config/tool_manifest.yaml"
SNAPSHOT="$HOME/snapshots/cai"
LOG="$ROOT/audit/ingest.log"
mkdir -p "$(dirname "$LOG")"

> "$LOG"
yq -o=json '.[]' "$MANIFEST" | jq -c '.[]' | while read entry; do
  path=$(echo "$entry" | jq -r '.path')
  hash=$(echo "$entry" | jq -r '.hash')
  approved=$(echo "$entry" | jq -r '.approved')
  live="$ROOT/$path"
  snap="$SNAPSHOT/$path"

  [[ "$approved" != "true" ]] && continue
  [[ -f "$live" && -f "$snap" ]] || continue

  actual=$(sha256sum "$live" | awk '{print $1}')
  [[ "$actual" != "$hash" ]] && {
    echo "❌ Skipped (hash mismatch): $path" >> "$LOG"
    continue
    if [[ "$actual" != "$hash" ]]; then
  echo "❌ Skipped (hash mismatch): $path" >> "$LOG"

  yq -i '.quarantined += [{"path":"'"$path"'","reason":"hash mismatch","timestamp":"'"$(date +%F_%T)"'","persona":"'"$persona"'"}]' ~/cai/quarantine/failed_modules.yaml
  continue
fi

  }

  echo "✅ Ingested: $path" >> "$LOG"
  # Insert actual ingest logic here (e.g., move, symlink, register)
done

