# Bundesliga FHD/WQHD – Git- und openATV-Feed-Aufbau

Diese Fassung arbeitet wie `GradientFHD`: Im Git liegen nur die Paketquellen.
Die IPKs werden mit `SRCREV = "${AUTOREV}"` durch das OE-/openATV-Buildsystem
erzeugt. Für normale Änderungen wird lokal keine IPK gebaut.

## 1. Diese fünf Ordner ins Skins-for-openATV Git kopieren

Direkt nach `G:\Mein Git\Skins-for-openATV\` kopieren:

- `BundesligaInstaller`
- `BundesligaFHD`
- `BundesligaWQHD`
- `BundesligaFHD-teams`
- `BundesligaWQHD-teams`

Optional kann diese Anleitung zusätzlich als `README_Bundesliga_Feed.md` ins
Repository kopiert werden. Den Ordner `oe-alliance-bb` nicht in diese fünf
Paketordner mischen; er enthält Vorlagen für das separate OE-Git.

## 2. Die drei BB-Dateien gehören ins OE-Git

Die Vorlagen aus `oe-alliance-bb` gehören im OE-Alliance-Repository nach:

`meta-oe/recipes-distros/openatv/plugins/`

- `enigma2-plugin-extensions-bundesligainstaller.bb`
- `enigma2-plugin-skins-bundesligafhd.bb`
- `enigma2-plugin-skins-bundesligawqhd.bb`

Nach Aufnahme dieser Rezepte baut der Feed automatisch folgende Pakete:

- `enigma2-plugin-extensions-bundesligainstaller`
- `enigma2-plugin-skins-bundesligafhd`
- `enigma2-plugin-skins-bundesligawqhd`

## 3. Dein normaler Support-Workflow

### XML oder Datei im Skin ändern

Beispiel:

`BundesligaFHD/usr/share/enigma2/BundesligaFHD/skin.xml`

oder:

`BundesligaWQHD/usr/share/enigma2/BundesligaWQHD/icons/mein_icon.png`

Danach nur noch:

```bash
cd "/g/Mein Git/Skins-for-openATV"
git switch python3
git pull --ff-only origin python3
git add -- BundesligaFHD BundesligaWQHD BundesligaInstaller
git commit -m "Update Bundesliga skins"
git push origin python3
```

Der OE-Feed baut die neuen Pakete aus dem aktuellen Git-Stand. Eine manuelle
IPK und eine manuelle Versionsänderung sind nicht nötig.

### Bild eines ausgelagerten Vereins ersetzen

Beispiel FHD Borussia Dortmund:

`BundesligaFHD-teams/Verein/Borussia_Dortmund/`

Beispiel WQHD Hertha BSC:

`BundesligaWQHD-teams/Verein/Hertha_BSC/`

Das vorhandene Bild unter demselben Dateinamen ersetzen und committen:

```bash
git add -- BundesligaFHD-teams BundesligaWQHD-teams
git commit -m "Update Bundesliga team images"
git push origin python3
```

Neue Installationen laden sofort die neue Datei. Auf einer Box mit bereits
installiertem Verein: Bundesliga-Konfiguration öffnen, BLAU `Vereine`, Verein
markieren und BLAU `Aktualisieren` drücken.

Solange der Dateiname gleich bleibt, müssen weder ZIP, IPK, Katalog noch
Prüfsumme neu erzeugt werden. Nur beim Hinzufügen, Löschen oder Umbenennen einer
benötigten Vereinsdatei muss außerdem die jeweilige Datei
`team_assets/catalog.json` im Skin angepasst werden.

## 4. Git Bash – erste Veröffentlichung

```bash
cd "/g/Mein Git/Skins-for-openATV"
git switch python3
git pull --ff-only origin python3
git status
git add -- BundesligaInstaller BundesligaFHD BundesligaWQHD BundesligaFHD-teams BundesligaWQHD-teams README_Bundesliga_Feed.md
git commit -m "Add Bundesliga FHD WQHD feed installer and team downloads"
git push origin python3
```

## 5. Verhalten auf der Box

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
