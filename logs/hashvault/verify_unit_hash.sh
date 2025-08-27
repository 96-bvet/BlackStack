#!/bin/bash
UNIT_PATH="WachterEID/systemd/registry_ingest.service"
LOG_PATH="WachterEID/logs/registry_ingest/hash_verification.log"

mkdir -p "$(dirname "$LOG_PATH")"
sha256sum "$UNIT_PATH" >> "$LOG_PATH"
echo "[✓] Hash logged for $UNIT_PATH at $(date)"
