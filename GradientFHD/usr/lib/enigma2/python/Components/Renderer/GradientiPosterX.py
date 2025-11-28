#!/usr/bin/python
# -*- coding: utf-8 -*-

# by digiteng...07.2021,
# 08.2021(stb lang support),
# 09.2021 mini fixes
# edit by lululla 07.2022
# recode from lululla 2023
# © Provided that digiteng rights are protected, all or part of the code can be used, modified...
# russian and py3 support by sunriser...
# downloading in the background while zaping...
# by beber...03.2022,
# 03.2022 several enhancements : several renders with one queue thread, google search (
# for infobar,
# <widget source="session.Event_Now" render="GradientiPosterX" position="100,100" size="185,278" />
# <widget source="session.Event_Next" render="GradientiPosterX" position="100,100" size="100,150" />
# <widget source="session.Event_Now" render="GradientiPosterX" position="100,100" size="185,278" nexts="2" />
# <widget source="session.CurrentService" render="GradientiPosterX" position="100,100" size="185,278" nexts="3" />

# for ch,
# <widget source="ServiceEvent" render="GradientiPosterX" position="100,100" size="185,278" />
# <widget source="ServiceEvent" render="GradientiPosterX" position="100,100" size="185,278" nexts="2" />

# for epg, event
# <widget source="Event" render="GradientiPosterX" position="100,100" size="185,278" />
# <widget source="Event" render="GradientiPosterX" position="100,100" size="185,278" nexts="2" />
# or put tag -->  path="/media/hdd/poster"

# by digiteng...07.2021, modified for fixes

from __future__ import print_function
from Components.Renderer.Renderer import Renderer
from Components.Renderer.GradientiPosterXDownloadThread import GradientiPosterXDownloadThread
from Components.Sources.CurrentService import CurrentService
from Components.Sources.Event import Event
from Components.Sources.EventInfo import EventInfo
from Components.Sources.ServiceEvent import ServiceEvent
from Components.config import config
from ServiceReference import ServiceReference
from enigma import (
    ePixmap,
    loadJPG,
    eEPGCache,
    eTimer,
)
import NavigationInstance
import os
import socket
import sys
import time
import traceback
import datetime
from .GradientConverlibr import convtext, cutName, REGEX

PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True
    import queue
    from _thread import start_new_thread
    from urllib.error import HTTPError, URLError
    from urllib.request import urlopen
else:
    import Queue as queue
    from Queue import LifoQueue as LifoQueue
    from thread import start_new_thread
    from urllib2 import HTTPError, URLError
    from urllib2 import urlopen


epgcache = eEPGCache.getInstance()
if PY3:
    pdb = queue.LifoQueue()
else:
    pdb = queue.LifoQueue()

# quiet by default; set True to enable debug prints in renderer
DEBUG_POSTER = False

