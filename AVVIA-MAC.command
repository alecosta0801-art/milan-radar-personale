#!/bin/bash
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
  python3 app.py
else
  echo "Python 3 non risulta installato."
  echo "Per l'avvio locale facoltativo installa Python 3.10 o successivo."
  echo "Sito ufficiale: https://www.python.org/downloads/"
  read -r -p "Premi Invio per chiudere…"
fi
