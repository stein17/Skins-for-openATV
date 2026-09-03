# Animated Weather – Wettersets

Diese neutralen Wettersets sind für das skinunabhängige Enigma2-Plugin
**Animated Weather 0.3-r2** vorbereitet. Das Plugin verändert OAWeather nicht.

Die Archive werden nicht im Plugin-IPK gespeichert. Bei der Installation lädt
das Plugin nur das ausgewählte Set aus dem offiziellen GitHub-Release, prüft
Dateigröße und SHA-256-Prüfsumme, entpackt es auf den ausgewählten Datenträger
und entfernt die temporäre ZIP anschließend wieder.

| Anzeige im Plugin | Ordner | Größe | Lizenz |
|---|---|---:|---|
| amCharts Weather Icon (animated) | `amcharts-1.0.0` | 160 × 160 | CC BY 4.0 |
| meteocons-Fill (animated) | `meteocons-2-fill` | 180 × 180 | MIT |
| meteocons-Flat (animated) | `meteocons-3-flat` | 180 × 180 | MIT |
| meteocons-Line (animated) | `meteocons-3-line` | 180 × 180 | MIT |
| meteocons-Monochrome White (animated) | `meteocons-3-monochrome-white` | 180 × 180 | MIT |
| stein17 Weather v1.3 (animated) | `stein17-weather-v1.3` | 180 × 180 | Copyright stein17 – Nutzung mit Animated Weather gestattet; sonst nur mit Genehmigung |

## Neu in stein17 Weather v1.3

- `partly-cloudy-night` besitzt drei gut sichtbare, unabhängig funkelnde Sterne.
- `partly-cloudy-night` und `mostly-clear-night` verwenden einen warmen
  elfenbein-gelben Mond als Kontrast zu den kühl weiß-blauen Wolken.
- Alte Niederschlagsreste wurden aus `partly-cloudy-day` und
  `partly-cloudy-night` entfernt.
- Metadaten und Vorschau wurden auf v1.3 aktualisiert.

Alle Motive des stein17-Sets enthalten genau 24 fortlaufend nummerierte Frames
von `a0.png` bis `a23.png`. Der Renderer skaliert die transparenten PNG-Dateien
proportional auf die im Skin festgelegte Widgetgröße.

Die fünf unveränderten öffentlichen Sets bleiben über das Release v1.2.0
erreichbar. `stein17-weather-v1.3.zip` wird aus dem Release
`animated-weather-icons-v1.3.0` geladen.

Die Lizenz des jeweiligen Grafikprojekts bleibt erhalten. Weitere Einzelheiten
liegen in jedem Set-Archiv.
