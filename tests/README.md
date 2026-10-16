# Tests der Garagen-App

Automatische Tests mit Playwright (Chromium, 390×844, Touch, de-AT). Sie starten selbst einen lokalen Server und
legen für jeden Test eine frische Datenbank an – echte Daten werden nie berührt.

```sh
sh tests/run_all.sh          # alles
python3 tests/test_logic.py  # nur Rechnungen
```

| Datei | prüft |
|---|---|
| `test_release.py` | Version in `sw.js` = `APP_VER` in `index.html`, Dateien für den Offline-Cache |
| `test_logic.py` | Zahlen mit Komma, Strings statt Zahlen, Verbrauch, Bilanz, Pickerl (alt/neu ab 19.5.2027), fremde Autos, Werkzeug-Ersparnis, Lagerwert, Prognose, Jahresrückblick |
| `test_nav.py` | Android-Zurück (Fenster, Bild, Zuschneiden, Beschriften), Wischen am Titel, Aktualisieren, Kaltstart, QR-Link |
| `test_backup.py` | Backup → Wiederherstellen ergibt dieselben Daten; kaputte Datei löscht nichts |
| `test_ux.py` | Bedienung: Rückgängig, eigene Fenster, Lager-Verlauf, Regal/Rolltor, Werkstatt-Raum (Antippen, Zurück, Schalter), Tippflächen |
| `test_robust.py` | Eingaben-Rückgängig, Tastatur, Fehleransicht, Update-Hinweis |
| `test_perf.py` | Tempo mit 1.500 Einträgen, 400 Tankungen, 330 Fotos |
| `crawl.py` | Screenshots aller Seiten und Fenster (`python3 tests/crawl.py dark 390 demo`) |
| `montage.py` | fasst Screenshots zu Übersichtsbildern zusammen |

Bei jedem Release nur `APP_VER` in `index.html` hochzählen – `sw.js` übernimmt die Version automatisch (`sw.js?v=…`).
