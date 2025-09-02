#!/bin/bash
PROMPT="$1"
echo "$PROMPT" | /opt/deepseek/main \
  -m /opt/deepseek/deepseek-coder-6.7b-instruct.Q4_K_M.gguf \
  --ctx-size 8192 --prompt-file /dev/stdin --log-disable
