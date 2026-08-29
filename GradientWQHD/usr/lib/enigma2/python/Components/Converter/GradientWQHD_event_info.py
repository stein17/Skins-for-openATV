"""
3. OPTIMIERTE GradientWQHD_event_info.py
=====================================

Converter fuer skin.xml - zeigt TMDb-Daten als Labels
08.26 @stein17: Spinner/Netzwerk-Sicherheit durch Hintergrundzugriffe

NEUE FEATURES:
- JSON- und TMDb-Zugriffe laufen außerhalb des Enigma2-GUI-Threads
- Vorhandene Werte werden im Speicher zwischengespeichert
- Fehlgeschlagene Abfragen werden zeitlich begrenzt wiederholt
- apply_title_mapping() Integration

SKIN.XML VERWENDUNG:
<!-- Titel -->
<widget source="session.CurrentService" render="Label">
  <convert type="GradientWQHD_event_info">title</convert>
</widget>

<!-- Rating -->
<widget source="session.CurrentService" render="Label">
  <convert type="GradientWQHD_event_info">tmdb_vote_average</convert>
</widget>

<!-- Jahr -->
<widget source="session.CurrentService" render="Label">
  <convert type="GradientWQHD_event_info">year</convert>
</widget>
"""
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.config import config
from enigma import eTimer, iServiceInformation
from ServiceReference import ServiceReference
import NavigationInstance
import os
import sys
import json
import threading
import time
import requests
from requests.adapters import HTTPAdapter, Retry
from Components.Renderer.GradientWQHDAPIProxy import FALLBACK_API_MARKER, wrap_requests

requests = wrap_requests(requests)
PY3 = sys.version_info[0] >= 3
if PY3:
    from urllib.parse import quote as urlquote
else:
    from urllib import quote as urlquote
try:
    from Components.Renderer.GradientWQHDConverlibr import convtext, apply_title_mapping
except:
    try:
        from GradientWQHDConverlibr import convtext, apply_title_mapping
    except:
        convtext = lambda x: x.lower().replace(' ', '_')
        apply_title_mapping = lambda x: x
DEBUG_INFO = False
try:
    lng = config.osd.language.value
    lng = lng[:-3]
except:
    lng = 'de'
tmdb_api = FALLBACK_API_MARKER
STORAGE_BASES = ('/media/hdd', '/media/usb', '/media/mmc', '/media/net', '/media/autofs')
cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')
try:
    tmdb_key_path = '/usr/share/enigma2/%s/tmdbkey' % cur_skin
    if os.path.exists(tmdb_key_path):
        with open(tmdb_key_path, 'r') as f:
            tmdb_api = f.read().strip()
except:
    pass

def get_storage_folder():
    # Prefer configured base from GradientWQHD (supports /media/autofs/...)
    try:
        sel = getattr(config.plugins.GradientWQHD, "posterXPath", None)
        if sel is not None and getattr(sel, "value", None) and sel.value != "AUTO":
            # Respect the explicit selection without probing a possibly offline
            # NAS/autofs path in the GUI thread.
            return os.path.join(str(sel.value).rstrip('/'), "xtra")
    except Exception:
        pass

    # AUTO fallback: same order as PosterX, BackdropX and StarX.
    for base in STORAGE_BASES:
        try:
            if os.path.isdir(base):
                return os.path.join(base, 'xtra')
        except Exception:
            pass
    return '/tmp'
STORAGE_FOLDER = get_storage_folder()
INFO_FOLDER = os.path.join(STORAGE_FOLDER, 'Info')

def create_http_session():
    session = requests.Session()
    retry_strategy = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
http_session = create_http_session()
_TMDB_HTTP_LOCK = threading.Lock()

def get_event_info_from_json(slug, field):
    if not slug:
        return None
    try:
        json_path = os.path.join(INFO_FOLDER, slug + '.json')
        if not os.path.exists(json_path):
            return None
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data.get(field)
    except:
        return None

def load_event_info_json(slug):
    if not slug:
        return None
    try:
        json_path = os.path.join(INFO_FOLDER, slug + '.json')
        if not os.path.exists(json_path):
            return None
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None

