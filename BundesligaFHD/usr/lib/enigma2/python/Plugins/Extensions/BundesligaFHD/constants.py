# -*- coding: utf-8 -*-
from __future__ import absolute_import

PLUGIN_NAME = "BundesligaFHD Config"
PLUGIN_VERSION = "0.7"
SKIN_NAME = "BundesligaFHD"
SKIN_XML = "BundesligaFHD/skin.xml"
SKIN_BASE = "/usr/share/enigma2/BundesligaFHD"
STATE_BASE = "/etc/enigma2/BundesligaFHD"
STATE_ACTIVE_DIR = STATE_BASE + "/mySkin"
TEAM_CATALOG = SKIN_BASE + "/team_assets/catalog.json"
DEFAULT_TEAM_TITLE = "Default"

# (interner Schlüssel, sichtbarer Text, Farbname in der Skin-XML)
COLOR_ITEMS = (
    ("service_name", "Sendername Farbe:", "ch-fg-name"),
    ("service_name_select", "Sendername ausgewählt:", "ch-fg-name-select"),
    ("event_name", "Sendungsname Farbe:", "ch-fg-event"),
    ("event_name_select", "Sendungsname ausgewählt:", "ch-fg-event-select"),
    ("bg_color_select", "Hintergrund ausgewählt:", "ch-bg-select"),

    ("fg_title_ib", "Infobar Titel Farbe:", "fg-title-ib"),
    ("fg_clock_ib", "Infobar Uhrzeit Farbe:", "fg-clock-ib"),
    ("fg_date_ib", "Infobar Datum Farbe:", "fg-date-ib"),

    ("fg_title_m", "Menü Titel Farbe:", "fg-title-m"),
    ("fg_title_s", "Setup Titel Farbe:", "fg-title-s"),
    ("fg_clock_s", "Menü/Setup Uhrzeit Farbe:", "fg-clock-s"),
    ("fg_date_s", "Menü/Setup Datum Farbe:", "fg-date-s"),

    ("club_primary", "Team Primärfarbe:", "club_primary"),
    ("club_selection_bg", "Border/Progress Primärfarbe:", "club_selection_bg"),
    ("club_selection_fg", "Ausgewählte Schriftfarbe:", "club_selection_fg"),
)

# Enigma2 verwendet bei diesen Skins #AARRGGBB mit #00 als deckend.
COLOR_CHOICES = [
    ("team", "Vereinsstandard"),
    ("#0008090c", "Schwarz"),
    ("#0018171c", "Schwarzgrau"),
    ("#00303030", "Dunkelgrau"),
    ("#00808080", "Grau"),
    ("#00d8d8d8", "Hellgrau"),
    ("#00fcfcfc", "Weiß"),
    ("#00dc052d", "Rot"),
    ("#00650010", "Dunkelrot"),
    ("#0000b140", "Grün"),
    ("#0000ff00", "Hellgrün"),
    ("#00005baa", "Blau"),
    ("#00002b55", "Dunkelblau"),
    ("#0000ffff", "Cyan"),
    ("#00ffd000", "Gelb"),
    ("#00b89a2f", "Gold"),
    ("#00f28c00", "Orange"),
    ("#00ff00ff", "Magenta"),
]

CATEGORY_TITLES = {
    "infobar": "Infobar",
    "sib": "SecondInfoBar",
    "secondinfobar": "SecondInfoBar",
    "ch_se": "Senderliste",
    "channelselection": "Senderliste",
    "channel_selection": "Senderliste",
    "softcam": "Softcam",
    "tuner": "Tuner",
    "weather": "Wetter",
    "vpn": "VPN",
    "clock": "Uhr",
    "eventview": "EventView",
    "ev": "EventView",
    "progress": "Progress",
    "emcsel": "EMC Senderliste",
    "movsel": "MovieSelection",
    "mini_tv": "MiniTV",
    "volume": "Lautstärke",
    "poster_i_now": "Poster Infobar Jetzt",
    "poster_i_next": "Poster Infobar Danach",
}
