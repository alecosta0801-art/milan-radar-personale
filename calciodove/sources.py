"""Controllo tecnico delle fonti e creazione di una coda prudente di revisione.

Una variazione o una menzione non diventa mai automaticamente una conferma.
Le conferme automatiche sono ammesse solo per futuri adattatori strutturati che
forniscano partita, territorio e gratuità in campi non ambigui.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .util import atomic_write_json, iso_now, load_json, normalized, plain_text, sha256_bytes

TEAM_ALIASES = {
    "internazionale": ["internazionale", "inter", "inter milan"],
    "milan": ["ac milan", "milan"],
    "hellas verona": ["hellas verona", "verona"],
    "juventus": ["juventus", "juve"],
    "atalanta": ["atalanta"],
    "sassuolo": ["sassuolo"],
    "napoli": ["napoli"],
    "roma": ["as roma", "roma"],
    "lazio": ["lazio"],
    "fiorentina": ["fiorentina"],
    "bologna": ["bologna"],
    "torino": ["torino"],
    "genoa": ["genoa"],
    "udinese": ["udinese"],
    "como": ["como 1907", "como"],
    "cagliari": ["cagliari"],
    "parma": ["parma"],
    "lecce": ["lecce"],
    "monza": ["monza"],
    "cremonese": ["cremonese"],
    "pisa": ["pisa"],
    "sampdoria": ["sampdoria"],
    "palermo": ["palermo"],
}


def _aliases(team_name: str) -> list[str]:
    key = normalized(team_name)
    return TEAM_ALIASES.get(key, [key])


def _positions(text: str, aliases: list[str]) -> list[int]:
    found: list[int] = []
    for alias in aliases:
        if len(alias) < 4:
            continue
        found.extend(match.start() for match in re.finditer(rf"\b{re.escape(alias)}\b", text))
    return sorted(found)


def detect_candidates(source: dict[str, Any], text: str, calendar: dict[str, Any]) -> list[dict[str, Any]]:
    if not source.get("scanMatches"):
        return []
    clean = normalized(text)
    required = [normalized(value) for value in source.get("requiredMarkers") or []]
    if required and not any(marker in clean for marker in required):
        return []
    now = datetime.now(timezone.utc)
    future_limit = now + timedelta(days=int(source.get("scanDays", 21)))
    candidates: list[dict[str, Any]] = []
    for event in calendar.get("events") or []:
        try:
            event_date = datetime.fromisoformat(str(event["date"]).replace("Z", "+00:00"))
        except (ValueError, TypeError, KeyError):
            continue
        if event_date < now - timedelta(days=2) or event_date > future_limit:
            continue
        home_positions = _positions(clean, _aliases(event["home"]["name"]))
        away_positions = _positions(clean, _aliases(event["away"]["name"]))
        pairs = [(abs(a - b), a, b) for a in home_positions for b in away_positions]
        distance, home_at, away_at = min(pairs, default=(10_000, 0, 0))
        if distance > int(source.get("pairWindow", 220)):
            continue
        start = max(0, min(home_at, away_at) - 140)
        end = min(len(clean), max(home_at, away_at) + 220)
        excerpt = clean[start:end]
        media_signals = []
        markers = {
            "LIVE": (" live ", "diretta", "direct", "in direct"),
            "HIGHLIGHTS": ("highlight", "rezumat", "résumé", "resumen"),
            "PAID_PLATFORM": ("paramount+", "abonat", "subscriber", "subscription"),
            "TEXT_SCORE": ("risultato", "score", "actions", "commentaires"),
        }
        for signal, words in markers.items():
            if any(word in f" {excerpt} " for word in words):
                media_signals.append(signal)
        is_milan = "Milan" in {event["home"]["name"], event["away"]["name"]}
        prefix = "PRIORITÀ MILAN. " if is_milan else ""
        candidates.append(
            {
                "id": f"auto-{source['id']}-{event['id']}",
                "state": "REVIEW",
                "eventId": event["id"],
                "priorityTeam": "AC Milan" if is_milan else None,
                "territories": source.get("territories") or [],
                "broadcaster": source.get("name"),
                "sourceId": source["id"],
                "sourceUrl": source["url"],
                "detectedAt": iso_now(),
                "mediaSignals": media_signals,
                "reason": prefix + "Le due squadre compaiono vicine nella fonte monitorata; diretta integrale, gratuità, data, territorio e canale richiedono verifica editoriale.",
                "automaticConfirmation": False,
            }
        )
        if len(candidates) >= int(source.get("candidateLimit", 30)):
            break
    return candidates


def check_sources(root: Path, calendar: dict[str, Any], timeout: int = 18) -> dict[str, Any]:
    registry = load_json(root / "config" / "fonti.json")
    previous_document = load_json(root / "data" / "stato-fonti.json", {"sources": []})
    previous = {item.get("id"): item for item in previous_document.get("sources") or []}
    statuses: list[dict[str, Any]] = []
    all_candidates: list[dict[str, Any]] = []

    for source in registry.get("sources") or []:
        old = previous.get(source["id"], {})
        base = {
            "id": source["id"],
            "name": source["name"],
            "territories": source.get("territories") or [],
            "url": source["url"],
            "official": bool(source.get("official")),
            "role": source.get("role") or "monitoraggio",
            "automation": source.get("automation") or "HEALTH_ONLY",
            "priorityMilan": bool(source.get("priorityMilan")),
            "checkedAt": iso_now(),
            "lastSuccessAt": old.get("lastSuccessAt"),
            "contentHash": old.get("contentHash"),
            "contentChanged": False,
            "note": source.get("note") or "",
        }
        if not source.get("enabled", True):
            base.update(
                status="LIMITED",
                checkedAt=None,
                error=source.get("disabledReason") or "Controllo automatico disattivato.",
            )
            statuses.append(base)
            continue
        try:
            request = Request(
                source["url"],
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; MilanRadarSourceMonitor/4.1; personal research)",
                    "Accept": "text/html,application/json;q=0.9,*/*;q=0.5",
                    "Accept-Encoding": "identity",
                },
            )
            with urlopen(request, timeout=timeout) as response:
                body = response.read(int(source.get("maxBytes", 2_000_000)) + 1)
                if len(body) > int(source.get("maxBytes", 2_000_000)):
                    body = body[: int(source.get("maxBytes", 2_000_000))]
                status_code = getattr(response, "status", 200)
                content_type = response.headers.get("Content-Type", "")
            decoded = body.decode("utf-8", errors="replace")
            readable_text = plain_text(decoded)
            # L'hash del testo visibile riduce falsi cambiamenti dovuti a token,
            # script pubblicitari e attributi HTML generati dinamicamente.
            digest = sha256_bytes(normalized(readable_text).encode("utf-8"))
            changed = bool(old.get("contentHash") and old.get("contentHash") != digest)
            base.update(
                status="CHANGED" if changed else "OK",
                httpStatus=status_code,
                contentType=content_type,
                contentHash=digest,
                contentChanged=changed,
                lastSuccessAt=iso_now(),
                error=None,
            )
            all_candidates.extend(detect_candidates(source, readable_text, calendar))
        except HTTPError as exc:
            base.update(status="BLOCKED" if exc.code in {401, 403, 429} else "ERROR", httpStatus=exc.code, error=f"HTTP {exc.code}")
        except (URLError, TimeoutError, OSError) as exc:
            base.update(status="ERROR", httpStatus=None, error=str(exc.reason if isinstance(exc, URLError) else exc)[:180])
        statuses.append(base)

    unique_candidates: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in all_candidates:
        unique_candidates[(candidate["sourceId"], candidate["eventId"])] = candidate
    queue = {
        "schemaVersion": 1,
        "generatedAt": iso_now(),
        "policy": "REVIEW_ONLY",
        "note": "Questi elementi non sono conferme e non appaiono tra le dirette gratuite finché non vengono revisionati.",
        "candidates": sorted(
            unique_candidates.values(),
            key=lambda item: (item.get("priorityTeam") != "AC Milan", item.get("eventId") or "", item.get("sourceId") or ""),
        ),
    }
    result = {
        "schemaVersion": 1,
        "generatedAt": iso_now(),
        "counts": {
            "total": len(statuses),
            "ok": sum(item["status"] in {"OK", "CHANGED"} for item in statuses),
            "limited": sum(item["status"] in {"LIMITED", "BLOCKED"} for item in statuses),
            "errors": sum(item["status"] == "ERROR" for item in statuses),
            "changed": sum(bool(item.get("contentChanged")) for item in statuses),
        },
        "sources": statuses,
    }
    atomic_write_json(root / "data" / "stato-fonti.json", result)
    atomic_write_json(root / "data" / "coda-revisione.json", queue)
    return result
