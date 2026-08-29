
# -*- coding: utf-8 -*-
# GradientStarX - patched for stable display in Player + Live
# Based on user's "OPTIMIERTE GradientStarX.py - Version 3" (minimal functional changes)
# 02.26 @stein17, Many new features and improvements
from __future__ import print_function

from Components.Renderer.Renderer import Renderer
from Components.config import config
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.CurrentService import CurrentService
from enigma import ePixmap, eTimer, loadPNG

import json
import os
import sys
import re
import requests
from requests.adapters import HTTPAdapter, Retry

try:
    from .GradientConverlibr import convtext, quoteEventName, apply_title_mapping
except Exception:
    from GradientConverlibr import convtext, quoteEventName, apply_title_mapping

PY3 = sys.version_info[0] >= 3

# --- TMDB key (keep user's logic) ---
tmdb_api = '3c3efcf47c3577558812bb9d64019d65'
try:
    lng = config.osd.language.value
    lng = lng[:-3]
except Exception:
    lng = 'en'

def load_tmdb_key():
    global tmdb_api
    try:
        cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')
        key_path = '/usr/share/enigma2/%s/tmdbkey' % cur_skin
        if os.path.exists(key_path):
            with open(key_path, 'r') as f:
                v = f.read().strip()
                if v:
                    tmdb_api = v
    except Exception:
        pass

load_tmdb_key()

# --- INFO folder: prefer persistent storage even if mounted read-only (reading cached jsons still works) ---
def get_info_folder():
    # Prefer configured base from GradientWQHD (supports /media/autofs/...)
    try:
        sel = getattr(config.plugins.GradientWQHD, "posterXPath", None)
        if sel is not None and getattr(sel, "value", None) and sel.value != "AUTO":
            base = sel.value
            if os.path.isdir(base):
                d = os.path.join(base, 'xtra', 'Info')
                os.makedirs(d, exist_ok=True)
                return d
    except Exception:
        pass

    candidates = []
    for base in ('/media/usb', '/media/hdd', '/media/mmc', '/media/net', '/media/autofs'):
        try:
            info_dir = os.path.join(base, 'xtra', 'Info')
            if os.path.exists(info_dir):
                return info_dir
            if os.path.exists(base):
                candidates.append(info_dir)
        except Exception:
            pass
    for d in candidates:
        try:
            os.makedirs(d, exist_ok=True)
            return d
        except Exception:
            pass
    path_folder = '/tmp/Info'
    try:
        os.makedirs(path_folder, exist_ok=True)
    except Exception:
        pass
    return path_folder

INFO_FOLDER = get_info_folder()

def load_tmdb_vote(slug):
    if not slug:
        return None
    path = os.path.join(INFO_FOLDER, slug + '.json')
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        val = data.get('tmdb_vote_average')
        if isinstance(val, (int, float, str)):
            return float(val)
    except Exception:
        return None
    return None