def save_event_info_to_json(slug, data):
    if not slug or not data:
        return False
    try:
        os.makedirs(INFO_FOLDER, exist_ok=True)
        json_path = os.path.join(INFO_FOLDER, slug + '.json')
        existing = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    existing = json.load(f)
            except:
                pass
        existing.update(data)
        tmp_path = json_path + '.tmp'
        with open(tmp_path, 'w') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, json_path)
        if DEBUG_INFO:
            print('[INFO] JSON saved: %s' % json_path)
        return True
    except Exception as e:
        if DEBUG_INFO:
            print('[INFO ERROR] %s' % str(e))
        return False

def fetch_from_tmdb(title, slug):
    try:
        search_title = apply_title_mapping(title)
        url = 'https://api.themoviedb.org/3/search/multi?api_key=%s&language=%s&query=%s' % (tmdb_api, lng, urlquote(search_title))
        with _TMDB_HTTP_LOCK:
            response = http_session.get(url, timeout=(3, 6))
        if response.status_code != 200:
            return None
        data = response.json()
        results = data.get('results', [])
        if not results:
            return None
        item = results[0]
        media_type = item.get('media_type', '')
        if media_type == 'person':
            if len(results) > 1:
                item = results[1]
                media_type = item.get('media_type', '')
            else:
                return None
        info = {'tmdb_id': item.get('id'), 'tmdb_vote_average': item.get('vote_average', 0), 'tmdb_vote_count': item.get('vote_count', 0), 'title': item.get('title') or item.get('name', ''), 'original_title': item.get('original_title') or item.get('original_name', ''), 'overview': item.get('overview', ''), 'poster_path': item.get('poster_path', ''), 'backdrop_path': item.get('backdrop_path', ''), 'original_language': item.get('original_language', ''), 'popularity': item.get('popularity', 0), 'media_type': media_type, 'adult': item.get('adult', False), 'Rated': '18' if item.get('adult') else 'NA'}
        if media_type == 'movie':
            release = item.get('release_date', '')
            if release:
                info['release_date'] = release
                info['year'] = release[:4]
        elif media_type == 'tv':
            first_air = item.get('first_air_date', '')
            if first_air:
                info['first_air_date'] = first_air
                info['year'] = first_air[:4]
        if item.get('genre_ids'):
            info['genre_ids'] = item.get('genre_ids')
        save_event_info_to_json(slug, info)
        return info
    except requests.exceptions.Timeout:
        if DEBUG_INFO:
            print('[INFO] TMDb Timeout')
        return None
    except requests.exceptions.RequestException as e:
        if DEBUG_INFO:
            print('[INFO] TMDb Error: %s' % str(e))
        return None
    except Exception as e:
        if DEBUG_INFO:
            print('[INFO] Unexpected Error: %s' % str(e))
        return None


# The Converter's getText() method runs in Enigma2's GUI thread. Neither NAS
# file access nor HTTP is allowed there. One worker per slug loads the JSON and,
# only when needed, performs the TMDb request. The existing one-second converter
# timer then picks up the in-memory result without any cross-thread GUI access.
_INFO_LOCK = threading.Lock()
_INFO_CACHE = {}
_INFO_PENDING = set()
_INFO_LAST_FAILURE = {}
_INFO_RETRY_SECONDS = 30.0


def _event_info_worker(title, slug, field):
    data = {}
    try:
        stored = load_event_info_json(slug)
        if isinstance(stored, dict):
            data.update(stored)
        if data.get(field) is None:
            fetched = fetch_from_tmdb(title, slug)
            if isinstance(fetched, dict):
                data.update(fetched)
    except Exception:
        pass
    finally:
        with _INFO_LOCK:
            _INFO_CACHE[slug] = data
            if data.get(field) is None:
                _INFO_LAST_FAILURE[slug] = time.time()
            else:
                _INFO_LAST_FAILURE.pop(slug, None)
            _INFO_PENDING.discard(slug)


def request_event_info_async(title, slug, field):
    now = time.time()
    start_worker = False
    with _INFO_LOCK:
        cached_data = _INFO_CACHE.get(slug)
        last_failure = _INFO_LAST_FAILURE.get(slug, 0.0)
        if isinstance(cached_data, dict) and cached_data.get(field) is not None:
            return cached_data
        if slug not in _INFO_PENDING and (now - last_failure) >= _INFO_RETRY_SECONDS:
            _INFO_PENDING.add(slug)
            start_worker = True

    if start_worker:
        worker = threading.Thread(
            target=_event_info_worker,
            args=(title, slug, field),
            name='GradientEventInfo-%s' % slug[:24]
        )
        worker.daemon = True
        worker.start()
    return None

