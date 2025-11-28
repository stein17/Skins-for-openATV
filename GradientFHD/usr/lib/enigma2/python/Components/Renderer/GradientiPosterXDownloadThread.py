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
import time
from random import choice
from requests import get, exceptions
from twisted.internet.reactor import callInThread
from .GradientConverlibr import quoteEventName, cutName, REGEX, convtext

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
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20120101 Firefox/33.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:35.0) Gecko/20120101 Firefox/35.0',
        'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:28.0) Gecko/20100101 Firefox/28.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
        'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; de) Presto/2.9.168 Version/11.52',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
    ]
    return random.choice(useragents)


# Quiet mode by default — set to True for debugging
DEBUG_POSTER = False

tmdb_api = "3c3efcf47c3577558812bb9d64019d65"
omdb_api = "6a4c9432"
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
    if DEBUG_POSTER:
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
    try:
        os.makedirs(path_folder, exist_ok=True)
    except Exception:
        pass


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


class GradientiPosterXDownloadThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.adsl = intCheck()
        if not self.adsl:
            if DEBUG_POSTER:
                print("Connessione assente, modalità offline.")
            return
        else:
            if DEBUG_POSTER:
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
            # Shorter timeouts to avoid long SSL handshakes blocking threads
            try:
                response = requests.get(url, headers=headers, timeout=(3, 6), verify=False)
                response.raise_for_status()
            except requests.exceptions.SSLError as e:
                if DEBUG_POSTER:
                    print("TMDb SSL error:", e)
                return False, "[ERROR : tmdb ssl]"
            except requests.exceptions.ConnectTimeout:
                if DEBUG_POSTER:
                    print("TMDb connect timeout")
                return False, "[ERROR : tmdb connect timeout]"
            except requests.exceptions.ReadTimeout:
                if DEBUG_POSTER:
                    print("TMDb read timeout")
                return False, "[ERROR : tmdb read timeout]"
            except requests.exceptions.RequestException as e:
                if DEBUG_POSTER:
                    print("TMDb request error:", e)
                return False, "[ERROR : tmdb request]"

            if response.status_code == requests.codes.ok:
                data = response.json()
                return self.downloadData2(data)
            else:
                return False, f"Error when searching on TMDb: {response.status_code}"
        except Exception as e:
            if DEBUG_POSTER:
                print('TMDb search error:', e)
            return False, "Error when searching on TMDb"

    def downloadData2(self, data):
        """
        Handle TMDb results. Returns tuple (bool, logstr).
        Only try to download when poster_path exists.
        """
        try:
            data_json = data if isinstance(data, dict) else json.loads(data)
        except Exception as e:
            if DEBUG_POSTER:
                print("downloadData2: invalid JSON:", e)
            return False, "[ERROR : tmdb] invalid JSON"

        if 'results' in data_json:
            try:
                self.sizeb = False
                for each in data_json['results']:
                    media_type = str(each.get('media_type') or '')
                    if media_type == "tv":
                        media_type = "serie"
                    if media_type not in ['serie', 'movie']:
                        continue

                    # determine title/year
                    year = ""
                    if media_type == "movie" and each.get('release_date'):
                        year = each.get('release_date').split("-")[0]
                    elif media_type == "serie" and each.get('first_air_date'):
                        year = each.get('first_air_date').split("-")[0]
                    title = each.get('name') or each.get('title') or ''
                    poster_path = each.get('poster_path') or ''
                    if not poster_path:
                        # no poster path — skip this result
                        if DEBUG_POSTER:
                            print("TMDb result has no poster_path; skipping:", title)
                        continue

                    # Build poster URL (use https)
                    poster = "https://image.tmdb.org/t/p/w500" + poster_path

                    rating = str(each.get('vote_average', 0))
                    show_title = title
                    if year:
                        show_title = "{} ({})".format(title, year)

                    # prepare download filename
                    try:
                        dwn_target = self.dwn_poster
                    except Exception:
                        safe_name = re.sub(r'[\\/:*?"<>|]', '_', title).strip()
                        dwn_target = os.path.join(path_folder, safe_name + ".jpg")

                    # Call savePoster in thread
                    callInThread(self.savePoster, poster, dwn_target)
                    if DEBUG_POSTER:
                        print('callInThread=Poster for', dwn_target)

                    # Non-blocking: if file exists and valid, return success; otherwise indicate started
                    if os.path.exists(dwn_target):
                        if self.verifyPoster(dwn_target):
                            try:
                                self.resizePoster(dwn_target)
                            except Exception:
                                pass
                            return True, "[SUCCESS poster: tmdb] title {} => {}".format(show_title, poster)
                        else:
                            continue
                    else:
                        return True, "[STARTED poster: tmdb] title {} => {}".format(show_title, poster)
                return False, "[SKIP : tmdb] Not found"
            except Exception as e:
                if DEBUG_POSTER:
                    print('downloadData2 error=', e)
                try:
                    if hasattr(self, 'dwn_poster') and os.path.exists(self.dwn_poster):
                        os.remove(self.dwn_poster)
                except Exception:
                    pass
                return False, "[ERROR : tmdb]"
        return False, "[SKIP : tmdb] Not found"

    def search_tvdb(self, dwn_poster, title, shortdesc, fulldesc, channel=None):
        """
        Scraping fallback for TheTVDB: best-effort.
        Tries to find og:image or first poster-like <img> on the search/result page.
        """
        try:
            title_safe = title.replace('+', ' ')
            q = requests.utils.quote(title_safe)
            search_url = f"https://thetvdb.com/search?query={q}"
            headers = {'User-Agent': getRandomUserAgent()}
            r = requests.get(search_url, headers=headers, timeout=(6, 12))
            r.raise_for_status()
            html_text = r.text
            # Try og:image
            m = re.search(r'<meta property="og:image" content="([^"]+)"', html_text, flags=re.I)
            if m:
                img = m.group(1)
                if img:
                    callInThread(self.savePoster, img, dwn_poster)
                    return True, "[SUCCESS : tvdb scrape og:image]"
            m2 = re.search(r"<img[^>]+src=['\"]([^'\"]+(?:banners|posters|thetvdb)[^'\"]+)['\"]", html_text, flags=re.I)
            if m2:
                img = m2.group(1)
                if img and not img.startswith('http'):
                    img = 'https://thetvdb.com' + img
                callInThread(self.savePoster, img, dwn_poster)
                return True, "[SUCCESS : tvdb scrape img]"
            return False, "[SKIP : tvdb no results]"
        except Exception as e:
            if DEBUG_POSTER:
                print('tvdb scrape error:', e)
            return False, "[ERROR : tvdb]"

    def search_omdb(self, dwn_poster, title, shortdesc, fulldesc, channel=None):
        try:
            self.dwn_poster = dwn_poster
            title_safe = title.replace('+', ' ')
            if not omdb_api:
                return False, "[SKIP : omdb missing key]"
            url = f"http://www.omdbapi.com/?apikey={omdb_api}&t={title_safe}"
            headers = {'User-Agent': getRandomUserAgent()}
            response = requests.get(url, headers=headers, timeout=(10, 20))
            response.raise_for_status()
            if response.status_code == requests.codes.ok:
                data = response.json()
                if 'Poster' in data and data['Poster'] != 'N/A':
                    poster_url = data['Poster']
                    callInThread(self.savePoster, poster_url, self.dwn_poster)
                    if DEBUG_POSTER:
                        print("OMDb poster queued:", poster_url)
                    return True, f"[SUCCESS poster: omdb] title {title_safe} => {poster_url}"
                else:
                    return False, f"[SKIP : omdb] {title_safe} => Poster not found"
            else:
                return False, f"Errore durante la ricerca su OMDB: {response.status_code}"
        except Exception as e:
            if DEBUG_POSTER:
                print('Errore nella ricerca OMDB:', e)
            return False, "Errore durante la ricerca su OMDB"

    def savePoster(self, url, callback):
        """
        Download poster (called in thread). Ensures parent dir exists
        and guards against invalid base URLs. Uses stricter timeouts.
        """
        headers = {"User-Agent": getRandomUserAgent()}
        try:
            if not url:
                if DEBUG_POSTER:
                    print("savePoster: empty url, skip")
                return callback
            # Guard: do not attempt if url ends with TMDb base path without poster path
            if url.rstrip().endswith("/t/p/w500") or url.rstrip().endswith("/t/p/w1280") or url.strip().endswith("image.tmdb.org/t/p/w500"):
                if DEBUG_POSTER:
                    print("savePoster: url appears to be TMDb base url without poster path:", url)
                return callback

            # Ensure parent dir exists
            try:
                parent = os.path.dirname(callback)
                if parent and not os.path.exists(parent):
                    os.makedirs(parent, exist_ok=True)
            except Exception:
                pass

            # perform request with short timeouts to avoid long blocking
            try:
                response = get(url if isinstance(url, str) else url.encode(), headers=headers, timeout=(3, 8))
                response.raise_for_status()
                with open(callback, "wb") as local_file:
                    local_file.write(response.content)
                if DEBUG_POSTER:
                    print("savePoster: saved to", callback)
            except exceptions.RequestException as error:
                if DEBUG_POSTER:
                    print("savePoster request error:", error)
                return callback
        except Exception as e:
            if DEBUG_POSTER:
                print('savePoster error:', e)
        return callback

    def resizePoster(self, dwn_poster):
        try:
            img = Image.open(dwn_poster)
            width, height = img.size
            # avoid integer division issues
            ratio = float(width) / float(height) if height else 1.0
            new_height = int(isz.split(",")[1])
            new_width = int(ratio * new_height)
            rimg = img.resize((new_width, new_height), Image.LANCZOS)
            img.close()
            rimg.save(dwn_poster)
            rimg.close()
        except Exception as e:
            if DEBUG_POSTER:
                print("ERROR resizePoster:{}".format(e))

    def verifyPoster(self, dwn_poster):
        # verify image exists and is valid; avoid removing non-existent files
        try:
            if not os.path.exists(dwn_poster):
                if DEBUG_POSTER:
                    print("verifyPoster: file does not exist:", dwn_poster)
                return False
            img = Image.open(dwn_poster)
            img.verify()
            fmt = getattr(img, "format", None)
            img.close()
            if fmt and fmt.upper() == "JPEG":
                return True
            else:
                try:
                    if os.path.exists(dwn_poster):
                        os.remove(dwn_poster)
                except Exception:
                    pass
                return False
        except Exception as e:
            if DEBUG_POSTER:
                print("verifyPoster error:", e)
            try:
                if os.path.exists(dwn_poster):
                    os.remove(dwn_poster)
            except Exception:
                pass
            return False

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
                if DEBUG_POSTER:
                    print("None type detected - poster not found")
                pdb.task_done()
                continue

            if os.path.exists(dwn_poster):
                try:
                    os.utime(dwn_poster, (time.time(), time.time()))
                except Exception:
                    pass

            # Search order: tmdb -> tvdb -> fanart -> imdb -> programmetv_google -> omdb
            search_methods = [
                self.search_tmdb,
                getattr(self, "search_tvdb", lambda *a, **k: (False, "[SKIP : tvdb not implemented]")),
                getattr(self, "search_fanart", lambda *a, **k: (False, "[SKIP : fanart not implemented]")),
                getattr(self, "search_imdb", lambda *a, **k: (False, "[SKIP : imdb not implemented]")),
                getattr(self, "search_programmetv_google", lambda *a, **k: (False, "[SKIP : google not implemented]")),
                getattr(self, "search_omdb", lambda *a, **k: (False, "[SKIP : omdb not implemented]"))
            ]

            for search_method in search_methods:
                if not os.path.exists(dwn_poster):
                    try:
                        val, log = search_method(dwn_poster, self.pstcanal, canal[4], canal[3], canal[0] if len(canal)>0 else None)
                    except TypeError:
                        val, log = search_method(dwn_poster, self.pstcanal, canal[4], canal[3])
                    self.logDB(log)
                    if "SUCCESS" in log or "STARTED" in log:
                        break

            pdb.task_done()

    def logDB(self, logmsg):
        try:
            with open("/tmp/PosterDB.log", "a") as w:
                w.write("%s\n" % logmsg)
        except Exception as e:
            if DEBUG_POSTER:
                print("logDB error:", str(e))

# downloadPoster / helper functions (kept minimal)
def downloadPoster(eventName):
    # Clean the event name using cutName function
    cleanedName = cutName(eventName)
    # Match the cleaned name against the regex triggers
    if REGEX.search(cleanedName):
        # Proceed with downloading the poster (handled by PosterDB)
        return True
    else:
        if DEBUG_POSTER:
            print("No match for eventName:", cleanedName)
        return False


# end of file
