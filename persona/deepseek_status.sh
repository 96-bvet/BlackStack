#!/bin/bash
echo "🔍 DeepSeek Status Check"
SCAN=~/BlackStack/WachterEID/config/deepseek_scan_output.yaml
REGISTRY=~/BlackStack/WachterEID/config/persona_tool_registry.yaml

echo "📦 Scanned tools:"
grep "id:" $SCAN

echo "📁 Registry entries:"
grep "id:" $REGISTRY

echo "✅ Status check complete"