class GradientWQHD_event_info(Converter, object):
    TITLE = 0
    ORIGINAL_TITLE = 1
    YEAR = 2
    OVERVIEW = 3
    TMDB_VOTE_AVERAGE = 4
    TMDB_VOTE_COUNT = 5
    TMDB_ID = 6
    RATED = 7
    IMDB_RATING = 8
    IMDB_ID = 9
    GENRE = 10
    DIRECTOR = 11
    ACTORS = 12
    RUNTIME = 13
    RELEASE_DATE = 14
    FIRST_AIR_DATE = 15
    MEDIA_TYPE = 16
    POPULARITY = 17

    def __init__(self, type):
        Converter.__init__(self, type)
        self.type = {'title': self.TITLE, 'original_title': self.ORIGINAL_TITLE, 'year': self.YEAR, 'overview': self.OVERVIEW, 'tmdb_vote_average': self.TMDB_VOTE_AVERAGE, 'tmdb_vote_count': self.TMDB_VOTE_COUNT, 'tmdb_id': self.TMDB_ID, 'rated': self.RATED, 'imdb_rating': self.IMDB_RATING, 'imdb_id': self.IMDB_ID, 'genre': self.GENRE, 'director': self.DIRECTOR, 'actors': self.ACTORS, 'runtime': self.RUNTIME, 'release_date': self.RELEASE_DATE, 'first_air_date': self.FIRST_AIR_DATE, 'media_type': self.MEDIA_TYPE, 'popularity': self.POPULARITY}.get(type.lower(), self.TITLE)
        self.poll_interval = 1000
        self.poll_enabled = True
        self.timer = eTimer()
        try:
            self.timer.timeout.connect(self.doUpdate)
        except:
            self.timer.callback.append(self.doUpdate)
        self.timer.start(self.poll_interval, False)

    @cached
    def getText(self):
        try:
            service = self.source.service
            info = service and service.info()
            if not info:
                return ''
            event = self.source.event
            if not event:
                return ''
            title = event.getEventName()
            if not title:
                return ''
            title = title.replace('Â\x86', '').replace('Â\x87', '').strip()
            slug = convtext(title)
            if not slug:
                return ''
            field_map = {self.TITLE: 'title', self.ORIGINAL_TITLE: 'original_title', self.YEAR: 'year', self.OVERVIEW: 'overview', self.TMDB_VOTE_AVERAGE: 'tmdb_vote_average', self.TMDB_VOTE_COUNT: 'tmdb_vote_count', self.TMDB_ID: 'tmdb_id', self.RATED: 'Rated', self.IMDB_RATING: 'imdb_rating', self.IMDB_ID: 'imdb_id', self.GENRE: 'genre', self.DIRECTOR: 'director', self.ACTORS: 'actors', self.RUNTIME: 'runtime', self.RELEASE_DATE: 'release_date', self.FIRST_AIR_DATE: 'first_air_date', self.MEDIA_TYPE: 'media_type', self.POPULARITY: 'popularity'}
            field = field_map.get(self.type)
            if not field:
                return ''
            info_data = request_event_info_async(title, slug, field)
            if info_data:
                value = info_data.get(field)
                if value is not None:
                    if self.type == self.TMDB_VOTE_AVERAGE:
                        try:
                            return '%.1f' % float(value)
                        except:
                            return str(value)
                    return str(value)
            return ''
        except Exception as e:
            if DEBUG_INFO:
                print('[INFO getText ERROR] %s' % str(e))
            return ''

    def doUpdate(self):
        try:
            if self.poll_enabled:
                self.changed((self.CHANGED_ALL,))
        except:
            pass
    text = property(getText)
if __name__ == '__main__':
    print('=' * 60)
    print('GradientWQHD_event_info - OPTIMIERTE VERSION')
    print('=' * 60)
    print()
    print('FEATURES:')
    print('  - JSON/TMDb laufen im Hintergrund')
    print('  - Kein blockierender Netzwerkzugriff im GUI-Thread')
    print('  - apply_title_mapping() Integration')
    print('  - Bessere Fehlerbehandlung')
    print()
    print('VERFUEGBARE FELDER:')
    print('  - title, original_title, year')
    print('  - overview, tmdb_vote_average, tmdb_vote_count')
    print('  - rated, imdb_rating, imdb_id')
    print('  - genre, director, actors, runtime')
    print('  - release_date, first_air_date, media_type')
    print()
