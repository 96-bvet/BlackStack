#!/bin/bash
if [[ "$USER" != "blackhawk63" ]]; then
  echo "Access denied: unauthorized persona"
  exit 1
fi
echo "Access granted"
