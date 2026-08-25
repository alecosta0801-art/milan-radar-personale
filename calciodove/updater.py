"""Orchestratore dell'aggiornamento calendario, fonti e catalogo."""
from __future__ import annotations

import traceback
from pathlib import Path
from typing import Any

from .calendar import refresh_calendar, validate_calendar
from .catalog import build_catalog
from .sources import check_sources
from .util import atomic_write_json, iso_now, load_json


def run_update(root: Path, *, check_network_sources: bool = True) -> dict[str, Any]:
    root = root.resolve()
    report: dict[str, Any] = {
        "schemaVersion": 1,
        "startedAt": iso_now(),
        "finishedAt": None,
        "ok": False,
        "steps": {},
        "warnings": [],
    }

    try:
        try:
            calendar = refresh_calendar(root)
            report["steps"]["calendar"] = {"ok": True, "mode": "NETWORK", "count": calendar["count"], "updatedAt": calendar["updatedAt"]}
        except Exception as exc:
            calendar = load_json(root / "data" / "calendario.json")
            errors = validate_calendar(calendar.get("events") or [])
            if errors:
                raise RuntimeError("Aggiornamento calendario fallito e cache non valida: " + str(exc)) from exc
            report["steps"]["calendar"] = {"ok": True, "mode": "CACHE", "count": calendar.get("count"), "error": str(exc)}
            report["warnings"].append("Calendario di rete non raggiungibile: usata la cache valida.")

        if check_network_sources:
            source_state = check_sources(root, calendar)
            report["steps"]["sources"] = {"ok": True, **source_state.get("counts", {})}
        else:
            source_state = load_json(root / "data" / "stato-fonti.json", {"counts": {}})
            report["steps"]["sources"] = {"ok": True, "mode": "SKIPPED", **(source_state.get("counts") or {})}

        catalog = build_catalog(root)
        report["steps"]["catalog"] = {
            "ok": True,
            "assignments": len(catalog["assignments"]),
            "opportunities": len(catalog["opportunities"]),
            "territories": catalog["coverage"]["territoriesCompared"],
            "generatedAt": catalog["generatedAt"],
            "milanFixtures": catalog["milanRadar"]["counts"]["fixtures"],
            "milanBroadcasters": catalog["milanRadar"]["counts"]["broadcasters"],
            "milanExactObservations": catalog["milanRadar"]["counts"]["exactObservations"],
            "milanConfirmedFree": catalog["milanRadar"]["counts"]["confirmedFreeFullMatches"],
        }
        report["ok"] = True
    except Exception as exc:
        report["error"] = str(exc)
        report["trace"] = traceback.format_exc(limit=8)
    finally:
        report["finishedAt"] = iso_now()
        atomic_write_json(root / "data" / "ultimo-aggiornamento.json", report)
    return report
