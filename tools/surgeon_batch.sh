#!/usr/bin/env bash
set -euo pipefail

# Resolve absolute path to scope file
SCOPE_FILE="$(realpath "$1")"
INSTRUCTIONS="$2"
AUDIT_DIR="/opt/sentinel/audit/staged/patches"
SURGEON_URL="http://localhost:8080"

# Ensure audit dir exists
sudo mkdir -p "$AUDIT_DIR"

# Read includes and excludes
mapfile -t INCLUDES < <(yq -r '.scope.include[]' "$SCOPE_FILE" | sed 's|"||g')
mapfile -t EXCLUDES < <(yq -r '.scope.exclude[]' "$SCOPE_FILE" | sed 's|"||g')

# Expand directories into file list
TARGETS=()
for ITEM in "${INCLUDES[@]}"; do
    if [ -d "$ITEM" ]; then
        while IFS= read -r FILE; do
            TARGETS+=("$FILE")
        done < <(find "$ITEM" -type f -name "*.py")
    elif [ -f "$ITEM" ]; then
        TARGETS+=("$ITEM")
    else
        echo "[WARN] Skipping missing: $ITEM"
    fi
done

# Remove excluded paths
for EX in "${EXCLUDES[@]}"; do
    TARGETS=("${TARGETS[@]/$EX}")
done

# Process each file
for FILE in "${TARGETS[@]}"; do
    [ -z "$FILE" ] && continue
    ID="OPT_$(basename "$FILE" | tr '.' '_' | tr '-' '_')"
    echo "[INFO] Processing $FILE (ID: $ID)"

    # Upload file
    curl -s -X PUT --data-binary @"$FILE" "$SURGEON_URL/upload/${ID}.mod" > /dev/null

    # Propose optimization
    DIFF_JSON=$(curl -s "$SURGEON_URL/propose" \
      -H "Content-Type: application/json" \
      -d "{
            \"id\": \"$ID\",
            \"target\": \"$FILE\",
            \"instructions\": \"$INSTRUCTIONS Scope manifest: $(tr '\n' ' ' < $SCOPE_FILE | sed 's/\"/\\\"/g')\"
          }")

    # Save diff + hash with sudo
    echo "$DIFF_JSON" | jq -r '.diff' | sudo tee "$AUDIT_DIR/${ID}.patch" > /dev/null
    sha256sum "$AUDIT_DIR/${ID}.patch" | sudo tee "$AUDIT_DIR/${ID}.patch.sha256" > /dev/null

    echo "[OK] Proposal saved: $AUDIT_DIR/${ID}.patch"
done

echo "[DONE] All proposals generated. Review diffs in $AUDIT_DIR."
