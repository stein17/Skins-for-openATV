#!/usr/bin/python
# -*- coding: utf-8 -*-

# edit by lululla 07.2022
# recode from lululla 2023
from __future__ import absolute_import
from Components.config import config
from PIL import Image
from enigma import getDesktop
import os
import re
import requests
import socket
import sys
import threading
import unicodedata
import random
import json
from random import choice
from requests import get, exceptions
from twisted.internet.reactor import callInThread
from .iConverlibr import quoteEventName
from Components.Renderer.iConverlibr import cutName, REGEX


try:
    from http.client import HTTPConnection
    HTTPConnection.debuglevel = 0
except ImportError:
    from httplib import HTTPConnection
    HTTPConnection.debuglevel = 0
from requests.adapters import HTTPAdapter, Retry

global my_cur_skin, srch

PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True
    import html
    html_parser = html
else:
    from HTMLParser import HTMLParser
    html = HTMLParser()


try:
    from urllib.error import URLError, HTTPError
    from urllib.request import urlopen
except:
    from urllib2 import URLError, HTTPError
    from urllib2 import urlopen


try:
    lng = config.osd.language.value
    lng = lng[:-3]
except:
    lng = 'en'
    pass


def getRandomUserAgent():
    useragents = [
        'Mozilla/5.0 (compatible; Konqueror/4.5; FreeBSD) KHTML/4.5.4 (like Gecko)',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20120101 Firefox/29.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20120101 Firefox/35.0',
        'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:28.0) Gecko/20100101 Firefox/28.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
        'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; de) Presto/2.9.168 Version/11.52',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
    ]
    return random.choice(useragents)


tmdb_api = "3c3efcf47c3577558812bb9d64019d65"
omdb_api = "6a4c9432"
# thetvdbkey = 'D19315B88B2DE21F'
thetvdbkey = "a99d487bb3426e5f3a60dea6d3d3c7ef"
fanart_api = "6d231536dea4318a88cb2520ce89473b"
my_cur_skin = False
cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')


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


isz = "185,278"
bisz = "300,450"
screenwidth = getDesktop(0).size()
if screenwidth.width() <= 1280:
    isz = isz.replace(isz, "185,278")
    bisz = bisz.replace(bisz, "300,450")
elif screenwidth.width() <= 1920:
    isz = isz.replace(isz, "342,514")
    bisz = bisz.replace(bisz, "780,1170")
else:
    isz = isz.replace(isz, "780,1170")
    bisz = bisz.replace(bisz, "1280,1920")


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


class iPosterXDownloadThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.adsl = intCheck()
        if not self.adsl:
            print("Connessione assente, modalità offline.")
            return
        else:
            print("Connessione rilevata.")
        self.checkMovie = ["film", "movie", "фильм", "кино", "ταινία",
                           "película", "cinéma", "cine", "cinema",
                           "filma"]
        self.checkTV = ["serial", "series", "serie", "serien", "série",
                        "séries", "serious", "folge", "episodio",
                        "episode", "épisode", "l'épisode", "ep.",
                        "animation", "staffel", "soap", "doku", "tv",
                        "talk", "show", "news", "factual",
                        "entertainment", "telenovela", "dokumentation",
                        "dokutainment", "documentary", "informercial",
                        "information", "sitcom", "reality", "program",
                        "magazine", "mittagsmagazin", "т/с", "м/с",
                        "сезон", "с-н", "эпизод", "сериал", "серия",
                        "actualité", "discussion", "interview", "débat",
                        "émission", "divertissement", "jeu", "magasine",
                        "information", "météo", "journal", "sport",
                        "culture", "infos", "feuilleton", "téléréalité",
                        "société", "clips", "concert", "santé",
                        "éducation", "variété"]

    def search_tmdb(self, dwn_poster, title, shortdesc, fulldesc, channel=None):
        try:
            self.dwn_poster = dwn_poster
            title_safe = title.replace('+', ' ')
            url = f"https://api.themoviedb.org/3/search/multi?api_key={tmdb_api}&language={lng}&query={title_safe}"
            headers = {'User-Agent': getRandomUserAgent()}
            response = requests.get(url, headers=headers, timeout=(10, 20), verify=False)
            response.raise_for_status()
            if response.status_code == requests.codes.ok:
                data = response.json()
                self.downloadData2(data)
                return True, "Download successfully started"
            else:
                return False, f"Error when searching on TMDb: {response.status_code}"
        except Exception as e:
            print('TMDb search error:', e)
            return False, "Error when searching on TMDb"

    def downloadData2(self, data):
        if isinstance(data, bytes):
            print("Decoding bytes to string...")
            data = data.decode('utf-8')
        data_json = data if isinstance(data, dict) else json.loads(data)
        if 'results' in data_json:
            try:
                self.sizeb = False
                for each in data_json['results']:
                    media_type = str(each['media_type']) if each.get('media_type') else ''
                    if media_type == "tv":
                        media_type = "serie"
                    if media_type in ['serie', 'movie']:
                        year = ""
                        if media_type == "movie" and 'release_date' in each and each['release_date']:
                            year = each['release_date'].split("-")[0]
                        elif media_type == "serie" and 'first_air_date' in each and each['first_air_date']:
                            year = each['first_air_date'].split("-")[0]
                        title = each.get('name', each.get('title', ''))
                        poster = "http://image.tmdb.org/t/p/w1280" + (each.get('poster_path') or '')
                        poster = "http://image.tmdb.org/t/p/w500" + (each.get('poster_path') or '')
                        rating = str(each.get('vote_average', 0))
                        show_title = title
                        if year:
                            show_title = "{} ({})".format(title, year)
                        # Check if poster and poster are valid before trying to save
                        if poster:
                            callInThread(self.savePoster, poster, self.dwn_poster)
                            print('callinThread=Poster')
                            # self.savePoster(self.dwn_poster, poster)
                            if self.verifyPoster(self.dwn_poster):
                                self.resizePoster(self.dwn_poster)
                            if poster:
                                self.sizeb = True
                                self.pstrNm = path_folder + '/' + self.title_safe + ".jpg"
                                self.dwn_poster = str(self.pstrNm)
                                print('callinThread=Poster')
                                callInThread(self.savePoster, poster, self.dwn_poster)
                                # self.savePoster(self.dwn_poster, poster)
                                if self.verifyPoster(self.dwn_poster):
                                    self.resizePoster(self.dwn_poster)
                            return True, "[SUCCESS poster: tmdb] title {} [poster{}-poster{}] => year{} => rating{} => showtitle{}".format(title, poster, poster, year, rating, show_title)
                    return False, "[SKIP : tmdb] Not found"
            except Exception as e:
                print('error=', e)
                if os.path.exists(self.dwn_poster):
                    os.remove(self.dwn_poster)
                return False, "[ERROR : tmdb]"

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

    def savePoster(self, url, callback):
        headers = {"User-Agent": getRandomUserAgent()}
        try:
            response = get(url.encode(), headers=headers, timeout=(3.05, 6))
            response.raise_for_status()
            with open(callback, "wb") as local_file:
                local_file.write(response.content)
        except exceptions.RequestException as error:
            print("ERROR in module 'download': %s" % (str(error)))
        return callback

    def resizePoster(self, dwn_poster):
        try:
            img = Image.open(dwn_poster)
            width, height = img.size
            ratio = float(width) // float(height)
            new_height = int(isz.split(",")[1])
            new_width = int(ratio * new_height)
            rimg = img.resize((new_width, new_height), Image.LANCZOS)
            img.close()
            rimg.save(dwn_poster)
            rimg.close()
        except Exception as e:
            print("ERROR:{}".format(e))

    def verifyPoster(self, dwn_poster):
        try:
            img = Image.open(dwn_poster)
            img.verify()
            if img.format == "JPEG":
                pass
            else:
                os.remove(dwn_poster)
                return False
        except Exception as e:
            print(e)
            os.remove(dwn_poster)
            return False
        return True

    def checkType(self, shortdesc, fulldesc):
        fd = shortdesc.splitlines()[0] if shortdesc else fulldesc.splitlines()[0] if fulldesc else ''
        global srch
        srch = "multi"
        return srch, fd

    def UNAC(self, string):
        string = html.unescape(string)
        string = unicodedata.normalize('NFD', string)
        string = re.sub(r"u0026", "&", string)
        string = re.sub(r"u003d", "=", string)
        string = re.sub(r'[\u0300-\u036f]', '', string)
        string = re.sub(r"[,!?\.\"]", ' ', string)
        string = re.sub(r'\s+', ' ', string)
        string = string.strip()
        return string

    def PMATCH(self, textA, textB):
        if not textB or not textA:
            return 0
        if textA == textB or textA.replace(" ", "") == textB.replace(" ", ""):
            return 100
        lId = len(textA.replace(" ", "")) if len(textA) > len(textB) else len(textB.replace(" ", ""))
        cId = sum(len(id) for id in textA.split() if id in textB)
        return 100 * cId // lId

class PosterDB(iPosterXDownloadThread):
    def __init__(self):
        iPosterXDownloadThread.__init__(self)
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
                pdb.task_done()
                continue

            if os.path.exists(dwn_poster):
                os.utime(dwn_poster, (time.time(), time.time()))

            search_methods = [
                self.search_tmdb,
                self.search_tvdb,
                self.search_fanart,
                self.search_imdb,
                self.search_programmetv_google,
                self.search_omdb
            ]

            for search_method in search_methods:
                if not os.path.exists(dwn_poster):
                    val, log = search_method(dwn_poster, self.pstcanal, canal[4], canal[3])
                    self.logDB(log)
                    if "SUCCESS" in log:
                        break

            pdb.task_done()

    def logDB(self, logmsg):
        try:
            with open("/tmp/PosterDB.log", "a") as w:
                w.write("%s\n" % logmsg)
        except Exception as e:
            print("logDB error:", str(e))
            traceback.print_exc()


def downloadPoster(eventName):
    # Clean the event name using cutName function
    cleanedName = cutName(eventName)
    # Match the cleaned name against the regex triggers
    if REGEX.search(cleanedName):
        # Proceed with downloading the poster
        # ...existing code to download the poster...
        pass
    else:
        print(f"No match found for event name: {cleanedName}")

# Example usage
eventName = "1737847882-KARAMELLA"
downloadPoster(eventName)
