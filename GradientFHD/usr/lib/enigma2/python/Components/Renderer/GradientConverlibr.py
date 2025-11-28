#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Unified helper library for Gradient* renderers.

Funktionen:
- quoteEventName: URL-encode event names for HTTP-Anfragen
- REGEX: einfaches Pattern zum Abschneiden von EPG-Müll (für Kompatibilität)
- cutName: Event-Titel aufräumen (Episoden, Staffeln, Altersangaben, etc. weg)
- getCleanTitle: kleine Nachbearbeitung (Kompatibilität)
- sanitize_filename: Dateinamen-Anteil säubern
- convtext: normalisierter Such-/Titel-Slug

Python 2/3 kompatibel.
"""

from re import sub, I, compile, DOTALL
from unicodedata import normalize
import sys

try:
    from six import text_type
except ImportError:  # fallback wenn six nicht vorhanden
    text_type = type(u"")

PY3 = sys.version_info[0] >= 3
if PY3:
    import html as _html
    from urllib.parse import quote_plus
else:
    from HTMLParser import HTMLParser as _HTMLParser
    _html = _HTMLParser()
    from urllib import quote_plus


def quoteEventName(eventName):
    """URL-encode event names für externe HTTP-Abfragen (TMDb, IMDb, Google...)."""
    try:
        text = eventName.decode('utf8').replace(u'\x86', u'').replace(u'\x87', u'').encode('utf8')
    except Exception:
        text = eventName
    return quote_plus(text, safe="+")


# Vereinfachtes REGEX für Rückwärts-Kompatibilität
REGEX = compile(
    r"\s\*\d{4}\Z|"      # " *2024" am Ende
    r"[\( \[ ].*?[ \) \]]|"  # Text in () oder []
    r"[:!]|"             # Doppelpunkte / Ausrufezeichen
    r"\s-\s.*",          # " - Rest" abschneiden
    DOTALL,
)


def _unicodify(s, encoding='utf-8', norm=None):
    if not isinstance(s, text_type):
        s = text_type(s, encoding, errors='ignore')
    if norm:
        s = normalize(norm, s)
    return s


def remove_accents(string):
    """Akzente entfernen, aber ASCII-Buchstaben behalten."""
    s = _unicodify(string, norm='NFD')
    return u''.join(ch for ch in s if not (u'\u0300' <= ch <= u'\u036f'))


def cutName(eventName=u""):
    """
    EPG-Titel aufräumen, Hauptnamen erhalten.

    - Episodenmuster (odc., ep., episode) am Ende entfernen
    - finale Staffel-/Episodennummern entfernen
    - Altersangaben (16+, (12+), ...) entfernen
    - Sonderzeichen einkürzen, Leerzeichen normalisieren
    """
    if not eventName:
        return u""

    ev = _unicodify(eventName, norm='NFC')

    # reine Zahlen unverändert lassen
    if ev.isdigit():
        return ev

    # kleines kosmetisches Beispiel wie im Original
    ev = ev.replace(u'&', u'e')

    # lange numerische IDs am Anfang wie "1234567890-..." weg
    if not ev[:2].isdigit() and not ev[:3].isdigit():
        ev = sub(r'^\d{10}-', u'', ev)

    # Episoden-Indikatoren am Ende entfernen (odc.123, ep.5, episode 3)
    ev = sub(r'[:\s]*\( ?(:?odc\.?\s*\d+|ep\.?\s*\d+|episode\.?\s*\d+) \)?$', u'', ev, flags=I)

    # Muster wie "2-8" am Ende -> "2"
    ev = sub(r'(\d+)[\s-]*(\d+)$', r'\1', ev)

    # einzelne Staffelnummern (2, 11, II, ...) am Ende kappen
    ev = sub(r'\s*(\d+|I{1,3}|IV|V|VI|VII|VIII|IX|X)$', u'', ev)

    # ein paar bekannte Störwörter
    terms_to_remove = [
        u'AXN', u'AXN Black', u'AXN White', u'Regina -', u'Live:', u'LIVE: ',
        u'Prima', u'programu', u'filter cine34', u'cine34', u'Episode', u'Ep', u'Top 10 - ',
    ]
    for term in terms_to_remove:
        ev = ev.replace(term, u'')

    # Altersangaben etc.
    for age in (u'18+', u'(18+)', u'16+', u'(16+)', u'12+', u'(12+)',
                u'7+', u'(7+)', u'6+', u'(6+)', u'0+', u'(0+)'):
        ev = ev.replace(age, u'')
    ev = ev.replace(u'+', u'')

    # Doppelpunkte/Minus -> Leerzeichen, Restliche Sonderzeichen raus
    ev = sub(r'[:\-]', u' ', ev)
    ev = sub(r'[^\w\s]', u' ', ev)
    ev = sub(r'\s+', u' ', ev).strip()
    return ev


def getCleanTitle(eventitle=u""):
    """Historischer Helper, nur für Rückwärts-Kompatibilität."""
    if not eventitle:
        return u""
    ev = _unicodify(eventitle)
    return ev.replace(u' ^`^s', u'').replace(u' ^`^y', u'')


def sanitize_filename(filename):
    """Dateinamen-sicher: nur Buchstaben/Zahlen/Leerzeichen/Minus/Unterstrich."""
    if not filename:
        return u""
    fn = _unicodify(filename)
    fn = sub(r'[^\w\s-]', u'', fn)
    return fn.strip()


def convtext(text=u""):
    """
    Normalisierter Slug für Suche + Dateinamen.

    - Akzente vereinheitlichen
    - technische Tags (1080p, HDTV, WEB-DL, ...) entfernen
    - cutName + getCleanTitle anwenden
    - Kleinbuchstaben, nur [A-Za-z0-9_] + Leerzeichen

    Beispiele:
        "Suits" -> "suits"
        "Detektiv Rockford – Anruf genügt" -> "detektiv rockford anruf genugt"
        "Hunde außer Kontrolle" -> "hunde außer kontrolle"
        "Die Rosenheim-Cops" -> "die rosenheim cops"
    """
    if not text:
        return u""

    t = _unicodify(text, norm='NFC')
    # EPG-Markup entfernen
    t = t.replace(u'\x86', u'').replace(u'\x87', u'')
    t = t.strip().lower()

    # typische Qualitäts-/Release-Tags entfernen
    junk = [
        u'1080p', u'1080i', u'720p', u'hdtv', u'web-dl', u'webrip', u'webhdrip', u'webhdtv',
        u'bdrip', u'dvdrip', u'dvdscr', u'bluray', u'brrip', u'xvid', u'x264', u'h264', u'avc',
        u'dts', u'ac3', u'ac3d', u'ac3md', u'dd51', u'retail', u'unrated', u'uncut', u'complete',
        u'internal', u'repack', u'sync', u'line.dubbed', u'dubbed',
    ]
    for j in junk:
        t = t.replace(j, u'')

    # Titelbereinigung
    t = cutName(t)
    t = getCleanTitle(t)

    # "xyz the" -> "the xyz" (falls gewünscht, wie im Original)
    if t.endswith(u' the'):
        t = u'the ' + t[:-4]

    # Akzente entfernen
    t = remove_accents(t)

    # nur Wortzeichen + Leerzeichen
    t = sub(r'[^\w\s]', u' ', t)
    t = sub(r'\s+', u' ', t).strip()

    return t
