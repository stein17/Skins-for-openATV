## ✨ Kurzüberblick / Quick Preview

**Schnellnavigation:**  
- [🇩🇪 Deutsch](#-deutsch) · [🇬🇧 English](#-english)

---

## 🇩🇪 Deutsch

### Kurzüberblick
- 🎨 **Skins für OpenATV** (GradientFHD / stein17)
- 🧩 **GradientFHD Plugin komplett überarbeitet** – viele neue Funktionen
- 🖼️ **Poster & Backdrops** für EPG/Live-TV, Senderliste, SecondInfoBar, Player usw.
- ⚙️ **AutoDB**: scannt Bouquets/Sender, liest EPG-Titel und lädt Artwork automatisch (lokal gecached)
- 💾 **Speicherort frei wählbar** (HDD / USB / NAS) – alles unter `<BASE>/xtra/` organisiert
- 🧹 **Automatische Cache-Verwaltung**: alte Poster/Backdrops/Info werden typischerweise nach ~3 Tagen bereinigt
- 🧩 **Custom Override**: eigene Poster/Backdrops haben immer Priorität und werden nie automatisch gelöscht
- ⚡ **Custom sofort aktiv**: kein Neustart nötig – Cache-Datei löschen oder kurz umschalten/zappen reicht
- ⏰ **PrimeTime frei einstellbar**: Anzeige/Markierung in EPG & Senderliste nach deiner Uhrzeit (nicht fix 20:15)
- 🧾 **Slug-Export**: Slugs als JSON exportieren (für korrektes Benennen eigener Dateien)
- 🔑 **API-Key Management** (TMDb / TVDb / Fanart) – eigene Keys bringen meist bessere Treffer & Limits
- 🧰 **Fehlerdiagnose** über Logs + `poster_info`/`backdrop_info` JSONs
- 🎞️ **Aufnahmen/Artwork**: optional Artwork speichern; „Poster als Cover neben Aufnahme“ möglich (wenn aktiviert)

### 🎬 MovieScanner (EMC / Aufnahmen & Movies)
- 🎬 **MovieScanner**: scannt ausgewählte Movie-/Aufnahmeordner und lädt Artwork (**Poster/Backdrop/Banner**) in den **EMC-Cache**
  ✅  → scannt ALLE Aufnahmen in konfigurierten Ordnern        
  ✅  → lädt: Serien-Poster, Staffel-Poster, Episode-Still    
  ✅  → lädt: Backdrop, Banner                                 
  ✅  → speichert in /media/hdd/xtra/EMC/                     

  🖼️ GradientPosterXEMC  (Poster-Renderer)                     
  ✅ → liest aus EMC-Cache                                   
  ✅ → Priorität: Staffel-Poster → Serien-Poster             

  🎞️ GradientBackdropXEMC  (Backdrop-Renderer)                 
  ✅ → liest aus EMC-Cache                                   
  ✅ → Priorität: Episode-Still → Staffel → Serien-Backdrop 
	
- ✅ **Ordner-Auswahl**: Pfade per **OK** an/aus, **GRÜN** startet den Suchlauf
- 🧠 **Titel-Erkennung**: nutzt bereinigten Titel (`safe_name`) + Media-Type-Erkennung (TV/Film)
- 🖼️ **Poster als Cover neben Aufnahme (optional)**: kopiert Poster als `*.jpg` neben die Aufnahme
- 🧹 **EMC Cache Cleanup**: nur Dateien behalten, zu denen passende Aufnahmen existieren (**GELB** = Vorschau, **GRÜN** = Löschen)
- ⏱️ **Zeitplan (optional)**: täglicher Cleanup zu **HH:MM** (Receiver muss an/idle sein)
- 📄 **Reports/Diagnose**: Scanner-Report + Provider-Report (Treffer pro Provider)

### 🧹 Löschlogik
- ✅ bleibt: `custom/` (deine eigenen Dateien)
- ♻️ wird bereinigt: Cache-/Info-Ordner (zeitbasiert, typ. ~3 Tage)

### 📚 Dokumentation (klickbar)
- 🖼️ **[PosterX & BackdropX (DE/EN)](docs/PosterX-BackdropX-DE-EN.md)**
- 🧩 **[Custom Override (DE/EN)](docs/Custom-Override-Poster-Backdrop-DE-EN.md)**
- 🎨 **[Universelle Skin Integration](docs/Universelle-Skin-Integration-GradientFHD.md)**

---

## 🇬🇧 English

### Quick preview
- 🎨 **Skins for OpenATV** (GradientFHD / stein17)
- 🧩 **GradientFHD plugin fully reworked** – many new features
- 🖼️ **Posters & backdrops** for EPG/Live-TV, channel list, SecondInfoBar, player, etc.
- ⚙️ **AutoDB**: scans bouquets/services, reads EPG titles and downloads artwork automatically (cached locally)
- 💾 **Selectable storage path** (HDD / USB / NAS) – everything organized under `<BASE>/xtra/`
- 🧹 **Automatic cache cleanup**: old posters/backdrops/info are typically removed after ~3 days
- 🧩 **Custom override**: your own posters/backdrops always take priority and are never auto-deleted
- ⚡ **Custom applies instantly**: no restart required – delete the cache file or briefly zap/switch service
- ⏰ **Prime time fully configurable**: EPG/channel list indicator based on your own time (not hardcoded to 20:15)
- 🧾 **Slug export**: export slugs to JSON (for correct custom filenames)
- 🔑 **API key management** (TMDb / TVDb / Fanart) – your own keys usually improve matches & rate limits
- 🧰 **Troubleshooting** via logs + `poster_info`/`backdrop_info` JSON debug files
- 🎞️ **Recordings/artwork**: optional storing of artwork; “copy poster as cover next to recording” available (if enabled)

### 🎬 MovieScanner (EMC / recordings & movies)
- 🎬 **MovieScanner**: scans selected movie/recording folders and fetches artwork (**poster/backdrop/banner**) into the **EMC cache**
- ✅ **Folder selection**: toggle paths with **OK**, start scanning with **GREEN**
- 🧠 **Title handling**: uses normalized titles (`safe_name`) + basic media-type detection (tv/movie)
- 🖼️ **Copy poster next to recording (optional)**: copies poster as `*.jpg` next to the recording
- 🧹 **EMC cache cleanup**: keeps only files that still have a matching recording (**YELLOW** = preview, **GREEN** = delete)
- ⏱️ **Scheduled cleanup (optional)**: daily cleanup at configurable **HH:MM** (receiver must be on/idle)
- 📄 **Reports/diagnostics**: scan report + provider report (hits per provider)

### 🧹 Deletion logic
- ✅ kept: `custom/` (your own files)
- ♻️ cleaned: cache/info folders (time-based rules, typically ~3 days)

### 📚 Documentation (clickable)
- 🖼️ **[PosterX & BackdropX (DE/EN)](docs/PosterX-BackdropX-DE-EN.md)**
- 🧩 **[Custom Override (DE/EN)](docs/Custom-Override-Poster-Backdrop-DE-EN.md)**
- 🎨 **[Universal Skin Integration](docs/Universelle-Skin-Integration-GradientFHD.md)**
