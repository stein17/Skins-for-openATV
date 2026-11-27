# PLi FullNight FHD – stein17 Mod

**Bedienungsanleitung und Übersicht der Skin-Einstellungen**  
**Version:** 1.0-r14 · **Auflösung:** Full HD (1920 × 1080) · **System:** OpenATV / Enigma2

Der PLi FullNight FHD – stein17 Mod bewahrt den dunklen Charakter des ursprünglichen FullNight-Skins und ergänzt ihn um verschiedene Farbpaletten, individuell wählbare Senderlisten, konfigurierbare Text- und Fortschrittsfarben sowie optionale Anzeigen für e2MDB, CAID, VPN und Wetter.

Alle genannten Optionen befinden sich im Menü **„PLi FullNight FHD Einstellungen“**. Die rechte Bildschirmseite zeigt zur markierten Einstellung eine Beschreibung bzw. Vorschau.

## 1. Farbpalette – das Grunddesign

Die **Farbpalette** bestimmt die Grundfarben des Skins: Hintergrund, Kopfzeilen, Flächen und Auswahlhintergründe.

Zur Auswahl stehen:

- **FullNight Original:** klassisches, sehr dunkles FullNight-Design (Standard)
- **Mitternachtsblau:** dunkles Blau für Hintergründe und Auswahlflächen
- **Nachtschwarz:** besonders dunkle, weitgehend neutrale Flächen
- **Teal:** dunkle Petrol-/Türkistöne
- **Taupe:** dunkle Braun-/Grautöne
- **Metrix Farbe:** dunkler Hintergrund mit kräftig blauen Kopfzeilen und Auswahlflächen

**Wichtig:** Die Farbpalette ist nicht dasselbe wie die Akzentfarbe. Beispiel: „FullNight Original“ kann mit einer cyanfarbenen Akzentfarbe kombiniert werden, ohne dass die gesamte Grundpalette cyan wird.

## 2. Akzentfarbe – wofür ist sie da?

Die **Akzentfarbe** ist die Hervorhebungsfarbe bestimmter Skin-Elemente, die auf den globalen Farbnamen `accent` zugreifen. Sie ist unabhängig von der Farbe des ausgewählten Listentexts.

Verfügbare Farben: **Bernstein (Standard), PLi Blau, Cyan, Hellblau, Graublau, Hellgrün, Grün, Silber und Weiß**.

**Beispiel:** Farbpalette „FullNight Original“ + Akzentfarbe „Bernstein“ ergibt die dunkle FullNight-Oberfläche mit bernsteinfarbenen Hervorhebungen. Mit „Cyan“ werden die entsprechenden Akzente cyanfarben, die Grundoberfläche bleibt dunkel.

Nicht jedes farbige Element im Skin verwendet die Akzentfarbe. Fortschrittsbalken besitzen eine eigene Einstellung.

## 3. Auswahltextfarbe – wofür ist sie da?

Die **Auswahltextfarbe** legt fest, welche globale Textfarbe für markierte Einträge verwendet wird, sofern der betreffende Bildschirm die globale Auswahltextfarbe benutzt.

Verfügbare Farben: **Bernstein (Standard), PLi Blau, Cyan, Hellblau, Graublau, Hellgrün, Grün, Silber und Weiß**.

**Unterschied zur Akzentfarbe:**

- **Akzentfarbe**: Farbe bestimmter grafischer Hervorhebungen.
- **Auswahltextfarbe**: Schriftfarbe markierter Listeneinträge.

**Beispiel:** Akzentfarbe „Cyan“ und Auswahltextfarbe „Bernstein“ sind gleichzeitig möglich. Der markierte Eintrag kann damit bernsteinfarben beschriftet sein, während andere Akzente cyanfarben dargestellt werden.

## 4. Senderlisten-Design (Bildschirm / Liste) ›

Hier wird festgelegt, **wie die Senderliste aufgebaut ist**. Das Untermenü verwendet die entsprechenden OpenATV-Einstellungen:

1. **Senderliste / Bildschirm:** gewünschten Bildschirm bzw. Darstellungsmodus wählen.
2. **Senderliste / Liste:** passende Listenanordnung auswählen (z. B. ein- oder mehrzeilige Liste; je nach verfügbaren Templates).