def save_tmdb_vote(slug, vote):
    if not slug or vote is None:
        return
    try:
        path = os.path.join(INFO_FOLDER, slug + '.json')
        data = {}
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data['tmdb_vote_average'] = float(vote)
        tmp_path = path + '.tmp'
        with open(tmp_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        pass

FILENAME_JUNK = [
    r'_+', r'-+', r'\.+',
    r'\d{4}[-_]\d{2}[-_]\d{2}', r'\d{2}[-_]\d{2}[-_]\d{4}', r'\d{8}', r'\d{4}',
    r'[Ss]\d{1,2}[Ee]\d{1,2}', r'[Ss]taffel\s*\d+', r'[Ee]pisode\s*\d+', r'[Ff]olge\s*\d+',
    r'1080[pi]', r'720[pi]', r'576[pi]', r'480[pi]',
    r'[Hh][Dd][Tt][Vv]', r'[Ww][Ee][Bb]', r'[Bb][Dd][Rr][Ii][Pp]',
    r'[Xx]264', r'[Hh]264', r'[Hh]265'
]

def clean_filename_for_search(filename):
    if not filename:
        return ''
    name = os.path.splitext(filename)[0]
    # strip common "recording prefix": YYYYMMDD HHMM - CHANNEL - TITLE
    name = re.sub(r'^\d{8}\s+\d{4}\s*-\s*[^-]+-\s*', '', name).strip()
    senders = [
        'Das Erste', 'ZDF', 'RTL', 'SAT1', 'SAT.1', 'ProSieben', 'Pro7', 'VOX', 'kabel eins',
        'RTLZWEI', 'RTL2', 'ARTE', 'Phoenix', '3sat', 'ONE', 'ZDFneo',
        'NDR', 'WDR', 'SWR', 'BR', 'HR', 'MDR', 'RBB', 'ARD'
    ]
    for sender in senders:
        name = re.sub(r'[_\-\s]*' + re.escape(sender) + r'[_\-\s]*', ' ', name, flags=re.I)
    for pattern in FILENAME_JUNK:
        name = re.sub(pattern, ' ', name)
    name = re.sub(r'[_\-]+', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def _read_ts_meta_title(ts_path):
    try:
        meta = ts_path + '.meta'
        if not os.path.exists(meta):
            return None
        with open(meta, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [x.strip() for x in f.read().splitlines()]
        # line 2 is title
        if len(lines) >= 2 and lines[1]:
            return lines[1].strip()
    except Exception:
        pass
    return None

def _get_playing_path():
    # best-effort; works even if widget source isn't CurrentService
    try:
        import NavigationInstance
        nav = getattr(NavigationInstance, 'instance', None)
        if nav:
            ref = nav.getCurrentlyPlayingServiceReference()
            if ref:
                p = ref.getPath()
                if p:
                    return p
    except Exception:
        pass
    return None

def create_http_session():
    session = requests.Session()
    retry_strategy = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

http_session = create_http_session()

class GradientStarX(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.background_pixmap_path = None
        self.filled_pixmap_path = None
        self.timer = None
        self._init_timer = None
        self._init_tries = 0
        self._last_key = None
        self._last_vote = None

    def applySkin(self, desktop, parent):
        attribs = []
        for (attrib, value) in self.skinAttributes:
            if attrib == 'pixmap':
                self.filled_pixmap_path = value
            elif attrib == 'backgroundPixmap':
                self.background_pixmap_path = value
            else:
                attribs.append((attrib, value))
        self.skinAttributes = attribs
        return Renderer.applySkin(self, desktop, parent)

    def postWidgetCreate(self, instance):
        # EMC/Player sometimes doesn't call changed() again after CLEAR.
        # Do a few delayed retries after create.
        if self._init_timer is None:
            self._init_timer = eTimer()
            try:
                self._init_timer.timeout.connect(self._init_retry)
            except Exception:
                self._init_timer.callback.append(self._init_retry)
        self._init_tries = 0
        self._init_timer.start(250, True)

    def _init_retry(self):
        self._init_tries += 1
        try:
            self._update()
        except Exception:
            pass
        if self._init_tries < 12:  # ~3 seconds total
            try:
                self._init_timer.start(250, True)
            except Exception:
                pass

    def changed(self, what):
        if not self.instance:
            return
        if what[0] == self.CHANGED_CLEAR:
            # don't permanently hide; schedule a retry (player clears event frequently)
            if self.timer is None:
                self.timer = eTimer()
                try:
                    self.timer.timeout.connect(self._update)
                except Exception:
                    self.timer.callback.append(self._update)
            self.timer.start(200, True)
            return

        if self.timer is None:
            self.timer = eTimer()
            try:
                self.timer.timeout.connect(self._update)
            except Exception:
                self.timer.callback.append(self._update)
        self.timer.start(10, True)

    def _update(self):
        if not self.instance:
            return

        try:
            title = None
            event = None
            file_path = None
            src = self.source

            # 1) Prefer currently playing file path (Player stability)
            play_path = _get_playing_path()
            if play_path and os.path.isfile(play_path):
                file_path = play_path

            # 2) Otherwise use source-specific info
            if file_path is None:
                if isinstance(src, ServiceEvent):
                    event = getattr(src, 'event', None)
                    svc = getattr(src, 'service', None)
                    if svc:
                        file_path = svc.getPath()
                elif isinstance(src, CurrentService):
                    ref = src.getCurrentServiceReference()
                    if ref:
                        file_path = ref.getPath()
                    event = getattr(src, 'event', None)
                else:
                    event = getattr(src, 'event', None)

            # 3) Title: if file playback, lock to meta/filename (avoid "Sendepause" etc.)
            if file_path and os.path.isfile(file_path):
                if file_path.endswith('.ts'):
                    title = _read_ts_meta_title(file_path)
                if not title:
                    title = clean_filename_for_search(os.path.basename(file_path))

            # 4) Live title from event
            if not title and event:
                ev_name = event.getEventName() if event else ''
                if ev_name:
                    ev_name = ev_name.replace('Â\x86', '').replace('Â\x87', '').strip()
                    # ignore generic/unstable placeholders
                    if ev_name.lower() not in ('sendepause',):
                        title = ev_name

            if not title:
                # If we already had a stable value for the same key, keep it
                if self._last_vote is not None and self._last_key:
                    self._render_stars(self._last_vote)
                else:
                    self.instance.hide()
                return

            mapped_title = apply_title_mapping(title)
            slug = convtext(mapped_title) if mapped_title else None
            if not slug:
                self.instance.hide()
                return

            key = file_path if (file_path and os.path.isfile(file_path)) else slug

            cached_vote = load_tmdb_vote(slug)
            if cached_vote is None and self._last_key == key and self._last_vote is not None:
                # keep last vote if current lookup fails transiently
                cached_vote = self._last_vote

            if cached_vote is not None:
                self._last_key = key
                self._last_vote = cached_vote
                self._render_stars(cached_vote)
                return

            # Network fetch only if we don't have anything cached
            vote = self._fetch_tmdb_vote(mapped_title)
            if vote is not None:
                save_tmdb_vote(slug, vote)
                self._last_key = key
                self._last_vote = vote
                self._render_stars(vote)
            else:
                self.instance.hide()

        except Exception:
            self.instance.hide()

    def _fetch_tmdb_vote(self, title):
        if not tmdb_api or not title:
            return None
        try:
            q = quoteEventName(title)
            url = 'http://api.themoviedb.org/3/search/multi?api_key=%s&query=%s' % (tmdb_api, q)
            if lng:
                url += '&language=%s' % lng
            r = http_session.get(url, timeout=(3, 6))
            r.raise_for_status()
            data = r.json()
            results = data.get('results') or []
            if not results:
                return None
            first = results[0]
            vote = first.get('vote_average')
            if vote is None:
                return None
            return float(vote)
        except Exception:
            return None

    def _render_stars(self, vote_average):
        try:
            if vote_average is None or vote_average <= 0:
                self.instance.hide()
                return

            widget_size = self.instance.size()
            target_width = widget_size.width()
            target_height = widget_size.height()
            if target_width <= 0 or target_height <= 0:
                self.instance.hide()
                return

            cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')
            skin_path = '/usr/share/enigma2/%s/' % cur_skin

            bg_path = os.path.join(skin_path, self.background_pixmap_path) if self.background_pixmap_path else os.path.join(skin_path, 'icons/starbar_empty.png')
            fg_path = os.path.join(skin_path, self.filled_pixmap_path) if self.filled_pixmap_path else os.path.join(skin_path, 'icons/starbar_filled.png')

            if not os.path.exists(bg_path) and not os.path.exists(fg_path):
                self.instance.hide()
                return

            try:
                from PIL import Image
                if os.path.exists(bg_path):
                    bg_img = Image.open(bg_path)
                    bg_img = bg_img.resize((target_width, target_height), Image.LANCZOS)
                else:
                    bg_img = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))

                if os.path.exists(fg_path):
                    fg_img = Image.open(fg_path)
                    fg_img = fg_img.resize((target_width, target_height), Image.LANCZOS)
                    ratio = float(vote_average) / 10.0
                    crop_width = int(target_width * ratio)
                    if crop_width > 0:
                        fg_cropped = fg_img.crop((0, 0, crop_width, target_height))
                        bg_img.paste(fg_cropped, (0, 0), fg_cropped if fg_cropped.mode == 'RGBA' else None)

                tmp_path = '/tmp/starbar_tmp_%d.png' % id(self)
                bg_img.save(tmp_path, 'PNG')
                self.instance.setPixmap(loadPNG(tmp_path))
                self.instance.show()
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            except ImportError:
                # fallback: show filled bar only
                if os.path.exists(fg_path):
                    self.instance.setPixmap(loadPNG(fg_path))
                    self.instance.show()
                else:
                    self.instance.hide()
        except Exception:
            self.instance.hide()
