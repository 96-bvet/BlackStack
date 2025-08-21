for tool in $tools; do
  category=$(yq e ".tools[] | select(.name == \"$tool\") | .category" "$MANIFEST")

  echo -e "\n[🛠️] Tool: $tool"
  echo "[📁] Category: $category"

  if [[ "$category" == "cybersecurity" || "$category" == "forensic" ]]; then
    echo "[⚡] Auto-approving $tool (category: $category)"
    confirm="y"
  else
    read -p "Approve this tool? [y/N]: " confirm
  fi

  if [[ "$confirm" == "y" ]]; then
    # Patch manifest
    yq e "(.tools[] | select(.name == \"$tool\") | .approved) = true" -i "$MANIFEST"

    # Log decision
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[✓] $tool approved at $timestamp by shell" >> "$LOG"

    # Save rollback snapshot
    mkdir -p "$ROLLBACK_DIR"
    yq e ".tools[] | select(.name == \"$tool\")" "$MANIFEST" > "$ROLLBACK_DIR/$tool.yaml"

    echo "[📦] Approval logged and rollback snapshot saved."
  else
    echo "[⏭️] Skipped: $tool"
  fi
done
