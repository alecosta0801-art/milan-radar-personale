@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Milan Radar — server locale

if not exist "app.py" (
  echo.
  echo ERRORE: app.py non è stato trovato.
  echo Estrai tutto lo ZIP in una cartella normale e riprova.
  echo.
  pause
  exit /b 1
)

py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if not errorlevel 1 goto avvia_py

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if not errorlevel 1 goto avvia_python

echo.
echo Python 3.10 o successivo non risulta disponibile.
echo Per l'uso su iPhone con GitHub Pages Python NON serve sul PC.
echo Per usare anche la versione locale, installalo da:
echo https://www.python.org/downloads/
echo Durante l'installazione seleziona "Add Python to PATH".
echo.
pause
exit /b 1

:avvia_py
py -3 app.py
goto controlla_esito

:avvia_python
python app.py

:controlla_esito
if errorlevel 1 (
  echo.
  echo Milan Radar non si è avviato correttamente.
  echo Chiudi eventuali vecchie finestre Milan Radar e riprova.
  echo Se l'errore resta, conserva il messaggio mostrato qui sopra.
  echo.
  pause
  exit /b 1
)
endlocal
