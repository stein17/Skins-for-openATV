import re
# 02.26 @stein17, Many new features and improvements
# ------------------------------------------------------------
# TVDb helpers: UUID(v4) vs legacy/no-key web fallback
# ------------------------------------------------------------
_TVDB_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

def _is_tvdb_uuid_key(api_key):
    try:
        return True if _TVDB_UUID_RE.match((api_key or '').strip()) else False
    except Exception:
        return False


# ------------------------------------------------------------
# TVDb legacy XML API (requires only legacy key; can be built-in)
# ------------------------------------------------------------
import xml.etree.ElementTree as _ET

_TVDB_HEX32_RE = re.compile(r"^[0-9a-fA-F]{32}$")

def _is_tvdb_hex32_key(api_key):
    try:
        value = (api_key or '').strip()
        return value == FALLBACK_API_MARKER or bool(_TVDB_HEX32_RE.match(value))
    except Exception:
        return False

def _tvdb_legacy_get_series_id(query, lang='de'):
    """Search series id via legacy GetSeries.php (no auth)."""
    q = (query or '').strip()
    if not q:
        return None
    try:
        url = "https://thetvdb.com/api/GetSeries.php?seriesname=%s&language=%s" % (requests.utils.quote(q), (lang or 'en'))
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
        if r.status_code != 200 or not (r.text or '').strip():
            return None
        root = _ET.fromstring(r.text.encode('utf-8') if isinstance(r.text, str) else r.text)
        # The XML varies: sometimes <Series><seriesid>, sometimes <Series><id>
        for series in root.findall('.//Series'):
            sid = None
            for tag in ('seriesid','id'):
                el = series.find(tag)
                if el is not None and (el.text or '').strip():
                    sid = (el.text or '').strip()
                    break
            if sid:
                return sid
    except Exception:
        return None
    return None

def _tvdb_legacy_get_banners_xml(api_key, series_id):
    if not api_key or not series_id:
        return None
    try:
        url = "https://thetvdb.com/api/%s/series/%s/banners.xml" % (api_key.strip(), str(series_id).strip())
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.status_code != 200 or not (r.text or '').strip():
            return None
        return r.text
    except Exception:
        return None

def _tvdb_legacy_pick_banner(banners_xml, want='poster', prefer_langs=('de','en','')):
    """want: 'poster' or 'fanart'"""
    if not banners_xml:
        return None
    try:
        root = _ET.fromstring(banners_xml.encode('utf-8') if isinstance(banners_xml, str) else banners_xml)
        candidates = []
        for b in root.findall('.//Banner'):
            btype = ((b.findtext('BannerType') or '')).strip().lower()
            btype2 = ((b.findtext('BannerType2') or '')).strip().lower()
            lang = ((b.findtext('Language') or '')).strip().lower()
            path = (b.findtext('BannerPath') or '').strip()
            if not path:
                continue
            if want == 'poster':
                if btype != 'poster' and btype2 != 'poster':
                    continue
            else:  # fanart/backdrop
                if btype != 'fanart' and btype2 != 'fanart':
                    continue
            candidates.append((lang, path))
        if not candidates:
            return None
        # prefer language order
        for pl in prefer_langs:
            pl = (pl or '').lower()
            for lang, path in candidates:
                if (lang or '') == pl:
                    return path
        # otherwise first
        return candidates[0][1]
    except Exception:
        return None

def _tvdb_legacy_banner_url(banner_path):
    if not banner_path:
        return None
    p = banner_path.lstrip('/')
    # artworks host serves legacy banners paths
    return "https://artworks.thetvdb.com/banners/%s" % p

def _tvdb_legacy_search(api_key, query, want='poster', prefer_langs=('de','en','')):
    """Legacy search: GetSeries.php -> banners.xml -> pick poster/fanart."""
    q = (query or '').strip()
    if not q:
        return None
    # Try DE then EN search id to cover German EPG titles
    sid = _tvdb_legacy_get_series_id(q, 'de') or _tvdb_legacy_get_series_id(q, 'en')
    if not sid:
        return None
    bx = _tvdb_legacy_get_banners_xml(api_key, sid)
    if not bx:
        return None
    path = _tvdb_legacy_pick_banner(bx, want=want, prefer_langs=prefer_langs)
    return _tvdb_legacy_banner_url(path) if path else None

def _tvdb_web_find_first_series_url(query):
    """Fallback that does NOT require an API key.
    It scrapes the TVDb website search page to obtain a series page URL.
    This is best-effort and may break if TVDb changes HTML."""
    q = (query or '').strip()
    if not q:
        return None
    try:
        url = "https://thetvdb.com/search?query=%s" % requests.utils.quote(q)
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
        if r.status_code != 200:
            return None
        html = r.text or ""
        # Prefer explicit /series/ links
        m = re.search(r'href="(/series/[^"]+)"', html)
        if not m:
            return None
        return "https://thetvdb.com%s" % m.group(1)
    except Exception:
        return None