Es werden nur die Listenlayouts angeboten, die zum gewählten Bildschirm passen. Der Skin bietet dafür eine Vorschau. Im klassischen Modus wird die Standard-OpenATV-Liste verwendet; dort steht nicht dieselbe FullNight-Vorschau zur Verfügung.

**Bedienung:** Mit **OK** Untermenü öffnen, mit **Grün** Auswahl übernehmen, mit **Rot** abbrechen. Danach im Hauptmenü mit **Grün** speichern.

## 5. Senderlisten-Farben (neuer Modus) ›

Für die **neuen Senderlisten-Modi** lassen sich die Textfarben einzelner Informationen getrennt anpassen:

| Einstellung | Bedeutung |
|---|---|
| Sendername (`ServiceName`) | Name des ausgewählten Senders |
| Sendungstitel (`Title1`) | Titel der aktuellen Sendung |
| Nächste Sendung 1 (`Title2`) | Titel der ersten Folgesendung, einschließlich zugehöriger Startzeit |
| Nächste Sendung 2 (`Title3`) | Titel der zweiten Folgesendung, einschließlich zugehöriger Startzeit |
| Kurzbeschreibung (`ShortDescription1`) | kurze Sendungsbeschreibung |
| Start-/Endzeit (`StartEndTime1`) | Uhrzeiten der aktuellen Sendung |
| Restzeit (`Remain`) | verbleibende Sendezeit |
| Primetime (`TitleP`) | Titel der Primetime-Sendung |

Zur Wahl stehen unter anderem **globale Auswahltextfarbe**, **normaler Text**, **Sekundärtext**, **Akzentfarbe** und die einzelnen festen Farben. So können beispielsweise Sendername, Folgesendungen und Restzeit unterschiedlich eingefärbt werden.

Das Untermenü enthält eine **Live-Vorschau** der gewählten Farben. Mit **Gelb** werden die Farben dieses Untermenüs auf die Vorgaben zurückgesetzt; mit **Grün** übernommen.

**Wichtig:** Diese individuellen Textfarben gelten für den **neuen Senderlistenmodus**, nicht für den alten/klassischen Modus. Bei der Palette **„Metrix Farbe“** setzt die Speicherlogik die Farben der ausgewählten Senderlistenfelder auf die globale Auswahltextfarbe.

## 6. Fortschrittsfarbe

Bestimmt den Stil der Fortschrittsbalken, zum Beispiel für Sendungsfortschritt in **Senderliste, EPG, Infobar und Player**.

Auswahlmöglichkeiten:

- **Blauer Verlauf** (Standard)
- **Dunkelgelber Verlauf**
- **Dunkelgrauer Verlauf**
- **Farbverlauf Grün–Gelb–Rot**
- **Teal-Verlauf**
- **Taupe-Verlauf**

Die Fortschrittsfarbe kann unabhängig von Farbpalette, Akzentfarbe und Auswahltextfarbe eingestellt werden.

## 7. CAID-Informationen

Blendet auf Wunsch Informationen zur Entschlüsselung in der Infobar ein. Je nach gewählter Variante können **Softcam, Cam-Version, Server, CAID und ECM** angezeigt werden.

Bei Nichtbedarf auf **„Ausgeschaltet“** stellen. Die tatsächlich sichtbaren Angaben hängen davon ab, welche Informationen das verwendete System bereitstellt.

## 8. e2MDB Poster/Backdrop im EPG

Ergänzt unterstützte EPG-Ansichten um Filmbilder bzw. Hintergründe aus **e2MDB**. Dies betrifft insbesondere EPGSelection, Multi-EPG und vertikale EPG-Ansichten.

Standard: **Ausgeschaltet**. Für die Aktivierung werden **e2MDB** und der Converter **E2MDBEventInfo** benötigt. Das Einstellungsplugin prüft diese Voraussetzungen beim Speichern.

## 9. e2MDB Poster/Backdrop in der Infobar

Hier kann die Bildanzeige in der Infobar gewählt werden:

- **Ausgeschaltet** (Standard)
- **Poster:** hochformatiges Motiv
- **Backdrop:** breites Hintergrundmotiv
- **Poster + Backdrop:** Kombination aus beiden

Die verfügbaren Bilder hängen von den in e2MDB vorhandenen Daten ab. Auch hier ist e2MDB einschließlich E2MDBEventInfo Voraussetzung.

## 10. VPN und öffentliche IP

Kann in der Infobar den **VPN-Status**, das **Land** und die **öffentliche IP-Adresse** anzeigen.

