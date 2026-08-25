#!/usr/bin/env python3
"""Aggiorna i dati da terminale o GitHub Actions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from calciodove.updater import run_update  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--skip-sources", action="store_true", help="Non interroga le fonti TV; utile nei test offline")
args = parser.parse_args()
report = run_update(ROOT, check_network_sources=not args.skip_sources)
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report["ok"] else 1)
