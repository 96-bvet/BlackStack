#!/bin/bash

REGISTRY="$HOME/BlackStack/WachterEID/config/tool_manifest_array.yaml"
TOOLSET="$HOME/cai/tools"
ACTIVE_PERSONA="$1"

yq ".${ACTIVE_PERSONA}[]" "$REGISTRY" | while read -r entry; do
  name=$(echo "$entry" | yq '.name')
  path=$(echo "$entry" | yq '.path')
  hash_expected=$(echo "$entry" | yq '.hash')
  full_path="$HOME/cai/$path"
  target="$TOOLSET/$name.py"

  if [[ ! -f "$full_path" ]]; then
    echo "⚠️ Missing file: $path"
    continue
  fi

  hash_actual=$(sha256sum "$full_path" | awk '{print $1}')
  if [[ "$hash_actual" != "$hash_expected" ]]; then
    echo "❌ Hash mismatch: $name"
    continue
  fi

  ln -sf "$full_path" "$target"
  echo "✅ Loaded: $name → $target"
done
