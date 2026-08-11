# Bundesliga FHD/WQHD – zwei Feed-Pakete mit Auflösungswechsel

Diese Fassung benötigt genau zwei BB-Dateien: eine für FHD und eine für WQHD.
Ein drittes Installer-Paket ist nicht mehr nötig. Der Wechsel der Auflösung ist
direkt in beiden Bundesliga-Config-Menüs eingebaut.


Der Ordner `oe-alliance-bb` enthält nur die Vorlagen für Captain und gehört
nicht in einen der vier Paketordner.

## 1. Genau zwei BB-Dateien für das OE-Git

Aus `oe-alliance-bb`:

- `enigma2-plugin-skins-bundesligafhd.bb`
- `enigma2-plugin-skins-bundesligawqhd.bb`


## 2. Verhalten auf der Box

- Das Config-Menü zeigt eindeutig `Aktiver Skin: Bundesliga FHD` oder
  `Aktiver Skin: Bundesliga WQHD`.
- Direkt darunter steht nur die mögliche Aktion zum Wechsel auf die andere
  Auflösung. Es werden nicht mehr beide Varianten als „installiert“ angezeigt.
- Beim Wechsel wird zuerst das Zielpaket installiert und geprüft.
- Verein, individuelle Farben und Skinparts werden auf das Ziel übertragen.
- Erst nach erfolgreicher Aktivierung wird das bisherige Skin-Paket entfernt.
- Schlägt die Installation fehl, bleibt der bisherige Skin aktiv und erhalten.
- Beim Entfernen werden Skin, Config-Plugin sowie die eigenen Converter und
  Renderer vollständig gelöscht.
- Gemeinsame Altdateien aus Version 1.2 werden erst beim letzten Bundesliga-
  Skin entfernt, damit eine noch vorhandene alte Installation funktionsfähig
  bleibt.

FHD und WQHD besitzen ab Version 1.3 eigene Komponentennamen (`BLFHD…` und
`BLWQHD…`). Dadurch überschreibt keine Variante mehr Dateien der anderen.


## 3. Normaler Git-Support

XML, Python-Datei oder Icon wie bisher direkt im passenden Git-Ordner ändern.
Danach:

```bash
cd "/g/Mein Git/Skins-for-openATV"
git switch python3
git pull --ff-only origin python3
git add -- BundesligaFHD BundesligaWQHD BundesligaFHD-teams BundesligaWQHD-teams README_Bundesliga_Feed.md
git commit -m "Update Bundesliga FHD WQHD"
git push origin python3
```

Der Feed baut durch `SRCREV = "${AUTOREV}"` aus dem aktuellen Git-Stand. Für
normale Skin-Änderungen muss keine IPK von Hand gebaut werden.

Bei einem Icon-Austausch in einem ausgelagerten Vereinsordner bleibt der
Dateiname gleich. Anschließend reicht ebenfalls Commit und Push. Bereits
installierte Vereine lassen sich in der Bundesliga-Konfiguration über
`BLAU – Vereine – BLAU – Aktualisieren` neu aus GitHub laden.


## 4. Verhalten auf der Box

- Der Auswahl-Installer fragt FHD oder WQHD ab.
- Er installiert den Skin über dessen Paketnamen vom openATV-Feed.
- Beim Wechsel installiert er zuerst den neuen Skin und entfernt danach den
  bisherigen Skin. Schlägt die neue Installation fehl, bleibt der alte Skin
  erhalten.
- Nur FC Bayern München ist im Feed-Paket enthalten.
- Bei einem fehlenden Verein fragt das Plugin vor dem Download.
- Ein bereits installierter anderer Verein kann behalten oder durch den neuen
  Verein ersetzt werden.
- Die großen Vereinsbilder werden als normale Dateien direkt aus dem
  `python3`-Branch geladen.
