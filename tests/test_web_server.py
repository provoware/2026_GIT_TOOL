from __future__ import annotations

import json
import socket
import threading
import urllib.request
from http import HTTPStatus
from pathlib import Path

import pytest

from system import web_server


class FakeBridge:
    def catalog(self):
        return [
            {
                "id": "notiz_editor",
                "name": "Notiz-Editor",
                "description": "Notizen",
                "enabled": True,
                "group": "Kreativ & Organisation",
                "actions": [
                    {
                        "id": "list_notes",
                        "label": "Notizen laden",
                        "mode": "read",
                        "fields": [],
                    }
                ],
                "default_action": "list_notes",
            }
        ]

    def snapshots(self):
        return {"notiz_editor": {"status": "ok", "message": "bereit", "data": {"notes": []}}}

    def invoke(self, module_id, action_id, payload):
        return {
            "status": "ok",
            "message": "ausgeführt",
            "data": {
                "module": module_id,
                "action": action_id,
                "payload": dict(payload),
            },
        }


def _config(
    tmp_path: Path, *, port: int = 8765, max_port: int | None = None
) -> web_server.WebServerConfig:
    static_dir = tmp_path / "web"
    static_dir.mkdir(parents=True)
    (static_dir / "index.html").write_text("<h1>Provoware Memo</h1>", encoding="utf-8")
    (static_dir / "app.js").write_text("console.log('ok')", encoding="utf-8")
    return web_server.WebServerConfig(
        host="127.0.0.1",
        port=port,
        max_port=max_port or port + 4,
        static_dir=static_dir,
        browser_candidates=("google-chrome",),
        chromium_fallbacks=("chromium",),
        allow_chromium_fallback=True,
        open_new_window=True,
    )


def _api(tmp_path: Path) -> web_server.ProvowareApi:
    def note_runner(request):
        if request["action"] == "list_notes":
            return {
                "status": "ok",
                "message": "ok",
                "data": {"notes": [{"id": "n1", "title": "Memo"}]},
                "ui": {},
            }
        return {
            "status": "ok",
            "message": "ok",
            "data": {"id": "n2", "title": request.get("title")},
            "ui": {},
        }

    def todo_runner(request):
        if request["action"] == "calendar":
            return {
                "status": "ok",
                "message": "ok",
                "data": {"entries": [], "view": request["view"]},
            }
        if request["action"] == "list":
            return {
                "status": "ok",
                "message": "ok",
                "data": {"items": [{"id": "t1", "title": "Test"}]},
            }
        if request["action"] == "set_legend":
            return {
                "status": "ok",
                "message": "ok",
                "data": {"legend": request["legend"]},
            }
        if request["action"] == "set_day_colors":
            return {
                "status": "ok",
                "message": "ok",
                "data": {"date": request["date"], "color_ids": request["color_ids"]},
            }
        if request["action"] in {"add_appointment", "update_appointment"}:
            return {
                "status": "ok",
                "message": "ok",
                "data": {
                    "id": request.get("id", "termin-1"),
                    "title": request["title"],
                    "date": request["date"],
                },
            }
        if request["action"] == "delete_appointment":
            return {"status": "ok", "message": "ok", "data": {"id": request["id"]}}
        if request["action"] == "list_reminders":
            return {
                "status": "ok",
                "message": "ok",
                "data": {"due": [], "upcoming": []},
            }
        if request["action"] == "acknowledge_reminder":
            return {
                "status": "ok",
                "message": "ok",
                "data": {"id": request["id"], "reminder_acknowledged": True},
            }
        return {
            "status": "ok",
            "message": "ok",
            "data": {"id": "t2", "title": request.get("title")},
        }

    def archive_runner(request):
        if request["action"] == "list_archives":
            return {
                "status": "ok",
                "message": "ok",
                "payload": {"archives": [{"slug": "genres", "name": "Genres"}]},
            }
        if request["action"] == "list_entries":
            return {
                "status": "ok",
                "message": "ok",
                "payload": {"entries": [{"id": 1, "value": "Fantasy"}]},
            }
        return {"status": "ok", "message": "ok", "payload": {"entry": {"id": 2}}}

    return web_server.ProvowareApi(
        tmp_path,
        note_runner=note_runner,
        todo_runner=todo_runner,
        archive_runner=archive_runner,
        module_bridge=FakeBridge(),
    )


def test_load_config_requires_loopback_and_static_files(tmp_path: Path) -> None:
    static_dir = tmp_path / "web"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("ok", encoding="utf-8")
    config_path = tmp_path / "web_server.json"
    config_path.write_text(
        json.dumps({"host": "0.0.0.0", "port": 8765, "max_port": 8770, "static_dir": "web"}),
        encoding="utf-8",
    )
    with pytest.raises(web_server.WebServerError, match="Loopback"):
        web_server.load_config(config_path, root=tmp_path)

    config_path.write_text(
        json.dumps({"host": "127.0.0.1", "port": 8765, "max_port": 8770, "static_dir": "web"}),
        encoding="utf-8",
    )
    config = web_server.load_config(config_path, root=tmp_path)
    assert config.host == "127.0.0.1"
    assert config.static_dir == static_dir.resolve()


def test_api_bootstrap_combines_existing_modules(tmp_path: Path) -> None:
    result = _api(tmp_path).dispatch("GET", "/api/bootstrap")
    assert result.status == HTTPStatus.OK
    assert result.payload["data"]["notes"][0]["title"] == "Memo"
    assert result.payload["data"]["todos"][0]["title"] == "Test"
    assert result.payload["data"]["archives"][0]["slug"] == "genres"
    assert result.payload["data"]["database"].endswith("data/archiv_manager.sqlite3")


