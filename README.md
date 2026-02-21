## ✨ Kurzüberblick / Quick Preview

### 🇩🇪 Deutsch
- 🎨 **Skins für OpenATV** (GradientFHD / stein17)
- 🧩 **GradientFHD Plugin komplett überarbeitet** – viele neue Funktionen
- 🖼️ **Poster & Backdrops** für EPG/Live-TV, Senderliste, SecondInfoBar, Player usw.
- ⚙️ **AutoDB**: scannt Bouquets/Sender, liest EPG-Titel und lädt Artwork automatisch (lokal gecached)
- 💾 **Speicherort frei wählbar** (HDD / USB / NAS) – alles unter `<BASE>/xtra/` organisiert
- 🧹 **Automatische Cache-Verwaltung**: alte Poster/Backdrops/Info werden typischerweise nach ~3 Tagen bereinigt
- 🧩 **Custom Override**: eigene Poster/Backdrops haben immer Priorität und werden nie automatisch gelöscht
- ⚡ **Custom sofort aktiv**: kein Neustart nötig – Cache-Datei löschen oder kurz umschalten/zappen reicht
- 🧾 **Slug-Export**: Slugs als JSON exportieren (für korrektes Benennen eigener Dateien)
- 🔑 **API-Key Management** (TMDb / TVDb / Fanart) – eigene Keys bringen meist bessere Treffer & Limits
- 🧰 **Fehlerdiagnose** über Logs + `poster_info`/`backdrop_info` JSONs
- 🎞️ **Aufnahmen/Artwork**: optional Artwork speichern; „Poster als Cover neben Aufnahme“ möglich (wenn aktiviert)
- 🎬 **MovieScanner (Aufnahmen/Movies): scannt ausgewählte Movie-/Aufnahmeordner und lädt Artwork (Poster/Backdrop/Banner) für vorhandene Dateien in den EMC-Cache.
- ✅ **Ordner-Auswahl: Pfade im Screen per OK an/aus, GRÜN startet den Suchlauf. 
- 🧠** Titel-Erkennung: arbeitet mit bereinigtem Titel (safe_name) + Media-Type-Erkennung (TV/Film) für bessere Treffer.
- 🖼️**„Poster als Cover neben Aufnahme“ (optional): kopiert das gefundene Poster als *.jpg neben die Aufnahme (nur wenn aktiviert).
- 🧹**EMC Cache-Verwaltung (Cleanup): behält nur Poster/Backdrops/Banner/Infos, zu denen eine passende Aufnahme im gesamten Movie-Ordner existiert – alles andere wird als Cache-Altlast gelöscht. Vorschau ohne Löschen per GELB, Löschen per GRÜN.
- ⏱️**Automatische Bereinigung (optional): planbarer täglicher Cleanup zu Uhrzeit HH:MM (wird beim GUI-Start eingerichtet; Box muss an/idle sein).
- 📄**Reports/Diagnose: schreibt Scanner-Report + Provider-Report (welcher Provider wie oft Poster/Backdrop/Banner geliefert hat) in den EMC-Bereich

**Hinweis (Löschlogik):**
- ✅ bleibt: `custom/` (deine eigenen Dateien)
- ♻️ wird bereinigt: Cache-/Info-Ordner (nach Zeit/Regeln, typ. ~3 Tage)

---

### 🇬🇧 English
- 🎨 **Skins for OpenATV** (GradientFHD / stein17)
- 🧩 **GradientFHD plugin fully reworked** – many new features
- 🖼️ **Posters & backdrops** for EPG/Live-TV, channel list, SecondInfoBar, player, etc.
- ⚙️ **AutoDB**: scans bouquets/services, reads EPG titles and downloads artwork automatically (cached locally)
- 💾 **Selectable storage path** (HDD / USB / NAS) – everything organized under `<BASE>/xtra/`
- 🧹 **Automatic cache cleanup**: old posters/backdrops/info are typically removed after ~3 days
- 🧩 **Custom override**: your own posters/backdrops always take priority and are never auto-deleted
- ⚡ **Custom applies instantly**: no restart required – delete the cache file or briefly zap/switch service
- 🧾 **Slug export**: export slugs to JSON (for correct custom filenames)
- 🔑 **API key management** (TMDb / TVDb / Fanart) – your own keys usually improve matches & rate limits
- 🧰 **Troubleshooting** via logs + `poster_info`/`backdrop_info` JSON debug files
- 🎞️ **Recordings/artwork**: optional storing of artwork; “copy poster as cover next to recording” available (if enabled)
- 🎬 **MovieScanner (recordings/movies): scans selected movie/recording folders and fetches artwork (poster/backdrop/banner) into the EMC cache.
- ✅ **Folder selection: toggle paths with OK, start scanning with GREEN. 
- 🧠 **Title handling: uses normalized titles (safe_name) + basic media-type detection (tv/movie) to improve matching.
- 🖼️ **“Copy poster next to recording” (optional): copies the found poster as *.jpg next to the recording (only if enabled).
- 🧹 **EMC cache cleanup: keeps only poster/backdrop/banner/info files that still have a matching recording anywhere in the movie folders; everything else is treated as leftover cache and removed. YELLOW = preview, GREEN = delete.
- ⏱️ **Scheduled cleanup (optional): daily cleanup at configurable HH:MM (schedule set on GUI start; receiver must be on/idle).
- 📄 **Reports/diagnostics: generates a scan report and a provider report (how many items each provider

**Note (deletion logic):**
- ✅ kept: `custom/` (your own files)
- ♻️ cleaned: cache/info folders (time-based rules, typically ~3 days)

---

## 📚 Dokumentation (klickbar)

- 🖼️ **[PosterX & BackdropX (DE/EN)](docs/PosterX-BackdropX-DE-EN.md)**
- 🧩 **[Custom Override (DE/EN)](docs/Custom-Override-Poster-Backdrop-DE-EN.md)**
- 🎨 **[Universelle Skin Integration](docs/Universelle-Skin-Integration-GradientFHD.md)**
