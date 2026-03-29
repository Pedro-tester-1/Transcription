@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "APP_NAME=Media Converter"

echo Instalando %APP_NAME%...

:: 1. Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado.
    echo Descargalo desde https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

:: 2. Verificar ffmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ERROR: ffmpeg no encontrado.
    echo Descargalo desde https://ffmpeg.org/download.html
    echo y agregalo al PATH del sistema.
    pause
    exit /b 1
)

:: 3. Crear entorno virtual e instalar dependencias
echo Instalando dependencias Python...
python -m venv "%SCRIPT_DIR%.venv"
call "%SCRIPT_DIR%.venv\Scripts\activate.bat"
pip install --upgrade pip -q
pip install -r "%SCRIPT_DIR%requirements.txt" -q

:: 4. Crear acceso directo en el escritorio
echo Creando acceso directo...
set "SHORTCUT=%USERPROFILE%\Desktop\Media Converter.lnk"
set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\pythonw.exe"

powershell -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s = $ws.CreateShortcut('%SHORTCUT%'); ^
   $s.TargetPath = '%PYTHON_EXE%'; ^
   $s.Arguments = '%SCRIPT_DIR%main.py'; ^
   $s.WorkingDirectory = '%SCRIPT_DIR%'; ^
   $s.IconLocation = '%SCRIPT_DIR%icon.png'; ^
   $s.Save()"

echo.
echo Instalacion completada.
echo Puedes abrir '%APP_NAME%' desde el acceso directo en el escritorio.
pause