def test_api_archive_entries_are_embedded_not_windowed(tmp_path: Path) -> None:
    result = _api(tmp_path).dispatch("GET", "/api/archives/genres/entries", {"query": ["fant"]})
    assert result.status == HTTPStatus.OK
    assert result.payload["data"]["entries"] == [{"id": 1, "value": "Fantasy"}]


def test_bind_server_uses_free_fallback_port(tmp_path: Path) -> None:
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("127.0.0.1", 0))
    blocker.listen(1)
    occupied = blocker.getsockname()[1]
    config = _config(tmp_path, port=occupied, max_port=min(occupied + 8, 65535))
    server = None
    try:
        server, selected, preferred_free = web_server.bind_server(config, _api(tmp_path))
        assert selected != occupied
        assert preferred_free is False
    finally:
        blocker.close()
        if server is not None:
            server.server_close()


def test_health_endpoint_served_over_real_loopback_socket(tmp_path: Path) -> None:
    config = _config(tmp_path, port=8765)
    server, port, _preferred = web_server.bind_server(config, _api(tmp_path), port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert response.status == HTTPStatus.OK
        assert payload["data"]["product"] == "Provoware Memo"
        assert payload["data"]["embedded_archive"] is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_browser_resolution_prefers_google_chrome(monkeypatch, tmp_path: Path) -> None:
    config = _config(tmp_path)
    monkeypatch.setattr(
        web_server.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name == "google-chrome" else None,
    )
    executable, is_google = web_server.resolve_browser(config)
    assert executable == "/usr/bin/google-chrome"
    assert is_google is True


def test_api_catalog_and_generic_module_action(tmp_path: Path) -> None:
    api = _api(tmp_path)
    catalog = api.dispatch("GET", "/api/catalog")
    assert catalog.status == HTTPStatus.OK
    assert catalog.payload["data"]["modules"][0]["id"] == "notiz_editor"

    action = api.dispatch(
        "POST",
        "/api/modules/notiz_editor/list_notes",
        body={"query": "memo"},
    )
    assert action.status == HTTPStatus.OK
    assert action.payload["data"]["action"] == "list_notes"


def test_api_file_listing_is_sorted_and_restricted(tmp_path: Path) -> None:
    folder = tmp_path / "files"
    folder.mkdir()
    (folder / "zeta.txt").write_text("z", encoding="utf-8")
    (folder / "alpha.txt").write_text("a", encoding="utf-8")
    api = _api(tmp_path)
    result = api.dispatch(
        "GET",
        "/api/files",
        {"path": [str(folder)], "sort": ["name"]},
    )
    assert result.status == HTTPStatus.OK
    assert [item["name"] for item in result.payload["data"]["entries"]] == [
        "alpha.txt",
        "zeta.txt",
    ]

    outside = api.dispatch("GET", "/api/files", {"path": ["/etc"]})
    assert outside.status == HTTPStatus.BAD_REQUEST


def test_static_assets_disable_cache_to_prevent_stale_ui(tmp_path: Path) -> None:
    config = _config(tmp_path, port=8765)
    server, port, _preferred = web_server.bind_server(config, _api(tmp_path), port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/app.js", timeout=5) as response:
            response.read()
        assert response.headers["Cache-Control"] == "no-store"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_image_preview_uses_controlled_png_response(tmp_path: Path) -> None:
    from PIL import Image

    image_path = tmp_path / "preview.jpg"
    Image.new("RGB", (2400, 1400), (30, 80, 140)).save(image_path)
    content, content_type = _api(tmp_path).file_preview(str(image_path))
    assert content_type == "image/png"
    assert content.startswith(b"\x89PNG")


def test_calendar_color_appointment_and_reminder_endpoints(tmp_path: Path) -> None:
    api = _api(tmp_path)
    legend = [
        {"id": f"farbe-{index}", "title": f"Farbe {index}", "color": "#2563eb"}
        for index in range(1, 6)
    ]
    saved_legend = api.dispatch("PUT", "/api/calendar/legend", body={"legend": legend})
    assert saved_legend.status == HTTPStatus.OK
    assert len(saved_legend.payload["data"]["legend"]) == 5

    marker = api.dispatch(
        "PUT",
        "/api/calendar/day-colors",
        body={"date": "2026-08-04", "color_ids": ["farbe-1", "farbe-2"]},
    )
    assert marker.payload["data"]["color_ids"] == ["farbe-1", "farbe-2"]

    appointment = api.dispatch(
        "POST",
        "/api/calendar/appointments",
        body={"title": "Termin", "date": "2026-08-04", "reminder_minutes": 30},
    )
    assert appointment.status == HTTPStatus.CREATED
    assert appointment.payload["data"]["id"] == "termin-1"

    updated = api.dispatch(
        "PUT",
        "/api/calendar/appointments/termin-1",
        body={"title": "Termin neu", "date": "2026-08-05"},
    )
    assert updated.payload["data"]["title"] == "Termin neu"

    reminders = api.dispatch("GET", "/api/calendar/reminders")
    assert reminders.payload["data"] == {"due": [], "upcoming": []}

    acknowledged = api.dispatch("POST", "/api/calendar/reminders/termin-1/acknowledge", body={})
    assert acknowledged.payload["data"]["reminder_acknowledged"] is True

    deleted = api.dispatch("DELETE", "/api/calendar/appointments/termin-1")
    assert deleted.payload["data"]["id"] == "termin-1"
