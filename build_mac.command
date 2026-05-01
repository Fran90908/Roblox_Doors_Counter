#!/usr/bin/env bash
# ====================================================================
#  Compila DoorsCounter.py a un .app de macOS con PyInstaller.
#  Doble click en este archivo desde Finder, o ejecuta:
#      ./build_mac.command
#  desde Terminal dentro de la carpeta del proyecto.
# ====================================================================
set -e

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

if [ ! -d ".venv" ]; then
  echo "Creando entorno virtual…"
  "$PYTHON" -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements-mac.txt
python -m pip install pyinstaller

# --onefile     -> un único bundle
# --windowed    -> .app sin consola
# --name        -> nombre del bundle
# --osx-bundle-identifier -> id único para macOS
pyinstaller \
  --onefile \
  --windowed \
  --name DoorsCounter \
  --osx-bundle-identifier org.beachlab.doorscounter \
  DoorsCounter.py

echo
echo "============================================================"
echo " Listo. La app está en:  dist/DoorsCounter.app"
echo " Para distribuirla, comprime:  cd dist && zip -r DoorsCounter-macos.zip DoorsCounter.app"
echo "============================================================"
