#!/usr/bin/python
# -*- coding: utf-8 -*-

# edit by lululla 07.2022
# recode from lululla 2023

# 02.26 @stein17, Many new features and improvements

from Components.config import config
from PIL import Image, ImageFile

# Pillow compatibility for ANTIALIAS / Resampling
try:
    Image.MAX_IMAGE_PIXELS = 25000000
    ImageFile.LOAD_TRUNCATED_IMAGES = True
except Exception:
    pass
try:
    try:
        ANTIALIAS = Image.Resampling.LANCZOS
    except Exception:
        try:
            ANTIALIAS = ANTIALIAS
        except Exception:
            ANTIALIAS = getattr(Image, 'ANTIALIAS', 1)
except Exception:
    ANTIALIAS = 1


from enigma import getDesktop
import os
import shutil
import re
import requests

import time
import json

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

    # TVDB placeholder detection -> treat as "no poster"
    # Example: images/missing/series.jpg  (comes from legacy banners.xml)
    if "images/missing" in banner_path:
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


def _force_tv_hint_if_episodic(hint, raw_title):
    try:
        if (hint or '').lower() != 'movie':
            return hint
        t = (raw_title or '')
        # episode markers -> treat as TV
        if re.search(r"\(\s*\d+\s*\)\s*$", t):  # (1609)
            return 'tv'
        if re.search(r"\bS\d+\s*E\d+\b", t, re.IGNORECASE):
            return 'tv'
        if re.search(r"\bFolge\s*\d+", t, re.IGNORECASE):
            return 'tv'
        if re.search(r"\b\d+\s*/\s*\d+\b", t):  # 25/64
            return 'tv'
    except Exception:
        pass
    return hint

# ------------------------------------------------------------
# Image sanity helpers
# ------------------------------------------------------------
MAX_POSTER_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_POSTER_PIXELS = 25_000_000

def _get_image_size(path):
    try:
        with Image.open(path) as im:
            return im.size  # (w, h)
    except Exception:
        return (0, 0)

def _image_too_large(path):
    try:
        if not path or not os.path.exists(path):
            return False
        if os.path.getsize(path) > MAX_POSTER_BYTES:
            return True
        w, h = _get_image_size(path)
        if not w or not h:
            return False
        if (w * h) > MAX_POSTER_PIXELS:
            return True
    except Exception:
        return False
    return False

def _is_portrait(path):
    w, h = _get_image_size(path)
    return (h > w) and w > 0 and h > 0

