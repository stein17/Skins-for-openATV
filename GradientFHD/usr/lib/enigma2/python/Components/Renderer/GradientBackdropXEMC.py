# OPTIMIERTE VERSION - GradientBackdropXEMC.py
# Verbessert: 2024-12-15
# 02.26 @stein17, Many new features and improvements
# 
# Für EMC (Enhanced Movie Center), Movie Player, Movieliste
# Zeigt Backdrops für Aufnahmen (.ts, .mkv, .mp4, .avi, etc.)
#
# Verbesserungen:
# - TITLE_MAPPINGS Integration
# - TMDb w1280 Backdrop (statt w500)
# - JSON-Speicherung mit backdrop_path
# - Besseres Error-Handling


"""
2. NEUE GradientBackdropXEMC.py
================================

Fuer Backdrop bei Aufnahmen/Filmen (EMC, Movie Player, Movieliste)

FEATURES:
- Gleiche Logik wie GradientPosterXEMC.py
- TITLE_MAPPINGS Integration
- JSON-Speicherung fuer Rating/FSK
- TMDb + OMDb + FanArt Suche
- Backdrop w1280 Aufloesung

SKIN.XML BEISPIELE:
<!-- EMC Selection -->
<widget source="Service" render="GradientBackdropXEMC" position="10,100" size="600,337" zPosition="3" alphatest="blend" />

<!-- Movie Player -->
<widget source="session.CurrentService" render="GradientBackdropXEMC" position="0,0" size="1280,720" zPosition="1" alphatest="blend" />
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
    from .GradientConverlibr import convtext, cutName, apply_title_mapping
except:
    from GradientConverlibr import convtext, cutName, apply_title_mapping
DEBUG_EMC = False
epgcache = eEPGCache.getInstance()

# -----------------------------------------------------------------------------
# EMC Cache-only Artwork (Poster/Backdrop/Banner)
#   - show artwork ONLY from /media/hdd/xtra/EMC/{poster,backdrop,banner}
#   - NEVER download and NEVER write next to recordings
# -----------------------------------------------------------------------------

EMC_POSTER_FOLDER = "/media/hdd/xtra/EMC/poster"
EMC_BACKDROP_FOLDER = "/media/hdd/xtra/EMC/backdrop"
EMC_BANNER_FOLDER = "/media/hdd/xtra/EMC/banner"

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
tmdb_api = '3c3efcf47c3577558812bb9d64019d65'
omdb_api = '6a4c9432'
fanart_api = '6d231536dea4318a88cb2520ce89473b'
FILENAME_JUNK = ['_+', '-+', '\\.+', '\\d{4}[-_]\\d{2}[-_]\\d{2}', '\\d{2}[-_]\\d{2}[-_]\\d{4}', '\\d{8}', '\\d{4}', '[Ss]\\d{1,2}[Ee]\\d{1,2}', '[Ss]taffel\\s*\\d+', '[Ee]pisode\\s*\\d+', '[Ff]olge\\s*\\d+', '[Tt]eil\\s*\\d+', '1080[pi]', '720[pi]', '576[pi]', '480[pi]', '[Hh][Dd][Tt][Vv]', '[Ww][Ee][Bb]', '[Bb][Dd][Rr][Ii][Pp]', '[Xx]264', '[Hh]264', '[Hh]265', '[Aa][Vv][Cc]', '[Aa][Cc]3', '[Dd][Tt][Ss]', '[Aa][Aa][Cc]', '[Gg][Ee][Rr][Mm][Aa][Nn]', '[Ee][Nn][Gg][Ll][Ii][Ss][Hh]', '[Dd][Uu][Bb][Bb][Ee][Dd]', '[Ss][Yy][Nn][Cc]']

def get_storage_folder():
    if os.path.isdir('/media/hdd'):
        return '/media/hdd/xtra'
    if os.path.isdir('/media/usb'):
        return '/media/usb/xtra'
    if os.path.isdir('/media/mmc'):
        return '/media/mmc/xtra'
    return '/tmp'
STORAGE_FOLDER = get_storage_folder()
INFO_FOLDER = os.path.join(STORAGE_FOLDER, 'Info')
for folder in [STORAGE_FOLDER, INFO_FOLDER]:
    if not os.path.exists(folder):
        try:
            os.makedirs(folder, exist_ok=True)
        except:
            pass

def getRandomUserAgent():
    useragents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0']
    import random
    return random.choice(useragents)

def clean_filename_for_search(filename):
    if not filename:
        return ''
    name = os.path.splitext(filename)[0]
    senders = ['Das Erste', 'ZDF', 'RTL', 'SAT1', 'SAT.1', 'ProSieben', 'Pro7', 'VOX', 'kabel eins', 'RTLZWEI', 'RTL2', 'NITRO', 'DMAX', 'TLC', 'sixx', 'ProSieben MAXX', 'SAT.1 Gold', 'ARTE', 'Phoenix', '3sat', 'ONE', 'ZDFneo', 'ZDFinfo', 'ARD alpha', 'NDR', 'WDR', 'SWR', 'BR', 'HR', 'MDR', 'RBB', 'SR', 'tagesschau24', 'KiKA', 'ORF', 'ORF1', 'ORF2', 'SRF', 'ServusTV', 'ATV', 'Puls4', 'ARD']
    for sender in senders:
        name = re.sub('[_\\-\\s]*' + re.escape(sender) + '[_\\-\\s]*', ' ', name, flags=re.I)
    for pattern in FILENAME_JUNK:
        name = re.sub(pattern, ' ', name)
    name = re.sub('[_\\-]+', ' ', name)
    name = re.sub('\\s+', ' ', name).strip()
    return name

def save_info_json(slug, data):
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

class EMCBackdropWorker(threading.Thread):

    def __init__(self, dest_path, title, shortdesc='', extdesc=''):
        threading.Thread.__init__(self)
        self.dest_path = dest_path
        self.title = title
        self.shortdesc = shortdesc
        self.extdesc = extdesc
        self.daemon = True
        self.success = False

    def run(self):
        try:
            search_title = apply_title_mapping(self.title)
            if DEBUG_EMC:
                print("[EMC BACKDROP] Searching: '%s' (original: '%s')" % (search_title, self.title))
            slug = convtext(self.title) if self.title else None
            result = self.search_tmdb(search_title, slug)
            if result:
                self.success = True
                return
            result = self.search_fanart(search_title, slug)
            if result:
                self.success = True
                return
            if DEBUG_EMC:
                print('[EMC BACKDROP] No backdrop found for: %s' % self.title)
        except Exception as e:
            if DEBUG_EMC:
                print('[EMC BACKDROP ERROR] %s' % str(e))

    def search_tmdb(self, title, slug):
        try:
            url = 'https://api.themoviedb.org/3/search/multi?api_key=%s&language=%s&query=%s' % (tmdb_api, lng, urlquote(title))
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
                backdrop_path = item.get('backdrop_path')
                if not backdrop_path:
                    backdrop_path = item.get('poster_path')
                if not backdrop_path:
                    continue
                backdrop_url = 'https://image.tmdb.org/t/p/w1280%s' % backdrop_path
                if slug:
                    info = {'tmdb_id': item.get('id'), 'tmdb_vote_average': item.get('vote_average', 0), 'tmdb_vote_count': item.get('vote_count', 0), 'title': item.get('title') or item.get('name', ''), 'overview': item.get('overview', ''), 'backdrop_path': backdrop_path, 'media_type': media_type, 'adult': item.get('adult', False), 'Rated': '18' if item.get('adult') else 'NA'}
                    if media_type == 'movie' and item.get('release_date'):
                        info['year'] = item.get('release_date', '')[:4]
                    elif media_type == 'tv' and item.get('first_air_date'):
                        info['year'] = item.get('first_air_date', '')[:4]
                    save_info_json(slug, info)
                return self.download_backdrop(backdrop_url)
            return False
        except Exception as e:
            if DEBUG_EMC:
                print('[EMC TMDb ERROR] %s' % str(e))
            return False

    def search_fanart(self, title, slug):
        try:
            url_maze = 'http://api.tvmaze.com/singlesearch/shows?q=%s' % urlquote(title)
            mj = requests.get(url_maze, timeout=(3, 6)).json()
            tvdb_id = mj.get('externals', {}).get('thetvdb')
            if not tvdb_id:
                return False
            url_fanart = 'https://webservice.fanart.tv/v3/tv/%s?api_key=%s' % (tvdb_id, fanart_api)
            fjs = requests.get(url_fanart, timeout=(3, 6)).json()
            backdrop_url = None
            if fjs.get('showbackground'):
                backdrop_url = fjs['showbackground'][0].get('url')
            elif fjs.get('tvthumb'):
                backdrop_url = fjs['tvthumb'][0].get('url')
            if backdrop_url:
                return self.download_backdrop(backdrop_url)
            return False
        except Exception as e:
            if DEBUG_EMC:
                print('[EMC FanArt ERROR] %s' % str(e))
            return False

    def download_backdrop(self, url):
        try:
            headers = {'User-Agent': getRandomUserAgent()}
            response = requests.get(url, headers=headers, timeout=(3, 6))
            response.raise_for_status()
            with open(self.dest_path, 'wb') as f:
                f.write(response.content)
            if DEBUG_EMC:
                print('[EMC BACKDROP] Saved: %s' % self.dest_path)
            return True
        except Exception as e:
            if DEBUG_EMC:
                print('[EMC BACKDROP Download ERROR] %s' % str(e))
            return False

class GradientBackdropXEMC(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.backdrop_path = None
        self.timer = eTimer()
        try:
            self.timer.timeout.connect(self._checkBackdrop)
        except:
            self.timer.callback.append(self._checkBackdrop)
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
            more = []
            for t in titles:
                if '_' in t:
                    more.append(t.replace('_', ' '))
                if '  ' in t:
                    more.append(re.sub(r'\s+', ' ', t).strip())
            titles += [t for t in more if t and t not in titles]
            try:
                mapped = []
                for t in list(titles):
                    mt = apply_title_mapping(t)
                    if mt and mt not in titles and mt not in mapped:
                        mapped.append(mt)
                titles += mapped
            except Exception:
                pass
            # ---- Episode-aware + Season-aware lookup ----
            # Priority: Episode-Still (S01E05) → Season-Poster(backdrop) → Series-Backdrop
            episode_titles = []
            season_bd_titles = []
            try:
                import re as _re3, os as _os3
                _fn = _os3.path.basename(path or '')
                # Format 1: S01E05
                _m  = _re3.search(r'[Ss](\d{1,2})[Ee](\d{1,3})', _fn)
                # Format 2: 1x06
                _m1x = _re3.search(r'\b(\d{1,2})[xX](\d{1,3})\b', _fn) if not _m else None
                # Format 3: 'Serie N. Titel'
                _m_n = _re3.search(r'^(.+?)\s+(\d{1,3})\.\s+(.+)$', _fn) if not _m and not _m1x else None

                if _m:
                    _s = int(_m.group(1)); _e = int(_m.group(2))
                    for _t in titles:
                        _clean = _re3.sub(r'\s*[Ss]\d{1,2}[Ee]\d{1,3}.*$', '', _t).strip()
                        if _clean:
                            episode_titles.append('%s_S%02dE%02d' % (_clean, _s, _e))
                            season_bd_titles.append('%s_S%02d' % (_clean, _s))
                elif _m1x:
                    _s = int(_m1x.group(1)); _e = int(_m1x.group(2))
                    for _t in titles:
                        _clean = _re3.sub(r'\s*\d{1,2}[xX]\d{1,3}.*$', '', _t).strip()
                        if _clean:
                            episode_titles.append('%s_S%02dE%02d' % (_clean, _s, _e))
                            season_bd_titles.append('%s_S%02d' % (_clean, _s))
                elif _m_n:
                    # Dokumentationsformat: Serie N. Titel → Staffel 1, Episode N
                    _s = 1; _e = int(_m_n.group(2))
                    for _t in titles:
                        _clean = _re3.sub(r'\s+\d{1,3}\..*$', '', _t).strip()
                        if _clean:
                            episode_titles.append('%s_S01E%02d' % (_clean, _e))
                            season_bd_titles.append('%s_S01' % _clean)
            except Exception:
                pass

            found = None
            # 1. Episode-Still
            if episode_titles:
                found = _emc_find_artwork(EMC_BACKDROP_FOLDER, episode_titles)
            # 2. Staffel-Backdrop
            if not found and season_bd_titles:
                found = _emc_find_artwork(EMC_BACKDROP_FOLDER, season_bd_titles)
            # 3. Serien-Backdrop (Fallback)
            if not found:
                found = _emc_find_artwork(EMC_BACKDROP_FOLDER, titles)
            if not found:
                self.instance.hide()
                return
            self.backdrop_path = found
            self._showBackdrop(found)
        except Exception as e:
            if DEBUG_EMC:
                print('[EMC Backdrop _updateEvent ERROR] %s' % str(e))
            self.instance.hide()
    def _startWorker(self, dest_path, query, short, ext):
        if self.worker and self.worker.is_alive():
            return
        self.worker = EMCBackdropWorker(dest_path, query, short, ext)
        self.worker.start()
        self.check_count = 0
        self.timer.start(300, True)

    def _checkBackdrop(self):
        try:
            self.check_count += 1
            if self.backdrop_path and os.path.exists(self.backdrop_path):
                if os.path.getsize(self.backdrop_path) > 0:
                    self._showBackdrop(self.backdrop_path)
                    return
            if self.check_count < 20:
                self.timer.start(300, True)
            else:
                self.instance.hide()
        except:
            self.instance.hide()

    def _showBackdrop(self, path):
        try:
            self.instance.setPixmap(loadJPG(path))
            self.instance.setScale(1)
            self.instance.show()
        except:
            self.instance.hide()
if __name__ == '__main__':
    print('=' * 60)
    print('GradientBackdropXEMC - NEU')
    print('=' * 60)
    print()
    print('ZWECK: Backdrop fuer Aufnahmen/Filme')
    print('VERWENDUNG:')
    print('  - EMC Selection')
    print('  - Movie Player')
    print('  - Movieliste')
    print()
    print('SPEICHERORT: EMC Cache-only (/media/hdd/xtra/EMC/backdrop)')
    print('  Film.ts -> Film_backdrop.jpg')
    print()
    print('FEATURES:')
    print('  - TITLE_MAPPINGS Integration')
    print('  - TMDb + FanArt Suche')
    print('  - JSON-Speicherung')
    print('  - w1280 Aufloesung')
    print()