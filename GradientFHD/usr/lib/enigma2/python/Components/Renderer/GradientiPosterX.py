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
from .GradientiConverlibr import convtext, cutName, REGEX

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
    os.makedirs(path_folder)


epgcache = eEPGCache.getInstance()
apdb = dict()


try:
    lng = config.osd.language.value
    lng = lng[:-3]
except:
    lng = 'en'
    pass


# SET YOUR PREFERRED BOUQUET FOR AUTOMATIC POSTER GENERATION
# WITH THE NUMBER OF ITEMS EXPECTED (BLANK LINE IN BOUQUET CONSIDERED)
# IF NOT SET OR WRONG FILE THE AUTOMATIC POSTER GENERATION WILL WORK FOR
# THE CHANNELS THAT YOU ARE VIEWING IN THE ENIGMA SESSION

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
        print("File non trovato:", autobouquet_file)
        return {}

    try:
        with open(autobouquet_file, 'r') as f:
            lines = f.readlines()
    except (IOError, OSError) as e:
        print("Errore nella lettura del file:", e)
        return {}

    autobouquet_count = min(autobouquet_count, len(lines))

    for i, line in enumerate(lines[:autobouquet_count]):
        if line.startswith('#SERVICE'):
            parts = line[9:].strip().split(':')
            if len(parts) == 11 and ':'.join(parts[3:7]) != '0:0:0:0':
                apdb[i] = ':'.join(parts)

    print("Trovati", len(apdb), "servizi validi.")
    return apdb


