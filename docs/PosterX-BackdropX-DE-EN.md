# 🖼️ PosterX & BackdropX – Dokumentation (DE/EN)

> **Datei-ID:** 🖼️ PosterX & BackdropX – Dokumentation (DE/EN)

# PosterX / BackdropX for Enigma2 (GradientFHD)  
**AutoDB • Live Search • Custom Artwork • Slug Export • Storage Path**  

> ✅ **DE/EN Doppel-README in einer Datei**  
> Diese README erklärt die Funktionen **PosterX / BackdropX** inkl. AutoDB, API-Keys, Speicherpfad, Slug-Export und Custom-Ordner.

---

## Inhaltsverzeichnis / Table of Contents

- [🇩🇪 Deutsch](#-deutsch)
  - [1. Überblick](#1-überblick)
  - [2. Was wird wo gespeichert](#2-was-wird-wo-gespeichert)
  - [3. AutoDB: Was ist das und wie läuft es](#3-autodb-was-ist-das-und-wie-läuft-es)
  - [4. AutoDB: Start, Laufzeit, Abbruch](#4-autodb-start-laufzeit-abbruch)
  - [5. Was wird automatisch gelöscht (Cleanup)](#5-was-wird-automatisch-gelöscht-cleanup)
  - [6. Bleiben Poster/Backdrops für Aufnahmen erhalten](#6-bleiben-posterbackdrops-für-aufnahmen-erhalten)
  - [7. API-Keys einstellen](#7-api-keys-einstellen)
  - [8. PosterX Speicherpfad auswählen](#8-posterx-speicherpfad-auswählen)
  - [9. Slugs auslesen (PosterX/BackdropX)](#9-slugs-auslesen-posterxbackdropx)
  - [10. Custom Artwork verwenden](#10-custom-artwork-verwenden)
  - [11. Was passiert nach einem neuen AutoDB Scan](#11-was-passiert-nach-einem-neuen-autodb-scan)
  - [12. Manuell Poster/Backdrops finden (Quellen)](#12-manuell-posterbackdrops-finden-quellen)
  - [13. Fehlerdiagnose (Logs)](#13-fehlerdiagnose-logs)
  - [14. FAQ](#14-faq)
- [🇬🇧 English](#-english)
  - [1. Overview](#1-overview)
  - [2. Storage layout](#2-storage-layout)
  - [3. AutoDB: What it is and how it works](#3-autodb-what-it-is-and-how-it-works)
  - [4. AutoDB: Start, runtime, stop](#4-autodb-start-runtime-stop)
  - [5. What gets deleted automatically (cleanup)](#5-what-gets-deleted-automatically-cleanup)
  - [6. Do posters/backdrops for recordings remain](#6-do-postersbackdrops-for-recordings-remain)
  - [7. API keys](#7-api-keys)
  - [8. PosterX storage path](#8-posterx-storage-path)
  - [9. Read slugs (PosterX/BackdropX)](#9-read-slugs-posterxbackdropx)
  - [10. Using custom artwork](#10-using-custom-artwork)
  - [11. What happens on the next AutoDB scan](#11-what-happens-on-the-next-autodb-scan)
  - [12. Where to find artwork manually (sources)](#12-where-to-find-artwork-manually-sources)
  - [13. Troubleshooting (logs)](#13-troubleshooting-logs)
  - [14. FAQ](#14-faq-1)

---

# 🇩🇪 Deutsch

## 1. Überblick

PosterX / BackdropX erweitert Enigma2 (GradientFHD) um:

- 🖼️ **Poster & Backdrops** für EPG/Live-TV, Senderliste, SecondInfoBar, Player usw.
- ⚙️ **AutoDB**: automatisches Vorladen/Scannen von Sendern und Speichern der Bilder
- 🔑 **API-Keys**: bessere Treffer mit eigenen Keys (TMDb/TVDb/Fanart)
- 💾 **Speicherpfad** frei wählbar (HDD / USB / NAS)
- 🧩 **Custom Artwork**: eigene Poster/Backdrops dauerhaft nutzen (ohne Auto-Löschung)
- 🧾 **Slug-Export**: Slugs automatisch in JSON exportieren (für Custom-Dateien)

---

## 2. Was wird wo gespeichert

Alles liegt unter dem ausgewählten **BASE-Pfad** (Standard: `/media/hdd`) im Ordner:

```
<BASE>/xtra/
```

### Ordnerstruktur

```
<BASE>/xtra/poster/           # Poster-Bilder (*.jpg)
<BASE>/xtra/backdrop/         # Backdrop-Bilder (*.jpg)
<BASE>/xtra/Info/             # Info/Rating/IDs (json)
<BASE>/xtra/poster_info/      # Download-Herkunft & Provider-Infos (json)
<BASE>/xtra/backdrop_info/    # Download-Herkunft & Provider-Infos (json)

<BASE>/xtra/custom/poster/    # Eigene Poster (werden NICHT gelöscht)
<BASE>/xtra/custom/backdrop/  # Eigene Backdrops (werden NICHT gelöscht)

<BASE>/xtra/PosterX_slugs.json
<BASE>/xtra/BackdropX_slugs.json
```

---

## 3. AutoDB: Was ist das und wie läuft es

AutoDB scannt regelmäßig (oder per Start) Sender/Bouquets, liest EPG-Titel und lädt automatisch:

- passende **Poster**
- passende **Backdrops**
- zusätzliche **Info-Daten** (IDs, Rating, Provider-Quelle)

Damit werden Bilder später sofort angezeigt (z.B. in der Senderliste/SecondInfoBar/Player), ohne dass erst im Hintergrund gesucht werden muss.

### Provider-Reihenfolge (vereinfachtes Prinzip)

Je nach Inhalt wird eine sinnvolle Reihenfolge genutzt, z.B.:

- 🎬 **Movies** → TMDb zuerst (oft beste Filmtreffer)
- 📺 **Serien** → TVDb zuerst (oft besser für Serien)
- Spezialfälle können Overrides nutzen (z.B. RTL Daily Shows)

---

## 4. AutoDB: Start, Laufzeit, Abbruch

### Start
AutoDB kann über das Plugin-Menü gestartet werden.  
Je nach Version/Setup kann AutoDB auch automatisch starten, z.B.:

- nach GUI-Neustart (wenn aktiviert)
- über Timer/Start-Trigger im Plugin

### Laufzeit
Während AutoDB läuft, werden neue Titel in eine Queue gepackt und verarbeitet.

### Abbruch / Beenden
✅ AutoDB kann per **EXIT** beendet werden (wie im Plugin vorgesehen).  
Wichtig: EXIT soll normale Menüs schließen und nur im Live-TV (InfoBar) als „AutoDB beenden“ dienen (so ist es stabil).

---

## 5. Was wird automatisch gelöscht (Cleanup)

Damit die Box nicht „voll läuft“, werden Dateien nach einer gewissen Zeit automatisch entfernt.

Typisch:

- Poster/Backdrops & Info-Dateien werden nach **~3 Tagen** als „alt“ betrachtet und gelöscht/erneuert

**Hinweis:** Das betrifft nur die „normalen“ Ordner:

- `<BASE>/xtra/poster/`
- `<BASE>/xtra/backdrop/`
- `<BASE>/xtra/Info/`
- `poster_info` / `backdrop_info`

✅ **Nicht gelöscht** wird:

- `<BASE>/xtra/custom/...`

---

## 6. Bleiben Poster/Backdrops für Aufnahmen erhalten

Grundsätzlich gilt:

- AutoDB/Live-Suche arbeitet EPG-basiert (Titel/Slug)
- Aufnahmen können eigene Titel/EPG-Daten haben

### Wichtig:
Wenn eine Aufnahme denselben **Slug** wie Live-TV verwendet, bleiben die Dateien oft verfügbar – aber Cleanup kann sie später entfernen.

✅ Empfehlung für Aufnahmen oder Lieblingssendungen:
➡️ **Custom Artwork nutzen**, damit es dauerhaft bleibt:

```
<BASE>/xtra/custom/poster/<slug>.jpg
<BASE>/xtra/custom/backdrop/<slug>.jpg
```

Custom-Dateien werden nicht gelöscht.

---

## 7. API-Keys einstellen

Im Plugin-Menü kannst du API-Keys setzen.

### Warum sind eigene API Keys besser?
- höhere Limits
- stabilere Treffer
- weniger Rate-Limit/Block
- genauere Ergebnisse

### „Legacy“ Keys
In manchen Setups sind „Legacy“-Keys bereits enthalten, damit grundsätzlich etwas funktioniert.  
✅ Mit **eigenen Keys** sind die Ergebnisse meistens deutlich besser.

### Wo bekomme ich die Keys?

- **TMDb API**: https://www.themoviedb.org/settings/api  
- **TheTVDB v4**: https://thetvdb.com/api-information  
- **Fanart.tv**: https://fanart.tv/get-an-api-key/  

*(Links können sich ändern – bei Bedarf im Browser öffnen.)*

---

## 8. PosterX Speicherpfad auswählen

Menüpunkt: **„PosterX Speicherpfad auswählen“**  
(EN: **PosterX storage path**)

Du wählst einen BASE-Pfad, z.B.:

- `Auto (empfohlen)`
- `/media/hdd`
- `/media/usb`
- `/media/net` (NAS)

Nach dem Speichern werden alle Ordner automatisch erzeugt:

```
<BASE>/xtra/...
<BASE>/xtra/custom/...
```

✅ Vorteil: alles (Poster/Backdrop/Info/Custom) liegt sauber zusammen in einem Baum.

---

## 9. Slugs auslesen (PosterX/BackdropX)

Menüpunkt: **„PosterX/BackdropX Slugs auslesen“**

### Was passiert?
Beim Aufruf werden automatisch Slugs gesammelt aus:

- `<BASE>/xtra/poster_info/*.json`
- `<BASE>/xtra/backdrop_info/*.json`
- `/var/volatile/tmp/PosterAutoDB.log`
- `/var/volatile/tmp/BackdropAutoDB.log`

Dann werden 2 JSON-Dateien geschrieben:

- `<BASE>/xtra/PosterX_slugs.json`
- `<BASE>/xtra/BackdropX_slugs.json`

### Wofür ist das gut?
Wenn du eigene Bilder nutzen willst, brauchst du den korrekten **Slug**:

✅ Beispiel:

```
Punkt 6 -> punkt_6
Ich - Einfach unverbesserlich 2 -> ich_einfach_unverbesserlich_2
```

---

## 10. Custom Artwork verwenden

Der wichtigste Ordner für „immer richtig“:

```
<BASE>/xtra/custom/
```

### Eigene Poster setzen
Lege deine Datei hier ab:

```
<BASE>/xtra/custom/poster/<slug>.jpg
```

### Eigene Backdrops setzen
Lege deine Datei hier ab:

```
<BASE>/xtra/custom/backdrop/<slug>.jpg
```

✅ Sobald ein Custom-Bild existiert, wird es bevorzugt und nicht überschrieben.

---

## 11. Was passiert nach einem neuen AutoDB Scan

- AutoDB lädt neue Daten für neue EPG-Titel
- vorhandene Cache-Dateien können ersetzt werden (nach Cleanup-Regeln)
- ✅ **Custom bleibt immer** und hat Priorität

Das heißt:

✅ Nach erneutem AutoDB Scan bleiben deine Custom-Bilder aktiv.

---

## 12. Manuell Poster/Backdrops finden (Quellen)

Wenn du selbst Bilder laden willst, sind diese Seiten die besten Startpunkte:

- 🎬 **TMDb**: https://www.themoviedb.org  
- 📺 **TVDb**: https://thetvdb.com  
- 🏞️ **Fanart.tv**: https://fanart.tv  
- ⭐ **IMDb**: https://www.imdb.com  
- 🔎 **Google Bilder**: https://images.google.com  

### Tipp
Für RTL Daily Shows können IMDb-Mediaviewer Backdrops am besten passen.

---

## 13. Fehlerdiagnose (Logs)

Wichtige Logs:

- `/var/volatile/tmp/PosterDB.log`
- `/var/volatile/tmp/BackdropDB.log`
- `/var/volatile/tmp/PosterAutoDB.log`
- `/var/volatile/tmp/BackdropAutoDB.log`

Wichtige Debug-Infos:

- `<BASE>/xtra/poster_info/*.json`
- `<BASE>/xtra/backdrop_info/*.json`
- `<BASE>/xtra/Info/*.json`

---

## 14. FAQ

### ❓ Warum wird immer wieder das gleiche falsche Bild geladen?
Weil bereits ein JSON-Cache existiert (Info/poster_info/backdrop_info).  
✅ Lösung: einzelne Slugs resetten (nur gezielt löschen) oder Custom setzen.

### ❓ Wird mein Custom-Bild gelöscht?
❌ Nein. Alles unter `<BASE>/xtra/custom/` bleibt erhalten.

### ❓ Kann ich den Speicherort später ändern?
✅ Ja, über „PosterX Speicherpfad auswählen“. Ordner werden automatisch neu angelegt.

---

---

# 🇬🇧 English

## 1. Overview

PosterX / BackdropX enhances Enigma2 (GradientFHD) with:

- 🖼️ Posters & backdrops for EPG/Live-TV, channel list, SecondInfoBar, player, etc.
- ⚙️ AutoDB: automatic scanning/prefetching and local caching
- 🔑 API keys: better matches with your own keys (TMDb/TVDb/Fanart)
- 💾 selectable storage path (HDD / USB / NAS)
- 🧩 Custom artwork: your own posters/backdrops (never auto-deleted)
- 🧾 Slug export: create slug lists for custom filenames

---

## 2. Storage layout

Everything is stored under the selected **BASE path** (default: `/media/hdd`) in:

```
<BASE>/xtra/
```

Folders:

```
<BASE>/xtra/poster/
<BASE>/xtra/backdrop/
<BASE>/xtra/Info/
<BASE>/xtra/poster_info/
<BASE>/xtra/backdrop_info/

<BASE>/xtra/custom/poster/
<BASE>/xtra/custom/backdrop/

<BASE>/xtra/PosterX_slugs.json
<BASE>/xtra/BackdropX_slugs.json
```

---

## 3. AutoDB: What it is and how it works

AutoDB scans bouquets/services, reads EPG titles and downloads:

- posters
- backdrops
- info data (IDs, ratings, sources)

This improves UI responsiveness because artwork is already cached locally.

---

## 4. AutoDB: Start, runtime, stop

- Start AutoDB from the plugin menu (depends on your build)
- It processes a queue of EPG events
- Stop with **EXIT** (configured to be safe and not interfere with normal menu closing)

---

## 5. What gets deleted automatically (cleanup)

To prevent storage from filling up, old cache files are removed (commonly after ~3 days):

- `<BASE>/xtra/poster/`
- `<BASE>/xtra/backdrop/`
- `<BASE>/xtra/Info/`
- `poster_info` / `backdrop_info`

✅ Not deleted:
- `<BASE>/xtra/custom/...`

---

## 6. Do posters/backdrops for recordings remain

Recordings depend on titles/slugs and the cache cleanup policy.  
To keep artwork permanently, use **custom artwork**.

---

## 7. API keys

Own API keys usually give better results and higher limits.

Key sources:

- TMDb: https://www.themoviedb.org/settings/api  
- TVDb v4: https://thetvdb.com/api-information  
- Fanart.tv: https://fanart.tv/get-an-api-key/  

---

## 8. PosterX storage path

Menu item: **PosterX storage path**  
Choose a BASE path:

- Auto (recommended)
- /media/hdd
- /media/usb
- /media/net

Folders will be created automatically.

---

## 9. Read slugs (PosterX/BackdropX)

Menu item: **Read slugs**

Sources:

- `<BASE>/xtra/poster_info/*.json`
- `<BASE>/xtra/backdrop_info/*.json`
- `/var/volatile/tmp/PosterAutoDB.log`
- `/var/volatile/tmp/BackdropAutoDB.log`

Outputs:

- `<BASE>/xtra/PosterX_slugs.json`
- `<BASE>/xtra/BackdropX_slugs.json`

---

## 10. Using custom artwork

Place your own files:

- Posters: `<BASE>/xtra/custom/poster/<slug>.jpg`
- Backdrops: `<BASE>/xtra/custom/backdrop/<slug>.jpg`

Custom artwork is always preferred and never auto-deleted.

---

## 11. What happens on the next AutoDB scan

- new items are fetched
- cache can be replaced by cleanup logic
- ✅ custom artwork stays and keeps priority

---

## 12. Where to find artwork manually (sources)

- TMDb: https://www.themoviedb.org  
- TVDb: https://thetvdb.com  
- Fanart.tv: https://fanart.tv  
- IMDb: https://www.imdb.com  
- Google Images: https://images.google.com  

---

## 13. Troubleshooting (logs)

Main logs:

- `/var/volatile/tmp/PosterDB.log`
- `/var/volatile/tmp/BackdropDB.log`
- `/var/volatile/tmp/PosterAutoDB.log`
- `/var/volatile/tmp/BackdropAutoDB.log`

JSON debug:

- `<BASE>/xtra/poster_info/`
- `<BASE>/xtra/backdrop_info/`
- `<BASE>/xtra/Info/`

---

## 14. FAQ

**Why do I always get the same wrong image?**  
Because cached JSON results are reused. Reset that slug or use custom artwork.

**Will my custom files be deleted?**  
No. Everything under `<BASE>/xtra/custom/` remains.

**Can I change the storage path later?**  
Yes, via PosterX storage path. Folders are created automatically.
