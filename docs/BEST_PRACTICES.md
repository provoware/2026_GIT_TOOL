# Best Practices (Standard)

## Allgemein
- Halte Funktionen klein und verständlich.
- Validiere Eingaben (Validation) und prüfe Rückgaben (Outputs).
- Nutze klare Fehlermeldungen.
- Trenne System-Standards (`config/system`) von Nutzer-Daten (`config/user`).

## Qualität
- Linting und Formatting vor jedem Release.
- Tests müssen vor dem Start erfolgreich sein.
- Nutze `npm run quality` für die komplette Prüfung.

## Barrierefreiheit (Accessibility)
- Hoher Kontrast und klare Fokus-Markierung.
- Buttons müssen per Tastatur erreichbar sein.
- ARIA-Attribute sinnvoll einsetzen.
