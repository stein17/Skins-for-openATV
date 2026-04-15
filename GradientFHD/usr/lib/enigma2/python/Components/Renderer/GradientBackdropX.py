#!/usr/bin/python3
# -*- coding: utf-8 -*-
# GradientBackdropX.py - patched build (progress + live bouquets + stream filter)
# NOTE: this header is sanitized to avoid IndentationError from stray text lines.

# BUGFIX VERSION - elif zu if geändert für korrekte Fallback-Kette
#!/usr/bin/python
# -*- coding: utf-8 -*-

# by digiteng...07.2021,
# 08.2021(stb lang support),
# 09.2021 mini fixes
# edit by lululla 07.2022
# recode from lululla 2023
# © Provided that digiteng rights are protected, all or part of the code can be used, modified...
# russian and py3 support by sunriser...
# downloading in the background while zaping...
# by beber...03.2022,
# 03.2022 several enhancements : several renders with one queue thread, google search (incl. molotov for france) + autosearch & autoclean thread ...
# for infobar,
# 02.26 @stein17, Many new features and improvements
# <widget source="session.Event_Now" render="GradientBackdropX" position="100,100" size="680,1000" />
# <widget source="session.Event_Next" render="GradientBackdropX" position="100,100" size="680,1000" />
# <widget source="session.Event_Now" render="GradientBackdropX" position="100,100" size="680,1000" nexts="2" />
# <widget source="session.CurrentService" render="GradientBackdropX" position="100,100" size="680,1000" nexts="3" />
# for ch,
# <widget source="ServiceEvent" render="GradientBackdropX" position="100,100" size="680,1000" nexts="2" />
# <widget source="ServiceEvent" render="GradientBackdropX" position="100,100" size="185,278" nexts="2" />
# for epg, event
# <widget source="Event" render="GradientBackdropX" position="100,100" size="680,1000" />
# <widget source="Event" render="GradientBackdropX" position="100,100" size="680,1000" nexts="2" />
# or put tag -->  path="/media/hdd/backdrop"

# ============================================================================
# OPTIONAL: Custom recording (movie) directories for "Recording Asset Protection"
# ============================================================================
# ENGLISH
# -------
# What this is:
#   Gradient Poster/Backdrop AutoDB keeps a LIVE artwork cache and normally deletes
#   old images after 3 days (cleanup).
#
#   To still have posters/backdrops (and Info JSON) for your RECORDINGS months later,
#   the code can "protect" artwork that belongs to existing recordings by scanning
#   your recording directories and matching titles/slugs.
#
# What this file does:
#   If your recordings are NOT stored in the default Enigma2 movie folders, you can
#   create this file to add additional directories to scan:
#
#       /etc/enigma2/xtra_recording_dirs.conf
#
#   Format:
#     - one directory path per line
#     - lines starting with '#' are comments
#
# Effect:
#   Artwork (poster/backdrop/info) matching recordings found in these directories
#   is kept (not deleted by the 3-day cleanup), so you can still see it in EMC/
#   MoviePlayer even after many months.
#
# Example:
#   /media/hdd/movie
#   /media/hdd/Serien
#   /media/hdd/Filme
#
# DEUTSCH
# -------
# Wofür ist das:
#   Gradient Poster/Backdrop AutoDB hält einen LIVE-Cache und löscht alte Bilder
#   normalerweise nach 3 Tagen (Cleanup).
#
#   Damit Poster/Backdrops (und Info-JSON) für vorhandene AUFNAHMEN auch nach Monaten
#   noch verfügbar sind, kann der Code Artwork schützen, indem er Aufnahme-Ordner
#   scannt und passende Titel/Slugs findet.
#
# Was diese Datei bewirkt:
#   Wenn deine Aufnahmen NICHT in den Standard-Enigma2 Movie-Ordnern liegen, kannst
#   du über diese Datei zusätzliche Ordner angeben, die gescannt werden sollen:
#
#       /etc/enigma2/xtra_recording_dirs.conf
#
#   Format:
#     - ein Ordnerpfad pro Zeile
#     - Zeilen die mit '#' beginnen sind Kommentare
#
# Wirkung:
#   Artwork (Poster/Backdrop/Info), das zu Aufnahmen aus diesen Ordnern passt, wird
#   geschützt (nicht vom 3-Tage-Cleanup gelöscht). Dadurch siehst du auch nach vielen
#   Monaten noch Poster/Backdrop in EMC/MoviePlayer.
#
# Beispiel:
#   /media/hdd/movie
#   /media/hdd/Serien
#   /media/hdd/Filme
# ============================================================================

from __future__ import print_function
from Components.Renderer.Renderer import Renderer
from .GradientBackdropXDownloadThread import (
    GradientBackdropXDownloadThread,
    get_store_slug,
    get_provider_override,
)

try:
    from .GradientPosterXDownloadThread import get_query_variants
except Exception:
    try:
        from GradientPosterXDownloadThread import get_query_variants
    except Exception:
        def get_query_variants(title, shortdesc=None, fulldesc=None, **kwargs):
            return {'slug_title': (title or '').strip()}

from Components.Sources.CurrentService import CurrentService
from Components.Sources.Event import Event
from Components.Sources.EventInfo import EventInfo
from Components.Sources.ServiceEvent import ServiceEvent
from Components.config import config
try:
    from Components.AVSwitch import AVSwitch
except Exception:
    AVSwitch = None
from ServiceReference import ServiceReference
from six import text_type
from enigma import (
    ePixmap,
    loadJPG,
    eEPGCache,
    eTimer,
    ePicLoad,
    BT_HALIGN_CENTER,
    BT_VALIGN_CENTER,
    BT_KEEP_ASPECT_RATIO,
    BT_SCALE,
)
import NavigationInstance
import os
import re
import shutil
import socket
import sys
import time
import json
import threading
import datetime

STOP_AUTODB_FILE = '/tmp/stop_backdrop_autodb'

MAX_BACKDROP_W = 685
MAX_BACKDROP_H = 388


def _backdropx_dbg(msg):
    return


def _unique_keep_order(items):
    out = []
    seen = set()
    for it in items or []:
        if not it:
            continue
        if it in seen:
            continue
        seen.add(it)
        out.append(it)
    return out


def _backdrop_slug_candidates(title, shortdesc=None, fulldesc=None, base_slug=None):
    """Build filename slug candidates for already-downloaded backdrops.

    Order matters: first the current canonical/base slug, then exact episodic/raw-title
    variants, then a couple of lightweight title normalizations.
    """
    candidates = []
    try:
        if base_slug:
            candidates.append(str(base_slug).strip())
    except Exception:
        pass

    raw_title = (title or '').strip()
    if raw_title:
        try:
            candidates.append(get_canonical_slug(raw_title))
        except Exception:
            pass
        try:
            candidates.append(convtext(raw_title))
        except Exception:
            pass

        # common EPG suffix cleanup while keeping episode numbers in exact candidate above
        cleaned = raw_title
        try:
            cleaned = re.sub(r'\s*[\-–:]\s*Folge\s*\d+.*$', '', cleaned, flags=re.I)
            cleaned = re.sub(r'\s*[\-–:]\s*Episode\s*\d+.*$', '', cleaned, flags=re.I)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        except Exception:
            pass
        if cleaned and cleaned != raw_title:
            try:
                candidates.append(get_canonical_slug(cleaned))
            except Exception:
                pass
            try:
                candidates.append(convtext(cleaned))
            except Exception:
                pass

    try:
        qv = get_query_variants(title, shortdesc, fulldesc) or {}
        slug_title = (qv.get('slug_title') or '').strip()
        if slug_title:
            try:
                candidates.append(get_store_slug(slug_title))
            except Exception:
                pass
            try:
                candidates.append(get_canonical_slug(slug_title))
            except Exception:
                pass
    except Exception:
        pass

    return _unique_keep_order(candidates)


def _resolve_existing_backdrop_path(title, shortdesc=None, fulldesc=None, base_slug=None):
    """Return first existing backdrop path, preferring exact/base slug then episodic variants."""
    try:
        candidates = _backdrop_slug_candidates(title, shortdesc, fulldesc, base_slug)
        for slug in candidates:
            p = os.path.join(path_folder, '%s.jpg' % slug)
            try:
                if os.path.exists(p) and os.path.getsize(p) > 0:
                    return p, slug
            except Exception:
                pass

        # Last-resort fallback: if only a per-episode file exists, prefer the most recent one
        # that matches the base slug prefix. This preserves older BackdropDB naming.
        if base_slug:
            try:
                pref = str(base_slug).strip() + '_'
                best = None
                best_mtime = -1
                for fn in os.listdir(path_folder):
                    if not fn.lower().endswith('.jpg'):
                        continue
                    if not fn.startswith(pref):
                        continue
                    p = os.path.join(path_folder, fn)
                    try:
                        if os.path.getsize(p) <= 0:
                            continue
                        mt = os.path.getmtime(p)
                    except Exception:
                        continue
                    if mt > best_mtime:
                        best_mtime = mt
                        best = p
                if best:
                    return best, os.path.splitext(os.path.basename(best))[0]
            except Exception:
                pass
    except Exception:
        pass
    return None, base_slug



# =========================================================================
# RECORDING ASSET PROTECTION (keep backdrops/posters/json for recordings)
# =========================================================================
RECORDING_PROTECT_CONF = '/etc/enigma2/xtra_recording_dirs.conf'

try:
    from .GradientConverlibr import convtext, get_canonical_slug as _xtra_convtext, apply_title_mapping as _xtra_apply_title_mapping
except Exception:
    try:
        from GradientConverlibr import convtext as _xtra_convtext, apply_title_mapping as _xtra_apply_title_mapping
    except Exception:
        _xtra_convtext = None
        _xtra_apply_title_mapping = None

_RECORDING_EXTS = ('.ts', '.mkv', '.mp4', '.avi', '.mpeg', '.mpg', '.m2ts', '.mov', '.wmv')


def get_canonical_slug(text):
    """Return a stable filename slug (lowercase, underscores, umlaut-safe)."""
    try:
        import re, unicodedata
        if not isinstance(text, str):
            text = str(text or "")
        # German umlauts / ß
        repl = {"ä":"ae","ö":"oe","ü":"ue","ß":"ss","Ä":"Ae","Ö":"Oe","Ü":"Ue"}
        for k,v in repl.items():
            text = text.replace(k, v)
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"[-–—/|,:!?.'\"()\[\]{}]", " ", text)
        text = re.sub(r"\s+", " ", text).strip().lower()
        text = text.replace(" ", "_")
        text = re.sub(r"_+", "_", text).strip("_")
        return text
    except Exception:
        return (text or "").replace(" ", "_").lower()

def _read_extra_recording_dirs():
    out = []
    try:
        if os.path.exists(RECORDING_PROTECT_CONF):
            with open(RECORDING_PROTECT_CONF, 'r') as f:
                for ln in f:
                    ln = (ln or '').strip()
                    if not ln or ln.startswith('#'):
                        continue
                    out.append(ln)
    except Exception:
        pass
    return out


def _get_recording_dirs():
    dirs = set()
    try:
        vd = getattr(config, 'movielist', None)
        if vd is not None and hasattr(vd, 'videodirs'):
            val = vd.videodirs.value
            if isinstance(val, (list, tuple)):
                for p in val:
                    if p:
                        dirs.add(str(p))
            elif isinstance(val, str) and val:
                dirs.add(val)
    except Exception:
        pass

    try:
        up = getattr(config, 'usage', None)
        if up is not None and hasattr(up, 'default_path'):
            p = up.default_path.value
            if p:
                dirs.add(str(p))
    except Exception:
        pass

    for p in (
        '/media/hdd/movie', '/media/hdd/movies', '/media/hdd/recordings',
        '/media/usb/movie', '/media/usb/movies', '/media/usb/recordings',
        '/media/mmc/movie', '/media/mmc/movies', '/media/mmc/recordings',
    ):
        if os.path.isdir(p):
            dirs.add(p)

    for p in _read_extra_recording_dirs():
        if os.path.isdir(p):
            dirs.add(p)

    return [d for d in dirs if d and os.path.isdir(d)]


