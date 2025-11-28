#!/usr/bin/python
# -*- coding: utf-8 -*-

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
import time
from .GradientPosterXDownloadThread import GradientPosterXDownloadThread
from .GradientConverlibr import convtext, cutName

PY3 = sys.version_info[0] >= 3
epgcache = eEPGCache.getInstance()

try:
    lng = config.osd.language.value
    lng = lng[:-3]
except Exception:
    lng = None


def get_emc_folder():
    if os.path.isdir("/media/hdd"):
        return "/media/hdd/imovie/"
    if os.path.isdir("/media/usb"):
        return "/media/usb/imovie/"
    return "/tmp/imovie/"


EMC_FOLDER = get_emc_folder()
if not os.path.exists(EMC_FOLDER):
    try:
        os.makedirs(EMC_FOLDER)
    except OSError:
        pass


class GradientPosterXEMC(Renderer):
    """
    Poster für EMC:
    - speichert Poster als .jpg neben den Aufnahmen (im EMC_FOLDER)
    - nutzt GradientPosterXDownloadThread
    """

    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.canal = [None] * 6
        self.timer = eTimer()
        try:
            self.timer.timeout.connect(self._showPoster)
        except Exception:
            self.timer.callback.append(self._showPoster)
        self.worker = None

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

            if isinstance(src, ServiceEvent):
                event = src.event
                svc = src.service
                if svc:
                    path = svc.getPath()
            elif isinstance(src, CurrentService):
                ref = src.getCurrentServiceReference()
                if ref:
                    path = ref.getPath()
            else:
                self.instance.hide()
                return

            if not path:
                self.instance.hide()
                return

            base = path.split(".ts")[0]
            poster_path = base + ".jpg"

            self.canal[5] = poster_path

            if os.path.exists(poster_path) and os.path.getsize(poster_path) > 0:
                self._showFile(poster_path)
                return

            # Titel möglichst aus Event holen
            if event:
                name = event.getEventName().replace("\xc2\x86", "").replace("\xc2\x87", "")
                short = event.getShortDescription() or ""
                ext = event.getExtendedDescription() or ""
            else:
                name = os.path.basename(base)
                short = ""
                ext = ""

            query = cutName(name) or name

            self.instance.hide()
            self._startWorker(poster_path, None, query, short, ext, None)
        except Exception:
            self.instance.hide()

    def _startWorker(self, dest_path, slug, query, short, ext, channel):
        if self.worker and self.worker.is_alive():
            pass
        self.worker = GradientPosterXDownloadThread(dest_path, slug, query, short, ext, channel)
        self.worker.daemon = True
        self.worker.start()
        self.timer.start(200, True)

    def _showPoster(self):
        try:
            poster_path = self.canal[5]
            if poster_path and os.path.exists(poster_path) and os.path.getsize(poster_path) > 0:
                self._showFile(poster_path)
            else:
                self.timer.start(500, True)
        except Exception:
            self.instance.hide()

    def _showFile(self, path):
        try:
            self.instance.setPixmap(loadJPG(path))
            self.instance.setScale(1)
            self.instance.show()
        except Exception:
            self.instance.hide()
