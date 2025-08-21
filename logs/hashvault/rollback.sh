#!/bin/bash
LINES=$(wc -l < ~/WachterEID/logs/hashvault/vault.db)
ROLLBACK_LINES=$((LINES - 1))
head -n "$ROLLBACK_LINES" ~/WachterEID/logs/hashvault/vault.db > ~/WachterEID/logs/hashvault/vault.db.tmp
mv ~/WachterEID/logs/hashvault/vault.db.tmp ~/WachterEID/logs/hashvault/vault.db
echo "Last hash ingest rolled back"
