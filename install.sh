#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Media Converter"
DESKTOP_FILE="media-converter.desktop"

echo "Instalando $APP_NAME..."

# 1. Verificar dependencias del sistema
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python3 no encontrado. Instala con: sudo apt install python3"
    exit 1
fi

if ! command -v ffmpeg &>/dev/null; then
    echo "ffmpeg no encontrado. Instalando..."
    sudo apt install -y ffmpeg
fi

# 2. Crear entorno virtual e instalar dependencias Python
echo "Instalando dependencias Python..."
python3 -m venv "$SCRIPT_DIR/.venv"
"$SCRIPT_DIR/.venv/bin/pip" install --upgrade pip -q
"$SCRIPT_DIR/.venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" -q

# 3. Crear el archivo .desktop
DESKTOP_CONTENT="[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Comment=Convierte MP4 a MP3 o texto
Exec=$SCRIPT_DIR/.venv/bin/python $SCRIPT_DIR/main.py
Icon=$SCRIPT_DIR/icon.png
Terminal=false
Categories=AudioVideo;Utility;
StartupWMClass=media-converter"

# Instalar en el menu de aplicaciones
mkdir -p "$HOME/.local/share/applications"
echo "$DESKTOP_CONTENT" > "$HOME/.local/share/applications/$DESKTOP_FILE"

# Instalar en el escritorio
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
if [ -d "$DESKTOP_DIR" ]; then
    echo "$DESKTOP_CONTENT" > "$DESKTOP_DIR/$DESKTOP_FILE"
    chmod +x "$DESKTOP_DIR/$DESKTOP_FILE"
    # KDE: marcar como de confianza
    gio set "$DESKTOP_DIR/$DESKTOP_FILE" metadata::trusted true 2>/dev/null || true
fi

# Actualizar base de datos de aplicaciones
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo ""
echo "Instalacion completada."
echo "Puedes abrir '$APP_NAME' desde el escritorio o el menu de aplicaciones."
