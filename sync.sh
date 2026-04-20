#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="./src/chronolight"
CODE_FILE="./board_code/code.py"

# Auto-detect CIRCUITPY mount (more reliable than hardcoding)
DEST=$(mount | awk '/CIRCUITPY/ {for (i=1;i<=NF;i++) if ($i == "on") print $(i+1)}')

if [ -z "$DEST" ]; then
    echo "CIRCUITPY not mounted"
    exit 1
fi

echo "Using CIRCUITPY at: $DEST"

echo "Syncing project files..."

# IMPORTANT: remove --delete (dangerous on CircuitPython)
rsync -av \
    --exclude "__pycache__/" \
    --exclude "*.pyc" \
    --exclude ".git/" \
    "$SRC_DIR" "$DEST/"

echo "Copying code.py (atomic replace)..."

# safer write pattern: write temp then move
TMP_FILE="$DEST/code.py.tmp"

cp "$CODE_FILE" "$TMP_FILE"
sync
mv "$TMP_FILE" "$DEST/code.py"
sync

echo "Done."