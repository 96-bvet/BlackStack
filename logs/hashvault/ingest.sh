#!/bin/bash
TARGET_DIR="$1"
APPROVED_PERSONA="$2"

if [[ "$APPROVED_PERSONA" != "blackhawk63" ]]; then
  echo "Access denied: persona mismatch"
  exit 1
fi

find "$TARGET_DIR" -type f | while read -r file; do
  HASH=$(sha256sum "$file" | awk '{print $1}')
  echo "$(date -Iseconds) | $file | $HASH" >> ~/WachterEID/logs/hashvault/vault.db
done

echo "Hash ingest complete for $TARGET_DIR"
