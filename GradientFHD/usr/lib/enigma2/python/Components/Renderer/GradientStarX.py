#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from Components.Renderer.Renderer import Renderer
from Components.VariableValue import VariableValue
from Components.config import config
from enigma import eSlider
import json
import os
import sys
import requests

from .GradientConverlibr import convtext, quoteEventName
try:
    from .Gradient_event_info import Gradient_event_info
except Exception:
    try:
        from Gradient_event_info import Gradient_event_info
    except Exception:
        Gradient_event_info = None

PY3 = sys.version_info[0] >= 3

# ---------------------------
# API-Keys
# ---------------------------

tmdb_api = "3c3efcf47c3577558812bb9d64019d65"

try:
    lng = config.osd.language.value
    lng = lng[:-3]
except Exception:
    lng = "en"


def load_tmdb_key():
    global tmdb_api
    try:
        cur_skin = config.skin.primary_skin.value.replace("/skin.xml", "")
        key_path = "/usr/share/enigma2/%s/tmdbkey" % cur_skin
        if os.path.exists(key_path):
            with open(key_path, "r") as f:
                v = f.read().strip()
                if v:
                    tmdb_api = v
    except Exception:
        pass


load_tmdb_key()


# ---------------------------
# Info-Ordner (/xtra/Info)
# ---------------------------

def isMountedInRW(mount_point):
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) > 1 and parts[1] == mount_point:
                    return True
    except Exception:
        pass
    return False


def get_info_folder():
    path_folder = "/tmp/Info"
    if os.path.exists("/media/hdd") and isMountedInRW("/media/hdd"):
        path_folder = "/media/hdd/xtra/Info"
    elif os.path.exists("/media/usb") and isMountedInRW("/media/usb"):
        path_folder = "/media/usb/xtra/Info"
    elif os.path.exists("/media/mmc") and isMountedInRW("/media/mmc"):
        path_folder = "/media/mmc/xtra/Info"
    if not os.path.exists(path_folder):
        try:
            os.makedirs(path_folder)
        except OSError:
            pass
    return path_folder


INFO_FOLDER = get_info_folder()


def load_tmdb_vote(slug):
    if not slug:
        return None
    path = os.path.join(INFO_FOLDER, slug + ".json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
        val = data.get("tmdb_vote_average")
        if isinstance(val, (int, float, str)):
            return float(val)
    except Exception:
        return None
    return None


def save_tmdb_vote(slug, vote):
    if not slug or vote is None:
        return
    try:
        path = os.path.join(INFO_FOLDER, slug + ".json")
        data = {}
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["tmdb_vote_average"] = float(vote)
        with open(path, "w") as f:
            json.dump(data, f)

        # Try to enrich this small JSON with full TMDb info
        try:
            if Gradient_event_info is not None:
                try:
                    # read back file to check whether details already present
                    try:
                        with open(path, 'r', encoding='utf-8') as _f:
                            _d = json.load(_f)
                    except Exception:
                        _d = {}
                    has_detail = any(k in _d for k in ('tmdb_id','overview','title','poster_path','backdrop_path'))
                    if not has_detail:
                        # guess a human-readable title from slug if no title present
                        title_guess = _d.get('title') or slug.replace('_',' ').replace('-', ' ')
                        try:
                            g = Gradient_event_info()
                            g.fetch_and_save(title_guess, slug)
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    except Exception:
        pass


def intCheck():
    """Keine Netztests mehr im GUI-Thread."""
    return True


class GradientStarX(VariableValue, Renderer):
    GUI_WIDGET = eSlider

    def __init__(self):
        Renderer.__init__(self)
        VariableValue.__init__(self)
        self.adsl = True
        self.__start = 0
        self.__end = 100
        self.text = ""

    def changed(self, what):
        if what[0] == self.CHANGED_CLEAR:
            (self.range, self.value) = ((0, 1), 0)
            return
        if what[0] != self.CHANGED_CLEAR:
            if self.instance:
                self.instance.hide()
            self._update()

    def _update(self):
        try:
            event = self.source.event
            if not event:
                return
            if PY3:
                evntNm = event.getEventName().replace("\xc2\x86", "").replace("\xc2\x87", "")
            else:
                evntNm = (
                    event.getEventName()
                    .replace("\xc2\x86", "")
                    .replace("\xc2\x87", "")
                    .encode("utf-8")
                )
            slug = convtext(evntNm) if evntNm else None
            if not slug:
                return

            # 1) Cache lesen
            cached_vote = load_tmdb_vote(slug)
            if cached_vote is not None:
                self._set_slider(cached_vote)
                return

            # 2) Von TMDb holen und in Info-JSON speichern
            vote = self._fetch_tmdb_vote(evntNm)
            if vote is not None:
                save_tmdb_vote(slug, vote)
                self._set_slider(vote)
        except Exception as e:
            print("GradientStarX _update exception:", e)

    def _fetch_tmdb_vote(self, title):
        if not tmdb_api or not title:
            return None
        try:
            q = quoteEventName(title)
            url = "http://api.themoviedb.org/3/search/multi?api_key=%s&query=%s" % (
                tmdb_api,
                q,
            )
            if lng:
                url += "&language=%s" % lng
            r = requests.get(url, timeout=(5.0, 10.0))
            r.raise_for_status()
            data = r.json()
            results = data.get("results") or []
            if not results:
                return None
            first = results[0]
            vote = first.get("vote_average")
            if vote is None:
                return None
            return float(vote)
        except Exception:
            return None

    def _set_slider(self, vote_average):
        try:
            # Skala 0..10 -> 0..100
            rtng = int(10 * float(vote_average))
            (self.range, self.value) = ((0, 100), rtng)
            if self.instance:
                self.instance.show()
        except Exception as e:
            print("GradientStarX _set_slider exception:", e)

    def postWidgetCreate(self, instance):
        instance.setRange(self.__start, self.__end)

    def setRange(self, range_):
        (self.__start, self.__end) = range_
        if self.instance is not None:
            self.instance.setRange(self.__start, self.__end)

    def getRange(self):
        return self.__start, self.__end
