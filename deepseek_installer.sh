#!/bin/bash

# === Config ===
DEEPSEEK_PATH="~/BlackStack/WachterEID/DeepSeek/run_deepseek.py"
EXPECTED_HASH="79d923f7ce818bf7f64a69397a9819608095ff8e2cc57ce365b9b1f2e8297263"
LOGFILE="/var/log/deepseek_install.log"
PERSONA_FILE="~/BlackStack/WachterEID/persona/active.txt"

echo "[*] DeepSeek Installer Starting..." | tee -a "$LOGFILE"

# === Verify DeepSeek Presence ===
if [ ! -f "$DEEPSEEK_PATH" ]; then
    echo "[!] DeepSeek script not found at $DEEPSEEK_PATH" | tee -a "$LOGFILE"
    exit 1
fi

# === Hash Check ===
CURRENT_HASH=$(sha256sum "$DEEPSEEK_PATH" | awk '{print $1}')
if [ "$CURRENT_HASH" != "$EXPECTED_HASH" ]; then
    echo "[!] Hash mismatch. Aborting install." | tee -a "$LOGFILE"
    exit 1
fi

# === Persona Routing ===
if [ ! -f "$PERSONA_FILE" ]; then
    echo "[!] Persona file missing. Aborting." | tee -a "$LOGFILE"
    exit 1
fi

ACTIVE_PERSONA=$(cat "$PERSONA_FILE")
echo "[*] Active persona: $ACTIVE_PERSONA" | tee -a "$LOGFILE"

# === Trigger Python Install Logic ===
python3 "$DEEPSEEK_PATH" --install "$ACTIVE_PERSONA"
echo "[✓] DeepSeek install triggered for persona: $ACTIVE_PERSONA" | tee -a "$LOGFILE"
