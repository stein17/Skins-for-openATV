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
- ⏰ **PrimeTime frei einstellbar**: Anzeige/Markierung in EPG & Senderliste nach deiner Uhrzeit (nicht fix 20:15)
- 🧾 **Slug-Export**: Slugs als JSON exportieren (für korrektes Benennen eigener Dateien)
- 🔑 **API-Key Management** (TMDb / TVDb / Fanart) – eigene Keys bringen meist bessere Treffer & Limits
- 🧰 **Fehlerdiagnose** über Logs + `poster_info`/`backdrop_info` JSONs
- 🎞️ **Aufnahmen/Artwork**: optional Artwork speichern; „Poster als Cover neben Aufnahme“ möglich (wenn aktiviert)

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
- ⏰ **Prime time fully configurable**: EPG/channel list indicator based on your own time (not hardcoded to 20:15)
- 🧾 **Slug export**: export slugs to JSON (for correct custom filenames)
- 🔑 **API key management** (TMDb / TVDb / Fanart) – your own keys usually improve matches & rate limits
- 🧰 **Troubleshooting** via logs + `poster_info`/`backdrop_info` JSON debug files
- 🎞️ **Recordings/artwork**: optional storing of artwork; “copy poster as cover next to recording” available (if enabled)

**Note (deletion logic):**
- ✅ kept: `custom/` (your own files)
- ♻️ cleaned: cache/info folders (time-based rules, typically ~3 days)

---

## 📚 Dokumentation (klickbar)

- 🖼️ **[PosterX & BackdropX (DE/EN)](docs/PosterX-BackdropX-DE-EN.md)**
- 🧩 **[Custom Override (DE/EN)](docs/Custom-Override-Poster-Backdrop-DE-EN.md)**
- 🎨 **[Universelle Skin Integration](docs/Universelle-Skin-Integration-GradientFHD.md)**
