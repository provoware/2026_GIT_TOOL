#!/usr/bin/env python3
"""Export-Center: JSON, TXT, PDF und ZIP in einem Schritt."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence
from zipfile import ZIP_DEFLATED, ZipFile

from config_utils import ensure_path, load_json


class ExportCenterError(Exception):
    """Fehler im Export-Center."""


@dataclass(frozen=True)
class ExportConfig:
    output_dir: Path
    sources: List[Path]
    report_base_name: str
    include_extensions: List[str]
    enabled_formats: List[str]


@dataclass(frozen=True)
class ExportResult:
    report_paths: List[Path]
    zip_path: Path | None
    created_at: datetime


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExportCenterError(f"{label} fehlt oder ist leer.")
    return value.strip()


def _require_list(value: object, label: str) -> List:
    if not isinstance(value, list):
        raise ExportCenterError(f"{label} ist keine Liste.")
    return value


def _require_extensions(values: object, label: str) -> List[str]:
    items = _require_list(values, label)
    extensions: List[str] = []
    for item in items:
        text = _require_text(item, label)
        if not text.startswith("."):
            raise ExportCenterError(f"{label} enthält keine Dateiendung: {text}")
        extensions.append(text.lower())
    return extensions


def _require_formats(values: object, label: str) -> List[str]:
    items = _require_list(values, label)
    formats: List[str] = []
    allowed = {"json", "txt", "pdf", "zip"}
    for item in items:
        text = _require_text(item, label).lower()
        if text not in allowed:
            raise ExportCenterError(f"{label} enthält unbekanntes Format: {text}")
        formats.append(text)
    if not formats:
        raise ExportCenterError(f"{label} ist leer.")
    return formats


def load_export_config(path: Path) -> ExportConfig:
    ensure_path(path, "config_path", ExportCenterError)
    data = load_json(
        path,
        ExportCenterError,
        "Export-Center-Konfiguration fehlt",
        "Export-Center-Konfiguration ungültig",
    )
    output_dir = Path(_require_text(data.get("output_dir"), "output_dir"))
    sources_raw = _require_list(data.get("sources"), "sources")
    sources = [Path(_require_text(item, "sources")) for item in sources_raw]
    report_base = _require_text(data.get("report_base_name"), "report_base_name")
    include_ext = _require_extensions(data.get("include_extensions"), "include_extensions")
    formats = _require_formats(data.get("enabled_formats"), "enabled_formats")
    return ExportConfig(
        output_dir=output_dir,
        sources=sources,
        report_base_name=report_base,
        include_extensions=include_ext,
        enabled_formats=formats,
    )


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _collect_files(sources: Iterable[Path], include_extensions: Sequence[str]) -> List[Path]:
    files: List[Path] = []
    for source in sources:
        if not source.exists():
            continue
        if source.is_file():
            files.append(source)
            continue
        for path in source.rglob("*"):
            if path.is_file() and path.suffix.lower() in include_extensions:
                files.append(path)
    return sorted(files)


def _build_report(files: Iterable[Path], sources: Iterable[Path]) -> dict:
    items = []
    for path in files:
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            size = 0
        items.append(
            {
                "path": str(path),
                "size_bytes": size,
            }
        )
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sources": [str(path) for path in sources],
        "file_count": len(items),
        "files": items,
    }


def _build_export_path(output_dir: Path, base_name: str, suffix: str) -> Path:
    ensure_path(output_dir, "output_dir", ExportCenterError)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate = output_dir / f"{base_name}_{_timestamp()}{suffix}"
    return candidate


def export_json(report: dict, output_dir: Path, base_name: str) -> Path:
    path = _build_export_path(output_dir, base_name, ".json")
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def export_txt(report: dict, output_dir: Path, base_name: str) -> Path:
    path = _build_export_path(output_dir, base_name, ".txt")
    lines = [
        "Export-Center Bericht",
        f"Zeitpunkt: {report.get('created_at', '-')}",
        f"Dateien: {report.get('file_count', 0)}",
        "Quellen:",
    ]
    for source in report.get("sources", []):
        lines.append(f"- {source}")
    lines.append("")
    lines.append("Dateiliste:")
    for item in report.get("files", []):
        lines.append(f"- {item.get('path')} ({item.get('size_bytes', 0)} Bytes)")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def export_pdf(report: dict, output_dir: Path, base_name: str) -> Path:
    path = _build_export_path(output_dir, base_name, ".pdf")
    text_lines = [
        "Export-Center Bericht",
        f"Zeitpunkt: {report.get('created_at', '-')}",
        f"Dateien: {report.get('file_count', 0)}",
        "Quellen:",
    ]
    for source in report.get("sources", []):
        text_lines.append(f"- {source}")
    text_lines.append("")
    text_lines.append("Dateiliste:")
    for item in report.get("files", []):
        text_lines.append(f"- {item.get('path')} ({item.get('size_bytes', 0)} Bytes)")
    pdf_content = _build_simple_pdf("\n".join(text_lines))
    path.write_bytes(pdf_content)
    return path


def _build_simple_pdf(text: str) -> bytes:
    if not isinstance(text, str) or not text.strip():
        raise ExportCenterError("PDF-Text fehlt oder ist leer.")

    def _escape(value: str) -> str:
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    lines = text.splitlines()
    content_lines = ["BT", "/F1 12 Tf", "72 760 Td"]
    for index, line in enumerate(lines):
        if index > 0:
            content_lines.append("0 -14 Td")
        content_lines.append(f"({_escape(line)}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines)
    objects = []
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")
    objects.append(
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj"
    )
    objects.append(
        f"4 0 obj\n<< /Length {len(stream.encode('utf-8'))} >>\nstream\n"
        f"{stream}\nendstream\nendobj"
    )
    objects.append("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")
    xref_positions = []
    output = "%PDF-1.4\n".encode("utf-8")
    for obj in objects:
        xref_positions.append(len(output))
        output += (obj + "\n").encode("utf-8")
    xref_start = len(output)
    output += f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode("utf-8")
    for pos in xref_positions:
        output += f"{pos:010d} 00000 n \n".encode("utf-8")
    output += (
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\n" f"startxref\n{xref_start}\n%%EOF\n"
    ).encode("utf-8")
    return output


def export_zip(files: Iterable[Path], output_dir: Path, base_name: str) -> Path:
    path = _build_export_path(output_dir, base_name, ".zip")
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        for file_path in files:
            archive.write(file_path, arcname=str(file_path))
    if not path.exists():
        raise ExportCenterError("ZIP-Export konnte nicht erstellt werden.")
    return path


def run_export(config: ExportConfig) -> ExportResult:
    if not isinstance(config, ExportConfig):
        raise ExportCenterError("config ist keine ExportConfig.")
    files = _collect_files(config.sources, config.include_extensions)
    report = _build_report(files, config.sources)
    report_paths: List[Path] = []
    zip_path: Path | None = None
    base_name = config.report_base_name
    if "json" in config.enabled_formats:
        report_paths.append(export_json(report, config.output_dir, base_name))
    if "txt" in config.enabled_formats:
        report_paths.append(export_txt(report, config.output_dir, base_name))
    if "pdf" in config.enabled_formats:
        report_paths.append(export_pdf(report, config.output_dir, base_name))
    if "zip" in config.enabled_formats:
        zip_path = export_zip(files, config.output_dir, base_name)
    return ExportResult(
        report_paths=report_paths,
        zip_path=zip_path,
        created_at=datetime.now(timezone.utc),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export-Center: JSON/TXT/PDF/ZIP erzeugen.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "config" / "export_center.json",
        help="Pfad zur Export-Center-Konfiguration (JSON).",
    )
    parser.add_argument(
        "--formats",
        nargs="*",
        default=None,
        help="Optional: Formate überschreiben (json txt pdf zip).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = load_export_config(args.config)
    if args.formats:
        config = ExportConfig(
            output_dir=config.output_dir,
            sources=config.sources,
            report_base_name=config.report_base_name,
            include_extensions=config.include_extensions,
            enabled_formats=_require_formats(args.formats, "formats"),
        )
    try:
        result = run_export(config)
    except ExportCenterError as exc:
        logging.error("Export-Center Fehler: %s", exc)
        print(f"Fehler: {exc}")
        return 1
    for path in result.report_paths:
        print(f"Report erstellt: {path}")
    if result.zip_path is not None:
        print(f"ZIP erstellt: {result.zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
