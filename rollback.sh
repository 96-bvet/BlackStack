#!/bin/bash
MODULE="$1"
SNAPSHOT="$2"
cp "$SNAPSHOT" "$MODULE"
echo "[ROLLBACK] Restored $MODULE from $SNAPSHOT" >> /mnt/host_blackstack/logs/refactor/rollback.log
