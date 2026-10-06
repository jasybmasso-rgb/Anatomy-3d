#!/usr/bin/env bash
# Télécharge le template Blender Z-Anatomy (CC BY-SA 4.0). Ne copie pas le .blend dans git.
set -euo pipefail
DEST="${1:-/tmp/zanatomy}"
mkdir -p "$DEST"
ZIP="$DEST/Z-Anatomy.zip"
URL="https://github.com/Z-Anatomy/Models-of-human-anatomy/raw/refs/heads/master/Z-Anatomy.zip"
echo "Téléchargement $URL"
curl -L --fail --retry 3 -o "$ZIP" "$URL"
unzip -o "$ZIP" -d "$DEST"
echo "Blend : $DEST/Z-Anatomy/Startup.blend"
ls -lh "$DEST/Z-Anatomy/Startup.blend"
