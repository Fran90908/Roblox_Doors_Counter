@echo off
REM ====================================================================
REM  Compila DoorsCounter_windows.py a un solo .exe sin consola.
REM  Usar desde Windows, en cmd o PowerShell, dentro de la carpeta
REM  del proyecto.
REM ====================================================================

REM 1) Asegurar que pip esta al dia y las dependencias instaladas
python -m pip install --upgrade pip
python -m pip install -r requirements-windows.txt
python -m pip install pyinstaller

REM 2) Compilar
REM    --onefile     -> un solo .exe portable
REM    --windowed    -> sin ventana de consola al lanzarlo
REM    --name        -> nombre final del ejecutable
pyinstaller --onefile --windowed --name DoorsCounter DoorsCounter_windows.py

echo.
echo ============================================================
echo  Listo. El ejecutable esta en:  dist\DoorsCounter.exe
echo ============================================================
pause