def _storage_xtra_base():
    # Use configured PosterX base if available; supports custom paths like /media/autofs/...
    try:
        sel = getattr(config.plugins.GradientFHD, "posterXPath", None)
        if sel is not None and getattr(sel, "value", None) and sel.value != "AUTO":
            base = sel.value
            if os.path.isdir(base):
                return os.path.join(base, "xtra")
    except Exception:
        pass

    # AUTO fallback: prefer first writable/usable mount
    for base in ("/media/hdd", "/media/usb", "/media/mmc", "/media/net", "/media/autofs"):
        try:
            if os.path.isdir(base):
                return os.path.join(base, "xtra")
        except Exception:
            pass
    return "/tmp"


def _meta_title_for_recording(media_path):
    try:
        meta = media_path + '.meta'
        if not os.path.exists(meta):
            base, _ = os.path.splitext(media_path)
            meta = base + '.meta'
        if not os.path.exists(meta):
            return None
        with open(meta, 'r') as f:
            lines = f.read().splitlines()
        if len(lines) >= 2:
            t = (lines[1] or '').strip()
            return t or None
    except Exception:
        return None


def _clean_filename_for_search(filename):
    try:
        name = os.path.splitext(os.path.basename(filename))[0]
        name = re.sub(r'\d{4}[-_]\d{2}[-_]\d{2}', ' ', name)
        name = re.sub(r'\d{8}', ' ', name)
        name = re.sub(r'(?i)(1080p|1080i|720p|2160p|4k|hdtv|web[- ]?dl|webrip|bdrip|bluray|x264|h264|h265|hevc|ac3|dts)', ' ', name)
        senders = ['Das Erste','ZDF','RTL','SAT1','SAT.1','ProSieben','Pro7','VOX','kabel eins','RTLZWEI','RTL2','ARTE','Phoenix','3sat','ONE','ZDFneo','ZDFinfo','NDR','WDR','SWR','BR','HR','MDR','RBB','ARD']
        for sn in senders:
            name = re.sub(r'(?i)[_\-\s]*' + re.escape(sn) + r'[_\-\s]*', ' ', name)
        name = re.sub(r'[_\-]+', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        return name
    except Exception:
        return ''


def _slug_candidates(title):
    out = set()
    if not title:
        return out

    t = title
    try:
        if _xtra_apply_title_mapping:
            t = _xtra_apply_title_mapping(t)
    except Exception:
        pass

    try:
        if _xtra_convtext:
            st = _xtra_convtext(t)
            if st:
                out.add(st)
    except Exception:
        pass

    try:
        st2 = convtext(t)
        if st2:
            out.add(st2)
    except Exception:
        pass

    return out


def _build_recording_slug_set(max_files=50000):
    slugs = set()
    count = 0
    for root in _get_recording_dirs():
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ('lost+found',)]
            for fn in filenames:
                if not fn:
                    continue
                if not fn.lower().endswith(_RECORDING_EXTS):
                    continue
                media = os.path.join(dirpath, fn)
                count += 1
                if count > max_files:
                    return slugs
                titles = []
                mt = _meta_title_for_recording(media)
                if mt:
                    titles.append(mt)
                titles.append(os.path.splitext(fn)[0])
                titles.append(_clean_filename_for_search(fn))
                for tt in titles:
                    tt = (tt or '').strip()
                    if not tt:
                        continue
                    for slug in _slug_candidates(tt):
                        slugs.add(slug)
    return slugs


def _touch_if_exists(p):
    try:
        if p and os.path.exists(p):
            os.utime(p, (time.time(), time.time()))
            return True
    except Exception:
        pass
    return False


def _refresh_recording_assets(slugs, log_func=None):
    base = _storage_xtra_base()
    poster_dir = os.path.join(base, 'poster')
    backdrop_dir = os.path.join(base, 'backdrop')
    info_dir = os.path.join(base, 'Info')
    touched = 0
    for slug in slugs:
        if not slug:
            continue
        touched += 1 if _touch_if_exists(os.path.join(poster_dir, slug + '.jpg')) else 0
        touched += 1 if _touch_if_exists(os.path.join(backdrop_dir, slug + '.jpg')) else 0
        touched += 1 if _touch_if_exists(os.path.join(info_dir, slug + '.json')) else 0
    if log_func:
        try:
            log_func('[AutoDB] recording-protect: %d slug(s), %d file(s) refreshed' % (len(slugs), touched))
        except Exception:
            pass
    return touched

from re import search, sub, I, S, escape

# ============================================================================
# AutoDB log path (OpenATV): /tmp is usually /var/volatile/tmp
# ============================================================================
try:
    LOG_DIR = '/var/volatile/tmp' if os.path.isdir('/var/volatile/tmp') else '/tmp'
except Exception:
    LOG_DIR = '/tmp'

def _autodb_log_path(name):
    try:
        return os.path.join(LOG_DIR, name)
    except Exception:
        return '/tmp/%s' % name



def _autodb_progress_path(name):
    try:
        return os.path.join(LOG_DIR, name)
    except Exception:
        return '/tmp/%s' % name


def _write_autodb_progress(kind, current, total, service_name=None, state='running'):
    # Write AutoDB progress as JSON (atomic)
    try:
        path = _autodb_progress_path('BackdropAutoDB.progress.json')
        tmp = path + '.tmp'
        cur = int(current) if current is not None else 0
        tot = int(total) if total is not None else 0
        pct = int((float(cur) * 100.0 / float(tot)) if tot else 0)
        data = {'ts': time.time(), 'kind': kind, 'state': state, 'current': cur, 'total': tot, 'percent': pct, 'service': service_name or ''}
        with open(tmp, 'w') as f:
            json.dump(data, f)
        try:
            os.replace(tmp, path)
        except Exception:
            os.rename(tmp, path)
    except Exception:
        pass


def _merge_info_payload(out_path, payload):
    """Merge debug payload into existing backdrop_info json without dropping cached URLs."""
    try:
        existing = {}
        if os.path.exists(out_path):
            try:
                with open(out_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f) or {}
            except Exception:
                existing = {}
        if not isinstance(existing, dict):
            existing = {}
        clean = {k: v for k, v in (payload or {}).items() if v is not None}
        existing.update(clean)
        tmp_path = out_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2, sort_keys=True)
        try:
            os.replace(tmp_path, out_path)
        except Exception:
            os.rename(tmp_path, out_path)
        return True
    except Exception:
        return False


def _write_backdrop_info_debug(slug, payload):
    """Write provider-trace info but keep existing backdrop_url/source intact."""
    if not slug:
        return False
    try:
        base = _storage_xtra_base()
        info_dir = os.path.join(base, 'backdrop_info')
        os.makedirs(info_dir, exist_ok=True)
        out_path = os.path.join(info_dir, slug + '.json')
        return _merge_info_payload(out_path, payload)
    except Exception:
        return False
PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True
    import queue
    import html
    html_parser = html
    from _thread import start_new_thread
    from urllib.error import HTTPError, URLError
    from urllib.request import urlopen
    from urllib.parse import quote_plus
else:
    pass
    import Queue
    from thread import start_new_thread
    from urllib2 import HTTPError, URLError
    from urllib2 import urlopen
    from urllib import quote_plus
    from HTMLParser import HTMLParser
    html_parser = HTMLParser()


try:
    from urllib import unquote, quote
except ImportError:
    pass
    from urllib.parse import unquote, quote


epgcache = eEPGCache.getInstance()
if PY3:
    pdb = queue.PriorityQueue()
else:
    pdb = Queue.PriorityQueue()

DEBUG_AUTODB = False  # set True only if you want verbose AutoDB per-event logging



