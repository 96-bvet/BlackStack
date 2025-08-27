#!/bin/bash

# WachterEID: decrypt_vault.sh
# Core decrypt logic for encrypted vaults

VAULT_ENCRYPTED="$1"
APPROVE1="$2"
APPROVE2="$3"

AUDIT_LOG="$HOME/BlackStack/WachterEID/logs/audit/decrypt.log"
VAULT_DECRYPTED="${VAULT_ENCRYPTED%.gpg}"

# === Validate Inputs ===
if [[ ! -f "$VAULT_ENCRYPTED" ]]; then
  echo "$(date -Iseconds) | ERROR | Vault not found: $VAULT_ENCRYPTED" >> "$AUDIT_LOG"
  exit 1
fi

if [[ "$APPROVE1" != "yes" || "$APPROVE2" != "yes" ]]; then
  echo "$(date -Iseconds) | ERROR | Approval mismatch | $VAULT_ENCRYPTED" >> "$AUDIT_LOG"
  exit 1
fi

# === Decrypt Vault ===
gpg --output "$VAULT_DECRYPTED" --decrypt "$VAULT_ENCRYPTED" 2>>"$AUDIT_LOG"

if [[ $? -ne 0 ]]; then
  echo "$(date -Iseconds) | ERROR | GPG failed | $VAULT_ENCRYPTED" >> "$AUDIT_LOG"
  exit 1
fi

echo "$(date -Iseconds) | DECRYPTED | $VAULT_DECRYPTED" >> "$AUDIT_LOG"
exit 0
