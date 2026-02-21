# Custom Override – Deutsch & English

---

# Deutsch 🇩🇪

# Custom Override für Poster & Backdrops (eigene Bilder verwenden)

Manchmal liefern TMDB/TVDB/Google falsche Poster/Backdrops oder es wird gar nichts gefunden.  
Mit dem **Custom Override** kannst du für **jede Sendung/Serie/Film** eigene Bilder hinterlegen, die **immer Vorrang** haben ✅

---

## Ordnerstruktur

Lege deine eigenen Dateien hier ab:

- **Poster:** `/media/hdd/xtra/custom/poster/`
- **Backdrops:** `/media/hdd/xtra/custom/backdrop/`

Die Renderer kopieren dann automatisch nach:

- **Poster-Cache:** `/media/hdd/xtra/poster/`
- **Backdrop-Cache:** `/media/hdd/xtra/backdrop/`

> Hinweis: Wenn deine Box `xtra` auf USB/MMC nutzt, gilt sinngemäß `/media/usb/xtra/...` oder `/media/mmc/xtra/...`.

---

## 1) Dateiname = Slug (wichtig!)

Der Dateiname muss genau dem **Slug** entsprechen, den der Renderer verwendet.

✅ Beispiel (Slug: `planet_weltweit`):

- Poster: `/media/hdd/xtra/custom/poster/planet_weltweit.jpg`
- Backdrop: `/media/hdd/xtra/custom/backdrop/planet_weltweit.jpg`

### Wie finde ich den richtigen Slug?
- Über dein Tool/Plugin „nach slug durchsuchen“ ✅  
- Alternativ (wenn Logs aktiv sind) steht der Slug oft im `[QUEUE]`-Eintrag.

---

## 2) Format

- Verwende **JPG** (`.jpg`)
- Empfehlung: nur Slug im Dateinamen, keine Sonderzeichen/Leerzeichen

---

## 3) Update ohne Neustart (Refresh)

Du musst Enigma2 **nicht** neu starten.  
Wichtig ist nur: der Cache muss **neu aufgebaut** werden.

### Variante A (empfohlen): Cache-Datei löschen
Wenn du ein Bild ersetzt hast, lösche die Cache-Datei — beim nächsten Event wird dein Custom automatisch kopiert.

**Poster refresh:**
```sh
rm -f /media/hdd/xtra/poster/<slug>.jpg
sync
```

**Backdrop refresh:**
```sh
rm -f /media/hdd/xtra/backdrop/<slug>.jpg
sync
```

### Variante B (sehr einfach): einmal kurz auf einen anderen Sender schalten
In der Praxis reicht oft:
1. kurz auf **einen anderen Sender** zappen
2. dann zurück

Beim Zurückschalten wird der Titel erneut verarbeitet und das Custom-Bild wird übernommen.

---

## 4) Kontrolle: wurde wirklich das Custom-Bild genutzt?

Sicherster Check ist ein **MD5-Vergleich**:

**Poster prüfen:**
```sh
md5sum /media/hdd/xtra/custom/poster/<slug>.jpg
md5sum /media/hdd/xtra/poster/<slug>.jpg
```

**Backdrop prüfen:**
```sh
md5sum /media/hdd/xtra/custom/backdrop/<slug>.jpg
md5sum /media/hdd/xtra/backdrop/<slug>.jpg
```

✅ Wenn beide Hashes identisch sind → Custom Override aktiv.

---

## 5) AutoDB

Wenn AutoDB läuft (manuell oder zu den festen Uhrzeiten), gilt dasselbe:
- Existiert ein Custom-Bild → es wird **immer bevorzugt** und in den Cache kopiert.
- Provider (TMDB/TVDB/Google) werden nur genutzt, wenn **kein** Custom-Bild existiert.

---

## Typische Fehlerquellen

- Datei liegt im falschen Ordner (`poster` vs `backdrop`)
- Dateiname ist nicht exakt der Slug (Groß/Kleinschreibung, Leerzeichen)
- Datei ist leer/0 Bytes
- Cache wurde nicht gelöscht und es wurde noch nicht neu “getriggert” → einmal zappen reicht meist

---

# English 🇬🇧

# Custom Override for Posters & Backdrops (use your own images)

Sometimes TMDB/TVDB/Google return wrong posters/backdrops — or nothing is found at all.  
With the **Custom Override**, you can provide your own images for **any show/series/movie**, and they will **always take priority** ✅

---

## Folder layout

Put your custom files here:

- **Posters:** `/media/hdd/xtra/custom/poster/`
- **Backdrops:** `/media/hdd/xtra/custom/backdrop/`

The renderers will automatically copy them into the cache:

- **Poster cache:** `/media/hdd/xtra/poster/`
- **Backdrop cache:** `/media/hdd/xtra/backdrop/`

> Note: If your box uses `xtra` on USB/MMC, the same applies to `/media/usb/xtra/...` or `/media/mmc/xtra/...`.

---

## 1) Filename = slug (important!)

The filename must match the **slug** used by the renderer.

✅ Example (slug: `planet_weltweit`):

- Poster: `/media/hdd/xtra/custom/poster/planet_weltweit.jpg`
- Backdrop: `/media/hdd/xtra/custom/backdrop/planet_weltweit.jpg`

### How do I find the correct slug?
- Use your tool/plugin that can “search by slug” ✅  
- Alternatively (if logging is enabled), the slug often appears in the `[QUEUE]` log line.

---

## 2) Format

- Use **JPG** (`.jpg`)
- Recommendation: filename = slug only, no special characters/spaces

---

## 3) Update without restarting Enigma2 (refresh)

You do **not** need to restart Enigma2.  
You only need the cache to be **rebuilt**.

### Option A (recommended): delete the cache file
After replacing an image, delete the cached file — on the next event your custom image will be copied again.

**Poster refresh:**
```sh
rm -f /media/hdd/xtra/poster/<slug>.jpg
sync
```

**Backdrop refresh:**
```sh
rm -f /media/hdd/xtra/backdrop/<slug>.jpg
sync
```

### Option B (very easy): zap once to another channel
In practice, it’s often enough to:
1. zap briefly to **any other channel**
2. zap back

When you return, the current title is processed again and the custom image is applied.

---

## 4) Verify: was the custom image used?

The most reliable check is an **MD5 comparison**:

**Check poster:**
```sh
md5sum /media/hdd/xtra/custom/poster/<slug>.jpg
md5sum /media/hdd/xtra/poster/<slug>.jpg
```

**Check backdrop:**
```sh
md5sum /media/hdd/xtra/custom/backdrop/<slug>.jpg
md5sum /media/hdd/xtra/backdrop/<slug>.jpg
```

✅ If both hashes are identical → Custom Override is active.

---

## 5) AutoDB

When AutoDB runs (manual or scheduled), it works the same way:
- If a custom image exists → it is **always preferred** and copied into the cache.
- Providers (TMDB/TVDB/Google) are only used if **no** custom image exists.

---

## Common pitfalls

- File is in the wrong folder (`poster` vs `backdrop`)
- Filename does not exactly match the slug (case/spaces)
- File is empty/0 bytes
- Cache was not deleted and no new “trigger” happened yet → zapping once usually fixes it
