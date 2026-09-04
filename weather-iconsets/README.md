# Animated Weather – Wettersets

Diese neutralen Wettersets sind für das skinunabhängige Enigma2-Plugin
**Animated Weather 0.3-r3** vorbereitet. Das Plugin verändert OAWeather nicht.

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
| stein17 Weather v1.4 (animated) | `stein17-weather-v1.4` | 180 × 180 | Copyright stein17 – Nutzung mit Animated Weather gestattet; sonst nur mit Genehmigung |

## Neu in stein17 Weather v1.4

- Die Sonnen in `partly-cloudy-day` und `mostly-sunny-day` besitzen keinen
  auffälligen runden Lichtpunkt mehr.
- Die Mondsichel in `clear-night` wurde ohne überstehende Konturlinien neu
  aufgebaut.
- `wind` kombiniert einen rot-weißen Windsack mit farbigen Blättern und drei
  enger gestaffelten Windlinien.
- Die Windlinien haben unterschiedliche, wechselnde Längen und laufen am
  rechten Ende weich transparent aus.

Alle Motive des stein17-Sets enthalten genau 24 fortlaufend nummerierte Frames
von `a0.png` bis `a23.png`. Der Renderer skaliert die transparenten PNG-Dateien
proportional auf die im Skin festgelegte Widgetgröße.

Die fünf unveränderten öffentlichen Sets bleiben über das Release v1.2.0
erreichbar. `stein17-weather-v1.4.zip` wird aus dem Release
`animated-weather-icons-v1.4.0` geladen.

Die Lizenz des jeweiligen Grafikprojekts bleibt erhalten. Weitere Einzelheiten
liegen in jedem Set-Archiv.
