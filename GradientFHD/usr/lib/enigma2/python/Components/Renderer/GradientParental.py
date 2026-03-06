# -*- coding: utf-8 -*-
# 02.26 @stein17, Many new features and improvements
"""GradientParental.py (OpenATV / Enigma2) - Fix for EMC/MoviePlayer + MovieList

READY-TO-COPY

You reported two remaining issues:
1) In MoviePlayer/EMC playback, with source="session.CurrentService" it always showed N/A.
   Cause: in some EMC/player situations CurrentService does not provide event/path immediately.
   Fix: robust path detection (source + NavigationInstance + parsing serviceRef strings)
        + .eit parsing + JSON Rated fallback.

2) With source="session.Event_Now" the icon may "stick" while scrolling a list.
   Cause: Event_Now is NOT the right source for a movie list selection, and the renderer
          kept the previous value on CHANGED_CLEAR.
   Fix: do NOT carry a cached value to a different item (different file_path/title)
        + periodic polling to catch delayed event/meta updates.

Recommended skin usage
----------------------
EMC MoviePlayer/Playback (best):
  <widget source="session.CurrentService" render="GradientParental" ... />

EMC MovieList selection (best):
  <widget source="Service" render="GradientParental" ... />

If you use the same widget in a shared template, this renderer tries to work with
all of: ServiceEvent, CurrentService, generic objects with .event/.service/.text.

Optional skin attributes
------------------------
path=".../parental"     (default: current skin /usr/share/enigma2/<skin>/parental)
prefix="FSK_" ext=".png"
showNA="1"              (default 1)
interval="500"          (polling ms; default 500)
keepLast="1"            (default 1)  Keep last valid value when same item loses event.
graceLive="2"           (seconds; default 2)
gracePlayback="0"       (0=infinite during playback; default 0)
force="NA|0|6|12|16|18" (debug)
debug="0|1" logfile="/tmp/GradientParental.log"

Installation
------------
/usr/lib/enigma2/python/Components/Renderer/GradientParental.py
rm -f /usr/lib/enigma2/python/Components/Renderer/GradientParental.pyc
rm -rf /usr/lib/enigma2/python/Components/Renderer/__pycache__
init 4; sleep 2; init 3
"""

from __future__ import absolute_import

import os
import re
import json
import sys
import time

from Components.Renderer.Renderer import Renderer
from Components.config import config
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.CurrentService import CurrentService
from enigma import ePixmap, eTimer, loadPNG

try:
    import NavigationInstance
except Exception:
    NavigationInstance = None

try:
    from .GradientConverlibr import convtext, apply_title_mapping
except Exception:
    try:
        from GradientConverlibr import convtext, apply_title_mapping
    except Exception:
        convtext = None
        apply_title_mapping = lambda x: x


# ---------------- storage path like your original ----------------

def isMountedInRW(mount_point):
    try:
        with open('/proc/mounts', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) > 1 and parts[1] == mount_point:
                    return True
    except Exception:
        pass
    return False


def get_info_folder():
    # Prefer configured base from GradientFHD (supports /media/autofs/...)
    try:
        sel = getattr(config.plugins.GradientFHD, "posterXPath", None)
        if sel is not None and getattr(sel, "value", None) and sel.value != "AUTO":
            base = sel.value
            if os.path.isdir(base):
                d = os.path.join(base, 'xtra', 'Info')
                os.makedirs(d, exist_ok=True)
                return d
    except Exception:
        pass

    for base in ('/media/usb', '/media/hdd', '/media/mmc', '/media/net', '/media/autofs'):
        try:
            if os.path.exists(base) and isMountedInRW(base):
                d = os.path.join(base, 'xtra', 'Info')
                os.makedirs(d, exist_ok=True)
                return d
        except Exception:
            pass

    d = '/tmp/Info'
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


INFO_FOLDER = get_info_folder()


