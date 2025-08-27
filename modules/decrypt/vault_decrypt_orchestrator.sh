#!/bin/bash

# WachterEID: vault_decrypt_orchestrator.sh
# GUI + persona-aware decrypt orchestrator

# === CONFIG ===
VAULT_DIR="$HOME/BlackStack/WachterEID/logs/hashvault"
REGISTRY_DIR="$HOME/BlackStack/WachterEID/registry"
AUDIT_LOG="$HOME/BlackStack/WachterEID/logs/audit/decrypt.log"
APPROVAL_LIST="$REGISTRY_DIR/personas/approved.list"
DECRYPT_SCRIPT="$HOME/BlackStack/WachterEID/modules/decrypt/decrypt_vault.sh"
REGISTRY_UPDATE="$HOME/BlackStack/WachterEID/modules/decrypt/register_decrypted_vault.sh"
SNAPSHOT_DIR="$HOME/BlackStack/WachterEID/snapshots/decrypt"

# === GUI: Select Vault ===
VAULT_ENCRYPTED=$(zenity --file-selection --title="Select Encrypted Vault (.gpg)" --filename="$VAULT_DIR/")
[[ -z "$VAULT_ENCRYPTED" ]] && zenity --error --text="No file selected. Aborting." && exit 1

# === Persona Resolution ===
PERSONA_ID=$(whoami)
if ! grep -q "$PERSONA_ID" "$APPROVAL_LIST"; then
  zenity --error --text="Persona $PERSONA_ID not approved for decryption."
  echo "$(date -Iseconds) | DENIED | $VAULT_ENCRYPTED | $PERSONA_ID" >> "$AUDIT_LOG"
  exit 1
fi

# === GUI Approval Prompts ===
zenity --question --text="Approve decryption (persona 1)?"
APPROVE1=$([[ $? -eq 0 ]] && echo "yes" || echo "no")

zenity --question --text="Approve decryption (persona 2)?"
APPROVE2=$([[ $? -eq 0 ]] && echo "yes" || echo "no")

if [[ "$APPROVE1" != "yes" || "$APPROVE2" != "yes" ]]; then
  zenity --error --text="Decryption denied: insufficient approvals."
  echo "$(date -Iseconds) | DENIED | $VAULT_ENCRYPTED | $PERSONA_ID | Multi-sig failed" >> "$AUDIT_LOG"
  exit 1
fi

# === Run Decrypt Logic ===
bash "$DECRYPT_SCRIPT" "$VAULT_ENCRYPTED" "$APPROVE1" "$APPROVE2"

# === Registry Update ===
VAULT_DECRYPTED="${VAULT_ENCRYPTED%.gpg}"
bash "$REGISTRY_UPDATE" "$VAULT_DECRYPTED"

# === Embed Hash Lineage ===
EMBED_SCRIPT="$HOME/BlackStack/WachterEID/modules/decrypt/embed_hash_log.sh"
bash "$EMBED_SCRIPT" "$VAULT_DECRYPTED"


# === Snapshot Sync ===
mkdir -p "$SNAPSHOT_DIR"
cp "$VAULT_DECRYPTED" "$SNAPSHOT_DIR/$(basename "$VAULT_DECRYPTED")-$(date +%Y%m%d%H%M%S)"

# === Final Message ===
zenity --info --text="Vault decrypted and registered successfully."
echo "$(date -Iseconds) | SUCCESS | $VAULT_DECRYPTED | $PERSONA_ID" >> "$AUDIT_LOG"
