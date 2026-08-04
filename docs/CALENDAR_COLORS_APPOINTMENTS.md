# Kalender: Farben, Termine und Erinnerungen

Provoware Memo verwendet weiterhin das bestehende Modul `todo_kalender` und die Datei `data/todo_kalender.json`. Aufgaben, Farblegende, Tagesmarkierungen, Termine und Erinnerungszustände liegen damit in einer gemeinsamen, rückwärtskompatiblen Datenablage.

## Farbübersicht

- Die Farblegende enthält genau fünf frei beschriftbare Farbfelder.
- Ein Datum kann mit einer bis vier Legendenfarben markiert werden.
- Die Legendentitel werden als Kurzinfo im Monatskalender angezeigt.
- Nicht mehr gültige Farbzuordnungen werden bei einer Legendenänderung kontrolliert entfernt.

## Termine

Termine unterstützen Datum, Ganztagsmodus, Start- und Endzeit, Ort, Notizen, eine optionale Legendenfarbe und eine Erinnerung zwischen dem Terminzeitpunkt und sieben Tagen vorher. Bearbeiten und Löschen erfolgen innerhalb der integrierten Browseroberfläche; es wird kein separates Fenster geöffnet.

## Erinnerungen

Der lokale Server liefert fällige und bevorstehende Erinnerungen. Die Oberfläche prüft sie regelmäßig, zeigt sie im Kalender und Footer an und kann nach ausdrücklicher Browserfreigabe Chrome-Benachrichtigungen erzeugen. Eine bestätigte Erinnerung bleibt gespeichert und wird nicht erneut angezeigt, bis der Termin oder Erinnerungszeitpunkt geändert wird.

## Header-Monatskalender

Der kompakte Monatskalender bleibt im Header-Dashboard sichtbar. Er zeigt den aktuellen Monat, Tagesmarkierungen sowie vorhandene Aufgaben oder Termine. Ein Klick auf ein Datum öffnet denselben Tag im vollständigen Kalender.