Zur Auswahl stehen je nach Variante Positionen **oben links, unten links, oben rechts oder unten rechts**, jeweils **mit oder ohne Provider-Anzeige**. Standard: **Ausgeschaltet**.

Die Anzeige dient der Information; diese Einstellung richtet keinen VPN-Tunnel ein.

## 11. Wetter in der Infobar

Bindet eine Wetteransicht auf Basis von **OAWeather** in die Infobar ein.

Vorgesehene Darstellungen sind:

- **5-Tage-Vorschau**
- **Kompakt oben links**
- **Kompakt oben rechts**
- **Kompakt unten rechts**

Standard: **Ausgeschaltet**. Die Wetterdarstellung benötigt entsprechend eingerichtete Wetterdaten bzw. OAWeather.

## 12. Animierte Wetter-Icons

Mit **„Animierte Wetter-Icons“ → „Aktiviert“** lassen sich die FullNight-Wettersymbole über **Animated Weather by @stein17** animiert anzeigen.

**So funktioniert die Aktivierung:**

1. Den Menüpunkt **„Animierte Wetter-Icons“** auf **„Aktiviert“** setzen.
2. Falls Animated Weather noch nicht installiert ist, bietet das Skin-Plugin automatisch die Installation der vorgesehenen Erweiterung aus dem offiziellen GitHub-Release an. Dafür muss der Receiver Internetzugang besitzen.
3. Die Nachfrage bestätigen und die Installation erfolgreich abschließen lassen.
4. Mit **Grün – Speichern** übernehmen und die GUI neu starten.

Lehnt man die Installation ab oder schlägt sie fehl, wird die Option wieder auf **„Ausgeschaltet“** gesetzt. Animierte Icons und die Wetteranzeige in der Infobar sind **zwei getrennte Einstellungen**: Für die Wetter-Infobar muss zusätzlich unter **„Wetter in der Infobar“** eine passende Ansicht gewählt werden.

## 13. Screen-Namen anzeigen

Diese Option ist hauptsächlich für **Support, Fehlersuche und Skin-Entwicklung** vorgesehen. Bei Aktivierung wird oben rechts der technische Enigma2-Screenname eingeblendet. So kann bei Problemen einfacher festgestellt werden, welcher Bildschirm gerade verwendet wird.

Standard: **Ausgeschaltet**.

## 14. Farbtasten und Speichern

Im Hauptmenü:

| Taste | Funktion |
|---|---|
| **Rot** | Abbrechen / Änderungen verwerfen |
| **Grün** | Einstellungen speichern |
| **Gelb** | Standardwerte der Haupteinstellungen wiederherstellen |
| **Blau** | Über / Informationen zum Skin |
| **OK** | Bei Einträgen mit `>` das jeweilige Untermenü öffnen |

Nach dem Speichern wird ein **GUI-Neustart** angeboten. Er ist erforderlich, damit neu erzeugte Farb- und Skinpart-Dateien vollständig geladen werden.

**Hinweis zu Standardwerten:** Die gelbe Taste setzt die in der Hauptliste enthaltenen Einstellungen zurück. Für die individuellen Senderlisten-Farben gibt es im zugehörigen Untermenü eine eigene gelbe Standardwerte-Taste. Bereits gespeicherte Einstellungen können bei einem Update erhalten bleiben.

## 15. Vorgaben bei einer Erstinstallation

- **Farbpalette:** FullNight Original
- **Akzentfarbe:** Bernstein
- **Auswahltextfarbe:** Bernstein
- **Fortschrittsfarbe:** Blauer Verlauf
- **CAID, e2MDB im EPG, e2MDB in der Infobar, VPN, Wetter und animierte Wetter-Icons:** Ausgeschaltet
- **Screen-Namen:** Ausgeschaltet

**Tipp:** Wer das ursprüngliche FullNight-Erscheinungsbild nutzen möchte, beginnt mit **FullNight Original + Bernstein + Bernstein** und aktiviert zusätzliche Skinparts nur nach Bedarf.

---

**Projekt:** [Skins-for-openATV von stein17](https://github.com/stein17/Skins-for-openATV)  
**Hinweis:** Die verfügbaren Senderlisten-Layouts und Zusatzanzeigen können von OpenATV-Version, installierten Erweiterungen und vorhandenen Daten abhängen.
