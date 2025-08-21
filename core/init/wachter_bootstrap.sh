#!/bin/bash

# Redirect all output to log file
exec > >(tee -a /home/blackhawk63/BlackStack/WachterEID/logs/bootstrap_stdout.log) 2>&1
set -x

# Set environment and working directory
export HOME=/home/blackhawk63
cd /home/blackhawk63/BlackStack/WachterEID/core/init

# Define canonical paths
ROOT="/home/blackhawk63/BlackStack/WachterEID"
SERVICE_NAME="registry_ingest"
UNIT_PATH="$ROOT/systemd/$SERVICE_NAME.service"
LOG_PATH="$ROOT/logs/$SERVICE_NAME/hash_verification.log"
SYMLINK_PATH="/etc/systemd/system/$SERVICE_NAME.service"
HOOK_PATH="$ROOT/modules/approval_hooks/verify_unit_hash.sh"

# Begin bootstrap
echo "[WachterEID] Bootstrapping $SERVICE_NAME..."

# Run hash verification
bash "$HOOK_PATH" "$UNIT_PATH" "$LOG_PATH"
if [[ $? -ne 0 ]]; then
  echo "[✗] Hash verification failed. Aborting startup."
  exit 1
fi

# Optional: create symlink if not present
if [[ ! -f "$SYMLINK_PATH" ]]; then
  echo "[✓] Creating systemd symlink for $SERVICE_NAME..."
  sudo ln -s "$UNIT_PATH" "$SYMLINK_PATH"
fi

# Final confirmation
echo "[✓] Bootstrap completed successfully."
exit 0
