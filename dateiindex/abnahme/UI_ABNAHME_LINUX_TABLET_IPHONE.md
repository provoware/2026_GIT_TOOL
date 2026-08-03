# UI-, Responsive-, Bedien- und Barrierefreiheitsabnahme

Stand: 2026-08-03  
Status: Automatisierte Abnahme eingerichtet; physische Geräteabnahme offen

## Geltungsbereich

- `system/launcher_gui.py`
- `system/main_window.py`
- Themes aus `config/launcher_gui.json`
- Maus-, Tastatur-, Fokus-, Touch- und Statusdarstellung
- Linux Desktop, Tablet-Viewports und iPhone-Viewports

## Verbindliche Statusbegriffe

- **Bestanden:** auf unterstützter Plattform automatisiert oder physisch geprüft.
- **Simuliert:** Viewport unter Linux/Xvfb vermessen; keine Aussage über echte Geräteintegration.
- **Blockiert:** Mindestgröße oder Plattform verhindert die geforderte Nutzung.
- **Physisch offen:** reale Hardware, Betriebssystemintegration und assistive Technik wurden noch nicht geprüft.

Eine Tablet- oder iPhone-Simulation darf niemals als physisch bestanden dokumentiert werden.

## Automatisierte Prüfschicht

Der Workflow `.github/workflows/ui-acceptance.yml` führt aus:

1. WCAG-AA-Kontrastprüfung aller Text-, Button- und Statuspaare.
2. Start von Launcher und Hauptfenster unter einem realen Tk/X11-Server via Xvfb.
3. Messung der angeforderten und tatsächlichen Fenstergröße.
4. Erkennung sichtbar aus dem Fenster ragender Widgets.
5. Erfassung fokussierbarer Bedienelemente.
6. Prüfung gemessener Touchziele gegen 44 × 44 Pixel.
7. Screenshots für jedes Geräteprofil und beide Fenster.
8. JSON- und Markdown-Abnahmebericht als Workflowartefakt.

## Geräteprofile

| Profil | Viewport | Art der Prüfung | Native Tk-Unterstützung |
|---|---:|---|---|
| Linux Desktop | 1440 × 900 | automatisiert + physisch erforderlich | ja |
| Linux kompakt | 1024 × 768 | automatisiert + physisch erforderlich | ja |
| Tablet quer | 1024 × 768 | Viewportsimulation + physisch erforderlich | nein |
| Tablet hoch | 768 × 1024 | Viewportsimulation + physisch erforderlich | nein |
| iPhone hoch | 390 × 844 | Viewportsimulation + physisch erforderlich | nein |
| iPhone quer | 844 × 390 | Viewportsimulation + physisch erforderlich | nein |

## Plattformgrenze

Tkinter ist eine Desktop-GUI und keine native Laufzeit für iOS, iPadOS oder Android. Eine echte iPhone-/Tablet-Freigabe setzt daher zuerst einen festgelegten mobilen Auslieferungsweg voraus, beispielsweise eine responsive Weboberfläche oder eine native App. Bis dahin sind mobile Ergebnisse ausschließlich Layoutsimulationen.

## Physische Linux-Abnahme

Für jeden Lauf dokumentieren:

- Distribution und Version
- Desktopumgebung und Skalierungsfaktor
- Bildschirmauflösung
- Python-/Tk-Version
- Maus- und Tastaturmodell beziehungsweise Eingabemethode
- Datum und Prüfer
- Screenshotnachweise

Prüfschritte:

- Start über `scripts/start.sh --safe-mode`
- vollständige Tab-Reihenfolge ohne Maus
- sichtbarer Fokus in allen Themes
- F1-Kontexthilfe an jedem primären Bedienelement
- alle Shortcuts einschließlich Undo/Redo
- Theme- und Kontrastwechsel
- Zoom von 80 bis 160 Prozent
- Verkleinern und Vergrößern beider Fenster
- Modulaktivierung und -deaktivierung
- Drag, Resize und Kollisionsblockierung
- Diagnose-/Wartungs-Busy-State
- Autosave-/Logoutbericht und kontrolliertes Schließen

## Physische Tablet-Abnahme

Erst nach Festlegung einer mobilen Laufzeit:

- Hoch- und Querformat
- Touchziele mindestens 44 × 44 Pixel
- keine horizontal abgeschnittenen Inhalte
- Bildschirmtastatur verdeckt keine Eingaben oder Aktionen
- Zoom und Betriebssystem-Schriftvergrößerung
- Wechsel zwischen Touch, externer Tastatur und gegebenenfalls Stift
- Fokusreihenfolge bei externer Tastatur
- Screenreader der Zielplattform

## Physische iPhone-Abnahme

Erst nach Bereitstellung einer iOS-kompatiblen Oberfläche:

- VoiceOver vollständig bedienbar
- Dynamic Type ohne abgeschnittene Texte
- Safe Areas und Displayaussparungen
- Hoch-/Querformat
- Touchziele mindestens 44 × 44 Punkte
- keine alleinige Farbcodierung von Statusinformationen
- sichtbare Fehlermeldungen mit konkreter Lösung
- reduzierte Bewegung und erhöhter Kontrast
- Wiederaufnahme nach Appwechsel und Bildschirmsperre

## Freigaberegel

Die Phase ist erst vollständig abgeschlossen, wenn:

1. der automatisierte Workflow grün ist,
2. die Linux-Abnahme auf realer Hardware dokumentiert ist,
3. ein mobiler Auslieferungsweg beschlossen und implementiert ist,
4. Tablet und iPhone auf realer Zielhardware geprüft wurden,
5. alle kritischen und wesentlichen Befunde geschlossen oder ausdrücklich akzeptiert sind.
