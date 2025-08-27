#!/bin/bash

# WachterEID: decrypt_vault.sh
# Modular, persona-gated decryption with audit logging and hash verification

# === CONFIG ===
VAULT_ENCRYPTED="$1"
VAULT_DECRYPTED="${VAULT_ENCRYPTED%.gpg}"
PERSONA_ID=$(whoami)
REGISTRY_DIR="$HOME/BlackStack/WachterEID/registry"
LOG_DIR="$HOME/BlackStack/WachterEID/logs"
HASH_INDEX="$LOG_DIR/hashvault/vault_index.json"
AUDIT_LOG="$LOG_DIR/audit/decrypt.log"
APPROVAL_GATE="$REGISTRY_DIR/personas/approved.list"

# === VALIDATE INPUT ===
if [[ ! -f "$VAULT_ENCRYPTED" || "${VAULT_ENCRYPTED##*.}" != "gpg" ]]; then
  echo "❌ Invalid or missing encrypted vault file: $VAULT_ENCRYPTED"
  exit 1
fi

# === CHECK PERSONA APPROVAL ===
if ! grep -q "$PERSONA_ID" "$APPROVAL_GATE"; then
  echo "❌ Persona $PERSONA_ID not approved for decryption"
  echo "$(date -Iseconds) | DENIED | $VAULT_ENCRYPTED | $PERSONA_ID" >> "$AUDIT_LOG"
  exit 1
fi

# === MULTI-SIG APPROVAL (Optional) ===
read -p "🔐 Approve decryption (persona 1)? (yes/no): " APPROVE1
read -p "🔐 Approve decryption (persona 2)? (yes/no): " APPROVE2

if [[ "$APPROVE1" != "yes" || "$APPROVE2" != "yes" ]]; then
  echo "❌ Decryption denied: insufficient approvals"
  echo "$(date -Iseconds) | DENIED | $VAULT_ENCRYPTED | $PERSONA_ID | Multi-sig failed" >> "$AUDIT_LOG"
  exit 1
fi

# === DECRYPT VAULT ===
gpg --output "$VAULT_DECRYPTED" --decrypt "$VAULT_ENCRYPTED"
DECRYPT_EXIT=$?

if [[ $DECRYPT_EXIT -ne 0 ]]; then
  echo "❌ Decryption failed"
  echo "$(date -Iseconds) | FAILED | $VAULT_ENCRYPTED | $PERSONA_ID" >> "$AUDIT_LOG"
  exit 1
fi

# === HASH VERIFICATION ===
EXPECTED_HASH=$(jq -r --arg file "$VAULT_DECRYPTED" '.[$file].hash_prefix' "$HASH_INDEX")
ACTUAL_HASH=$(sha256sum "$VAULT_DECRYPTED" | awk '{print $1}')

if [[ "${ACTUAL_HASH:0:8}" != "$EXPECTED_HASH" ]]; then
  echo "⚠️ Hash mismatch detected for $VAULT_DECRYPTED"
  echo "$(date -Iseconds) | HASH_MISMATCH | $VAULT_DECRYPTED | $PERSONA_ID" >> "$AUDIT_LOG"
else
  echo "✅ Hash verified: $VAULT_DECRYPTED"
fi

# === LOG EVENT ===
echo "$(date -Iseconds) | SUCCESS | $VAULT_ENCRYPTED → $VAULT_DECRYPTED | $PERSONA_ID" >> "$AUDIT_LOG"
echo "🎯 Vault decrypted and logged successfully."
