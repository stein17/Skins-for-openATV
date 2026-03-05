#!/usr/bin/python3
# -*- coding: utf-8 -*-
# GradientPosterX.py - patched build (progress + live bouquets + stream filter)
# NOTE: this header is sanitized to avoid IndentationError from stray text lines.

# by digiteng...07.2021,
# 08.2021(stb lang support),
# 09.2021 mini fixes
# © Provided that digiteng rights are protected, all or part of the code can be used, modified...
# russian and py3 support by sunriser...
# downloading in the background while zaping...
# by beber...03.2022,
# 03.2022 several enhancements : several renders with one queue thread, google search (incl. molotov for france) + autosearch & autoclean thread ...

# 06.24 @stein17, Created new info!
# 02.26 @stein17, Many new features and improvements
#Infobar
    #Poster now
    #<widget source="session.Event_Now" render="GradientPosterX" nexts="0" position="10,285" cornerRadius="6" size="170,255" zPosition="100" scale="stretch"/>
    #Poster next
    #<widget source="session.CurrentService" render="GradientPosterX" nexts="1" position="1100,285" cornerRadius="6" size="170,255" zPosition="100" scale="stretch"/>
    #Backdrop now
    #<widget source="session.CurrentService" render="GradientBackdropX" nexts="1" position="800,375" cornerRadius="6" size="290,164" zPosition="98" scale="stretch"/>
    #Backdrop next
    #<widget source="session.Event_Now" render="GradientBackdropX" nexts="0" position="190,375" cornerRadius="6" size="290,164" zPosition="98" scale="stretch"/>

#Channel Selection Poster
    #<widget source="ServiceEvent" render="GradientPosterX" nexts="0" position="750,385" delayPic="0" usedImage="poster" cornerRadius="6" size="170,255" zPosition="100" />
    #<widget source="ServiceEvent" render="GradientPosterX" nexts="1" ...
    #<widget source="ServiceEvent" render="GradientPosterX" nexts="2" ...
#Channel Selection Backdrop
    #<widget source="ServiceEvent" render="GradientBackdropX" nexts="0" position="750,500" delayPic="0" usedImage="backdrop" cornerRadius="6" size="170,96" zPosition="98" />
    #<widget source="ServiceEvent" render="GradientBackdropX" nexts="1" ...
    #<widget source="ServiceEvent" render="GradientBackdropX" nexts="2" ...
#Channel Selection Event
    #<widget source="ServiceEvent" render="GradientNxtEvntX"  snglEvent="0" nxtEvents="" font="Regular; 14" position="750,642" size="170,32" valign="center" halign="left" zPosition="5" backgroundColor="background" transparent="1" Wrap="1" />
    #<widget source="ServiceEvent" render="GradientNxtEvntX"  snglEvent="1" nxtEvents="" ...
    #<widget source="ServiceEvent" render="GradientNxtEvntX"  snglEvent="2" nxtEvents="" ...

#EPG
    #<widget source="Event" render="GradientPosterX" position="310,415" cornerRadius="6" size="170,255" zPosition="100" />
    #<widget source="Event" render="GradientBackdropX" position="310,500" cornerRadius="6" size="170,96" zPosition="98" />

#Movie,EMC Selection
    #<widget source="Service" render="GradientPosterX" position="825,506" cornerRadius="6" size="110,164" zPosition="100" />
    #<widget source="Service" render="GradientBackdropX" position="974,506" cornerRadius="6" size="290,164" zPosition="98" />

#Player
    #<widget source="session.Event_Now" render="GradientPosterX" position="10,325" cornerRadius="6" size="170,255" zPosition="100" />
    #<widget source="session.Event_Now" render="GradientBackdropX" position="210,415" cornerRadius="6" size="290,164" zPosition="98" />
    
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
    

from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, eTimer, loadJPG, eEPGCache, BT_HALIGN_CENTER, BT_VALIGN_CENTER, BT_KEEP_ASPECT_RATIO, BT_SCALE
from ServiceReference import ServiceReference
from Components.config import config
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.CurrentService import CurrentService
from Components.Sources.EventInfo import EventInfo
from Components.Sources.Event import Event
from Components.Renderer.GradientPosterXDownloadThread import GradientPosterXDownloadThread, get_store_slug, get_provider_override, is_daily_series, get_query_variants, try_upgrade_poster_from_info, _allow_google
import NavigationInstance
import os
import sys
import socket
import re
import shutil
import time
import json
import datetime
import unicodedata
import traceback

STOP_AUTODB_FILE = '/tmp/stop_poster_autodb'



# =========================================================================
# RECORDING ASSET PROTECTION (keep posters/backdrops/json for recordings)
# =========================================================================
# AutoDB (live-TV) downloads a lot of temporary artwork. Cleaning after 3 days
# is correct for LIVE cache, but NOT for recordings: if a recording exists on
# disk we want to keep its poster/backdrop/info JSON for months.
#
# How it works:
# - Scan movie/recording directories and compute the same slug used by EMC/xtra
#   (GradientConverlibr.convtext + apply_title_mapping).
# - Before cleanup, touch (utime) the matching poster/backdrop/json files so
#   they will NOT be removed by the 3-day cleanup.
#
# Optional config file to add custom recording directories:
#   /etc/enigma2/xtra_recording_dirs.conf
# One path per line.

RECORDING_PROTECT_CONF = '/etc/enigma2/xtra_recording_dirs.conf'

try:
    from .GradientConverlibr import convtext as _xtra_convtext, apply_title_mapping as _xtra_apply_title_mapping
except Exception:
    try:
        from GradientConverlibr import convtext as _xtra_convtext, apply_title_mapping as _xtra_apply_title_mapping
    except Exception:
        _xtra_convtext = None
        _xtra_apply_title_mapping = None

