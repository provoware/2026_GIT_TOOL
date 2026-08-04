#!/usr/bin/env python3
"""Resolve, install and validate all declared Provoware Memo Python dependencies."""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")
IMPORT_NAMES = {
    "pillow": "PIL",
    "pytest": "pytest",
    "ruff": "ruff",
    "black": "black",
}


class DependencyError(RuntimeError):
    """Controlled dependency resolution failure."""


@dataclass(frozen=True)
class Result:
    requirement: str
    distribution: str
    import_name: str
    status: str
    detail: str


def read_requirements(path: Path) -> list[str]:
    if not path.is_file():
        raise DependencyError(f"Requirements-Datei fehlt: {path}")
    items: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = re.split(r"\s+#", line, maxsplit=1)[0].strip()
        if line.startswith(("-r", "--requirement")):
            raise DependencyError(
                "Verschachtelte Requirements sind in der Startroutine nicht zulässig."
            )
        items.append(line)
    return items


def distribution_name(requirement: str) -> str:
    match = NAME_RE.match(requirement)
    if not match:
        raise DependencyError(f"Ungültige Requirement-Angabe: {requirement}")
    return match.group(0)


def import_name(distribution: str) -> str:
    normalized = distribution.casefold().replace("_", "-")
    return IMPORT_NAMES.get(normalized, distribution.replace("-", "_"))


def installed(distribution: str) -> tuple[bool, str]:
    try:
        return True, importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return False, "nicht installiert"


def ensure_pip() -> None:
    probe = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode == 0:
        return
    repair = subprocess.run(
        [sys.executable, "-m", "ensurepip", "--upgrade"],
        capture_output=True,
        text=True,
        check=False,
    )
    if repair.returncode != 0:
        detail = repair.stderr.strip() or repair.stdout.strip()
        raise DependencyError(f"Pip konnte nicht repariert werden: {detail}")


def install(requirements: Path) -> None:
    commands = [
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "-r",
            str(requirements),
        ],
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--prefer-binary",
            "-r",
            str(requirements),
        ],
    ]
    messages: list[str] = []
    for command in commands:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode == 0:
            return
        messages.append(completed.stderr.strip() or completed.stdout.strip())
    detail = " | ".join(message for message in messages if message)
    raise DependencyError(f"Installation fehlgeschlagen: {detail}")


def validate(requirements: list[str]) -> list[Result]:
    results: list[Result] = []
    for requirement in requirements:
        distribution = distribution_name(requirement)
        module = import_name(distribution)
        is_installed, version = installed(distribution)
        if not is_installed:
            results.append(
                Result(requirement, distribution, module, "missing", version)
            )
            continue
        try:
            importlib.import_module(module)
        except Exception as exc:
            results.append(
                Result(
                    requirement,
                    distribution,
                    module,
                    "broken",
                    f"{type(exc).__name__}: {exc}",
                )
            )
        else:
            results.append(Result(requirement, distribution, module, "ok", version))
    return results


def pip_check() -> tuple[bool, str]:
    completed = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        check=False,
    )
    text = (completed.stdout or completed.stderr).strip()
    return completed.returncode == 0, text or "keine Konflikte"


def write_report(
    path: Path | None,
    results: list[Result],
    graph_ok: bool,
    graph_detail: str,
) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "product": "Provoware Memo",
        "ok": all(item.status == "ok" for item in results) and graph_ok,
        "results": [asdict(item) for item in results],
        "pip_check": {"ok": graph_ok, "detail": graph_detail},
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Provoware-Memo-Abhängigkeitsauflösung"
    )
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)

    try:
        requirements = read_requirements(args.requirements)
        ensure_pip()
        results = validate(requirements)
        if any(item.status != "ok" for item in results) and not args.check_only:
            print(
                "Abhängigkeiten: Fehlende oder beschädigte Pakete werden "
                "automatisch repariert."
            )
            install(args.requirements)
            importlib.invalidate_caches()
            results = validate(requirements)

        graph_ok, graph_detail = pip_check()
        if not graph_ok and not args.check_only:
            install(args.requirements)
            importlib.invalidate_caches()
            results = validate(requirements)
            graph_ok, graph_detail = pip_check()

        write_report(args.report, results, graph_ok, graph_detail)
        for item in results:
            print(
                f"Abhängigkeit {item.distribution} / Import {item.import_name}: "
                f"{item.status.upper()} — {item.detail}"
            )
        print(
            f"Abhängigkeitsgraph: {'OK' if graph_ok else 'FEHLER'} — "
            f"{graph_detail}"
        )
        if any(item.status != "ok" for item in results) or not graph_ok:
            raise DependencyError(
                "Nachvalidierung der Abhängigkeiten ist fehlgeschlagen."
            )
        print("Abhängigkeiten: vollständig installiert und nachvalidiert.")
        return 0
    except DependencyError as exc:
        print(f"Abhängigkeiten: FEHLER — {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
