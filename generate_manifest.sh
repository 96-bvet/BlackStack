#!/bin/bash

TARGET_DIR=~/BlackStack/BlackStack
MANIFEST_FILE=sentinel_manifest.yaml

echo "modules:" > "$MANIFEST_FILE"

find "$TARGET_DIR" -type f -name "*.py" | while read -r filepath; do
  filename=$(basename "$filepath")
  relpath="${filepath/#$TARGET_DIR\//}"

  echo "  - name: $filename" >> "$MANIFEST_FILE"
  echo "    path: $relpath" >> "$MANIFEST_FILE"
  echo "    cluster: unassigned" >> "$MANIFEST_FILE"
  echo "    role: unknown" >> "$MANIFEST_FILE"
  echo "    status: pending" >> "$MANIFEST_FILE"
done

echo "Manifest generated at $MANIFEST_FILE"
