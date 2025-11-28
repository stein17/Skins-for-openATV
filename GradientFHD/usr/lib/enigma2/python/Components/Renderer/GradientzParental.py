#!/usr/bin/python
# -*- coding: utf-8 -*-

# <widget render="zParental" source="session.Event_Now" position="315,874" size="50,50" zPosition="3" transparent="1" alphatest="blend"/>
from __future__ import print_function
from Components.Renderer.Renderer import Renderer
from Components.config import config
from enigma import ePixmap, eTimer, loadPNG
import json
import os
import re
import sys
from .GradientConverlibr import convtext

PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True


def isMountedInRW(mount_point):
    with open("/proc/mounts", "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) > 1 and parts[1] == mount_point:
                return True
    return False


curskin = config.skin.primary_skin.value.replace('/skin.xml', '')
pratePath = '/usr/share/enigma2/%s/parental' % curskin
path_folder = "/tmp/poster"
if os.path.exists("/media/hdd"):
    if isMountedInRW("/media/hdd"):
        path_folder = "/media/hdd/poster"
elif os.path.exists("/media/usb"):
    if isMountedInRW("/media/usb"):
        path_folder = "/media/usb/poster"
elif os.path.exists("/media/mmc"):
    if isMountedInRW("/media/mmc"):
        path_folder = "/media/mmc/poster"

if not os.path.exists(path_folder):
    os.makedirs(path_folder)


class GradientzParental(Renderer):

    def __init__(self):
        Renderer.__init__(self)

    GUI_WIDGET = ePixmap

    def changed(self, what):
        if not self.instance:
            return
        if what[0] == self.CHANGED_CLEAR:
            self.instance.hide()
        if what[0] != self.CHANGED_CLEAR:
            self.delay()

    def showParental(self):
        self.event = self.source.event
        if not self.event:
            return
        fd = "%s\n%s\n%s" % (
            self.event.getEventName(),
            self.event.getShortDescription(),
            self.event.getExtendedDescription()
        )
        try:
            age = re.search(r"\d{1,2}\+", fd)
            cert = None

            if age:
                cert = re.sub(r"\+", "", age.group()).strip()
            else:
                try:
                    if PY3:
                        eventNm = self.event.getEventName().replace('\xc2\x86', '').replace('\xc2\x87', '')
                    else:
                        eventNm = self.event.getEventName().replace('\xc2\x86', '').replace('\xc2\x87', '').encode('utf-8')

                    self.pstcanal = convtext(eventNm) if eventNm else None
                    if not self.pstcanal:
                        # print('Event non trovato per la visualizzazione del poster')
                        return

                    infos_file = "%s%s.json" % (path_folder, self.pstcanal)
                    if os.path.exists(infos_file):
                        with open(infos_file, "r") as f:
                            age = json.load(f).get('Rated', '')
                            cert = {
                                "TV-G": "0", "G": "0", "TV-Y7": "6", "TV-Y": "6", "TV-10": "10",
                                "TV-12": "12", "TV-14": "14", "TV-PG": "16", "PG-13": "16", "PG": "16",
                                "TV-MA": "18", "R": "18", "N/A": "UN", "Not Rated": "UN",
                                "Unrated": "UN", "": "UN", "Passed": "UN"
                            }.get(age, "UN")
                except Exception as e:
                    pass
                    # print("Errore durante la lettura delle informazioni sul rating:", e)

            if cert:
                self.instance.setPixmap(loadPNG(os.path.join(pratePath, "FSK_%s.png" % cert)))
                self.instance.show()
            else:
                self.instance.hide()
        except Exception as e:
            pass
            # print("Error in showParental:", e)
            self.instance.hide()

    def delay(self):
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.showParental)
        except AttributeError:
            self.timer.callback.append(self.showParental)
        self.timer.start(10, True)
