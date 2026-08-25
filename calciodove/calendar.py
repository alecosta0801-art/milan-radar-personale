"""Aggiornamento prudente del calendario Serie A da ESPN."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from .util import atomic_write_json, iso_now, load_json

ESPN_URL = (
    "https://site.web.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard"
    "?dates=20260801-20270601&limit=500"
)


def _number(value: Any) -> int | float | None:
    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except (TypeError, ValueError):
        return None


def _team(competitor: dict[str, Any]) -> dict[str, Any]:
    team = competitor.get("team") or {}
    color = str(team.get("color") or "26364c").lstrip("#")
    alt = str(team.get("alternateColor") or "ffffff").lstrip("#")
    if len(color) != 6:
        color = "26364c"
    if len(alt) != 6:
        alt = "ffffff"
    return {
        "name": team.get("shortDisplayName") or team.get("displayName") or "—",
        "fullName": team.get("displayName") or team.get("shortDisplayName") or "—",
        "short": team.get("abbreviation") or "—",
        "color": f"#{color}",
        "alternateColor": f"#{alt}",
    }


def normalize_feed(raw: dict[str, Any], round_map: dict[str, int]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for source_event in raw.get("events") or []:
        competition = (source_event.get("competitions") or [{}])[0]
        competitors = competition.get("competitors") or []
        home = next((x for x in competitors if x.get("homeAway") == "home"), {})
        away = next((x for x in competitors if x.get("homeAway") == "away"), {})
        status_type = (competition.get("status") or {}).get("type") or (source_event.get("status") or {}).get("type") or {}
        state = status_type.get("state") or "pre"
        status = "LIVE" if state == "in" else "FINISHED" if status_type.get("completed") or state == "post" else "SCHEDULED"
        if "postpon" in str(status_type.get("description") or "").casefold():
            status = "POSTPONED"
        event_id = str(source_event.get("id") or "")
        broadcasts: list[str] = []
        for item in competition.get("geoBroadcasts") or []:
            name = ((item.get("media") or {}).get("shortName") or "").strip()
            if name and name not in broadcasts:
                broadcasts.append(name)
        if not broadcasts:
            for group in competition.get("broadcasts") or []:
                for name in group.get("names") or []:
                    if name and name not in broadcasts:
                        broadcasts.append(name)
        events.append(
            {
                "id": event_id,
                "round": round_map.get(event_id),
                "date": source_event.get("date") or competition.get("date"),
                "status": status,
                "statusText": status_type.get("shortDetail") or status_type.get("description") or "",
                "home": _team(home),
                "away": _team(away),
                "homeScore": _number(home.get("score")),
                "awayScore": _number(away.get("score")),
                "providerHints": broadcasts,
            }
        )
    events.sort(key=lambda event: (event.get("date") or "", event["id"]))
    for index, event in enumerate(events):
        if not event["round"]:
            event["round"] = index // 10 + 1
    return events


def validate_calendar(events: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids = [event.get("id") for event in events]
    if len(events) != 380:
        errors.append(f"Attese 380 partite, trovate {len(events)}")
    if len(set(ids)) != len(ids):
        errors.append("ID partita duplicati")
    rounds = {round_number: 0 for round_number in range(1, 39)}
    for event in events:
        round_number = event.get("round")
        if round_number not in rounds:
            errors.append(f"Giornata non valida per {event.get('id')}")
        else:
            rounds[round_number] += 1
        if not event.get("date") or not event.get("home") or not event.get("away"):
            errors.append(f"Partita incompleta: {event.get('id')}")
    for round_number, count in rounds.items():
        if count != 10:
            errors.append(f"Giornata {round_number}: {count} partite invece di 10")
    return errors


def refresh_calendar(root: Path, timeout: int = 30) -> dict[str, Any]:
    round_data = load_json(root / "data" / "round-map.json")
    round_map = {
        str(event_id): round_number
        for round_number, ids in enumerate(round_data["rounds"], start=1)
        for event_id in ids
    }
    request = Request(
        ESPN_URL,
        headers={"User-Agent": "MilanRadar/4.1 (personal legal broadcast catalogue)", "Accept": "application/json"},
    )
    with urlopen(request, timeout=timeout) as response:
        raw = json.load(response)
    events = normalize_feed(raw, round_map)
    errors = validate_calendar(events)
    if errors:
        raise ValueError("; ".join(errors[:8]))
    result = {
        "schemaVersion": 1,
        "season": "2026-27",
        "source": {"name": "ESPN scoreboard feed", "url": ESPN_URL},
        "updatedAt": iso_now(),
        "count": len(events),
        "events": events,
    }
    atomic_write_json(root / "data" / "calendario.json", result)
    return result