_RECORDING_EXTS = ('.ts', '.mkv', '.mp4', '.avi', '.mpeg', '.mpg', '.m2ts', '.mov', '.wmv')


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

    # enigma2 movielist config (if available)
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

    # fallback default movie path
    try:
        up = getattr(config, 'usage', None)
        if up is not None and hasattr(up, 'default_path'):
            p = up.default_path.value
            if p:
                dirs.add(str(p))
    except Exception:
        pass

    # common defaults
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
    # Robust base selection: prefer existing xtra dirs (avoid false RW detection)
    for p in ("/media/hdd/xtra", "/media/usb/xtra", "/media/mmc/xtra"):
        try:
            if os.path.isdir(p):
                return p
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
                low = fn.lower()
                if not low.endswith(_RECORDING_EXTS):
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


def _wait_for_poster(path, timeout=12.0):
    try:
        end = time.time() + float(timeout)
        while time.time() < end:
            if path and os.path.exists(path) and os.path.getsize(path) > 1024:
                return True
            time.sleep(0.1)
    except Exception:
        pass
    return False

def _poster_info_trusted(slug, title=None):
    try:
        if not store_slug:
            return False
        base = _storage_xtra_base()
        info_dir = os.path.join(base, "poster_info")
        jf = os.path.join(info_dir, slug + ".json")
        if not os.path.exists(jf):
            return False
        data = json.load(open(jf))
        source = data.get("source") or data.get("last_provider")
        providers = data.get("providers_tried") or []
        if not source:
            for it in providers:
                if it.get("status") == "success":
                    source = it.get("provider")
                    break
        if source in ("tmdb", "tvdb", "imdb", "fanart", "omdb", "custom"):
            return True
        if source == "google":
            try:
                if title and is_daily_series(title):
                    return False
            except Exception:
                pass
            return True
        return False
    except Exception:
        return False


def _refresh_recording_assets(slugs, log_func=None):
    """Touch poster/backdrop/json for recordings so they survive 3-day cleanup."""
    base = _storage_xtra_base()
    poster_dir = os.path.join(base, 'poster')
    backdrop_dir = os.path.join(base, 'backdrop')
    info_dir = os.path.join(base, 'Info')

    touched = 0
    for slug in slugs:
        if not store_slug:
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
        path = _autodb_progress_path('PosterAutoDB.progress.json')
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
    """Merge debug payload into existing poster_info json without dropping cached URLs."""
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


def _write_poster_info_debug(store_slug, payload):
    """Write provider-trace info but keep existing poster_url/source intact."""
    if not store_slug:
        return False
    try:
        base = _storage_xtra_base()
        poster_info_dir = os.path.join(base, 'poster_info')
        os.makedirs(poster_info_dir, exist_ok=True)
        out_path = os.path.join(poster_info_dir, store_slug + '.json')
        return _merge_info_payload(out_path, payload)
    except Exception:
        return False
PY3 = (sys.version_info[0] == 3)
try:
        if PY3:
                import queue
                from _thread import start_new_thread
                import Queue
                from thread import start_new_thread
except:
        pass

epgcache = eEPGCache.getInstance()

try:
        from Components.config import config
        lng = config.osd.language.value
except:
        lng = None
        pass

apdb = dict()
#
# AUTOMATISCHE POSTER-GENERIERUNG (AutoDB)
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
                print("[PosterAutoDB] error reading bouquets.tv:", e)
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
                print("[PosterAutoDB] error reading bouquet %s: %s" % (bouquet_file, e))


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
                print("[PosterAutoDB] error reading bouquet name %s: %s" % (bouquet_file, e))
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
                print("[PosterAutoDB] bouquet config read error:", e)

# 3) Neue Konfigurationsdatei mit Anleitung schreiben
try:
        with open(autodb_bouquets_file, 'w') as f:
                f.write("# ==============================================\n")
                f.write("#  Poster-AutoDB Bouquets\n")
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
                                # Beispiel: 1|userbouquet.dbe27.tv  #NAME HD+(TV)
                                f.write("%s|%s  #NAME %s\n" % (flag, b_id, bname))
                        else:
                                f.write("%s|%s\n" % (flag, b_id))
except Exception as e:
        print("[PosterAutoDB] bouquet config write error:", e)

# 4) APDB (ServiceRefs) wird NICHT mehr beim Import gebaut.
#    Stattdessen wird APDB im AutoDB-Thread bei einem Lauf erzeugt.


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



