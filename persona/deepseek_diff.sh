#!/bin/bash
OLD=$1
NEW=$2

echo "🔍 Comparing DeepSeek snapshots..."
diff -u "$OLD" "$NEW" > ~/BlackStack/WachterEID/logs/deepseek_diff.log

echo "✅ Diff saved to logs/deepseek_diff.log"