def _remove_silent(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

import sys
import threading
import difflib
import unicodedata
import random
import time  # FIX: für TVDB v4 Token-Caching
import json
from random import choice
from requests import get, exceptions
from twisted.internet.reactor import callInThread

try:
    from .GradientFHDConverlibr import convtext, apply_title_mapping, get_canonical_slug, normalize_title_for_filename, is_daily_series, get_search_variants, get_min_score_for_title, check_for_existing_file
except:
    try:
        from GradientFHDConverlibr import convtext, apply_title_mapping, get_canonical_slug, normalize_title_for_filename, is_daily_series, get_search_variants, get_min_score_for_title, check_for_existing_file
    except:
        convtext = lambda x: x.lower().replace(' ', '_') if x else ""
        get_canonical_slug = convtext
        normalize_title_for_filename = convtext
        is_daily_series = lambda x: False
        get_search_variants = lambda x: [x]
        get_min_score_for_title = lambda x: 60
        check_for_existing_file = lambda t,f,e='.jpg': (False, None)
        apply_title_mapping = lambda x: x
        apply_title_mapping = lambda x: x
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

global my_cur_skin, srch

# ---- Skin-Pfad für Custom-API-Keys ----------------------------------------
try:
    cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')
except Exception:
    cur_skin = 'GradientFHD'
my_cur_skin = False   # False = noch nicht versucht, None = versucht/fehlgeschlagen

PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True
    import html
    html_parser = html
else:
    from HTMLParser import HTMLParser
    html = HTMLParser()


try:
    from urllib.parse import quote_plus
except:
    from urllib import quote_plus


try:
    lng = config.osd.language.value
    lng = lng[:-3]
except:
    lng = 'en'
    pass


# einfache Alias-Liste fuer bekannte deutsche Titel -> Originaltitel
alias_map = {
    "sat 1 fruhstucksfernsehen": "sat.1-frühstücksfernsehen",
    "fluss des lebens": "fluss des lebens",
    "wer weiss denn sowas": "wer weiß denn sowas?",
    "wer weiß denn sowas": "wer weiß denn sowas?",
    "unsere helden die tierarzte in der arktis": "unsere helden die tierärzte in der arktis",

    'fang des lebens der gefahrlichste job alaskas': 'deadliest catch',
    "hor mal wer da hammert": 'home improvement',
    "j a g im auftrag der ehre": 'jag',
    "punkt 12 das rtl mittagsjournal": 'punkt 12',
    "auf streife die spezialisten": 'auf streife die spezialisten',
    "auf streife": 'auf streife',
    "csi miami": 'csi: miami',
    "two and a half men": 'two and a half men',
    "tagesschau": 'tagesschau',
    "heute in deutschland": 'heute',
}

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


def getRandomUserAgent():
    useragents = [
        'Mozilla/5.0 (compatible; Konqueror/4.5; FreeBSD) KHTML/4.5.4 (like Gecko)',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20120101 Firefox/29.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20120101 Firefox/35.0',
        'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:28.0) Gecko/20100101 Firefox/28.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
        'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; de) Presto/2.9.168 Version/11.52',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
    ]
    return random.choice(useragents)


tmdb_api = FALLBACK_API_MARKER
omdb_api = FALLBACK_API_MARKER
# TheTVDB fallback is supplied by the Gradient API proxy.
TVDB_LEGACY_DEFAULT_KEY = FALLBACK_API_MARKER
# default: use built-in legacy key unless user overrides via /usr/share/enigma2/<skin>/thetvdbkey
thetvdbkey = TVDB_LEGACY_DEFAULT_KEY

# Fanart.tv API key (optional). Override via /usr/share/enigma2/<skin>/fanartkey
fanart_api = FALLBACK_API_MARKER




# ----------------------------------------------------------------------------
# Central API key container (used by MovieScanner + other modules)
# Plugin-config keys (if set) still have priority; this is only the bundled default.
# ----------------------------------------------------------------------------
API_KEYS = {
	"tmdb_api": tmdb_api,
	"omdb_api": omdb_api,
	"tvdb_api": thetvdbkey,   # legacy XML key (hex32) OR v4 UUID if user overrides externally
	"fanart_api": fanart_api,
}

def get_api_key(name, default=""):
	try:
		ak = API_KEYS.get(name)
		return (ak or default or "").strip()
	except Exception:
		return (default or "").strip()

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
            log('TVDB v4 login exception: %s [Sendung: %s]' % (str(e), search_title or '?'))  # FIX
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


def _tvdb_v4_search_series(api_key, query, log=None):
    query = (query or '').strip()
    if not query:
        return None, None

    # DE -> ohne language -> EN
    for params in (
        {'query': query, 'type': 'series', 'language': 'deu', 'limit': 10},
        {'query': query, 'type': 'series', 'limit': 10},
        {'query': query, 'type': 'series', 'language': 'eng', 'limit': 10},
    ):
        j = _tvdb_v4_get(api_key, '/search', params=params, log=log)
        data = (j or {}).get('data') or []
        if not isinstance(data, list) or not data:
            continue

        it = data[0] or {}
        tvdb_id = it.get('tvdb_id') or it.get('id')
        try:
            tvdb_id = int(tvdb_id)
        except Exception:
            tvdb_id = None

        poster = it.get('poster') or it.get('image_url') or it.get('thumbnail')
        return tvdb_id, _tvdb_v4_artwork_url(poster)

    return None, None


def _tvdb_v4_best_backdrop(api_key, tvdb_id, log=None):
    if not tvdb_id:
        return None

    # DE -> ohne lang -> EN
    for params in (
        {'lang': 'deu'},
        {},
        {'lang': 'eng'},
    ):
        j = _tvdb_v4_get(api_key, '/series/%s/artworks' % tvdb_id, params=params, log=log)
        if not j:
            continue

        data = j.get('data')
        artworks = None

        if isinstance(data, dict):
            artworks = data.get('artworks') or data.get('images')
        elif isinstance(data, list):
            artworks = data

        if not isinstance(artworks, list) or not artworks:
            continue

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

            # Querformat bevorzugen
            if w and h and w < h:
                continue

            score = a.get('score') or 0
            try:
                score = float(score)
            except Exception:
                score = 0.0

            cand = (w, score, img)
            if best is None or cand[0] > best[0] or (cand[0] == best[0] and cand[1] > best[1]):
                best = cand

        if best:
            return _tvdb_v4_artwork_url(best[2])

    return None




def clean_recursive(regexStr="", replaceStr="", eventTitle=""):
    while True:
        clean_name = re.sub(regexStr, replaceStr, eventTitle)
        if clean_name == eventTitle:
            break
        eventTitle = clean_name
    return clean_name


def _load_custom_api_keys():
    """Load custom API keys from skin folder (called once at module level and on demand).
    Priority: skin-folder files > built-in renderer defaults.
    Supports both thetvdbkey (UUID v4) and thetvdbkey_legacy (32-hex) separately.
    """
    global tmdb_api, omdb_api, fanart_api, thetvdbkey, my_cur_skin
    try:
        sd = "/usr/share/enigma2/{}".format(cur_skin)
        skin_paths = {
            "tmdb_api":    [
                os.path.join(sd, "tmdbkey"),
                os.path.join(sd, "apikey"),
            ],
            "omdb_api":    [os.path.join(sd, "omdbkey")],
            "fanart_api":  [os.path.join(sd, "fanartkey")],
            # UUID v4 key is stored in thetvdbkey; legacy 32-hex in thetvdbkey_legacy
            "thetvdbkey":  [
                os.path.join(sd, "thetvdbkey"),
            ],
            "thetvdbkey_legacy": [
                os.path.join(sd, "thetvdbkey_legacy"),
            ],
        }
        loaded_any = False
        for key, paths in skin_paths.items():
            for path in (paths or []):
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
                        # Only override thetvdbkey with legacy key if no UUID key is set
                        if not _is_tvdb_uuid_key(thetvdbkey):
                            thetvdbkey = value
                    loaded_any = True
                    break
        my_cur_skin = True if loaded_any else None
    except Exception:
        my_cur_skin = None


try:
    _load_custom_api_keys()
except Exception:
    my_cur_skin = None


def get_tmdb_api_key():
    try:
        return (tmdb_api or "").strip()
    except Exception:
        return ""


# Keep the on-disk poster cache lightweight.
# The renderer widgets in this skin currently top out around 340x500, so there is
# no benefit in caching giant poster files like 780x1170 / 1280x1920 for normal use.
# AutoDB keeps working; only the stored poster size is reduced to a sensible maximum.
MAX_POSTER_W = 340
MAX_POSTER_H = 500
STORAGE_BASES = ("/media/hdd", "/media/usb", "/media/mmc", "/media/net", "/media/autofs")
isz = "185,278"
bisz = "340,500"
screenwidth = getDesktop(0).size()
if screenwidth.width() <= 1280:
    isz = "185,278"
    bisz = "300,450"
elif screenwidth.width() <= 1920:
    isz = "342,500"
    bisz = "340,500"
else:
    isz = "342,500"
    bisz = "340,500"


def isMountedInRW(mount_point):
    with open("/proc/mounts", "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) > 1 and parts[1] == mount_point:
                return True
    return False


def getPosterXBasePath():
    """Return the user selected base path for /xtra.
    Falls back to auto detection (HDD -> USB -> MMC -> NAS)."""
    try:
        from Components.config import config
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
    global base_path, xtra_base, path_folder, info_folder, poster_info_folder
    base_path = getPosterXBasePath()
    xtra_base = os.path.join(base_path, "xtra")

    # Default/fallback folders
    path_folder = os.path.join(xtra_base, "poster")
    info_folder = os.path.join(xtra_base, "Info")
    poster_info_folder = os.path.join(xtra_base, "poster_info")

    if not ensure:
        return

    # Directory creation may wake an unavailable NAS/autofs mount. Call this
    # only from a download worker, never while Enigma2 creates the renderer.
    for d in (
        xtra_base,
        path_folder,
        info_folder,
        poster_info_folder,
        os.path.join(xtra_base, "backdrop"),
        os.path.join(xtra_base, "backdrop_info"),
        os.path.join(xtra_base, "custom", "poster"),
        os.path.join(xtra_base, "custom", "backdrop"),
    ):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass

_refresh_storage_paths(ensure=False)




def try_upgrade_poster_from_info(title, out_path):
    """If /xtra/Info provides a TMDb poster_path, prefer it over weak sources (e.g. Google)."""
    try:
        slug = get_store_slug(title)
        jf = os.path.join(info_folder, slug + ".json")
        if not os.path.exists(jf):
            return False
        data = json.load(open(jf))
        poster_path = data.get("poster_path") or ""
        tmdb_id = data.get("tmdb_id") or data.get("id")
        if not poster_path:
            return False
        url = "https://image.tmdb.org/t/p/w500" + poster_path
        if _download_file_simple(url, out_path, timeout=(10, 25)):
            # sanity: portrait posters only
            if _is_portrait(out_path):
                try:
                    os.makedirs(poster_info_folder, exist_ok=True)
                except Exception:
                    pass
                try:
                    info = {
                        "title": data.get("title") or data.get("name") or title,
                        "source": "tmdb",
                        "tmdb_id": int(tmdb_id) if tmdb_id is not None else None,
                        "poster_url": url,
                        "poster_path": poster_path,
                        "fetched_at": int(time.time())
                    }
                    tmp = os.path.join(poster_info_folder, slug + ".json.tmp")
                    out_json = os.path.join(poster_info_folder, slug + ".json")
                    with open(tmp, "w") as f:
                        json.dump(info, f, ensure_ascii=False, indent=2)
                    os.replace(tmp, out_json)
                except Exception:
                    pass
                return True
            _remove_silent(out_path)
        return False
    except Exception:
        return False

def _download_file_simple(url, out_path, timeout=(3.05, 6)):
    """Kleiner Downloader fuer load_poster_from_json (ohne Thread-Objekt)."""
    try:
        headers = {'User-Agent': getRandomUserAgent()}
        r = requests.get(url, headers=headers, stream=True, timeout=timeout)
        if r.status_code != 200:
            return False
        try:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
        except Exception:
            pass
        tmp = out_path + '.tmp'
        with open(tmp, 'wb') as f:
            for chunk in r.iter_content(1024 * 64):
                if chunk:
                    f.write(chunk)
        os.replace(tmp, out_path)
        if _image_too_large(out_path):
            _remove_silent(out_path)
            return False
        return True
    except Exception:
        return False



# ==========================
# Canonical slug + overrides
# ==========================

DEFAULT_PROVIDER_ORDER = ["tmdb", "tvdb", "fanart", "imdb", "google", "omdb"]

# Provider overrides by canonical slug (underscore-based)
PROVIDER_OVERRIDES = {
    # RTL Punkt-* : IMDb ist am besten, aber falls IMDb blockt (403/429) -> Google Fallback.
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


# =========================================================================
# SERIES / FRANCHISE RULES (avoid episode-title poster spam + force originals)
# =========================================================================
SERIES_RULES = [
    {'id':'impractical_jokers', 'match_prefixes':['bad_buddies_echte_schadenfreu'], 'base_title':'Impractical Jokers', 'base_slug':'impractical_jokers', 'force_orig':'Impractical Jokers'},
    {'id':'dangerous_borders', 'match_prefixes':['dangerous_borders_grenzschutz_suedamerika'], 'base_title':"The World's Most Dangerous Borders", 'base_slug':'the_worlds_most_dangerous_borders', 'force_orig':"The World's Most Dangerous Borders"},
    {'id':'bergwelten', 'match_prefixes':['bergwelten'], 'base_title':'Bergwelten', 'base_slug':'bergwelten'},
    {'id':'besseresser', 'match_prefixes':['besseresser'], 'base_title':'BesserEsser', 'base_slug':'besseresser', 'providers':['tmdb']},
    {'id':'blaue_planet', 'match_prefixes':['der_blaue_planet'], 'base_title':'Der Blaue Planet', 'base_slug':'der_blaue_planet'},
    {'id':'praxis_mit_meerblick', 'match_prefixes':['praxis_mit_meerblick'], 'base_title':'Praxis mit Meerblick', 'base_slug':'praxis_mit_meerblick'},
    {'id':'rund_um_den_globus', 'match_prefixes':['rund_um_den_globus'], 'base_title':'Rund um den Globus', 'base_slug':'rund_um_den_globus'},
    {'id':'sea_patrol', 'match_prefixes':['sea_patrol'], 'base_title':'Sea Patrol', 'base_slug':'sea_patrol'},
    {'id':'versailles', 'match_prefixes':['versailles'], 'base_title':'Versailles', 'base_slug':'versailles'},
    {'id':'geld_macht_liebe', 'match_prefixes':['geld_macht_liebe'], 'base_title':'Geld.Macht.Liebe', 'base_slug':'geld_macht_liebe'},
    {'id':'ladykracher', 'match_prefixes':['ladykracher'], 'base_title':'Ladykracher', 'base_slug':'ladykracher'},
    {'id':'capturing_winter', 'match_prefixes':['capturing_winter'], 'base_title':'Capturing Winter', 'base_slug':'capturing_winter', 'providers':['tvdb']},
    {'id':'die_ps_profis', 'match_prefixes':['die_ps_profis_mehr_power_aus_dem_pott'], 'base_title':'Die PS-Profis - Mehr Power aus dem Pott', 'base_slug':'die_ps_profis_mehr_power_aus_dem_pott', 'providers':['tvdb']},
    {'id':'die_alpen_von_oben', 'match_prefixes':['die_alpen_von_oben'], 'base_title':'Die Alpen von Oben', 'base_slug':'die_alpen_von_oben', 'force_orig':'The Alps from Above'},
    {'id':'extreme_iceland', 'match_prefixes':['extreme_iceland'], 'base_title':'Extreme Iceland', 'base_slug':'extreme_iceland'},
    {'id':'planet_weltweit', 'match_prefixes':['planet_weltweit'], 'base_title':'Planet Weltweit', 'base_slug':'planet_weltweit'},
    {'id':'sprintour', 'match_prefixes':['sprintour'], 'base_title':'Sprintour', 'base_slug':'sprintour'},
    {'id':'vip_trip', 'match_prefixes':['vip_trip_prominente_auf_reisen'], 'base_title':'VIP Trip - Prominente auf Reisen', 'base_slug':'vip_trip_prominente_auf_reisen'},
    {'id':'most_amazing_clips', 'match_prefixes':['most_amazing_clips'], 'base_title':'Most Amazing Clips', 'base_slug':'most_amazing_clips'},
    {'id':'terra_x', 'match_prefixes':['terra_x'], 'base_title':'Terra X', 'base_slug':'terra_x'},
    {'id':'terra_x_history', 'match_prefixes':['terra_x_history'], 'base_title':'Terra X History', 'base_slug':'terra_x_history'},
]

def _apply_series_rules(qv):
    try:
        raw_title = (qv.get('mapped_title') or qv.get('raw_title') or '').strip()
        raw_slug  = get_canonical_slug(raw_title)
        slug_title = (qv.get('slug_title') or '').strip()
        slug_slug  = get_canonical_slug(slug_title) if slug_title else raw_slug
        matched = None
        for r in SERIES_RULES:
            for pref in (r.get('match_prefixes') or []):
                if raw_slug == pref or raw_slug.startswith(pref + "_") or slug_slug == pref or slug_slug.startswith(pref + "_"):
                    matched = r
                    break
            if matched:
                break
        if not matched:
            return qv
        base_title = matched.get('base_title') or slug_title or raw_title
        base_slug  = matched.get('base_slug') or get_canonical_slug(base_title)

        # Terra X: keep full title first, then fallback to base variants
        if matched.get('id') in ('terra_x','terra_x_history'):
            deq = list(qv.get('de_queries') or [])
            if raw_title and (raw_title not in deq):
                deq = [raw_title] + deq
            if base_title and base_title not in deq:
                deq.append(base_title)
            if matched.get('id') == 'terra_x' and 'Terra X History' not in deq:
                deq.append('Terra X History')
            qv['de_queries'] = deq
        else:
            deq = []
            forced_de = matched.get('force_de')
            if forced_de:
                deq.append(forced_de)
            if base_title and base_title not in deq:
                deq.append(base_title)
            qv['de_queries'] = deq

        forced_orig = matched.get('force_orig')
        if forced_orig:
            oq = list(qv.get('orig_queries') or [])
            if forced_orig not in oq:
                oq = [forced_orig] + oq
            qv['orig_queries'] = oq

        qv['base_title'] = base_title
        qv['base_slug'] = base_slug
        qv['rule_id'] = matched.get('id')
        if matched.get('providers'):
            qv['providers_override'] = matched.get('providers')
        return qv
    except Exception:
        return qv


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


def _detect_media_hint(title, shortdesc=None, fulldesc=None):
    """Heuristic: returns 'tv' or 'movie' (prefer TV unless clear film indicators exist)."""
    t = (title or "").lower()
    sd = (shortdesc or "").lower()
    fd = (fulldesc or "").lower()
    hay = " ".join([t, sd, fd])

    # TV indicators
    tv_patterns = [
        r"\bstaffel\b", r"\bepisode\b", r"\bfolge\b", r"\bteil\b",
        r"\bs\d{1,2}\s*e\d{1,2}\b", r"\bs\d{1,2}e\d{1,2}\b",
        r"\b\d{1,4}\s*/\s*\d{1,4}\b",  # 1/10 etc.
        r"\b\d{1,4}\s*\(\d{1,4}\)\b"
    ]
    for p in tv_patterns:
        try:
            if re.search(p, hay, flags=re.IGNORECASE):
                return "tv"
        except Exception:
            pass

    # Film indicators (only if explicitly present in EPG)
    film_patterns = [r"\bspielfilm\b", r"\bfilm\b", r"\bkino\b", r"\bmovie\b"]
    for p in film_patterns:
        try:
            if re.search(p, hay, flags=re.IGNORECASE):
                return "movie"
        except Exception:
            pass

    # Year in title -> likely a movie
    try:
        if re.search(r"\((19|20)\d{2}\)", title or "") or re.search(r"\b(19|20)\d{2}\b", title or ""):
            return "movie"
    except Exception:
        pass

    # Default: tv is a safer default for German EPG (Daily Soaps etc.)
    return "tv"

# =========================================================================
# TITLE NORMALIZATION & SEARCH VARIANTS (DE -> ORIGINAL fallback)
# =========================================================================

_GERMAN_STOPWORDS = set([
    "der","die","das","und","mit","ohne","nicht","nichts","echt","echte","weltweit","alarm","im","cockpit",
    "wettkampf","schmiede","waffenschmiede","staffel","folge","teil","episode"
])

_ENGLISH_STOPWORDS = set([
    'the','a','an','and','or','of','in','on','to','with','for','from','by','at','into','over','under',
    'without','vs','versus',
])

def _looks_person_name(s):
    """Heuristic: two or three Title-Case words => likely a person name (avoid orig-de)."""
    try:
        if not s:
            return False
        t = s.strip()
        low_words = re.findall(r"[A-Za-zÄÖÜäöüß]+", t.lower())
        if any(w in _ENGLISH_STOPWORDS for w in low_words):
            return False
        return bool(re.match(r"^[A-ZÄÖÜ][A-Za-zÄÖÜäöüß]+(?:\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß]+){1,2}$", t))
    except Exception:
        return False


def _looks_english(s):
    """Heuristic for 'Original - German' titles. Avoids false positives for person names."""
    try:
        if not s:
            return False
        t = s.strip()
        if not t:
            return False
        if _looks_person_name(t):
            return False
        if re.search(r"[äöüßÄÖÜ]", t):
            return False
        if re.search(r"[^A-Za-z0-9 \-:'\(\)\[\]!?,.&/]", t):
            return False
        words = re.findall(r"[A-Za-z]+", t.lower())
        if not words:
            return False
        if any(w in _ENGLISH_STOPWORDS for w in words):
            return True
        if len(words) == 1 and words[0] not in _GERMAN_STOPWORDS:
            return True
        return False
    except Exception:
        return False

def _looks_german(s):
    try:
        if not s:
            return False
        t = s.strip()
        if not t:
            return False
        if re.search(r"[äöüßÄÖÜ]", t):
            return True
        words = re.findall(r"[A-Za-zÄÖÜäöüß]+", t.lower())
        if not words:
            return False
        german_hits = sum(1 for w in words if w in _GERMAN_STOPWORDS)
        return german_hits >= 1
    except Exception:
        return False

def _strip_subtitle(title):
    try:
        t = (title or "").strip()
        t = _strip_episode_tokens(t)
        t = re.sub(r"\s*\[[^\]]+\]\s*$", "", t).strip()
        t = re.sub(r"\s*\([^\)]+\)\s*$", "", t).strip()
        if ":" in t and len(t.split(":")[0].strip()) >= 4:
            t = t.split(":", 1)[0].strip()
        if " - " in t:
            left = t.split(" - ", 1)[0].strip()
            if len(left) >= 3:
                t = left
        return t.strip()
    except Exception:
        return title


# --- v17: external title overrides (small, user-maintained) -----------------
_TITLE_OVERRIDES_CACHE = {"mtime": None, "data": None}

def _title_overrides_path():
    for p in (os.path.join(xtra_base, "custom", "title_overrides.json"), os.path.join(xtra_base, "title_overrides.json")):
        if os.path.exists(p):
            return p
    return os.path.join(xtra_base, "custom", "title_overrides.json")

def _load_title_overrides():
    path = _title_overrides_path()
    try:
        st = os.stat(path)
        mtime = int(st.st_mtime)
    except Exception:
        _TITLE_OVERRIDES_CACHE["mtime"] = None
        _TITLE_OVERRIDES_CACHE["data"] = None
        return None

    if _TITLE_OVERRIDES_CACHE["data"] is not None and _TITLE_OVERRIDES_CACHE["mtime"] == mtime:
        return _TITLE_OVERRIDES_CACHE["data"]

    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception:
        data = None

    _TITLE_OVERRIDES_CACHE["mtime"] = mtime
    _TITLE_OVERRIDES_CACHE["data"] = data
    return data

def _match_override(store_slug, raw_title=None):
    data = _load_title_overrides()
    if not data or not store_slug:
        return None

    # A) flat dict: {"slug": "query"}
    if isinstance(data, dict) and "overrides" not in data:
        if store_slug in data:
            v = data.get(store_slug)
            return {"match": store_slug, "match_type": "slug_exact", "query": v} if isinstance(v, str) else v
        for k, v in data.items():
            if isinstance(k, str) and store_slug.startswith(k):
                return {"match": k, "match_type": "slug_prefix", "query": v} if isinstance(v, str) else v
        return None

    # B) {"overrides":[{...}]}
    if isinstance(data, dict) and isinstance(data.get("overrides"), list):
        for o in data["overrides"]:
            try:
                mt = o.get("match_type", "slug_exact")
                m = o.get("match")
                if not m:
                    continue
                if mt == "slug_exact" and store_slug == m:
                    return o
                if mt == "slug_prefix" and store_slug.startswith(m):
                    return o
                if mt == "title_exact" and raw_title and raw_title == m:
                    return o
                if mt == "title_contains" and raw_title and m in raw_title:
                    return o
            except Exception:
                continue
    return None

def _allow_google():
    return os.path.exists(os.path.join(xtra_base, ".allow_google")) or os.path.exists(os.path.join(xtra_base, "custom", ".allow_google"))

def get_query_variants(title, shortdesc=None, fulldesc=None, **kwargs):
    """v17: Generic, EPG-driven query plan (no hardcoded title lists)."""
    raw = (title or "").strip()
    raw = apply_title_mapping(raw) if callable(globals().get("apply_title_mapping")) else raw
    hint = _detect_media_hint(raw, shortdesc, fulldesc)

    def _norm_ws(s):
        return re.sub(r"\s+", " ", (s or "").strip())

    def _strip_episode_markers(s):
        s = _norm_ws(s)
        if not s:
            return s
        s = re.sub(r"\s*\(\d{1,5}\)\s*$", "", s)  # (1609)
        s = re.sub(r"\s*\b\d{1,3}\s*/\s*\d{1,3}\b\s*$", "", s)  # 25/64
        s = re.sub(r"\s*\bS\d{1,2}E\d{1,2}\b\s*$", "", s, flags=re.I)
        s = re.sub(r"\s*\b\d{1,2}x\d{1,2}\b\s*$", "", s, flags=re.I)
        s = re.sub(r"\s*[-–:]\s*Folge\b.*$", "", s, flags=re.I)
        return _norm_ws(s)

    def _punct_variant(s):
        s = _norm_ws(s)
        s = re.sub(r"[\!\?\"\']", "", s)
        return _norm_ws(s)

    full = _norm_ws(raw)
    clean = _strip_episode_markers(full)
    punct = _punct_variant(clean)

    variants = []
    for v in (full, clean, punct):
        if v and v not in variants:
            variants.append(v)

    # split variants (keep full always)
    if " - " in clean:
        left = _norm_ws(clean.split(" - ", 1)[0])
        if left and left not in variants:
            variants.append(left)
        hc = _norm_ws(clean.replace(" - ", ": "))
        if hc and hc not in variants:
            variants.append(hc)
    if ":" in clean:
        left = _norm_ws(clean.split(":", 1)[0])
        if left and left not in variants:
            variants.append(left)

    # If there are multiple separators, prefer the leftmost base title
    base_multi = None
    try:
        if clean.count(" - ") >= 2:
            base_multi = _norm_ws(clean.split(" - ", 1)[0])
            if base_multi and base_multi not in variants:
                variants.insert(0, base_multi)
    except Exception:
        pass

    slug_title = base_multi or clean or full
    base_slug = get_store_slug(slug_title) if slug_title else get_store_slug(full)

    qv = {
        "de_queries": variants,
        "orig_queries": [],
        "slug_title": slug_title,
        "base_slug": base_slug,
        "hint": "movie" if hint == "movie" else "tv",
        "reason": "v17=generic_variants"
    }

    # Orig-title fallback from /xtra/Info/<slug>.json (if present)
    try:
        info = _load_info_json_safe(base_slug)
        ot = (info.get("original_title") or info.get("original_name") or info.get("originalTitle") or "").strip()
        if ot and ot not in qv["orig_queries"]:
            qv["orig_queries"].append(ot)
    except Exception:
        pass

    ov = _match_override(base_slug, raw_title=full)
    if ov:
        qv["rule_id"] = ov.get("match", "")
        if ov.get("action") == "skip":
            qv["providers_override"] = []
            qv["reason"] = "override=skip"
            return qv
        if isinstance(ov.get("query"), str) and ov.get("query").strip():
            qv["de_queries"] = [ov["query"].strip()]
            qv["reason"] = "override=query"
        if isinstance(ov.get("providers"), list) and ov.get("providers"):
            qv["providers_override"] = ov["providers"]
            qv["reason"] = qv.get("reason","") + "|override=providers"

    return qv

def _load_info_json_safe(slug):
    """Load /xtra/Info/<slug>.json if present."""
    try:
        if not slug:
            return {}
        jf = os.path.join(info_folder, slug + ".json")
        if not os.path.exists(jf):
            return {}
        with open(jf, "r") as f:
            return json.load(f) or {}
    except Exception:
        return {}

def get_provider_override(title, shortdesc=None, fulldesc=None):
    slug = get_store_slug(title)
    if slug in PROVIDER_OVERRIDES:
        return PROVIDER_OVERRIDES.get(slug)

    hint = _detect_media_hint(title, shortdesc, fulldesc)
    # Default provider order (posters): keep it lean for speed.
    # fanart/omdb are intentionally NOT used for poster images by default.
    if hint == "movie":
        return ["tmdb", "tvdb", "imdb", "google"]
    return ["tvdb", "tmdb", "imdb", "google"]


def get_imdb_id_override(title):
    slug = get_store_slug(title)
    return IMDB_ID_OVERRIDES.get(slug)


def load_poster_from_json(title, target1, target2=None):
    import os, json
    # Use store-slug (episode-safe) so daily soaps like "Rote Rosen (1600)" map to "rote_rosen.json"
    slug = get_store_slug(title)

    # 1) Erst poster_info pruefen (enthaelt direkte URL + Quelle)
    poster_info_bases = [os.path.join(xtra_base, 'poster_info'), '/tmp/poster_info', '/tmp']
    for base in poster_info_bases:
        jf = os.path.join(base, slug + '.json')
        if os.path.exists(jf):
            try:
                data = json.load(open(jf))
                url = data.get('poster_url') or data.get('url') or ''
                if url:
                    _download_file_simple(url, target1)
                    if target2 and target2 != target1:
                        _download_file_simple(url, target2)
                    return True
            except Exception:
                pass

    # 2) Fallback: alte Meta-Info (/xtra/Info) mit TMDb poster_path
    info_bases = [os.path.join(xtra_base, 'Info'), '/tmp']
    for base in info_bases:
        jf = os.path.join(base, slug + '.json')
        if os.path.exists(jf):
            try:
                data = json.load(open(jf))
                poster_path = data.get('poster_path') or data.get('Poster') or ''
                if poster_path:
                    url = 'https://image.tmdb.org/t/p/w780' + poster_path
                    _download_file_simple(url, target1)
                    if target2 and target2 != target1:
                        _download_file_simple(url, target2)
                    return True
            except Exception:
                pass
    return False


# fallback stub
try:
    apply_title_mapping
except NameError:
    def apply_title_mapping(t):
        return t


def quoteEventName(eventName):
    try:
        text = eventName.decode('utf8').replace(u'\x86', u'').replace(u'\x87', u'').encode('utf8')
    except:
        text = eventName
    return quote_plus(text, safe="+")


def dataenc(data):
    if PY3:
        data = data.decode("utf-8")
    else:
        data = data.encode("utf-8")
    return data


def sanitize_filename(filename):
    # FIX: Normalisierte Dateinamen - IMMER lowercase gegen Duplikate
    if not filename:
        return ""
    sanitized = re.sub(r'[^\w\s-]', '', filename)
    sanitized = sanitized.lower().strip()  # FIX: IMMER lowercase!
    return sanitized



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

DEBUG_POSTER = False



def sanitize_filename_safe(filename):
    """
    v2.8: Sichere Dateinamen-Sanitisierung (KRITISCHER BUGFIX!)
    
    PROBLEM: Titel mit "/" crashen beim Speichern
    BEISPIEL: "Unschuldig (1/2)" → FileNotFoundError!
    
    WICHTIG: NUR für Dateipfade, NICHT für Such-Queries!
    """
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
    """
    v2.8: Multi-Variant Search - Die ECHTE Lösung!
    
    Generiert intelligente Such-Varianten ohne tausende manuelle Mappings.
    
    Beispiel: "Die Albtraum(ver)mieter"
    Varianten:
      1. "Die Albtraum(ver)mieter"
      2. "Albtraum(ver)mieter" (ohne "Die")
      3. "Die Albtraum ver mieter" (Sonderzeichen → Spaces) ← FINDET TVDB!
      4. "Die Albtraumvermieter" (Sonderzeichen entfernt)
      5. "Die Albtraum" (vor Klammern)
      6. "Albtraum" (ohne "Die", vor Klammern)
    """
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
    
    # Ohne deutsche Artikel
    for article in ['Die ', 'Der ', 'Das ', 'Ein ', 'Eine ']:
        if title.startswith(article):
            add_variant(title[len(article):])
    
    # Sonderzeichen als Spaces (WICHTIG!)
    clean = re.sub(r'[()\[\]{}<>]', ' ', title)
    clean = re.sub(r'\s+', ' ', clean).strip()
    add_variant(clean)
    
    # Auch ohne Artikel
    for article in ['Die ', 'Der ', 'Das ', 'The ']:
        if clean.startswith(article):
            add_variant(clean[len(article):])
    
    # Sonderzeichen entfernt
    clean2 = re.sub(r'[^a-zA-Z0-9äöüÄÖÜß\s-]', '', title)
    clean2 = re.sub(r'\s+', ' ', clean2).strip()
    add_variant(clean2)
    
    # Nur Hauptteil (vor Klammern)
    for sep in [' (', '(', ' [', '[', ' - ']:
        if sep in title:
            part = title.split(sep)[0].strip()
            if len(part) >= 3:
                add_variant(part)
                for article in ['Die ', 'Der ', 'Das ', 'The ']:
                    if part.startswith(article):
                        add_variant(part[len(article):])
    
    # Episode-Nummern entfernen
    no_numbers = re.sub(r'\s*\(\s*\d+\s*\)\s*', ' ', title)
    no_numbers = re.sub(r'\s+', ' ', no_numbers).strip()
    if no_numbers != title:
        add_variant(no_numbers)
    
    return variants[:15]  # Max 15 Varianten



class GradientFHDPosterXDownloadThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        _refresh_storage_paths(ensure=False)
        self.checkMovie = ["film", "movie", "фильм", "кино", "ταινία",
                           "película", "cinéma", "cine", "cinema",
                           "filma"]
        self.checkTV = ["serial", "series", "serie", "serien", "série",
                        "séries", "serious", "folge", "episodio",
                        "episode", "épisode", "l'épisode", "ep.",
                        "animation", "staffel", "soap", "doku", "tv",
                        "talk", "show", "news", "factual",
                        "entertainment", "telenovela", "dokumentation",
                        "dokutainment", "documentary", "informercial",
                        "information", "sitcom", "reality", "program",
                        "magazine", "mittagsmagazin", "т/с", "м/с",
                        "сезон", "с-н", "эпизод", "сериал", "серия",
                        "actualité", "discussion", "interview", "débat",
                        "émission", "divertissement", "jeu", "magasine",
                        "information", "météo", "journal", "sport",
                        "culture", "infos", "feuilleton", "téléréalité",
                        "société", "clips", "concert", "santé",
                        "éducation", "variété"]
        self.sizeb = False

    def prepare_storage(self):
        """Create cache folders from the worker thread before file/network I/O."""
        _refresh_storage_paths(ensure=True)


    # ------------------------------------------------------------------------
    # CUSTOM override: /media/hdd/xtra/custom/poster/<slug>.jpg
    # If exists, it will be copied to the destination path and all providers
    # will be skipped. Custom assets never expire.
    # ------------------------------------------------------------------------
    def _custom_base_dir(self):
        for base in (xtra_base,):
            try:
                if os.path.exists(base):
                    return base
            except Exception:
                pass
        return '/tmp'

    def _try_custom_poster(self, dwn_poster, title, slug_title=None):
        """
        Custom poster override (highest priority).

        We try multiple slug candidates so users can drop files like:
          /media/hdd/xtra/custom/poster/<store_slug>.jpg
        even when the EPG title contains episode/topic suffixes.

        Priority:
          1) store_slug (stable, based on overrides + base-title rules)
          2) slug from base title (split at ' - ' / ' – ' / ':' )
          3) slug from full raw title (legacy)

        If a custom poster exists, it is copied to dwn_poster *even if* a cached
        poster already exists elsewhere; custom always wins.
        """
        try:
            raw = (title or '').strip()
            if not raw:
                return False, None

            # base title (strip episode/topic suffixes)
            base = raw
            for sep in (' - ', ' – ', ':'):
                if sep in base:
                    base = base.split(sep, 1)[0].strip()
            if not base:
                base = raw

            # Build candidate slugs (dedup, keep order)
            candidates = []
            def _add(s):
                s = (s or '').strip().strip('_')
                if s and s not in candidates:
                    candidates.append(s)

            # stable slug(s)
            try:
                _add(get_store_slug(slug_title or raw))
            except Exception:
                pass
            try:
                _add(get_store_slug(base))
            except Exception:
                pass

            # canonical/convtext fallbacks
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

            custom_root = os.path.join(self._custom_base_dir(), 'custom', 'poster')
            for slug in candidates:
                custom_path = os.path.join(custom_root, '%s.jpg' % slug)
                if not os.path.exists(custom_path):
                    continue

                # Ensure output folder exists
                try:
                    os.makedirs(os.path.dirname(dwn_poster), exist_ok=True)
                except Exception:
                    pass

                try:
                    shutil.copy2(custom_path, dwn_poster)
                    try:
                        self.sizeb = True
                        self.resizePoster(dwn_poster)
                    except Exception:
                        pass
                except Exception:
                    # If copy fails, treat as not found
                    return False, None

                # Write info json (best effort)
                try:
                    self.save_poster_info_json(slug, {
                        'title': raw,
                        'base_title': base,
                        'source': 'custom',
                        'custom_file': custom_path,
                        'poster_file': dwn_poster,
                        'slug_candidates': candidates,
                        'fetched_at': int(time.time())
                    })
                except Exception:
                    pass

                return True, '[SUCCESS : custom] %s' % custom_path

            return False, None
        except Exception:
            return False, None


    def search_tmdb(self, dwn_poster, title, shortdesc, fulldesc, channel=None, slug_title=None):
        """TMDb poster search (harmonized with Backdrop scoring).
        
        Key points:
          - If Info/<slug>.json already has tmdb_id + poster_path -> download directly (fast).
          - Otherwise perform TMDb search with Backdrop-like scoring and write/merge Info/<slug>.json
            with both poster_path + backdrop_path when a match is found.
          - Deduplicate + cap query variants to keep requests low.
        """
        ok_custom, msg_custom = self._try_custom_poster(dwn_poster, title, slug_title)
        if ok_custom:
            return True, msg_custom
        
        # stable slug for storing + for Info lookup (independent of Backdrop)
        try:
            store_slug = get_store_slug(slug_title or title)
            self.store_slug = store_slug
        except Exception:
            store_slug = get_store_slug(slug_title or title)
        
        # Fast-path: use Info json if already present (created by Backdrop or earlier Poster hit).
        try:
            if store_slug and try_upgrade_poster_from_info(store_slug, dwn_poster) and self.verifyPoster(dwn_poster):
                return True, "[SUCCESS : tmdb] Poster from Info.json"
        except Exception:
            pass
        
        # TMDb search. No separate connectivity probe is needed here; the
        # provider request already has timeouts and reports its own error.
        try:
            tmdb_api = get_tmdb_api_key()
            if not tmdb_api:
                return False, "TMDb: missing key"
        
            from difflib import SequenceMatcher
        
            qv = get_query_variants(title, shortdesc, fulldesc, channel=channel, slug_title=slug_title)
            hint = (qv.get("hint") or "tv").lower()
            is_movie = (hint == "movie")
        
            de_queries = qv.get("de_queries") or []
            orig_queries = qv.get("orig_queries") or []
        
            # Augment orig_queries from Info/<slug>.json (original_title) if present
            try:
                if store_slug:
                    jf = os.path.join(info_folder, store_slug + ".json")
                    if os.path.exists(jf):
                        data = json.load(open(jf))
                        ot = (data.get("original_title") or "").strip()
                        if ot and ot not in orig_queries:
                            orig_queries.append(ot)
            except Exception:
                pass
        
            def _norm_q(s):
                s = (s or "").strip().lower()
                s = re.sub(r"\s+", " ", s)
                s = re.sub(r"[\!\?\"\'\(\)\[\]\{\}]", "", s)
                return s
        
            # Deduplicate queries
            seen = set()
            merged = []
            for q in (de_queries + orig_queries):
                nq = _norm_q(q)
                if not nq or nq in seen:
                    continue
                seen.add(nq)
                merged.append(q.strip())
        
            queries = merged[:3] if merged else [(title or "").strip()]
            if not queries or not queries[0]:
                return False, "TMDb: Not found"
        
            def _score(q, cand_title, cand_orig, has_poster, year=None):
                qn = _norm_q(q)
                tn = _norm_q(cand_title)
                on = _norm_q(cand_orig)
                best = 0
                for cand in (tn, on):
                    if not cand:
                        continue
                    r = int(100 * SequenceMatcher(None, qn, cand).ratio())
                    best = max(best, r)
                    if qn == cand:
                        best = max(best, 100)
                    if qn and cand and (qn in cand or cand in qn):
                        best = max(best, min(99, r + 8))
                if has_poster:
                    best += 3
                if year:
                    best += 1
                return best
        
            min_score = get_min_score_for_title(title or "")

            langs = ["de", "en", ""]

            # Live-mode speed: reduce number of queries and tighten timeouts.
            is_live = bool(getattr(self, "_is_live", False))
            if is_live:
                if queries:
                    queries = queries[:1]
                langs = ["de", "en"]
            tmdb_timeout = (2, 4) if is_live else (3, 8)

            def _search_endpoint(endpoint, query_list):
                for q in (query_list or []):
                    if not q:
                        continue
                    q_best = None
                    q_best_score = -1
                    q_best_lang = None
                    for L in langs:
                        lang = L if L else "en"
                        url = "https://api.themoviedb.org/3/search/%s?api_key=%s&language=%s&query=%s" % (
                            endpoint, tmdb_api, lang, quoteEventName(q)
                        )
                        try:
                            r = requests.get(url, timeout=tmdb_timeout)
                            if r.status_code != requests.codes.ok:
                                continue
                            js = r.json() or {}
                            results = js.get("results") or []
                        except Exception:
                            continue

                        for it in results[:10]:
                            cand_title = (it.get("name") if endpoint == "tv" else it.get("title")) or ""
                            cand_orig = (it.get("original_name") if endpoint == "tv" else it.get("original_title")) or ""
                            has_poster = bool(it.get("poster_path"))
                            date_key = "first_air_date" if endpoint == "tv" else "release_date"
                            year = (it.get(date_key) or "").strip()
                            sc = _score(q, cand_title, cand_orig, has_poster, year=year)
                            if sc > q_best_score:
                                q_best_score = sc
                                q_best = it
                                q_best_lang = lang

                        if q_best_score >= 98:
                            break

                    if q_best and q_best_score >= min_score:
                        return q_best, q_best_score, q_best_lang, q

                return None, -1, None, None

            endpoints = ["movie", "tv"] if is_movie else ["tv", "movie"]
            best = None
            best_score = -1
            best_lang = None
            best_query = None
            best_is_movie = None

            for ep in endpoints:
                b, sc, bl, bq = _search_endpoint(ep, queries)
                if b:
                    best = b
                    best_score = sc
                    best_lang = bl
                    best_query = bq
                    best_is_movie = (ep == "movie")
                    break

            if not best:
                return False, "TMDb: Not found"

            is_movie = bool(best_is_movie)
        
            poster_path_tmdb = best.get("poster_path") or ""
            tmdb_id = best.get("id")
            if not poster_path_tmdb or not tmdb_id:
                return False, "TMDb: Not found"
        
            img_url = "https://image.tmdb.org/t/p/w500" + poster_path_tmdb
            if not _download_file_simple(img_url, dwn_poster, timeout=(10, 25)):
                return False, "TMDb: download failed"
        
            if not self.verifyPoster(dwn_poster):
                try:
                    os.unlink(dwn_poster)
                except Exception:
                    pass
                return False, "TMDb: invalid poster"
        
            # Merge/write Info json (contains poster + backdrop + year etc)
            try:
                media_type = "movie" if is_movie else "tv"
                info_payload = {
                    "tmdb_id": tmdb_id,
                    "tmdb_vote_average": float(best.get("vote_average") or 0.0),
                    "tmdb_vote_count": int(best.get("vote_count") or 0),
                    "title": (best.get("title") if is_movie else best.get("name")) or (title or ""),
                    "original_title": (best.get("original_title") if is_movie else best.get("original_name")) or "",
                    "overview": best.get("overview") or "",
                    "poster_path": best.get("poster_path") or "",
                    "backdrop_path": best.get("backdrop_path") or "",
                    "original_language": best.get("original_language") or "",
                    "adult": bool(best.get("adult")) if is_movie else False,
                    "media_type": media_type,
                }
                date_key = "release_date" if is_movie else "first_air_date"
                dt = (best.get(date_key) or "").strip()
                if dt:
                    info_payload[date_key] = dt
                    info_payload["year"] = dt[:4]
                self.save_info_json(store_slug, info_payload)
            except Exception:
                pass
        
            return True, "[SUCCESS : tmdb] %s (score=%s lang=%s query=%s)" % (title, best_score, best_lang, best_query)
        
        except Exception:
            return False, "Error when searching on TMDb"
        
        
    def save_info_json(self, slug, data):
        """Speichert TMDb-Daten als JSON fuer GradientFHDStarX/Parental."""
        if not slug or not data:
            return False
        try:
            json_path = os.path.join(info_folder, slug + ".json")
            existing = {}
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r") as f:
                        existing = json.load(f)
                except:
                    existing = {}
            existing.update(data)
            tmp_path = json_path + ".tmp"
            with open(tmp_path, "w") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, json_path)
            return True
        except Exception:
            return False

    def save_poster_info_json(self, slug, data):
        """Speichert Poster-Quelle/URL getrennt in /xtra/poster_info (kein Merge)."""
        if not slug or not isinstance(data, dict):
            return False
        try:
            json_path = os.path.join(poster_info_folder, slug + ".json")
            # nicht mergen -> Quelle bleibt eindeutig
            tmp_path = json_path + ".tmp"
            with open(tmp_path, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, json_path)
            return True
        except Exception:
            return False

    def fetch_certification(self, tmdb_id, media_type):
        """Holt Altersfreigabe von TMDb (Movie: release_dates, TV: content_ratings)."""
        try:
            session = requests.Session()
            retries = Retry(total=1, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retries)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            if media_type == 'movie':
                url = "https://api.themoviedb.org/3/movie/%s/release_dates?api_key=%s" % (tmdb_id, tmdb_api)
            else:
                url = "https://api.themoviedb.org/3/tv/%s/content_ratings?api_key=%s" % (tmdb_id, tmdb_api)
            response = session.get(url, timeout=(3, 6))
            if response.status_code == 200:
                data = response.json()
                cert = None
                if media_type == 'movie':
                    for res in data.get('results', []):
                        if res.get('iso_3166_1') in ('DE', 'US', 'GB'):
                            for rel in res.get('release_dates', []):
                                if rel.get('certification'):
                                    cert = rel.get('certification')
                                    break
                        if cert:
                            break
                else:
                    for res in data.get('results', []):
                        if res.get('iso_3166_1') in ('DE', 'US', 'GB') and res.get('rating'):
                            cert = res.get('rating')
                            break
                return cert
        except Exception:
            return None
        return None


    def downloadData2(self, data):
        """Pick best TMDb result and download a single poster.

        v17: avoid downloading multiple posters / creating duplicates.
        """
        from difflib import SequenceMatcher
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        data_json = data if isinstance(data, dict) else json.loads(data)

        results = data_json.get('results') if isinstance(data_json, dict) else None
        if not results:
            return False, "TMDb: no results"

        query = getattr(self, "title_safe", "") or ""
        qn = clean_search_title(query).lower() if query else ""
        expected = getattr(self, "_expected_media_type", None)  # 'tv'|'movie'|None

        def _sim(a, b):
            try:
                return int(SequenceMatcher(None, a, b).ratio() * 100)
            except Exception:
                return 0

        best = None
        best_score = -1

        for each in results:
            try:
                poster_path = each.get('poster_path')
                if not poster_path:
                    continue
                mt = each.get('media_type')
                if not mt:
                    mt = expected or 'tv'
                if mt == "serie":
                    mt = "tv"
                title = each.get('name') or each.get('title') or ""
                tn = clean_search_title(title).lower() if title else ""
                score = _sim(qn, tn) if (qn and tn) else 0
                if expected and mt and expected != mt:
                    score -= 12
                vc = int(each.get('vote_count') or 0)
                if vc > 50:
                    score += 3
                if vc > 500:
                    score += 5
                if score > best_score:
                    best_score = score
                    best = (each, mt, title)
            except Exception:
                continue

        if not best or best_score < 55:
            return False, "TMDb: low match score (%s)" % best_score

        each, mt, title = best
        poster_path = each.get('poster_path')
        poster_url = "http://image.tmdb.org/t/p/w500" + poster_path

        try:
            info = {
                'tmdb_id': each.get('id'),
                'tmdb_vote_average': each.get('vote_average', 0),
                'tmdb_vote_count': each.get('vote_count', 0),
                'title': each.get('title') or each.get('name', ''),
                'original_title': each.get('original_title') or each.get('original_name', ''),
                'overview': each.get('overview', ''),
                'poster_path': each.get('poster_path', ''),
                'backdrop_path': each.get('backdrop_path', ''),
                'original_language': each.get('original_language', ''),
                'media_type': 'movie' if mt == 'movie' else 'tv',
                'adult': each.get('adult', False)
            }
            if mt == 'movie':
                rel = each.get('release_date', '')
                if rel:
                    info['release_date'] = rel
                    info['year'] = rel[:4]
            else:
                fa = each.get('first_air_date', '')
                if fa:
                    info['first_air_date'] = fa
                    info['year'] = fa[:4]

            cert = self.fetch_certification(each.get('id'), 'movie' if mt == 'movie' else 'tv')
            if cert:
                info['Rated'] = cert
            elif info.get('adult'):
                info['Rated'] = '18'

            slug = getattr(self, 'slug', '') or get_store_slug(getattr(self, 'store_slug', '') or title)
            self.save_info_json(slug, info)
            self.save_poster_info_json(slug, {
                'title': info.get('title') or title,
                'source': 'tmdb',
                'tmdb_id': info.get('tmdb_id'),
                'media_type': info.get('media_type'),
                'poster_url': poster_url,
                'poster_path': info.get('poster_path', ''),
                'fetched_at': int(time.time())
            })
        except Exception:
            pass

        self.savePoster(poster_url, self.dwn_poster)
        if self.verifyPoster(self.dwn_poster):
            try:
                self.resizePoster(self.dwn_poster)
            except Exception:
                pass
            return True, "TMDb: downloaded (%s)" % best_score

        return False, "TMDb: poster invalid"


    def search_tvdb(self, dwn_poster, title, shortdesc, fulldesc, channel=None, slug_title=None):
        ok_custom, msg_custom = self._try_custom_poster(dwn_poster, title, slug_title)
        if ok_custom:
            return True, msg_custom

        api_key = (thetvdbkey or '').strip()

        q = (title or '').replace('+',' ').strip()
        if not q:
            return False, "TVDb: empty title"

        try:
            poster_url = None
            tvdb_id = None

            # --- v4 UUID key path ---
            if api_key and _is_tvdb_uuid_key(api_key):
                tvdb_id, poster_url = _tvdb_v4_search_series(api_key, q, log=None)

            # --- Legacy 32-hex key path (also used as fallback when UUID gives no result) ---
            if not poster_url:
                # Determine the best legacy key to use:
                # 1. If thetvdbkey is already a 32-hex key, use it directly.
                # 2. Otherwise try to read thetvdbkey_legacy from the skin folder.
                legacy_key = None
                if api_key and _is_tvdb_hex32_key(api_key):
                    legacy_key = api_key
                else:
                    # Try thetvdbkey_legacy file
                    try:
                        lp = os.path.join(_tvdb_skin_dir(), 'thetvdbkey_legacy')
                        if os.path.exists(lp):
                            with open(lp, 'r') as _f:
                                _lv = (_f.read() or '').strip()
                            if _lv and _is_tvdb_hex32_key(_lv):
                                legacy_key = _lv
                    except Exception:
                        pass
                    # Last resort: built-in default
                    if not legacy_key:
                        _bik = (TVDB_LEGACY_DEFAULT_KEY or '').strip()
                        if _bik and _is_tvdb_hex32_key(_bik):
                            legacy_key = _bik

                if legacy_key:
                    poster_url = _tvdb_legacy_search(legacy_key, q, want='poster', prefer_langs=('de','en',''))

            # --- Web scrape fallback (no key needed) ---
            if not poster_url:
                poster_url = _tvdb_web_search_poster(q)
            if not poster_url:
                return False, "TVDb: Not found"
            if not poster_url:
                return False, "TVDb: Not found"
            if poster_url.rstrip('/').endswith('/banners'):
                return False, "TVDb: invalid poster url"

            # TVDB placeholder detection (legacy/v4/web)
            # Example: https://artworks.thetvdb.com/banners/images/missing/series.jpg
            try:
                _pu = (poster_url or "")
                if "/images/missing/" in _pu or _pu.endswith("/images/missing/series.jpg"):
                    return False, "TVDb: placeholder (missing) ignored"
            except Exception:
                pass


            self.dwn_poster = dwn_poster
            if getattr(self, "store_slug", None):
                self.slug = self.store_slug
            else:
                self.slug = get_store_slug(slug_title or title)

            self.savePoster(poster_url, dwn_poster)
            if not self.verifyPoster(dwn_poster):
                return False, "TVDb: poster invalid"
            try:
                self.resizePoster(dwn_poster)
            except Exception:
                pass

            try:
                slug = getattr(self, 'slug', '') or get_store_slug(slug_title or title)
                self.save_poster_info_json(slug, {
                    'title': title or q,
                    'source': 'tvdb',
                    'tvdb_id': tvdb_id,
                    'poster_url': poster_url,
                    'fetched_at': int(time.time())
                })
            except Exception:
                pass

            # Optional: validate/upgrade TVDb poster with a strong TMDb match to avoid wrong series posters
            # (keeps TVDb-first order but prefers TMDb when it is an almost-certain exact match).
            try:
                ok_tmdb, msg_tmdb = self.search_tmdb(dwn_poster, title, shortdesc, fulldesc, channel=channel, slug_title=slug_title)
                if ok_tmdb and "score=" in (msg_tmdb or ""):
                    try:
                        msc = re.search(r"score=(\\d+)", msg_tmdb)
                        scv = int(msc.group(1)) if msc else 0
                    except Exception:
                        scv = 0
                    if scv >= 98:
                        return True, msg_tmdb
            except Exception:
                pass

            return True, "[SUCCESS : tvdb] %s" % poster_url
        except Exception as e:
            return False, "TVDb error (%s)" % e


    def search_fanart(self, dwn_poster, title, shortdesc, fulldesc, channel=None, slug_title=None):
        ok_custom, msg_custom = self._try_custom_poster(dwn_poster, title, slug_title)
        if ok_custom:
            return True, msg_custom
        try:
            api_key = (fanart_api if 'fanart_api' in globals() else '').strip()
        except Exception:
            api_key = ''
        if not api_key:
            return False, "Fanart: key missing"
        return False, "Fanart: Not implemented"

    def search_imdb(self, dwn_poster, title, shortdesc, fulldesc, channel=None, slug_title=None):
        # CUSTOM override (never expires)
        ok_custom, msg_custom = self._try_custom_poster(dwn_poster, title, slug_title)
        if ok_custom:
            return True, msg_custom

        # IMDb direct override (no search) for known problematic titles
        try:
            ttid = get_imdb_id_override(title)
            if ttid:
                # IMDb blocks "bot-like" UAs quickly. Use a browser UA + language headers.
                headers = {
                    "User-Agent": getRandomUserAgent(),
                    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Connection": "close",
                }
                url_candidates = [
                    "https://www.imdb.com/de/title/%s/" % ttid,
                    "https://www.imdb.com/title/%s/" % ttid,
                    "https://m.imdb.com/title/%s/" % ttid,
                ]

                img_url = None
                last_status = None
                for url in url_candidates:
                    try:
                        r = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
                        last_status = r.status_code
                        if r.status_code != 200:
                            continue
                        html = r.text or ""

                        # Prefer OG image, fallback to twitter image
                        m = re.search(r'property="og:image"\s+content="([^"]+)"', html)
                        if not m:
                            m = re.search(r'name="twitter:image"\s+content="([^"]+)"', html)
                        if m:
                            img_url = m.group(1)
                            break

                        # JSON-LD fallback (rare)
                        m = re.search(r'"image"\s*:\s*\[\s*"([^"]+)"', html)
                        if m:
                            img_url = m.group(1)
                            break
                    except Exception:
                        continue

                if img_url:
                    ok = self.savePoster(img_url, dwn_poster)
                    if ok:
                        try:
                            self.save_poster_info_json(get_store_slug(title), {
                                "title": title,
                                "source": "imdb",
                                "imdb_id": ttid,
                                "poster_url": img_url,
                                "fetched_at": int(time.time()),
                            })
                        except Exception:
                            pass
                        return True, "[SUCCESS : imdb] %s" % img_url
                else:
                    # keep trace for debugging
                    return False, "[SKIP : imdb] %s (HTTP %s, og:image not found)" % (str(title), str(last_status))
        except Exception:
            pass

        """
        IMDb Poster Search (robust):
          1) Use IMDb Suggest JSON (stable, no HTML scraping)
          2) Fallback to mobile HTML find (best effort)
        """
        try:
            self.dwn_poster = dwn_poster
            url_poster = None
            chkType, fd = self.checkType(shortdesc, fulldesc)

            # Title normalization (keep original case; no sanitize_filename here!)
            raw_title = (title or "").replace("+", " ").strip()
            self.title_safe = raw_title

            # Try to extract AKA from description (optional)
            aka = None
            try:
                aka_m = re.findall(r'\(([^)]{2,80})\)', fd or "")
                for a in aka_m:
                    if a and not str(a).isdigit():
                        aka = a
                        break
            except Exception:
                aka = None

            # Extract year (optional)
            year = ''
            try:
                y = re.findall(r'19\d{2}|20\d{2}', fd or "")
                year = y[0] if y else ''
            except Exception:
                year = ''

            # Build candidate queries in deterministic order
            candidates = []
            for c in [raw_title, aka]:
                if c:
                    c = c.strip()
                    if c and c.lower() not in [x.lower() for x in candidates]:
                        candidates.append(c)

            # HTTP setup
            headers = {
                "User-Agent": getRandomUserAgent(),
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
            }
            cookies = {"CONSENT": "YES+"}

            retries = Retry(total=2, connect=2, read=2, backoff_factor=0.3,
                            status_forcelist=(429, 500, 502, 503, 504),
                            allowed_methods=("GET",))
            adapter = HTTPAdapter(max_retries=retries)
            http = requests.Session()
            http.mount("http://", adapter)
            http.mount("https://", adapter)

            def _normalize_imdb_image(url):
                if not url:
                    return url
                try:
                    # Remove size modifiers to get a higher-quality image when possible
                    url = url.replace("\\u0026", "&").replace("\\u003d", "=").replace("\\/", "/")
                    # Typical IMDb pattern: ...._V1_UX182_CR0,0,182,268_AL_.jpg -> ...._V1_.jpg
                    url = re.sub(r'\._V1_.*?(\.(?:jpg|jpeg|png|webp))(?:\?.*)?$', r'._V1_\1', url, flags=re.IGNORECASE)
                except Exception:
                    pass
                return url

            def _imdb_suggest_best(query):
                """
                Returns dict {id, title, year, img} or None
                """
                q = (query or "").strip()
                if not q:
                    return None
                # Suggest endpoint requires first letter
                first = q[0].lower()
                if not first.isalpha():
                    first = "a"
                q_enc = quoteEventName(q).replace("%20", "%20")
                endpoints = [
                    "https://v3.sg.media-imdb.com/suggestion/{}/{}.json".format(first, q_enc),
                    "https://v2.sg.media-imdb.com/suggestion/{}/{}.json".format(first, q_enc),
                ]
                best = None
                best_score = -1.0
                for ep in endpoints:
                    try:
                        r = http.get(ep, headers=headers, cookies=cookies, timeout=(6, 12))
                        if r.status_code != 200:
                            continue
                        js = r.json()
                        items = js.get("d") or []
                        for it in items:
                            try:
                                imdb_id = it.get("id") or ""
                                it_title = it.get("l") or ""
                                it_year = it.get("y")
                                it_img = None
                                if isinstance(it.get("i"), dict):
                                    it_img = it["i"].get("imageUrl")
                                elif isinstance(it.get("i"), (list, tuple)) and it.get("i"):
                                    # very old format
                                    it_img = it["i"][0]
                                # Type hint (optional)
                                it_q = (it.get("q") or "").lower()

                                # Score with PMATCH (0..1)
                                score = self.PMATCH(it_title, q)
                                # slight bias to series when we detect tv-like type
                                if chkType.startswith("tv") and ("tv series" in it_q or "tv mini-series" in it_q):
                                    score += 0.05
                                if chkType.startswith("movie") and ("feature" in it_q or "movie" in it_q):
                                    score += 0.03
                                # Year bias if available
                                if year and it_year and str(it_year) == str(year):
                                    score += 0.03

                                if score > best_score and imdb_id.startswith("tt"):
                                    best_score = score
                                    best = {"id": imdb_id, "title": it_title, "year": it_year, "img": it_img}
                            except Exception:
                                continue
                    except Exception:
                        continue

                # Minimal threshold to avoid wrong matches
                if best and best_score >= 0.55:
                    return best
                return None

            # 1) Suggest JSON first
            for cand in candidates:
                best = _imdb_suggest_best(cand)
                if best and best.get("img"):
                    url_poster = _normalize_imdb_image(best.get("img"))
                    if url_poster:
                        self.savePoster(url_poster, dwn_poster)
                        if self.verifyPoster(dwn_poster):
                            self.sizeb = True
                            self.resizePoster(dwn_poster)
                            try:
                                slug = get_canonical_slug(title)
                                self.save_poster_info_json(slug, {
                                    "title": title,
                                    "source": "imdb",
                                    "imdb_id": best.get("id"),
                                    "poster_url": url_poster,
                                    "fetched_at": int(time.time()),
                                    "method": "suggest"
                                })
                            except Exception:
                                pass
                            return True, "[SUCCESS poster: imdb] {} [{}-{}] => {} (suggest {})".format(self.title_safe, chkType, year, url_poster, best.get("id"))

            # 2) Fallback: mobile HTML find (best effort)
            # NOTE: HTML scraping is brittle; keep it as last resort inside IMDb stage.
            for cand in candidates:
                try:
                    url_mimdb = "https://m.imdb.com/find?q={}".format(quoteEventName(cand))
                    html = http.get(url_mimdb, headers=headers, cookies=cookies, timeout=(6, 12)).text

                    # Try to extract first sensible title + image
                    # Pattern tries to capture: tt-id + image src + title text
                    hits = re.findall(
                        r'href="/title/(tt\d+)/[^"]*".*?<img[^>]+src="([^"]+)".*?>.*?<span[^>]*>([^<]{2,120})</span>',
                        html, flags=re.S | re.I
                    )
                    if not hits:
                        # Older mobile layout fallback
                        hits = re.findall(
                            r'href="/title/(tt\d+)/[^"]*".*?<img[^>]+src="([^"]+)"[^>]*>.*?class="h3">\s*([^<]{2,120})\s*<',
                            html, flags=re.S | re.I
                        )

                    best_hit = None
                    best_score = -1.0
                    for tt, img, ttl in hits:
                        score = self.PMATCH(ttl, cand)
                        if score > best_score:
                            best_score = score
                            best_hit = (tt, img, ttl)

                    if best_hit and best_score >= 0.55:
                        tt, img, ttl = best_hit
                        url_poster = _normalize_imdb_image(img)
                        if url_poster:
                            self.savePoster(url_poster, dwn_poster)
                            if self.verifyPoster(dwn_poster):
                                self.sizeb = True
                                self.resizePoster(dwn_poster)
                                try:
                                    slug = get_canonical_slug(title)
                                    self.save_poster_info_json(slug, {
                                        "title": title,
                                        "source": "imdb",
                                        "imdb_id": tt,
                                        "poster_url": url_poster,
                                        "fetched_at": int(time.time()),
                                        "method": "html"
                                    })
                                except Exception:
                                    pass
                                return True, "[SUCCESS poster: imdb] {} [{}-{}] => {} (html {})".format(self.title_safe, chkType, year, url_poster, tt)
                except Exception:
                    continue

            return False, "[SKIP : imdb] {} [{}-{}] => (No Entry found)".format(self.title_safe, chkType, year)

        except Exception as e:
            if os.path.exists(dwn_poster):
                try:
                    os.remove(dwn_poster)
                except Exception:
                    pass
            return False, "[ERROR : imdb] {} => ({})".format(getattr(self, "title_safe", title), str(e))


    def search_programmetv_google(self, dwn_poster, title, shortdesc, fulldesc, channel=None, slug_title=None):
        # CUSTOM override (never expires)
        ok_custom, msg_custom = self._try_custom_poster(dwn_poster, title, slug_title)
        if ok_custom:
            return True, msg_custom

        try:
            self.dwn_poster = dwn_poster
            url_ptv = ''
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
            chkType, fd = self.checkType(shortdesc, fulldesc)
            if chkType.startswith("movie"):
                return False, "[SKIP : programmetv-google] {} [{}] => Skip movie title".format(title, chkType)
            title_safe = title
            # title_safe = self.UNAC(title)
            # title_safe = quoteEventName(title_safe)
            self.title_safe = title_safe.replace('+', ' ')
            # Für IMDb: Original-Schreibweise beibehalten, nur URL-encode
            # self.title_safe = sanitize_filename(self.title_safe)  # REMOVED: macht lowercase!
            url_ptv = "site:programme-tv.net+" + self.title_safe
            if channel and self.title_safe.find(channel.split()[0]) < 0:
                url_ptv += "+" + quoteEventName(channel)
            url_ptv = "https://www.google.com/search?q={}&tbm=isch&tbs=ift:jpg%2Cisz:m".format(url_ptv)
            ff = requests.get(url_ptv, stream=True, headers=headers, cookies={'CONSENT': 'YES+'}).text
            if not PY3:
                ff = ff.encode('utf-8')
            ptv_id = 0
            plst = re.findall(r'\],\["https://www.programme-tv.net(.*?)",\d+,\d+]', ff)
            for posterlst in plst:
                self.sizeb = False
                ptv_id += 1
                url_poster = "https://www.programme-tv.net{}".format(posterlst)
                url_poster = re.sub(r"\\u003d", "=", url_poster)
                url_poster_size = re.findall(r'([\d]+)x([\d]+).*?([\w\.-]+).jpg', url_poster)
                if url_poster_size and url_poster_size[0]:
                    get_title = self.UNAC(url_poster_size[0][2].replace('-', ''))
                    if self.title_safe == get_title:
                        h_ori = float(url_poster_size[0][1])
                        h_tar = float(re.findall(r'(\d+)', isz)[1])
                        ratio = h_ori / h_tar
                        w_ori = float(url_poster_size[0][0])
                        w_tar = w_ori / ratio
                        w_tar = int(w_tar)
                        h_tar = int(h_tar)
                        url_poster = re.sub(r'/\d+x\d+/', "/" + str(w_tar) + "x" + str(h_tar) + "/", url_poster)
                        url_poster = re.sub(r'crop-from/top/', '', url_poster)
                        self.savePoster(url_poster, self.dwn_poster)
                        # self.savePoster(dwn_poster, url_poster)
                        if os.path.exists(dwn_poster):
                            if self.verifyPoster(dwn_poster):
                                self.resizePoster(dwn_poster)
                            # poster
                            self.pstrNm = path_folder + '/' + sanitize_filename_safe(get_canonical_slug(self.title_safe)) + ".jpg"
                            dwn_poster = str(self.pstrNm)
                            self.savePoster(url_poster, dwn_poster)
                            # self.savePoster(dwn_poster, url_poster)
                            self.sizeb = True
                            self.resizePoster(dwn_poster)
                            try:
                                slug = get_canonical_slug(title)
                                self.save_poster_info_json(slug, {
                                    'title': title,
                                    'source': 'programmetv',
                                    'poster_url': url_poster,
                                    'fetched_at': int(time.time())
                                })
                            except Exception:
                                pass
                            return True, "[SUCCESS url_poster: programmetv-google] {} [{}] => Found self.title_safe : '{}' => {} => {} (initial size: {}) [{}]".format(self.title_safe, chkType, get_title, url_ptv, url_poster, url_poster_size, ptv_id)
                return False, "[SKIP : programmetv-google] {} [{}] => Not found [{}] => {}".format(self.title_safe, chkType, ptv_id, url_ptv)

        except Exception as e:
            if os.path.exists(dwn_poster):
                os.remove(dwn_poster)
            return False, "[ERROR : programmetv-google] {} [{}] => {} ({})".format(self.title_safe, chkType, url_ptv, str(e))

    def search_molotov_google(self, dwn_poster, title, shortdesc, fulldesc, channel=None, slug_title=None):
        # CUSTOM override (never expires)
        ok_custom, msg_custom = self._try_custom_poster(dwn_poster, title, slug_title)
        if ok_custom:
            return True, msg_custom

        try:
            self.dwn_poster = dwn_poster
            url_mgoo = ''
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
            chkType, fd = self.checkType(shortdesc, fulldesc)
            title_safe = title
            # title_safe = self.UNAC(title)
            # title_safe = quoteEventName(title_safe)
            self.title_safe = title_safe.replace('+', ' ')
            # Für IMDb: Original-Schreibweise beibehalten, nur URL-encode
            # self.title_safe = sanitize_filename(self.title_safe)  # REMOVED: macht lowercase!
            if channel:
                pchannel = self.UNAC(channel).replace(' ', '')
            else:
                pchannel = ''
            poster = None
            pltc = None
            imsg = ''
            url_mgoo = "site:molotov.tv+" + self.title_safe
            if channel and self.title_safe.find(channel.split()[0]) < 0:
                url_mgoo += "+" + quoteEventName(channel)
            url_mgoo = "https://www.google.com/search?q={}&tbm=isch".format(url_mgoo)
            ff = requests.get(url_mgoo, stream=True, headers=headers, cookies={'CONSENT': 'YES+'}).text
            if not PY3:
                ff = ff.encode('utf-8')
            plst = re.findall(r'https://www.molotov.tv/(.*?)"(?:.*?)?"(.*?)"', ff)
            len_plst = len(plst)
            molotov_id = 0
            molotov_table = [0, 0, None, None, 0]
            partialtitle = 0
            partialchannel = 0
            for pl in plst:
                get_path = "https://www.molotov.tv/" + pl[0]
                get_name = self.UNAC(pl[1])
                get_title = re.findall(r'(.*?)[ ]+en[ ]+streaming', get_name)
                if get_title:
                    get_title = get_title[0]
                else:
                    get_title = None
                get_channel = re.findall(r'(?:streaming|replay)?[ ]+sur[ ]+(.*?)[ ]+molotov.tv', get_name)
                if get_channel:
                    get_channel = self.UNAC(get_channel[0]).replace(' ', '')
                else:
                    get_channel = re.findall(r'regarder[ ]+(.*?)[ ]+en', get_name)
                    if get_channel:
                        get_channel = self.UNAC(get_channel[0]).replace(' ', '')
                    else:
                        get_channel = None
                partialchannel = self.PMATCH(pchannel, get_channel)
                partialtitle = self.PMATCH(self.title_safe, get_title)
                if partialtitle > molotov_table[0]:
                    molotov_table = [partialtitle, partialchannel, get_name, get_path, molotov_id]
                if partialtitle == 100 and partialchannel == 100:
                    break
                molotov_id += 1

            if molotov_table[0]:
                ffm = requests.get(molotov_table[3], stream=True, headers=headers).text
                if not PY3:
                    ffm = ffm.encode('utf-8')
                pltt = re.findall(r'"https://fusion.molotov.tv/(.*?)/jpg" alt="(.*?)"', ffm)
                if len(pltt) > 0:
                    pltc = self.UNAC(pltt[0][1])
                    plst = "https://fusion.molotov.tv/" + pltt[0][0] + "/jpg"
                    imsg = "Found title ({}%) & channel ({}%) : '{}' + '{}' [{}/{}]".format(molotov_table[0], molotov_table[1], molotov_table[2], pltc, molotov_table[4], len_plst)
            else:
                plst = re.findall(r'\],\["https://(.*?)",\d+,\d+].*?"https://.*?","(.*?)"', ff)
                len_plst = len(plst)
                if len_plst > 0:
                    for pl in plst:
                        if pl[1].startswith("Regarder"):
                            pltc = self.UNAC(pl[1])
                            partialtitle = self.PMATCH(self.title_safe, pltc)
                            get_channel = re.findall(r'regarder[ ]+(.*?)[ ]+en', pltc)
                            if get_channel:
                                get_channel = self.UNAC(get_channel[0]).replace(' ', '')
                            else:
                                get_channel = None
                            partialchannel = self.PMATCH(pchannel, get_channel)
                            if partialchannel > 0 and partialtitle < 50:
                                partialtitle = 50
                            plst = "https://" + pl[0]
                            molotov_table = [partialtitle, partialchannel, pltc, plst, -1]
                            imsg = "Fallback title ({}%) & channel ({}%) : '{}' [{}/{}]".format(molotov_table[0], molotov_table[1], pltc, -1, len_plst)
                            break

            if molotov_table[0] == 100 and molotov_table[1] == 100:
                poster = plst
            elif chkType.startswith("movie"):
                imsg = "Skip movie type '{}' [{}%-{}%-{}]".format(pltc, molotov_table[0], molotov_table[1], len_plst)
            elif molotov_table[0] == 100:
                poster = plst
            elif molotov_table[0] >= 50 and molotov_table[1]:
                poster = plst
            elif molotov_table[0] >= 75:
                poster = plst
            elif chkType == '':
                imsg = "Skip unknown type '{}' [{}%-{}%-{}]".format(pltc, molotov_table[0], molotov_table[1], len_plst)
            elif molotov_table[0] >= 25 and molotov_table[1]:
                poster = plst
            elif molotov_table[0] >= 50:
                poster = plst
            else:
                imsg = "Not found '{}' [{}%-{}%-{}]".format(pltc, molotov_table[0], molotov_table[1], len_plst)
            if poster:
                self.sizeb = False
                url_poster = re.sub(r'/\d+x\d+/', "/" + re.sub(r', ', 'x', isz) + "/", poster)
                self.savePoster(poster, dwn_poster)
                # self.savePoster(dwn_poster, url_poster)
                if os.path.exists(dwn_poster):
                    if self.verifyPoster(dwn_poster):
                        self.resizePoster(dwn_poster)
                    # poster
                    self.pstrNm = path_folder + '/' + sanitize_filename_safe(get_canonical_slug(self.title_safe)) + ".jpg"
                    dwn_poster = str(self.pstrNm)
                    url_poster = re.sub(r'/\d+x\d+/', "/" + re.sub(r', ', 'x', bisz) + "/", poster)
                    self.savePoster(poster, dwn_poster)
                    # self.savePoster(dwn_poster, url_poster)
                    if os.path.exists(dwn_poster):
                        if self.verifyPoster(dwn_poster):
                            self.sizeb = True
                            self.resizePoster(dwn_poster)
                    try:
                        slug = get_canonical_slug(title)
                        self.save_poster_info_json(slug, {
                            'title': title,
                            'source': 'molotov',
                            'poster_url': url_poster,
                            'fetched_at': int(time.time())
                        })
                    except Exception:
                        pass
                    return True, "[SUCCESS url_poster: molotov-google] {} ({}) [{}] => {} => {} => {}".format(self.title_safe, channel, chkType, imsg, url_mgoo, url_poster)
                return False, "[SKIP : molotov-google] {} ({}) [{}] => {} => {} => {} (jpeg error)".format(self.title_safe, channel, chkType, imsg, url_mgoo, url_poster)
        except Exception as e:
            if os.path.exists(dwn_poster):
                os.remove(dwn_poster)
            return False, "[ERROR : molotov-google] {} [{}] => {} ({})".format(self.title_safe, chkType, url_mgoo, str(e))

    def search_google(self, dwn_poster, title, shortdesc, fulldesc, channel=None, slug_title=None):
        # CUSTOM override (never expires)
        ok_custom, msg_custom = self._try_custom_poster(dwn_poster, title, slug_title)
        if ok_custom:
            return True, msg_custom
        # v17: Google is opt-in only (prevents many wrong posters)
        if not _allow_google():
            return False, "Google: disabled (opt-in)"


        """
        Google Images Poster Search (last resort, robust):
        - Always uses CONSENT cookie (EU)
        - Avoids overly strict filters (jpg/medium) that often kill results
        - Tries multiple query variants in-order
        """
        try:
            self.dwn_poster = dwn_poster
            chkType, fd = self.checkType(shortdesc, fulldesc)

            raw_title = (title or "").replace("+", " ").strip()
            self.title_safe = raw_title

            # Optional year hint
            year = None
            try:
                y = re.findall(r'19\d{2}|20\d{2}', fd or "")
                year = y[0] if y else None
            except Exception:
                year = None

            # Type hint from chkType
            srch = None
            try:
                if chkType.startswith("movie"):
                    srch = chkType[6:]
                elif chkType.startswith("tv"):
                    srch = chkType[3:]
            except Exception:
                srch = None

            headers = {
                "User-Agent": getRandomUserAgent(),
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            cookies = {"CONSENT": "YES+"}

            retries = Retry(total=2, connect=2, read=2, backoff_factor=0.3,
                            status_forcelist=(429, 500, 502, 503, 504),
                            allowed_methods=("GET",))
            adapter = HTTPAdapter(max_retries=retries)
            http = requests.Session()
            http.mount("http://", adapter)
            http.mount("https://", adapter)

            def _decode_url(u):
                if not u:
                    return u
                try:
                    u = u.replace("\\u0026", "&").replace("\\u003d", "=").replace("\\/", "/")
                except Exception:
                    pass
                return u

            # Build query variants (keep order, unique)
            qlist = []
            base = raw_title
            if base:
                qlist.append('"{}" poster'.format(base))
                qlist.append('{} poster'.format(base))
            if channel and base and channel not in base:
                qlist.append('{} {} poster'.format(base, channel))
            if srch and base:
                qlist.append('{} {} poster'.format(base, srch))
            if year and base:
                qlist.append('{} {} poster'.format(base, year))
            # Small helper: imdb keyword (helps for some shows)
            if base:
                qlist.append('{} imdb poster'.format(base))

            # De-duplicate preserving order
            seen = set()
            queries = []
            for q in qlist:
                k = q.lower().strip()
                if k and k not in seen:
                    seen.add(k)
                    queries.append(q)

            found = False
            url_google_used = ""
            url_poster = ""

            def _extract_image_urls(html):
                urls = []
                if not html:
                    return urls
                # Variant A: legacy array format
                urls.extend(['https://%s' % x for x in re.findall(r'\],\["https?://(.*?)",\d+,\d+]', html)])
                # Variant B: "ou":"https://..."
                urls.extend(re.findall(r'"ou":"(https?://[^"]+)"', html))
                # Variant C: direct googleusercontent/gstatic URLs inside JSON blobs
                urls.extend(re.findall(r'(https?://[^"\\\s]+(?:gstatic|googleusercontent)[^"\\\s]+)', html))
                # Normalize & filter
                out = []
                seen_u = set()
                for u in urls:
                    u = _decode_url(u)
                    if not u:
                        continue
                    if u.startswith("data:"):
                        continue
                    # skip obvious thumbnails when better exists
                    if "encrypted-tbn0.gstatic.com/images" in u and len(u) < 120:
                        continue
                    if u not in seen_u:
                        seen_u.add(u)
                        out.append(u)
                return out

            for q in queries:
                try:
                    url_google = "https://www.google.com/search?q={}&tbm=isch&tbs=sbd:0".format(quoteEventName(q))
                    url_google_used = url_google
                    html = http.get(url_google, headers=headers, cookies=cookies, timeout=(6, 12)).text
                    posterlst = _extract_image_urls(html)
                    if not posterlst:
                        continue

                    for u in posterlst[:30]:
                        self.sizeb = False
                        url_poster = u
                        self.savePoster(url_poster, dwn_poster)
                        if os.path.exists(dwn_poster) and self.verifyPoster(dwn_poster):
                            # Google liefert oft Backdrops/landscape – Poster muessen portrait sein
                            if not _is_portrait(dwn_poster):
                                _remove_silent(dwn_poster)
                                continue
                            self.resizePoster(dwn_poster)
                            found = True
                            break
                        else:
                            _remove_silent(dwn_poster)
                    if found:
                        break
                except Exception:
                    continue

            if found:
                try:
                    slug = get_canonical_slug(title)
                    self.save_poster_info_json(slug, {
                        "title": title,
                        "source": "google",
                        "poster_url": url_poster,
                        "fetched_at": int(time.time()),
                        "query_url": url_google_used
                    })
                except Exception:
                    pass
                return True, "[SUCCESS poster: google] {} [{}-{}] => {}".format(self.title_safe, chkType, year, url_poster)

            # Google is the last provider in PosterDB -> create a small negative cache json
            try:
                slug = get_canonical_slug(title)
                self.save_poster_info_json(slug, {
                    "title": title,
                    "source": None,
                    "poster_url": None,
                    "status": "not_found",
                    "last_provider": "google",
                    "fetched_at": int(time.time()),
                })
            except Exception:
                pass

            return False, "[SKIP : google] {} [{}-{}] => {} (Not found)".format(self.title_safe, chkType, year, url_google_used)

        except Exception as e:
            if os.path.exists(dwn_poster):
                try:
                    os.remove(dwn_poster)
                except Exception:
                    pass
            return False, "[ERROR : google] {} => ({})".format(getattr(self, "title_safe", title), str(e))


    def savePoster(self, url, callback):
###         print('000000000URLLLLL=', url)
###         print('000000000CALLBACK=', callback)
        import io
        AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
                  "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
                  "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
                  "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)",
                  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edge/87.0.664.75",
                  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363"]
        headers = {"User-Agent": choice(AGENTS)}
        try:
            response = get(url.encode(), headers=headers, timeout=(3.05, 6))
            response.raise_for_status()

            try:
                os.makedirs(os.path.dirname(callback), exist_ok=True)
            except Exception:
                pass

            img = Image.open(io.BytesIO(response.content or b''))
            try:
                img = img.convert('RGB')
            except Exception:
                pass

            width, height = img.size
            if width and height:
                scale = min(float(MAX_POSTER_W) / float(width), float(MAX_POSTER_H) / float(height), 1.0)
                new_width = max(1, int(round(width * scale)))
                new_height = max(1, int(round(height * scale)))
                if new_width != width or new_height != height:
                    rimg = img.resize((new_width, new_height), ANTIALIAS)
                    try:
                        img.close()
                    except Exception:
                        pass
                    img = rimg

            img.save(callback, format='JPEG', quality=90, optimize=True)
            try:
                img.close()
            except Exception:
                pass
            if _image_too_large(callback):
                _remove_silent(callback)

        except exceptions.RequestException as error:
            try:
                l = globals().get('logger', None)
                if l:
                    l.debug("download failed: %s", str(error))
            except Exception:
                pass
        except Exception:
            pass
        return callback

    def resizePoster(self, dwn_poster):
        try:
            target = bisz if self.sizeb else isz
            self.sizeb = False

            max_w, max_h = [int(x) for x in target.split(",")]
            img = Image.open(dwn_poster)
            try:
                # Normalize orientation but keep portrait posters portrait.
                try:
                    img = img.convert("RGB")
                except Exception:
                    pass

                width, height = img.size
                if not width or not height:
                    img.close()
                    return

                # Never upscale tiny files; only shrink when larger than target box.
                scale = min(float(max_w) / float(width), float(max_h) / float(height), 1.0)
                new_width = max(1, int(round(width * scale)))
                new_height = max(1, int(round(height * scale)))

                if new_width == width and new_height == height:
                    img.save(dwn_poster, format="JPEG", quality=90, optimize=True)
                else:
                    rimg = img.resize((new_width, new_height), ANTIALIAS)
                    try:
                        rimg.save(dwn_poster, format="JPEG", quality=90, optimize=True)
                    finally:
                        try:
                            rimg.close()
                        except Exception:
                            pass
            finally:
                try:
                    img.close()
                except Exception:
                    pass
        except Exception:
            pass


    def verifyPoster(self, posterfile):
        """Validate poster file exists, decodes, and is portrait-ish."""
        try:
            if not posterfile or not os.path.exists(posterfile):
                return False
            if os.path.getsize(posterfile) < 1024:
                return False
            if _image_too_large(posterfile):
                _remove_silent(posterfile)
                return False
            try:
                from PIL import Image, ImageFile
            except Exception:
                return True
            try:
                im = Image.open(posterfile)
                im.verify()
            except Exception:
                return False
            try:
                im = Image.open(posterfile)
                w, h = im.size
                if not w or not h:
                    return False
                if float(h) / float(w) < 1.05:
                    return False
            except Exception:
                pass
            return True
        except Exception:
            return False

    def checkType(self, shortdesc, fulldesc):
        if shortdesc and shortdesc != '':
            fd = shortdesc.splitlines()[0]
        elif fulldesc and fulldesc != '':
            fd = fulldesc.splitlines()[0]
        else:
            fd = ''
        global srch
        srch = "multi"
        return srch, fd

    def UNAC(self, string):
        string = html.unescape(string)
        string = unicodedata.normalize('NFD', string)
        string = re.sub(r"u0026", "&", string)
        string = re.sub(r"u003d", "=", string)
        string = re.sub(r'[\u0300-\u036f]', '', string)
        string = re.sub(r"[,!?\.\"]", ' ', string)
        # string = re.sub(r"[-/:']", '', string)
        # string = re.sub(r"[^a-zA-Z0-9 ]", "", string)
        # string = string.lower()
        string = re.sub(r'\s+', ' ', string)
        string = string.strip()
        return string

    def search_omdb(self, dwn_poster, title, shortdesc, fulldesc, channel=None, slug_title=None):
        # CUSTOM override (never expires)
        ok_custom, msg_custom = self._try_custom_poster(dwn_poster, title, slug_title)
        if ok_custom:
            return True, msg_custom

        try:
            self.dwn_poster = dwn_poster
            title_safe = title.replace('+', ' ')
            if not omdb_api:
                return False, "[SKIP : omdb missing key]"
            url = f"http://www.omdbapi.com/?apikey={omdb_api}&t={title_safe}"
            headers = {'User-Agent': getRandomUserAgent()}
            response = requests.get(url, headers=headers, timeout=(3.05, 6))
            response.raise_for_status()
            if response.status_code == requests.codes.ok:
                data = response.json()
                if 'Poster' in data and data['Poster'] != 'N/A':
                    poster_url = data['Poster']
                    self.savePoster(poster_url, self.dwn_poster)
                    if DEBUG_POSTER:
                        print("OMDb poster queued:", poster_url)
                    return True, f"[SUCCESS poster: omdb] title {title_safe} => {poster_url}"
                else:
                    return False, f"[SKIP : omdb] {title_safe} => Poster not found"
            else:
                return False, f"Errore durante la ricerca su OMDB: {response.status_code}"
        except Exception as e:
            if DEBUG_POSTER:
                print('Errore nella ricerca OMDB:', e)
            return False, "Errore durante la ricerca su OMDB"





    # ------------------------------------------------------------------
    # Provider order preference by media type
    #   - Movies: prefer TMDb before TVDb
    #   - Series: prefer TVDb before TMDb
    # ------------------------------------------------------------------
    def _get_media_hint(self, title, shortdesc, fulldesc):
        """Try to infer media_type (movie/tv) for provider ordering.

        Priority:
          1) existing /media/hdd/xtra/Info/<slug>.json (if available)
          2) EPG text heuristics (Film/Spielfilm vs Staffel/Folge/Episode)
        """
        try:
            slug = get_store_slug(title)
            p = os.path.join(info_folder, slug + '.json')
            if os.path.exists(p):
                try:
                    data = json.load(open(p, 'r'))
                    mt = data.get('media_type')
                    if mt in ('movie', 'tv'):
                        return mt
                except Exception:
                    pass
        except Exception:
            pass

        blob = ' '.join([str(shortdesc or ''), str(fulldesc or '')]).lower()
        try:
            if re.search(r'\\b(staffel|folge|episode|episoden)\\b', blob, re.I):
                return 'tv'
            if re.search(r'\\b(film|spielfilm|kino|movie)\\b', blob, re.I):
                return 'movie'
        except Exception:
            pass
        return None

    def _reorder_providers_for_media(self, providers, media_hint):
        """Reorder provider list depending on inferred media_type."""
        if not providers:
            return providers
        try:
            providers = list(providers)
        except Exception:
            return providers

        # do not touch explicit overrides like IMDb-only lists
        if len(providers) <= 1:
            return providers

        # only reorder if both are present
        if 'tmdb' in providers and 'tvdb' in providers:
            if media_hint == 'movie':
                # tmdb first
                providers = [p for p in providers if p not in ('tmdb','tvdb')]
                providers = ['tmdb','tvdb'] + providers
            elif media_hint == 'tv':
                # tvdb first
                providers = [p for p in providers if p not in ('tmdb','tvdb')]
                providers = ['tvdb','tmdb'] + providers
        return providers
    def downloadData(self, canal, base, title, shortdesc, fulldesc, dwn_poster):
        """Main entry point called by GradientFHDPosterX.py.

        Enforces:
          - canonical slug filenames (via GradientFHDPosterX.py -> get_store_slug)
          - provider overrides (e.g. Punkt 6/7/8 => IMDb only)
          - episode grouping (e.g. Ultimate Rush parts => one image)
          - skip filler EPG titles (Sendepause, Programmende, ...)
        """
        try:
            raw_title = title or ""
            base_title = _strip_episode_tokens(raw_title)

            # Skip filler titles
            if base_title and base_title.strip().lower() in SKIP_TITLES:
                try:
                    self.logAutoDB("[SKIP : title] %s (filler)" % base_title)
                except Exception:
                    pass
                return False, "[SKIP : title] filler"

            # Ensure we always operate on base title (no episode tokens)
            title = base_title
            try:
                self.store_slug = get_store_slug(title)
            except Exception:
                pass
            if getattr(self, 'store_slug', '') == 'unknown':
                return False, "[SKIP : slug] unknown"

            # Try to reuse existing cached poster (poster_info / Info)
            try:
                if load_poster_from_json(title, dwn_poster, dwn_poster):
                    return True, "[CACHE : poster] %s" % title
            except Exception:
                pass

            providers = get_provider_override(title)

            # v17: Google opt-in only
            try:
                if 'google' in providers and not _allow_google():
                    providers = [p for p in providers if p != 'google']
            except Exception:
                pass

            # media-type based provider preference

            try:

                media_hint = self._get_media_hint(title, shortdesc, fulldesc)

                providers = self._reorder_providers_for_media(providers, media_hint)

            except Exception:

                pass

            # Provider loop
            for p in providers:
                try:
                    if p == "tmdb":
                        ok, msg = self.search_tmdb(dwn_poster, title, shortdesc, fulldesc, canal)
                    elif p == "tvdb":
                        ok, msg = self.search_tvdb(dwn_poster, title, shortdesc, fulldesc, canal)
                    elif p == "fanart":
                        ok, msg = self.search_fanart(dwn_poster, title, shortdesc, fulldesc, canal)
                    elif p == "imdb":
                        ok, msg = self.search_imdb(dwn_poster, title, shortdesc, fulldesc, canal)
                    elif p == "google":
                        ok, msg = self.search_google(dwn_poster, title, shortdesc, fulldesc, canal)
                    elif p == "omdb":
                        ok, msg = self.search_omdb(dwn_poster, title, shortdesc, fulldesc, canal)
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
        import re as _re
        if not textA or not textB:
            return 0
        def norm(s):
            s = '' if s is None else str(s)
            s = self.UNAC(s.lower())
            return _re.sub(r'[^a-z0-9]', '', s)
        a=norm(textA); b=norm(textB)
        if not a or not b:
            return 0
        if a==b:
            return 100
        import difflib
        return int(difflib.SequenceMatcher(None,a,b).ratio()*100)