def default_icon_path():
    try:
        cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')
        return '/usr/share/enigma2/%s/parental' % cur_skin
    except Exception:
        return '/usr/share/enigma2/GradientFHD/parental'


# ---------------- EPG text parsing (like your original) ----------------

EPG_AGE_PATTERNS = [
    re.compile(r'[aA]b\s+(\d+)'),
    re.compile(r'\b(\d{1,2})\+\b'),
    re.compile(r'Od lat:\s*(\d+)', re.IGNORECASE),
    re.compile(r'FSK\s*(\d+)', re.IGNORECASE),
    re.compile(r'ab\s*(\d{1,2})\s*(?:J|Jahre)', re.IGNORECASE),
]


def extract_age_from_epg_text(text):
    if not text:
        return None
    for rx in EPG_AGE_PATTERNS:
        m = rx.search(text)
        if m:
            age = m.group(1)
            return age.replace('7', '6')
    return None


RATING_MAP = {
    'TV-G': '0', 'G': '0',
    'TV-Y7': '6', 'TV-Y': '6',
    'TV-10': '10',
    'TV-12': '12',
    'TV-14': '14',
    'TV-PG': '16', 'PG-13': '16', 'PG': '16',
    'TV-MA': '18', 'R': '18',
    'N/A': 'NA', 'Not Rated': 'NA', 'Unrated': 'NA', 'NA': 'NA', 'Passed': 'NA', '': 'NA'
}


def map_rated_to_fsk(rated):
    if not rated:
        return None
    rated = rated.strip()
    if rated in RATING_MAP:
        return RATING_MAP[rated]
    if rated.isdigit():
        return rated
    return 'NA'