# Esecuzione della funzione
apdb = process_autobouquet()


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
            self.logDB("[QUEUE] : {} : {}-{} ({})".format(canal[0], canal[1], canal[2], canal[5]))
            self.pstcanal = convtext(canal[5])

            if self.pstcanal is not None:
                dwn_poster = os.path.join(path_folder, self.pstcanal + ".jpg")
            else:
                print("None type detected - poster not found")
                pdb.task_done()  # Per evitare il blocco del thread
                continue

            if os.path.exists(dwn_poster):
                os.utime(dwn_poster, (time.time(), time.time()))

            if not os.path.exists(dwn_poster):
                val, log = self.search_tmdb(dwn_poster, self.pstcanal, canal[4], canal[3])
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_tvdb(dwn_poster, self.pstcanal, canal[4], canal[3])
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_fanart(dwn_poster, self.pstcanal, canal[4], canal[3])
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_imdb(dwn_poster, self.pstcanal, canal[4], canal[3])
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_google(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                self.logDB(log)
            elif not os.path.exists(dwn_poster):
                val, log = self.search_omdb(dwn_poster, self.pstcanal, canal[4], canal[3])
                self.logDB(log)
            pdb.task_done()

    def logDB(self, logmsg):
        try:
            with open("/tmp/PosterDB.log", "a") as w:
                w.write("%s\n" % logmsg)
        except Exception as e:
            print("logDB error:", str(e))
            traceback.print_exc()


threadDB = PosterDB()
threadDB.start()


class PosterAutoDB(GradientiPosterXDownloadThread):
    def __init__(self):
        GradientiPosterXDownloadThread.__init__(self)
        self.logdbg = None
        self.pstcanal = None

    def run(self):
        self.logAutoDB("[AutoDB] *** Initialized ***")
        while True:
            time.sleep(7200)  # 7200 - Start every 2 hours
            self.logAutoDB("[AutoDB] *** Running ***")
            self.pstcanal = None
            # AUTO ADD NEW FILES - 1440 (24 hours ahead)
            for service in apdb.values():
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
                                print("None type detected - poster not found")
                                continue

                            if os.path.exists(dwn_poster):
                                os.utime(dwn_poster, (time.time(), time.time()))

                            if not os.path.exists(dwn_poster):
                                val, log = self.search_tmdb(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                                if val and log.find("SUCCESS"):
                                    newfd += 1
                                else:
                                    self.logAutoDB("[AutoDB] Failed to find poster for event: {}".format(canal[5]))
                            elif not os.path.exists(dwn_poster):
                                val, log = self.search_tvdb(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                                if val and log.find("SUCCESS"):
                                    newfd += 1
                                else:
                                    self.logAutoDB("[AutoDB] Failed to find poster for event: {}".format(canal[5]))
                            elif not os.path.exists(dwn_poster):
                                val, log = self.search_fanart(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                                if val and log.find("SUCCESS"):
                                    newfd += 1
                                else:
                                    self.logAutoDB("[AutoDB] Failed to find poster for event: {}".format(canal[5]))
                            elif not os.path.exists(dwn_poster):
                                val, log = self.search_imdb(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                                if val and log.find("SUCCESS"):
                                    newfd += 1
                                else:
                                    self.logAutoDB("[AutoDB] Failed to find poster for event: {}".format(canal[5]))
                            elif not os.path.exists(dwn_poster):
                                val, log = self.search_google(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                                if val and log.find("SUCCESS"):
                                    newfd += 1
                                else:
                                    self.logAutoDB("[AutoDB] Failed to find poster for event: {}".format(canal[5]))
                            elif not os.path.exists(dwn_poster):
                                val, log = self.search_omdb(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0])
                                if val and log.find("SUCCESS"):
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
                diff_tm = now_tm - os.path.getmtime(file_path)
                if diff_tm > 120 and os.path.getsize(file_path) == 0:
                    os.remove(file_path)
                    emptyfd += 1
                elif diff_tm > 63072000:
                    os.remove(file_path)
                    oldfd += 1
            self.logAutoDB("[AutoDB] {} old file(s) removed".format(oldfd))
            self.logAutoDB("[AutoDB] {} empty file(s) removed".format(emptyfd))
            self.logAutoDB("[AutoDB] *** Stopping ***")

    def logAutoDB(self, logmsg):
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("/tmp/PosterAutoDB.log", "a") as w:
                w.write("[{}] {}\n".format(timestamp, logmsg))
        except Exception as e:
            print("logAutoDB error: {}".format(e))
            traceback.print_exc()


threadAutoDB = PosterAutoDB()
threadAutoDB.start()


class GradientiPosterX(Renderer):
    def __init__(self):
        Renderer.__init__(self)
        self.adsl = intCheck()
        if not self.adsl:
            print("Connessione assente, modalità offline.")
            return
        else:
            print("Connessione rilevata.")
        self.nxts = 0
        self.path = path_folder  # + '/'
        self.canal = [None, None, None, None, None, None]
        self.oldCanal = None
        self.logdbg = None
        self.pstcanal = None
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.showPoster)
        except:
            self.timer.callback.append(self.showPoster)

    def applySkin(self, desktop, parent):
        attribs = []
        for (attrib, value,) in self.skinAttributes:
            if attrib == "nexts":
                self.nxts = int(value)
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
            if source_type is ServiceEvent:  # source="ServiceEvent"
                service = self.source.getCurrentService()
                servicetype = "ServiceEvent"
            elif source_type is CurrentService:  # source="session.CurrentService"
                service = self.source.getCurrentServiceRef()
                servicetype = "CurrentService"
            elif source_type is EventInfo:  # source="session.Event_Now" or source="session.Event_Next"
                service = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
                servicetype = "EventInfo"
            elif source_type is Event:  # source="Event"
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

                if not autobouquet_file and service_name not in apdb:
                    apdb[service_name] = service_str

        except Exception as e:
            print("Error (service):", str(e))
            if self.instance:
                self.instance.hide()
            return
        if not servicetype:
            print("Error: service type undefined")
            if self.instance:
                self.instance.hide()
            return

        try:
            curCanal = "{}-{}".format(self.canal[1], self.canal[2])
            if curCanal == self.oldCanal:
                return

            self.oldCanal = curCanal
            self.logPoster("Service: {} [{}] : {} : {}".format(servicetype, self.nxts, self.canal[0], self.oldCanal))

            self.pstcanal = convtext(self.canal[5])
            if self.pstcanal is not None:
                self.pstrNm = os.path.join(self.path, str(self.pstcanal) + ".jpg")
                self.pstcanal = self.pstrNm

            if os.path.exists(self.pstcanal):
                self.timer.start(10, True)
            else:
                canal = self.canal[:]
                pdb.put(canal)
                start_new_thread(self.waitPoster, ())

        except Exception as e:
            print("Error (eFile):", str(e))
            if self.instance:
                self.instance.hide()
            return

    def generatePosterPath(self):
        """Genera il percorso completo per il poster."""
        if self.canal[5]:
            pstcanal = convtext(self.canal[5])
            return os.path.join(self.path, str(pstcanal) + ".jpg")
        return None

    def showPoster(self):
        if self.instance:
            self.instance.hide()
        self.pstrNm = self.generatePosterPath()
        if self.pstrNm and os.path.exists(self.pstrNm):
            print('showPoster----')
            self.logPoster("[LOAD : showPoster] " + self.pstrNm)
            self.instance.setPixmap(loadJPG(self.pstrNm))
            self.instance.setScale(1)
            self.instance.show()

    def waitPoster(self):
        if self.instance:
            self.instance.hide()

        self.pstrNm = self.generatePosterPath()
        if self.pstrNm:
            loop = 180  # Numero massimo di tentativi
            found = False
            self.logPoster("[LOOP: waitPoster] " + self.pstrNm)

            while loop > 0:
                if os.path.exists(self.pstrNm):
                    found = True
                    break
                time.sleep(0.5)
                loop -= 1

            if found:
                self.timer.start(10, True)            
            
    def logPoster(self, logmsg):
        try:
            with open("/tmp/xtra_Poster.log", "a") as w:
                w.write("%s\n" % logmsg)
        except Exception as e:
            print('logPoster error', str(e))
            traceback.print_exc()        

    def search_omdb(self, dwn_poster, title, shortdesc, fulldesc, channel=None):
        try:
            self.dwn_poster = dwn_poster
            title_safe = title.replace('+', ' ')
            url = f"http://www.omdbapi.com/?apikey={omdb_api}&t={title_safe}"
            headers = {'User-Agent': getRandomUserAgent()}
            response = requests.get(url, headers=headers, timeout=(10, 20))
            response.raise_for_status()
            if response.status_code == requests.codes.ok:
                data = response.json()
                if 'Poster' in data and data['Poster'] != 'N/A':
                    poster_url = data['Poster']
                    callInThread(self.savePoster, poster_url, self.dwn_poster)
                    return True, f"[SUCCESS poster: omdb] title {title_safe} => {poster_url}"
                else:
                    return False, f"[SKIP : omdb] {title_safe} => Poster not found"
            else:
                return False, f"Errore durante la ricerca su OMDB: {response.status_code}"
        except Exception as e:
            print('Errore nella ricerca OMDB:', e)
            return False, "Errore durante la ricerca su OMDB"


def findPoster(eventName):
    # Clean the event name using cutName function
    cleanedName = cutName(eventName)
    # Match the cleaned name against the regex triggers
    if REGEX.search(cleanedName):
        # Proceed with finding the poster
        # ...existing code to find and download the poster...
        pass
    else:
        print(f"No match found for event name: {cleanedName}")

# Example usage
eventName = "1737847083-KARAMELLA"
findPoster(eventName)