# STRUKTUR (Verzeichnisbaum + Pflichtdateien)

Stand: 2026-01-26

## Zweck
Diese Datei ist die **Single Source of Truth** für den Projektaufbau.
Bitte **bei jeder neuen Datei/jedem neuen Ordner** aktualisieren.

## Hinweise
- **Pflichtdateien** sind hier explizit aufgeführt.
- **Dummy-Dateien** sind klar markiert und werden später automatisch ersetzt.
- **Vendor/Build-Verzeichnisse** (z. B. `node_modules/`) werden als Knoten gezeigt, Inhalte sind aus Platzgründen nicht aufgefächert.

## Dummy-Dateien (Platzhalter)
- `data/baumstruktur.txt` (DUMMY)
- `data/dummy_register.json` (DUMMY)
- `data/test_state.json` (DUMMY)
- `logs/start_run.log` (DUMMY)
- `logs/test_run.log` (DUMMY)

## Verzeichnisbaum
```
.
├── .github
│   └── workflows
│       └── ci.yml
├── config
│   ├── agent_rules.json
│   ├── black.toml
│   ├── charakter_modul.json
│   ├── datei_suche.json
│   ├── download_aufraeumen.json
│   ├── launcher_gui.json
│   ├── module_selftests.json
│   ├── modules.json
│   ├── notiz_editor.json
│   ├── pytest.ini
│   ├── records.json
│   ├── requirements.txt
│   ├── ruff.toml
│   ├── test_gate.json
│   ├── todo_config.json
│   └── todo_kalender.json
├── dashboard-timeline-tool
│   ├── projekt_dashboard_tool_react.jsx
│   └── projekt_dashboard_tool_react.txt
├── data
│   ├── log_exports
│   │   └── .gitkeep
│   ├── .gitkeep
│   ├── baumstruktur.txt
│   ├── dummy_register.json
│   ├── test_state.json
│   ├── todo_archive.txt
│   └── todo_kalender.json
├── docs
│   └── MODUL_API.md
├── gms-archiv-tool_v1.2.3_2026-01-06
│   ├── docs
│   │   ├── PROJECT.md
│   │   └── TOOL_GUIDE.md
│   ├── node_modules
│   ├── src
│   │   ├── config
│   │   │   └── modules.js
│   │   ├── system
│   │   │   └── startupChecks.js
│   │   ├── utils
│   │   │   └── logging.js
│   │   ├── App.jsx
│   │   ├── index.css
│   │   ├── main.jsx
│   │   └── selftest.js
│   ├── CHANGELOG.md
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.cjs
│   ├── README.md
│   ├── requirements.md
│   ├── tailwind.config.cjs
│   └── vite.config.js
├── logs
│   ├── .gitkeep
│   ├── start_run.log
│   └── test_run.log
├── modules
│   ├── beispiel_modul
│   │   ├── manifest.json
│   │   └── module.py
│   ├── charakter_modul
│   │   ├── manifest.json
│   │   └── module.py
│   ├── datei_suche
│   │   ├── manifest.json
│   │   └── module.py
│   ├── download_aufraeumen
│   │   ├── manifest.json
│   │   └── module.py
│   ├── notiz_editor
│   │   ├── manifest.json
│   │   └── module.py
│   ├── status
│   │   ├── manifest.json
│   │   └── module.py
│   └── todo_kalender
│       ├── manifest.json
│       └── module.py
├── reports
│   ├── kontrastpruefung_launcher_gui.md
│   └── responsivitaet_launcher_gui.md
├── scripts
│   ├── assign_agent.py
│   ├── bootstrap.sh
│   ├── check_env.sh
│   ├── generate_launcher_gui_contrast_report.py
│   ├── progress.js
│   ├── repo_basis_check.sh
│   ├── run_tests.sh
│   ├── show_standards.sh
│   ├── start.sh
│   ├── system_scan.sh
│   └── update_records.py
├── src
│   ├── core
│   │   ├── __init__.py
│   │   ├── agent_assignment.py
│   │   ├── data_model.py
│   │   ├── errors.py
│   │   └── todo_parser.py
│   ├── records
│   │   ├── __init__.py
│   │   └── record_updater.py
│   └── __init__.py
├── system
│   ├── color_utils.py
│   ├── config_models.py
│   ├── config_utils.py
│   ├── dependency_checker.py
│   ├── error_simulation.py
│   ├── filename_fixer.py
│   ├── health_check.py
│   ├── json_validator.py
│   ├── launcher.py
│   ├── launcher_gui.py
│   ├── log_exporter.py
│   ├── logging_center.py
│   ├── module_checker.py
│   ├── module_integration_checks.py
│   ├── module_loader.py
│   ├── module_registry.py
│   ├── module_selftests.py
│   ├── qa_checks.py
│   ├── standards_viewer.py
│   ├── store.py
│   ├── structure_checker.py
│   ├── test_gate.py
│   └── todo_manager.py
├── tests
│   ├── test_agent_assignment.py
│   ├── test_charakter_modul_module.py
│   ├── test_data_model.py
│   ├── test_datei_suche_module.py
│   ├── test_dependency_checker.py
│   ├── test_download_aufraeumen_module.py
│   ├── test_error_simulation.py
│   ├── test_filename_fixer.py
│   ├── test_json_validator.py
│   ├── test_launcher.py
│   ├── test_launcher_gui.py
│   ├── test_launcher_gui_contrast.py
│   ├── test_log_exporter.py
│   ├── test_module_checker.py
│   ├── test_module_integration_checks.py
│   ├── test_module_selftests.py
│   ├── test_notiz_editor_module.py
│   ├── test_qa_checks.py
│   ├── test_robustness_checks.py
│   ├── test_todo_kalender_module.py
│   └── test_todo_manager.py
├── .gitignore
├── AGENTS.md
├── ANALYSE_BERICHT.md
├── ANLEITUNG_TOOL.md
├── CHANGELOG.md
├── DEV_DOKU.md
├── DONE.md
├── klick_start.sh
├── PROGRESS.md
├── PROJEKT_INFO.md
├── README.md
├── standards.md
├── STYLEGUIDE.md
├── TODO.md
└── todo.txt
```
