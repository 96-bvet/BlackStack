#!/bin/bash
echo "$1" > /tmp/infer.log
HASH=$(sha256sum /tmp/infer.log | awk '{print $1}')
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
cp /tmp/infer.log "/mnt/host_blackstack/logs/deepseek/$TIMESTAMP.$HASH.log"
