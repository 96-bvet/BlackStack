#!/bin/bash
cat ~/WachterEID/logs/hashvault/vault.db | while read -r line; do
  FILE=$(echo "$line" | cut -d'|' -f2 | xargs)
  HASH=$(echo "$line" | cut -d'|' -f3 | xargs)
  CURRENT=$(sha256sum "$FILE" | awk '{print $1}')
  if [[ "$HASH" != "$CURRENT" ]]; then
    echo "⚠️ Mismatch: $FILE"
  fi
done

