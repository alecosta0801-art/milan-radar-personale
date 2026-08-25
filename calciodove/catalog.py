"""Costruzione e validazione del catalogo TV pubblico."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .util import atomic_write_json, iso_now, load_json, valid_web_url

REQUIRED_ASSIGNMENT_FIELDS = {
    "id",
    "eventId",
    "territories",
    "broadcaster",
    "watchUrl",
    "sourceUrl",
    "access",
    "restriction",
    "verification",
}

FOCUS_BROADCASTERS = {
    "rsi-la2",
    "digi-sport-ro",
    "bbc-iplayer",
    "itvx",
    "cbs-golazo",
    "rtbf-auvio",
}
FOCUS_STATES = {
    "CONFIRMED_FREE",
    "CONFIRMED_NOT_FREE",
    "PROBABLE_NOT_FREE",
    "POSSIBLE_NOT_CONFIRMED",
    "NOT_CONFIRMED",
    "NO_EVIDENCE",
    "HIGHLIGHTS_ONLY",
    "TEXT_SCORE_ONLY",
}


def _freshness(assignment: dict[str, Any], event: dict[str, Any] | None) -> str:
    checked = str((assignment.get("verification") or {}).get("checkedAt") or "")
    try:
        checked_date = datetime.fromisoformat(checked.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - checked_date).days
    except ValueError:
        return "UNKNOWN"
    if event and event.get("status") == "FINISHED":
        return "HISTORICAL"
    return "CURRENT" if age <= 14 else "RECHECK"


def validate_catalog(catalog: dict[str, Any], country_codes: set[str], event_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if catalog.get("schemaVersion") != 3:
        errors.append("schemaVersion deve essere 3")
    if catalog.get("coverage", {}).get("territoriesCompared") != 249:
        errors.append("La copertura deve contenere 249 Paesi e territori")
    radar = catalog.get("milanRadar") or {}
    broadcasters = radar.get("broadcasters") or []
    if {item.get("id") for item in broadcasters} != FOCUS_BROADCASTERS:
        errors.append("Milan Radar deve contenere esattamente i sei broadcaster prioritari")
    registered_sources = {item.get("id") for item in catalog.get("sources") or []}
    for broadcaster in broadcasters:
        if broadcaster.get("territory") not in country_codes:
            errors.append(f"Profilo Milan con territorio non valido: {broadcaster.get('id')}")
        if broadcaster.get("baselineState") not in FOCUS_STATES:
            errors.append(f"Profilo Milan con stato non valido: {broadcaster.get('id')}")
        if not valid_web_url(str(broadcaster.get("watchUrl") or "")):
            errors.append(f"Profilo Milan senza watchUrl valido: {broadcaster.get('id')}")
        if not set(broadcaster.get("sourceIds") or []).issubset(registered_sources):
            errors.append(f"Profilo Milan con fonti non presenti nel monitor: {broadcaster.get('id')}")
    fixtures = radar.get("fixtures") or []
    if len(fixtures) != 38:
        errors.append("Milan Radar deve contenere le 38 partite di Serie A del Milan")
    fixture_ids = [str(item.get("eventId") or "") for item in fixtures]
    if len(set(fixture_ids)) != len(fixture_ids) or any(event_id not in event_ids for event_id in fixture_ids):
        errors.append("Le fixture Milan devono essere uniche e presenti nel calendario")
    observation_keys: set[tuple[str, str]] = set()
    for observation in radar.get("observations") or []:
        key = (str(observation.get("eventId") or ""), str(observation.get("broadcasterId") or ""))
        if key in observation_keys:
            errors.append(f"Osservazione Milan duplicata: {key[0]} / {key[1]}")
        observation_keys.add(key)
        if key[0] not in set(fixture_ids) or key[1] not in FOCUS_BROADCASTERS:
            errors.append(f"Osservazione Milan fuori ambito: {key[0]} / {key[1]}")
        if observation.get("state") not in FOCUS_STATES:
            errors.append(f"Osservazione Milan con stato non valido: {observation.get('id')}")
        if not valid_web_url(str(observation.get("sourceUrl") or "")):
            errors.append(f"Osservazione Milan senza fonte valida: {observation.get('id')}")
        if observation.get("countsAsFreeFullMatch") and observation.get("state") != "CONFIRMED_FREE":
            errors.append(f"Osservazione Milan conteggiata gratis senza CONFIRMED_FREE: {observation.get('id')}")
    seen: set[str] = set()
    for index, assignment in enumerate(catalog.get("assignments") or []):
        missing = REQUIRED_ASSIGNMENT_FIELDS - set(assignment)
        if missing:
            errors.append(f"Assegnazione {index}: campi mancanti {sorted(missing)}")
        assignment_id = str(assignment.get("id") or "")
        if assignment_id in seen:
            errors.append(f"ID assegnazione duplicato: {assignment_id}")
        seen.add(assignment_id)
        if str(assignment.get("eventId")) not in event_ids:
            errors.append(f"{assignment_id}: eventId non presente nel calendario")
        territories = assignment.get("territories") or []
        if not territories or any(code not in country_codes for code in territories):
            errors.append(f"{assignment_id}: territorio non valido")
        for field in ("watchUrl", "sourceUrl"):
            if not valid_web_url(str(assignment.get(field) or "")):
                errors.append(f"{assignment_id}: {field} non valido")
        rights_url = assignment.get("rightsUrl")
        if rights_url and not valid_web_url(str(rights_url)):
            errors.append(f"{assignment_id}: rightsUrl non valido")
        if (assignment.get("verification") or {}).get("status") != "CONFIRMED":
            errors.append(f"{assignment_id}: una pubblicazione puntuale deve essere CONFIRMED")
    for opportunity in catalog.get("opportunities") or []:
        territories = opportunity.get("territories") or []
        if not territories or any(code not in country_codes for code in territories):
            errors.append(f"Opportunità {opportunity.get('id')}: territorio non valido")
        if opportunity.get("eventId"):
            errors.append(f"Opportunità {opportunity.get('id')}: non deve fingere un eventId")
    return errors


def _build_milan_radar(root: Path, calendar: dict[str, Any]) -> dict[str, Any]:
    """Unisce profili editoriali e calendario senza trasformare indizi in dirette."""
    editorial = load_json(root / "editorial" / "milan-radar.json")
    focus_name = str((editorial.get("team") or {}).get("calendarName") or "Milan")
    fixtures = [
        {
            "eventId": str(event["id"]),
            "round": event.get("round"),
            "date": event.get("date"),
            "status": event.get("status"),
            "home": event.get("home", {}).get("name"),
            "away": event.get("away", {}).get("name"),
        }
        for event in calendar.get("events") or []
        if focus_name in {event.get("home", {}).get("name"), event.get("away", {}).get("name")}
    ]
    fixture_ids = {item["eventId"] for item in fixtures}
    broadcaster_ids = {item.get("id") for item in editorial.get("broadcasters") or []}
    errors: list[str] = []
    if len(fixtures) != 38:
        errors.append(f"Il calendario Milan deve contenere 38 partite, trovate {len(fixtures)}")
    if broadcaster_ids != FOCUS_BROADCASTERS:
        errors.append("I sei broadcaster prioritari Milan non corrispondono alla configurazione obbligatoria")
    for broadcaster in editorial.get("broadcasters") or []:
        if broadcaster.get("baselineState") not in FOCUS_STATES:
            errors.append(f"Profilo {broadcaster.get('id')}: baselineState non valido")
        if not valid_web_url(str(broadcaster.get("watchUrl") or "")):
            errors.append(f"Profilo {broadcaster.get('id')}: watchUrl non valido")
        if not broadcaster.get("sourceIds"):
            errors.append(f"Profilo {broadcaster.get('id')}: nessuna fonte monitorata")
    for observation in editorial.get("observations") or []:
        label = observation.get("id") or "osservazione"
        if str(observation.get("eventId")) not in fixture_ids:
            errors.append(f"{label}: la partita non è del Milan")
        if observation.get("broadcasterId") not in FOCUS_BROADCASTERS:
            errors.append(f"{label}: broadcaster non prioritario")
        if observation.get("state") not in FOCUS_STATES:
            errors.append(f"{label}: stato non valido")
        if not valid_web_url(str(observation.get("sourceUrl") or "")):
            errors.append(f"{label}: sourceUrl non valido")
        if observation.get("countsAsFreeFullMatch") and observation.get("state") != "CONFIRMED_FREE":
            errors.append(f"{label}: soltanto CONFIRMED_FREE può contare come diretta gratuita")
        if observation.get("state") in {"HIGHLIGHTS_ONLY", "TEXT_SCORE_ONLY"} and observation.get("countsAsFreeFullMatch"):
            errors.append(f"{label}: highlights/score non possono contare come partita integrale")
    if errors:
        raise ValueError("Milan Radar non valido:\n- " + "\n- ".join(errors))
    result = dict(editorial)
    result["fixtures"] = sorted(fixtures, key=lambda item: item.get("date") or "")
    result["counts"] = {
        "fixtures": len(fixtures),
        "broadcasters": len(broadcaster_ids),
        "exactObservations": len(editorial.get("observations") or []),
        "confirmedFreeFullMatches": sum(bool(item.get("countsAsFreeFullMatch")) for item in editorial.get("observations") or []),
    }
    return result


def build_catalog(root: Path) -> dict[str, Any]:
    editorial = load_json(root / "editorial" / "catalogo-editoriale.json")
    calendar = load_json(root / "data" / "calendario.json")
    countries = load_json(root / "config" / "countries.json")
    source_state = load_json(root / "data" / "stato-fonti.json", {"counts": {}, "sources": []})
    queue = load_json(root / "data" / "coda-revisione.json", {"candidates": []})
    event_by_id = {str(event["id"]): event for event in calendar.get("events") or []}
    codes = list(countries["codes"])

    assignments: list[dict[str, Any]] = []
    for assignment in editorial.get("assignments") or []:
        item = dict(assignment)
        item["freshness"] = _freshness(item, event_by_id.get(str(item.get("eventId"))))
        assignments.append(item)

    opportunities = list(editorial.get("opportunities") or [])
    reviews = list(editorial.get("reviews") or [])
    automated_candidates = queue.get("candidates") or []
    assignment_territories = {code for item in assignments for code in item.get("territories") or []}
    opportunity_territories = {code for item in opportunities for code in item.get("territories") or []}
    review_territories = {code for item in reviews for code in item.get("territories") or []}
    review_territories.update(code for item in automated_candidates for code in item.get("territories") or [])

    country_index = []
    for code in codes:
        if code in assignment_territories:
            status = "CONFIRMED_THIS_SEASON"
        elif code in opportunity_territories:
            status = "SELECTIVE_PACKAGE"
        elif code in review_territories:
            status = "REVIEW"
        else:
            status = "NO_CONFIRMED_OPTION"
        country_index.append({"code": code, "status": status})

    source_counts = source_state.get("counts") or {}
    milan_radar = _build_milan_radar(root, calendar)
    catalog = {
        "schemaVersion": 3,
        "product": "Milan Radar by CalcioDove",
        "season": editorial.get("season") or "2026-27",
        "generatedAt": iso_now(),
        "editorialUpdatedAt": editorial.get("updatedAt"),
        "coverage": {
            "territoriesCompared": len(codes),
            "standard": countries.get("standard"),
            "sourcesRegistered": source_counts.get("total", 0),
            "sourcesReachable": source_counts.get("ok", 0),
            "sourcesLimited": source_counts.get("limited", 0),
            "sourcesErrored": source_counts.get("errors", 0),
            "confirmedAssignments": len(assignments),
            "selectivePrograms": len(opportunities),
            "reviewCandidates": len(reviews) + len(automated_candidates),
            "meaning": "Ogni territorio è confrontato con il catalogo e le fonti registrate. Non esiste un registro mondiale ufficiale che provi l'assenza assoluta di altre trasmissioni.",
        },
        "policy": {
            "freeDefinition": "Diretta legale della singola partita accessibile senza abbonamento a pagamento nel territorio autorizzato.",
            "excluded": [
                "prove promozionali",
                "servizi inclusi soltanto in un abbonamento preesistente",
                "VPN o aggiramenti geografici",
                "streaming non ufficiali",
                "highlights, radio e live testuali",
            ],
            "publicationRule": "Un pacchetto selettivo non viene mai applicato a tutto il turno. Solo una fonte sufficientemente puntuale può creare una conferma.",
        },
        "assignments": assignments,
        "opportunities": opportunities,
        "reviews": reviews,
        "automaticReviewQueue": automated_candidates,
        "editorialExceptions": editorial.get("exceptions") or [],
        "milanRadar": milan_radar,
        "sources": source_state.get("sources") or [],
        "countryIndex": country_index,
    }
    errors = validate_catalog(catalog, set(codes), set(event_by_id))
    if errors:
        raise ValueError("Catalogo TV non valido:\n- " + "\n- ".join(errors[:30]))
    atomic_write_json(root / "data" / "catalogo-tv.json", catalog)
    return catalog
