#!/usr/bin/python
# -*- coding: utf-8 -*-

# by digiteng
# v1 07.2020, 11.2021
# recode from lululla 2022
# for channellist
# <widget source="ServiceEvent" render="GradientiStarX" position="750,390" size="200,20" alphatest="blend" transparent="1" zPosition="3" />
# or
# <widget source="ServiceEvent" render="GradientiStarX" pixmap="xtra/star.png" position="750,390" size="200,20" alphatest="blend" transparent="1" zPosition="3" />
# edit lululla 05-2022
# <ePixmap pixmap="oZeta-FHD/star.png" position="136,104" size="200,20" alphatest="blend" zPosition="10" transparent="1" />
# <widget source="session.Event_Now" render="GradientiStarX" pixmap="oZeta-FHD/menu/staryellow.png" position="560,367" size="200,20" alphatest="blend" transparent="1" zPosition="3" />
# <ePixmap pixmap="menu/stargrey.png" position="136,104" size="200,20" alphatest="blend" zPosition="10" transparent="1" />
# <widget source="session.Event_Next" render="GradientiStarX" pixmap="oZeta-FHD/menu/staryellow.png" position="560,367" size="200,20" alphatest="blend" transparent="1" zPosition="3" />

from __future__ import print_function
from Components.Renderer.Renderer import Renderer
# from Components.Sources.Event import Event
# from Components.Sources.EventInfo import EventInfo
# from Components.Sources.ServiceEvent import ServiceEvent
from Components.VariableValue import VariableValue
from Components.config import config
from enigma import eSlider
import json
import os
import socket
import sys
from .GradientiConverlibr import convtext, quoteEventName

global cur_skin, my_cur_skin, tmdb_api
PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True
    from urllib.request import urlopen
    from urllib.error import HTTPError, URLError
else:
    from urllib2 import urlopen
    from urllib2 import HTTPError, URLError


try:
    lng = config.osd.language.value
    lng = lng[:-3]
except:
    lng = 'en'
    pass
print('language: ', lng)


formatImg = 'w185'
tmdb_api = "3c3efcf47c3577558812bb9d64019d65"
omdb_api = "cb1d9f55"
thetvdbkey = 'D19315B88B2DE21F'
# thetvdbkey = "a99d487bb3426e5f3a60dea6d3d3c7ef"


def isMountedInRW(mount_point):
    with open("/proc/mounts", "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) > 1 and parts[1] == mount_point:
                return True
    return False


my_cur_skin = False
cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')

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


try:
    if my_cur_skin is False:
        skin_paths = {
            "tmdb_api": "/usr/share/enigma2/{}/tmdbkey".format(cur_skin),
            "omdb_api": "/usr/share/enigma2/{}/omdbkey".format(cur_skin),
            "thetvdbkey": "/usr/share/enigma2/{}/thetvdbkey".format(cur_skin)
        }
        for key, path in skin_paths.items():
            if os.path.exists(path):
                with open(path, "r") as f:
                    value = f.read().strip()
                    if key == "tmdb_api":
                        tmdb_api = value
                    elif key == "omdb_api":
                        omdb_api = value
                    elif key == "thetvdbkey":
                        thetvdbkey = value
                my_cur_skin = True
except Exception as e:
    print("Errore nel caricamento delle API:", str(e))
    my_cur_skin = False


def intCheck():
    try:
        response = urlopen("http://google.com", None, 5)
        response.close()
    except HTTPError:
        return False
    except URLError:
        return False
    except socket.timeout:
        return False
    return True


class GradientiStarX(VariableValue, Renderer):

    def __init__(self):
        Renderer.__init__(self)
        VariableValue.__init__(self)
        self.adsl = intCheck()
        if not self.adsl:
            print("Connessione assente, modalità offline.")
            return
        else:
            print("Connessione rilevata.")
        self.__start = 0
        self.__end = 100
        self.text = ""

    GUI_WIDGET = eSlider

    def changed(self, what):
        if what[0] == self.CHANGED_CLEAR:
            (self.range, self.value) = ((0, 1), 0)
            return
        if what[0] != self.CHANGED_CLEAR:
            print('zstar event B what[0] != self.CHANGED_CLEAR')
            if self.instance:
                self.instance.hide()
            self.infos()

    def infos(self):
        try:
            self.event = self.source.event
            if not self.event:
                return
            if PY3:
                self.evntNm = self.event.getEventName().replace('\xc2\x86', '').replace('\xc2\x87', '')
            else:
                self.evntNm = self.event.getEventName().replace('\xc2\x86', '').replace('\xc2\x87', '').encode('utf-8')
            self.pstcanal = convtext(self.evntNm) if self.evntNm else None
            if not self.pstcanal:
                print('Evento non trovato per la visualizzazione del poster')
                return
            dwn_infos = "%s/%s" % (path_folder, self.pstcanal)
            if not os.path.exists(dwn_infos):
                self.download_and_save_info(dwn_infos)
            else:
                data = self.load_info_from_file(dwn_infos)
                self.process_data(data)
        except Exception as e:
            print("General Exception in infos: ", e)

    def download_and_save_info(self, dwn_infos):

        try:
            url = "http://api.themoviedb.org/3/search/multi?api_key=%s&query=%s" % (tmdb_api, quoteEventName(self.evntNm))
            url_data = json.load(urlopen(url))
            if url_data.get('results'):
                movie_id = url_data['results'][0]['id']
                data = self.fetch_movie_data(movie_id)
                open(dwn_infos, "w").write(json.dumps(data))
        except Exception as e:
            print("Download Exception: ", e)

    def fetch_movie_data(self, movie_id):
        movie_url = "https://api.themoviedb.org/3/movie/%s?api_key=%s&append_to_response=credits&language=%s" % (movie_id, tmdb_api, lng)
        return json.load(urlopen(movie_url))

    def load_info_from_file(self, filepath):
        with open(filepath, "r") as f:
            return json.load(f)

    def process_data(self, data):
        try:
            ImdbRating = data.get('vote_average', '0')
            if ImdbRating and ImdbRating != '0':
                rtng = int(10 * float(ImdbRating))
            else:
                rtng = 0
            (self.range, self.value) = ((0, 100), rtng)
            self.instance.show()
        except Exception as e:
            print("Process Data Exception: ", e)

    def postWidgetCreate(self, instance):
        instance.setRange(self.__start, self.__end)

    def setRange(self, range):
        (self.__start, self.__end) = range
        if self.instance is not None:
            self.instance.setRange(self.__start, self.__end)

    def getRange(self):
        return self.__start, self.__end
