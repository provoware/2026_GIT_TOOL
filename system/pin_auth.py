#!/usr/bin/env python3
"""PIN-Login: prüft PIN und setzt Zufallssperre bei Fehleingaben."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

from config_utils import ensure_path, load_json
from logging_center import setup_logging as setup_logging_center

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "pin.json"
DEFAULT_STATE = Path(__file__).resolve().parents[1] / "data" / "pin_state.json"


class PinAuthError(Exception):
    """Allgemeiner Fehler für den PIN-Check."""


@dataclass(frozen=True)
class PinConfig:
    enabled: bool
    pin_hint: str
    pin_hash: str
    salt: str
    max_attempts: int
    lock_min_seconds: int
    lock_max_seconds: int


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PinAuthError(f"{label} fehlt oder ist leer.")
    return value.strip()


def _require_int_min(value: object, label: str, minimum: int) -> int:
    if not isinstance(value, int):
        raise PinAuthError(f"{label} ist keine Zahl.")
    if value < minimum:
        raise PinAuthError(f"{label} muss mindestens {minimum} sein.")
    return value


def _hash_pin(pin: str, salt: str) -> str:
    if not isinstance(pin, str) or not pin:
        raise PinAuthError("PIN fehlt oder ist leer.")
    if not isinstance(salt, str) or not salt:
        raise PinAuthError("Salt fehlt oder ist leer.")
    return hashlib.sha256(f"{salt}{pin}".encode("utf-8")).hexdigest()


def load_pin_config(path: Path) -> PinConfig:
    ensure_path(path, "config_path", PinAuthError)
    data = load_json(path, PinAuthError, "PIN-Konfiguration fehlt", "PIN-Konfiguration ungültig")
    enabled = data.get("enabled", False)
    if not isinstance(enabled, bool):
        raise PinAuthError("enabled ist kein Wahrheitswert (bool).")
    pin_hint = _require_text(data.get("pin_hint", ""), "pin_hint")
    pin_hash = _require_text(data.get("pin_hash", ""), "pin_hash")
    salt = _require_text(data.get("salt", ""), "salt")
    max_attempts = _require_int_min(data.get("max_attempts", 3), "max_attempts", 1)
    lock_min_seconds = _require_int_min(data.get("lock_min_seconds", 2), "lock_min_seconds", 1)
    lock_max_seconds = _require_int_min(data.get("lock_max_seconds", 7), "lock_max_seconds", 1)
    if lock_min_seconds > lock_max_seconds:
        raise PinAuthError("lock_min_seconds darf nicht größer als lock_max_seconds sein.")
    return PinConfig(
        enabled=enabled,
        pin_hint=pin_hint,
        pin_hash=pin_hash,
        salt=salt,
        max_attempts=max_attempts,
        lock_min_seconds=lock_min_seconds,
        lock_max_seconds=lock_max_seconds,
    )


def load_state(path: Path) -> Dict[str, Any]:
    ensure_path(path, "state_path", PinAuthError)
    if not path.exists():
        return {"failed_attempts": 0, "locked_until": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PinAuthError(f"PIN-Statusdatei ungültig: {path}") from exc


def save_state(path: Path, state: Dict[str, Any]) -> None:
    ensure_path(path, "state_path", PinAuthError)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _parse_locked_until(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _format_time(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def check_pin(config: PinConfig, state_path: Path) -> int:
    if not config.enabled:
        print("PIN-Check: deaktiviert.")
        return 0

    state = load_state(state_path)
    failed_attempts = int(state.get("failed_attempts", 0))
    locked_until = _parse_locked_until(state.get("locked_until"))
    now = datetime.now(timezone.utc)
    if locked_until and locked_until > now:
        wait_seconds = int((locked_until - now).total_seconds())
        print(
            "PIN-Check: Gesperrt wegen Fehlversuchen. "
            f"Bitte {wait_seconds} Sekunden warten (bis {_format_time(locked_until)})."
        )
        return 2

    pin = input("Bitte PIN eingeben: ").strip()
    if not pin:
        print("PIN-Check: Keine Eingabe. Bitte erneut starten.")
        return 1

    if _hash_pin(pin, config.salt) == config.pin_hash:
        save_state(state_path, {"failed_attempts": 0, "locked_until": None})
        print("PIN-Check: Zugriff erlaubt.")
        return 0

    failed_attempts += 1
    lock_seconds = random.randint(config.lock_min_seconds, config.lock_max_seconds)
    locked_until = now + timedelta(seconds=lock_seconds)
    save_state(
        state_path,
        {"failed_attempts": failed_attempts, "locked_until": locked_until.isoformat()},
    )
    remaining = max(config.max_attempts - failed_attempts, 0)
    print("PIN-Check: Falsche PIN.")
    print(
        f"PIN-Check: Zufallssperre aktiv für {lock_seconds} Sekunden "
        f"(bis {_format_time(locked_until)})."
    )
    if remaining == 0:
        print("PIN-Check: Maximale Fehlversuche erreicht. Bitte später erneut versuchen.")
    else:
        print(f"PIN-Check: Noch {remaining} Versuch(e) übrig.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PIN-Login: prüft PIN und setzt Zufallssperre bei Fehleingaben.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Pfad zur PIN-Konfiguration (JSON).",
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=DEFAULT_STATE,
        help="Pfad zur PIN-Statusdatei (JSON).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug-Modus aktivieren.",
    )
    return parser


def setup_logging(debug: bool) -> None:
    setup_logging_center(debug)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.debug)

    try:
        config = load_pin_config(args.config)
    except PinAuthError as exc:
        logging.error("PIN-Check konnte nicht starten: %s", exc)
        return 2

    try:
        return check_pin(config, args.state)
    except PinAuthError as exc:
        logging.error("PIN-Check fehlgeschlagen: %s", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