def load_rated(slug):
    if not slug:
        return None
    path = os.path.join(INFO_FOLDER, slug + '.json')
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        rated = (data.get('Rated') or '').strip()
        return rated or None
    except Exception:
        return None


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
    senders = ['Das Erste', 'ZDF', 'RTL', 'SAT1', 'SAT.1', 'ProSieben', 'Pro7', 'VOX',
               'kabel eins', 'RTLZWEI', 'RTL2', 'ARTE', 'Phoenix', '3sat', 'ONE', 'ZDFneo',
               'NDR', 'WDR', 'SWR', 'BR', 'HR', 'MDR', 'RBB', 'ARD']
    for sender in senders:
        name = re.sub(r'[_\-\s]*' + re.escape(sender) + r'[_\-\s]*', ' ', name, flags=re.I)
    for pattern in FILENAME_JUNK:
        name = re.sub(pattern, ' ', name)
    name = re.sub(r'[_\-]+', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


# ---------------- EIT parsing for recordings (Descriptor 0x55) ----------------


def _age_from_eit_file(eit_path):
    try:
        with open(eit_path, 'rb') as f:
            data = f.read()
    except Exception:
        return None

    best_deu = None
    best_any = None

    def consider(country, age):
        nonlocal best_deu, best_any
        if age is None:
            return
        if country == 'DEU':
            best_deu = age if best_deu is None else max(best_deu, age)
        best_any = age if best_any is None else max(best_any, age)

    pos = 0
    n = len(data)
    while pos + 3 <= n:
        table_id = data[pos]
        if table_id < 0x4E or table_id > 0x6F:
            pos += 1
            continue

        section_length = ((data[pos + 1] & 0x0F) << 8) | data[pos + 2]
        section_end = pos + 3 + section_length
        if section_end > n or section_length < 15:
            pos += 1
            continue

        evpos = pos + 14
        loop_end = section_end - 4

        while evpos + 12 <= loop_end:
            dll = ((data[evpos + 10] & 0x0F) << 8) | data[evpos + 11]
            descpos = evpos + 12
            descend = descpos + dll
            if descend > loop_end:
                break

            while descpos + 2 <= descend:
                tag = data[descpos]
                length = data[descpos + 1]
                payload_start = descpos + 2
                payload_end = payload_start + length
                if payload_end > descend:
                    break

                if tag == 0x55 and length >= 4:
                    limit = payload_start + (length // 4) * 4
                    for i in range(payload_start, limit, 4):
                        ccode_b = data[i:i + 3]
                        try:
                            ccode = ccode_b.decode('ascii', 'ignore')
                        except Exception:
                            ccode = ''
                        rating = data[i + 3]
                        if rating == 0x00:
                            continue
                        age = int(rating) + 3
                        consider(ccode, age)

                descpos = payload_end

            evpos = descend

        pos = section_end

    return best_deu if best_deu is not None else best_any


# ---------------- key normalization ----------------


def normalize_fsk_key(age_str):
    if age_str is None:
        return None
    s = str(age_str).strip()
    if not s:
        return None
    if s.upper() in ('NA', 'N/A'):
        return 'NA'
    if s in ('0', '6', '12', '16', '18'):
        return s

    try:
        m = re.search(r'(\d{1,2})', s)
        if not m:
            return 'NA'
        age = int(m.group(1))
    except Exception:
        return 'NA'

    if age < 6:
        return '0'
    if age < 12:
        return '6'
    if age < 16:
        return '12'
    if age < 18:
        return '16'
    return '18'


def _extract_path_from_ref_string(s):
    """Extract filesystem path from a service reference string if present."""
    if not s or ':' not in s:
        return None
    tail = s.split(':')[-1]
    if tail.startswith('/'):
        return tail
    return None


def _nav_current_path():
    """Try to get currently playing service path from NavigationInstance."""
    try:
        if NavigationInstance is None or getattr(NavigationInstance, 'instance', None) is None:
            return None
        nav = NavigationInstance.instance
        ref = None
        try:
            ref = nav.getCurrentlyPlayingServiceReference()
        except Exception:
            ref = None
        if ref is None:
            try:
                ref = nav.getCurrentServiceReference()
            except Exception:
                ref = None
        if ref is None:
            return None
        if hasattr(ref, 'getPath'):
            p = ref.getPath()
            return p or None
    except Exception:
        return None
    return None


class GradientParental(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)

        self._icon_path = default_icon_path()
        self._prefix = 'FSK_'
        self._ext = '.png'

        self._show_na = True
        self._interval_ms = 500

        self._keep_last = True
        self._grace_live = 2
        self._grace_playback = 0  # 0 = infinite

        self._force = None

        # cache is only for the SAME item
        self._last_item_id = None
        self._last_key = None
        self._last_key_ts = 0

        self._debug = False
        self._logfile = '/tmp/GradientParental.log'

        self._poll = eTimer()
        self._poll_connected = False

    def _log(self, *parts):
        if not self._debug:
            return
        msg = "[GradientParental] %s %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), " ".join([str(p) for p in parts]))
        try:
            with open(self._logfile, 'a', encoding='utf-8') as f:
                f.write(msg + "\n")
        except Exception:
            try:
                print(msg)
            except Exception:
                pass

    def applySkin(self, desktop, parent):
        attribs = []
        for (attrib, value) in self.skinAttributes:
            if attrib == 'path':
                self._icon_path = value
            elif attrib == 'prefix':
                self._prefix = value
            elif attrib == 'ext':
                self._ext = value
            elif attrib == 'showNA':
                self._show_na = str(value).strip() not in ('0', 'false', 'False', 'no', 'No')
            elif attrib == 'interval':
                try:
                    self._interval_ms = int(value)
                except Exception:
                    pass
            elif attrib == 'keepLast':
                self._keep_last = str(value).strip() not in ('0', 'false', 'False', 'no', 'No')
            elif attrib == 'graceLive':
                try:
                    self._grace_live = int(value)
                except Exception:
                    pass
            elif attrib == 'gracePlayback':
                try:
                    self._grace_playback = int(value)
                except Exception:
                    pass
            elif attrib == 'force':
                v = str(value).strip()
                self._force = v if v else None
            elif attrib == 'debug':
                self._debug = str(value).strip() in ('1', 'true', 'True', 'yes', 'Yes')
            elif attrib == 'logfile':
                self._logfile = str(value).strip() or self._logfile
            else:
                attribs.append((attrib, value))

        self.skinAttributes = attribs

        if self._debug:
            try:
                with open(self._logfile, 'w', encoding='utf-8') as f:
                    f.write('')
            except Exception:
                pass
            self._log('applySkin icon_path=', self._icon_path, 'force=', self._force,
                      'keepLast=', self._keep_last, 'graceLive=', self._grace_live,
                      'gracePlayback=', self._grace_playback, 'interval=', self._interval_ms)

        return Renderer.applySkin(self, desktop, parent)

    def postWidgetCreate(self, instance):
        Renderer.postWidgetCreate(self, instance)
        self._connect_poll()
        self._start_poll()
        self._update()

    def preWidgetRemove(self, instance):
        self._stop_poll()
        Renderer.preWidgetRemove(self, instance)

    def onShow(self):
        self._connect_poll()
        self._start_poll()
        self._update()

    def onHide(self):
        self._stop_poll()

    def changed(self, what):
        # IMPORTANT: do not hide on CHANGED_CLEAR. Just update.
        if not self.instance:
            return
        self._update()

    def _connect_poll(self):
        if self._poll_connected:
            return
        try:
            if hasattr(self._poll, 'timeout') and hasattr(self._poll.timeout, 'connect'):
                self._poll.timeout.connect(self._update)
                self._poll_connected = True
                return
        except Exception:
            pass
        try:
            if hasattr(self._poll, 'callback'):
                self._poll.callback.append(self._update)
                self._poll_connected = True
                return
        except Exception:
            pass

    def _start_poll(self):
        try:
            self._poll.start(max(200, int(self._interval_ms)), False)
        except Exception:
            pass

    def _stop_poll(self):
        try:
            self._poll.stop()
        except Exception:
            pass

    # --------------- core ---------------

    def _get_event_and_path(self):
        src = getattr(self, 'source', None)
        event = None
        file_path = None

        # 1) known source types
        if isinstance(src, ServiceEvent):
            event = getattr(src, 'event', None)
            svc = getattr(src, 'service', None)
            try:
                if svc and hasattr(svc, 'getPath'):
                    file_path = svc.getPath() or None
            except Exception:
                file_path = None

        elif isinstance(src, CurrentService):
            event = getattr(src, 'event', None)
            try:
                ref = src.getCurrentServiceReference()
                if ref and hasattr(ref, 'getPath'):
                    file_path = ref.getPath() or None
            except Exception:
                file_path = None

        # 2) generic attributes
        if event is None and src is not None:
            event = getattr(src, 'event', None)

        if file_path is None and src is not None:
            # src.service might be an eServiceReference
            svc = getattr(src, 'service', None)
            try:
                if svc and hasattr(svc, 'getPath'):
                    file_path = svc.getPath() or None
            except Exception:
                file_path = None

        if file_path is None and src is not None:
            # src.text might be a service reference string
            try:
                txt = getattr(src, 'text', None)
                file_path = _extract_path_from_ref_string(txt)
            except Exception:
                file_path = None

        # 3) NavigationInstance fallback (very important for playback)
        if file_path is None:
            file_path = _nav_current_path()

        return event, file_path

    def _update(self):
        if not self.instance:
            return

        event, file_path = self._get_event_and_path()

        # identify current item (prevents "sticky icon" across list items)
        item_id = file_path
        if not item_id and event is not None:
            try:
                item_id = event.getEventName() or None
            except Exception:
                item_id = None

        if item_id != self._last_item_id:
            # new selection/new playback item -> reset last-key cache
            self._last_item_id = item_id
            self._last_key = None
            self._last_key_ts = 0

        is_playback = bool(file_path)

        # -------- decide key --------
        if self._force:
            key = normalize_fsk_key(self._force)
            self._set_icon_key(key)
            return

        # A) try direct rating from event
        age_int = None
        if event is not None:
            for meth in ('getParentalData', 'getParentalRating'):
                try:
                    if hasattr(event, meth):
                        val = getattr(event, meth)()
                        if isinstance(val, tuple) and len(val) >= 2:
                            age_int = int(val[1])
                        else:
                            age_int = int(val)
                        if age_int <= 0:
                            age_int = None
                        break
                except Exception:
                    age_int = None

        if age_int is not None:
            key = normalize_fsk_key(age_int)
            self._remember_key(key)
            key = self._maybe_keep_last(key, is_playback)
            self._set_icon_key(key)
            return

        # B) try parse rating from EPG text
        title = None
        if event is not None:
            try:
                name = (event.getEventName() or '')
                short = (event.getShortDescription() or '')
                ext = (event.getExtendedDescription() or '')
                full_text = '%s\n%s\n%s' % (name, short, ext)
                age = extract_age_from_epg_text(full_text)
                if age:
                    key = normalize_fsk_key(age)
                    self._remember_key(key)
                    key = self._maybe_keep_last(key, is_playback)
                    self._set_icon_key(key)
                    return
                title = name.replace('\xc2\x86', '').replace('\xc2\x87', '').strip()
            except Exception:
                title = None

        # C) try .eit file for recordings
        if file_path:
            try:
                eit_path = os.path.splitext(file_path)[0] + '.eit'
                if os.path.exists(eit_path):
                    age_from_eit = _age_from_eit_file(eit_path)
                    if age_from_eit is not None:
                        key = normalize_fsk_key(age_from_eit)
                        self._remember_key(key)
                        key = self._maybe_keep_last(key, is_playback)
                        self._set_icon_key(key)
                        return
            except Exception:
                pass

        # D) filename -> xtra Info JSON Rated
        if (not title) and file_path:
            title = clean_filename_for_search(os.path.basename(file_path))

        if title:
            mapped_title = apply_title_mapping(title) if apply_title_mapping else title
            slug = convtext(mapped_title) if (convtext and mapped_title) else None
            rated = load_rated(slug) if slug else None
            if rated:
                key = normalize_fsk_key(map_rated_to_fsk(rated))
            else:
                key = 'NA' if self._show_na else None
        else:
            key = 'NA' if self._show_na else None

        key = self._maybe_keep_last(key, is_playback)

        if self._debug:
            self._log('update', 'item_id=', item_id, 'file_path=', file_path, 'key=', key)

        self._set_icon_key(key)

    def _remember_key(self, key):
        if key and key != 'NA':
            self._last_key = key
            self._last_key_ts = int(time.time())

    def _maybe_keep_last(self, key, is_playback):
        if not self._keep_last:
            return key

        if key and key != 'NA':
            self._remember_key(key)
            return key

        if not self._last_key:
            return key

        now = int(time.time())
        grace = self._grace_playback if is_playback else self._grace_live

        # playback: gracePlayback=0 means infinite
        if is_playback and grace == 0:
            return self._last_key

        if grace > 0 and (now - self._last_key_ts) <= grace:
            return self._last_key

        return key

    def _set_icon_key(self, key):
        if key is None:
            try:
                self.instance.hide()
            except Exception:
                pass
            return

        icon_name = '%s%s%s' % (self._prefix, key, self._ext)
        icon_path = os.path.join(self._icon_path, icon_name)

        if (not os.path.exists(icon_path)) and self._show_na and key != 'NA':
            icon_name = '%sNA%s' % (self._prefix, self._ext)
            icon_path = os.path.join(self._icon_path, icon_name)

        if os.path.exists(icon_path):
            try:
                self.instance.setPixmap(loadPNG(icon_path))
                try:
                    self.instance.setScale(1)
                except Exception:
                    pass
                self.instance.show()
            except Exception:
                try:
                    self.instance.hide()
                except Exception:
                    pass
        else:
            try:
                self.instance.hide()
            except Exception:
                pass