def isMountedInRW(mount_point):
    with open("/proc/mounts", "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) > 1 and parts[1] == mount_point:
                return True
    return False


cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')
noposter = "/usr/share/enigma2/%s/main/noposter.jpg" % cur_skin
path_folder = "/media/usb/xtra/poster/"
if os.path.exists("/media/hdd"):
    if isMountedInRW("/media/hdd"):
        path_folder = "/media/hdd/xtra/poster/"
elif os.path.exists("/media/usb"):
    if isMountedInRW("/media/usb"):
        path_folder = "/media/usb/xtra/poster/"
elif os.path.exists("/media/mmc"):
    if isMountedInRW("/media/mmc"):
        path_folder = "/media/mmc/xtra/poster/"

if not os.path.exists(path_folder):
    os.makedirs(path_folder)


REGEX = re.compile(
                r'\s\*\d{4}\Z|'                                 # remove ( *1234)
                r'([\(\[\|].*?[\)\]\|])|'               # remove ([xxx] or (xxx) or |xxx|)
#               r'(\s{1,}\:\s{1,}).+|'                  # remove ( : xxx)
                r'(\.\s{1,}\").+|'                              # remove (. "xxx)
                r'(\?\s{1,}\").+|'                              # remove (? "xxx)
                r'(\.{2,}\Z)'                                   # remove (..)
                , re.DOTALL)


def convtext(text):
        text = text.replace('\xc2\x86', '')
        text = text.replace('\xc2\x87', '')
        text = REGEX.sub('', text)
        text = re.sub(r"[-,!/\.\":]", ' ', text)  # replace (- or , or ! or / or . or " or :) by space
        text = re.sub(r'\s{1,}', ' ', text)             # replace multiple space by one space
        text = text.strip()

        try:
                text = unicode(text, 'utf-8')
        except NameError:
                pass
        text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")
        text = text.lower()
        return str(text)


def _guess_media_type(service_name, title, shortdesc='', fulldesc=''):
        """Heuristic: decide 'movie' vs 'tv' for provider order.

        We keep it conservative: default is 'tv' to avoid harming series,
        but movie channels and strong movie hints force 'movie'.
        """
        try:
                s = (service_name or '').lower()
                t = (title or '').lower()
                blob = ' '.join([(title or ''), (shortdesc or ''), (fulldesc or '')]).lower()

                # movie-channel hints
                if any(k in s for k in ['sky cinema', 'cinema', 'movie', 'film', 'kino']):
                        return 'movie'

                # strong TV-series hints
                if any(k in blob for k in ['staffel', 'episode', 'folge', 's0', 'e0', 'season']):
                        return 'tv'

                # daily magazines / news tend to be TV formats
                if any(k in t for k in ['punkt', 'tagesschau', 'heute journal', 'sport', 'news']):
                        return 'tv'

                # sequels on movie channels already covered; keep default
        except Exception:
                pass
        return 'tv'


if PY3:
        pdb = queue.LifoQueue()
else:
        pdb = Queue.LifoQueue()


class PosterDB(GradientPosterXDownloadThread):
    def __init__(self):
        GradientPosterXDownloadThread.__init__(self)
        # Logging aktivieren
        self.logdbg = True
        self.logdbg_verbose = False  # set True to get PosterDB_debug.log
        # de-dup within a short window (prevents double queue entries)
        self._seen_keys = {}  # key -> last_ts
        self._seen_ttl = 120  # seconds
        self._cooldown_fail = {}  # (service,slug)->last_fail_ts
        self._cooldown_ttl = 180  # seconds


    def _safe_call(self, func, *args):
        try:
            res = func(*args)
            if isinstance(res, tuple) and len(res) == 2:
                return res
            return False, "[ERROR] %s returned %s" % (getattr(func, "__name__", "func"), res)
        except Exception as e:
            return False, "[ERROR] %s (%s)" % (getattr(func, "__name__", "func"), e)

    def run(self):
        self.logDB("[QUEUE] : Initialized")
        while True:
            canal = pdb.get()
            now = int(time.time())
            self.logDB("[QUEUE] : {} : {}-{} ({})".format(canal[0], canal[1], canal[2], canal[2]))
            # Use stable store slug derived from a canonical title (prevents duplicates)
            # event_slug (canal[5]) may include episode/subtitle; keep it only for logging.
            event_slug = canal[5]

            # Build query plan (DE first, then ORIGINAL fallback) and a stable slug-title
            qv = {}
            try:
                qv = get_query_variants(canal[2], canal[4], canal[3])
            except Exception:
                qv = {}
            slug_title = (qv.get("slug_title") or canal[2] or "").strip()
            store_slug = (qv.get('base_slug') or get_store_slug(slug_title)) if slug_title else get_store_slug(canal[2])

            # v17 queue slug: show stable store_slug for custom/diagnostics
            self.logDB("[QUEUE] : {} : {}-{} ({})".format(canal[0], canal[1], canal[2], store_slug))

            if store_slug == "unknown":
                self.logDB("[SKIP : slug] unknown for %s" % (canal[2] or ""))
                try:
                    pdb.task_done()
                except Exception:
                    pass
                continue


            # De-dup: avoid re-searching the same store_slug repeatedly (scrolling causes spam)
            key = (canal[0], store_slug)
            last = self._seen_keys.get(key)
            if last and (now - last) < self._seen_ttl:
                # Only skip duplicates if the target poster already exists.
                # If the file is missing (deleted/custom rebuild), do NOT skip.
                try:
                    _dup_target = path_folder + store_slug + ".jpg"
                    if os.path.exists(_dup_target):
                        self.logDB("[SKIP dup] %s:%s (%ss)" % (canal[0], store_slug, now-last))
                        try:
                            pdb.task_done()
                        except Exception:
                            pass
                        continue
                except Exception:
                    # fallback to original behavior on unexpected errors
                    self.logDB("[SKIP dup] %s:%s (%ss)" % (canal[0], store_slug, now-last))
                    try:
                        pdb.task_done()
                    except Exception:
                        pass
                    continue
            self._seen_keys[key] = now

            # v17 cooldown: avoid hammering providers for recently-failed slugs
            lf = self._cooldown_fail.get((canal[0], store_slug))
            if lf and (now - lf) < self._cooldown_ttl:
                self.logDB("[SKIP cooldown] %s:%s (%ss)" % (canal[0], store_slug, now-lf))
                try:
                    pdb.task_done()
                except Exception:
                    pass
                continue


            dwn_poster = path_folder + store_slug + ".jpg"



            # --- CUSTOM poster override (always wins) ---


            try:


                base = _storage_xtra_base()


                custom_p = os.path.join(base, "custom", "poster", store_slug + ".jpg")


                if os.path.exists(custom_p) and os.path.getsize(custom_p) > 0:


                    try:


                        shutil.copy2(custom_p, dwn_poster)


                    except Exception:


                        try:


                            with open(custom_p, "rb") as _fi, open(dwn_poster, "wb") as _fo:


                                _fo.write(_fi.read())


                        except Exception:


                            pass


                    try:


                        os.utime(dwn_poster, (time.time(), time.time()))


                    except Exception:


                        pass


                    try:


                        self.logDB("[SUCCESS : custom] %s -> %s" % (custom_p, dwn_poster))


                    except Exception:


                        pass


                    try:


                        pdb.task_done()


                    except Exception:


                        pass


                    continue


            except Exception:


                pass

            # Prevent duplicate parallel work on same store_slug (scrolling can enqueue repeatedly)
            _lock = None
            try:
                _slug = store_slug
                _lock = "/tmp/posterx_%s.lock" % _slug
                _now = time.time()
                if os.path.exists(_lock):
                    try:
                        if (_now - os.path.getmtime(_lock)) < 45:
                            self.logDB("[SKIP] inflight slug=%s" % _slug)
                            pdb.task_done()
                            continue
                        else:
                            os.remove(_lock)
                    except Exception:
                        pass
                try:
                    with open(_lock, "w") as f:
                        f.write(str(int(_now)))
                except Exception:
                    pass
            except Exception:
                _lock = None

            de_queries = qv.get("de_queries") or [slug_title or canal[2]]
            orig_queries = qv.get("orig_queries") or []
            hint = qv.get("hint") or "tv"

            # Provider order (live queue): honor overrides from GradientPosterXDownloadThread
            try:
                providers = (qv.get('providers_override') or get_provider_override(slug_title or canal[2], canal[4], canal[3]))
            except Exception:
                providers = ["tmdb", "tvdb", "fanart", "imdb", "google", "omdb"]

            # v17: Google is opt-in only (prevents many wrong posters)
            try:
                if 'google' in providers and not _allow_google():
                    providers = [p for p in providers if p != 'google']
            except Exception:
                pass

            # Live UI speed: keep poster provider chain lean.
            # - fanart/omdb are not useful for poster images here
            # - google is disabled in Live to avoid UI stalls; keep it for AutoDB
            try:
                providers = [p for p in providers if p not in ('fanart','omdb')]
                providers = [p for p in providers if p != 'google']
            except Exception:
                pass
            try:
                self.logDB('[PLAN] providers=%s' % ','.join(providers))
            except Exception:
                pass

            self.logDBG("[QUEUE poster] service=%s event_ts=%s store_slug=%s event_slug=%s hint=%s raw_title=%s slug_title=%s de=%s orig=%s reason=%s rule=%s providers=%s" % (
                canal[0], canal[1], store_slug, event_slug, hint, repr(canal[2]), repr(slug_title), repr(de_queries), repr(orig_queries), qv.get("reason",""), qv.get('rule_id',''), " > ".join(providers)
            ))
            if os.path.exists(dwn_poster):
                if _poster_info_trusted(store_slug, canal[2]):
                    os.utime(dwn_poster, (time.time(), time.time()))
                else:
                    try:
                        os.remove(dwn_poster)
                    except Exception:
                        pass

            # Prefer TMDb from /xtra/Info when available to keep Poster/Backdrop consistent
            info_used = False
            info_log = None
            info_url = None
            info_tmdb_id = None
            try:
                base = _storage_xtra_base()
                info_json = os.path.join(base, "Info", store_slug + ".json")
                poster_path = ""
                info_data = {}
                if os.path.exists(info_json):
                    try:
                        info_data = json.load(open(info_json))
                    except Exception:
                        info_data = {}
                    poster_path = (info_data.get("poster_path") or "")
                    if poster_path:
                        info_url = "https://image.tmdb.org/t/p/original" + poster_path
                        info_tmdb_id = info_data.get("tmdb_id") or info_data.get("id")
                pinfo = os.path.join(base, "poster_info", store_slug + ".json")
                src = None
                if os.path.exists(pinfo):
                    try:
                        src = json.load(open(pinfo)).get("source")
                    except Exception:
                        src = None
                if info_url:
                    if (not os.path.exists(dwn_poster)) or (src not in ("tmdb", "tmdb_info")):
                        if try_upgrade_poster_from_info(store_slug, dwn_poster):
                            try:
                                os.utime(dwn_poster, (time.time(), time.time()))
                            except Exception:
                                pass
                            info_used = True
                            info_log = "[SUCCESS : tmdb] %s (via Info.json)" % (slug_title or canal[2])
                            newfd = newfd + 1
                    elif os.path.exists(dwn_poster) and (src in ("tmdb", "tmdb_info")):
                        info_used = True
                        info_log = "[CACHE : tmdb] %s (via Info.json)" % (slug_title or canal[2])
            except Exception:
                pass
            # Provider order already computed above (providers)

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
                    providers_tried.append({
                        'provider': provider,
                        'status': status,
                        'url': url,
                        'log': logmsg
                    })
                except Exception:
                    providers_tried.append({'provider': provider, 'status': 'unknown', 'log': logmsg})

            # Prefer TMDb first when Info JSON is present
            if info_url and ('tmdb' in providers):
                providers = ['tmdb'] + [p for p in providers if p != 'tmdb']

            if info_used and info_log:
                self.logDB(info_log)
                _track('tmdb', info_log)

            # Provider loop (stop at first successful download)
            # pass context to provider implementations
            try:
                self.store_slug = store_slug
                self._expected_media_type = 'movie' if hint == 'movie' else 'tv'
            except Exception:
                pass
            for p in (providers if not info_used else []):
                if os.path.exists(dwn_poster):
                    break
                tried = []
                last_err = None
                success = False

                def _try_provider(query_title):
                    if p == 'tmdb':
                        return self._safe_call(self.search_tmdb, dwn_poster, query_title, canal[4], canal[3], canal[0], slug_title)
                    elif p == 'tvdb':
                        return self._safe_call(self.search_tvdb, dwn_poster, query_title, canal[4], canal[3], canal[0], slug_title)
                    elif p == 'fanart':
                        return self._safe_call(self.search_fanart, dwn_poster, query_title, canal[4], canal[3], canal[0], slug_title)
                    elif p == 'imdb':
                        return self._safe_call(self.search_imdb, dwn_poster, query_title, canal[4], canal[3], canal[0], slug_title)
                    elif p == 'google':
                        return self._safe_call(self.search_google, dwn_poster, query_title, canal[4], canal[3], canal[0], slug_title)
                    elif p == 'omdb':
                        return self._safe_call(self.search_omdb, dwn_poster, query_title, canal[4], canal[3], canal[0], slug_title)
                    else:
                        return False, "[SKIP : %s] unknown provider" % p

                # Try DE queries first, then ORIGINAL fallback
                for lang, queries in (('de', de_queries), ('orig', orig_queries)):
                    for q in (queries or []):
                        tried.append(q)
                        self.logDBG("[TRY] provider=%s lang=%s query=%s slug=%s" % (p, lang, repr(q), store_slug))
                        val, log = _try_provider(q)
                        _track(p, log)
                        if isinstance(log, str) and "[ERROR" in log:
                            last_err = log
                        if val or os.path.exists(dwn_poster):
                            # One success line is enough (keep PosterDB.log like BackdropDB.log)
                            if isinstance(log, str) and log.strip():
                                self.logDB(log)
                            success = True
                            break
                    if success:
                        break

                if success:
                    break

                # Provider failed: log a single summary line (avoid per-query spam)
                if last_err:
                    self.logDB(last_err)
                else:
                    # show at most 3 tried queries
                    tshow = tried[:3]
                    more = "" if len(tried) <= 3 else ", ..."
                    self.logDB("[SKIP : %s] Not found (tried: %s%s)" % (p, ", ".join(tshow), more))
                        # v17: remember failures for cooldown
            try:
                if not os.path.exists(dwn_poster):
                    self._cooldown_fail[(canal[0], store_slug)] = int(time.time())
            except Exception:
                pass

            try:
                if store_slug:
                    payload = {
                        'ts': int(time.time()),
                        'service': canal[0],
                        'event_ts': canal[1],
                        'title': canal[2],
                        'slug': store_slug,
                        'providers_tried': providers_tried,
                        'query_plan': qv,
                    }
                    if os.path.exists(dwn_poster):
                        payload['poster_file'] = dwn_poster
                    if info_used and info_url:
                        payload['source'] = 'tmdb'
                        payload['url'] = info_url
                        if info_tmdb_id is not None:
                            payload['tmdb_id'] = info_tmdb_id
                    _write_poster_info_debug(store_slug, payload)
            except Exception as e:
                self.logDB("[ERROR] poster_info json (%s)" % e)
            try:
                if _lock and os.path.exists(_lock):
                    os.remove(_lock)
            except Exception:
                pass
            pdb.task_done()

    def logDB(self, logmsg):
        """Write *user-facing* PosterDB.log lines (kept minimal like BackdropDB.log)."""
        import traceback
        if not self.logdbg:
            return
        try:
            with open(_autodb_log_path('PosterDB.log'), 'a') as w:
                w.write('%s\n' % logmsg)
        except Exception as e:
            print('PosterDB log error:', e)
            try:
                traceback.print_exc()
            except Exception:
                pass

    def logDBG(self, logmsg):
        """Verbose debug log (optional; disabled by default)."""
        import traceback
        if not getattr(self, 'logdbg_verbose', False):
            return
        try:
            ts = time.strftime('%Y-%m-%d %H:%M:%S')
            with open(_autodb_log_path('PosterDB_debug.log'), 'a') as w:
                w.write('%s %s\n' % (ts, logmsg))
        except Exception as e:
            print('PosterDB debug log error:', e)
            try:
                traceback.print_exc()
            except Exception:
                pass


threadDB = PosterDB()
threadDB.start()

RUN_TRIGGER_FILE = '/tmp/run_poster_autodb'
RUN_TRIGGER_FILE_ONCE = '/tmp/run_poster_autodb_once'

class PosterAutoDB(GradientPosterXDownloadThread):
        def __init__(self):
                GradientPosterXDownloadThread.__init__(self)
                self.logdbg = None

        def _safe_call(self, func, *args):
                try:
                        res = func(*args)
                        if isinstance(res, tuple) and len(res) == 2:
                                return res
                        return False, "[ERROR] %s returned %s" % (getattr(func, "__name__", "func"), res)
                except Exception as e:
                        return False, "[ERROR] %s (%s)" % (getattr(func, "__name__", "func"), e)

        def _wait_until_window_or_trigger(self):
                """Wait until 00:00/05:00 OR trigger file exists."""
                while True:
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
                """
                Warten, bis es genau 00:00 oder 05:00 Uhr (Ortszeit) ist.
                """
                while True:
                        now = time.localtime()  # lokale Zeit der Box
                        hour = now.tm_hour
                        minute = now.tm_min
                        if (hour == 0 or hour == 5) and minute == 0:
                                return
                        # bis zur nächsten Minute schlafen
                        sleep_secs = 60 - now.tm_sec
                        if sleep_secs < 5:
                                sleep_secs = 5
                        time.sleep(sleep_secs)

        def run(self):
                self.logAutoDB("[AutoDB] *** Initialized (night mode 00:00 & 05:00) ***")
                while True:
                        self.logAutoDB("[AutoDB] Waiting for next run window (00:00 / 05:00, local time)")
                        reason = self._wait_until_window_or_trigger()
                        if reason == 'trigger':
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
                        processed_slugs = set()
                        # AUTO ADD NEW FILES - 1440 (24 hours ahead)
                        try:
                                active, total = build_apdb_for_autodb()
                                self.logAutoDB('[AutoDB] Active bouquets: %s' % ', '.join(active))
                                self.logAutoDB('[AutoDB] Total services in apdb: %d' % int(total))
                                _write_autodb_progress('poster', 0, total, state='running')
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

                                _write_autodb_progress('poster', _idx + 1, total, state='running')
                                try:
                                        events = epgcache.lookupEvent(["IBDCTESX", (service, 0, -1, 1440)])
                                        newfd = 0
                                        newcn = None
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

                                                canal = [None, None, None, None, None, None]
                                                canal[0] = ServiceReference(service).getServiceName().replace("\xc2\x86", "").replace("\xc2\x87", "")
                                                if evt[1] is None or evt[4] is None:
                                                        continue
                                                else:
                                                        canal[1] = evt[1]
                                                        canal[2] = evt[4]
                                                        canal[3] = evt[5]
                                                        canal[4] = evt[6]
                                                        # Build query plan (DE -> ORIGINAL) + apply series rules for stable store_slug
                                                        qv = {}
                                                        try:
                                                                qv = get_query_variants(canal[2], canal[4], canal[3])
                                                        except Exception:
                                                                qv = {}
                                                        slug_title = (qv.get('slug_title') or canal[2] or '').strip()
                                                        de_queries = qv.get('de_queries') or [slug_title or canal[2]]
                                                        orig_queries = qv.get('orig_queries') or []
                                                        canal[5] = (qv.get('base_slug') or get_store_slug(slug_title) or get_store_slug(canal[2]))
                                                        store_slug = canal[5]
                                                        if store_slug == "unknown":
                                                                self.logAutoDB("[SKIP : slug] unknown for %s" % (canal[2] or ""))
                                                                continue
                                                        try:
                                                                if store_slug in processed_slugs:
                                                                        continue
                                                                processed_slugs.add(store_slug)
                                                        except Exception:
                                                                pass
                                                        try:
                                                                self.store_slug = store_slug
                                                        except Exception:
                                                                pass
                                                        dwn_poster = path_folder + store_slug + ".jpg"
                                                        # --- CUSTOM poster override (highest priority) ---
                                                        try:
                                                                base = _storage_xtra_base()
                                                                custom_dir = os.path.join(base, "custom", "poster")
                                                                # candidate slugs: store_slug + base-title slug
                                                                cand = []
                                                                if store_slug:
                                                                        cand.append(store_slug)
                                                                try:
                                                                        _rt = canal[2] or ""
                                                                        _bt = _rt
                                                                        for sep in [" - ", " – ", ":", " — "]:
                                                                                if sep in _bt:
                                                                                        _bt = _bt.split(sep, 1)[0]
                                                                                        break
                                                                        _bt_slug = _slugify(_bt)
                                                                        if _bt_slug and _bt_slug not in cand:
                                                                                cand.append(_bt_slug)
                                                                except Exception:
                                                                        pass
                                                                custom_src = None
                                                                custom_used_slug = None
                                                                for _s in cand:
                                                                        p = os.path.join(custom_dir, _s + ".jpg")
                                                                        if os.path.exists(p) and os.path.getsize(p) > 0:
                                                                                custom_src = p
                                                                                custom_used_slug = _s
                                                                                break
                                                                if custom_src:
                                                                        try:
                                                                                shutil.copy2(custom_src, dwn_poster)
                                                                        except Exception:
                                                                                # fallback copy
                                                                                try:
                                                                                        with open(custom_src, "rb") as _fi, open(dwn_poster, "wb") as _fo:
                                                                                                _fo.write(_fi.read())
                                                                                except Exception:
                                                                                        pass
                                                                        _write_poster_info_debug(store_slug, {
                                                                                "provider": "custom",
                                                                                "custom_slug": custom_used_slug,
                                                                                "custom_path": custom_src,
                                                                                "updated": int(time.time())
                                                                        })
                                                                        os.utime(dwn_poster, (time.time(), time.time()))
                                                                        continue
                                                        except Exception:
                                                                pass

                                                        if os.path.exists(dwn_poster):
                                                                if _poster_info_trusted(store_slug, canal[2]):
                                                                        os.utime(dwn_poster, (time.time(), time.time()))
                                                                        continue
                                                                else:
                                                                        try:
                                                                                os.remove(dwn_poster)
                                                                        except Exception:
                                                                                pass
                                                        # Prefer TMDb from /xtra/Info when available to keep Poster/Backdrop consistent
                                                        info_used = False
                                                        info_log = None
                                                        info_url = None
                                                        info_tmdb_id = None
                                                        try:
                                                            base = _storage_xtra_base()
                                                            info_json = os.path.join(base, "Info", store_slug + ".json")
                                                            poster_path = ""
                                                            info_data = {}
                                                            if os.path.exists(info_json):
                                                                try:
                                                                    info_data = json.load(open(info_json))
                                                                except Exception:
                                                                    info_data = {}
                                                                poster_path = (info_data.get("poster_path") or "")
                                                                if poster_path:
                                                                    info_url = "https://image.tmdb.org/t/p/original" + poster_path
                                                                    info_tmdb_id = info_data.get("tmdb_id") or info_data.get("id")
                                                            pinfo = os.path.join(base, "poster_info", store_slug + ".json")
                                                            src = None
                                                            if os.path.exists(pinfo):
                                                                try:
                                                                    src = json.load(open(pinfo)).get("source")
                                                                except Exception:
                                                                    src = None
                                                            if info_url:
                                                                if (not os.path.exists(dwn_poster)) or (src not in ("tmdb", "tmdb_info")):
                                                                    if try_upgrade_poster_from_info(store_slug, dwn_poster):
                                                                        try:
                                                                            os.utime(dwn_poster, (time.time(), time.time()))
                                                                        except Exception:
                                                                            pass
                                                                        info_used = True
                                                                        info_log = "[SUCCESS : tmdb] %s (via Info.json)" % (slug_title or canal[2])
                                                                        newfd = newfd + 1
                                                                elif os.path.exists(dwn_poster) and (src in ("tmdb", "tmdb_info")):
                                                                    info_used = True
                                                                    info_log = "[CACHE : tmdb] %s (via Info.json)" % (slug_title or canal[2])
                                                        except Exception:
                                                            pass

                                                        # Provider order (AutoDB) with overrides + media_type heuristic
                                                        self.logAutoDB('[QUEUE] : %s : %s-%s (%s)' % (canal[0], canal[1], canal[2], canal[5]))
                                                        providers_tried = []
                                                        import re as _re
                                                        try:
                                                                providers = (qv.get('providers_override') or get_provider_override(canal[2], canal[4], canal[3]) or [])
                                                        except Exception:
                                                                providers = []
                                                        if not providers:
                                                                mtype = _guess_media_type(canal[0], canal[2], canal[4], canal[3])
                                                                if mtype == 'movie':
                                                                        providers = ['tmdb', 'tvdb', 'fanart', 'imdb', 'google', 'omdb']
                                                                else:
                                                                        providers = ['tvdb', 'tmdb', 'fanart', 'imdb', 'google', 'omdb']
                                                        # v17: Google opt-in only
                                                        try:
                                                                if 'google' in providers and not _allow_google():
                                                                        providers = [p for p in providers if p != 'google']
                                                        except Exception:
                                                                pass

                                                        # Keep provider chain lean (AutoDB can keep google as last resort if enabled).
                                                        try:
                                                                providers = [p for p in providers if p not in ('fanart','omdb')]
                                                        except Exception:
                                                                pass
                                                        
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
                                                        
                                                        # Prefer TMDb first when Info JSON is present
                                                        if info_url and ('tmdb' in providers):
                                                                providers = ['tmdb'] + [p for p in providers if p != 'tmdb']

                                                        if info_used and info_log:
                                                                self.logAutoDB(info_log)
                                                                _track('tmdb', info_log)

                                                        for p in (providers if not info_used else []):
                                                        
                                                                if os.path.exists(dwn_poster):
                                                        
                                                                        break
                                                        
                                                                def _try_provider(query_title):
                                                        
                                                                        if p == 'tmdb':
                                                        
                                                                                return self._safe_call(self.search_tmdb, dwn_poster, query_title, canal[4], canal[3], canal[0])
                                                        
                                                                        elif p == 'tvdb':
                                                        
                                                                                return self._safe_call(self.search_tvdb, dwn_poster, query_title, canal[4], canal[3], canal[0])
                                                        
                                                                        elif p == 'fanart':
                                                        
                                                                                return self._safe_call(self.search_fanart, dwn_poster, query_title, canal[4], canal[3], canal[0])
                                                        
                                                                        elif p == 'imdb':
                                                        
                                                                                return self._safe_call(self.search_imdb, dwn_poster, query_title, canal[4], canal[3], canal[0])
                                                        
                                                                        elif p == 'google':
                                                        
                                                                                return self._safe_call(self.search_google, dwn_poster, query_title, canal[4], canal[3], canal[0])
                                                        
                                                                        elif p == 'omdb':
                                                        
                                                                                return self._safe_call(self.search_omdb, dwn_poster, query_title, canal[4], canal[3], canal[0])
                                                        
                                                                        else:
                                                        
                                                                                return (False, "[SKIP : %s] unknown provider" % p)
                                                        
                                                        
                                                        
                                                                # DE queries
                                                        
                                                                for q in de_queries:
                                                        
                                                                        self.logAutoDB("[TRY] provider=%s lang=de query=%s slug=%s" % (p, repr(q), store_slug))
                                                        
                                                                        val, log = _try_provider(q)
                                                        
                                                                        _track(p, log)
                                                        
                                                                        self.logAutoDB(log)
                                                        
                                                                        if val and _wait_for_poster(dwn_poster):
                                                        
                                                                                newfd = newfd + 1
                                                        
                                                                                break
                                                        
                                                                if os.path.exists(dwn_poster) and os.path.getsize(dwn_poster) > 0:
                                                        
                                                                        break
                                                        
                                                        
                                                        
                                                                # ORIGINAL fallback
                                                        
                                                                for q in orig_queries:
                                                        
                                                                        self.logAutoDB("[TRY] provider=%s lang=orig query=%s slug=%s" % (p, repr(q), store_slug))
                                                        
                                                                        val, log = _try_provider(q)
                                                        
                                                                        _track(p, log)
                                                        
                                                                        self.logAutoDB(log)
                                                        
                                                                        if val and _wait_for_poster(dwn_poster):
                                                        
                                                                                newfd = newfd + 1
                                                        
                                                                                break
                                                        
                                                                if os.path.exists(dwn_poster) and os.path.getsize(dwn_poster) > 0:
                                                        
                                                                        break
                                                        
                                                        
                                                        
                                                        # FR-only sources (between IMDb and final Google)
                                                        if lng == 'fr_FR':
                                                                if not os.path.exists(dwn_poster):
                                                                        val, log = self._safe_call(self.search_molotov_google, dwn_poster, canal[2], canal[4], canal[3], canal[0])
                                                                        _track('molotov', log)
                                                                        self.logAutoDB(log)
                                                                        if os.path.exists(dwn_poster) and os.path.getsize(dwn_poster) > 0:
                                                                                newfd = newfd + 1
                                                                if not os.path.exists(dwn_poster):
                                                                        val, log = self._safe_call(self.search_programmetv_google, dwn_poster, canal[2], canal[4], canal[3], canal[0])
                                                                        _track('programmetv', log)
                                                                        self.logAutoDB(log)
                                                                        if os.path.exists(dwn_poster) and os.path.getsize(dwn_poster) > 0:
                                                                                newfd = newfd + 1
                                                        
                                                        # Persist poster_info json (AutoDB)
                                                        try:
                                                                if store_slug:
                                                                        payload = {
                                                                                'ts': int(time.time()),
                                                                                'service': canal[0],
                                                                                'event_ts': canal[1],
                                                                                'title': canal[2],
                                                                                'slug': store_slug,
                                                                                'providers_tried': providers_tried,
                        'query_plan': qv,
                                                                        }
                                                                        if os.path.exists(dwn_poster):
                                                                                payload['poster_file'] = dwn_poster
                                                                        if info_used and info_url:
                                                                                payload['source'] = 'tmdb'
                                                                                payload['url'] = info_url
                                                                                if info_tmdb_id is not None:
                                                                                        payload['tmdb_id'] = info_tmdb_id
                                                                        _write_poster_info_debug(store_slug, payload)
                                                        except Exception as e:
                                                                self.logAutoDB('[AutoDB] poster_info json error: %s' % e)
                                                newcn = canal[0]
                                        if stop_loop:
                                                break
                                        self.logAutoDB("[AutoDB] {} new file(s) added ({})".format(newfd, newcn))
                                except Exception as e:
                                        self.logAutoDB("[AutoDB] *** service error : {} ({})".format(service, e))
                        # AUTO REMOVE OLD FILES
                        now_tm = time.time()
                        try:
                                _rec_slugs = _build_recording_slug_set()
                                _refresh_recording_assets(_rec_slugs, log_func=self.logAutoDB)
                        except Exception:
                                _rec_slugs = set()
                        emptyfd = 0
                        oldfd = 0
                        for f in os.listdir(path_folder):
                                fullpath = os.path.join(path_folder, f)
                                try:
                                        diff_tm = now_tm - os.path.getmtime(fullpath)
                                        if diff_tm > 120 and os.path.getsize(fullpath) == 0:  # Detect empty files > 2 minutes
                                                os.remove(fullpath)
                                                emptyfd += 1
                                        # Detect old files > 3 days old (keep if used by recordings)
                                        try:
                                                _stem = os.path.splitext(os.path.basename(fullpath))[0]
                                                _is_rec = (_stem in _rec_slugs)
                                        except Exception:
                                                _is_rec = False
                                        if diff_tm > 259200 and (not _is_rec):
                                                os.remove(fullpath)
                                                oldfd += 1
                                except Exception as e:
                                        self.logAutoDB("[AutoDB] *** file cleanup error for {}: {}".format(fullpath, e))
                        self.logAutoDB("[AutoDB] {} old file(s) removed".format(oldfd))
                        self.logAutoDB("[AutoDB] {} empty file(s) removed".format(emptyfd))
                        _write_autodb_progress('poster', total, total, state='finished')
                        self.logAutoDB("[AutoDB] *** Job finished ***")
                        # cooldown (max 300s) but wake immediately if a trigger appears
                        for _ in range(300):
                            try:
                                if os.path.exists(RUN_TRIGGER_FILE) or os.path.exists(RUN_TRIGGER_FILE_ONCE):
                                    break
                            except Exception:
                                pass
                            time.sleep(1)

        def logAutoDB(self, logmsg):
            try:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(_autodb_log_path('PosterAutoDB.log'), "a") as w:
                    w.write("[{}] {}\n".format(timestamp, logmsg))
            except Exception as e:
                print("logAutoDB error: {}".format(e))
                traceback.print_exc()


threadAutoDB = PosterAutoDB()
threadAutoDB.start()

class GradientPosterX(Renderer):
        def __init__(self):
                Renderer.__init__(self)
                self.nxts = 0
                self.canal = [None, None, None, None, None, None]
                self.oldCanal = None
                self.logdbg = None
                if not self.intCheck():
                       return
                self.timer = eTimer()
                self.timer.callback.append(self.showPoster)

        def applySkin(self, desktop, parent):
                attribs = []
                for (attrib, value,) in self.skinAttributes:
                        if attrib == "nexts":
                                self.nxts = int(value)
                        else:
                                attribs.append((attrib, value))
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

        GUI_WIDGET = ePixmap

        def changed(self, what):
                if not self.instance:
                        return
                if what[0] == self.CHANGED_CLEAR:
                        self.instance.hide()
                if what[0] != self.CHANGED_CLEAR:
                        servicetype = None
                        try:
                                service = None
                                if isinstance(self.source, ServiceEvent):  # source="ServiceEvent"
                                        service = self.source.getCurrentService()
                                        servicetype = "ServiceEvent"
                                elif isinstance(self.source, CurrentService):  # source="session.CurrentService"
                                        service = self.source.getCurrentServiceRef()
                                        servicetype = "CurrentService"
                                elif isinstance(self.source, EventInfo):  # source="session.Event_Now" or source="session.Event_Next"
                                        # IMPORTANT: use the event provided by the source (NOW vs NEXT)
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
                                elif isinstance(self.source, Event):  # source="Event"
                                        if self.nxts:
                                                service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
                                        else:
                                                self.canal[0] = None
                                                self.canal[1] = self.source.event.getBeginTime()
                                                self.canal[2] = self.source.event.getEventName()
                                                self.canal[3] = self.source.event.getExtendedDescription()
                                                self.canal[4] = self.source.event.getShortDescription()
                                                # Use canonical slug for filenames (underscores) to avoid duplicates
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
                                        # Use canonical slug for filenames (underscores) to avoid duplicates
                                        qv = get_query_variants(self.canal[2], self.canal[4], self.canal[3])

                                        self.canal[5] = get_store_slug(qv.get('slug_title') or self.canal[2])
                        except Exception as e:
                                self.logPoster("Error (service) : " + str(e))
                                self.instance.hide()
                                return
                        if not servicetype:
                                self.logPoster("Error service type undefined")
                                self.instance.hide()
                                return
                        try:
                                curCanal = "{}-{}".format(self.canal[1], self.canal[2])
                                if curCanal == self.oldCanal:
                                        return
                                self.oldCanal = curCanal
                                self.logPoster("Service : {} [{}] : {} : {}".format(servicetype, self.nxts, self.canal[0], self.oldCanal))
                                pstrNm = path_folder + self.canal[5] + ".jpg"
                                if os.path.exists(pstrNm):
                                        self.timer.start(100, True)
                                else:
                                        canal = self.canal[:]
                                        pdb.put(canal)
                                        start_new_thread(self.waitPoster, ())
                        except Exception as e:
                                self.logPoster("Error (eFile) : " + str(e))
                                self.instance.hide()
                                return

        def showPoster(self):
                self.instance.hide()
                if self.canal[5]:
                        pstrNm = path_folder + self.canal[5] + ".jpg"
                        if os.path.exists(pstrNm):
                                self.logPoster("[LOAD : showPoster] {}".format(pstrNm))
                                self.instance.setPixmap(loadJPG(pstrNm))
                                try:  # some images do not support .setPixmapScaleFlags
                                        self.instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
                                except Exception:  # use old .setScale(1) instead
                                        self.instance.setScale(1)
                                self.instance.show()

        def waitPoster(self):
                self.instance.hide()
                if self.canal[5]:
                        pstrNm = path_folder + self.canal[5] + ".jpg"
                        loop = 180
                        found = None
                        self.logPoster("[LOOP : waitPoster] {}".format(pstrNm))
                        while loop >= 0:
                                if os.path.exists(pstrNm):
                                        if os.path.getsize(pstrNm) > 0:
                                                loop = 0
                                                found = True
                                time.sleep(0.5)
                                loop = loop - 1
                        if found:
                                self.timer.start(10, True)

        def logPoster(self, logmsg):
            return


#try:
    #folder_size=sum([sum(map(lambda fname: os.path.getsize(os.path.join(path_folder, fname)), files)) for path_folder, folders, files in os.walk(path_folder)])
    #posters_sz = "%0.f" % (folder_size/(1024*1024.0))
    #if posters_sz >= "100":    # folder remove size(100MB)...
        #import shutil
        #shutil.rmtree(path_folder)
#except:
    #pass


