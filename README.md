# 2026_GIT_TOOL

## Kurzbeschreibung
Dieses Projekt ist ein sauberer Neuaufbau mit Fokus auf Robustheit, Nachvollziehbarkeit und Linux. Ziel ist ein barrierefreies Tool, das verständlich bleibt und klare Standards nutzt.

## Ist-Analyse (aktueller Stand)
- Es gibt noch keine ausführbare Anwendung, keine definierte Start-Routine und keine Tests.
- Die aktuelle Struktur ist minimal (Doku + Aufgabenliste). Es fehlen getrennte Ordner für Systemlogik, variable Daten und Konfiguration.
- Wichtige Qualitätsziele (Barrierefreiheit, Logging, automatische Prüfungen) sind dokumentiert, aber noch nicht implementiert.

## Ziele (in Arbeit)
- **Barrierefreiheit**: Tastaturbedienung, hoher Kontrast und verständliche Meldungen.
- **Automatische Startprüfung**: Start-Routine prüft Struktur, löst Abhängigkeiten und gibt Nutzer-Feedback.
- **Qualitätssicherung**: Automatische Tests und Codeformatierung (Codeformat = automatische Einheitlichkeit des Codes).
- **Trennung von Bereichen**: Systemlogik getrennt von variablen Dateien und Konfiguration.
- **Einheitliche Standards**: Klare Modul-Schnittstellen und gemeinsames Datenmodell.

## Schnellstart (aktuell nur Doku)
Derzeit gibt es noch kein ausführbares Startskript.

**Sobald die Start-Routine existiert, wird hier ein vollständiger Befehl stehen**, z. B.:
- `./start.sh` (Start-Routine = automatischer Projektstart mit Prüfungen und Feedback)

## Bedienung in einfacher Sprache
- **Starten**: Öffne die Projektdateien in deinem Editor. Eine Start-Routine wird später den Rest automatisch erledigen.
- **Fehler**: Fehlertexte sollen klar erklären, was passiert ist und was du tun kannst.
- **Tastatur**: Jede Funktion soll ohne Maus erreichbar sein.

## Barrierefreiheit und Kontrast
- Hoher Kontrast zwischen Text und Hintergrund.
- Deutliche Schaltflächen (Buttons) mit klarer Beschriftung.
- Mehrere Farbthemen (Themes) zur Auswahl (z. B. Hell, Dunkel, Kontrast).

## Logging und Debugging
- **Logging (Protokollierung)**: Jede Aktion soll protokolliert werden.
- **Debugging (Fehlersuche)**: Optionaler Modus mit mehr Details.

## Weiterführende Vorschläge für Laien
- Lies die Datei `todo.txt`, um die nächsten kleinen Schritte zu sehen.
- Nutze kurze, klare Commit-Nachrichten, z. B. „Doku: README erweitert“.
- Arbeite Schritt für Schritt: erst verstehen, dann ändern, dann testen.

## Dateiübersicht
- `README.md`: Einfache Projekt-Anleitung.
- `DEV_DOKU.md`: Entwickler-Dokumentation und Standards.
- `todo.txt`: Offene Aufgaben im Überblick.
- `CHANGELOG.md`: Änderungen je Version.

## Lizenz
Noch nicht festgelegt.
