from __future__ import annotations

import json
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen

from calciodove.calendar import validate_calendar
from calciodove.catalog import validate_catalog
from calciodove.server import CalcioDoveServer, Handler

ROOT = Path(__file__).resolve().parents[1]


def read(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calendar = read("data/calendario.json")
        cls.catalog = read("data/catalogo-tv.json")
        cls.countries = set(read("config/countries.json")["codes"])
        cls.source_registry = read("config/fonti.json")
        cls.radar_editorial = read("editorial/milan-radar.json")

    def test_world_coverage_is_249(self):
        self.assertEqual(249, len(self.countries))
        self.assertEqual(249, len(self.catalog["countryIndex"]))
        self.assertEqual(self.countries, {row["code"] for row in self.catalog["countryIndex"]})

    def test_calendar_is_complete(self):
        self.assertEqual([], validate_calendar(self.calendar["events"]))
        self.assertEqual(380, len(self.calendar["events"]))

    def test_catalog_is_valid(self):
        ids = {event["id"] for event in self.calendar["events"]}
        self.assertEqual([], validate_catalog(self.catalog, self.countries, ids))

    def test_selective_programs_are_not_attached_to_matches(self):
        self.assertTrue(self.catalog["opportunities"])
        self.assertTrue(all("eventId" not in item for item in self.catalog["opportunities"]))

    def test_confirmations_are_point_specific(self):
        ids = {event["id"] for event in self.calendar["events"]}
        for item in self.catalog["assignments"]:
            self.assertEqual("CONFIRMED", item["verification"]["status"])
            self.assertIn(item["eventId"], ids)
            self.assertTrue(item["territories"])

    def test_automatic_candidates_remain_separate(self):
        assignment_ids = {item["id"] for item in self.catalog["assignments"]}
        candidate_ids = {item["id"] for item in self.catalog["automaticReviewQueue"]}
        self.assertTrue(assignment_ids.isdisjoint(candidate_ids))
        self.assertTrue(all(not item["automaticConfirmation"] for item in self.catalog["automaticReviewQueue"]))

    def test_milan_radar_has_exactly_38_milan_fixtures(self):
        fixtures = self.catalog["milanRadar"]["fixtures"]
        self.assertEqual(38, len(fixtures))
        self.assertEqual(set(range(1, 39)), {item["round"] for item in fixtures})
        self.assertEqual(38, len({item["eventId"] for item in fixtures}))
        self.assertTrue(all("Milan" in {item["home"], item["away"]} for item in fixtures))

    def test_milan_radar_has_the_six_requested_broadcasters(self):
        expected = {"rsi-la2", "digi-sport-ro", "bbc-iplayer", "itvx", "cbs-golazo", "rtbf-auvio"}
        broadcasters = self.catalog["milanRadar"]["broadcasters"]
        self.assertEqual(expected, {item["id"] for item in broadcasters})
        self.assertTrue(all(item["watchUrl"].startswith("https://") for item in broadcasters))

    def test_milan_observations_never_inflate_free_matches(self):
        allowed = {
            "CONFIRMED_FREE", "CONFIRMED_NOT_FREE", "PROBABLE_NOT_FREE",
            "POSSIBLE_NOT_CONFIRMED", "NOT_CONFIRMED", "NO_EVIDENCE",
            "HIGHLIGHTS_ONLY", "TEXT_SCORE_ONLY",
        }
        observations = self.catalog["milanRadar"]["observations"]
        fixture_ids = {item["eventId"] for item in self.catalog["milanRadar"]["fixtures"]}
        keys = {(item["eventId"], item["broadcasterId"]) for item in observations}
        self.assertEqual(len(observations), len(keys))
        for item in observations:
            self.assertIn(item["eventId"], fixture_ids)
            self.assertIn(item["state"], allowed)
            if item["countsAsFreeFullMatch"]:
                self.assertEqual("CONFIRMED_FREE", item["state"])
                self.assertEqual("FULL_MATCH_LIVE", item["medium"])
            if item["state"] in {"HIGHLIGHTS_ONLY", "TEXT_SCORE_ONLY"}:
                self.assertFalse(item["countsAsFreeFullMatch"])

    def test_known_milan_venezia_verdict_is_paid_digi_live(self):
        observations = self.catalog["milanRadar"]["observations"]
        digi = next(item for item in observations if item["eventId"] == "401874758" and item["broadcasterId"] == "digi-sport-ro")
        self.assertEqual("CONFIRMED_NOT_FREE", digi["state"])
        self.assertEqual("FULL_MATCH_LIVE", digi["medium"])
        self.assertEqual("Digi Sport 3", digi["channel"])
        self.assertFalse(digi["countsAsFreeFullMatch"])

    def test_fifteen_sources_have_milan_priority(self):
        sources = self.source_registry["sources"]
        priorities = [item for item in sources if item.get("priorityMilan")]
        self.assertEqual(22, len(sources))
        self.assertEqual(15, len(priorities))
        registered = {item["id"] for item in sources}
        used = {source_id for item in self.radar_editorial["broadcasters"] for source_id in item["sourceIds"]}
        self.assertTrue(used.issubset(registered))
        self.assertTrue(all(next(item for item in sources if item["id"] == source_id)["priorityMilan"] for source_id in used))

    def test_frontend_exposes_the_milan_matrix(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        javascript = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
        for label in ("RSI LA 2", "Digi Sport", "BBC iPlayer", "ITVX", "CBS Sports Golazo", "RTBF Auvio"):
            self.assertIn(label, html)
        for element_id in ("focus-event", "focus-summary", "broadcaster-grid", "milan-fixtures"):
            self.assertIn(f'id="{element_id}"', html)
        self.assertIn("function renderFocus()", javascript)
        self.assertIn("mr4.focus", javascript)


class ServerTests(unittest.TestCase):
    def test_health_and_home(self):
        server = CalcioDoveServer(("127.0.0.1", 0), Handler, ROOT)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            with urlopen(f"http://127.0.0.1:{port}/api/health", timeout=3) as response:
                health = json.load(response)
            self.assertTrue(health["ok"])
            self.assertTrue(health["python"])
            self.assertEqual("Milan Radar", health["product"])
            self.assertEqual("4.1.0", health["version"])
            with urlopen(f"http://127.0.0.1:{port}/", timeout=3) as response:
                body = response.read().decode("utf-8")
            self.assertIn("Milan Radar", body)
            self.assertIn("RSI LA 2", body)
            self.assertIn("Digi Sport", body)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
