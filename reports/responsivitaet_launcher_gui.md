# Responsivitäts-Check: Launcher-GUI

## Ziel
Prüfen, ob die Startübersicht bei kleinen Fenstergrößen bedienbar bleibt
(Responsivität = Anpassung an kleinere Bildschirmgrößen).

## Prüfumgebung
- GUI: `system/launcher_gui.py`
- Getestete Fenstergrößen:
  - 640×420 (Minimum)
  - 800×600 (kleines Standardfenster)

## Ergebnis (Kurzfassung)
- Bedienung bleibt möglich: **Ja**
- Alle Bedienelemente sind erreichbar: **Ja**
- Text bleibt lesbar, keine Überlappungen: **Ja**

## Beobachtungen
- Die Steuerleiste ist in zwei Reihen aufgeteilt, damit sie bei kleinen Breiten nicht abgeschnitten wird.
- Der Hinweistext im Footer bricht automatisch um, sodass er in schmalen Fenstern lesbar bleibt.
- Das Ausgabefeld wächst mit dem Fenster und bleibt fokussierbar.

## Empfehlung
- Bei Fenstern kleiner als 640×420 kann es eng werden. Empfehlung: Mindestgröße beibehalten.
- Für sehr kleine Displays könnte ein „kompakter Modus“ ergänzt werden (separate Aufgabe).