def isMountedInRW(mount_point):
    with open("/proc/mounts", "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) > 1 and parts[1] == mount_point:
                return True
    return False


cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')
noposter = "/usr/share/enigma2/%s/main/noposter.jpg" % cur_skin
path_folder = "/tmp/poster"
if os.path.exists("/media/hdd"):
    if isMountedInRW("/media/hdd"):
        path_folder = "/media/hdd/xtra/poster"
elif os.path.exists("/media/usb"):
    if isMountedInRW("/media/usb"):
        path_folder = "/media/usb/xtra/poster"
elif os.path.exists("/media/mmc"):
    if isMountedInRW("/media/mmc"):
        path_folder = "/media/mmc/xtra/poster"

if not os.path.exists(path_folder):
    try:
        os.makedirs(path_folder, exist_ok=True)
    except Exception:
        pass


epgcache = eEPGCache.getInstance()
apdb = dict()


try:
    lng = config.osd.language.value
    lng = lng[:-3]
except:
    lng = 'en'
    pass


def SearchBouquetTerrestrial():
    import glob
    import codecs
    file = '/etc/enigma2/userbouquet.favourites.tv'
    for file in sorted(glob.glob('/etc/enigma2/*.tv')):
        with codecs.open(file, "r", encoding="utf-8") as f:
            file = f.read()
            x = file.strip().lower()
            if x.find('eeee') != -1:
                if x.find('82000') == -1 and x.find('c0000') == -1:
                    return file
                    break


autobouquet_file = None


def process_autobouquet():
    global autobouquet_file
    autobouquet_file = SearchBouquetTerrestrial() or '/etc/enigma2/userbouquet.favourites.tv'
    autobouquet_count = 70
    apdb = {}

    if not os.path.exists(autobouquet_file):
        if DEBUG_POSTER:
            print("File non trovato:", autobouquet_file)
        return {}

    try:
        with open(autobouquet_file, 'r') as f:
            lines = f.readlines()
    except (IOError, OSError) as e:
        if DEBUG_POSTER:
            print("Errore nella lettura del file:", e)
        return {}

    autobouquet_count = min(autobouquet_count, len(lines))

    for i, line in enumerate(lines[:autobouquet_count]):
        if line.startswith('#SERVICE'):
            parts = line[9:].strip().split(':')
            if len(parts) == 11 and ':'.join(parts[3:7]) != '0:0:0:0':
                apdb[i] = ':'.join(parts)

    if DEBUG_POSTER:
        print("Trovati", len(apdb), "servizi validi.")
    return apdb


# Esecuzione della funzione
apdb = process_autobouquet()


# fast non-blocking connectivity check (socket)
def intCheck():
    try:
        sock = socket.create_connection(("8.8.8.8", 53), timeout=1)
        sock.close()
        return True
    except Exception:
        return False


omdb_api = "6a4c9432"


class PosterDB(GradientiPosterXDownloadThread):
    def __init__(self):
        GradientiPosterXDownloadThread.__init__(self)
        self.logdbg = None
        self.pstcanal = None

    def run(self):
        self.logDB("[QUEUE] : Initialized")
        while True:
            canal = pdb.get()
            try:
                self.logDB("[QUEUE] : {} : {}-{} ({})".format(canal[0], canal[1], canal[2], canal[5]))
            except Exception:
                self.logDB("[QUEUE] : queue item malformed")
            self.pstcanal = convtext(canal[5]) if canal and len(canal) > 5 else None

            if self.pstcanal is not None:
                dwn_poster = os.path.join(path_folder, self.pstcanal + ".jpg")
            else:
                if DEBUG_POSTER:
                    print("None type detected - poster not found")
                pdb.task_done()
                continue

            if os.path.exists(dwn_poster):
                try:
                    os.utime(dwn_poster, (time.time(), time.time()))
                except Exception:
                    pass

            if not os.path.exists(dwn_poster):
                val, log = self.search_tmdb(dwn_poster, self.pstcanal, canal[4] if len(canal)>4 else None, canal[3] if len(canal)>3 else None)
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_tvdb(dwn_poster, self.pstcanal, canal[4] if len(canal)>4 else None, canal[3] if len(canal)>3 else None)
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_fanart(dwn_poster, self.pstcanal, canal[4] if len(canal)>4 else None, canal[3] if len(canal)>3 else None)
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_imdb(dwn_poster, self.pstcanal, canal[4] if len(canal)>4 else None, canal[3] if len(canal)>3 else None)
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_google(dwn_poster, self.pstcanal, canal[4] if len(canal)>4 else None, canal[3] if len(canal)>3 else None, canal[0] if len(canal)>0 else None)
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_omdb(dwn_poster, self.pstcanal, canal[4] if len(canal)>4 else None, canal[3] if len(canal)>3 else None)
                self.logDB(log)
            pdb.task_done()

    def logDB(self, logmsg):
        try:
            with open("/tmp/PosterDB.log", "a") as w:
                w.write("%s\n" % logmsg)
        except Exception as e:
            if DEBUG_POSTER:
                print("logDB error:", str(e))
                traceback.print_exc()


threadDB = PosterDB()
threadDB.start()


class PosterAutoDB(GradientiPosterXDownloadThread):
    def __init__(self):
        GradientiPosterXDownloadThread.__init__(self)
        self.logdbg = None
        self.pstcanal = None

    def logAutoDB(self, logmsg):
        """Method to log AutoDB messages to /tmp/PosterAutoDB.log"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("/tmp/PosterAutoDB.log", "a") as w:
                w.write("[{}] {}\n".format(timestamp, logmsg))
        except Exception as e:
            if DEBUG_POSTER:
                print("logAutoDB error: {}".format(e))
                traceback.print_exc()

    def run(self):
        self.logAutoDB("[AutoDB] *** Initialized ***")
        while True:
            time.sleep(7200)  # 7200 - Start every 2 hours
            self.logAutoDB("[AutoDB] *** Running ***")
            self.pstcanal = None
            # AUTO ADD NEW FILES - 1440 (24 hours ahead)
            for service in list(apdb.values()):
                try:
                    events = epgcache.lookupEvent(['IBDCTESX', (service, 0, -1, 1440)])
                    newfd = 0
                    newcn = None
                    for evt in events:
                        self.logAutoDB("[AutoDB] evt {} events ({})".format(evt, len(events)))
                        canal = [None] * 6
                        if PY3:
                            canal[0] = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
                        else:
                            canal[0] = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '').encode('utf-8')
                        if evt[1] is None or evt[4] is None or evt[5] is None or evt[6] is None:
                            self.logAutoDB("[AutoDB] *** Missing EPG for {}".format(canal[0]))
                        else:
                            canal[1:6] = [evt[1], evt[4], evt[5], evt[6], evt[4]]
                            self.pstcanal = convtext(canal[5]) if canal[5] else None

                            if self.pstcanal is not None:
                                dwn_poster = os.path.join(path_folder, self.pstcanal + ".jpg")
                            else:
                                if DEBUG_POSTER:
                                    print("None type detected - poster not found")
                                continue

                            if os.path.exists(dwn_poster):
                                try:
                                    os.utime(dwn_poster, (time.time(), time.time()))
                                except Exception:
                                    pass

                            if not os.path.exists(dwn_poster):
                                val, log = self.search_tmdb(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                                if val and "SUCCESS" in log:
                                    newfd += 1
                                else:
                                    self.logAutoDB("[AutoDB] Failed to find poster for event: {}".format(canal[5]))
                            elif not os.path.exists(dwn_poster):
                                val, log = self.search_tvdb(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                                if val and "SUCCESS" in log:
                                    newfd += 1
                                else:
                                    self.logAutoDB("[AutoDB] Failed to find poster for event: {}".format(canal[5]))
                            elif not os.path.exists(dwn_poster):
                                val, log = self.search_fanart(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                                if val and "SUCCESS" in log:
                                    newfd += 1
                                else:
                                    self.logAutoDB("[AutoDB] Failed to find poster for event: {}".format(canal[5]))
                            elif not os.path.exists(dwn_poster):
                                val, log = self.search_imdb(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                                if val and "SUCCESS" in log:
                                    newfd += 1
                                else:
                                    self.logAutoDB("[AutoDB] Failed to find poster for event: {}".format(canal[5]))
                            elif not os.path.exists(dwn_poster):
                                val, log = self.search_google(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                                if val and "SUCCESS" in log:
                                    newfd += 1
                                else:
                                    self.logAutoDB("[AutoDB] Failed to find poster for event: {}".format(canal[5]))
                            elif not os.path.exists(dwn_poster):
                                val, log = self.search_omdb(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                                if val and "SUCCESS" in log:
                                    newfd += 1
                                else:
                                    self.logAutoDB("[AutoDB] Failed to find poster for event: {}".format(canal[5]))
                            newcn = canal[0]

                        self.logAutoDB("[AutoDB] {} new file(s) added ({})".format(newfd, newcn))
                except Exception as e:
                    self.logAutoDB("[AutoDB] *** Service error: {}".format(e))
                    traceback.print_exc()
            # AUTO REMOVE OLD FILES
            now_tm = time.time()
            emptyfd = 0
            oldfd = 0
            for f in os.listdir(path_folder):
                file_path = os.path.join(path_folder, f)
                try:
                    diff_tm = now_tm - os.path.getmtime(file_path)
                except Exception:
                    diff_tm = 0
                if diff_tm > 120 and os.path.getsize(file_path) == 0:
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                    emptyfd += 1
                elif diff_tm > 63072000:
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                    oldfd += 1
            self.logAutoDB("[AutoDB] {} old file(s) removed".format(oldfd))
            self.logAutoDB("[AutoDB] {} empty file(s) removed".format(emptyfd))
            self.logAutoDB("[AutoDB] *** Stopping ***")


threadAutoDB = PosterAutoDB()
threadAutoDB.start()


class GradientiPosterX(Renderer):
    def __init__(self):
        Renderer.__init__(self)
        self.adsl = intCheck()
        if not self.adsl:
            if DEBUG_POSTER:
                print("Connessione assente, modalità offline.")
            return
        else:
            if DEBUG_POSTER:
                print("Connessione rilevata.")
        self.nxts = 0
        self.path = path_folder
        self.canal = [None, None, None, None, None, None]
        self.oldCanal = None
        self.logdbg = None
        self.pstcanal = None
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.showPoster)
        except:
            try:
                self.timer.callback.append(self.showPoster)
            except Exception:
                pass

    def applySkin(self, desktop, parent):
        attribs = []
        for (attrib, value,) in self.skinAttributes:
            if attrib == "nexts":
                try:
                    self.nxts = int(value)
                except Exception:
                    self.nxts = 0
            if attrib == "path":
                self.path = str(value)
            attribs.append((attrib, value))
        self.skinAttributes = attribs
        return Renderer.applySkin(self, desktop, parent)

    GUI_WIDGET = ePixmap

    def changed(self, what):
        if not self.instance:
            return
        if what[0] == self.CHANGED_CLEAR:
            self.instance.hide()
            return

        servicetype = None
        try:
            service = None
            source_type = type(self.source)
            if source_type is ServiceEvent:
                service = self.source.getCurrentService()
                servicetype = "ServiceEvent"
            elif source_type is CurrentService:
                service = self.source.getCurrentServiceRef()
                servicetype = "CurrentService"
            elif source_type is EventInfo:
                service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
                servicetype = "EventInfo"
            elif source_type is Event:
                if self.nxts:
                    service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
                else:
                    self.canal[0] = None
                    self.canal[1] = self.source.event.getBeginTime()
                    event_name = self.source.event.getEventName().replace('\xc2\x86', '').replace('\xc2\x87', '')
                    if not PY3:
                        event_name = event_name.encode('utf-8')
                    self.canal[2] = event_name
                    self.canal[3] = self.source.event.getExtendedDescription()
                    self.canal[4] = self.source.event.getShortDescription()
                    self.canal[5] = event_name
                servicetype = "Event"
            if service is not None:
                service_str = service.toString()
                events = epgcache.lookupEvent(['IBDCTESX', (service_str, 0, -1, -1)])
                service_name = ServiceReference(service).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
                if not PY3:
                    service_name = service_name.encode('utf-8')
                self.canal[0] = service_name
                self.canal[1] = events[self.nxts][1]
                self.canal[2] = events[self.nxts][4]
                self.canal[3] = events[self.nxts][5]
                self.canal[4] = events[self.nxts][6]
                self.canal[5] = self.canal[2]

        except Exception as e:
            if DEBUG_POSTER:
                print("Error (service):", str(e))
            if self.instance:
                self.instance.hide()
            return
        if not servicetype:
            if DEBUG_POSTER:
                print("Error: service type undefined")
            if self.instance:
                self.instance.hide()
            return

        try:
            curCanal = "{}-{}".format(self.canal[1], self.canal[2])
            if curCanal == self.oldCanal:
                return

            self.oldCanal = curCanal
            if DEBUG_POSTER:
                self.logPoster("Service: {} [{}] : {} : {}".format(servicetype, self.nxts, self.canal[0], self.oldCanal))

            self.pstcanal = convtext(self.canal[5]) if self.canal[5] else None
            if self.pstcanal is not None:
                self.pstrNm = os.path.join(self.path, str(self.pstcanal) + ".jpg")
            else:
                self.pstrNm = None

            if self.pstrNm and os.path.exists(self.pstrNm):
                self.timer.start(200, True)
            else:
                canal = self.canal[:]
                pdb.put(canal)
                # Guard: only start one waitPoster thread per renderer instance
                if not getattr(self, "_waiting_poster", False):
                    try:
                        self._waiting_poster = True
                        start_new_thread(self.waitPoster, ())
                    except Exception:
                        self._waiting_poster = False

        except Exception as e:
            if DEBUG_POSTER:
                print("Error (eFile):", str(e))
            if self.instance:
                self.instance.hide()
            return

    def generatePosterPath(self):
        if self.canal[5]:
            pstcanal = convtext(self.canal[5])
            return os.path.join(self.path, str(pstcanal) + ".jpg")
        return None

    def showPoster(self):
        if self.instance:
            self.instance.hide()
        self.pstrNm = self.generatePosterPath()
        if self.pstrNm and os.path.exists(self.pstrNm):
            if DEBUG_POSTER:
                pass
###                 print('showPoster----')
            try:
                self.instance.setPixmap(loadJPG(self.pstrNm))
                self.instance.setScale(1)
                self.instance.show()
            except Exception:
                if DEBUG_POSTER:
                    print("showPoster setPixmap failed")

    def waitPoster(self):
        if self.instance:
            self.instance.hide()

        self.pstrNm = self.generatePosterPath()
        if self.pstrNm:
            loop = 180
            found = False
            self.logPoster("[LOOP: waitPoster] " + self.pstrNm)

            while loop > 0:
                if os.path.exists(self.pstrNm):
                    found = True
                    break
                time.sleep(0.5)
                loop -= 1

            if found:
                self.timer.start(200, True)

        # clear guard flag
        try:
            self._waiting_poster = False
        except Exception:
            pass

    def logPoster(self, logmsg):
        try:
            with open("/tmp/xtra_Poster.log", "a") as w:
                w.write("%s\n" % logmsg)
        except Exception as e:
            if DEBUG_POSTER:
                print('logPoster error', str(e))
                traceback.print_exc()

# end of file
