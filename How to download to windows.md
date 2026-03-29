# How to download to windows

## Requirements

Before installing, you need to have these two programs installed:

### 1. Python
- Go to https://www.python.org/downloads/
- Download the latest version
- Run the installer and **make sure to check "Add Python to PATH"** before clicking Install

### 2. ffmpeg
- Go to https://ffmpeg.org/download.html
- Under "Windows" click "Windows builds from gyan.dev"
- Download the `ffmpeg-release-essentials.zip`
- Extract it and copy the folder to `C:\ffmpeg`
- Open the Start menu, search "environment variables" and open it
- Click "Environment Variables" → under "System variables" find "Path" → Edit → New
- Add `C:\ffmpeg\bin` and click OK

---

## Installation

1. Go to https://github.com/Pedro-tester-1/Transcription
2. Click the green "Code" button → "Download ZIP"
3. Extract the ZIP wherever you want (example: `C:\Users\YourName\Transcription`)
4. Open the extracted folder and double click `install.bat`
5. Wait for it to finish — it will create a shortcut on your Desktop

---

## Running the app

Double click the "Media Converter" shortcut on your Desktop.

> The first time you use transcription, the app will download the Whisper model (~150 MB). This only happens once.
