#!/bin/bash

# WachterEID: embed_hash_log.sh
# Embed hash lineage into decrypted vault

VAULT_DECRYPTED="$1"
AUDIT_LOG="$HOME/BlackStack/WachterEID/logs/audit/decrypt.log"
REGISTRY_INDEX="$HOME/BlackStack/WachterEID/registry/decrypt/decrypted_index.json"

# === Validate Input ===
if [[ ! -f "$VAULT_DECRYPTED" ]]; then
  echo "$(date -Iseconds) | ERROR | Vault not found: $VAULT_DECRYPTED" >> "$AUDIT_LOG"
  exit 1
fi

# === Compute Hash ===
VAULT_HASH=$(sha256sum "$VAULT_DECRYPTED" | awk '{print $1}')
TIMESTAMP=$(date -Iseconds)
PERSONA=$(whoami)

# === Embed Metadata ===
echo "## Vault Metadata" >> "$VAULT_DECRYPTED"
echo "Decrypted by: $PERSONA" >> "$VAULT_DECRYPTED"
echo "Timestamp: $TIMESTAMP" >> "$VAULT_DECRYPTED"
echo "SHA256: $VAULT_HASH" >> "$VAULT_DECRYPTED"

# === Update Registry ===
jq --arg file "$(basename "$VAULT_DECRYPTED")" \
   --arg hash "$VAULT_HASH" \
   --arg time "$TIMESTAMP" \
   --arg persona "$PERSONA" \
   '.vaults += [{"file":$file,"hash":$hash,"timestamp":$time,"persona":$persona}]' \
   "$REGISTRY_INDEX" > "${REGISTRY_INDEX}.tmp" && mv "${REGISTRY_INDEX}.tmp" "$REGISTRY_INDEX"

# === Log Success ===
echo "$TIMESTAMP | HASH EMBEDDED | $VAULT_DECRYPTED | $VAULT_HASH" >> "$AUDIT_LOG"
