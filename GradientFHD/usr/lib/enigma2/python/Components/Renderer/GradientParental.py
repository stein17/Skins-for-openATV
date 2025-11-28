#!/usr/bin/python
# -*- coding: utf-8 -*-

from Components.Renderer.Renderer import Renderer
from Components.config import config
from enigma import ePixmap, eTimer, loadPNG

import os
import re
import json
import sys

from .GradientConverlibr import convtext

PY3 = sys.version_info[0] >= 3


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


_cur_skin = config.skin.primary_skin.value.replace("/skin.xml", "")
ICON_PATH = "/usr/share/enigma2/%s/parental" % _cur_skin


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


EPG_AGE_PATTERNS = [
    re.compile(r"[aA]b\s+(\d+)"),                              # "ab 12"
    re.compile(r"\b(\d{1,2})\+\b"),                            # "12+"
    re.compile(r"Od lat:\s*(\d+)", re.IGNORECASE),             # "Od lat: 12"
    re.compile(r"FSK\s*(\d+)", re.IGNORECASE),                 # "FSK 12"
    re.compile(r"ab\s*(\d{1,2})\s*(?:J|Jahre)", re.IGNORECASE) # "ab 12 Jahren"
]


def extract_age_from_epg_text(text):
    if not text:
        return None
    for rx in EPG_AGE_PATTERNS:
        m = rx.search(text)
        if m:
            age = m.group(1)
            return age.replace("7", "6")
    return None


RATING_MAP = {
    "TV-G": "0",
    "G": "0",
    "TV-Y7": "6",
    "TV-Y": "6",
    "TV-10": "10",
    "TV-12": "12",
    "TV-14": "14",
    "TV-PG": "16",
    "PG-13": "16",
    "PG": "16",
    "TV-MA": "18",
    "R": "18",
    "N/A": "NA",
    "Not Rated": "NA",
    "Unrated": "NA",
    "NA": "NA",
    "Passed": "NA",
    "": "NA",
}


def map_rated_to_fsk(rated):
    if not rated:
        return None
    rated = rated.strip()
    if rated in RATING_MAP:
        return RATING_MAP[rated]
    if rated.isdigit():
        return rated
    return "NA"


def load_rated(slug):
    if not slug:
        return None
    path = os.path.join(INFO_FOLDER, slug + ".json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
        rated = (data.get("Rated") or "").strip()
        return rated or None
    except Exception:
        return None


class GradientParental(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.timer = None

    def changed(self, what):
        if not self.instance:
            return
        if what[0] == self.CHANGED_CLEAR:
            self.instance.hide()
            return
        if self.timer is None:
            self.timer = eTimer()
            try:
                self.timer.timeout.connect(self._update)
            except AttributeError:
                self.timer.callback.append(self._update)
        self.timer.start(10, True)

    def _update(self):
        event = getattr(self.source, "event", None)
        if not event:
            self._set_icon(None)
            return

        name = event.getEventName() or ""
        short = event.getShortDescription() or ""
        ext = event.getExtendedDescription() or ""
        full_text = "%s\n%s\n%s" % (name, short, ext)

        # 1) EPG
        age = extract_age_from_epg_text(full_text)
        if age:
            self._set_icon(age)
            return

        # 2) Rated aus Info-JSON
        if PY3:
            clean_name = name.replace("\xc2\x86", "").replace("\xc2\x87", "")
        else:
            clean_name = name.replace("\xc2\x86", "").replace("\xc2\x87", "").encode("utf-8")

        slug = convtext(clean_name) if clean_name else None
        rated = load_rated(slug) if slug else None

        if rated:
            age_from_rated = map_rated_to_fsk(rated)
            self._set_icon(age_from_rated)
        else:
            self._set_icon(None)

    def _set_icon(self, age_str):
        if age_str:
            icon_name = "FSK_%s.png" % age_str
        else:
            icon_name = "FSK_NA.png"

        icon_path = os.path.join(ICON_PATH, icon_name)
        if os.path.exists(icon_path):
            try:
                self.instance.setPixmap(loadPNG(icon_path))
                self.instance.setScale(1)
                self.instance.show()
            except Exception:
                self.instance.hide()
        else:
            self.instance.hide()
