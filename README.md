# Media Converter

Aplicacion de escritorio para Linux que convierte archivos multimedia de forma sencilla.

## Funciones

- MP4 -> MP3
- MP4 -> Texto (transcripcion con Whisper)
- MP3 -> Texto (transcripcion con Whisper)

## Instalacion

```bash
git clone https://github.com/Pedro-tester-1/Transcription.git && cd Transcription && chmod +x install.sh && ./install.sh
```

El script instala `ffmpeg` si no lo tienes, crea el entorno virtual, instala las dependencias y crea un acceso directo en el escritorio y en el menu de aplicaciones de KDE.

> La primera vez que uses transcripcion, Whisper descargara el modelo (~150 MB).

## Desinstalar

```bash
./uninstall.sh
```

## Requisitos

- Python 3.10+
- Kubuntu / Ubuntu (cualquier distro con apt)

## Licencia

MIT
