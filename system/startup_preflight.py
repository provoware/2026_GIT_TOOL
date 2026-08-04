#!/usr/bin/env python3
"""Fail-fast preflight validation for the Provoware Memo startup chain."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

MIN_PYTHON = (3, 10)
MIN_FREE_BYTES = 256 * 1024 * 1024
REQUIRED_FILES = (
    "config/product.json",
    "config/modules.json",
    "config/launcher_gui.json",
    "config/requirements.txt",
    "config/web_server.json",
    "scripts/start.sh",
    "scripts/ensure_venv.sh",
    "system/startup_preflight.py",
    "system/dependency_checker.py",
    "system/web_server.py",
    "web/index.html",
    "web/app.js",
    "web/styles.css",
    "system/launcher_gui.py",
    "modules/archiv_manager/manifest.json",
)
REQUIRED_DIRS = ("config", "system", "scripts", "modules", "web", "data", "logs")
JSON_FILES = (
    "config/product.json",
    "config/modules.json",
    "config/launcher_gui.json",
    "config/web_server.json",
    "modules/archiv_manager/manifest.json",
)


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def _write_report(path: Path | None, root: Path, checks: Iterable[Check], ok: bool) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "product": "Provoware Memo",
        "root": str(root),
        "ok": ok,
        "python": sys.version.split()[0],
        "checks": [asdict(check) for check in checks],
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def validate(root: Path) -> list[Check]:
    checks: list[Check] = []
    root = root.resolve()

    missing_dirs = [item for item in REQUIRED_DIRS if not (root / item).is_dir()]
    checks.append(
        Check(
            "project_directories",
            "error" if missing_dirs else "ok",
            ", ".join(missing_dirs) if missing_dirs else "vollständig",
        )
    )

    missing_files = [item for item in REQUIRED_FILES if not (root / item).is_file()]
    checks.append(
        Check(
            "critical_files",
            "error" if missing_files else "ok",
            ", ".join(missing_files) if missing_files else "vollständig",
        )
    )

    product_detail = "nicht geprüft"
    product_status = "error"
    product_path = root / "config/product.json"
    if product_path.is_file():
        try:
            product = json.loads(product_path.read_text(encoding="utf-8"))
            product_status = (
                "ok"
                if product.get("name") == "Provoware Memo" and product.get("id") == "provoware_memo"
                else "error"
            )
            product_detail = f"{product.get('name')} ({product.get('id')})"
        except (OSError, json.JSONDecodeError) as exc:
            product_detail = str(exc)
    checks.append(Check("product_identity", product_status, product_detail))

    invalid_json: list[str] = []
    for relative in JSON_FILES:
        path = root / relative
        if not path.is_file():
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            invalid_json.append(f"{relative}: {exc}")
    checks.append(
        Check(
            "json",
            "error" if invalid_json else "ok",
            "; ".join(invalid_json) if invalid_json else "gültig",
        )
    )

    py_ok = sys.version_info[:2] >= MIN_PYTHON
    checks.append(Check("python", "ok" if py_ok else "error", sys.version.split()[0]))

    try:
        usage = shutil.disk_usage(root)
        disk_ok = usage.free >= MIN_FREE_BYTES
        disk_detail = f"{usage.free // (1024 * 1024)} MiB frei"
    except OSError as exc:
        disk_ok = False
        disk_detail = str(exc)
    checks.append(Check("disk", "ok" if disk_ok else "error", disk_detail))

    unwritable: list[str] = []
    for relative in ("data", "logs"):
        path = root / relative
        if path.exists() and not os.access(path, os.W_OK | os.X_OK):
            unwritable.append(relative)
    checks.append(
        Check(
            "writable_runtime",
            "error" if unwritable else "ok",
            ", ".join(unwritable) if unwritable else "data und logs beschreibbar",
        )
    )
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Provoware-Memo-Vorvalidierung")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    checks = validate(root)
    ok = all(check.status == "ok" for check in checks)
    for index, check in enumerate(checks, start=1):
        print(
            f"Vorvalidierung [{index}/{len(checks)}] {check.name}: "
            f"{check.status.upper()} — {check.detail}"
        )
    _write_report(args.report, root, checks, ok)
    if not ok:
        print(
            "Vorvalidierung: Kritischer Projektzustand. Es werden keine "
            "Abhängigkeiten installiert und kein Teilstart ausgeführt.",
            file=sys.stderr,
        )
        return 12
    print("Vorvalidierung: Provoware Memo ist vollständig und startfähig vorbereitet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
