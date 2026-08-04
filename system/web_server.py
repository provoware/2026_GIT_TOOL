#!/usr/bin/env python3
"""Loopback web server and integrated API for Provoware Memo."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_DIR = PROJECT_ROOT / "system"
for import_root in (PROJECT_ROOT, SYSTEM_DIR):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from modules.archiv_manager import entry as archive_module  # noqa: E402
from modules.notiz_editor import module as note_module  # noqa: E402
from modules.todo_kalender import module as todo_module  # noqa: E402

MAX_JSON_BYTES = 1_048_576
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "web_server.json"
DEFAULT_RUNTIME_STATE = PROJECT_ROOT / "data" / "runtime" / "web_server.json"


class WebServerError(RuntimeError):
    """Controlled web server configuration or startup error."""


@dataclass(frozen=True)
class WebServerConfig:
    host: str
    port: int
    max_port: int
    static_dir: Path
    browser_candidates: tuple[str, ...]
    chromium_fallbacks: tuple[str, ...]
    allow_chromium_fallback: bool
    open_new_window: bool


@dataclass(frozen=True)
class ApiResult:
    status: int
    payload: dict[str, Any]


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise WebServerError(f"{field} ist kein Objekt.")
    return value


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WebServerError(f"{field} fehlt oder ist leer.")
    return value.strip()


def _require_int(value: Any, field: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise WebServerError(f"{field} ist keine Ganzzahl.")
    if not minimum <= value <= maximum:
        raise WebServerError(f"{field} liegt außerhalb {minimum}..{maximum}.")
    return value


def load_config(path: Path = DEFAULT_CONFIG, *, root: Path = PROJECT_ROOT) -> WebServerConfig:
    config_path = path if path.is_absolute() else root / path
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WebServerError(f"Webserver-Konfiguration fehlt: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise WebServerError(f"Webserver-Konfiguration ist ungültig: {exc}") from exc
    data = _require_mapping(raw, "Konfiguration")
    host = _require_text(data.get("host", "127.0.0.1"), "host")
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise WebServerError("Der integrierte Server darf ausschließlich an Loopback gebunden werden.")
    port = _require_int(data.get("port", 8765), "port", minimum=1, maximum=65535)
    max_port = _require_int(data.get("max_port", port + 20), "max_port", minimum=port, maximum=65535)
    static_value = _require_text(data.get("static_dir", "web"), "static_dir")
    static_dir = Path(static_value)
    if not static_dir.is_absolute():
        static_dir = root / static_dir
    static_dir = static_dir.resolve()
    if not static_dir.is_dir():
        raise WebServerError(f"Weboberfläche fehlt: {static_dir}")
    if not (static_dir / "index.html").is_file():
        raise WebServerError(f"Startseite fehlt: {static_dir / 'index.html'}")

    browser_candidates = tuple(
        _require_text(item, "browser_candidates")
        for item in data.get("browser_candidates", ["google-chrome", "google-chrome-stable"])
    )
    chromium_fallbacks = tuple(
        _require_text(item, "chromium_fallbacks")
        for item in data.get("chromium_fallbacks", ["chromium", "chromium-browser"])
    )
    return WebServerConfig(
        host=host,
        port=port,
        max_port=max_port,
        static_dir=static_dir,
        browser_candidates=browser_candidates,
        chromium_fallbacks=chromium_fallbacks,
        allow_chromium_fallback=bool(data.get("allow_chromium_fallback", True)),
        open_new_window=bool(data.get("open_new_window", True)),
    )


def _json_success(data: Any, message: str = "OK") -> dict[str, Any]:
    return {"status": "ok", "message": message, "data": data}


def _json_error(message: str, *, code: str = "request_error") -> dict[str, Any]:
    return {"status": "error", "message": message, "code": code, "data": {}}


def _module_data(response: Mapping[str, Any], *, payload_key: str) -> Any:
    if response.get("status") != "ok":
        raise WebServerError(str(response.get("message") or "Modulaufruf fehlgeschlagen."))
    container = response.get(payload_key)
    if not isinstance(container, Mapping):
        raise WebServerError("Modulausgabe enthält keine gültigen Daten.")
    return container


class ProvowareApi:
    """Dispatch API requests into the existing note, todo and archive modules."""

    def __init__(
        self,
        root: Path = PROJECT_ROOT,
        *,
        note_runner: Callable[[dict[str, Any]], dict[str, Any]] = note_module.run,
        todo_runner: Callable[[dict[str, Any]], dict[str, Any]] = todo_module.run,
        archive_runner: Callable[[dict[str, Any]], dict[str, Any]] = archive_module.run,
    ) -> None:
        self.root = root.resolve()
        self._note_runner = note_runner
        self._todo_runner = todo_runner
        self._archive_runner = archive_runner
        self._lock = threading.RLock()
        self.database_path = self.root / "data" / "archiv_manager.sqlite3"

    def dispatch(
        self,
        method: str,
        raw_path: str,
        query: Mapping[str, list[str]] | None = None,
        body: Mapping[str, Any] | None = None,
    ) -> ApiResult:
        method = method.upper()
        path = urllib.parse.unquote(raw_path).rstrip("/") or "/"
        query = query or {}
        body = body or {}
        try:
            with self._lock:
                return self._dispatch_locked(method, path, query, body)
        except (KeyError, TypeError, ValueError, WebServerError) as exc:
            return ApiResult(HTTPStatus.BAD_REQUEST, _json_error(str(exc)))
        except Exception as exc:  # noqa: BLE001
            return ApiResult(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                _json_error(f"Interner Serverfehler: {type(exc).__name__}", code="internal_error"),
            )

    def _dispatch_locked(
        self,
        method: str,
        path: str,
        query: Mapping[str, list[str]],
        body: Mapping[str, Any],
    ) -> ApiResult:
        if path == "/api/health" and method == "GET":
            return ApiResult(
                HTTPStatus.OK,
                _json_success(
                    {
                        "product": "Provoware Memo",
                        "product_id": "provoware_memo",
                        "database": str(self.database_path),
                        "embedded_archive": True,
                    },
                    "Server und Datenmodule sind erreichbar.",
                ),
            )

        if path == "/api/bootstrap" and method == "GET":
            notes = _module_data(self._note_runner({"action": "list_notes"}), payload_key="data")
            todos = _module_data(self._todo_runner({"action": "list"}), payload_key="data")
            archives = _module_data(self._archive_runner({"action": "list_archives"}), payload_key="payload")
            calendar = _module_data(
                self._todo_runner({"action": "calendar", "view": "monat"}), payload_key="data"
            )
            return ApiResult(
                HTTPStatus.OK,
                _json_success(
                    {
                        "notes": notes.get("notes", []),
                        "todos": todos.get("items", []),
                        "archives": archives.get("archives", []),
                        "calendar": calendar,
                        "database": str(self.database_path),
                    },
                    "Provoware-Memo-Daten geladen.",
                ),
            )

        if path == "/api/notes":
            if method == "GET":
                result = _module_data(self._note_runner({"action": "list_notes"}), payload_key="data")
                return ApiResult(HTTPStatus.OK, _json_success(result, "Notizen geladen."))
            if method == "POST":
                request = {
                    "action": "create_note",
                    "title": body.get("title"),
                    "body": body.get("body"),
                    "tags": body.get("tags", []),
                    "template_id": body.get("template_id"),
                    "custom_fields": body.get("custom_fields", {}),
                }
                result = _module_data(self._note_runner(request), payload_key="data")
                return ApiResult(HTTPStatus.CREATED, _json_success(result, "Notiz gespeichert."))

        if path.startswith("/api/notes/") and path.endswith("/favorite") and method == "POST":
            note_id = path.removeprefix("/api/notes/").removesuffix("/favorite").strip("/")
            result = _module_data(
                self._note_runner({"action": "toggle_favorite", "id": note_id}), payload_key="data"
            )
            return ApiResult(HTTPStatus.OK, _json_success(result, "Favoritenstatus aktualisiert."))

        if path == "/api/todos":
            if method == "GET":
                result = _module_data(self._todo_runner({"action": "list"}), payload_key="data")
                return ApiResult(HTTPStatus.OK, _json_success(result, "Aufgaben geladen."))
            if method == "POST":
                result = _module_data(
                    self._todo_runner(
                        {
                            "action": "add",
                            "title": body.get("title"),
                            "planned_date": body.get("planned_date"),
                            "notes": body.get("notes", ""),
                        }
                    ),
                    payload_key="data",
                )
                return ApiResult(HTTPStatus.CREATED, _json_success(result, "Aufgabe gespeichert."))

        if path.startswith("/api/todos/") and path.endswith("/complete") and method == "POST":
            todo_id = path.removeprefix("/api/todos/").removesuffix("/complete").strip("/")
            request: dict[str, Any] = {"action": "complete", "id": todo_id}
            if body.get("done_date"):
                request["done_date"] = body["done_date"]
            result = _module_data(self._todo_runner(request), payload_key="data")
            return ApiResult(HTTPStatus.OK, _json_success(result, "Aufgabe erledigt."))

        if path == "/api/calendar" and method == "GET":
            request: dict[str, Any] = {
                "action": "calendar",
                "view": self._query_value(query, "view", "monat"),
            }
            reference_date = self._query_value(query, "reference_date", "")
            if reference_date:
                request["reference_date"] = reference_date
            result = _module_data(self._todo_runner(request), payload_key="data")
            return ApiResult(HTTPStatus.OK, _json_success(result, "Kalender geladen."))

        if path == "/api/archives":
            if method == "GET":
                result = _module_data(
                    self._archive_runner({"action": "list_archives"}), payload_key="payload"
                )
                return ApiResult(HTTPStatus.OK, _json_success(result, "Archive geladen."))
            if method == "POST":
                result = _module_data(
                    self._archive_runner(
                        {
                            "action": "create_archive",
                            "name": body.get("name"),
                            "description": body.get("description", ""),
                            "split_on_comma": bool(body.get("split_on_comma", True)),
                            "source": "provoware-web",
                        }
                    ),
                    payload_key="payload",
                )
                return ApiResult(HTTPStatus.CREATED, _json_success(result, "Archiv angelegt."))

        if path.startswith("/api/archives/") and path.endswith("/entries"):
            archive_slug = path.removeprefix("/api/archives/").removesuffix("/entries").strip("/")
            if not archive_slug:
                raise WebServerError("Archivkennung fehlt.")
            if method == "GET":
                request = {
                    "action": "list_entries",
                    "archive": archive_slug,
                    "query": self._query_value(query, "query", ""),
                }
                category = self._query_value(query, "category", "")
                if category:
                    request["category"] = category
                result = _module_data(self._archive_runner(request), payload_key="payload")
                return ApiResult(HTTPStatus.OK, _json_success(result, "Archiveinträge geladen."))
            if method == "POST":
                result = _module_data(
                    self._archive_runner(
                        {
                            "action": "add_entries",
                            "archive": archive_slug,
                            "value": body.get("value", ""),
                            "category": body.get("category", "Allgemein"),
                            "source": "provoware-web",
                            "apply_spelling": bool(body.get("apply_spelling", False)),
                        }
                    ),
                    payload_key="payload",
                )
                return ApiResult(HTTPStatus.CREATED, _json_success(result, "Archiveintrag verarbeitet."))

        if path.startswith("/api/archive-entries/"):
            entry_id = int(path.removeprefix("/api/archive-entries/").strip("/"))
            if method in {"PUT", "PATCH"}:
                result = _module_data(
                    self._archive_runner(
                        {
                            "action": "update_entry",
                            "entry_id": entry_id,
                            "value": body.get("value", ""),
                            "category": body.get("category", "Allgemein"),
                            "source": "provoware-web",
                        }
                    ),
                    payload_key="payload",
                )
                return ApiResult(HTTPStatus.OK, _json_success(result, "Archiveintrag aktualisiert."))
            if method == "DELETE":
                result = _module_data(
                    self._archive_runner(
                        {"action": "delete_entry", "entry_id": entry_id, "source": "provoware-web"}
                    ),
                    payload_key="payload",
                )
                return ApiResult(HTTPStatus.OK, _json_success(result, "Archiveintrag gelöscht."))

        return ApiResult(HTTPStatus.NOT_FOUND, _json_error("API-Endpunkt nicht gefunden.", code="not_found"))

    @staticmethod
    def _query_value(query: Mapping[str, list[str]], key: str, default: str) -> str:
        values = query.get(key)
        if not values:
            return default
        return str(values[0])


class ProvowareRequestHandler(BaseHTTPRequestHandler):
    server_version = "ProvowareMemo/1.0"
    protocol_version = "HTTP/1.1"
    api: ProvowareApi
    static_dir: Path

    def do_GET(self) -> None:  # noqa: N802
        self._handle_request()

    def do_POST(self) -> None:  # noqa: N802
        self._handle_request()

    def do_PUT(self) -> None:  # noqa: N802
        self._handle_request()

    def do_PATCH(self) -> None:  # noqa: N802
        self._handle_request()

    def do_DELETE(self) -> None:  # noqa: N802
        self._handle_request()

    def _handle_request(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path.startswith("/api/"):
            body = self._read_json_body() if self.command in {"POST", "PUT", "PATCH"} else {}
            if body is None:
                return
            result = self.api.dispatch(
                self.command,
                parsed.path,
                urllib.parse.parse_qs(parsed.query, keep_blank_values=True),
                body,
            )
            self._send_json(result.status, result.payload)
            return
        if self.command != "GET":
            self._send_json(HTTPStatus.METHOD_NOT_ALLOWED, _json_error("Methode nicht erlaubt."))
            return
        self._serve_static(parsed.path)

    def _read_json_body(self) -> Mapping[str, Any] | None:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, _json_error("Ungültige Content-Length."))
            return None
        if length < 0 or length > MAX_JSON_BYTES:
            self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, _json_error("Anfrage ist zu groß."))
            return None
        try:
            raw = self.rfile.read(length) if length else b"{}"
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(HTTPStatus.BAD_REQUEST, _json_error("JSON-Anfrage ist ungültig."))
            return None
        if not isinstance(value, Mapping):
            self._send_json(HTTPStatus.BAD_REQUEST, _json_error("JSON-Anfrage muss ein Objekt sein."))
            return None
        return value

    def _serve_static(self, raw_path: str) -> None:
        relative = raw_path.lstrip("/") or "index.html"
        candidate = (self.static_dir / relative).resolve()
        try:
            candidate.relative_to(self.static_dir)
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not candidate.is_file():
            candidate = self.static_dir / "index.html"
        content = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self._common_headers()
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"} else content_type)
        self.send_header("Cache-Control", "no-cache" if candidate.name == "index.html" else "public, max-age=3600")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status: int, payload: Mapping[str, Any]) -> None:
        content = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        self.send_response(status)
        self._common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _common_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'",
        )

    def log_message(self, fmt: str, *args: Any) -> None:
        if os.environ.get("PROVOWARE_WEB_QUIET") == "1":
            return
        super().log_message(fmt, *args)


def handler_factory(api: ProvowareApi, static_dir: Path):
    class BoundHandler(ProvowareRequestHandler):
        pass

    BoundHandler.api = api
    BoundHandler.static_dir = static_dir.resolve()
    return BoundHandler


def bind_server(
    config: WebServerConfig,
    api: ProvowareApi,
    *,
    host: str | None = None,
    port: int | None = None,
    max_port: int | None = None,
    strict_port: bool = False,
) -> tuple[ThreadingHTTPServer, int, bool]:
    selected_host = host or config.host
    preferred = config.port if port is None else port
    upper = config.max_port if max_port is None else max_port
    if preferred == 0:
        server = ThreadingHTTPServer((selected_host, 0), handler_factory(api, config.static_dir))
        server.daemon_threads = True
        return server, int(server.server_address[1]), True
    if not 1 <= preferred <= 65535 or not preferred <= upper <= 65535:
        raise WebServerError("Ungültiger Portbereich.")
    last_error: OSError | None = None
    candidates = [preferred] if strict_port else list(range(preferred, upper + 1))
    for candidate in candidates:
        try:
            server = ThreadingHTTPServer(
                (selected_host, candidate), handler_factory(api, config.static_dir)
            )
        except OSError as exc:
            last_error = exc
            continue
        server.daemon_threads = True
        return server, candidate, candidate == preferred
    detail = f": {last_error}" if last_error else ""
    raise WebServerError(f"Kein freier Port im Bereich {preferred}..{upper}{detail}")


def resolve_browser(config: WebServerConfig) -> tuple[str | None, bool]:
    for candidate in config.browser_candidates:
        executable = shutil.which(candidate)
        if executable:
            return executable, True
    if config.allow_chromium_fallback:
        for candidate in config.chromium_fallbacks:
            executable = shutil.which(candidate)
            if executable:
                return executable, False
    return None, False


def launch_browser(url: str, config: WebServerConfig) -> tuple[bool, str]:
    executable, is_google_chrome = resolve_browser(config)
    if executable is None:
        return False, "Google Chrome oder ein erlaubter Chromium-Fallback wurde nicht gefunden."
    command = [executable]
    if config.open_new_window:
        command.append("--new-window")
    command.append(url)
    try:
        subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        return False, f"Browserstart fehlgeschlagen: {exc}"
    name = "Google Chrome" if is_google_chrome else Path(executable).name
    return True, f"{name} geöffnet."


def write_runtime_state(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def smoke_test(config: WebServerConfig, api: ProvowareApi) -> int:
    server, port, _preferred = bind_server(config, api, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://{config.host}:{port}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if response.status != HTTPStatus.OK or payload.get("status") != "ok":
            raise WebServerError("Health-Endpunkt lieferte keinen erfolgreichen Status.")
        print(f"Webserver-Smoke-Test: OK — {url}")
        return 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Provoware Memo – integrierter Webserver")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--max-port", type=int)
    parser.add_argument("--strict-port", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--check-browser", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--runtime-state", type=Path, default=DEFAULT_RUNTIME_STATE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    server: ThreadingHTTPServer | None = None
    try:
        config = load_config(args.config)
        api = ProvowareApi()
        if args.smoke_test:
            return smoke_test(config, api)
        if args.check_browser:
            browser, is_google_chrome = resolve_browser(config)
            if browser is None:
                raise WebServerError(
                    "Google Chrome oder ein erlaubter Chromium-Fallback ist nicht installiert."
                )
            browser_name = "Google Chrome" if is_google_chrome else Path(browser).name
            print(f"Provoware Memo: Browserprüfung bestanden — {browser_name}.")

        server, port, preferred_free = bind_server(
            config,
            api,
            host=args.host,
            port=args.port,
            max_port=args.max_port,
            strict_port=args.strict_port,
        )
        host = args.host or config.host
        url = f"http://{host}:{port}/"
        print(
            f"Provoware Memo: Port {port} ist gebunden "
            f"({'Wunschport frei' if preferred_free else 'freier Ersatzport'})."
        )
        print(f"Provoware Memo: Webserver bereit — {url}")
        print(f"Provoware Memo: Archivdatenbank eingebettet — {api.database_path}")
        if args.check_only:
            write_runtime_state(
                args.runtime_state,
                {
                    "product": "Provoware Memo",
                    "status": "validated",
                    "host": host,
                    "port": port,
                    "url": url,
                    "preferred_port_free": preferred_free,
                    "database": str(api.database_path),
                },
            )
            return 0
        state = {
            "product": "Provoware Memo",
            "status": "ready",
            "host": host,
            "port": port,
            "url": url,
            "preferred_port_free": preferred_free,
            "database": str(api.database_path),
            "pid": os.getpid(),
        }
        write_runtime_state(args.runtime_state, state)
        if not args.no_browser:
            opened, detail = launch_browser(url, config)
            print(f"Provoware Memo: {detail}")
            if not opened:
                print(f"Provoware Memo: Bitte URL manuell in Google Chrome öffnen: {url}", file=sys.stderr)
        print("Provoware Memo: Server läuft. Beenden mit Strg+C.")
        server.serve_forever(poll_interval=0.25)
        return 0
    except KeyboardInterrupt:
        print("\nProvoware Memo: Server wird beendet.")
        return 0
    except (OSError, WebServerError) as exc:
        print(f"Provoware Memo: Webserver-Fehler — {exc}", file=sys.stderr)
        return 14
    finally:
        if server is not None:
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
