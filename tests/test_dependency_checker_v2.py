from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "system"))

import dependency_checker as checker  # noqa: E402


def test_distribution_and_import_names_are_separate() -> None:
    assert checker.distribution_name("Pillow>=10.4.0") == "Pillow"
    assert checker.import_name("Pillow") == "PIL"
    assert checker.import_name("some-package") == "some_package"


def test_requirements_reader_ignores_comments(tmp_path: Path) -> None:
    path = tmp_path / "requirements.txt"
    path.write_text(
        "# comment\nPillow>=10.4.0  # image preview\npytest>=8\n",
        encoding="utf-8",
    )
    assert checker.read_requirements(path) == ["Pillow>=10.4.0", "pytest>=8"]


def test_validation_reports_missing_distribution(monkeypatch) -> None:
    monkeypatch.setattr(checker, "installed", lambda name: (False, "nicht installiert"))
    results = checker.validate(["Pillow>=10.4.0"])
    assert results[0].distribution == "Pillow"
    assert results[0].import_name == "PIL"
    assert results[0].status == "missing"


def test_validation_reports_successful_import(monkeypatch) -> None:
    monkeypatch.setattr(checker, "installed", lambda name: (True, "10.4.0"))
    monkeypatch.setattr(checker.importlib, "import_module", lambda name: object())
    results = checker.validate(["Pillow>=10.4.0"])
    assert results[0].status == "ok"
