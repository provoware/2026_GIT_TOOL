# Protokolle

Dieser Ordner enthält ausschließlich lokal erzeugte Laufzeit- und Diagnoseprotokolle.

## Wichtige Dateien

- `tool.log`: zentrale, rotierende Laufzeitprotokollierung
- `start_run.log`: Ausgabe der Startprüfung, sobald `scripts/start.sh` ausgeführt wird
- `test_run.log`: Ausgabe der lokalen Testprüfung
- `autosave.log`: Meldungen der automatischen Sicherung, sofern aktiviert

Die eigentlichen Logdateien werden nicht versioniert und nicht in Release-ZIPs übernommen. Bei einer Supportanfrage können die benötigten Dateien gezielt aus diesem Ordner kopiert werden.

Alte rotierte Dateien heißen beispielsweise `tool.log.1`. Sie können bei beendetem Tool gelöscht werden.
