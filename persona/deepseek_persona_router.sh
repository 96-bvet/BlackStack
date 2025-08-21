#!/bin/bash
SCAN_OUTPUT=~/BlackStack/WachterEID/config/deepseek_scan_output.yaml
REGISTRY=~/BlackStack/WachterEID/config/persona_tool_registry.yaml

echo "🔄 Routing tools by persona..."
python3 ~/BlackStack/WachterEID/modules/deepseek_registry_builder.py

echo "✅ Persona registry updated: $REGISTRY"
