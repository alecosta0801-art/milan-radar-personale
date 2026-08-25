"""Server locale Milan Radar, basato solo sulla libreria standard Python."""
from __future__ import annotations

import argparse
import json
import mimetypes
import threading
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .updater import run_update
from .util import load_json


class CalcioDoveServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler, root: Path):
        super().__init__(address, handler)
        self.root = root.resolve()
        self.update_lock = threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    server_version = "MilanRadar/4.1"

    @property
    def root(self) -> Path:
        return self.server.root  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def _json(self, value, status=HTTPStatus.OK) -> None:
        body = json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        api_files = {
            "/api/catalog": self.root / "data" / "catalogo-tv.json",
            "/api/calendar": self.root / "data" / "calendario.json",
            "/api/status": self.root / "data" / "ultimo-aggiornamento.json",
            "/api/sources": self.root / "data" / "stato-fonti.json",
        }
        if path == "/api/health":
            self._json({"ok": True, "product": "Milan Radar", "version": "4.1.0", "python": True})
            return
        if path in api_files:
            try:
                self._json(load_json(api_files[path]))
            except FileNotFoundError:
                self._json({"ok": False, "error": "Dati non ancora generati"}, HTTPStatus.NOT_FOUND)
            return
        self._serve_static(path)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/refresh":
            self._json({"ok": False, "error": "Endpoint inesistente"}, HTTPStatus.NOT_FOUND)
            return
        lock = self.server.update_lock  # type: ignore[attr-defined]
        if not lock.acquire(blocking=False):
            self._json({"ok": False, "error": "Aggiornamento già in corso"}, HTTPStatus.CONFLICT)
            return
        try:
            report = run_update(self.root, check_network_sources=True)
            self._json(report, HTTPStatus.OK if report["ok"] else HTTPStatus.INTERNAL_SERVER_ERROR)
        finally:
            lock.release()

    def _serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"", "/"} else request_path.lstrip("/")
        target = (self.root / relative).resolve()
        try:
            target.relative_to(self.root)
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if target.suffix in {".html", ".css", ".js", ".json"}:
            content_type += "; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store" if target.suffix == ".json" else "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.end_headers()
        self.wfile.write(body)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Avvia Milan Radar nel browser")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8788)
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    server = None
    last_error = None
    for port in range(args.port, args.port + 10):
        try:
            server = CalcioDoveServer((args.host, port), Handler, root)
            if port != args.port:
                print(f"La porta {args.port} era occupata: uso automaticamente la porta {port}.")
            break
        except OSError as exc:
            last_error = exc
    if server is None:
        print(f"Impossibile avviare Milan Radar: {last_error}")
        print("Chiudi eventuali vecchie finestre dell’app e riprova.")
        raise SystemExit(1)
    actual_port = int(server.server_address[1])
    shown_host = "localhost" if args.host in {"127.0.0.1", "0.0.0.0"} else args.host
    url = f"http://{shown_host}:{actual_port}/"
    print("\nMilan Radar è pronto.")
    print(f"Apri: {url}")
    print("Per chiudere: Ctrl+C o chiudi questa finestra.\n")
    if not args.no_browser:
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nChiusura Milan Radar…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
