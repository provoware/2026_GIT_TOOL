# Provoware GitHub Workflow Dispatch MCP

Eine eng begrenzte MCP-App mit genau einem schreibenden Tool:

`dispatch_workflow_on_main(repository, workflow, inputs)`

## Sicherheitsvertrag

- `ref` ist kein Toolargument und intern unveränderlich auf `main` gesetzt.
- Nur in der lokalen JSON-Allowlist eingetragene Repositories und Workflowdateien sind erlaubt.
- Der Workflow muss unter `.github/workflows/<datei>` auf `main` existieren und aktiv sein.
- Unbekannte Inputs, fehlende Pflichtinputs und ungültige Formate werden vor dem API-Aufruf abgelehnt.
- Workflowdateien dürfen nur einfache `.yml`- oder `.yaml`-Dateinamen sein; keine Pfade oder URLs.
- GitHub-API-Ziel ist fest auf `https://api.github.com` gesetzt.
- Token und Inputwerte werden weder zurückgegeben noch protokolliert.
- Der GitHub-Token benötigt ausschließlich Repositoryberechtigung **Actions: write** sowie Leserechte für Repositoryinhalt und Metadaten.

GitHub stellt dafür `POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches` bereit. Die App sendet ausschließlich `ref: main` und die nach Allowlist validierten Inputs.

## Installation

```bash
cd mcp_dispatch
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp config/dispatch_allowlist.example.json config/dispatch_allowlist.json
export GITHUB_TOKEN='...'
provoware-github-dispatch-mcp
```

Streamable-HTTP-Endpunkt: `http://127.0.0.1:8000/mcp`

## Token

Empfohlen wird ein GitHub-App-Installationstoken oder ein feingranulares Token mit minimalem Repositoryzugriff. Der Token wird ausschließlich über `GITHUB_TOKEN` eingelesen und niemals in Konfigurationsdateien gespeichert.

## Allowlist

Die Allowlist steuert Repository, Workflow und jedes einzelne Inputformat. Das mitgelieferte Beispiel erlaubt ausschließlich:

- Repository `provoware/PROVOWARE_VIDEO_AUTOMATION_2026`
- Workflow `kubuntu-pr-validation.yml`
- die fünf SHA-gebundenen Abnahmeinputs

Für produktive Nutzung wird die Beispieldatei nach `config/dispatch_allowlist.json` kopiert und bewusst geprüft.

## Prüfung

```bash
pytest
ruff check src tests
python -m compileall -q src tests
```

## ChatGPT-Einbindung

Die App wird als benutzerdefinierte MCP-App mit dem Streamable-HTTP-Endpunkt verbunden. Die eingebaute GitHub-App wird dadurch nicht verändert; die neue App ergänzt ausschließlich das eng begrenzte Dispatch-Tool.
