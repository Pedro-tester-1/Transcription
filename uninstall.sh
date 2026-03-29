#!/bin/bash

DESKTOP_FILE="media-converter.desktop"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"

rm -f "$HOME/.local/share/applications/$DESKTOP_FILE"
rm -f "$DESKTOP_DIR/$DESKTOP_FILE"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo "Media Converter desinstalado."