def isMountedInRW(mount_point):
    with open("/proc/mounts", "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) > 1 and parts[1] == mount_point:
                return True
    return False


cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')
noposter = "/usr/share/enigma2/%s/main/noposter.jpg" % cur_skin
path_folder = os.path.join(_storage_xtra_base(), "backdrop") + "/"

if not os.path.exists(path_folder):
    os.makedirs(path_folder, exist_ok=True)


epgcache = eEPGCache.getInstance()
apdb = dict()



# ============================================================================
# LIVE SELECTION TRACKING (performance):
# Track latest SERVICE only (not title), because many skins have multiple
# GradientBackdropX instances (nexts=0..4) that would otherwise fight each other.
# Timestamp is updated only when the service changes.
# ============================================================================
_LIVE_LOCK = threading.Lock()
_LIVE_LATEST_SERVICE = None
_LIVE_LATEST_TS = 0.0


def _make_live_service(canal):
    try:
        return (canal[0] or '').strip()
    except Exception:
        return ''


def set_live_latest(canal):
    global _LIVE_LATEST_SERVICE, _LIVE_LATEST_TS
    svc = _make_live_service(canal)
    with _LIVE_LOCK:
        if svc and svc != _LIVE_LATEST_SERVICE:
            _LIVE_LATEST_SERVICE = svc
            _LIVE_LATEST_TS = time.time()


def get_live_latest():
    with _LIVE_LOCK:
        return _LIVE_LATEST_SERVICE, _LIVE_LATEST_TS


try:
    lng = config.osd.language.value
    lng = lng[:-3]
except:
    pass
    lng = 'en'
    pass



# AUTOMATISCHE BACKDROP-GENERIERUNG (AutoDB)
# ---------------------------------------
# - Es werden die TV-Bouquets aus /etc/enigma2/bouquets.tv eingelesen.
# - Es wird eine Konfigurationsdatei erzeugt:
#       /etc/enigma2/poster_autodb_bouquets.txt
# - Dort kannst du mit 1/0 steuern, welche Bouquets AutoDB benutzt.
# - AutoDB arbeitet dann nur mit den Sendern aus den aktivierten Bouquets.
#

bouquets_main_file = '/etc/enigma2/bouquets.tv'
autodb_bouquets_file = '/etc/enigma2/poster_autodb_bouquets.txt'
bouquet_dir = '/etc/enigma2'


def _read_bouquets_from_main():
    """
    Liest /etc/enigma2/bouquets.tv und sammelt alle referenzierten
    userbouquet.*.tv Einträge.
    """
    bouquet_ids = []
    if not os.path.exists(bouquets_main_file):
        return bouquet_ids
    try:
        with open(bouquets_main_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line.startswith('#SERVICE'):
                    continue
                if 'FROM BOUQUET "' in line:
                    part = line.split('FROM BOUQUET "', 1)[1]
                    name = part.split('"', 1)[0]
                    if name.endswith('.tv') and name not in bouquet_ids:
                        bouquet_ids.append(name)
    except Exception as e:
        print("[BackdropAutoDB] error reading bouquets.tv:", e)
    return bouquet_ids


def _collect_services_from_bouquet_id(bouquet_id, services, seen):
    """
    Liest alle #SERVICE Zeilen aus einer userbouquet.*.tv Datei und sammelt ServiceRefs.
    """
    bouquet_file = os.path.join(bouquet_dir, bouquet_id)
    if not os.path.exists(bouquet_file):
        return
    try:
        with open(bouquet_file, 'r') as f:
            for line in f:
                if not line.startswith('#SERVICE'):
                    continue
                parts = line[9:].strip().split(':')
                if len(parts) < 11:
                    continue
                # ServiceRef nur aus den ersten 11 Teilen bauen
                srvref = ':'.join(parts[:11])
                if srvref in seen:
                    continue
                seen.add(srvref)
                services.append(srvref)
    except Exception as e:
        print("[BackdropAutoDB] error reading bouquet %s: %s" % (bouquet_file, e))


def _get_bouquet_display_name(bouquet_id):
    """
    Liest aus /etc/enigma2/userbouquet.*.tv die #NAME-Zeile aus.
    """
    bouquet_file = os.path.join(bouquet_dir, bouquet_id)
    if not os.path.exists(bouquet_file):
        return None
    try:
        with open(bouquet_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#NAME'):
                    # alles nach "#NAME " nehmen
                    return line[5:].strip()
    except Exception as e:
        print("[BackdropAutoDB] error reading bouquet name %s: %s" % (bouquet_file, e))
    return None


# 1) bouquets.tv einlesen
bouquet_ids = _read_bouquets_from_main()

# 2) Vorherige Bouquet-Konfiguration (1/0) einlesen
bouquet_flags = {}
if os.path.exists(autodb_bouquets_file):
    try:
        with open(autodb_bouquets_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('|')
                if len(parts) >= 2:
                    flag = parts[0].strip()
                    # zweites Feld kann "userbouquet.dbe27.tv  #NAME HD+(TV)" sein
                    name_field = parts[1].strip().split()[0]
                    enabled = (flag != '0')
                    bouquet_flags[name_field] = enabled
    except Exception as e:
        print("[BackdropAutoDB] bouquet config read error:", e)

# 3) Neue Konfigurationsdatei mit Anleitung schreiben
try:
    with open(autodb_bouquets_file, 'w') as f:
        f.write("# ==============================================\n")
        f.write("#  Poster/Backdrop-AutoDB Bouquets\n")
        f.write("# ==============================================\n")
        f.write("# Diese Datei wird automatisch aus folgendem File erzeugt:\n")
        f.write("#   /etc/enigma2/bouquets.tv\n")
        f.write("#\n")
        f.write("# Hier kannst du steuern, welche Bouquets von AutoDB\n")
        f.write("# verwendet werden. AutoDB arbeitet nur mit Sendern aus\n")
        f.write("# Bouquets, die mit '1|' markiert sind.\n")
        f.write("#\n")
        f.write("# AUFBAU EINER ZEILE:\n")
        f.write("#   1|userbouquet.name.tv  #NAME Anzeigename\n")
        f.write("#\n")
        f.write("# BEDEUTUNG:\n")
        f.write("#   1 = Bouquet AKTIV   -> Sender in diesem Bouquet werden von AutoDB benutzt\n")
        f.write("#   0 = Bouquet AUS     -> Bouquet wird von AutoDB ignoriert\n")
        f.write("#\n")
        f.write("# BEISPIELE:\n")
        f.write("#   1|userbouquet.favourites.tv  #NAME Favoriten (TV)\n")
        f.write("#   0|userbouquet.pluto_tv_de.tv  #NAME Pluto TV (DE)\n")
        f.write("#\n")
        f.write("# SO KANNST DU ANPASSEN:\n")
        f.write("#   - 1 in 0 ändern  -> Bouquet bleibt in der Liste, wird aber von AutoDB ignoriert\n")
        f.write("#   - ganze Zeile löschen -> Bouquet wird komplett ignoriert\n")
        f.write("#\n")
        f.write("# WICHTIG:\n")
        f.write("#   - Diese Datei wird bei jedem Enigma2-Start neu geschrieben.\n")
        f.write("#   - Deine Einstellungen (0/1) werden übernommen, solange der Bouquet-Name gleich bleibt.\n")
        f.write("#   - Neue Bouquets aus bouquets.tv werden automatisch mit '1|' (aktiv) hinzugefügt.\n")
        f.write("# ==============================================\n\n")
        for b_id in bouquet_ids:
            enabled = bouquet_flags.get(b_id, True)
            flag = '1' if enabled else '0'
            bname = _get_bouquet_display_name(b_id)
            if bname:
                f.write("%s|%s  #NAME %s\n" % (flag, b_id, bname))
            else:
                f.write("%s|%s\n" % (flag, b_id))
except Exception as e:
    print("[BackdropAutoDB] bouquet config write error:", e)

# 4) APDB (ServiceRefs) wird NICHT mehr beim Import gebaut.
#    Das war langsam und kann den GUI-Thread blockieren (Spinner).
#    Stattdessen wird APDB im AutoDB-Thread bei einem Lauf erzeugt.
raw_services = []
seen_services = set()


def _read_autodb_config_runtime():
    """Read bouquet enable/disable config from autodb_bouquets_file.

    Returns:
        (bouquet_list_in_file_order, flags_dict)

    Notes:
    - This is read at runtime so changes made by AutoDBManager take effect immediately.
    - If the file contains no entries, fallback to bouquet_ids from bouquets.tv.
    """
    bq_list = []
    flags = {}

    try:
        if os.path.exists(autodb_bouquets_file):
            with open(autodb_bouquets_file, 'r') as f:
                for line in f:
                    line = (line or '').strip()
                    if not line or line.startswith('#'):
                        continue
                    if '|' not in line:
                        continue
                    parts = line.split('|', 1)
                    if len(parts) < 2:
                        continue
                    flag = parts[0].strip()
                    name_field = parts[1].strip().split()[0]
                    if not name_field:
                        continue
                    enabled = (flag != '0')
                    bq_list.append(name_field)
                    flags[name_field] = enabled
    except Exception as e:
        try:
            print('[AutoDB] config read error:', e)
        except Exception:
            pass

    # fallback: if file has no usable entries
    if not bq_list:
        try:
            bq_list = list(bouquet_ids)
        except Exception:
            bq_list = []
        for b in bq_list:
            flags[b] = True

    return bq_list, flags

def is_probably_stream_service(service_ref):
    """Return True for IPTV/stream services that usually have no Enigma2 EPG.

    We skip them in AutoDB to avoid wasting time and noisy logs.
    """
    try:
        s = (service_ref or '').strip()
        if not s:
            return True
        low = s.lower()
        # common streaming service types
        if s.startswith('4097:') or s.startswith('5001:') or s.startswith('5002:') or s.startswith('1:64:'):
            return True
        # url-like or m3u8/hls fragments
        if 'http' in low or 'https' in low or 'm3u8' in low or 'rtmp' in low or 'rtsp' in low:
            return True
        # encoded URL in serviceref
        if '%3a%2f%2f' in low:
            return True
        # DVB refs typically start with "1:"
        if not s.startswith('1:'):
            return True
        return False
    except Exception:
        return False



def build_apdb_for_autodb():
    """Build apdb from enabled bouquets (runs inside AutoDB thread).

    Important:
    - re-reads bouquet enable/disable config each run (no Enigma2 restart required).
    """
    global apdb

    bq_list, flags = _read_autodb_config_runtime()

    raw = []
    seen = set()
    for b_id in bq_list:
        if not flags.get(b_id, True):
            continue
        _collect_services_from_bouquet_id(b_id, raw, seen)

    # Filter out IPTV/stream services (no Enigma2 EPG)

    try:

        raw = [r for r in raw if not is_probably_stream_service(r)]

    except Exception:

        pass


    apdb.clear()
    for idx, service in enumerate(raw):
        apdb[idx] = service

    active = [b_id for b_id in bq_list if flags.get(b_id, True)]
    return active, len(apdb)



# try:
    # folder_size = sum([sum(map(lambda fname: os.path.getsize(os.path.join(path_folder, fname)), files)) for folder_p, folders, files in os.walk(path_folder)])
    # ozposter = "%0.f" % (folder_size / (1024 * 1024.0))
    # if ozposter >= "5":
        # shutil.rmtree(path_folder)
# except:
    # pass


def OnclearMem():
    try:
        os.system('sync')
        os.system('echo 1 > /proc/sys/vm/drop_caches')
        os.system('echo 2 > /proc/sys/vm/drop_caches')
        os.system('echo 3 > /proc/sys/vm/drop_caches')
    except:
        pass
        pass


def quoteEventName(eventName):
    try:
        text = eventName.decode('utf8').replace(u'\x86', u'').replace(u'\x87', u'').encode('utf8')
    except:
        pass
        text = eventName
    return quote_plus(text, safe="+")


REGEX = re.compile(
    r'[\(\[].*?[\)\]]|'                    # Parentesi tonde o quadre
    r':?\s?odc\.\d+|'                      # odc. con o senza numero prima
    r'\d+\s?:?\s?odc\.\d+|'                # numero con odc.
    r'[:!]|'                               # due punti o punto esclamativo
    r'\s-\s.*|'                            # trattino con testo successivo
    r',|'                                  # virgola
    r'/.*|'                                # tutto dopo uno slash
    r'\|\s?\d+\+|'                         # | seguito da numero e +
    r'\d+\+|'                              # numero seguito da +
    r'\s\*\d{4}\Z|'                        # * seguito da un anno a 4 cifre
    r'[\(\[\|].*?[\)\]\|]|'                # Parentesi tonde, quadre o pipe
    r'(?:\"[\.|\,]?\s.*|\"|'               # Testo tra virgolette
    r'\.\s.+)|'                            # Punto seguito da testo
    r'Премьера\.\s|'                       # Specifico per il russo
    r'[хмтдХМТД]/[фс]\s|'                  # Pattern per il russo con /ф o /с
    r'\s[сС](?:езон|ерия|-н|-я)\s.*|'      # Stagione o episodio in russo
    r'\s\d{1,3}\s[чсЧС]\.?\s.*|'           # numero di parte/episodio in russo
    r'\.\s\d{1,3}\s[чсЧС]\.?\s.*|'         # numero di parte/episodio in russo con punto
    r'\s[чсЧС]\.?\s\d{1,3}.*|'             # Parte/Episodio in russo
    r'\d{1,3}-(?:я|й)\s?с-н.*',            # Finale con numero e suffisso russo
    re.DOTALL)


def intCheck():
    """Fast, GUI-safe internet connectivity check.
    Avoids blocking HTTP requests in the main thread."""
    try:
        # Quick TCP check without DNS; 1.1.1.1:53 (Cloudflare) is usually reachable if routing works.
        s = socket.create_connection(("1.1.1.1", 53), timeout=0.8)
        try:
            s.close()
        except Exception:
            pass
        return True
    except Exception:
        return False



def remove_accents(string):
    if not isinstance(string, text_type):
        string = text_type(string, 'utf-8')
    string = re.sub(u"[àáâãäå]", 'a', string)
    string = re.sub(u"[èéêë]", 'e', string)
    string = re.sub(u"[ìíîï]", 'i', string)
    string = re.sub(u"[òóôõö]", 'o', string)
    string = re.sub(u"[ùúûü]", 'u', string)
    string = re.sub(u"[ýÿ]", 'y', string)
    return string


def unicodify(s, encoding='utf-8', norm=None):
    if not isinstance(s, text_type):
        s = text_type(s, encoding)
    if norm:
        from unicodedata import normalize
        s = normalize(norm, s)
    return s


def str_encode(text, encoding="utf8"):
    if not PY3:
        if isinstance(text, text_type):
            return text.encode(encoding)
    return text


def cutName(eventName=""):
    if eventName:
        eventName = eventName.replace('"', '').replace('.', '').replace(' | ', '')  # .replace('Х/Ф', '').replace('М/Ф', '').replace('Х/ф', '')
        eventName = eventName.replace('(18+)', '').replace('18+', '').replace('(16+)', '').replace('16+', '').replace('(12+)', '')
        eventName = eventName.replace('12+', '').replace('(7+)', '').replace('7+', '').replace('(6+)', '').replace('6+', '')
        eventName = eventName.replace('(0+)', '').replace('0+', '').replace('+', '')
        eventName = eventName.replace('المسلسل العربي', '')
        eventName = eventName.replace('مسلسل', '')
        eventName = eventName.replace('برنامج', '')
        eventName = eventName.replace('فيلم وثائقى', '')
        eventName = eventName.replace('حفل', '')
        return eventName
    return ""


def getCleanTitle(eventitle=""):
    # save_name = re.sub('\\(\d+\)$', '', eventitle)
    # save_name = re.sub('\\(\d+\/\d+\)$', '', save_name)  # remove episode-number " (xx/xx)" at the end
    # # save_name = re.sub('\ |\?|\.|\,|\!|\/|\;|\:|\@|\&|\'|\-|\"|\%|\(|\)|\[|\]\#|\+', '', save_name)
    save_name = eventitle.replace(' ^`^s', '').replace(' ^`^y', '')
    return save_name


def dataenc(data):
    if PY3:
        data = data.decode("utf-8")
    else:
        pass
        data = data.encode("utf-8")
    return data


def sanitize_filename(filename):
    # Replace spaces with underscores and remove invalid characters (like ':')
    sanitized = re.sub(r'[^\w\s-]', '', filename)  # Remove invalid characters
    # sanitized = sanitized.replace(' ', '_')      # Replace spaces with underscores
    # sanitized = sanitized.replace('-', '_')      # Replace dashes with underscores
    return sanitized.strip()


def convtext(text=''):
    try:
        if text is None:
            return
        if text == '':
            return
        else:
            pass
            text = text.lower()
            text = text.lstrip()
            
            # text = cutName(text)
            # text = getCleanTitle(text)

            if text.endswith("the"):
                text = "the " + text[:-4]
            
            # Modifiche personalizzate
            if 'giochi olimpici parigi' in text:
                text = 'olimpiadi di parigi'
            if 'bruno barbieri' in text:
                text = text.replace('bruno barbieri', 'brunobarbierix')
            if "anni '60" in text:
                text = "anni 60"
            if 'tg regione' in text:
                text = 'tg3'
            if 'studio aperto' in text:
                text = 'studio aperto'
            if 'josephine ange gardien' in text:
                text = 'josephine ange gardien'
            if 'elementary' in text:
                text = 'elementary'
            if 'squadra speciale cobra 11' in text:
                text = 'squadra speciale cobra 11'
            if 'criminal minds' in text:
                text = 'criminal minds'
            if 'i delitti del barlume' in text:
                text = 'i delitti del barlume'
            if 'senza traccia' in text:
                text = 'senza traccia'
            if 'hudson e rex' in text:
                text = 'hudson e rex'
            if 'ben-hur' in text:
                text = 'ben-hur'
            if 'alessandro borghese - 4 ristoranti' in text:
                text = 'alessandroborgheseristoranti'
            if 'alessandro borghese: 4 ristoranti' in text:
                text = 'alessandroborgheseristoranti' 

            cutlist = ['x264', '720p', '1080p', '1080i', 'pal', 'german', 'english', 'ws', 'dvdrip', 'unrated',
                       'retail', 'web-dl', 'dl', 'ld', 'mic', 'md', 'dvdr', 'bdrip', 'bluray', 'dts', 'uncut', 'anime',
                       'ac3md', 'ac3', 'ac3d', 'ts', 'dvdscr', 'complete', 'internal', 'dtsd', 'xvid', 'divx', 'dubbed',
                       'line.dubbed', 'dd51', 'dvdr9', 'dvdr5', 'h264', 'avc', 'webhdtvrip', 'webhdrip', 'webrip',
                       'webhdtv', 'webhd', 'hdtvrip', 'hdrip', 'hdtv', 'ituneshd', 'repack', 'sync', '1^tv', '1^ tv',
                       '1^ visione rai', '1^ visione', ' - prima tv', ' - primatv', 'prima visione',
                       'film -', 'de filippi', 'first screening',
                       'live:', 'new:', 'film:', 'première diffusion', 'nouveau:', 'en direct:', 
                       'premiere:', 'estreno:', 'nueva emisión:', 'en vivo:'
                       ]
            for word in cutlist:
                text = text.replace(word, '')
            text = ' '.join(text.split())

            text = cutName(text)
            text = getCleanTitle(text)

            text = text.partition("-")[0]  # Mantieni solo il testo prima del primo "-"

            # Pulizia finale
            text = text.replace('.', ' ').replace('-', ' ').replace('_', ' ').replace('+', '')

            # Rimozione pattern specifici
            if search(r'[Ss][0-9]+[Ee][0-9]+', text):
                text = sub(r'[Ss][0-9]+[Ee][0-9]+.*[a-zA-Z0-9_]+', '', text, flags=S | I)
            text = sub(r'\(.*\)', '', text).rstrip()
            text = text.partition("(")[0]
            text = sub(r"\\s\d+", "", text)
            text = text.partition(":")[0]
            text = re.sub(r'(odc.\s\d+)+.*?FIN', '', text)
            text = re.sub(r'(odc.\d+)+.*?FIN', '', text)
            text = re.sub(r'(\d+)+.*?FIN', '', text)
            text = re.sub('FIN', '', text)

            # Rimuovi accenti e normalizza
            text = remove_accents(text)

            # Forzature finali
            text = text.replace('XXXXXX', '60')
            text = text.replace('brunobarbierix', 'bruno barbieri - 4 hotel')
            text = text.replace('alessandroborgheseristoranti', 'alessandro borghese - 4 ristoranti')
            text = text.replace('il ritorno di colombo', 'colombo')

            # text = sanitize_filename(text)
###             # print('sanitize_filename text: ' + text)
            return text.capitalize()
    except Exception as e:
        pass
        pass


def _guess_media_type(service_name, title, shortdesc='', fulldesc=''):
    """Heuristic: decide 'movie' vs 'tv' for provider order in AutoDB."""
    try:
        s = (service_name or '').lower()
        t = (title or '').lower()
        blob = ' '.join([(title or ''), (shortdesc or ''), (fulldesc or '')]).lower()

        if any(k in s for k in ['sky cinema', 'cinema', 'movie', 'film', 'kino']):
            return 'movie'

        if any(k in blob for k in ['staffel', 'episode', 'folge', 's0', 'e0', 'season']):
            return 'tv'

        # daily magazines/news formats
        if any(k in t for k in ['punkt', 'tagesschau', 'heute journal', 'sport', 'news']):
            return 'tv'
    except Exception:
        pass
    return 'tv'


def convtextPAUSED(text=''):
    text = text.lower()
    text = text.lstrip()
    text = text.replace("\xe2\x80\x93", "").replace('\xc2\x86', '').replace('\xc2\x87', '')  # replace special
    if 'bruno barbieri' in text:
        text = text.replace('bruno barbieri', 'brunobarbierix')
    if "anni '60" in text:
        text = "anni 60"
    if 'tg regione' in text:
        text = 'tg3'
    if 'studio aperto' in text:
        text = 'studio aperto'
    if 'josephine ange gardien' in text:
        text = 'josephine ange gardien'
    if 'elementary' in text:
        text = 'elementary'
    if 'squadra speciale cobra 11' in text:
        text = 'squadra speciale cobra 11'
    if 'criminal minds' in text:
        text = 'criminal minds'
    if 'i delitti del barlume' in text:
        text = 'i delitti del barlume'
    if 'senza traccia' in text:
        text = 'senza traccia'
    if 'hudson e rex' in text:
        text = 'hudson e rex'
    if 'ben-hur' in text:
        text = 'ben-hur'
    if 'la7 ' in text:
        text = 'la7'
    if 'skytg24' in text:
        text = 'skytg24'
    cutlist = ['x264', '720p', '1080p', '1080i', 'pal', 'german', 'english', 'ws', 'dvdrip', 'unrated',
               'retail', 'web-dl', 'dl', 'ld', 'mic', 'md', 'dvdr', 'bdrip', 'bluray', 'dts', 'uncut', 'anime',
               'ac3md', 'ac3', 'ac3d', 'ts', 'dvdscr', 'complete', 'internal', 'dtsd', 'xvid', 'divx', 'dubbed',
               'line.dubbed', 'dd51', 'dvdr9', 'dvdr5', 'h264', 'avc', 'webhdtvrip', 'webhdrip', 'webrip',
               'webhdtv', 'webhd', 'hdtvrip', 'hdrip', 'hdtv', 'ituneshd', 'repack', 'sync', '1^tv', '1^ tv',
               '1^ visione rai', '1^ visione', ' - prima tv', ' - primatv', 'prima visione',
               'film -', 'de filippi', 'first screening', 'premiere:', 'live:', 'new:',
               'première diffusion', 'nouveau:', 'en direct:',
               'estreno:', 'nueva emisión:', 'en vivo:']
    text = text.replace('.wmv', '').replace('.flv', '').replace('.ts', '').replace('.m2ts', '').replace('.mkv', '').replace('.avi', '').replace('.mpeg', '').replace('.mpg', '').replace('.iso', '').replace('.mp4', '')

    for word in cutlist:
        text = sub(r'(\_|\-|\.|\+)' + escape(word.lower()) + r'(\_|\-|\.|\+)', '+', text, flags=I)
    text = text.replace('.', ' ').replace('-', ' ').replace('_', ' ').replace('+', '').replace(" Director's Cut", "").replace(" director's cut", "").replace("[Uncut]", "").replace("Uncut", "")

    text_split = text.split()
    if text_split and text_split[0].lower() in ("new:", "live:"):
        text_split.pop(0)  # remove annoying prefixes
    text = " ".join(text_split)

    if search(r'[Ss][0-9]+[Ee][0-9]+', text):
        text = sub(r'[Ss][0-9]+[Ee][0-9]+.*[a-zA-Z0-9_]+', '', text, flags=S | I)
    text = sub(r'\(.*\)', '', text).rstrip()  # remove episode number from series, like "series name (234)"

    # # List of bad strings to remove
    # bad_strings = [
        # "ae|", "al|", "ar|", "at|", "ba|", "be|", "bg|", "br|", "cg|", "ch|", "cz|", "da|", "de|", "dk|",
        # "ee|", "en|", "es|", "eu|", "ex-yu|", "fi|", "fr|", "gr|", "hr|", "hu|", "in|", "ir|", "it|", "lt|",
        # "mk|", "mx|", "nl|", "no|", "pl|", "pt|", "ro|", "rs|", "ru|", "se|", "si|", "sk|", "sp|", "tr|",
        # "uk|", "us|", "yu|",
        # "1080p-dual-lat-cine-calidad.com", "1080p-dual-lat-cine-calidad.com-1",
        # "1080p-dual-lat-cinecalidad.mx", "1080p-lat-cine-calidad.com", "1080p-lat-cine-calidad.com-1",
        # "1080p-lat-cinecalidad.mx", "1080p.dual.lat.cine-calidad.com", "3d", "'", "#", "[]",  # "/", "(", ")", "-",
        # "4k", "aac", "blueray", "ex-yu:", "fhd", "hd", "hdrip", "hindi", "imdb", "multi:", "multi-audio",
        # "multi-sub", "multi-subs", "multisub", "ozlem", "sd", "top250", "u-", "uhd", "vod", "x264"
    # ]

    # # Remove numbers from 1900 to 2030
    # bad_strings.extend(map(str, range(1900, 2030)))
    # # Construct a regex pattern to match any of the bad strings
    # bad_strings_pattern = re.compile('|'.join(map(re.escape, bad_strings)))
    # # Remove bad strings using regex pattern
    # text = bad_strings_pattern.sub('', text)
    # # List of bad suffixes to remove
    # bad_suffix = [
        # " al", " ar", " ba", " da", " de", " en", " es", " eu", " ex-yu", " fi", " fr", " gr", " hr", " mk",
        # " nl", " no", " pl", " pt", " ro", " rs", " ru", " si", " swe", " sw", " tr", " uk", " yu"
    # ]
    # # Construct a regex pattern to match any of the bad suffixes at the end of the string
    # bad_suffix_pattern = re.compile(r'(' + '|'.join(map(re.escape, bad_suffix)) + r')$')
    # # Remove bad suffixes using regex pattern
    # text = bad_suffix_pattern.sub('', text)
    # # Replace ".", "_", "'" with " "
    # text = re.sub(r'[._\']', ' ', text)

    text = text.partition("-")[0]

    text = remove_accents(text)

    text = text + 'FIN'
    text = re.sub(r'(odc.\s\d+)+.*?FIN', '', text)
    text = re.sub(r'(odc.\d+)+.*?FIN', '', text)
    text = re.sub(r'(\d+)+.*?FIN', '', text)
    text = text.partition("(")[0]
    text = re.sub(r"\\s\d+", "", text)
    text = re.sub('FIN', '', text)

    text = sanitize_filename(text)

    # forced
    text = text.replace('XXXXXX', '60')
    text = text.replace('brunobarbierix', 'bruno barbieri - 4 hotel')

    text = quote(text, safe="")
    return unquote(text).capitalize()


def convtextxx(text=''):
    try:
        if text is None:
            return  # Esci dalla funzione se text è None
        if text == '':
            return
        else:
            pass
            text = text.lower()
            text = text.lstrip()
            # #
            text = cutName(text)
            text = getCleanTitle(text)
            # #
            if text.endswith("the"):
                text = "the " + text[:-4]

            # text = re.sub(r'^\w{4}:', '', text)

            text_split = text.split()
            if text_split and text_split[0].lower() in ("new:", "live:"):
                text_split.pop(0)  # remove annoying prefixes
            text = " ".join(text_split)

            text = text.replace("\xe2\x80\x93", "").replace('\xc2\x86', '').replace('\xc2\x87', '')  # replace special
            text = text.replace('1^ visione rai', '').replace('1^ visione', ''.replace(' - prima tv', '')).replace('primatv', '')
            text = text.replace('prima visione', '').replace('1^tv', '').replace('1^ tv', '')
            text = text.replace('live:', '').replace('new:', '').replace('((', '(').replace('))', ')')
            if 'giochi olimpici parigi' in text:
                text = 'olimpiadi di parigi'
            if 'bruno barbieri' in text:
                text = text.replace('bruno barbieri', 'brunobarbierix')
            if "anni '60" in text:
                text = "anni 60"
            if 'tg regione' in text:
                text = 'tg3'
            if 'studio aperto' in text:
                text = 'studio aperto'
            if 'josephine ange gardien' in text:
                text = 'josephine ange gardien'
            if 'elementary' in text:
                text = 'elementary'
            if 'squadra speciale cobra 11' in text:
                text = 'squadra speciale cobra 11'
            if 'criminal minds' in text:
                text = 'criminal minds'
            if 'i delitti del barlume' in text:
                text = 'i delitti del barlume'
            if 'senza traccia' in text:
                text = 'senza traccia'
            if 'hudson e rex' in text:
                text = 'hudson e rex'
            if 'ben-hur' in text:
                text = 'ben-hur'
            if 'la7 ' in text:
                text = 'la7'
            if 'skytg24' in text:
                text = 'skytg24'
            # remove xx: at start
            text = re.sub(r'^\w{2}:', '', text)
            # remove xx|xx at start
            text = re.sub(r'^\w{2}\|\w{2}\s', '', text)
            # remove xx - at start
            text = re.sub(r'^.{2}\+? ?- ?', '', text)
            # remove all leading content between and including ||
            text = re.sub(r'^\|\|.*?\|\|', '', text)
            text = re.sub(r'^\|.*?\|', '', text)
            # remove everything left between pipes.
            text = re.sub(r'\|.*?\|', '', text)
            # remove all content between and including () multiple times
            text = re.sub(r'\(\(.*?\)\)|\(.*?\)', '', text)
            # remove all content between and including [] multiple times
            text = re.sub(r'\[\[.*?\]\]|\[.*?\]', '', text)
            # remove episode number in arabic series
            text = re.sub(r' +ح', '', text)
            # remove season number in arabic series
            text = re.sub(r' +ج', '', text)
            # remove season number in arabic series
            text = re.sub(r' +م', '', text)
            # List of bad strings to remove
            bad_strings = [
                "ae|", "al|", "ar|", "at|", "ba|", "be|", "bg|", "br|", "cg|", "ch|", "cz|", "da|", "de|", "dk|",
                "ee|", "en|", "es|", "eu|", "ex-yu|", "fi|", "fr|", "gr|", "hr|", "hu|", "in|", "ir|", "it|", "lt|",
                "mk|", "mx|", "nl|", "no|", "pl|", "pt|", "ro|", "rs|", "ru|", "se|", "si|", "sk|", "sp|", "tr|",
                "uk|", "us|", "yu|",
                "1080p", "1080p-dual-lat-cine-calidad.com", "1080p-dual-lat-cine-calidad.com-1",
                "1080p-dual-lat-cinecalidad.mx", "1080p-lat-cine-calidad.com", "1080p-lat-cine-calidad.com-1",
                "1080p-lat-cinecalidad.mx", "1080p.dual.lat.cine-calidad.com", "3d", "'", "#", "[]",  # "/", "(", ")", "-",
                "4k", "720p", "aac", "blueray", "ex-yu:", "fhd", "hd", "hdrip", "hindi", "imdb", "multi:", "multi-audio",
                "multi-sub", "multi-subs", "multisub", "ozlem", "sd", "top250", "u-", "uhd", "vod", "x264"
            ]

            # Remove numbers from 1900 to 2030
            bad_strings.extend(map(str, range(1900, 2030)))
            # Construct a regex pattern to match any of the bad strings
            bad_strings_pattern = re.compile('|'.join(map(re.escape, bad_strings)))
            # Remove bad strings using regex pattern
            text = bad_strings_pattern.sub('', text)
            # List of bad suffixes to remove
            bad_suffix = [
                " al", " ar", " ba", " da", " de", " en", " es", " eu", " ex-yu", " fi", " fr", " gr", " hr", " mk",
                " nl", " no", " pl", " pt", " ro", " rs", " ru", " si", " swe", " sw", " tr", " uk", " yu"
            ]
            # Construct a regex pattern to match any of the bad suffixes at the end of the string
            bad_suffix_pattern = re.compile(r'(' + '|'.join(map(re.escape, bad_suffix)) + r')$')
            # Remove bad suffixes using regex pattern
            text = bad_suffix_pattern.sub('', text)
            # Replace ".", "_", "'" with " "
            text = re.sub(r'[._\']', ' ', text)
            # recoded lulu
            text = text + 'FIN'
            '''
            if re.search(r'[Ss][0-9][Ee][0-9]+.*?FIN', text):
                text = re.sub(r'[Ss][0-9][Ee][0-9]+.*?FIN', '', text)
            if re.search(r'[Ss][0-9] [Ee][0-9]+.*?FIN', text):
                text = re.sub(r'[Ss][0-9] [Ee][0-9]+.*?FIN', '', text)
            '''
            text = re.sub(r'(odc.\s\d+)+.*?FIN', '', text)
            text = re.sub(r'(odc.\d+)+.*?FIN', '', text)
            text = re.sub(r'(\d+)+.*?FIN', '', text)
            text = text.partition("(")[0] + 'FIN'
            text = re.sub(r"\\s\d+", "", text)
            text = text.partition("(")[0]
            # text = text.partition(":")[0]  # not work on csi: new york (only-->  csi)
            text = text.partition(" -")[0]
            text = re.sub(' - +.+?FIN', '', text)  # all episodes and series ????
            text = re.sub('FIN', '', text)
            text = re.sub(r"[\<\>\:\"\/\\\|\?\*!]", "_", str(text))
            # text = re.sub(r'^\|[\w\-\|]*\|', '', text)
            text = re.sub(r"[-,?!+/\.\":]", '', text)  # replace (- or , or ! or / or . or " or :) by space
            # recoded  end
            text = text.strip(' -')

            text = remove_accents(text)

            # forced
            text = text.replace('XXXXXX', '60')
            text = text.replace('brunobarbierix', 'bruno barbieri - 4 hotel')
            text = quote(text, safe="")
        return unquote(text).capitalize()
    except Exception as e:
        pass
        pass


# =========================================================================
# GLOBAL BACKDROP DECODE LOCK:
# Prevent multiple GradientBackdropX instances from decoding the same file
# at the same time.
# =========================================================================
_BACKDROP_PATH_LOCK = threading.Lock()
_BACKDROP_ACTIVE_PATHS = set()

def _backdrop_acquire_path(path):
    if not path:
        return False
    with _BACKDROP_PATH_LOCK:
        if path in _BACKDROP_ACTIVE_PATHS:
            return False
        _BACKDROP_ACTIVE_PATHS.add(path)
        return True

def _backdrop_release_path(path):
    if not path:
        return
    with _BACKDROP_PATH_LOCK:
        _BACKDROP_ACTIVE_PATHS.discard(path)

def _backdrop_path_busy(path):
    if not path:
        return False
    with _BACKDROP_PATH_LOCK:
        return path in _BACKDROP_ACTIVE_PATHS


class BackdropDB(GradientBackdropXDownloadThread):
    def __init__(self):
        GradientBackdropXDownloadThread.__init__(self)
        self.logdbg = None
        self.pstcanal = None

        self._inflight = set()
        self._done = {}  # key -> (timestamp, ok)

        self._ok_ttl = 6 * 3600
        self._fail_ttl = 10 * 60

        self._lock = threading.Lock()

    def _event_key(self, canal, raw_title):
        return "%s::%s" % (_make_live_service(canal), (raw_title or "").strip().lower())

    def _should_skip_cached(self, key):
        now = time.time()
        with self._lock:
            if key in self._inflight:
                return True
            ts_ok = self._done.get(key)
            if ts_ok is not None:
                ts, ok = ts_ok
                ttl = self._ok_ttl if ok else self._fail_ttl
                if (now - ts) < ttl:
                    return True
                self._done.pop(key, None)
            self._inflight.add(key)
        return False

    def _mark_done(self, key, ok):
        now = time.time()
        with self._lock:
            self._inflight.discard(key)
            self._done[key] = (now, bool(ok))

    def _safe_call(self, func, *args):
        try:
            res = func(*args)
            if isinstance(res, tuple) and len(res) == 2:
                return res
            return False, "[ERROR] %s returned %r" % (getattr(func, '__name__', 'func'), res)
        except Exception as e:
            return False, "[ERROR] %s (%s)" % (getattr(func, '__name__', 'func'), e)

    def _is_latest(self, canal):
        latest_svc, _ts = get_live_latest()
        if latest_svc is None or latest_svc == '':
            return True
        try:
            return (canal[0] or '').strip() == latest_svc
        except Exception:
            return True

    def _latest_idle(self, min_idle=0.6):
        latest, ts = get_live_latest()
        if latest is None:
            return True
        try:
            return (time.time() - float(ts)) >= float(min_idle)
        except Exception:
            return True


    def _wait_until_idle(self, canal, min_idle, max_wait):
        """Wait until the user stayed on the current service long enough.

        Returns:
            True  -> idle reached
            False -> idle not reached within max_wait
            None  -> aborted because user changed service
        """
        try:
            start = time.time()
            while (time.time() - start) < float(max_wait):
                if not self._is_latest(canal):
                    return None
                if self._latest_idle(min_idle):
                    return True
                time.sleep(0.25)
            if not self._is_latest(canal):
                return None
            return bool(self._latest_idle(min_idle))
        except Exception:
            return False

    def run(self):
        self.logDB("[QUEUE] : Initialized")
        while True:
            item = pdb.get()
            if isinstance(item, tuple) and len(item) == 3:
                _prio, _ts, canal = item
            else:
                canal = item
            raw_title = (canal[2] or canal[5] or '')
            key = self._event_key(canal, raw_title)

            # drop if user already moved on
            if not self._is_latest(canal):
                pdb.task_done()
                continue

            if self._should_skip_cached(key):
                pdb.task_done()
                continue

            self.logDB("[QUEUE] : {} : {}-{} ({})".format(canal[0], canal[1], canal[2], raw_title))

            # Canonical slug for filenames (underscores) to avoid duplicates
            try:
                self.pstcanal = get_store_slug(raw_title)
            except Exception:
                self.pstcanal = get_canonical_slug(raw_title)

            if not self.pstcanal:
                self._mark_done(key, False)
                pdb.task_done()
                continue

            dwn_backdrop = os.path.join(path_folder, "%s.jpg" % self.pstcanal)


            # --- CUSTOM backdrop override (always wins) ---

            try:

                base = _storage_xtra_base()

                custom_b = os.path.join(base, "custom", "backdrop", "%s.jpg" % self.pstcanal)

                if os.path.exists(custom_b) and os.path.getsize(custom_b) > 0:

                    try:

                        shutil.copy2(custom_b, dwn_backdrop)

                    except Exception:

                        try:

                            with open(custom_b, "rb") as _fi, open(dwn_backdrop, "wb") as _fo:

                                _fo.write(_fi.read())

                        except Exception:

                            pass

                    try:

                        os.utime(dwn_backdrop, (time.time(), time.time()))

                    except Exception:

                        pass

                    try:

                        self.logDB("[SUCCESS : custom] %s -> %s" % (custom_b, dwn_backdrop))

                    except Exception:

                        pass

                    try:

                        bdb.task_done()

                    except Exception:

                        pass

                    continue

            except Exception:

                pass

            if os.path.exists(dwn_backdrop):
                try:
                    os.utime(dwn_backdrop, (time.time(), time.time()))
                except Exception:
                    pass
                self._mark_done(key, True)
                pdb.task_done()
                continue

            ok = False
            providers_tried = []
            import re as _re

            def _track(provider, logmsg):
                try:
                    status = 'unknown'
                    if isinstance(logmsg, str):
                        if '[SUCCESS' in logmsg:
                            status = 'success'
                        elif '[SKIP' in logmsg:
                            status = 'skip'
                        elif '[ERROR' in logmsg:
                            status = 'error'
                    url = None
                    if isinstance(logmsg, str):
                        m = _re.search(r'=>\s*(https?://\S+)', logmsg)
                        if m:
                            url = m.group(1)
                    providers_tried.append({'provider': provider, 'status': status, 'url': url, 'log': logmsg})
                except Exception:
                    providers_tried.append({'provider': provider, 'status': 'unknown', 'log': logmsg})

            # Provider order (live): honor overrides from GradientBackdropXDownloadThread
            try:
                providers = get_provider_override(raw_title)
            except Exception:
                providers = ["tmdb", "tvdb", "fanart", "imdb", "google"]

            # Run non-google providers first
            for p in providers:
                if ok or (not self._is_latest(canal)):
                    break
                if p == 'google':
                    continue
                try:
                    if p == 'tmdb':
                        val, log = self._safe_call(self.search_tmdb, dwn_backdrop, raw_title, canal[4], canal[3], canal[0])
                    elif p == 'tvdb':
                        val, log = self._safe_call(self.search_tvdb, dwn_backdrop, raw_title, canal[4], canal[3], canal[0])
                    elif p == 'fanart':
                        val, log = self._safe_call(self.search_fanart, dwn_backdrop, raw_title, canal[4], canal[3], canal[0])
                    elif p == 'imdb':
                        val, log = self._safe_call(self.search_imdb, dwn_backdrop, raw_title, canal[4], canal[3], canal[0])
                    else:
                        continue
                    self.logDB(log)
                    _track(p, log)
                    ok = os.path.exists(dwn_backdrop)
                except Exception as e:
                    _track(p, "[ERROR] %s" % e)


            nxts = canal[6] if (isinstance(canal, (list, tuple)) and len(canal) > 6) else 0
            google_attempted = False

            # Google strategy (only if enabled in provider list):
            # - Now (nxts==0): quick idle (0.6s)
            # - Next items (nxts>0): only if user stayed on the service longer (2.5s)
            if (not ok) and ('google' in providers) and self._is_latest(canal):
                if nxts in (0, '0', None):
                    if self._latest_idle(0.6):
                        val, log = self._safe_call(self.search_google, dwn_backdrop, raw_title, canal[4], canal[3], canal[0])
                        self.logDB(log)
                        _track('google', log)
                        ok = os.path.exists(dwn_backdrop)
                        google_attempted = True
                else:
                    idle_ok = self._wait_until_idle(canal, 2.5, 4.0)
                    if idle_ok is None:
                        # user moved away -> do not cache failure
                        with self._lock:
                            self._inflight.discard(key)
                        pdb.task_done()
                        continue
                    if idle_ok:
                        val, log = self._safe_call(self.search_google, dwn_backdrop, raw_title, canal[4], canal[3], canal[0])
                        self.logDB(log)
                        _track('google', log)
                        ok = os.path.exists(dwn_backdrop)
                        google_attempted = True

            # Persist backdrop_info (success or fail) for debugging
            try:
                slug = self.pstcanal
                if slug:
                    payload = {
                        'ts': int(time.time()),
                        'service': canal[0],
                        'event_ts': canal[1],
                        'title': raw_title,
                        'slug': slug,
                        'providers_tried': providers_tried,
                    }
                    if os.path.exists(dwn_backdrop):
                        payload['backdrop_file'] = dwn_backdrop
                    _write_backdrop_info_debug(slug, payload)
            except Exception:
                pass

            # If this was a NEXT item and we didn't attempt Google, do NOT cache failure.
            if (not ok) and (not google_attempted) and (nxts not in (0, '0', None)):
                with self._lock:
                    self._inflight.discard(key)
                pdb.task_done()
                continue

            # if user changed selection mid-run, do not cache as failure
            if (not ok) and (not self._is_latest(canal)):
                with self._lock:
                    self._inflight.discard(key)
                pdb.task_done()
                continue

            self._mark_done(key, ok)
            pdb.task_done()

    def logDB(self, logmsg):
        try:
            with open(_autodb_log_path('BackdropDB.log'), "a") as w:
                w.write("%s\n" % logmsg)
        except Exception:
            try:
                traceback.print_exc()
            except Exception:
                pass


threadDB = BackdropDB()
threadDB.start()



# --- Protected titles (evergreen shows) ---
# Titles (lowercase, accent-insensitive) that should NEVER be removed by AutoDB cleanup.
# You can extend this list safely. Matching is done against the file slug (convtext(title)).
PROTECTED_TITLES = {
    # Nachrichten/Talkshows
    "barbara salesch", "ulrich wetzel", "auf streife",
    "rtl aktuell", "punkt_6", "punkt_7", "punkt_8",
    "punkt_12", "punkt_9", "punkt_11",
    "tagesschau", "heute", "tagesthemen", "heute journal",
    "brisant", "explosiv", "rtl extra", "stern tv",
    
    # Frühstücksfernsehen
    "sat 1 frühstücksfernsehen", "frühstücksfernsehen",
    "moma", "morgenmagazin", "volle kanne",
    
    # Daily Soaps
    "gute zeiten schlechte zeiten", "gzsz",
    "unter uns", "alles was zählt", "rote rosen",
    "sturm der liebe", "lindenstraße", "verbotene liebe",
    "in aller freundschaft", "marienhof",
    "dahoam is dahoam", "watzmann ermittelt",
    
    # Gerichtsshows
    "das strafgericht", "barbara salesch", "ulrich wetzel",
    "richter alexander hold",
    
    # Wissenschaft
    "nano", "quarks", "galileo", "welt der wunder",
    
    # Weitere
    "wer weiß denn sowas", "wer weiss denn sowas",
    "gefragt gejagt", "quizduell",
}

def _norm_protected_key(s):
    try:
        s = remove_accents(s.lower())
    except Exception:
        try:
            s = s.lower()
        except Exception:
            return ""
    # keep only letters/numbers/spaces
    s = re.sub(r"[^a-z0-9\s\-]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# Precompute normalized slug keys
_PROTECTED_KEYS = set(_norm_protected_key(x) for x in PROTECTED_TITLES if x)


# Recording slug cache (rebuilt per AutoDB run)
_REC_SLUGS_CACHE = set()

def is_protected_file(path_or_name):
    """
    Decide if a file should be protected from cleanup based on its filename (slug).
    """
    try:
        name = os.path.basename(path_or_name)
        name = os.path.splitext(name)[0]
        try:
            if name in _REC_SLUGS_CACHE:
                return True
        except Exception:
            pass
        key = _norm_protected_key(name)
        # allow prefix match: "auf streife - die spezialisten" should protect under "auf streife"
        for p in _PROTECTED_KEYS:
            if not p:
                continue
            if key == p or key.startswith(p + " ") or key.startswith(p + "-"):
                return True
    except Exception:
        pass
    return False

RUN_TRIGGER_FILE = '/tmp/run_backdrop_autodb'
RUN_TRIGGER_FILE_ONCE = '/tmp/run_backdrop_autodb_once'

class BackdropAutoDB(GradientBackdropXDownloadThread):
    def __init__(self):
        GradientBackdropXDownloadThread.__init__(self)
        self.logdbg = None

    def _safe_call(self, func, *args):
        try:
            res = func(*args)
            if isinstance(res, tuple) and len(res) == 2:
                return res
            return False, "[ERROR] %s returned %r" % (getattr(func, '__name__', 'func'), res)
        except Exception as e:
            return False, "[ERROR] %s (%s)" % (getattr(func, '__name__', 'func'), e)

    def _wait_until_window_or_trigger(self):
        """Wait until 00:00/05:00 OR a trigger file exists.

        Returns:
            'time'      -> night window
            'trigger'   -> manual/boot trigger
        """
        while True:
            # manual trigger
            try:
                if os.path.exists(RUN_TRIGGER_FILE) or os.path.exists(RUN_TRIGGER_FILE_ONCE):
                    return 'trigger'
            except Exception:
                pass

            now = time.localtime()
            hour = now.tm_hour
            minute = now.tm_min
            if (hour == 0 or hour == 5) and minute == 0:
                return 'time'

            sleep_secs = 60 - now.tm_sec
            if sleep_secs < 5:
                sleep_secs = 5
            time.sleep(sleep_secs)

    def _wait_until_night_window(self):
        """Warten, bis es genau 00:00 oder 05:00 Uhr (Ortszeit) ist."""
        while True:
            now = time.localtime()
            hour = now.tm_hour
            minute = now.tm_min
            if (hour == 0 or hour == 5) and minute == 0:
                return
            sleep_secs = 60 - now.tm_sec
            if sleep_secs < 5:
                sleep_secs = 5
            time.sleep(sleep_secs)

    def run(self):
        self.logAutoDB("[AutoDB] *** Initialized (night mode 00:00 & 05:00, local time) ***")
        while True:
            self.logAutoDB("[AutoDB] Waiting for next run window (00:00 / 05:00, local time)")
            reason = self._wait_until_window_or_trigger()
            if reason == 'trigger':
                # clear trigger(s)
                try:
                    if os.path.exists(RUN_TRIGGER_FILE_ONCE):
                        os.remove(RUN_TRIGGER_FILE_ONCE)
                except Exception:
                    pass
                try:
                    if os.path.exists(RUN_TRIGGER_FILE):
                        os.remove(RUN_TRIGGER_FILE)
                except Exception:
                    pass
                self.logAutoDB('[AutoDB] *** Triggered run requested ***')
            self.logAutoDB("[AutoDB] *** Running ***")

            try:
                active, total = build_apdb_for_autodb()
                self.logAutoDB('[AutoDB] Active bouquets: %s' % ', '.join(active))
                self.logAutoDB('[AutoDB] Total services in apdb: %d' % int(total))
                _write_autodb_progress('backdrop', 0, total, state='running')
            except Exception as e:
                self.logAutoDB('[AutoDB] APDB build error: %s' % e)

            for _idx, service in enumerate(apdb.values()):
                # Stop support (requested by AutoDBManager)
                try:
                        if os.path.exists(STOP_AUTODB_FILE):
                                self.logAutoDB('[AutoDB] *** Stop requested ***')
                                break
                except Exception:
                        pass

                _write_autodb_progress('backdrop', _idx + 1, total, state='running')
                newfd = 0
                service_name = None
                try:
                    service_name = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
                    events = epgcache.lookupEvent(['IBDCTESX', (service, 0, -1, 1440)])
                    if not events:
                        self.logAutoDB("[AutoDB] 0 new file(s) added ({})".format(service_name or service))
                        continue

                    stop_loop = False
                    for evt in events:
                        # Stop support (requested by AutoDBManager)
                        try:
                                if os.path.exists(STOP_AUTODB_FILE):
                                        self.logAutoDB('[AutoDB] *** Stop requested ***')
                                        stop_loop = True
                                        break
                        except Exception:
                                pass

                        if evt[1] is None or evt[4] is None:
                            continue

                        raw_title = evt[4]
                        if not raw_title:
                            continue

                        slug = get_store_slug(raw_title)
                        if not slug:
                            continue
                        
                        dwn_backdrop = os.path.join(path_folder, "%s.jpg" % slug)

                        
                        # --- CUSTOM backdrop override (always wins, AutoDB) ---
                        
                        try:
                        
                            base = _storage_xtra_base()
                        
                            custom_b = os.path.join(base, "custom", "backdrop", "%s.jpg" % slug)
                        
                            if os.path.exists(custom_b) and os.path.getsize(custom_b) > 0:
                        
                                try:
                        
                                    shutil.copy2(custom_b, dwn_backdrop)
                        
                                except Exception:
                        
                                    try:
                        
                                        with open(custom_b, "rb") as _fi, open(dwn_backdrop, "wb") as _fo:
                        
                                            _fo.write(_fi.read())
                        
                                    except Exception:
                        
                                        pass
                        
                                try:
                        
                                    os.utime(dwn_backdrop, (time.time(), time.time()))
                        
                                except Exception:
                        
                                    pass
                        
                                try:
                        
                                    self.logAutoDB("[SUCCESS : custom] %s -> %s" % (custom_b, dwn_backdrop))
                        
                                except Exception:
                        
                                    pass
                        
                                continue
                        
                        except Exception:
                        
                            pass

                        if os.path.exists(dwn_backdrop):
                            os.utime(dwn_backdrop, (time.time(), time.time()))
                            continue
                        
                        shortdesc = evt[6] if len(evt) > 6 and evt[6] is not None else ''
                        fulldesc = evt[5] if len(evt) > 5 and evt[5] is not None else ''
                        
                        self.logAutoDB('[QUEUE] : %s : %s-%s (%s)' % (service_name, evt[1], raw_title, slug))
                        
                        providers_tried = []
                        import re as _re
                        try:
                            providers = get_provider_override(raw_title) or []
                        except Exception:
                            providers = []
                        if not providers:
                            mtype = _guess_media_type(service_name, raw_title, shortdesc, fulldesc)
                            if mtype == 'movie':
                                providers = ['tmdb', 'tvdb', 'fanart', 'imdb', 'google']
                            else:
                                providers = ['tvdb', 'tmdb', 'fanart', 'imdb', 'google']
                        
                        def _track(provider, logmsg):
                            try:
                                status = 'unknown'
                                if isinstance(logmsg, str):
                                    if '[SUCCESS' in logmsg:
                                        status = 'success'
                                    elif '[SKIP' in logmsg:
                                        status = 'skip'
                                    elif '[ERROR' in logmsg:
                                        status = 'error'
                                url = None
                                if isinstance(logmsg, str):
                                    m = _re.search(r'=>\s*(https?://\S+)', logmsg)
                                    if m:
                                        url = m.group(1)
                                providers_tried.append({'provider': provider, 'status': status, 'url': url, 'log': logmsg})
                            except Exception:
                                providers_tried.append({'provider': provider, 'status': 'unknown', 'log': logmsg})
                        
                        for p in providers:
                            if os.path.exists(dwn_backdrop):
                                break
                            if p == 'tvdb':
                                val, log = self._safe_call(self.search_tvdb, dwn_backdrop, raw_title, shortdesc, fulldesc, service_name)
                            elif p == 'tmdb':
                                val, log = self._safe_call(self.search_tmdb, dwn_backdrop, raw_title, shortdesc, fulldesc, service_name)
                            elif p == 'fanart':
                                val, log = self._safe_call(self.search_fanart, dwn_backdrop, raw_title, shortdesc, fulldesc, service_name)
                            elif p == 'imdb':
                                val, log = self._safe_call(self.search_imdb, dwn_backdrop, raw_title, shortdesc, fulldesc, service_name)
                            elif p == 'google':
                                val, log = self._safe_call(self.search_google, dwn_backdrop, raw_title, shortdesc, fulldesc, service_name)
                            else:
                                continue
                            _track(p, log)
                            self.logAutoDB(log)
                        
                        if os.path.exists(dwn_backdrop) and os.path.getsize(dwn_backdrop) > 0:
                            newfd += 1
                        
                        # Persist backdrop_info json (AutoDB)
                        try:
                            payload = {
                                'ts': int(time.time()),
                                'service': service_name,
                                'event_ts': evt[1],
                                'title': raw_title,
                                'slug': slug,
                                'providers_tried': providers_tried,
                            }
                            if os.path.exists(dwn_backdrop):
                                payload['backdrop_file'] = dwn_backdrop
                            _write_backdrop_info_debug(slug, payload)
                        except Exception as e:
                            self.logAutoDB('[AutoDB] backdrop_info json error: %s' % e)

                    if stop_loop:
                            break
                    # once per service (like PosterAutoDB)
                    self.logAutoDB("[AutoDB] {} new file(s) added ({})".format(newfd, service_name or service))

                except Exception as e:
                    self.logAutoDB("[AutoDB] *** service error : {} ({})".format(service, e))

            # cleanup (keep as before)
            now_tm = time.time()
            try:
                _REC_SLUGS_CACHE.clear()
                _REC_SLUGS_CACHE.update(_build_recording_slug_set())
                _refresh_recording_assets(_REC_SLUGS_CACHE, log_func=self.logAutoDB)
            except Exception:
                pass
            emptyfd = 0
            oldfd = 0
            for f in os.listdir(path_folder):
                fullpath = os.path.join(path_folder, f)
                try:
                    diff_tm = now_tm - os.path.getmtime(fullpath)
                    if diff_tm > 120 and os.path.getsize(fullpath) == 0:
                        os.remove(fullpath)
                        emptyfd += 1
                        continue
                    if diff_tm > 259200 and (not is_protected_file(fullpath)):
                        os.remove(fullpath)
                        oldfd += 1
                except Exception:
                    pass

            self.logAutoDB("[AutoDB] {} old file(s) removed".format(oldfd))
            self.logAutoDB("[AutoDB] {} empty file(s) removed".format(emptyfd))
            _write_autodb_progress('backdrop', total, total, state='finished')
            self.logAutoDB("[AutoDB] *** Job finished ***")
            # If we ran because of a manual trigger, don't block the scheduled night runs.
            # Short cooldown prevents tight loops if something keeps triggering.
            for _ in range(300):
                                try:
                                        if os.path.exists(RUN_TRIGGER_FILE) or os.path.exists(RUN_TRIGGER_FILE_ONCE):
                                                break
                                except Exception:
                                        pass
                                time.sleep(1)  # cooldown (interruptible)
    def logAutoDB(self, logmsg):
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(_autodb_log_path('BackdropAutoDB.log'), "a") as w:
                w.write("[{}] {}\n".format(timestamp, logmsg))
        except Exception:
            try:
                traceback.print_exc()
            except Exception:
                pass


threadAutoDB = BackdropAutoDB()
threadAutoDB.start()


class GradientBackdropX(Renderer):
        GUI_WIDGET = ePixmap

        def __init__(self):
                Renderer.__init__(self)
                self.nxts = 0
                self.canal = [None, None, None, None, None, None]
                self.oldCanal = None
                self.logdbg = None
                self._dbg_last_path = None
                self._dbg_last_title = None
                self._dbg_load_count = 0
                self._resolved_path = None
                self._resolved_slug = None
                self._dbg_changed_count = 0
                self._dbg_parent_name = None
                self._dbg_parent_id = None
                self._decode_delay_ms = 100
                self._dbg_pos_x = None
                self._waiting_path = None
                self._waitBackdropPath = None
                self._waitBackdropQueued = False
                self._waitBackdropLoops = 0
                self._loading_path = None
                self._decode_path = None
                self.picload = None
                self.picload_conn = None
                if not self.intCheck():
                       return
                self.timer = eTimer()
                self.timer.callback.append(self.showBackdrop)
                self.waitTimer = eTimer()
                self.waitTimer.callback.append(self.waitBackdrop)

        def applySkin(self, desktop, parent):
                attribs = []
                try:
                        self._dbg_parent_name = parent.__class__.__name__ if parent is not None else None
                        self._dbg_parent_id = id(parent) if parent is not None else None
                        self._dbg_pos_x = None
                        self._decode_delay_ms = 100
                        _backdropx_dbg("applySkin() self_id=%s parent=%s parent_id=%s skinAttributes=%s" % (
                                id(self),
                                repr(self._dbg_parent_name),
                                repr(self._dbg_parent_id),
                                repr(self.skinAttributes)
                        ))
                except Exception:
                        pass
                for (attrib, value,) in self.skinAttributes:
                        if attrib == "nexts":
                                self.nxts = int(value)
                        else:
                                attribs.append((attrib, value))
                                if attrib == 'position':
                                        try:
                                                self._dbg_pos_x = int(value[0])
                                        except Exception:
                                                pass
                try:
                        if self._dbg_parent_name == 'InfoBar' and self._dbg_pos_x is not None and self._dbg_pos_x >= 1000:
                                self._decode_delay_ms = 180
                        else:
                                self._decode_delay_ms = 100
                        _backdropx_dbg("applySkin() delay self_id=%s parent=%s pos_x=%s delay_ms=%s" % (
                                id(self),
                                repr(self._dbg_parent_name),
                                repr(self._dbg_pos_x),
                                repr(self._decode_delay_ms)
                        ))
                except Exception:
                        pass
                self.skinAttributes = attribs
                return Renderer.applySkin(self, desktop, parent)

        def intCheck(self):
                sock = False
                try:
                     import socket
                     socket.setdefaulttimeout(0.5)
                     socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
                     sock = True
                except:
                        sock = False
                return sock

        def postWidgetCreate(self, instance):
                Renderer.postWidgetCreate(self, instance)
                try:
                        self.picload = ePicLoad()
                        try:
                                self.picload_conn = self.picload.PictureData.connect(self._onPicDecoded)
                        except Exception:
                                self.picload.PictureData.get().append(self._onPicDecoded)
                except Exception as e:
                        self.picload = None
                        self.logBackdrop("Error (ePicLoad init) : " + str(e))

        def preWidgetRemove(self, instance):
                try:
                        if getattr(self, 'timer', None) is not None:
                                self.timer.stop()
                except Exception:
                        pass
                try:
                        if getattr(self, 'waitTimer', None) is not None:
                                self.waitTimer.stop()
                except Exception:
                        pass
                try:
                        self._clearPixmap()
                except Exception:
                        pass
                try:
                        Renderer.preWidgetRemove(self, instance)
                except Exception:
                        pass

        def _clearPixmap(self):
                try:
                        if self.instance is not None:
                                try:
                                        self.instance.setPixmap(None)
                                except Exception:
                                        pass
                                self.instance.hide()
                except Exception:
                        pass

        def _getDecodeSize(self):
                w = 0
                h = 0
                try:
                        sz = self.instance.size()
                        w = sz.width()
                        h = sz.height()
                except Exception:
                        try:
                                for (attrib, value) in getattr(self, 'skinAttributes', []):
                                        if attrib == 'size':
                                                try:
                                                        w, h = [int(x) for x in str(value).split(',')]
                                                except Exception:
                                                        w, h = value
                                                break
                        except Exception:
                                pass
                if w <= 0:
                        w = 300
                if h <= 0:
                        h = 169
                w = min(int(w), MAX_BACKDROP_W)
                h = min(int(h), MAX_BACKDROP_H)
                return int(w), int(h)

        def _startDecodePoster(self, pstrNm):
                if not self.instance or not pstrNm or not os.path.exists(pstrNm):
                        return False
                try:
                        self._clearPixmap()
                        self._decode_path = pstrNm
                        if self.picload is None:
                                self.picload = ePicLoad()
                                try:
                                        self.picload_conn = self.picload.PictureData.connect(self._onPicDecoded)
                                except Exception:
                                        self.picload.PictureData.get().append(self._onPicDecoded)
                        width, height = self._getDecodeSize()
                        sc = (1, 1)
                        try:
                                sc = AVSwitch().getFramebufferScale()
                        except Exception:
                                pass
                        try:
                                self.picload.setPara((width, height, sc[0], sc[1], False, 1, '#00000000'))
                        except Exception:
                                self.picload.setPara([width, height, sc[0], sc[1], False, 1, '#00000000'])
                        res = self.picload.startDecode(pstrNm)
                        try:
                                _backdropx_dbg("EPICLOAD START self_id=%s instance_id=%s nxts=%s path=%s size=%sx%s res=%s" % (
                                        id(self),
                                        id(self.instance) if self.instance is not None else None,
                                        self.nxts,
                                        repr(pstrNm),
                                        width,
                                        height,
                                        repr(res)
                                ))
                        except Exception:
                                pass
                        if res != 0:
                                self.logBackdrop("Error (startDecode) : %s (%s)" % (res, pstrNm))
                                self._decode_path = None
                                return False
                        return True
                except Exception as e:
                        self.logBackdrop("Error (ePicLoad decode) : " + str(e))
                        self._decode_path = None
                        return False

        def _onPicDecoded(self, picInfo=None):
                try:
                        if not self.instance or not self.picload or not self._decode_path:
                                return
                        ptr = self.picload.getData()
                        if ptr is None:
                                self.logBackdrop("Error (ePicLoad data) : %s" % repr(self._decode_path))
                                return
                        self.instance.setPixmap(ptr)
                        try:
                                self.instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
                        except Exception:
                                try:
                                        self.instance.setScale(1)
                                except Exception:
                                        pass
                        self.instance.show()
                        try:
                                self._dbg_last_path = self._decode_path
                                self._dbg_last_title = self.canal[2]
                                self._loading_path = None
                                self._waiting_path = None
                                _backdropx_dbg("EPICLOAD DONE self_id=%s instance_id=%s nxts=%s path=%s title=%s" % (
                                        id(self),
                                        id(self.instance) if self.instance is not None else None,
                                        self.nxts,
                                        repr(self._dbg_last_path),
                                        repr(self._dbg_last_title)
                                ))
                        except Exception:
                                pass
                except Exception as e:
                        self.logBackdrop("Error (ePicLoad callback) : " + str(e))
                finally:
                        self._decode_path = None

        def changed(self, what):
                if not self.instance:
                        return
                try:
                        self._dbg_changed_count += 1
                        _backdropx_dbg("changed() self_id=%s instance_id=%s parent=%s parent_id=%s nxts=%s count=%s what=%s source=%s" % (
                                id(self),
                                id(self.instance) if self.instance is not None else None,
                                repr(self._dbg_parent_name),
                                repr(self._dbg_parent_id),
                                self.nxts,
                                self._dbg_changed_count,
                                repr(what),
                                self.source.__class__.__name__ if self.source is not None else 'None'
                        ))
                except Exception:
                        pass
                if what[0] == self.CHANGED_CLEAR:
                        self._clearPixmap()
                        return
                servicetype = None
                try:
                        service = None
                        if isinstance(self.source, ServiceEvent):
                                service = self.source.getCurrentService()
                                servicetype = "ServiceEvent"
                        elif isinstance(self.source, CurrentService):
                                service = self.source.getCurrentServiceRef()
                                servicetype = "CurrentService"
                        elif isinstance(self.source, EventInfo):
                                servicetype = "EventInfo"
                                ev = getattr(self.source, 'event', None)
                                if ev is not None:
                                        try:
                                                service_ref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
                                                if service_ref:
                                                        self.canal[0] = ServiceReference(service_ref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
                                                else:
                                                        self.canal[0] = None
                                        except Exception:
                                                self.canal[0] = None
                                        try:
                                                self.canal[1] = ev.getBeginTime()
                                                self.canal[2] = ev.getEventName()
                                                self.canal[3] = ev.getExtendedDescription()
                                                self.canal[4] = ev.getShortDescription()
                                                qv = get_query_variants(self.canal[2], self.canal[4], self.canal[3])
                                                self.canal[5] = get_store_slug(qv.get('slug_title') or self.canal[2])
                                        except Exception:
                                                service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
                                        else:
                                                service = None
                                else:
                                        service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
                        elif isinstance(self.source, Event):
                                if self.nxts:
                                        service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
                                else:
                                        self.canal[0] = None
                                        self.canal[1] = self.source.event.getBeginTime()
                                        self.canal[2] = self.source.event.getEventName()
                                        self.canal[3] = self.source.event.getExtendedDescription()
                                        self.canal[4] = self.source.event.getShortDescription()
                                        qv = get_query_variants(self.canal[2], self.canal[4], self.canal[3])
                                        self.canal[5] = get_store_slug(qv.get('slug_title') or self.canal[2])
                                servicetype = "Event"
                        if service:
                                events = epgcache.lookupEvent(['IBDCTESX', (service.toString(), 0, -1, -1)])
                                self.canal[0] = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
                                self.canal[1] = events[self.nxts][1]
                                self.canal[2] = events[self.nxts][4]
                                self.canal[3] = events[self.nxts][5]
                                self.canal[4] = events[self.nxts][6]
                                qv = get_query_variants(self.canal[2], self.canal[4], self.canal[3])
                                self.canal[5] = get_store_slug(qv.get('slug_title') or self.canal[2])
                except Exception as e:
                        self.logBackdrop("Error (service) : " + str(e))
                        self._clearPixmap()
                        return
                if not servicetype:
                        self.logBackdrop("Error service type undefined")
                        self._clearPixmap()
                        return
                try:
                        curCanal = "{}-{}".format(self.canal[1], self.canal[2])
                        try:
                                _backdropx_dbg("changed() RESOLVED self_id=%s instance_id=%s nxts=%s servicetype=%s canal=%s oldCanal=%s slug=%s" % (
                                        id(self),
                                        id(self.instance) if self.instance is not None else None,
                                        self.nxts,
                                        servicetype,
                                        repr(curCanal),
                                        repr(self.oldCanal),
                                        repr(self.canal[5])
                                ))
                        except Exception:
                                pass
                        same_canal = (curCanal == self.oldCanal)
                        self.logBackdrop("Service : {} [{}] : {} : {}".format(servicetype, self.nxts, self.canal[0], curCanal))
                        resolved_path, resolved_slug = _resolve_existing_backdrop_path(self.canal[2], self.canal[4], self.canal[3], self.canal[5])
                        pstrNm = resolved_path or (path_folder + self.canal[5] + ".jpg")
                        if same_canal:
                                if os.path.exists(pstrNm) and os.path.getsize(pstrNm) > 0:
                                        try:
                                                _backdropx_dbg("changed() SKIP same canal nxts=%s canal=%s" % (self.nxts, repr(curCanal)))
                                        except Exception:
                                                pass
                                        return
                                try:
                                        _backdropx_dbg("changed() SAME canal but missing file -> retry nxts=%s canal=%s path=%s" % (self.nxts, repr(curCanal), repr(pstrNm)))
                                except Exception:
                                        pass
                        self.oldCanal = curCanal
                        self._resolved_path = pstrNm
                        self._resolved_slug = resolved_slug or self.canal[5]
                        try:
                                _backdropx_dbg("changed() PATH nxts=%s title=%s path=%s exists=%s size=%s resolved_slug=%s base_slug=%s" % (
                                        self.nxts,
                                        repr(self.canal[2]),
                                        repr(pstrNm),
                                        os.path.exists(pstrNm),
                                        os.path.getsize(pstrNm) if os.path.exists(pstrNm) else -1,
                                        repr(resolved_slug),
                                        repr(self.canal[5])
                                ))
                        except Exception:
                                pass
                        if os.path.exists(pstrNm) and os.path.getsize(pstrNm) > 0:
                                self._waiting_path = None
                                self._waitBackdropPath = None
                                self._waitBackdropQueued = False
                                try:
                                        self.waitTimer.stop()
                                except Exception:
                                        pass
                                try:
                                        _backdropx_dbg("changed()->timer.start nxts=%s delay=%s path=%s" % (self.nxts, getattr(self, '_decode_delay_ms', 100), repr(pstrNm)))
                                except Exception:
                                        pass
                                self.timer.start(getattr(self, '_decode_delay_ms', 100), True)
                        else:
                                canal = self.canal[:]
                                try:
                                        _backdropx_dbg("changed()->queue/waitBackdrop nxts=%s path=%s canal=%s waiting_path=%s" % (self.nxts, repr(pstrNm), repr(canal), repr(self._waiting_path)))
                                except Exception:
                                        pass
                                # Hide stale poster immediately while waiting for a new file.
                                self._clearPixmap()
                                self._dbg_last_path = None
                                self._dbg_last_title = None
                                if self._waiting_path == pstrNm and self._waitBackdropQueued:
                                        try:
                                                _backdropx_dbg("changed()->SKIP duplicate waitBackdrop nxts=%s path=%s" % (self.nxts, repr(pstrNm)))
                                        except Exception:
                                                pass
                                        return
                                self._waiting_path = pstrNm
                                self._waitBackdropPath = pstrNm
                                self._waitBackdropQueued = True
                                self._waitBackdropLoops = 180
                                pdb.put(canal)
                                self.waitTimer.start(500, True)
                except Exception as e:
                        self.logBackdrop("Error (eFile) : " + str(e))
                        self._clearPixmap()
                        return

        def showBackdrop(self):
                try:
                        _backdropx_dbg("showBackdrop() ENTER self_id=%s instance_id=%s parent=%s parent_id=%s nxts=%s canal=%s oldCanal=%s" % (
                                id(self),
                                id(self.instance) if self.instance is not None else None,
                                repr(self._dbg_parent_name),
                                repr(self._dbg_parent_id),
                                self.nxts,
                                repr(self.canal),
                                repr(self.oldCanal)
                        ))
                except Exception:
                        pass
                if self.canal[5]:
                        pstrNm = getattr(self, '_resolved_path', None) or (path_folder + self.canal[5] + ".jpg")
                        if os.path.exists(pstrNm) and os.path.getsize(pstrNm) > 0:
                                if self._dbg_last_path == pstrNm and self._decode_path is None:
                                        try:
                                                _backdropx_dbg("SKIP LOADJPG same path nxts=%s path=%s title=%s" % (
                                                        self.nxts,
                                                        repr(pstrNm),
                                                        repr(self.canal[2])
                                                ))
                                        except Exception:
                                                pass
                                        try:
                                                self.instance.show()
                                        except Exception:
                                                pass
                                        self._waiting_path = None
                                        self._waitBackdropPath = None
                                        self._waitBackdropQueued = False
                                        return
                                self.logBackdrop("[LOAD : showBackdrop] {}".format(pstrNm))
                                try:
                                        self._dbg_load_count += 1
                                        self._loading_path = pstrNm
                                        _backdropx_dbg("LOADJPG BEFORE self_id=%s instance_id=%s nxts=%s count=%s path=%s size=%s old_path=%s old_title=%s" % (
                                                id(self),
                                                id(self.instance) if self.instance is not None else None,
                                                self.nxts,
                                                self._dbg_load_count,
                                                repr(pstrNm),
                                                os.path.getsize(pstrNm) if os.path.exists(pstrNm) else -1,
                                                repr(self._dbg_last_path),
                                                repr(self._dbg_last_title)
                                        ))
                                except Exception:
                                        pass
                                if not self._startDecodePoster(pstrNm):
                                        try:
                                                self._clearPixmap()
                                                self.instance.setPixmap(loadJPG(pstrNm))
                                                try:
                                                        self.instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
                                                except Exception:
                                                        self.instance.setScale(1)
                                                self.instance.show()
                                                self._dbg_last_path = pstrNm
                                                self._dbg_last_title = self.canal[2]
                                                self._loading_path = None
                                                self._waiting_path = None
                                                self._waitBackdropPath = None
                                                self._waitBackdropQueued = False
                                                try:
                                                        _backdropx_dbg("LOADJPG AFTER nxts=%s path=%s title=%s" % (
                                                                self.nxts,
                                                                repr(self._dbg_last_path),
                                                                repr(self._dbg_last_title)
                                                        ))
                                                except Exception:
                                                        pass
                                        except Exception as e:
                                                self.logBackdrop("Error (fallback loadJPG) : " + str(e))
                        else:
                                self._clearPixmap()
                                self._dbg_last_path = None
                                self._dbg_last_title = None

        def waitBackdrop(self):
                pstrNm = self._waitBackdropPath
                if not pstrNm:
                        self._waitBackdropQueued = False
                        return
                if not self._waitBackdropQueued:
                        return
                if self._waitBackdropLoops == 180:
                        self.logBackdrop("[LOOP : waitBackdrop] {}".format(pstrNm))
                        try:
                                _backdropx_dbg("waitBackdrop() ENTER nxts=%s path=%s" % (self.nxts, repr(pstrNm)))
                        except Exception:
                                pass
                if os.path.exists(pstrNm) and os.path.getsize(pstrNm) > 0:
                        self._waitBackdropQueued = False
                        self._waitBackdropLoops = 0
                        self._waiting_path = None
                        self._waitBackdropPath = None
                        try:
                                _backdropx_dbg("waitBackdrop() FOUND nxts=%s path=%s -> timer.start(%s)" % (self.nxts, repr(pstrNm), getattr(self, '_decode_delay_ms', 100)))
                        except Exception:
                                pass
                        self.timer.start(getattr(self, '_decode_delay_ms', 100), True)
                        return
                self._waitBackdropLoops -= 1
                if self._waitBackdropLoops <= 0:
                        self._waitBackdropQueued = False
                        self._waiting_path = None
                        self._waitBackdropPath = None
                        try:
                                _backdropx_dbg("waitBackdrop() TIMEOUT nxts=%s path=%s" % (self.nxts, repr(pstrNm)))
                        except Exception:
                                pass
                        self._clearPixmap()
                        self._dbg_last_path = None
                        self._dbg_last_title = None
                        return
                self.waitTimer.start(500, True)

        def logBackdrop(self, logmsg):
            try:
                _backdropx_dbg(str(logmsg))
            except Exception:
                pass
            return





