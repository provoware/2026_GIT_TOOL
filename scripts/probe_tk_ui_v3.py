#!/usr/bin/env python3
"""Kanonische Tk-Probe mit einem isolierten Prozess pro Profil und Oberfläche."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "system"))
sys.path.insert(0, str(ROOT / "scripts"))

import probe_tk_ui as base
from config_models import load_gui_config
from ui_acceptance import DEVICE_PROFILES, DeviceProfile


REQUIRED_WIDGETS = {
    "launcher": (
        "controls_frame",
        "help_section",
        "developer_frame",
        "status_label",
        "footer_label",
        "output_text",
    ),
    "main_window": (
        "workspace",
        "status_label",
        "note_label",
    ),
}


def _profile_by_key(key: str) -> DeviceProfile:
    for profile in DEVICE_PROFILES:
        if profile.key == key:
            return profile
    raise ValueError(f"Unbekanntes Geräteprofil: {key}")


def _hidden_required_widgets(app: Any, surface: str) -> list[dict[str, Any]]:
    hidden: list[dict[str, Any]] = []
    for attribute in REQUIRED_WIDGETS[surface]:
        widget = getattr(app, attribute, None)
        if widget is None:
            hidden.append({"attribute": attribute, "reason": "missing"})
            continue
        try:
            mapped = bool(widget.winfo_ismapped())
            width = int(widget.winfo_width())
            height = int(widget.winfo_height())
        except Exception as exc:
            hidden.append(
                {"attribute": attribute, "reason": "unmeasurable", "error": str(exc)}
            )
            continue
        if not mapped or width <= 1 or height <= 1:
            hidden.append(
                {
                    "attribute": attribute,
                    "reason": "not_visible",
                    "mapped": mapped,
                    "size": [width, height],
                }
            )
    if surface == "main_window":
        for index, module_widget in enumerate(getattr(app, "module_widgets", [])):
            frame = getattr(module_widget, "frame", None)
            if frame is None or not frame.winfo_ismapped():
                hidden.append(
                    {
                        "attribute": f"module_widgets[{index}].frame",
                        "reason": "not_visible",
                    }
                )
    return hidden


def _run_single(
    profile: DeviceProfile,
    surface: str,
    output: Path,
    screenshots: Path | None,
) -> None:
    import tkinter as tk

    os.environ["GENREARCHIV_WRITE_MODE"] = "read-only"
    module_config = ROOT / "config" / "modules.json"
    gui_config = load_gui_config(ROOT / "config" / "launcher_gui.json")
    if surface == "launcher":
        factory = base._launcher_factory(module_config, gui_config)
    elif surface == "main_window":
        factory = base._main_window_factory(module_config, gui_config)
    else:
        raise ValueError(f"Unbekannte Oberfläche: {surface}")

    root = tk.Tk()
    root.geometry(f"{profile.width}x{profile.height}+0+0")
    root.update_idletasks()
    app = factory(root)
    root.geometry(f"{profile.width}x{profile.height}+0+0")
    record = base._measure(root, profile, surface)
    record["hidden_required_widgets"] = _hidden_required_widgets(app, surface)
    if screenshots is not None:
        base._capture(root, screenshots / f"{surface}__{profile.key}.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    # Der Prozess endet unmittelbar danach. Kein geteilter Tcl-Interpreter und kein
    # manuelles Löschen von Tkinter-intern verwalteten Callback-Kommandos.


def _child_command(
    profile: DeviceProfile,
    surface: str,
    output: Path,
    screenshots: Path | None,
) -> list[str]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--single-profile",
        profile.key,
        "--single-surface",
        surface,
        "--output",
        str(output),
    ]
    if screenshots is not None:
        command.extend(["--screenshots", str(screenshots)])
    return command


def _run_coordinator(
    selected_profiles: list[DeviceProfile],
    output: Path,
    screenshots: Path | None,
) -> None:
    records: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="genrearchiv-ui-probe-") as temp_dir:
        temp_root = Path(temp_dir)
        for profile in selected_profiles:
            for surface in ("launcher", "main_window"):
                record_path = temp_root / f"{profile.key}__{surface}.json"
                subprocess.run(
                    _child_command(profile, surface, record_path, screenshots),
                    check=True,
                    timeout=45,
                    env={**os.environ, "GENREARCHIV_WRITE_MODE": "read-only"},
                )
                record = json.loads(record_path.read_text(encoding="utf-8"))
                if not isinstance(record, dict):
                    raise RuntimeError(
                        f"Probe lieferte keinen Datensatz: {profile.key}/{surface}"
                    )
                records.append(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"schema_version": 1, "records": records}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument(
        "--profiles",
        nargs="*",
        default=[profile.key for profile in DEVICE_PROFILES],
    )
    parser.add_argument("--single-profile")
    parser.add_argument("--single-surface", choices=("launcher", "main_window"))
    args = parser.parse_args()

    if bool(args.single_profile) != bool(args.single_surface):
        parser.error("--single-profile und --single-surface müssen gemeinsam verwendet werden.")
    if args.single_profile:
        _run_single(
            _profile_by_key(args.single_profile),
            args.single_surface,
            args.output,
            args.screenshots,
        )
        # Interpreterbereinigung wird bewusst dem Prozessende überlassen.
        os._exit(0)

    selected_keys = {key.strip() for key in args.profiles if key.strip()}
    profiles = [profile for profile in DEVICE_PROFILES if profile.key in selected_keys]
    unknown = selected_keys - {profile.key for profile in profiles}
    if unknown:
        parser.error(f"Unbekannte Geräteprofile: {', '.join(sorted(unknown))}")
    _run_coordinator(profiles, args.output, args.screenshots)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