def _tvdb_web_extract_poster_url(series_url):
    """Extract a poster URL from a TVDb series page (best-effort)."""
    if not series_url:
        return None
    try:
        r = requests.get(series_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
        if r.status_code != 200:
            return None
        html = r.text or ""
        # Look for artworks.thetvdb.com poster URLs (v4 or legacy)
        # v4 example: https://artworks.thetvdb.com/banners/v4/series/<id>/posters/<hash>.jpg
        m = re.search(r'(https://artworks\.thetvdb\.com/banners/(?:v4/series/[^"]+/posters/[^"]+\.jpg|posters/[^"]+\.jpg))', html)
        if m:
            return m.group(1)
        # fallback: any artworks jpg that includes /posters/
        m = re.search(r'(https://artworks\.thetvdb\.com/[^"]*posters[^"]*\.jpg)', html)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None

def _tvdb_web_search_poster(query):
    series_url = _tvdb_web_find_first_series_url(query)
    if not series_url:
        return None
    return _tvdb_web_extract_poster_url(series_url)

# BUGFIX VERSION - callInThread zu synchronem Aufruf geändert für korrekte Datei-Existenz-Prüfung
#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
OPTIMIERTE GradientFHDBackdropXDownloadThread.py
Fuer GradientFHD Skin

NEUE FEATURES:
1. Title Mappings fuer deutsche Sendungen (beliebig erweiterbar)
2. JSON-Speicherung fuer Rating-Sterne und Altersfreigabe
3. Erweiterte Sport-Keywords
4. Kuerzere Timeouts (3-6 Sek) fuer fluessigeren Betrieb
5. Erweiterte checkTV-Liste fuer Magazine, Sport, Dokus
6. HTTPAdapter mit Retry-Mechanismus

INSTALLATION:
Ersetze die bestehende GradientFHDBackdropXDownloadThread.py damit.
"""

# ============================================================================
# IMPORTS
# ============================================================================
from Components.config import config
from PIL import Image
from enigma import getDesktop
import os
import shutil
import re
import requests
import time
import json
import socket
import sys
import threading
import difflib
import unicodedata
import random
import json
import time
from random import choice
from requests import get, exceptions
from twisted.internet.reactor import callInThread

try:
    from .GradientFHDConverlibr import quoteEventName, cutName, REGEX, convtext, apply_title_mapping, get_canonical_slug, normalize_title_for_filename, is_daily_series, get_search_variants, get_min_score_for_title, check_for_existing_file
except:
    from GradientFHDConverlibr import quoteEventName, cutName, REGEX, convtext, apply_title_mapping, get_canonical_slug, normalize_title_for_filename, is_daily_series, get_search_variants, get_min_score_for_title, check_for_existing_file


# ---------------------------------------------------------------------------
# Canonical title handling / provider overrides (stein17)
# ---------------------------------------------------------------------------

PROVIDER_OVERRIDES = {
    # Punkt 6/7/8: IMDb liefert oft Portrait/zu klein (Backdrop-Validator),
    # deshalb Google als Fallback immer zulassen.
    "punkt_6":  ["imdb", "google"],
    "punkt_7":  ["imdb", "google"],
    # Punkt 8: IMDb ist meist korrekt, aber wird gelegentlich geblockt oder liefert kein brauchbares 16:9.
    # Deshalb Google als Fallback zulassen.
    "punkt_8":  ["imdb", "google"],
    "punkt_12": ["tmdb", "imdb", "tvdb", "fanart", "google"],
}

SKIP_TITLES = set([
    "sendepause",
])

GROUP_PREFIXES = [
    "ultimate_rush",
]

def _strip_episode_tokens(t):
    if not t:
        return ""
    t = re.sub(r"\(\s*S\d+\s*/\s*E\d+\s*\)", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\bS\d+\s*/\s*E\d+\b", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\bS\d+\s*E\d+\b", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\(\s*\d{2,6}\s*\)", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def get_base_title(title):
    t = _strip_episode_tokens(str(title or ""))
    if not t:
        return ""
    slug = get_canonical_slug(t)
    for pref in GROUP_PREFIXES:
        if slug == pref or slug.startswith(pref + "_"):
            return pref.replace("_", " ")
    return t

def get_store_slug(title):
    base = get_base_title(title)
    return get_canonical_slug(base) if base else get_canonical_slug(title)

def get_provider_override(title):
    return PROVIDER_OVERRIDES.get(get_store_slug(title))

_URL_CACHE = {}

def _single_info_mode():
    try:
        return os.path.exists(os.path.join(xtra_base, '.single_info_json')) or os.path.exists(os.path.join(xtra_base, 'custom', '.single_info_json'))
    except Exception:
        return False


def _prime_url_cache():
    try:
        if not os.path.isdir(path_folder):
            return
        if _single_info_mode():
            if not os.path.isdir(info_folder):
                return
            for fn in os.listdir(info_folder):
                if not fn.endswith(".json"):
                    continue
                try:
                    data = json.load(open(os.path.join(info_folder, fn)))
                    url = data.get("backdrop_url") or data.get("tvdb_backdrop_url")
                    if not url:
                        continue
                    slug = os.path.splitext(fn)[0]
                    local = os.path.join(path_folder, slug + ".jpg")
                    if os.path.exists(local):
                        _URL_CACHE[url] = local
                except Exception:
                    continue
            return
        if not os.path.isdir(backdrop_info_folder):
            return
        for fn in os.listdir(backdrop_info_folder):
            if not fn.endswith(".json"):
                continue
            try:
                data = json.load(open(os.path.join(backdrop_info_folder, fn)))
                url = data.get("backdrop_url")
                if not url:
                    continue
                slug = os.path.splitext(fn)[0]
                local = os.path.join(path_folder, slug + ".jpg")
                if os.path.exists(local):
                    _URL_CACHE[url] = local
            except Exception:
                continue
    except Exception:
        pass
try:
    from .GradientFHD_event_info import GradientFHD_event_info
except:
    try:
        from GradientFHD_event_info import GradientFHD_event_info
    except:
        GradientFHD_event_info = None

try:
    from http.client import HTTPConnection
    HTTPConnection.debuglevel = 0
except ImportError:
    from httplib import HTTPConnection
    HTTPConnection.debuglevel = 0

from requests.adapters import HTTPAdapter, Retry
from Components.Renderer.GradientFHDAPIProxy import FALLBACK_API_MARKER, wrap_get, wrap_requests

requests = wrap_requests(requests)
get = wrap_get(get)

# ============================================================================
# PYTHON VERSION
# ============================================================================
PY3 = sys.version_info[0] >= 3
if PY3:
    import html
    html_parser = html
    from urllib.error import URLError, HTTPError
    from urllib.request import urlopen
    from urllib.parse import quote_plus
else:
    from HTMLParser import HTMLParser
    html = HTMLParser()
    from urllib2 import URLError, HTTPError, urlopen
    from urllib import quote_plus

# ============================================================================
# CONFIGURATION
# ============================================================================
DEBUG_BACKDROP = False  # Set to True for debugging

# API Keys (koennen durch skin-spezifische Keys ueberschrieben werden)
tmdb_api = FALLBACK_API_MARKER
omdb_api = FALLBACK_API_MARKER

# ============================================================================
# FIX: Telenovela/Daily-Serie Erkennung (automatisch eingefügt)
# ============================================================================
TELENOVELA_TITLES = {
    'gute zeiten schlechte zeiten', 'gzsz',
    'unter uns',
    'alles was zählt', 'alles was zaehlt', 'awz',
    'sturm der liebe',
    'rote rosen',
    'verbotene liebe',
    'berlin tag und nacht', 'berlin tag & nacht',
    'köln 50667', 'koeln 50667', 'koln 50667',
    'krass schule',
    'in aller freundschaft',
}

def is_telenovela(title):
    """Prüft ob es eine tägliche Serie/Telenovela ist."""
    if not title:
        return False
    title_lower = title.lower().strip()
    title_clean = re.sub(r'\s*-?\s*[Ff]olge\s*\d+.*$', '', title_lower)
    title_clean = re.sub(r'\s*\(\d+\)\s*$', '', title_clean).strip()
    for tele in TELENOVELA_TITLES:
        if title_clean == tele or title_clean.startswith(tele):
            return True
    return False

def get_telenovela_base_title(title):
    """Extrahiert Basis-Titel ohne Episodennummer."""
    if not title:
        return title
    patterns = [
        r'\s*-?\s*[Ff]olge\s*\d+.*$',
        r'\s*\(\d+\)\s*$',
        r'\s*[Ee]pisode\s*\d+.*$',
    ]
    result = title
    for pattern in patterns:
        result = re.sub(pattern, '', result, flags=re.I)
    return result.strip()


thetvdbkey = FALLBACK_API_MARKER


# ============================================================================
# TheTVDB v4 support (optional)
# ============================================================================
# If the user enters a TheTVDB v4 API key (UUID), the old legacy XML endpoints
# will not work. We therefore detect UUID keys and use the v4 JSON API.
#
# Legacy XML (old):
#   https://thetvdb.com/api/<LEGACY_KEY>/series/<ID>/<lang>.xml
# v4 JSON (new):
#   POST https://api4.thetvdb.com/v4/login    {"apikey":"...", "pin":"..."?}
#   GET  https://api4.thetvdb.com/v4/search?query=...&type=series
#   GET  https://api4.thetvdb.com/v4/series/<id>/artworks
#
# Optional PIN:
#   Some user-supported keys require a PIN. You may create a file:
#     /usr/share/enigma2/<skin>/thetvdbpin
#   with the PIN in the first line.
# ============================================================================

import json

_TVDB_V4_TOKEN = None
_TVDB_V4_TOKEN_TS = 0


def _is_tvdb_v4_key(key):
    try:
        key = (key or '').strip()
        return bool(re.match(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', key))
    except Exception:
        return False


def _tvdb_v4_artwork_url(p):
    p = (p or '').strip()
    if not p:
        return None
    if p.startswith('http://') or p.startswith('https://'):
        return p
    p = p.lstrip('/')
    return 'https://artworks.thetvdb.com/banners/%s' % p


def _tvdb_skin_dir():
    try:
        cur = config.skin.primary_skin.value.replace('/skin.xml', '')
        return '/usr/share/enigma2/%s' % cur
    except Exception:
        return '/usr/share/enigma2/GradientFHD'


def _tvdb_v4_pin_from_file():
    try:
        p = os.path.join(_tvdb_skin_dir(), 'thetvdbpin')
        if os.path.exists(p):
            with open(p, 'r') as f:
                v = (f.read() or '').strip()
            return v or None
    except Exception:
        pass
    return None


def _tvdb_v4_get_token(api_key, log=None, search_title=None):  # FIX: Parameter erweitert
    global _TVDB_V4_TOKEN, _TVDB_V4_TOKEN_TS

    api_key = (api_key or '').strip()
    if not api_key:
        return None

    try:
        if _TVDB_V4_TOKEN and (time.time() - _TVDB_V4_TOKEN_TS) < 20 * 3600:
            return _TVDB_V4_TOKEN
    except Exception:
        pass

    url = 'https://api4.thetvdb.com/v4/login'
    payload = {'apikey': api_key}

    pin = _tvdb_v4_pin_from_file()
    if pin:
        payload['pin'] = pin

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            if log:
                log('TVDB v4 login failed: HTTP %s' % r.status_code)
            return None
        j = r.json() if hasattr(r, 'json') else json.loads(r.text)
        token = (((j or {}).get('data') or {}).get('token') or '').strip()
        if not token:
            if log:
                log('TVDB v4 login failed: no token in response')
            return None
        _TVDB_V4_TOKEN = token
        _TVDB_V4_TOKEN_TS = time.time()
        return token
    except Exception as e:
        if log:
            log('TVDB v4 login exception: %s [Sendung: %s]' % (str(e), search_title or '?'))  # FIX: Sendungsname
        return None


def _tvdb_v4_get(api_key, endpoint, params=None, log=None, search_title=None):  # FIX: Parameter erweitert
    token = _tvdb_v4_get_token(api_key, log=log)
    if not token:
        return None
    url = 'https://api4.thetvdb.com/v4/%s' % endpoint.lstrip('/')
    headers = {
        'Authorization': 'Bearer %s' % token,
        'Accept': 'application/json',
    }
    try:
        r = requests.get(url, headers=headers, params=params or {}, timeout=10)
        if r.status_code != 200:
            if log:
                log('TVDB v4 GET failed: %s HTTP %s' % (endpoint, r.status_code))
            return None
        return r.json()
    except Exception as e:
        if log:
            log('TVDB v4 GET exception: %s' % str(e))
        return None


def _tvdb_v4_search_series(api_key, query, log=None):  # FIX: Logging verbessert
    query = (query or '').strip()
    if not query:
        return None, None
    
    # FIX: Verbessertes Logging - zeigt WELCHE SENDUNG gesucht wird (BACKDROP!)
    if log:
        log('>>> TVDB v4 BACKDROP-Suche für: "%s"' % query)

    j = _tvdb_v4_get(api_key, '/search', params={'query': query, 'type': 'series', 'language': 'deu', 'limit': 10}, log=log)
    if not j:
        return None, None

    data = j.get('data') or []
    if not isinstance(data, list) or not data:
        return None, None

    it = data[0] or {}
    tvdb_id = it.get('tvdb_id') or it.get('id')
    try:
        tvdb_id = int(tvdb_id)
    except Exception:
        tvdb_id = None

    poster = it.get('poster') or it.get('image_url') or it.get('thumbnail')
    return tvdb_id, _tvdb_v4_artwork_url(poster)


def _tvdb_v4_best_backdrop(api_key, tvdb_id, log=None, search_title=None):  # FIX: Parameter erweitert
    if not tvdb_id:
        return None
    
    # FIX: Log entfernt (zu verbose) - wird am Ende mit URL geloggt
    # search_title wird für "nicht gefunden" Log verwendet
    _search_title = search_title  # Speichere für später

    j = _tvdb_v4_get(api_key, '/series/%s/artworks' % tvdb_id, params={'lang': 'deu'}, log=log)
    if not j:
        return None

    data = j.get('data')
    artworks = None

    if isinstance(data, dict):
        artworks = data.get('artworks') or data.get('images')
    elif isinstance(data, list):
        artworks = data

    if not isinstance(artworks, list) or not artworks:
        return None

    best = None
    for a in artworks:
        if not isinstance(a, dict):
            continue
        img = a.get('image') or a.get('image_url') or a.get('thumbnail')
        if not img:
            continue
        w = a.get('width') or 0
        h = a.get('height') or 0
        try:
            w = int(w)
            h = int(h)
        except Exception:
            w, h = 0, 0

        if h and w and w < h:
            continue

        score = a.get('score') or 0
        cand = (w, score, img)
        if best is None or cand[0] > best[0] or (cand[0] == best[0] and cand[1] > best[1]):
            best = cand

    if not best:
        if log:
            log('<<< TVDB v4 Kein Backdrop für: "%s"' % (_search_title or 'ID=%s' % tvdb_id))
        return None

    # Log wird beim Aufruf gemacht, hier nicht nötig
    # ID und URL werden dort angezeigt
    
    return _tvdb_v4_artwork_url(best[2])

fanart_api = FALLBACK_API_MARKER

# Sprache
try:
    lng = config.osd.language.value
    lng = lng[:-3]
except:
    lng = 'de'

# ============================================================================
# TITLE MAPPINGS - HIER BELIEBIG ERWEITERN!
# ============================================================================
# Format: 'suchbegriff_kleinschreibung': 'Korrekter TMDb/IMDb Titel'

TITLE_MAPPINGS = {
    # ============ DAILY SOAPS ============
    'gzsz': 'Gute Zeiten, schlechte Zeiten',
    'gute zeiten schlechte zeiten': 'Gute Zeiten, schlechte Zeiten',
    'unter uns': 'Unter uns',
    'alles was zaehlt': 'Alles was zaehlt',
    'awz': 'Alles was zaehlt',
    'sturm der liebe': 'Sturm der Liebe',
    'rote rosen': 'Rote Rosen',
    'verbotene liebe': 'Verbotene Liebe',
    'lindenstrasse': 'Lindenstrasse',
    'marienhof': 'Marienhof',
    'berlin tag und nacht': 'Berlin - Tag & Nacht',
    'koeln 50667': 'Koeln 50667',
    
    # ============ NACHRICHTEN ============
    'tagesschau': 'Tagesschau',
    'tagesthemen': 'Tagesthemen',
    'heute': 'heute',
    'heute journal': 'heute-journal',
    'heute-journal': 'heute-journal',
    'heute show': 'heute-show',
    'heute-show': 'heute-show',
    'rtl aktuell': 'RTL Aktuell',
    'sat.1 nachrichten': 'SAT.1 Nachrichten',
    'newstime': 'Newstime',
    'punkt 12': 'Punkt 12',
    
    # ============ MAGAZINE ============
    'mittagsmagazin': 'Mittagsmagazin',
    'moma': 'Morgenmagazin',
    'morgenmagazin': 'Morgenmagazin',
    'brisant': 'Brisant',
    'leute heute': 'Leute heute',
    'hallo deutschland': 'hallo deutschland',
    'explosiv': 'Explosiv - Das Magazin',
    'taff': 'taff',
    'galileo': 'Galileo',
    'abenteuer leben': 'Abenteuer Leben',
    'wiso': 'WISO',
    'frontal': 'Frontal 21',
    'panorama': 'Panorama',
    'report': 'Report',
    'monitor': 'Monitor',
    'kontraste': 'Kontraste',
    'exakt': 'Exakt',
    'fakt': 'Fakt',
    'extra': 'Extra - Das RTL Magazin',
    'stern tv': 'stern TV',
    
    # ============ TALK SHOWS ============
    'maischberger': 'Maischberger',
    'anne will': 'Anne Will',
    'hart aber fair': 'hart aber fair',
    'markus lanz': 'Markus Lanz',
    'maybrit illner': 'Maybrit Illner',
    'sandra maischberger': 'Maischberger',
    'ndr talk show': 'NDR Talk Show',
    'koelner treff': 'Koelner Treff',
    '3 nach 9': '3 nach 9',
    'riverboat': 'Riverboat',
    
    # ============ GAME SHOWS ============
    'wer wird millionaer': 'Wer wird Millionaer?',
    'wwm': 'Wer wird Millionaer?',
    'das supertalent': 'Das Supertalent',
    'dsds': 'Deutschland sucht den Superstar',
    'deutschland sucht den superstar': 'Deutschland sucht den Superstar',
    'the voice of germany': 'The Voice of Germany',
    'the voice': 'The Voice of Germany',
    'the masked singer': 'The Masked Singer',
    'joko und klaas': 'Joko & Klaas gegen ProSieben',
    'schlag den star': 'Schlag den Star',
    'schlag den raab': 'Schlag den Raab',
    'genial daneben': 'Genial daneben',
    'das quiz': 'Das Quiz',
    'gefragt gejagt': 'Gefragt - Gejagt',
    'der preis ist heiss': 'Der Preis ist heiss',
    'bares fuer rares': 'Bares fuer Rares',
    'die hoehle der loewen': 'Die Hoehle der Loewen',
    
    # ============ COMEDY ============
    'tv total': 'TV total',
    'late night berlin': 'Late Night Berlin',
    'extra 3': 'extra 3',
    'die anstalt': 'Die Anstalt',
    'neo magazin royale': 'NEO MAGAZIN ROYALE',
    'zdf magazin royale': 'ZDF Magazin Royale',
    'nuhr im ersten': 'Nuhr im Ersten',
    'nightwash': 'NightWash',
    'quatsch comedy club': 'Quatsch Comedy Club',
    
    # ============ SPORT ============
    'sportschau': 'Sportschau',
    'das aktuelle sportstudio': 'das aktuelle sportstudio',
    'sportstudio': 'das aktuelle sportstudio',
    'champions league': 'UEFA Champions League',
    'uefa champions league': 'UEFA Champions League',
    'europa league': 'UEFA Europa League',
    'uefa europa league': 'UEFA Europa League',
    'bundesliga': 'Bundesliga',
    'dfb pokal': 'DFB-Pokal',
    'dfb-pokal': 'DFB-Pokal',
    'formel 1': 'Formula 1',
    'formula 1': 'Formula 1',
    'f1': 'Formula 1',
    'motogp': 'MotoGP',
    'tennis': 'Tennis',
    'wimbledon': 'Wimbledon',
    'us open': 'US Open',
    'olympia': 'Olympic Games',
    'olympische spiele': 'Olympic Games',
    'tour de france': 'Tour de France',
    'ski alpin': 'FIS Alpine Ski World Cup',
    'biathlon': 'Biathlon World Cup',
    'handball': 'Handball',
    'handball wm': 'IHF World Championship',
    'basketball': 'Basketball',
    'nba': 'NBA',
    'nfl': 'NFL',
    'american football': 'NFL',
    'boxen': 'Boxing',
    'ufc': 'UFC',
    'ran': 'ran',
    'sky sport': 'Sky Sport',
    'dazn': 'DAZN',
    
    # ============ KRIMI / SERIEN ============
    'tatort': 'Tatort',
    'polizeiruf 110': 'Polizeiruf 110',
    'der alte': 'Der Alte',
    'soko': 'SOKO',
    'soko muenchen': 'SOKO Muenchen',
    'soko koeln': 'SOKO Koeln',
    'soko leipzig': 'SOKO Leipzig',
    'soko wien': 'SOKO Wien',
    'soko stuttgart': 'SOKO Stuttgart',
    'alarm fuer cobra 11': 'Alarm fuer Cobra 11 - Die Autobahnpolizei',
    'cobra 11': 'Alarm fuer Cobra 11 - Die Autobahnpolizei',
    'ein fall fuer zwei': 'Ein Fall fuer zwei',
    'der bergdoktor': 'Der Bergdoktor',
    'die rosenheim cops': 'Die Rosenheim-Cops',
    'rosenheim cops': 'Die Rosenheim-Cops',
    'in aller freundschaft': 'In aller Freundschaft',
    'grossstadtrevier': 'Grossstadtrevier',
    'notruf hafenkante': 'Notruf Hafenkante',
    
    # ============ DOKUMENTATIONEN ============
    'terra x': 'Terra X',
    'planet erde': 'Planet Earth',
    'planet earth': 'Planet Earth',
    'unsere erde': 'Our Planet',
    'wildes deutschland': 'Wildes Deutschland',
    'abenteuer wildnis': 'Abenteuer Wildnis',
    'universum': 'Universum',
    'die story': 'Die Story',
    'zdfzeit': 'ZDFzeit',
    'phoenix': 'Phoenix',
    'arte': 'ARTE',
    '37 grad': '37 Grad',
    'die reportage': 'Die Reportage',
    
    # ============ KINDER ============
    'die sendung mit der maus': 'Die Sendung mit der Maus',
    'sendung mit der maus': 'Die Sendung mit der Maus',
    'loewenzahn': 'Loewenzahn',
    'logo': 'logo!',
    'kika': 'KiKA',
    'sesamstrasse': 'Sesamstrasse',
    'sandmaennchen': 'Unser Sandmaennchen',
    'bibi blocksberg': 'Bibi Blocksberg',
    'bibi und tina': 'Bibi & Tina',
    'wickie': 'Wickie und die starken Maenner',
    'benjamin bluemchen': 'Benjamin Bluemchen',
    'peppa wutz': 'Peppa Pig',
    'paw patrol': 'PAW Patrol',
    
    # ============ REALITY / DATING ============
    'der bachelor': 'Der Bachelor',
    'die bachelorette': 'Die Bachelorette',
    'bachelor in paradise': 'Bachelor in Paradise',
    'temptation island': 'Temptation Island',
    'love island': 'Love Island',
    'are you the one': 'Are You the One?',
    'first dates': 'First Dates',
    'schwiegertochter gesucht': 'Schwiegertochter gesucht',
    'bauer sucht frau': 'Bauer sucht Frau',
    'promi big brother': 'Promi Big Brother',
    'big brother': 'Big Brother',
    'ich bin ein star': "I'm a Celebrity...Get Me Out of Here!",
    'dschungelcamp': "I'm a Celebrity...Get Me Out of Here!",
    'sommerhaus der stars': 'Das Sommerhaus der Stars',
    'kampf der realitystars': 'Kampf der Realitystars',
    'das perfekte dinner': 'Das perfekte Dinner',
    'kitchen impossible': 'Kitchen Impossible',
    'grill den henssler': 'Grill den Henssler',
    
    # ============ OESTERREICH ============
    'zeit im bild': 'Zeit im Bild',
    'zib': 'Zeit im Bild',
    'willkommen oesterreich': 'Willkommen Oesterreich',
    
    # ============ SCHWEIZ ============
    'tagesschau srf': 'Tagesschau SRF',
    '10 vor 10': '10 vor 10',

    
    # ============ v2.3: IHRE SENDER ============
    'ulrich wetzel das strafgericht': 'Ulrich Wetzel',
    'ulrich wetzel': 'Ulrich Wetzel',
    'barbara salesch das strafgericht': 'Barbara Salesch',
    'barbara salesch': 'Barbara Salesch',
    'der blaulicht report': 'Der Blaulicht Report',
    'der blaulicht report die neuen einsatze': 'Der Blaulicht Report',
    'der trodeltrupp': 'Der Trödeltrupp',
    'der trodeltrupp das geld liegt im keller': 'Der Trödeltrupp',
    'armes deutschland': 'Armes Deutschland',
    'armes deutschland stempeln oder abrackern': 'Armes Deutschland',
    'lebensretter hautnah': 'Lebensretter hautnah',
    'lebensretter hautnah wenn jede sekunde zahlt': 'Lebensretter hautnah',
    'das duell zwischen tull und tranen': 'Zwischen Tüll und Tränen',
    'traumhaus am strand gesucht': 'Beach Front Bargain Hunt',
    'die kuchenschlacht': 'Die Küchenschlacht',
    'jag im auftrag der ehre': 'JAG',
    'mayday alarm im cockpit': 'Air Crash Investigation',
}

# ============================================================================
# SPORT KEYWORD MAPPING - Fuer dynamische Sport-Titel
# ============================================================================
SPORT_KEYWORDS = {
    'fussball': 'Football',
    'bundesliga': 'Bundesliga',
    'champions league': 'UEFA Champions League',
    'europa league': 'UEFA Europa League',
    'dfb pokal': 'DFB-Pokal',
    'dfb-pokal': 'DFB-Pokal', 
    'formel 1': 'Formula 1',
    'formel1': 'Formula 1',
    'f1': 'Formula 1',
    'motogp': 'MotoGP',
    'tennis': 'Tennis',
    'wimbledon': 'Wimbledon',
    'olympia': 'Olympic Games',
    'olympische': 'Olympic Games',
    'tour de france': 'Tour de France',
    'biathlon': 'Biathlon World Cup',
    'ski': 'FIS Alpine Ski World Cup',
    'handball': 'Handball',
    'basketball': 'Basketball',
    'nba': 'NBA Basketball',
    'nfl': 'NFL Football',
    'boxen': 'Boxing',
    'ufc': 'UFC',
    'wm': 'World Championship',
    'em': 'European Championship',
    'weltmeisterschaft': 'World Championship',
    'europameisterschaft': 'European Championship',
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def getRandomUserAgent():
    useragents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/120.0.0.0',
    ]
    return random.choice(useragents)


def isMountedInRW(mount_point):
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) > 1 and parts[1] == mount_point:
                    return True
    except:
        pass
    return False


def sanitize_filename(filename):
    """Safe sanitize: never crash on None/bytes."""
    if filename is None:
        return ''
    try:
        if isinstance(filename, bytes):
            filename = filename.decode('utf-8', 'ignore')
    except Exception:
        pass
    try:
        sanitized = re.sub(r'[^\w\s-]', '', str(filename))
    except Exception:
        sanitized = ''
    return sanitized.strip()


# ============================================================================
# PATH CONFIGURATION
# ============================================================================
cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')
nobackdrop = "/usr/share/enigma2/%s/main/nobackdrop.jpg" % cur_skin
STORAGE_BASES = ("/media/hdd", "/media/usb", "/media/mmc", "/media/net", "/media/autofs")

def getPosterXBasePath():
    """Return the user selected base path for /xtra.
    Falls back to auto detection (HDD -> USB -> MMC -> NAS)."""
    try:
        sel = getattr(getattr(config.plugins, 'GradientFHD', None), 'posterXPath', None)
        if sel is not None and getattr(sel, 'value', None) and sel.value != "AUTO":
            return sel.value
    except Exception:
        pass
    for p in STORAGE_BASES:
        try:
            if os.path.exists(p) and isMountedInRW(p):
                return p
        except Exception:
            pass
    return "/media/hdd"


def _refresh_storage_paths(ensure=False):
    global base_path, xtra_base, path_folder, info_folder, backdrop_info_folder
    base_path = getPosterXBasePath()
    xtra_base = os.path.join(base_path, "xtra")

    # Backdrop folder
    path_folder = os.path.join(xtra_base, "backdrop")

    # Info folder (fuer JSON mit Rating/Parental)
    info_folder = os.path.join(xtra_base, "Info")

    # Backdrop-info folder (debug/trace: which provider was used)
    backdrop_info_folder = os.path.join(xtra_base, "backdrop_info")

    if not ensure:
        return

    # Directory creation may wake an unavailable NAS/autofs mount. Call this
    # only from a download worker, never while Enigma2 creates the renderer.
    for folder in (
        xtra_base,
        path_folder,
        info_folder,
        backdrop_info_folder,
        os.path.join(xtra_base, "poster"),
        os.path.join(xtra_base, "poster_info"),
        os.path.join(xtra_base, "custom", "poster"),
        os.path.join(xtra_base, "custom", "backdrop"),
    ):
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception:
            pass

_refresh_storage_paths(ensure=False)

# ============================================================================
# LOAD SKIN-SPECIFIC API KEYS
# Supports: tmdbkey/apikey, omdbkey, fanartkey, thetvdbkey (UUID v4 or legacy),
#           thetvdbkey_legacy (32-hex fallback), thetvdbpin
# ============================================================================
my_cur_skin = False
try:
    sd = "/usr/share/enigma2/{}".format(cur_skin)
    skin_paths = {
        "tmdb_api":          [os.path.join(sd, "tmdbkey"), os.path.join(sd, "apikey")],
        "omdb_api":          [os.path.join(sd, "omdbkey")],
        "fanart_api":        [os.path.join(sd, "fanartkey")],
        "thetvdbkey":        [os.path.join(sd, "thetvdbkey")],
        "thetvdbkey_legacy": [os.path.join(sd, "thetvdbkey_legacy")],
    }
    for key, paths in skin_paths.items():
        for path in (paths if isinstance(paths, list) else [paths]):
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        value = (f.read() or "").strip()
                except Exception:
                    value = ""
                if not value:
                    continue
                if key == "tmdb_api":
                    tmdb_api = value
                elif key == "omdb_api":
                    omdb_api = value
                elif key == "fanart_api":
                    fanart_api = value
                elif key == "thetvdbkey":
                    thetvdbkey = value
                elif key == "thetvdbkey_legacy":
                    # Only use legacy key if thetvdbkey is not already a 32-hex key
                    try:
                        import re as _re2
                        _is_hex32 = bool(_re2.match(r'^[0-9a-fA-F]{32}$', (thetvdbkey or '')))
                    except Exception:
                        _is_hex32 = False
                    if not _is_hex32:
                        thetvdbkey_legacy = value
                my_cur_skin = True
                break
except Exception:
    pass

# Keep a separate legacy key variable accessible by tvdb helpers
try:
    thetvdbkey_legacy
except NameError:
    thetvdbkey_legacy = thetvdbkey  # Built-in legacy key fallback

# ============================================================================
# IMAGE SIZES - Backdrop
# Hard cap to reduce ePicLoad / accelAlloc pressure on the box.
# ============================================================================
MAX_BACKDROP_W = 685
MAX_BACKDROP_H = 388
isz = "300,169"
bisz = "685,388"


# ============================================================================
# HTTP SESSION MIT RETRY
# ============================================================================

# ============================================================================
# v2.1 ANTI-FALSCHE-BACKDROPS FIXES
# ============================================================================
# ============================================================================
# v2.5 EXTRA MAPPINGS + TMDb matching tweaks
# - Some DE daily shows have weak/odd metadata on TMDb; allow lower match threshold for them.
LOW_SCORE_TMDB_TITLES = {
    # Court shows / daily legal
    'barbara salesch',
    'ulrich wetzel',
    'barbara salesch das strafgericht',
    'ulrich wetzel das strafgericht',
    'das strafgericht',
    'richter alexander hold',

    # Daily soaps (DE)
    'rote rosen',
    'in aller freundschaft',
    'unter uns',
    'alles was zaehlt',
    'gute zeiten schlechte zeiten',
    'gzsz',
    'sturm der liebe',
    'dahoam is dahoam',
    'watzmann ermittelt',

    # Common spellings
    'alles was zahlt',
    'lindenstrasse',
}

# For these titles we strongly prefer TV results over movies (reduces false matches)
FORCE_TV_TMDB_TITLES = set(LOW_SCORE_TMDB_TITLES)


# v2.4 EXTRA MAPPINGS (DE -> EN / alternative official titles)
# ============================================================================
try:
    TITLE_MAPPINGS.update({
        'detektiv rockford': 'The Rockford Files',
        'detektiv rockford anruf genugegt': 'The Rockford Files',
        'rockford': 'The Rockford Files',
        'tierarzt dr jeff': 'Dr. Jeff: Rocky Mountain Vet',
        'tierarzt dr. jeff': 'Dr. Jeff: Rocky Mountain Vet',
        'dr jeff': 'Dr. Jeff: Rocky Mountain Vet',
        'loewenzahn classics': 'Loewenzahn',
    
        'die schatzsucher - goldrausch in alaska': 'Gold Rush',
        'die schatzsucher goldrausch in alaska': 'Gold Rush',
        'goldrausch in alaska': 'Gold Rush',
        'barbara salesch - das strafgericht': 'Barbara Salesch',
        'ulrich wetzel - das strafgericht': 'Ulrich Wetzel',
        'mayday - alarm im cockpit': 'Air Crash Investigation',
        'mayday alarm im cockpit': 'Air Crash Investigation',
        'alarm im cockpit': 'Air Crash Investigation',
        'max carshop': 'Max’ Carshop – Schrauben frei Schnauze',})
except Exception:
    pass

BLACKLISTED_RESULTS = {
    'ran', 'report', 'reportage', 'dokumentation', 'doku',
    'nachrichten', 'news', 'heute journal', 'tagesthemen',
    'phoenix', 'arte', 'zdf', 'ard', '3sat',
    'fussball', 'fußball', 'football', 'soccer',
    'snooker man', 'dar', 'darts',
    'plan b', 'mutter auf streife',
    
    # === v2.3: Spezifische Blacklist ===
    'das duell',  # Zu generisch, matched falschen Film
    'strafgericht',  # Zu generisch
}

def is_blacklisted(result_title, search_title):
    result_lower = result_title.lower().strip()
    search_lower = search_title.lower().strip()
    if result_lower in BLACKLISTED_RESULTS:
        return True
    if len(result_lower) < 4 and result_lower != search_lower:
        return True
    if 'csi' in search_lower and 'csi' in result_lower:
        # Nur blockieren wenn Result ein ANDERES CSI ist (nicht nur "CSI")
        if 'miami' in search_lower and ('ny' in result_lower or 'vegas' in result_lower or 'cyber' in result_lower):
            return True
        if 'ny' in search_lower and ('miami' in result_lower or 'vegas' in result_lower or 'cyber' in result_lower):
            return True
        if 'vegas' in search_lower and ('miami' in result_lower or 'ny' in result_lower or 'cyber' in result_lower):
            return True
    if 'auf streife' in search_lower and 'mutter' in result_lower:
        return True
    return False

def get_dynamic_min_score(title):
    import re
    clean = title or ''
    clean = re.sub(r'\s*-\s*Folge\s+\d+', '', clean, flags=re.I)
    clean = re.sub(r'\s*\(\d+\)', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    clean = re.sub(r'^(der|die|das|the)\s+', '', clean, flags=re.I)

    word_count = len(clean.split())
    if word_count <= 1:
        return 85 if len(clean) >= 6 else 95
    elif word_count == 2:
        return 78
    elif word_count == 3:
        return 70
    else:
        return 60


def check_aspect_ratio(image_path):
    """Prüft ob Bild Landscape (Backdrop) oder Portrait (Poster) ist"""
    try:
        from PIL import Image
        img = Image.open(image_path)
        width, height = img.size
        img.close()
        aspect_ratio = float(width) / float(height)
        
        # Backdrop sollte ~16:9 (1.77) oder breiter sein
        # Poster ist ~2:3 (0.67)
        if aspect_ratio > 1.3:  # Landscape
            return True
        else:  # Portrait oder Quadrat
            return False
    except:
        return True  # Bei Fehler akzeptieren

def verify_media_type(result, search_title):
    media_type = result.get('media_type', '')
    if any(kw in search_title.lower() for kw in ['folge', 'staffel', 'episode']):
        if media_type != 'tv': return False
    if any(kw in search_title.lower() for kw in ['live', 'vorberichte']):
        if media_type == 'movie': return False
    return True

def create_http_session():
    """Erstellt HTTP Session mit Retry-Mechanismus."""
    session = requests.Session()
    retry_strategy = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# ============================================================================
# MAIN DOWNLOAD THREAD CLASS
# ============================================================================

def clean_search_title(title):
    """
    AGGRESSIVE Titel-Bereinigung für bessere Treffer und weniger Duplikate
    
    Entfernt:
    - Episodennummern: "Rote Rosen 1571" → "Rote Rosen"
    - Staffel/Episode: "(S06/E02)" → ""
    - Untertitel bei Anthologien: "Rosamunde Pilcher: ..." → "Rosamunde Pilcher"
    - Specials: "- Best of", "- Special" → ""
    - Sonderzeichen: "&" → "and", multiple spaces → single space
    """
    if not title:
        return title
    
    import re
    original = title
    
    # 1. Entferne klassische Episoden-Formate
    patterns = [
        r'\s*\(S\d+/E\d+\)',      # (S06/E02)
        r'\s*\(\d+/\d+\)',         # (1/10)
        r'\s*\(\d+\)',               # (5)
        r'\s*-\s*Episode\s+\d+',    # - Episode 7942
        r'\s*S\d+E\d+',               # S01E05
        r'\s*Folge\s+\d+',            # Folge 12
    ]
    
    for pattern in patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    
    # 2. WICHTIG: Episodennummern am Ende
    # "Rote Rosen 1571" → "Rote Rosen"
    # "GZSZ 8234" → "GZSZ"
    title = re.sub(r'\s+\d{3,}$', '', title)  # 3+ Ziffern am Ende
    
    # 3. Anthologie-Serien: Alles nach ":" entfernen
    # "Rosamunde Pilcher: Titel" → "Rosamunde Pilcher"
    anthology_series = [
        'rosamunde pilcher',
        'inga lindström', 
        'inga lindstrom',
        'katie fforde',
        'herzkino',
    ]
    
    title_lower = title.lower()
    for series in anthology_series:
        if title_lower.startswith(series):
            if ':' in title:
                title = title.split(':')[0].strip()
                break
    
    # 4. Specials/Best of entfernen
    if ' - ' in title:
        parts = title.split(' - ')
        # Entferne "Best of", "Special", etc. (aber nur wenn es am Ende ist!)
        if len(parts) > 1:
            last_part_lower = parts[-1].lower()
            if any(x in last_part_lower for x in ['best of', 'special', 'highlights', 'extra']):
                title = ' - '.join(parts[:-1])
    
    # 5. Sonderzeichen normalisieren
    title = re.sub(r'\s+', ' ', title)  # Multiple spaces → single space
    title = re.sub(r'[&]', 'and', title)  # & → and
    title = re.sub(r'[:]', '', title)  # : entfernen (außer bei Uhrzeiten)
    
    # 6. Cleanup
    title = re.sub(r'^[-:\s]+|[-:\s]+$', '', title)
    title = title.strip()
    
    return title if title else original


# ==========================
# Canonical slug + overrides
# ==========================

DEFAULT_PROVIDER_ORDER = ["tmdb", "tvdb", "fanart", "imdb", "google", "omdb"]

# Provider overrides by canonical slug (underscore-based)
PROVIDER_OVERRIDES = {
    # RTL Punkt-* : IMDb liefert oft nur Portrait/klein -> Backdrop-Validator reject.
    # Deshalb: IMDb versuchen, aber immer Google-Fallback erlauben.
    "punkt_6": ["imdb", "google"],
    "punkt_7": ["imdb", "google"],
    "punkt_8": ["imdb", "google"],
    # Punkt 12 works on TMDb (fallback IMDb if needed)
    "punkt_12": ["tmdb", "imdb", "tvdb", "fanart", "google", "omdb"],
}

# Direct IMDb IDs (skip IMDb search, use the title page og:image)
IMDB_ID_OVERRIDES = {
    "punkt_6": "tt0334862",
    "punkt_7": "tt0334863",
    "punkt_8": "tt19114452",
}

# EPG filler / non-content titles: skip completely (avoid useless traffic)
SKIP_TITLES = {
    "sendepause", "programmende", "sendeschluss", "sendeschluß", "kein programm",
    "no information", "no title", "no event", "testbild", "pause", "off air",
}

_EP_PATTERNS = [
    # (S28/E11), S28/E11, S28 E11, S28.E11 etc.
    r"\(\s*S\d{1,2}\s*[/\. ]\s*E\d{1,3}\s*\)",
    r"\bS\d{1,2}\s*[/\. ]\s*E\d{1,3}\b",
    # Folge 4268, Episode 1234
    r"\bFolge\s+\d+\b",
    r"\bEpisode\s+\d+\b",
    # Trailing (4268) / - 4268
    r"\(\s*\d{3,5}\s*\)",
    r"\s+-\s*\d{3,5}\b",
]

def _strip_episode_tokens(title):
    try:
        t = title or ""
        for p in _EP_PATTERNS:
            t = re.sub(p, "", t, flags=re.IGNORECASE)
        # collapse whitespace
        t = re.sub(r"\s{2,}", " ", t).strip()
        return t
    except Exception:
        return title

def get_canonical_slug(title):
    t = _strip_episode_tokens(title)
    t = (t or "").strip().lower()
    # normalize umlauts
    t = t.replace("ä","ae").replace("ö","oe").replace("ü","ue").replace("ß","ss")
    # keep letters/numbers, turn other into underscores
    t = re.sub(r"[^a-z0-9]+", "_", t)
    t = re.sub(r"_+", "_", t).strip("_")
    return t or "unknown"

def get_store_slug(title):
    # group "ultimate rush ..." => one slug
    t = _strip_episode_tokens(title)
    if t and t.strip().lower().startswith("ultimate rush"):
        return "ultimate_rush"
    return get_canonical_slug(t)

def get_provider_override(title):
    slug = get_store_slug(title)
    return PROVIDER_OVERRIDES.get(slug, DEFAULT_PROVIDER_ORDER)

def get_imdb_id_override(title):
    slug = get_store_slug(title)
    return IMDB_ID_OVERRIDES.get(slug)




def sanitize_filename_safe(filename):
    """v2.8: Sichere Dateinamen-Sanitisierung"""
    if not filename:
        return ''
    try:
        if isinstance(filename, bytes):
            filename = filename.decode('utf-8', 'ignore')
    except Exception:
        pass
    
    safe = str(filename)
    safe = safe.replace('/', '-')
    safe = safe.replace('\\', '-')
    safe = safe.replace(':', '-')
    safe = safe.replace('*', '')
    safe = safe.replace('?', '')
    safe = safe.replace('"', '')
    safe = safe.replace('<', '')
    safe = safe.replace('>', '')
    safe = safe.replace('|', '')
    
    safe = re.sub(r'\s+', ' ', safe)
    safe = re.sub(r'-+', '-', safe)
    safe = safe.strip().strip('-').strip('.')
    
    return safe


def generate_search_variants(title):
    """v2.8: Multi-Variant Search"""
    if not title:
        return []
    
    variants = []
    seen = set()
    
    def add_variant(v):
        v = v.strip()
        if v and v not in seen and len(v) >= 2:
            seen.add(v)
            variants.append(v)
    
    add_variant(title)
    
    for article in ['Die ', 'Der ', 'Das ', 'Ein ', 'Eine ']:
        if title.startswith(article):
            add_variant(title[len(article):])
    
    clean = re.sub(r'[()\[\]{}<>]', ' ', title)
    clean = re.sub(r'\s+', ' ', clean).strip()
    add_variant(clean)
    
    for article in ['Die ', 'Der ', 'Das ', 'The ']:
        if clean.startswith(article):
            add_variant(clean[len(article):])
    
    clean2 = re.sub(r'[^a-zA-Z0-9äöüÄÖÜß\s-]', '', title)
    clean2 = re.sub(r'\s+', ' ', clean2).strip()
    add_variant(clean2)
    
    for sep in [' (', '(', ' [', '[', ' - ']:
        if sep in title:
            part = title.split(sep)[0].strip()
            if len(part) >= 3:
                add_variant(part)
                for article in ['Die ', 'Der ', 'Das ', 'The ']:
                    if part.startswith(article):
                        add_variant(part[len(article):])
    
    no_numbers = re.sub(r'\s*\(\s*\d+\s*\)\s*', ' ', title)
    no_numbers = re.sub(r'\s+', ' ', no_numbers).strip()
    if no_numbers != title:
        add_variant(no_numbers)
    
    return variants[:15]



class GradientFHDBackdropXDownloadThread(threading.Thread):


    # ------------------------------------------------------------------------
    # CUSTOM override: /media/hdd/xtra/custom/backdrop/<slug>.jpg
    # If exists, it will be used and copied to destination, skipping all providers.
    # ------------------------------------------------------------------------
    def _custom_base_dir(self):
        for base in (xtra_base,):
            try:
                if os.path.exists(base):
                    return base
            except Exception:
                pass
        return '/tmp'

    def _try_custom_backdrop(self, dwn_backdrop, title, service_name=None, event_ts=None, slug_title=None):
        """
        Custom backdrop override (highest priority).

        Checks:
          /media/hdd/xtra/custom/backdrop/<store_slug>.jpg
        and other slug candidates derived from base title & full title.
        Custom always wins (copied to dwn_backdrop even if cache/provider exists).
        """
        try:
            raw = (title or '').strip()
            if not raw:
                return False, None

            base = raw
            for sep in (' - ', ' – ', ':'):
                if sep in base:
                    base = base.split(sep, 1)[0].strip()
            if not base:
                base = raw

            candidates = []
            def _add(s):
                s = (s or '').strip().strip('_')
                if s and s not in candidates:
                    candidates.append(s)

            try:
                _add(get_store_slug(slug_title or raw))
            except Exception:
                pass
            try:
                _add(get_store_slug(base))
            except Exception:
                pass

            try:
                _add(get_canonical_slug(slug_title or raw))
            except Exception:
                pass
            try:
                _add(get_canonical_slug(base))
            except Exception:
                pass

            try:
                _add(convtext(slug_title or raw))
            except Exception:
                pass
            try:
                _add(convtext(base))
            except Exception:
                pass

            if not candidates:
                return False, None

            custom_root = os.path.join(self._custom_base_dir(), 'custom', 'backdrop')
            for slug in candidates:
                custom_path = os.path.join(custom_root, '%s.jpg' % slug)
                if not os.path.exists(custom_path):
                    continue

                try:
                    os.makedirs(os.path.dirname(dwn_backdrop), exist_ok=True)
                except Exception:
                    pass

                try:
                    shutil.copy2(custom_path, dwn_backdrop)
                    try:
                        self.resizeBackdrop(dwn_backdrop)
                    except Exception:
                        pass
                except Exception:
                    return False, None

                try:
                    self.save_backdrop_info_json(slug, {
                        'title': raw,
                        'base_title': base,
                        'source': 'custom',
                        'custom_file': custom_path,
                        'backdrop_file': dwn_backdrop,
                        'slug_candidates': candidates,
                        'service': service_name,
                        'event_ts': event_ts,
                        'fetched_at': int(time.time())
                    })
                except Exception:
                    pass

                return True, '[SUCCESS : custom] %s' % custom_path

            return False, None
        except Exception:
            return False, None

            # Validate backdrop if validator exists
            try:
                if hasattr(self, 'verifyBackdrop') and callable(getattr(self, 'verifyBackdrop')):
                    if not self.verifyBackdrop(custom_path):
                        return False, '[SKIP : custom] Not a valid backdrop'
            except Exception:
                pass

            try:
                os.makedirs(os.path.dirname(dwn_backdrop), exist_ok=True)
            except Exception:
                pass
            shutil.copy2(custom_path, dwn_backdrop)

            # Write backdrop_info JSON
            try:
                self.save_backdrop_info_json(slug, {
                    'ts': int(time.time()),
                    'service': service_name,
                    'event_ts': event_ts,
                    'title': raw,
                    'slug': slug,
                    'backdrop_file': dwn_backdrop,
                    'providers_tried': [{
                        'provider': 'custom',
                        'status': 'success',
                        'url': None,
                        'log': '[SUCCESS : custom] %s' % custom_path
                    }]
                })
            except Exception:
                pass

            return True, '[SUCCESS : custom] %s' % custom_path
        except Exception:
            return False, None
    def __init__(self):
        threading.Thread.__init__(self)
        _refresh_storage_paths(ensure=False)
        
        # HTTP Session mit Retry
        self.http = create_http_session()
        
        # Initialized later by prepare_storage() in the worker thread. Its
        # constructor creates the Info folder and may otherwise wake a NAS.
        self._event_info = None
        
        # Erweiterte Listen fuer Medientyp-Erkennung
        self.checkMovie = [
            "film", "movie", "spielfilm", "kino", "cinema",
            "film", "kino", "tainia", "pelicula", "cinema", "filma"
        ]

        # ERWEITERTE TV-LISTE fuer Magazine, Dokus, Sport etc.
        self.checkTV = [
            # Standard
            "serial", "series", "serie", "serien", "serie", "series",
            "folge", "episodio", "episode", "episode", "staffel",
            "season", "ep.", "animation",
            # Nachrichten & Magazine
            "nachrichten", "news", "aktuell", "journal", "magazin",
            "magazine", "reportage", "bericht", "meldung",
            "mittagsmagazin", "morgenmagazin", "abendmagazin",
            # Talk & Entertainment
            "talk", "show", "entertainment", "unterhaltung",
            "comedy", "satire", "kabarett", "late night",
            # Reality & Dating
            "reality", "dating", "bachelor", "casting",
            # Dokumentation
            "doku", "dokumentation", "documentary", "dokutainment",
            "reportage", "wissen", "bildung", "natur", "tier",
            "geschichte", "history", "science",
            # Sport (erweitert!)
            "sport", "fussball", "football", "soccer", "bundesliga",
            "champions", "europa league", "tennis", "formel",
            "formula", "motorsport", "rennen", "race", "olympia",
            "leichtathletik", "schwimmen", "turnen", "handball",
            "basketball", "volleyball", "hockey", "golf", "ski",
            "biathlon", "boxen", "wrestling", "ufc", "mma",
            "sportschau", "sportstudio",
            # Quiz & Game
            "quiz", "game", "gameshow", "rate", "gewinn", "jackpot",
            # Seifenoper
            "soap", "telenovela", "daily",
            # Kinder
            "kinder", "kids", "animation", "zeichentrick", "anime",
            # Sonstiges
            "sitcom", "program", "sendung", "factual", "infomercial",
            "information", "service", "ratgeber", "verbraucher",
            # Internationale Keywords
            "t/s", "m/s", "sezon", "s-n", "epizod", "serial", "serija",
            "actualite", "discussion", "interview", "debat",
            "emission", "divertissement", "jeu", "meteo",
            "culture", "infos", "feuilleton", "telerealite",
            "societe", "clips", "concert", "sante", "variete"
        ]

    def prepare_storage(self):
        """Create cache folders from the worker thread before file/network I/O."""
        _refresh_storage_paths(ensure=True)
        if self._event_info is None and GradientFHD_event_info is not None:
            try:
                self._event_info = GradientFHD_event_info(
                    info_folder=info_folder,
                    tmdb_api=tmdb_api,
                    lang=lng
                )
            except Exception:
                self._event_info = None

    # ========================================================================
    # TITLE MAPPING FUNCTION - Hauptfunktion fuer bessere Treffer
    # ========================================================================

    # --- xtra info helpers ---
    def _xtra_base_dir(self):
        # Prefer base derived from info_folder (/.../xtra/Info)
        try:
            if isinstance(info_folder, str) and info_folder:
                return os.path.dirname(info_folder.rstrip('/'))
        except Exception:
            pass
        # Fallback derived from path_folder (/.../xtra/backdrop/)
        try:
            if isinstance(path_folder, str) and path_folder:
                p = path_folder.rstrip('/')
                if os.path.basename(p) in ('backdrop', 'backdrops'):
                    return os.path.dirname(p)
                return os.path.dirname(p)
        except Exception:
            pass
        return xtra_base

    def _ensure_dir(self, p):
        try:
            os.makedirs(p, exist_ok=True)
        except Exception:
            try:
                if not os.path.isdir(p):
                    os.makedirs(p)
            except Exception:
                pass

    def _single_info_mode(self):
        try:
            base = self._xtra_base_dir()
            return os.path.exists(os.path.join(base, '.single_info_json')) or os.path.exists(os.path.join(base, 'custom', '.single_info_json'))
        except Exception:
            return False

    def _merge_info_json_fields(self, slug, fields, overwrite=False):
        try:
            if not slug or not isinstance(fields, dict):
                return False
            jf = os.path.join(info_folder, slug + ".json")
            existing = {}
            if os.path.exists(jf):
                try:
                    with open(jf, "r") as f:
                        existing = json.load(f) or {}
                except Exception:
                    existing = {}
            for k, v in fields.items():
                if v is None:
                    continue
                if overwrite or (k not in existing) or existing.get(k) in (None, ""):
                    existing[k] = v
            tmp = jf + ".tmp"
            with open(tmp, "w") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            os.replace(tmp, jf)
            return True
        except Exception:
            return False

    
    def _sanitize_slug(self, slug):
        """Normalize slug so it never contains extensions or path parts."""
        try:
            if not slug:
                return ""
            # strip any path
            slug = os.path.basename(str(slug))
            # remove common image extensions (also if already duplicated)
            for ext in ('.jpg', '.jpeg', '.png', '.webp'):
                if slug.lower().endswith(ext):
                    slug = slug[:-len(ext)]
                    break
            # remove trailing dots/spaces
            slug = slug.strip().strip('.')
            return slug
        except Exception:
            return slug or ""

    def save_backdrop_info_json(self, slug, payload):
        """Write /xtra/backdrop_info/<slug>.json"""
        try:
            if not slug:
                return
            slug = self._sanitize_slug(slug)
            if not slug:
                return
            data = {}
            if isinstance(payload, dict):
                data.update(payload)
            try:
                data.setdefault('ts', int(time.time()))
            except Exception:
                pass
            if self._single_info_mode():
                try:
                    info_fields = {}
                    if data.get('url'):
                        info_fields['backdrop_url'] = data.get('url')
                    if data.get('source'):
                        info_fields['backdrop_source'] = data.get('source')
                    if data.get('tmdb_id') is not None:
                        info_fields['tmdb_id'] = data.get('tmdb_id')
                    if data.get('url') and data.get('source') == 'tvdb':
                        info_fields['tvdb_backdrop_url'] = data.get('url')
                    self._merge_info_json_fields(slug, info_fields, overwrite=False)

                    # keep full trace inside Info.json
                    jf = os.path.join(info_folder, slug + ".json")
                    existing = {}
                    if os.path.exists(jf):
                        try:
                            with open(jf, "r") as f:
                                existing = json.load(f) or {}
                        except Exception:
                            existing = {}
                    if not isinstance(existing, dict):
                        existing = {}
                    existing['backdrop_info'] = data
                    tmp = jf + ".tmp"
                    with open(tmp, "w") as f:
                        json.dump(existing, f, ensure_ascii=False, indent=2)
                    os.replace(tmp, jf)
                except Exception:
                    pass
                return
            base = self._xtra_base_dir()
            outdir = os.path.join(base, 'backdrop_info')
            self._ensure_dir(outdir)
            outpath = os.path.join(outdir, '%s.json' % slug)
            try:
                with open(outpath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception:
                with open(outpath, 'w') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _find_info_json_path(self, slug):
        """Return best-matching /xtra/Info/<slug>.json path.
        - exact match first
        - then case-insensitive / sanitized filename match (helps existing duplicates)
        """
        try:
            if not slug:
                return None
            slug = self._sanitize_slug(slug)
            if not slug:
                return None
            p = os.path.join(info_folder, slug + ".json")
            if os.path.exists(p):
                return p
            # fallback: find any json whose sanitized basename matches (case-insensitive)
            try:
                want = slug.lower()
                for fn in os.listdir(info_folder):
                    if not fn.lower().endswith(".json"):
                        continue
                    base = os.path.splitext(fn)[0]
                    if self._sanitize_slug(base).lower() == want:
                        return os.path.join(info_folder, fn)
            except Exception:
                pass
        except Exception:
            pass
        return None

    def _try_backdrop_from_info_json(self, dwn_backdrop, title, slug):
        """If Info JSON already contains a TMDb backdrop_path, download directly and log as TMDb (not Google)."""
        try:
            if not dwn_backdrop or os.path.exists(dwn_backdrop):
                return False, None
            p = self._find_info_json_path(slug)
            if not p:
                return False, None
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    j = json.load(f)
            except Exception:
                return False, None
            if not isinstance(j, dict):
                return False, None
            bp = j.get("backdrop_path")
            tmdb_id = j.get("tmdb_id") or j.get("id")
            # treat presence of backdrop_path as TMDb even if j['source']=='google'
            if isinstance(bp, str) and bp.startswith("/") and len(bp) > 2:
                url = "https://image.tmdb.org/t/p/original" + bp
                self.saveBackdrop(url, dwn_backdrop)
                if os.path.exists(dwn_backdrop) and self.verifyBackdrop(dwn_backdrop):
                    # write backdrop_info so you can see the true provider
                    try:
                        payload = {
                            "title": title,
                            "source": "tmdb_info",
                            "tmdb_id": int(tmdb_id) if tmdb_id is not None else None,
                            "url": url,
                            "ts": int(time.time())
                        }
                        # write /xtra/backdrop_info/<slug>.json (debug/trace)
                        self.save_backdrop_info_json(slug, payload)
                    except Exception:
                        pass
                    return True, "[SUCCESS : tmdb] %s (via Info.json)" % title
                return False, "[SKIP : tmdb] Info.json had backdrop_path but download failed"

            # Single-info mode: accept direct backdrop_url
            try:
                direct_url = j.get("backdrop_url") or j.get("tvdb_backdrop_url")
                if direct_url:
                    self.saveBackdrop(direct_url, dwn_backdrop)
                    if os.path.exists(dwn_backdrop) and self.verifyBackdrop(dwn_backdrop):
                        try:
                            payload = {
                                "title": title,
                                "source": j.get("backdrop_source") or "info_url",
                                "tmdb_id": int(tmdb_id) if tmdb_id is not None else None,
                                "url": direct_url,
                                "ts": int(time.time())
                            }
                            self.save_backdrop_info_json(slug, payload)
                        except Exception:
                            pass
                        return True, "[SUCCESS : info] %s (via Info.json)" % title
            except Exception:
                pass
        except Exception:
            pass
        return False, None

    def _read_tvdb_id_from_poster_info(self, slug):
        try:
            if not slug:
                return None
            base = self._xtra_base_dir()
            p = os.path.join(base, 'poster_info', '%s.json' % slug)
            if not os.path.exists(p):
                return None
            with open(p, 'r', encoding='utf-8') as f:
                j = json.load(f)
            tid = j.get('tvdb_id') or j.get('tvdbId') or j.get('id')
            if tid is None:
                return None
            return int(str(tid).strip())
        except Exception:
            return None

    def _tvdb_candidates(self, title):
        """v2.8: Multi-Variant Search"""
        return generate_search_variants(title or '')

    def _tvdb_pick_background_from_series_page(self, series_id):
        """Scrape TheTVDB series page (by numeric id redirect) and return a background url if present."""
        try:
            sid = int(series_id)
        except Exception:
            return None
        try:
            url = 'https://thetvdb.com/series/%s' % sid
            headers = {'User-Agent': getRandomUserAgent()}
            r = self.http.get(url, headers=headers, timeout=(6, 12), allow_redirects=True)
            if r.status_code != 200:
                return None
            html = r.text or ''
            m = re.search(r'(https?://artworks\.thetvdb\.com/[^"\s>]+/backgrounds/[^"\s<]+\.jpg)', html, re.I)
            if m:
                return m.group(1)
            m = re.search(r'(https?://artworks\.thetvdb\.com/[^"\s>]+/fanart/[^"\s<]+\.jpg)', html, re.I)
            if m:
                return m.group(1)
            m = re.search(r'(https?://artworks\.thetvdb\.com/[^"\s>]+\.jpg)', html, re.I)
            if m:
                return m.group(1)
        except Exception:
            return None
        return None
    def apply_title_mapping(self, title):
        """Wendet Title Mappings an um bessere Treffer zu erzielen.

        v2.4 Bugfix:
        - Keine Substring-Mappings innerhalb eines Wortes mehr.
          Beispiel vorher: "Alpenpanorama" -> Mapping-Key "panorama" -> "Panorama" (falsch)
        - Stattdessen: Key muss als ganzes Wort (oder Wortsequenz) vorkommen.
        """
        if not title:
            return title

        def _umlauts(s):
            try:
                return (s
                        .replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
                        .replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
                        .replace('ß', 'ss'))
            except Exception:
                return s

        def _norm(s):
            try:
                s = _umlauts(s)
            except Exception:
                pass
            try:
                s = self.UNAC(s)
            except Exception:
                pass
            try:
                s = s.lower().strip()
            except Exception:
                return ''
            s = re.sub(r'[^\w\s]', ' ', s)
            s = re.sub(r'\s+', ' ', s).strip()
            return s

        def _contains_wordseq(haystack, needle):
            if not haystack or not needle:
                return False
            if haystack == needle:
                return True
            padded = ' %s ' % haystack
            needle_p = ' %s ' % needle
            return needle_p in padded

        if not hasattr(self, '_title_map_norm'):
            try:
                self._title_map_norm = {}
                for k, v in TITLE_MAPPINGS.items():
                    nk = _norm(k)
                    if nk:
                        self._title_map_norm[nk] = v
            except Exception:
                self._title_map_norm = {}
        if not hasattr(self, '_sport_map_norm'):
            try:
                self._sport_map_norm = {}
                for k, v in SPORT_KEYWORDS.items():
                    nk = _norm(k)
                    if nk:
                        self._sport_map_norm[nk] = v
            except Exception:
                self._sport_map_norm = {}

        original = title
        n = _norm(title)
        if not n:
            return original

    def simplify_title_for_search(self, title):
        """Vereinfacht EPG-Titel für Suchzwecke (ohne harte Mappings)."""
        if not title:
            return title
        t = title.strip()
        # keep full title for known patterns where the right side is the real show name
        if re.search(r'goldrausch\s+in\s+alaska', t, flags=re.I):
            return t.strip()
        t = re.sub(r'\bclassics\b', '', t, flags=re.I).strip()
        t = re.sub(r'\bhighlight(s)?\b', '', t, flags=re.I).strip()
        t = re.sub(r'\s*\(\d{1,4}\)\s*$', '', t)
        t = re.sub(r'\s*-\s*Folge\s+\d+.*$', '', t, flags=re.I)
        # trailing standalone episode numbers (common in EPG): 'Rote Rosen 1551'
        t = re.sub(r'\s+\d{3,4}$', '', t)
        if ' - ' in t:
            left, right = t.split(' - ', 1)
            left = left.strip()
            right = right.strip()
            left_words = len(left.split())
            # Mayday / Alarm im Cockpit: right side is essential, keep full
            if re.search(r'alarm\s+im\s+cockpit', t, flags=re.I):
                return t.strip()
            # if left is only one word, it is often ambiguous (e.g. Mayday) -> keep full
            if left_words <= 1 and len(right) >= 4:
                return t.strip()
            if len(left) >= 4:
                t = left
        return t.strip()

    def normalize_for_match(self, title):
        """Normalisierung für PMATCH (Artikel entfernen)."""
        if not title:
            return ''
        try:
            t = (title
                 .replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
                 .replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
                 .replace('ß', 'ss'))
        except Exception:
            t = title
        try:
            t = self.UNAC(t)
        except Exception:
            pass
        t = (t or '').lower().strip()
        t = re.sub(r'[^\w\s]', ' ', t)
        t = re.sub(r'\s+', ' ', t).strip()
        t = re.sub(r'^(der|die|das|den|dem|des|ein|eine|einer|eines|the|a|an|le|la|les|el|il|lo|un|une)\s+', '', t)
        return t


        mapped = self._title_map_norm.get(n)
        if mapped:
            return mapped

        for key, val in self._title_map_norm.items():
            if _contains_wordseq(n, key):
                return val

        for key, val in self._sport_map_norm.items():
            if _contains_wordseq(n, key):
                return val

        return original


        # 1) direct mapping
        mapped = self._title_map_norm.get(n)
        if mapped:
            return _simplify(mapped)

        # 2) partial mapping (substring)
        for key, val in self._title_map_norm.items():
            if not key:
                continue
            if n.startswith(key) or key in n:
                return _simplify(val)

        # 3) sport keywords
        for key, val in self._sport_map_norm.items():
            if not key:
                continue
            if key in n:
                return _simplify(val)

        # fallback: simplified original
        return _simplify(original)

        
        title_lower = title.lower().strip()
        
        # 1. Direktes Mapping pruefen
        if title_lower in TITLE_MAPPINGS:
            mapped = TITLE_MAPPINGS[title_lower]
            if DEBUG_BACKDROP:
                print("[TITLE MAPPING] '%s' -> '%s'" % (title, mapped))
            return mapped
        
        # 2. Teilweise Uebereinstimmung pruefen (fuer Titel mit Zusaetzen)
        for key, mapped in TITLE_MAPPINGS.items():
            if title_lower.startswith(key) or key in title_lower:
                if DEBUG_BACKDROP:
                    print("[PARTIAL MAPPING] '%s' -> '%s'" % (title, mapped))
                return mapped
        
        # 3. Sport-Keywords pruefen
        for sport_key, sport_mapped in SPORT_KEYWORDS.items():
            if sport_key in title_lower:
                if DEBUG_BACKDROP:
                    print("[SPORT MAPPING] '%s' -> '%s'" % (title, sport_mapped))
                return sport_mapped
        
        return title

    # ========================================================================
    # JSON SPEICHERUNG fuer Rating & Parental
    # ========================================================================
    def save_info_json(self, slug, data):
        """
        Speichert TMDb-Daten als JSON fuer GradientFHDStarX und GradientFHDParental.
        """
        if not slug or not data:
            return False
        slug = self._sanitize_slug(slug)
        if not slug:
            return False
        
        try:
            json_path = os.path.join(info_folder, slug + ".json")
            
            # Existierende Daten laden und mergen
            existing = {}
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r") as f:
                        existing = json.load(f)
                except:
                    existing = {}
            
            # Neue Daten mergen
            existing.update(data)
            
            # Atomic write
            tmp_path = json_path + ".tmp"
            with open(tmp_path, "w") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, json_path)
            
            if DEBUG_BACKDROP:
                print("[JSON] Saved: %s" % json_path)
            return True
        except Exception as e:
            if DEBUG_BACKDROP:
                print("[JSON ERROR] %s" % str(e))
            return False

    def extract_info_from_tmdb_result(self, result, media_type="movie"):
        """
        Extrahiert relevante Infos aus TMDb-Ergebnis fuer JSON.
        """
        info = {}
        
        try:
            # Basis-Infos
            info['tmdb_id'] = result.get('id')
            info['tmdb_vote_average'] = result.get('vote_average', 0)
            info['tmdb_vote_count'] = result.get('vote_count', 0)
            info['title'] = result.get('title') or result.get('name', '')
            info['original_title'] = result.get('original_title') or result.get('original_name', '')
            info['overview'] = result.get('overview', '')
            info['poster_path'] = result.get('poster_path', '')
            info['backdrop_path'] = result.get('backdrop_path', '')
            info['original_language'] = result.get('original_language', '')
            info['adult'] = result.get('adult', False)
            info['media_type'] = media_type
            
            # Jahr extrahieren
            if media_type == 'movie':
                release = result.get('release_date', '')
                if release:
                    info['release_date'] = release
                    info['year'] = release[:4]
            else:
                first_air = result.get('first_air_date', '')
                if first_air:
                    info['first_air_date'] = first_air
                    info['year'] = first_air[:4]
            
            # Genres (wenn verfuegbar)
            if result.get('genre_ids'):
                info['genre_ids'] = result.get('genre_ids')
            
            # Altersfreigabe schaetzen basierend auf adult-Flag
            if result.get('adult', False):
                info['Rated'] = '18'
            else:
                info['Rated'] = 'NA'
                
        except Exception as e:
            if DEBUG_BACKDROP:
                print("[EXTRACT INFO ERROR] %s" % str(e))
        
        return info

    def fetch_certification(self, tmdb_id, media_type):
        """
        Holt Altersfreigabe (Certification) von TMDb.
        """
        try:
            if media_type == 'movie':
                url = "https://api.themoviedb.org/3/movie/%s/release_dates?api_key=%s" % (tmdb_id, tmdb_api)
            else:
                url = "https://api.themoviedb.org/3/tv/%s/content_ratings?api_key=%s" % (tmdb_id, tmdb_api)
            
            response = self.http.get(url, timeout=(3, 6))
            if response.status_code == 200:
                data = response.json()
                
                if media_type == 'movie':
                    for country in data.get('results', []):
                        if country.get('iso_3166_1') in ['DE', 'US', 'GB']:
                            for release in country.get('release_dates', []):
                                cert = release.get('certification', '')
                                if cert:
                                    return cert
                else:
                    for rating in data.get('results', []):
                        if rating.get('iso_3166_1') in ['DE', 'US', 'GB']:
                            return rating.get('rating', '')
        except:
            pass
        return None


    def fetch_tmdb_backdrop(self, tmdb_id, media_type):
        """Fetch a real backdrop via TMDb /images endpoint.

        Some TMDb entries have backdrop_path=None in search results, but still have backdrops in /images.
        This reduces Google fallback significantly.
        Returns: full backdrop_url or None
        """
        try:
            if not tmdb_id:
                return None
            if media_type == 'movie':
                url = "https://api.themoviedb.org/3/movie/%s/images?api_key=%s" % (tmdb_id, tmdb_api)
            else:
                url = "https://api.themoviedb.org/3/tv/%s/images?api_key=%s" % (tmdb_id, tmdb_api)

            r = self.http.get(url, timeout=(3, 8))
            if r.status_code != 200:
                return None
            js = r.json() if hasattr(r, 'json') else None
            if not isinstance(js, dict):
                return None
            backs = js.get('backdrops') or []
            if not backs:
                return None

            # pick best candidate: prefer width>=1280 and highest vote_average/vote_count
            def score(b):
                try:
                    w = int(b.get('width') or 0)
                    va = float(b.get('vote_average') or 0)
                    vc = int(b.get('vote_count') or 0)
                except Exception:
                    w, va, vc = 0, 0.0, 0
                # width weight dominates
                return (1 if w >= 1280 else 0, va, vc, w)

            backs_sorted = sorted(backs, key=score, reverse=True)
            for b in backs_sorted[:8]:
                fp = b.get('file_path')
                if fp:
                    return "https://image.tmdb.org/t/p/w1280%s" % fp
        except Exception:
            return None
        return None

    # ========================================================================
    # SEARCH METHODS
    # ========================================================================
    def search_tmdb(self, dwn_backdrop, title, shortdesc, fulldesc, channel=None):
        # CUSTOM override (never expires)
        ok_custom, msg_custom = self._try_custom_backdrop(dwn_backdrop, title, channel, None)
        if ok_custom:
            return True, msg_custom

        """TMDb search (movie+tv) with proper language fallback and tolerant matching.

        Fixes common DE/EN issues:
        - Enigma2 lang codes are like de_DE -> TMDb expects de-DE
        - If localized title not available, fallback to en-US and no-language
        """
        try:
            self.channel = channel
            self.dwn_backdrop = dwn_backdrop

            original_title = (title or '').strip()
            mapped_title = (self.apply_title_mapping(original_title) or '').strip()
            query_base = mapped_title or original_title
            if not query_base:
                return False, "[SKIP : tmdb] Empty title"
            # Fast-path: if /xtra/Info/<slug>.json already has TMDb backdrop_path,
            # download directly and report TMDb success (prevents "SUCCESS : google" in AutoDB when TMDb data exists).
            try:
                slug = get_canonical_slug(query_base) or convtext(original_title)
            except Exception:
                slug = None
            ok_info, log_info = self._try_backdrop_from_info_json(dwn_backdrop, original_title, slug)
            if ok_info:
                return True, log_info


            # Build query variants (try simpler first)
            qv = []
            def _add(q):
                q = (q or '').strip()
                if q and q not in qv:
                    qv.append(q)

            _add(query_base)
            # split common separators
            for sep in (' - ', ':', '–', '—'):
                if sep in query_base:
                    _add(query_base.split(sep, 1)[0])
            # simplified (accents/slug-like)
            try:
                simp = self.simplify_title_for_search(query_base)
                _add(simp)
            except Exception:
                pass

            # Language chain: de-DE -> de -> en-US -> None
            def _tmdb_lang_chain():
                base = ''
                try:
                    base = (lng or '')  # global lng in this module
                except Exception:
                    base = ''
                base = (base or '').replace('_', '-')
                chain = []
                if base:
                    chain.append(base)
                    if '-' in base:
                        chain.append(base.split('-', 1)[0])
                # Always try German first (improves matching for German EPG titles)
                chain.append('de-DE')
                chain.append('de')
                chain.append('en-US')
                chain.append(None)
                out = []
                for x in chain:
                    if x not in out:
                        out.append(x)
                return out

            langs = _tmdb_lang_chain()

            # Matching helpers
            from difflib import SequenceMatcher

            def _norm(s):
                try:
                    return self.normalize_for_match(s or '')
                except Exception:
                    try:
                        return (s or '').lower()
                    except Exception:
                        return ''

            def _score(q, cand_title, cand_orig):
                qn = _norm(q)
                if not qn:
                    return 0
                tn = _norm(cand_title)
                on = _norm(cand_orig)

                # Exact / contains matches first
                if tn and qn == tn:
                    return 100
                if on and qn == on:
                    return 100
                if tn and (qn in tn or tn in qn):
                    return 95
                if on and (qn in on or on in qn):
                    return 92

                # Fuzzy ratio
                r1 = SequenceMatcher(None, qn, tn).ratio() if tn else 0.0
                r2 = SequenceMatcher(None, qn, on).ratio() if on else 0.0
                return int(round(max(r1, r2) * 100))

            # Determine if it looks like a movie from EPG text
            text_hint = (original_title + ' ' + (shortdesc or '') + ' ' + (fulldesc or '')).lower()
            movie_hint = any(k in text_hint for k in (
                'spielfilm', 'film', 'kino', 'thriller', 'komödie', 'komoedie',
                'drama', 'horror', 'action', 'krimi'
            ))

            best = None
            best_score = -1
            best_lang = None

            # Query TMDb
            for q in qv[:3]:
                for _lang in langs:
                    # multi search (tv+movie) is usually enough
                    if _lang:
                        url = "https://api.themoviedb.org/3/search/multi?api_key=%s&language=%s&query=%s" % (
                            tmdb_api, _lang, requests.utils.quote(q)
                        )
                    else:
                        url = "https://api.themoviedb.org/3/search/multi?api_key=%s&query=%s" % (
                            tmdb_api, requests.utils.quote(q)
                        )
                    try:
                        resp = self.http.get(url, timeout=(3, 8))
                        if getattr(resp, 'status_code', None) != 200:
                            continue
                        data = resp.json()
                    except Exception:
                        continue

                    results = (data or {}).get('results') or []
                    if not isinstance(results, list) or not results:
                        # for movies we can also try /search/movie as an extra chance
                        if movie_hint:
                            if _lang:
                                url2 = "https://api.themoviedb.org/3/search/movie?api_key=%s&language=%s&query=%s" % (
                                    tmdb_api, _lang, requests.utils.quote(q)
                                )
                            else:
                                url2 = "https://api.themoviedb.org/3/search/movie?api_key=%s&query=%s" % (
                                    tmdb_api, requests.utils.quote(q)
                                )
                            try:
                                resp2 = self.http.get(url2, timeout=(3, 8))
                                if getattr(resp2, 'status_code', None) != 200:
                                    continue
                                data2 = resp2.json()
                                results = (data2 or {}).get('results') or []
                            except Exception:
                                results = []
                        if not results:
                            continue

                    for each in results[:12]:
                        mt = each.get('media_type') or ('movie' if movie_hint else None)
                        if mt not in ('tv', 'movie'):
                            continue
                        cand_title = each.get('title') or each.get('name') or ''
                        cand_orig = each.get('original_title') or each.get('original_name') or ''
                        sc = _score(q, cand_title, cand_orig)

                        # Make movie matches a bit more tolerant than TV
                        min_ok = 60 if mt == 'movie' else 70
                        if sc < min_ok:
                            continue

                        # Prefer candidates that already have a backdrop_path
                        has_bd = bool(each.get('backdrop_path'))
                        boost = 3 if has_bd else 0
                        sc2 = sc + boost

                        if sc2 > best_score:
                            best = each
                            best_score = sc2
                            best_lang = _lang

                    # if we found a near-perfect match, stop early
                    if best_score >= 98:
                        break
                if best_score >= 98:
                    break

            if not best:
                return False, "[SKIP : tmdb] No sufficiently matching result"

            tmdb_id = best.get('id')
            best_media_type = best.get('media_type') or ('movie' if movie_hint else 'tv')

            backdrop_url = None
            backdrop_path = best.get('backdrop_path')
            if backdrop_path:
                backdrop_url = "https://image.tmdb.org/t/p/original%s" % backdrop_path
            else:
                try:
                    backdrop_url = self.fetch_tmdb_backdrop(tmdb_id, 'movie' if best_media_type == 'movie' else 'tv')
                except Exception:
                    backdrop_url = None

            if not backdrop_url:
                return False, "[SKIP] Provider: TMDb | Grund: search + images"

            # Create /xtra/Info JSON for rating/parental, etc.
            try:
                info = self.extract_info_from_tmdb_result(best, 'movie' if best_media_type == 'movie' else 'tv')
                if tmdb_id:
                    # certification (Rated) enhancement
                    try:
                        rated = self.fetch_certification(tmdb_id, best_media_type)
                        if rated:
                            info['Rated'] = rated
                    except Exception:
                        pass
                self.save_info_json(dwn_backdrop, info)
            except Exception:
                pass
            # Download image + write backdrop_info JSON
            try:
                self.saveBackdrop(backdrop_url, dwn_backdrop)
                if os.path.exists(dwn_backdrop) and self.verifyBackdrop(dwn_backdrop):
                    try:
                        slug2 = get_canonical_slug(query_base) or convtext(original_title)
                        payload = {
                            'title': query_base,
                            'source': 'tmdb',
                            'tmdb_id': tmdb_id,
                            'url': backdrop_url,
                            'lang': best_lang or '',
                            'ts': int(time.time())
                        }
                        if slug2:
                            self.save_backdrop_info_json(slug2, payload)
                    except Exception:
                        pass
                    return True, "[SUCCESS : tmdb] %s (score=%d lang=%s)" % (query_base, best_score, best_lang or 'none')
                try:
                    if os.path.exists(dwn_backdrop):
                        os.remove(dwn_backdrop)
                except Exception:
                    pass
                return False, '[SKIP : tmdb] Download failed'
            except Exception as e:
                return False, '[ERROR : tmdb] %s' % str(e)

        except Exception as e:
            return False, "[ERROR : tmdb] %s" % str(e)
    def downloadData2(self, data):
        """Verarbeitet TMDb-Ergebnisse, waehlt den besten Treffer und speichert JSON.
        - Nur media_type 'movie' oder 'tv'
        - Nur echte Backdrops (kein Poster-Fallback)
        - Bester Kandidat via PMATCH/UNAC mit Mindestscore
        - Speichert JSON unter Slug (mapped_title)
        - Speichert Backdrop genau einmal unter self.dwn_backdrop
        """
        try:
            # data kann schon ein dict sein oder ein JSON-String
            data_json = data if isinstance(data, dict) else json.loads(data)
        except Exception as e:
            if DEBUG_BACKDROP:
                print("[downloadData2] invalid JSON: %s" % e)
            return False, "[ERROR : tmdb] invalid JSON"

        # TMDb can return either a search wrapper {"results": [...]} or (in some call paths)
        # a single already-picked item dict. Be tolerant and accept both.
        results = data_json.get('results') or []
        if not results:
            looks_like_item = any(k in data_json for k in (
                'id', 'backdrop_path', 'poster_path', 'media_type', 'title', 'name', 'original_title', 'original_name'
            ))
            if looks_like_item:
                results = [data_json]
            else:
                return False, "[SKIP : tmdb] No results"

        # Referenztitel fuer Matching
        query_title = getattr(self, 'mapped_title', None) or getattr(self, 'original_title', None) or getattr(self, 'title_safe', None) or ''
        query_title_raw = query_title or ''
        query_title_simpl = self.simplify_title_for_search(query_title_raw)
        query_norm = self.normalize_for_match(query_title_simpl or query_title_raw)

        # normalized query key for allowlists
        qn = query_norm


        best = None
        best_media_type = None
        best_score = -1

        for each in results:
            media_type = each.get('media_type', '')
            if media_type == 'tv':
                media_type = 'tv'
            elif media_type == 'movie':
                media_type = 'movie'
            else:
                # Personen, Collections etc. ignorieren
                continue
            # Backdrop optional: manche Treffer haben backdrop_path=None in search,
            # aber liefern Backdrops über /images.
            backdrop_path = each.get('backdrop_path')

            cand_title = each.get('title') or each.get('name') or ''
            if is_blacklisted(cand_title, query_title):
                continue
            if not verify_media_type(each, query_title):
                continue
            cand_norm = self.normalize_for_match(cand_title or '')

            score = self.PMATCH(query_norm, cand_norm)

            # penalties to avoid false positives
            try:
                q_digits = re.findall(r'\d+', query_norm)
                c_digits = re.findall(r'\d+', cand_norm)
                if (not q_digits) and c_digits:
                    score -= 20
                elif q_digits and (not c_digits):
                    score -= 10
            except Exception:
                pass

            # prefer TV on non-cinema channels
            try:
                ch = (getattr(self, 'channel', '') or '').lower()
                prefer_movie = ('cinema' in ch or 'movie' in ch)
                prefer_tv = not prefer_movie
                if prefer_tv and media_type == 'movie':
                    score -= 12
                if prefer_movie and media_type == 'tv':
                    score -= 12
            except Exception:
                pass

            # force TV for allowlisted titles (court shows / soaps)
            try:
                if qn in FORCE_TV_TMDB_TITLES:
                    if media_type == 'tv':
                        score += 10
                    elif media_type == 'movie':
                        score -= 10
            except Exception:
                pass

            if score < 0:
                score = 0

            if DEBUG_BACKDROP:
                print("[TMDB] candidate '%s' (%s) score=%d" % (cand_title, media_type, score))

            if score > best_score:
                best_score = score
                best = each
                best_media_type = media_type

        # Mindestscore, um grobe Fehlertreffer wie "Mobile Suit Gundam" fuer "Suits"
        # oder "The Ardennes" fuer irgendwelche Magazine zu verhindern
        MIN_SCORE = 40

        try:
            query_title = self.apply_title_mapping(query_title)
        except Exception:
            pass
        required_score = get_dynamic_min_score(query_title)

        # If title is in allowlist, reduce threshold (helps daily shows / reboots)
        try:
            if qn in LOW_SCORE_TMDB_TITLES:
                required_score = max(55, int(required_score) - 18)
        except Exception:
            pass
        if not best or best_score < required_score:
            if DEBUG_BACKDROP:
                print("[TMDB] no sufficiently good candidate (best_score=%d, query='%s')" % (best_score, query_title))
            return False, "[SKIP : tmdb] No sufficiently matching result"

        try:
            backdrop_path = best.get('backdrop_path')
            backdrop_url = None
            if backdrop_path:
                backdrop_url = "https://image.tmdb.org/t/p/w1280%s" % backdrop_path
            else:
                # try /images endpoint fallback
                try:
                    tmdb_id_tmp = best.get('id')
                    backdrop_url = self.fetch_tmdb_backdrop(tmdb_id_tmp, 'movie' if best_media_type == 'movie' else 'tv')
                except Exception:
                    backdrop_url = None

            if not backdrop_url:
                return False, "[SKIP] Provider: TMDb | Grund: search + images"

            # JSON fuer PosterFX/Infos erzeugen
            info = self.extract_info_from_tmdb_result(best, 'movie' if best_media_type == 'movie' else 'tv')

            tmdb_id = best.get('id')
            if tmdb_id:
                try:
                    cert = self.fetch_certification(tmdb_id, 'movie' if best_media_type == 'movie' else 'tv')
                    if cert:
                        info['Rated'] = cert
                except Exception as e:
                    if DEBUG_BACKDROP:
                        print("[TMDB] certification error: %s" % e)

            if getattr(self, 'slug', None):
                self.save_info_json(self.slug, info)

            # Backdrop genau EINMAL speichern
            if getattr(self, 'dwn_backdrop', None):
                self.saveBackdrop(backdrop_url, self.dwn_backdrop)

            show_title = info.get('title') or (best.get('title') or best.get('name') or '')
            if DEBUG_BACKDROP:
                print("[SUCCESS : tmdb] %s score=%d" % (show_title, best_score))
            return True, "[SUCCESS : tmdb] %s (score=%d)" % (show_title, best_score)

        except Exception as e:
            if DEBUG_BACKDROP:
                print("[downloadData2 error] %s" % str(e))
            return False, "[ERROR : tmdb] %s" % str(e)
    def search_tvdb(self, dwn_backdrop, title, shortdesc, fulldesc, channel=None):
        # CUSTOM override (never expires)
        ok_custom, msg_custom = self._try_custom_backdrop(dwn_backdrop, title, channel, None)
        if ok_custom:
            return True, msg_custom

        """TVDb Backdrop: resolve independently (no poster_info dependency)."""
        try:
            mapped_title = self.apply_title_mapping(title)
            base_title = (mapped_title or title or '').replace('+', ' ').strip()
            if not base_title:
                return False, "[SKIP : tvdb] Empty title"            # slug for info filenames (do NOT cache across events!)
            slug = get_canonical_slug(mapped_title) or convtext(title) or convtext(base_title)
            if not slug:
                return False, "[SKIP : tvdb] No slug"
            # 1) Do NOT depend on poster_info (poster/backdrop are independent)
            series_id = None

            tried = []
            cands = self._tvdb_candidates(base_title)
            try:
                self.logAutoDB("[TVDB-Search] Query='%s', Variants=%d" % (base_title, len(cands)))
            except Exception:
                pass

            # 2) Resolve via legacy GetSeries.php (same as PosterDB)
            LEGACY_KEY = FALLBACK_API_MARKER
            if not series_id:
                for q in cands:
                    if not q:
                        continue
                    tried.append(q)
                    try:
                        qenc = quote(q.encode('utf-8'))
                    except Exception:
                        try:
                            qenc = quote(q)
                        except Exception:
                            qenc = q
                    url = 'https://thetvdb.com/api/GetSeries.php?seriesname=%s' % qenc
                    headers = {'User-Agent': getRandomUserAgent()}
                    r = self.http.get(url, headers=headers, timeout=(6, 12))
                    if r.status_code != 200:
                        continue
                    xml = r.text or ''
                    mid = re.search(r'<seriesid>(\d+)</seriesid>', xml, re.I)
                    if mid:
                        try:
                            series_id = int(mid.group(1))
                            break
                        except Exception:
                            series_id = None

            if not series_id:
                if tried:
                    return False, '[SKIP : tvdb] Not found (tried: %s)' % ', '.join(tried)
                return False, '[SKIP : tvdb] Not found'

            # 3) Try legacy series/<id>/<lang> and read <fanart>
            for lang in ('de', 'en', ''):
                try:
                    url = 'https://thetvdb.com/api/%s/series/%s%s' % (LEGACY_KEY, series_id, ('/%s' % lang) if lang else '')
                    headers = {'User-Agent': getRandomUserAgent()}
                    r = self.http.get(url, headers=headers, timeout=(6, 12))
                    if r.status_code != 200:
                        continue
                    xml = r.text or ''
                    mf = re.search(r'<fanart>(.*?)</fanart>', xml, re.I)
                    if mf:
                        path = (mf.group(1) or '').strip()
                        if path:
                            img = path if path.startswith('http') else ('https://artworks.thetvdb.com/banners/%s' % path.lstrip('/'))
                            self.saveBackdrop(img, dwn_backdrop)
                            if os.path.exists(dwn_backdrop) and self.verifyBackdrop(dwn_backdrop):
                                if slug:
                                    self.save_backdrop_info_json(slug, {'title': base_title, 'source': 'tvdb_legacy', 'tvdb_id': int(series_id), 'url': img})
                                return True, '[SUCCESS : tvdb] %s' % img
                except Exception:
                    pass

            # 4) Scrape series page (often exposes v4 /backgrounds/ url publicly)
            try:
                img = self._tvdb_pick_background_from_series_page(series_id)
                if img:
                    self.saveBackdrop(img, dwn_backdrop)
                    if os.path.exists(dwn_backdrop) and self.verifyBackdrop(dwn_backdrop):
                        if slug:
                            self.save_backdrop_info_json(slug, {'title': base_title, 'source': 'tvdb_page', 'tvdb_id': int(series_id), 'url': img})
                        return True, '[SUCCESS : tvdb] %s' % img
            except Exception:
                pass

            return False, '[SKIP : tvdb] No backdrop found (series_id=%s)' % series_id
        except Exception as e:
            return False, '[ERROR : tvdb] %s' % str(e)

    def search_fanart(self, dwn_backdrop, title, shortdesc, fulldesc, channel=None):
        # CUSTOM override (never expires)
        ok_custom, msg_custom = self._try_custom_backdrop(dwn_backdrop, title, channel, None)
        if ok_custom:
            return True, msg_custom

        """FanArt.tv Suche - speziell fuer Backdrops optimiert."""
        try:
            mapped_title = self.apply_title_mapping(title)
            title_safe = (mapped_title or title or '').replace('+', ' ')
            try:
                if not getattr(self, 'slug', None):
                    self.slug = get_canonical_slug(mapped_title or title)
            except Exception:
                pass
            try:
                if not getattr(self, 'slug', None):
                    self.slug = get_canonical_slug(mapped_title or title)
            except Exception:
                pass
            try:
                if not getattr(self, 'slug', None):
                    self.slug = get_canonical_slug(mapped_title or title)
            except Exception:
                pass
            try:
                if not getattr(self, 'slug', None):
                    self.slug = get_canonical_slug(mapped_title or title)
            except Exception:
                pass
            
            # Erst TVMaze fuer TVDB-ID
            url_maze = "http://api.tvmaze.com/singlesearch/shows?q=%s" % requests.utils.quote(title_safe)
            mj = self.http.get(url_maze, timeout=(3, 6)).json()
            if not isinstance(mj, dict):
                return False, "[SKIP : fanart] Not found"

            tvdb_id = mj.get('externals', {}).get('thetvdb')
            
            if not tvdb_id:
                return False, "[SKIP : fanart] No TVDB ID"
            
            # FanArt API
            url_fanart = "https://webservice.fanart.tv/v3/tv/%s?api_key=%s" % (tvdb_id, fanart_api)
            fjs = self.http.get(url_fanart, timeout=(3, 6)).json()
            
            # Backdrop/Fanart priorisieren
            backdrop_url = None
            if fjs.get('showbackground'):
                backdrop_url = fjs['showbackground'][0].get('url')
            elif fjs.get('tvthumb'):
                backdrop_url = fjs['tvthumb'][0].get('url')
            elif fjs.get('hdtvlogo'):
                backdrop_url = fjs['hdtvlogo'][0].get('url')
            
            if backdrop_url:
                self.saveBackdrop(backdrop_url, dwn_backdrop)
                try:
                    if getattr(self, 'slug', None):
                        self.save_info_json(self.slug, {'title': (title or '').strip(), 'source': 'fanart'})
                except Exception:
                    pass
                return True, "[SUCCESS : fanart] %s" % title
            
            return False, "[SKIP : fanart] No backdrop"
            
        except Exception as e:
            if DEBUG_BACKDROP:
                print("[fanart error] %s" % str(e))
            return False, "[ERROR : fanart] %s" % str(e)

    def search_imdb(self, dwn_backdrop, title, shortdesc, fulldesc, channel=None):
        # CUSTOM override (never expires)
        ok_custom, msg_custom = self._try_custom_backdrop(dwn_backdrop, title, channel, None)
        if ok_custom:
            return True, msg_custom

        """IMDb Backdrop (verbessert).

        Hintergrund:
        - IMDb kann Bot-Checks liefern (HTML ohne og:image)
        - IMDb liefert gelegentlich nur Portrait-Bilder

        Strategie:
        1) Wenn IMDB_ID_OVERRIDE existiert: direkte Title-Page (www + mobile) abfragen und og:image nutzen.
        2) Wenn kein Override oder og:image nicht erreichbar: m.imdb.com/find Scrape.
        3) Nur SUCCESS, wenn verifyBackdrop() wirklich OK ist; sonst Fallback moeglich.
        """
        # --- Direct override (no search) ---
        try:
            ttid = get_imdb_id_override(title)
            if ttid:
                urls = [
                    "https://www.imdb.com/title/%s/" % ttid,
                    "https://m.imdb.com/title/%s/" % ttid,
                ]
                headers = {
                    "User-Agent": "Mozilla/5.0 (X11; Linux; enigma2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                }
                img_url = None
                for url in urls:
                    try:
                        r = requests.get(url, headers=headers, timeout=10)
                        if r.status_code != 200:
                            continue
                        m = re.search(r'property="og:image"\s+content="([^"]+)"', r.text)
                        if m:
                            img_url = m.group(1)
                            break
                    except Exception:
                        continue

                if img_url:
                    self.saveBackdrop(img_url, dwn_backdrop)
                    if os.path.exists(dwn_backdrop) and self.verifyBackdrop(dwn_backdrop):
                        try:
                            self.save_backdrop_info_json(get_store_slug(title), {
                                "title": title,
                                "source": "imdb",
                                "imdb_id": ttid,
                                "backdrop_url": img_url,
                                "ts": int(time.time()),
                            })
                        except Exception:
                            pass
                        return True, "[SUCCESS : imdb] %s" % img_url

                    # Portrait / ungueltig -> loeschen und weiter versuchen
                    try:
                        if os.path.exists(dwn_backdrop):
                            os.remove(dwn_backdrop)
                    except Exception:
                        pass
                    return False, "[SKIP : imdb] Not a valid backdrop"
        except Exception:
            pass

        # --- Fallback: IMDb Scraping (find) ---
        try:
            self.dwn_backdrop = dwn_backdrop
            mapped_title = self.apply_title_mapping(title)
            title_safe = (mapped_title or title or '').replace('+', ' ')

            # ensure slug for Info JSON
            try:
                if not getattr(self, 'slug', None):
                    self.slug = get_canonical_slug(mapped_title or title)
            except Exception:
                pass

            self.title_safe = sanitize_filename(title_safe or '')

            url_mimdb = "https://m.imdb.com/find?q=%s" % requests.utils.quote(title_safe)
            headers = {'User-Agent': getRandomUserAgent()}
            url_read = self.http.get(url_mimdb, headers=headers, timeout=(3, 6)).text

            imdb_pattern = re.compile(r'<img src="(https://m\.media-amazon\.com/images/[^"]+)"', re.DOTALL)
            matches = imdb_pattern.findall(url_read)

            if not matches:
                return False, "[SKIP : imdb] Not found"

            backdrop_url = matches[0]
            # Request a larger image variant (best-effort)
            backdrop_url = re.sub(r'\._V1_.*?\.jpg', '._V1_UX1280_.jpg', backdrop_url)

            self.saveBackdrop(backdrop_url, dwn_backdrop)

            if os.path.exists(dwn_backdrop) and self.verifyBackdrop(dwn_backdrop):
                try:
                    self.save_backdrop_info_json(get_store_slug(title), {
                        "title": (title or '').strip(),
                        "source": "imdb",
                        "backdrop_url": backdrop_url,
                        "ts": int(time.time()),
                    })
                except Exception:
                    pass
                return True, "[SUCCESS : imdb] %s" % (title or '')

            # downloaded but not a valid backdrop -> remove and continue with next provider
            try:
                if os.path.exists(dwn_backdrop):
                    os.remove(dwn_backdrop)
            except Exception:
                pass
            return False, "[SKIP : imdb] Not a valid backdrop"

        except Exception as e:
            if DEBUG_BACKDROP:
                print("[imdb error] %s" % str(e))
            return False, "[ERROR : imdb] %s" % str(e)


    def search_google(self, dwn_backdrop, title, shortdesc, fulldesc, channel=None):
        # CUSTOM override (never expires)
        ok_custom, msg_custom = self._try_custom_backdrop(dwn_backdrop, title, channel, None)
        if ok_custom:
            return True, msg_custom

        """Google Bildersuche als letzter Fallback.

        v2.4:
        - probiert mehrere Query-Varianten (DE/EN) und vereinfacht den Titel
        - SUCCESS nur, wenn verifyBackdrop() wirklich passt
        """
        try:
            mapped_title = self.apply_title_mapping(title)
            base_title = self.simplify_title_for_search(mapped_title or title)
            title_safe = (base_title or mapped_title or title or '').replace('+', ' ').strip()

            # ensure slug for JSON
            try:
                if not getattr(self, 'slug', None):
                    self.slug = get_canonical_slug(base_title or mapped_title or title)
            except Exception:
                pass

            q_variants = []
            if title_safe:
                q_variants.append(title_safe)
            if title and title.strip() and title.strip() != title_safe:
                q_variants.append(title.strip())
            # try longer/more specific query first
            q_variants = list(dict.fromkeys(sorted(q_variants, key=lambda s: len(s or ''), reverse=True)))

            suffixes = [
                'backdrop',
                'hintergrund',
                'wallpaper',
                'tv show backdrop',
                'serie hintergrund',
            ]

            headers = {'User-Agent': getRandomUserAgent()}
            img_pattern = re.compile(r'"(https?://[^\"]+\.(?:jpg|jpeg|png|webp))"', re.I)

            for q in q_variants[:2]:
                for suf in suffixes:
                    search_query = "%s %s" % (q, suf)
                    url = "https://www.google.com/search?q=%s&tbm=isch" % requests.utils.quote(search_query)
                    r = self.http.get(url, headers=headers, timeout=(6, 12))
                    matches = img_pattern.findall(r.text or '')

                    for img_url in matches[:12]:
                        low = img_url.lower()
                        if 'google' in low or 'gstatic' in low:
                            continue

                        self.saveBackdrop(img_url, dwn_backdrop)

                        if os.path.exists(dwn_backdrop) and self.verifyBackdrop(dwn_backdrop):
                            try:
                                if getattr(self, 'slug', None):
                                    self.save_info_json(self.slug, {'title': (title or '').strip(), 'source': 'google'})
                            except Exception:
                                pass
                            return True, "[SUCCESS : google] %s" % (title or '')

                        try:
                            if os.path.exists(dwn_backdrop):
                                os.remove(dwn_backdrop)
                        except Exception:
                            pass

            return False, "[SKIP : google] Not found"

        except Exception as e:
            if DEBUG_BACKDROP:
                print("[google error] %s" % str(e))
            return False, "[ERROR : google] %s" % str(e)

    # ========================================================================
    # HELPER METHODS

    # ========================================================================

    def saveBackdrop(self, url, filepath):
        """Download + normalize backdrop as bounded baseline JPEG."""
        import io
        tmp = filepath + '.tmp'
        try:
            headers = {'User-Agent': getRandomUserAgent()}
            response = self.http.get(url, headers=headers, timeout=(3, 8))
            response.raise_for_status()
            data = response.content or b''

            img = Image.open(io.BytesIO(data))
            try:
                img = img.convert('RGB')
            except Exception:
                pass

            width, height = img.size
            if not width or not height:
                try:
                    img.close()
                except Exception:
                    pass
                return False

            scale = min(float(MAX_BACKDROP_W) / float(width), float(MAX_BACKDROP_H) / float(height), 1.0)
            new_width = max(1, int(round(width * scale)))
            new_height = max(1, int(round(height * scale)))

            if new_width != width or new_height != height:
                try:
                    rimg = img.resize((new_width, new_height), Image.LANCZOS)
                except Exception:
                    rimg = img.resize((new_width, new_height), Image.ANTIALIAS)
                try:
                    img.close()
                except Exception:
                    pass
                img = rimg

            img.save(tmp, 'JPEG', quality=90, optimize=True, progressive=False)
            try:
                img.close()
            except Exception:
                pass
            os.replace(tmp, filepath)
            return True

        except Exception as e:
            if DEBUG_BACKDROP:
                print("[saveBackdrop error] %s" % str(e))
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass
            return False

    def verifyBackdrop(self, dwn_backdrop):


        """Prüft, ob ein geladenes Bild als Backdrop taugt."""
        try:
            if not os.path.exists(dwn_backdrop):
                return False

            # basic content checks
            try:
                with open(dwn_backdrop, 'rb') as f:
                    head = f.read(12)
                # PNG magic
                if head.startswith(bytes((0x89, 0x50, 0x4E, 0x47))):
                    return False
                # WebP magic
                if head[0:4] == b'RIFF' and head[8:12] == b'WEBP':
                    return False
            except Exception:
                pass

            img = Image.open(dwn_backdrop)
            w, h = img.size
            img.close()

            if w <= 0 or h <= 0:
                return False
            if w < 300 or h < 160:
                return False
            ratio = float(w) / float(h)
            if ratio < 1.40:
                return False
            if ratio > 2.20:
                return False
            return True
        except Exception:
            return False

    def resizeBackdrop(self, dwn_backdrop):

        """Shrink backdrop to the configured maximum box without upscaling."""
        try:
            img = Image.open(dwn_backdrop)
            try:
                img = img.convert('RGB')
            except Exception:
                pass
            width, height = img.size
            if not width or not height:
                try:
                    img.close()
                except Exception:
                    pass
                return

            scale = min(float(MAX_BACKDROP_W) / float(width), float(MAX_BACKDROP_H) / float(height), 1.0)
            new_width = max(1, int(round(width * scale)))
            new_height = max(1, int(round(height * scale)))

            if new_width != width or new_height != height:
                try:
                    rimg = img.resize((new_width, new_height), Image.LANCZOS)
                except Exception:
                    rimg = img.resize((new_width, new_height), Image.ANTIALIAS)
                try:
                    img.close()
                except Exception:
                    pass
                img = rimg

            img.save(dwn_backdrop, 'JPEG', quality=90, optimize=True, progressive=False)
            try:
                img.close()
            except Exception:
                pass
        except Exception as e:
            if DEBUG_BACKDROP:
                print("[resizeBackdrop error] %s" % str(e))

    def checkType(self, shortdesc, fulldesc):
        """Bestimmt Medientyp."""
        fd = ''
        if shortdesc:
            fd = shortdesc.splitlines()[0]
        elif fulldesc:
            fd = fulldesc.splitlines()[0]
        return "multi", fd

    def UNAC(self, string):
        """Entfernt Akzente und Sonderzeichen."""
        try:
            string = html.unescape(string) if PY3 else html.unescape(string)
            string = unicodedata.normalize('NFD', string)
            string = re.sub(r'[\u0300-\u036f]', '', string)
            string = re.sub(r"[,!?\.\"]", ' ', string)
            string = re.sub(r'\s+', ' ', string)
            return string.strip()
        except:
            return string





    # Provider order preference by media type
    #   - Movies: prefer TMDb before TVDb
    #   - Series: prefer TVDb before TMDb
    # ------------------------------------------------------------------
    def _get_media_hint(self, title, shortdesc, fulldesc):
        try:
            slug = get_store_slug(title)
            info_p = os.path.join(info_folder, slug + ".json")
            if os.path.exists(info_p):
                try:
                    data = json.load(open(info_p, "r"))
                    mt = (data.get("media_type") or "").lower().strip()
                    if mt in ("movie", "tv"):
                        return mt
                except Exception:
                    pass
            txt = "%s %s" % (shortdesc or "", fulldesc or "")
            # Simple heuristics
            if re.search(r"\b(staffel|folge|episode|s\d+e\d+)\b", txt, re.I):
                return "tv"
            if re.search(r"\b(film|spielfilm|kino|movie)\b", txt, re.I):
                return "movie"
        except Exception:
            pass
        return None

    def _reorder_providers_for_media(self, providers, media_hint):
        try:
            if not providers or not isinstance(providers, (list, tuple)):
                return providers
            prov = list(providers)
            if media_hint == "movie":
                # ensure tmdb before tvdb
                if "tmdb" in prov and "tvdb" in prov and prov.index("tmdb") > prov.index("tvdb"):
                    prov.remove("tmdb")
                    prov.insert(prov.index("tvdb"), "tmdb")
            elif media_hint == "tv":
                # ensure tvdb before tmdb
                if "tmdb" in prov and "tvdb" in prov and prov.index("tvdb") > prov.index("tmdb"):
                    prov.remove("tvdb")
                    prov.insert(prov.index("tmdb"), "tvdb")
            return prov
        except Exception:
            return providers

    def downloadData(self, canal, base, title, shortdesc, fulldesc, dwn_backdrop):
        """Main entry point called by GradientFHDBackdropX.py.
        Canonical slug is provided by GradientFHDBackdropX.py via get_store_slug(title).
        """
        try:
            raw_title = title or ""
            base_title = _strip_episode_tokens(raw_title)

            if base_title and base_title.strip().lower() in SKIP_TITLES:
                try:
                    self.logAutoDB("[SKIP : title] %s (filler)" % base_title)
                except Exception:
                    pass
                return False, "[SKIP : title] filler"

            title = base_title

            # try existing cached backdrop
            try:
                if os.path.exists(dwn_backdrop) and os.path.getsize(dwn_backdrop) > 0:
                    return True, "[CACHE : backdrop] %s" % dwn_backdrop
            except Exception:
                pass
            # try to reuse from Info json (tmdb backdrop_path)
            try:
                slug0 = get_canonical_slug(title) or convtext(title)
                ok_info, _msg = self._try_backdrop_from_info_json(dwn_backdrop, title, slug0)
                if ok_info:
                    return True, "[CACHE : info] %s" % title
            except Exception:
                pass

            providers = get_provider_override(title)

            # media-type based provider preference

            try:

                media_hint = self._get_media_hint(title, shortdesc, fulldesc)

                providers = self._reorder_providers_for_media(providers, media_hint)

            except Exception:

                pass

            for p in providers:
                try:
                    if p == "tmdb":
                        ok, msg = self.search_tmdb(dwn_backdrop, title, shortdesc, fulldesc, canal)
                    elif p == "tvdb":
                        ok, msg = self.search_tvdb(dwn_backdrop, title, shortdesc, fulldesc, canal)
                    elif p == "fanart":
                        ok, msg = self.search_fanart(dwn_backdrop, title, shortdesc, fulldesc, canal)
                    elif p == "imdb":
                        ok, msg = self.search_imdb(dwn_backdrop, title, shortdesc, fulldesc, canal)
                    elif p == "google":
                        ok, msg = self.search_google(dwn_backdrop, title, shortdesc, fulldesc, canal)
                    else:
                        continue

                    if ok:
                        try:
                            self.logAutoDB("[OK : %s] %s" % (p, msg))
                        except Exception:
                            pass
                        return True, msg
                    else:
                        try:
                            self.logAutoDB("%s" % msg)
                        except Exception:
                            pass
                except Exception as e:
                    try:
                        self.logAutoDB("[ERROR : %s] %s (%s)" % (p, title, str(e)))
                    except Exception:
                        pass

            return False, "[SKIP] Not found"
        except Exception as e:
            try:
                self.logAutoDB("[ERROR] downloadData failed: %s" % str(e))
            except Exception:
                pass
            return False, "[ERROR] downloadData failed"

    def PMATCH(self, textA, textB):
        """Berechnet Uebereinstimmung zwischen zwei Strings."""
        if not textB or not textA:
            return 0
        if textA == textB:
            return 100
        if textA.replace(" ", "") == textB.replace(" ", ""):
            return 100
        lId = max(len(textA.replace(" ", "")), len(textB.replace(" ", "")))
        cId = sum(len(id) for id in textA.split() if id in textB)
        return 100 * cId // lId if lId > 0 else 0

# v2.3 OPTIMIERT - Anti-Falsche-Backdrops
print("[Backdrop v2.3] Blacklist, Dynamic Score, CSI-Check aktiv")
print("[Backdrop v2.3] Umlaut-Handling in GradientFHDConverlibr.py verbessert (ö→oe)")
