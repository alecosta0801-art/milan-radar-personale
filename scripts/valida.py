#!/usr/bin/env python3
"""Valida calendario e catalogo senza usare la rete."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from calciodove.calendar import validate_calendar  # noqa: E402
from calciodove.catalog import validate_catalog  # noqa: E402
from calciodove.util import load_json  # noqa: E402

calendar = load_json(ROOT / "data" / "calendario.json")
catalog = load_json(ROOT / "data" / "catalogo-tv.json")
countries = set(load_json(ROOT / "config" / "countries.json")["codes"])
events = calendar.get("events") or []
errors = validate_calendar(events)
errors += validate_catalog(catalog, countries, {str(event["id"]) for event in events})
if errors:
    print("VALIDAZIONE FALLITA")
    for error in errors:
        print("-", error)
    raise SystemExit(1)
radar = catalog["milanRadar"]
print(
    f"VALIDO: {len(events)} partite, {len(countries)} territori, "
    f"{len(radar['fixtures'])} gare Milan, {len(radar['broadcasters'])} emittenti prioritarie, "
    f"{len(radar['observations'])} verifiche Milan puntuali"
)
