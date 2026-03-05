#!/usr/bin/python
# -*- coding: utf-8 -*-
# 02.26 @stein17, Many new features and improvements
"""
OPTIMIERTE GradientPosterXEMC.py
Fuer GradientFHD Skin

Fuer EMC (Enhanced Movie Center), Movie Player, Movieliste
Zeigt Poster fuer Aufnahmen (.ts, .mkv, .mp4, .avi, etc.)

NEUE FEATURES:
1. TITLE_MAPPINGS fuer deutsche Sendungen
2. Verbesserte Titelextraktion aus Dateinamen
3. JSON-Speicherung fuer Rating/FSK (GradientStarX/GradientParental)
4. Robustere Fehlerbehandlung
5. Bessere Dateinamensbereinigung

SKIN.XML BEISPIELE:
<!-- EMC Selection -->
<widget source="Service" render="GradientPosterXEMC" position="825,506" size="110,164" zPosition="4" alphatest="blend" />

<!-- Movie Player -->
<widget source="session.CurrentService" render="GradientPosterXEMC" position="10,325" size="170,255" zPosition="4" alphatest="blend" />

<!-- Movieliste -->
<widget source="ServiceEvent" render="GradientPosterXEMC" position="750,385" size="170,255" zPosition="4" alphatest="blend" />
"""

from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, eTimer, loadJPG, eEPGCache
from ServiceReference import ServiceReference
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.CurrentService import CurrentService
from Components.Sources.EventInfo import EventInfo
from Components.Sources.Event import Event
from Components.config import config
import NavigationInstance
import os
import sys
import re
import unicodedata
import json
import time
import threading
import requests
from twisted.internet.reactor import callInThread

PY3 = sys.version_info[0] >= 3
if PY3:
    from urllib.parse import quote as urlquote
else:
    from urllib import quote as urlquote

try:
    from .GradientConverlibr import convtext, cutName
except:
    from GradientConverlibr import convtext, cutName

DEBUG_EMC = False
epgcache = eEPGCache.getInstance()


# -----------------------------------------------------------------------------
# EMC Cache-only Artwork (Poster/Backdrop/Banner)
#   - show artwork ONLY from <storage>/xtra/EMC/{poster,backdrop,banner}
#   - NEVER download and NEVER write next to recordings
#   - storage is resolved dynamically like MovieScanner
# -----------------------------------------------------------------------------

def _get_emc_cache_base():
    """Resolve EMC cache base path compatible with GradientMoviescanner."""
    try:
        base = config.plugins.GradientFHD.poster_storage_base.value
        if base == "AUTO":
            for candidate in ("/media/hdd", "/media/usb", "/media/mmc"):
                if os.path.isdir(candidate):
                    base = candidate
                    break
            else:
                base = "/media/hdd"
    except Exception:
        base = "/media/hdd"
    return os.path.join(base, "xtra", "EMC")


EMC_BASE = _get_emc_cache_base()
EMC_POSTER_FOLDER = os.path.join(EMC_BASE, "poster")
EMC_BACKDROP_FOLDER = os.path.join(EMC_BASE, "backdrop")
EMC_BANNER_FOLDER = os.path.join(EMC_BASE, "banner")

for _d in (EMC_BASE, EMC_POSTER_FOLDER, EMC_BACKDROP_FOLDER, EMC_BANNER_FOLDER):
    try:
        if not os.path.exists(_d):
            os.makedirs(_d, exist_ok=True)
    except Exception:
        pass

PATHS_LOG = "/tmp/GradientFHD_paths.log"

