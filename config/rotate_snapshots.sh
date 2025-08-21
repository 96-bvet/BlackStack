#!/bin/bash

SRC="$HOME/snapshots/cai"
ARCHIVE="$HOME/snapshots/archive"
STAMP=$(date +"%Y-%m-%d_%H-%M-%S")
DEST="$ARCHIVE/$STAMP"

mkdir -p "$DEST"
cp -r "$SRC"/* "$DEST"
echo "📦 Snapshot archive created: $DEST"
