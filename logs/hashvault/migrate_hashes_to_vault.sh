#!/bin/bash

HASHVAULT="/home/blackhawk63/BlackStack/WachterEID/logs/hashvault"
LOGFILE="$HASHVAULT/migration.log"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

mkdir -p "$HASHVAULT"
echo "=== Hash Migration Log: $TIMESTAMP ===" >> "$LOGFILE"

SEARCH_ROOT="/home/blackhawk63/BlackStack/WachterEID"
EXCLUDE_DIR="$HASHVAULT"

# Match any file with 'hash' in its name, excluding the vault itself
find "$SEARCH_ROOT" -type f -iname "*hash*" ! -path "$EXCLUDE_DIR/*" | while read -r HASHFILE; do
    BASENAME=$(basename "$HASHFILE")
    DEST="$HASHVAULT/$BASENAME"

    # Rename if collision
    if [[ -e "$DEST" ]]; then
        DEST="$HASHVAULT/${BASENAME%.*}_$TIMESTAMP.${BASENAME##*.}"
    fi

    mv "$HASHFILE" "$DEST"
    echo "Moved: $HASHFILE → $DEST" >> "$LOGFILE"
done

echo "Migration complete. Log saved to $LOGFILE"