def _log_active_paths_once():
    try:
        with open(PATHS_LOG, "a+", encoding="utf-8") as lf:
            lf.write("[%s] GradientPosterXEMC EMC_BASE=%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), EMC_BASE))
    except Exception:
        pass

_log_active_paths_once()

# Keep module-level helper variable names stable (cleanup/no-op for linters)
del _d

# folder index cache: {folder: {norm_key: fullpath}}
_EMC_INDEX = {}
_EMC_INDEX_MTIME = {}

def _emc_read_meta_title(media_path):
    """
    Enigma2 recording meta: <file>.ts.meta (or generally <file>.<ext>.meta)
    Title is usually on 2nd line.
    """
    try:
        meta_path = media_path + ".meta"
        if not os.path.exists(meta_path):
            return ""
        with open(meta_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.read().splitlines()
        if len(lines) >= 2:
            return (lines[1] or "").strip()
    except Exception:
        pass
    return ""

def _emc_extract_title_from_filename(path):
    try:
        base = os.path.basename(path)
        stem = os.path.splitext(base)[0]
        # common recording naming: "YYYYMMDD HHMM - CHANNEL - Title"
        if " - " in stem:
            stem = stem.split(" - ")[-1]
        stem = (stem or "").strip()
        # underscores are common in refs/titles -> treat like spaces
        stem = stem.replace("_", " ")
        stem = re.sub(r"\s+", " ", stem).strip()
        return stem
    except Exception:
        return ""


def _emc_expand_title_variants(title):
    """Generate robust title variants for cache matching (no manual per-title mapping)."""
    if not title:
        return []
    try:
        t = str(title).strip()
    except Exception:
        return []
    if not t:
        return []

    variants = []
    def add(x):
        if not x:
            return
        x = str(x).strip()
        if not x:
            return
        if x not in variants:
            variants.append(x)

    add(t)
    add(t.replace('_', ' '))
    add(re.sub(r"\s+", " ", t.replace('_', ' ')).strip())

    # Remove bracketed qualifiers: [Extended Cut], (Director's Cut), etc.
    t_nobr = re.sub(r"\[[^\]]+\]", " ", t)
    t_nobr = re.sub(r"\([^\)]*\)", " ", t_nobr)
    t_nobr = re.sub(r"\s+", " ", t_nobr).strip()
    add(t_nobr)

    # Split on common subtitle separators and add shorter base titles
    for sep in [" - ", " – ", " — ", ":", "|"]:
        if sep in t:
            base = t.split(sep, 1)[0].strip()
            add(base)
        if sep in t_nobr:
            base = t_nobr.split(sep, 1)[0].strip()
            add(base)

    # Remove common edition/quality tags
    tags_pat = r"\b(extended\s+cut|director.?s\s+cut|uncut|special\s+edition|remastered|ultimate\s+edition|\d{k}|uhd|hd)\b"
    t_notags = re.sub(tags_pat, " ", t_nobr, flags=re.IGNORECASE)
    t_notags = re.sub(r"\s+", " ", t_notags).strip()
    add(t_notags)

    return [v for v in variants if v]
def _emc_norm_key(s):
    """
    Normalize for matching:
      - case-insensitive
      - '_' treated as space
      - German umlauts normalized to ae/oe/ue and ß->ss
      - strip diacritics
      - keep a-z0-9 and spaces
    """
    if not s:
        return ""
    try:
        s = str(s).strip()
    except Exception:
        return ""
    if not s:
        return ""
    s = s.replace("\xc2\x86", "").replace("\xc2\x87", "")
    s = s.replace("Â\x86", "").replace("Â\x87", "")
    s = s.replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = s.casefold()
    # German transliterations (pre-diacritic stripping)
    s = s.replace("ß", "ss")
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    # strip remaining diacritics
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _special_series_id(series_title):
    """Known special series aliases where episode-title mapping is needed."""
    k = _emc_norm_key(series_title)
    if not k:
        return None
    if ('wir waren wie brueder' in k) or ('wir waren wie bruder' in k) or ('band of brothers' in k):
        return 'band_of_brothers'
    return None


def _special_episode_number(series_title, episode_title):
    """Map known localized episode titles to S01Exx (currently: Band of Brothers)."""
    sid = _special_series_id(series_title)
    if sid != 'band_of_brothers' or not episode_title:
        return None

    ek = _emc_norm_key(episode_title)
    if not ek:
        return None

    # German + English aliases
    table = {
        'currahee': 1,
        'der erste tag': 2,
        'day of days': 2,
        'brennpunkt normandie': 3,
        'carentan': 3,
        'die neuen': 4,
        'replacements': 4,
        'kreuzungen': 5,
        'crossroads': 5,
        'bastogne': 6,
        'durchbruch': 7,
        'the breaking point': 7,
        'der spezialauftrag': 8,
        'the last patrol': 8,
        'warum wir kaempfen': 9,
        'why we fight': 9,
        'kriegsende': 10,
        'points': 10,
    }

    best = None
    best_len = 0
    for raw, ep in table.items():
        rk = _emc_norm_key(raw)
        if not rk:
            continue
        if ek == rk or ek.startswith(rk) or rk.startswith(ek) or (rk in ek) or (ek in rk):
            if len(rk) > best_len:
                best = ep
                best_len = len(rk)
    return best


def _special_series_alias_titles(series_title):
    sid = _special_series_id(series_title)
    if sid == 'band_of_brothers':
        return ['Band of Brothers', 'Wir waren wie Brüder', 'Wir waren wie Brueder']
    return [series_title] if series_title else []


def _emc_build_index(folder):
    try:
        mtime = os.path.getmtime(folder)
    except Exception:
        return {}
    if _EMC_INDEX_MTIME.get(folder) == mtime and folder in _EMC_INDEX:
        return _EMC_INDEX[folder]
    idx = {}
    try:
        for fn in os.listdir(folder):
            if not fn.lower().endswith(".jpg"):
                continue
            stem = os.path.splitext(fn)[0]
            key = _emc_norm_key(stem)
            if key and key not in idx:
                idx[key] = os.path.join(folder, fn)
    except Exception:
        idx = {}
    _EMC_INDEX[folder] = idx
    _EMC_INDEX_MTIME[folder] = mtime
    return idx

def _emc_find_artwork(folder, titles):
    """Return best matching jpg path from folder for any of titles (cache-only)."""
    idx = _emc_build_index(folder)
    if not idx:
        return None

    best = None
    best_score = 10**9

    def consider(p, score):
        nonlocal best, best_score
        try:
            if not p or not os.path.exists(p) or os.path.getsize(p) <= 0:
                return
        except Exception:
            return
        if score < best_score:
            best = p
            best_score = score

    # 0) exact key match
    for t in titles or []:
        k = _emc_norm_key(t)
        if not k:
            continue
        p = idx.get(k)
        if p:
            consider(p, 0)

    if best:
        return best

    # 1) prefix both ways (handles "Titel 001" and "Titel Extended Cut")
    for t in titles or []:
        k = _emc_norm_key(t)
        if not k:
            continue
        for kk, p in idx.items():
            if kk.startswith(k) or k.startswith(kk):
                # score by length delta to prefer closest
                consider(p, 100 + abs(len(kk) - len(k)))

    if best:
        return best

    # 2) contains both ways (last resort but still limited to same folder)
    for t in titles or []:
        k = _emc_norm_key(t)
        if not k:
            continue
        for kk, p in idx.items():
            if (k in kk) or (kk in k):
                consider(p, 200 + abs(len(kk) - len(k)))

    return best
    # exact match pass
    for t in titles or []:
        k = _emc_norm_key(t)
        if not k:
            continue
        p = idx.get(k)
        if p and os.path.exists(p) and os.path.getsize(p) > 0:
            return p

    # prefix fallback (e.g. "Titel 001")
    for t in titles or []:
        k = _emc_norm_key(t)
        if not k:
            continue
        for kk, p in idx.items():
            if kk.startswith(k) and os.path.exists(p) and os.path.getsize(p) > 0:
                return p

    return None


try:
    lng = config.osd.language.value
    lng = lng[:-3]
except Exception:
    lng = 'de'

# API Keys
tmdb_api = '3c3efcf47c3577558812bb9d64019d65'
omdb_api = '6a4c9432'

# TITLE_MAPPINGS - Gleiche wie in GradientPosterXDownloadThread
TITLE_MAPPINGS = {
    # Daily Soaps
    'gzsz': 'Gute Zeiten, schlechte Zeiten',
    'gute zeiten schlechte zeiten': 'Gute Zeiten, schlechte Zeiten',
    'unter uns': 'Unter uns',
    'alles was zaehlt': 'Alles was zaehlt',
    'awz': 'Alles was zaehlt',
    'sturm der liebe': 'Sturm der Liebe',
    'rote rosen': 'Rote Rosen',
    'berlin tag und nacht': 'Berlin - Tag & Nacht',
    'koeln 50667': 'Koeln 50667',
    
    # Nachrichten
    'tagesschau': 'Tagesschau',
    'tagesthemen': 'Tagesthemen',
    'heute': 'heute',
    'heute journal': 'heute-journal',
    'heute-journal': 'heute-journal',
    'heute show': 'heute-show',
    'heute-show': 'heute-show',
    'rtl aktuell': 'RTL Aktuell',
    
    # Magazine
    'mittagsmagazin': 'Mittagsmagazin',
    'morgenmagazin': 'Morgenmagazin',
    'moma': 'Morgenmagazin',
    'brisant': 'Brisant',
    'explosiv': 'Explosiv - Das Magazin',
    'taff': 'taff',
    'galileo': 'Galileo',
    'stern tv': 'stern TV',
    
    # Talk Shows
    'maischberger': 'Maischberger',
    'anne will': 'Anne Will',
    'hart aber fair': 'hart aber fair',
    'markus lanz': 'Markus Lanz',
    'maybrit illner': 'Maybrit Illner',
    'ndr talk show': 'NDR Talk Show',
    
    # Quiz/Game Shows
    'wer wird millionaer': 'Wer wird Millionaer?',
    'wwm': 'Wer wird Millionaer?',
    'gefragt gejagt': 'Gefragt - Gejagt',
    'bares fuer rares': 'Bares fuer Rares',
    'die hoehle der loewen': 'Die Hoehle der Loewen',
    'das supertalent': 'Das Supertalent',
    'dsds': 'Deutschland sucht den Superstar',
    'the voice of germany': 'The Voice of Germany',
    'the masked singer': 'The Masked Singer',
    'schlag den star': 'Schlag den Star',
    
    # Krimis/Serien
    'tatort': 'Tatort',
    'polizeiruf 110': 'Polizeiruf 110',
    'der alte': 'Der Alte',
    'soko muenchen': 'SOKO Muenchen',
    'soko koeln': 'SOKO Koeln',
    'soko leipzig': 'SOKO Leipzig',
    'alarm fuer cobra 11': 'Alarm fuer Cobra 11 - Die Autobahnpolizei',
    'cobra 11': 'Alarm fuer Cobra 11 - Die Autobahnpolizei',
    'der bergdoktor': 'Der Bergdoktor',
    'die rosenheim cops': 'Die Rosenheim-Cops',
    'rosenheim cops': 'Die Rosenheim-Cops',
    'in aller freundschaft': 'In aller Freundschaft',
    'notruf hafenkante': 'Notruf Hafenkante',
    
    # Sport
    'sportschau': 'Sportschau',
    'sportstudio': 'das aktuelle sportstudio',
    'champions league': 'UEFA Champions League',
    'europa league': 'UEFA Europa League',
    'bundesliga': 'Bundesliga',
    'formel 1': 'Formula 1',
    'f1': 'Formula 1',
    
    # Dokus
    'terra x': 'Terra X',
    'planet erde': 'Planet Earth',
    'wildes deutschland': 'Wildes Deutschland',
    '37 grad': '37 Grad',
    
    # Reality
    'der bachelor': 'Der Bachelor',
    'die bachelorette': 'Die Bachelorette',
    'bauer sucht frau': 'Bauer sucht Frau',
    'dschungelcamp': "I'm a Celebrity...Get Me Out of Here!",
    'ich bin ein star': "I'm a Celebrity...Get Me Out of Here!",
    'das perfekte dinner': 'Das perfekte Dinner',
    
    # Kinder
    'die sendung mit der maus': 'Die Sendung mit der Maus',
    'loewenzahn': 'Loewenzahn',
    'peppa wutz': 'Peppa Pig',
    'paw patrol': 'PAW Patrol',
}

# Muster die aus Dateinamen entfernt werden sollen
FILENAME_JUNK = [
    r'_+', r'-+', r'\.+',
    r'\d{4}[-_]\d{2}[-_]\d{2}',  # Datum 2024-01-15
    r'\d{2}[-_]\d{2}[-_]\d{4}',  # Datum 15-01-2024
    r'\d{8}',                     # Datum 20240115
    r'\d{4}',                     # Jahr
    r'[Ss]\d{1,2}[Ee]\d{1,2}',   # S01E05
    r'[Ss]taffel\s*\d+',
    r'[Ee]pisode\s*\d+',
    r'[Ff]olge\s*\d+',
    r'[Tt]eil\s*\d+',
    r'1080[pi]', r'720[pi]', r'576[pi]', r'480[pi]',
    r'[Hh][Dd][Tt][Vv]', r'[Ww][Ee][Bb]', r'[Bb][Dd][Rr][Ii][Pp]',
    r'[Xx]264', r'[Hh]264', r'[Hh]265', r'[Aa][Vv][Cc]',
    r'[Aa][Cc]3', r'[Dd][Tt][Ss]', r'[Aa][Aa][Cc]',
    r'[Gg][Ee][Rr][Mm][Aa][Nn]', r'[Ee][Nn][Gg][Ll][Ii][Ss][Hh]',
    r'[Dd][Uu][Bb][Bb][Ee][Dd]', r'[Ss][Yy][Nn][Cc]',
]


def get_storage_folder():
    """Findet den Speicherort fuer temporaere Dateien (an EMC-Base angelehnt)."""
    try:
        xtra = os.path.dirname(EMC_BASE)
        if xtra:
            return xtra
    except Exception:
        pass
    if os.path.isdir("/media/hdd"):
        return "/media/hdd/xtra"
    if os.path.isdir("/media/usb"):
        return "/media/usb/xtra"
    if os.path.isdir("/media/mmc"):
        return "/media/mmc/xtra"
    return "/tmp"


STORAGE_FOLDER = get_storage_folder()
INFO_FOLDER = os.path.join(STORAGE_FOLDER, "Info")

for folder in [STORAGE_FOLDER, INFO_FOLDER]:
    if not os.path.exists(folder):
        try:
            os.makedirs(folder, exist_ok=True)
        except:
            pass


def getRandomUserAgent():
    useragents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    import random
    return random.choice(useragents)


def clean_filename_for_search(filename):
    """
    Bereinigt Dateinamen fuer die Suche
    z.B. "Tatort_2024-01-15_Das_Erste_1080p.ts" -> "Tatort"
    """
    if not filename:
        return ""
    
    # Erweiterung entfernen
    name = os.path.splitext(filename)[0]
    
    # Sender-Namen entfernen
    senders = [
        'Das Erste', 'ZDF', 'RTL', 'SAT1', 'SAT.1', 'ProSieben', 'Pro7',
        'VOX', 'kabel eins', 'RTLZWEI', 'RTL2', 'NITRO', 'DMAX', 'TLC',
        'sixx', 'ProSieben MAXX', 'SAT.1 Gold', 'ARTE', 'Phoenix', '3sat',
        'ONE', 'ZDFneo', 'ZDFinfo', 'ARD alpha', 'NDR', 'WDR', 'SWR',
        'BR', 'HR', 'MDR', 'RBB', 'SR', 'tagesschau24', 'KiKA',
        'ORF', 'ORF1', 'ORF2', 'SRF', 'ServusTV', 'ATV', 'Puls4',
    ]
    for sender in senders:
        name = re.sub(r'[_\-\s]*' + re.escape(sender) + r'[_\-\s]*', ' ', name, flags=re.I)
    
    # Junk-Pattern entfernen
    for pattern in FILENAME_JUNK:
        name = re.sub(pattern, ' ', name)
    
    # Unterstriche/Bindestriche zu Leerzeichen
    name = re.sub(r'[_\-]+', ' ', name)
    
    # Mehrfache Leerzeichen
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def apply_title_mapping(title):
    """Wendet TITLE_MAPPINGS an"""
    if not title:
        return title
    
    title_lower = title.lower().strip()
    
    # Exakter Match
    if title_lower in TITLE_MAPPINGS:
        return TITLE_MAPPINGS[title_lower]
    
    # Teilweiser Match
    for key, mapped in TITLE_MAPPINGS.items():
        if title_lower.startswith(key) or key in title_lower:
            return mapped
    
    return title


def save_info_json(slug, data):
    """Speichert Info-JSON fuer GradientStarX/GradientParental"""
    if not slug or not data:
        return False
    try:
        json_path = os.path.join(INFO_FOLDER, slug + '.json')
        existing = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    existing = json.load(f)
            except:
                pass
        existing.update(data)
        with open(json_path + '.tmp', 'w') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        os.replace(json_path + '.tmp', json_path)
        return True
    except Exception as e:
        if DEBUG_EMC:
            print('[EMC JSON ERROR] %s' % str(e))
        return False


class EMCPosterWorker(threading.Thread):
    """Worker-Thread fuer EMC Poster-Download"""
    
    def __init__(self, dest_path, title, shortdesc="", extdesc=""):
        threading.Thread.__init__(self)
        self.dest_path = dest_path
        self.title = title
        self.shortdesc = shortdesc
        self.extdesc = extdesc
        self.daemon = True
        self.success = False
    
    def run(self):
        try:
            # Title Mapping anwenden
            search_title = apply_title_mapping(self.title)
            if DEBUG_EMC:
                print("[EMC] Searching: '%s' (original: '%s')" % (search_title, self.title))
            
            # Slug fuer JSON
            slug = convtext(self.title) if self.title else None
            
            # TMDb Suche
            result = self.search_tmdb(search_title, slug)
            if result:
                self.success = True
                return
            
            # OMDb Fallback
            result = self.search_omdb(search_title, slug)
            if result:
                self.success = True
                return
            
            if DEBUG_EMC:
                print("[EMC] No poster found for: %s" % self.title)
                
        except Exception as e:
            if DEBUG_EMC:
                print("[EMC ERROR] %s" % str(e))
    
    def search_tmdb(self, title, slug):
        try:
            url = 'https://api.themoviedb.org/3/search/multi?api_key=%s&language=%s&query=%s' % (
                tmdb_api, lng, urlquote(title)
            )
            headers = {'User-Agent': getRandomUserAgent()}
            response = requests.get(url, headers=headers, timeout=(3, 6))
            
            if response.status_code != 200:
                return False
            
            data = response.json()
            results = data.get('results', [])
            
            for item in results:
                media_type = item.get('media_type', '')
                if media_type not in ['movie', 'tv']:
                    continue
                
                poster_path = item.get('poster_path')
                if not poster_path:
                    continue
                
                # Poster URL
                poster_url = 'https://image.tmdb.org/t/p/w500%s' % poster_path
                
                # Info-JSON speichern
                if slug:
                    info = {
                        'tmdb_id': item.get('id'),
                        'tmdb_vote_average': item.get('vote_average', 0),
                        'tmdb_vote_count': item.get('vote_count', 0),
                        'title': item.get('title') or item.get('name', ''),
                        'overview': item.get('overview', ''),
                        'media_type': media_type,
                        'adult': item.get('adult', False),
                        'Rated': '18' if item.get('adult') else 'NA',
                    }
                    if media_type == 'movie' and item.get('release_date'):
                        info['year'] = item.get('release_date', '')[:4]
                    elif media_type == 'tv' and item.get('first_air_date'):
                        info['year'] = item.get('first_air_date', '')[:4]
                    
                    save_info_json(slug, info)
                
                # Poster downloaden
                return self.download_poster(poster_url)
            
            return False
            
        except Exception as e:
            if DEBUG_EMC:
                print("[EMC TMDb ERROR] %s" % str(e))
            return False
    
    def search_omdb(self, title, slug):
        try:
            url = 'http://www.omdbapi.com/?t=%s&apikey=%s' % (urlquote(title), omdb_api)
            response = requests.get(url, timeout=(3, 6))
            data = response.json()
            
            if data.get('Response') != 'True':
                return False
            
            poster_url = data.get('Poster')
            if not poster_url or poster_url == 'N/A':
                return False
            
            # Info-JSON speichern
            if slug:
                info = {
                    'Rated': data.get('Rated', 'NA'),
                    'imdb_rating': data.get('imdbRating', 'N/A'),
                    'imdb_id': data.get('imdbID', ''),
                    'year': data.get('Year', ''),
                    'genre': data.get('Genre', ''),
                    'plot': data.get('Plot', ''),
                }
                save_info_json(slug, info)
            
            return self.download_poster(poster_url)
            
        except Exception as e:
            if DEBUG_EMC:
                print("[EMC OMDb ERROR] %s" % str(e))
            return False
    
    def download_poster(self, url):
        try:
            headers = {'User-Agent': getRandomUserAgent()}
            response = requests.get(url, headers=headers, timeout=(3, 6))
            response.raise_for_status()
            
            with open(self.dest_path, 'wb') as f:
                f.write(response.content)
            
            if DEBUG_EMC:
                print("[EMC] Poster saved: %s" % self.dest_path)
            return True
            
        except Exception as e:
            if DEBUG_EMC:
                print("[EMC Download ERROR] %s" % str(e))
            return False


class GradientPosterXEMC(Renderer):
    """
    Poster-Renderer fuer EMC / Movie Player
    Cache-only: zeigt Poster nur aus EMC Cache (<storage>/xtra/EMC/poster)
    """
    
    GUI_WIDGET = ePixmap
    
    def __init__(self):
        Renderer.__init__(self)
        self.poster_path = None
        self.timer = eTimer()
        try:
            self.timer.timeout.connect(self._checkPoster)
        except:
            self.timer.callback.append(self._checkPoster)
        self.worker = None
        self.check_count = 0
    
    def changed(self, what):
        if not self.instance:
            return
        if what[0] == self.CHANGED_CLEAR:
            self.instance.hide()
            return
        self._updateEvent()
    
    def _updateEvent(self):
        try:
            src = self.source
            event = None
            path = None
            ref = None
            # Service-Pfad ermitteln
            if isinstance(src, ServiceEvent):
                event = src.event
                svc = getattr(src, 'service', None)
                if svc:
                    try:
                        path = svc.getPath()
                    except Exception:
                        path = None
            elif isinstance(src, CurrentService):
                ref = src.getCurrentServiceReference()
                if ref:
                    try:
                        path = ref.getPath()
                    except Exception:
                        path = None
            else:
                self.instance.hide()
                return
            if not path:
                self.instance.hide()
                return
            # Titel-Kandidaten sammeln (Event -> .meta -> ref.getName -> Filename)
            titles = []
            if event:
                try:
                    n = (event.getEventName() or '').strip()
                    if n:
                        titles.append(n)
                except Exception:
                    pass
            meta_title = _emc_read_meta_title(path)
            if meta_title:
                titles.append(meta_title)
            if ref:
                try:
                    rn = (ref.getName() or '').strip()
                    if rn:
                        titles.append(rn)
                except Exception:
                    pass
            fn_title = _emc_extract_title_from_filename(path)
            if fn_title:
                titles.append(fn_title)
            # Variants / Normalisierung (automatisch, keine manuellen Einträge pro Aufnahme)
            expanded = []
            for _t in titles:
                for v in _emc_expand_title_variants(_t):
                    if v and v not in expanded:
                        expanded.append(v)

            # TITLE_MAPPINGS anwenden (wenn vorhanden)
            try:
                mapped = []
                for _t in list(expanded):
                    mt = apply_title_mapping(_t)
                    if mt and mt not in expanded and mt not in mapped:
                        mapped.append(mt)
                expanded += mapped
            except Exception:
                pass

            titles = expanded

            # ---- Season-aware / episode-title-aware lookup ----
            # Priority: Staffel-Poster (Sxx) -> Episode-Titel-Poster -> Serien-Poster
            season_titles = []
            episode_like_titles = []
            try:
                import re as _re2, os as _os2

                def _dedupe(seq):
                    out = []
                    seen = set()
                    for x in seq or []:
                        if not x:
                            continue
                        x = str(x).strip()
                        if not x:
                            continue
                        if x in seen:
                            continue
                        seen.add(x)
                        out.append(x)
                    return out

                def _clean_series(x):
                    if not x:
                        return ''
                    y = str(x).strip()
                    # S01E05 / [S01E05]
                    y = _re2.sub(r'\s*[\[(]?[Ss]\d{1,2}[Ee]\d{1,3}[\])]?.*$', '', y).strip()
                    # 1x06 / [1x06]
                    y = _re2.sub(r'\s*[\[(]?\d{1,2}[xX]\d{1,3}[\])]?.*$', '', y).strip()
                    # Doku-Format: "Serie 3. Titel"
                    y = _re2.sub(r'\s+\d{1,3}\..*$', '', y).strip()
                    y = _re2.sub(r'\s+', ' ', y).strip(' -_')
                    return y

                _fn = _os2.path.basename(path or '')
                _stem = _os2.path.splitext(_fn)[0].strip()

                # Format 1: S01E05
                _m = _re2.search(r'[Ss](\d{1,2})[Ee](\d{1,3})', _stem)
                # Format 2: 1x06
                _m1x = _re2.search(r'\b(\d{1,2})[xX](\d{1,3})\b', _stem) if not _m else None
                # Format 3: "Serie 1. Titel" (Dokumentationen)
                _m_n = _re2.search(r'^(.+?)\s+(\d{1,3})\.\s+(.+)$', _stem) if not _m and not _m1x else None
                # Format 4: "Serie-Episodentitel"
                _m_h = _re2.search(r'^(.+?)\s*[-–]\s*(.+)$', _stem) if not _m and not _m1x and not _m_n else None

                # Fallback: SxxExx kann auch im Event-/Meta-Titel stehen
                if not _m and not _m1x:
                    _joined = ' | '.join([t for t in titles if t])
                    _m = _re2.search(r'[Ss](\d{1,2})[Ee](\d{1,3})', _joined)
                    _m1x = _re2.search(r'\b(\d{1,2})[xX](\d{1,3})\b', _joined) if not _m else None

                if _m:
                    _s = int(_m.group(1))
                    for _t in titles:
                        _clean = _clean_series(_t)
                        if _clean:
                            season_titles.append('%s_S%02d' % (_clean, _s))
                    _clean_fn = _clean_series(_stem)
                    if _clean_fn:
                        season_titles.append('%s_S%02d' % (_clean_fn, _s))
                elif _m1x:
                    _s = int(_m1x.group(1))
                    for _t in titles:
                        _clean = _clean_series(_t)
                        if _clean:
                            season_titles.append('%s_S%02d' % (_clean, _s))
                    _clean_fn = _clean_series(_stem)
                    if _clean_fn:
                        season_titles.append('%s_S%02d' % (_clean_fn, _s))
                elif _m_n:
                    # Dokumentationsformat -> Staffel 1
                    _series = (_m_n.group(1) or '').strip()
                    _ep_title = (_m_n.group(3) or '').strip()
                    if _series:
                        season_titles.append('%s_S01' % _series)
                    if _series and _ep_title:
                        episode_like_titles.append('%s-%s' % (_series, _ep_title))
                        episode_like_titles.append('%s - %s' % (_series, _ep_title))
                    episode_like_titles.append(_stem)
                elif _m_h:
                    # Serie-Episodentitel (z.B. "Wir waren wie Brüder-Bastogne")
                    _series = (_m_h.group(1) or '').strip()
                    _ep_title = (_m_h.group(2) or '').strip()
                    _special_ep = _special_episode_number(_series, _ep_title)
                    _alias_titles = _special_series_alias_titles(_series)

                    if _series:
                        # Prefer stable alias titles for matching (avoids wrong poster matches)
                        for _at in _alias_titles:
                            if _at and _at not in titles:
                                titles.insert(0, _at)

                    if _special_ep:
                        # For known series: prefer season poster only (episode-title posters can be wrong)
                        for _at in _alias_titles:
                            if _at:
                                season_titles.append('%s_S01' % _at)
                        # Prevent fallback to wrong "Series-EpisodeTitle" posters
                        try:
                            _keep_norm = set([_emc_norm_key(x) for x in _alias_titles if x])
                            _series_only = []
                            for _t2 in list(titles):
                                _nk = _emc_norm_key(_t2)
                                if _nk in _keep_norm and _t2 not in _series_only:
                                    _series_only.append(_t2)
                            for _at in _alias_titles:
                                if _at and _at not in _series_only:
                                    _series_only.insert(0, _at)
                            titles = _series_only
                        except Exception:
                            pass
                    else:
                        # Generic behavior for other series
                        if _series and _ep_title:
                            episode_like_titles.append('%s-%s' % (_series, _ep_title))
                            episode_like_titles.append('%s - %s' % (_series, _ep_title))
                        episode_like_titles.append(_stem)
                        if _series:
                            # defensiver Staffel-Fallback
                            season_titles.append('%s_S01' % _series)

                season_titles = _dedupe(season_titles)
                episode_like_titles = _dedupe(episode_like_titles)
            except Exception:
                pass

            # Cache-only lookup
            found = None
            if season_titles:
                found = _emc_find_artwork(EMC_POSTER_FOLDER, season_titles)
            if not found and episode_like_titles:
                found = _emc_find_artwork(EMC_POSTER_FOLDER, episode_like_titles)
            if not found:
                found = _emc_find_artwork(EMC_POSTER_FOLDER, titles)
            if not found:
                self.instance.hide()
                return
            self.poster_path = found
            self._showPoster(found)
        except Exception as e:
            if DEBUG_EMC:
                print('[EMC Poster _updateEvent ERROR] %s' % str(e))
            self.instance.hide()
    def _startWorker(self, dest_path, query, short, ext):
        # Alten Worker stoppen wenn noch aktiv
        if self.worker and self.worker.is_alive():
            return  # Warten auf alten Worker
        
        self.worker = EMCPosterWorker(dest_path, query, short, ext)
        self.worker.start()
        self.check_count = 0
        self.timer.start(300, True)  # Nach 300ms pruefen
    
    def _checkPoster(self):
        try:
            self.check_count += 1
            
            # Poster pruefen
            if self.poster_path and os.path.exists(self.poster_path):
                if os.path.getsize(self.poster_path) > 0:
                    self._showPoster(self.poster_path)
                    return
            
            # Maximal 20 Versuche (ca. 6 Sekunden)
            if self.check_count < 20:
                self.timer.start(300, True)
            else:
                self.instance.hide()
                
        except:
            self.instance.hide()
    
    def _showPoster(self, path):
        try:
            self.instance.setPixmap(loadJPG(path))
            self.instance.setScale(1)
            self.instance.show()
        except:
            self.instance.hide()


# Test
if __name__ == '__main__':
    print("=" * 60)
    print("GradientPosterXEMC - OPTIMIERTE VERSION")
    print("=" * 60)
    print()
    print("FEATURES:")
    print("  - TITLE_MAPPINGS fuer deutsche Sendungen")
    print("  - JSON-Speicherung fuer Rating/FSK")
    print("  - Verbesserte Dateinamensbereinigung")
    print("  - TMDb + OMDb Suche")
    print()
    print("TITLE_MAPPINGS Anzahl: %d" % len(TITLE_MAPPINGS))
    print()
    print("Dateinamensbereinigung Test:")
    test_files = [
        "Tatort_2024-01-15_Das_Erste_1080p.ts",
        "GZSZ_RTL_S01E1234.ts",
        "Der_Bergdoktor_ZDF_720p_German.mkv",
        "Sportschau_2024-03-10_ARD.ts",
        "The_Dark_Knight_2008_1080p_BluRay.mkv",
    ]
    for f in test_files:
        cleaned = clean_filename_for_search(f)
        mapped = apply_title_mapping(cleaned)
        print("  '%s'" % f)
        print("    -> cleaned: '%s'" % cleaned)
        print("    -> mapped:  '%s'" % mapped)
        print()
