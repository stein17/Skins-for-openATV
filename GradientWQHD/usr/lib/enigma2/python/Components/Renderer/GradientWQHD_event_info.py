#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# GradientWQHD_event_info.py
# Klasse GradientWQHD_event_info: TMDb lookup + JSON Info speichern (merge, atomic)
# 02.26 @stein17, Many new features and improvements
#<!-- Titel -->
#<widget name="title" source="session.CurrentService" render="Label" position="20,20" size="600,40">
#  <convert type="GradientWQHD_event_info">title</convert>
#</widget>

#<!-- Jahr -->
#<widget name="year" source="session.CurrentService" render="Label" position="640,20" size="80,40">
#  <convert type="GradientWQHD_event_info">year</convert>
#</widget>

#<!-- Rating -->
#<widget name="rating" source="session.CurrentService" render="Label" position="20,70" size="80,30">
#  <convert type="GradientWQHD_event_info">tmdb_vote_average</convert>
#</widget>

#<!-- Altersfreigabe (wenn vorhanden) -->
#<widget name="rated" source="session.CurrentService" render="Label" position="120,70" size="120,30">
#  <convert type="GradientWQHD_event_info">rated</convert>
#</widget>

#<!-- Plot -->
#<widget name="plot" source="session.CurrentService" render="Label" position="20,110" size="900,120" wrap="1">
#  <convert type="GradientWQHD_event_info">overview</convert>
#</widget>

#<!-- Poster (Konverter sollte poster_path in URL/Datei auflösen) -->
#<widget name="poster" source="session.CurrentService" render="Pixmap" position="950,20" size="300,450">
#  <convert type="GradientWQHD_event_info">poster_path</convert>
#</widget>


from __future__ import print_function
import os
import json
import shutil
import requests
from urllib.parse import quote as _urlquote

class GradientWQHD_event_info(object):
    def __init__(self, info_folder=None, tmdb_api=None, lang=None):
        # Default Info folder detection (like in other Renderern)
        if info_folder:
            self.INFO_FOLDER = info_folder
        else:
            try:
                sel = getattr(config.plugins.GradientWQHD, "posterXPath", None)
                if sel is not None and getattr(sel, "value", None) and sel.value != "AUTO":
                    base = sel.value
                    if os.path.isdir(base):
                        self.INFO_FOLDER = os.path.join(base, "xtra", "Info")
                    else:
                        self.INFO_FOLDER = "/tmp/Info"
                else:
                    chosen = None
                    for base in ("/media/usb", "/media/hdd", "/media/mmc", "/media/net", "/media/autofs"):
                        if os.path.isdir(base):
                            chosen = base
                            break
                    self.INFO_FOLDER = os.path.join(chosen, "xtra", "Info") if chosen else "/tmp/Info"
            except Exception:
                self.INFO_FOLDER = "/tmp/Info"
        self._ensure_folder(self.INFO_FOLDER)
        self.tmdb_api = tmdb_api or self._find_tmdb_key()
        self.lang = lang

    def _ensure_folder(self, path):
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            pass

    def _find_tmdb_key(self):
        # 1) env var
        k = os.environ.get("TMDB_API")
        if k:
            return k
        # 2) attempt to read known renderer files (naive regex)
        candidates = [
            "/usr/lib/enigma2/python/Components/Renderer/GradientWQHDStarX.py",
            "/usr/lib/enigma2/python/Components/Renderer/GradientWQHDPosterXDownloadThread.py",
            "/usr/lib/enigma2/python/Components/Renderer/GradientWQHDBackdropXDownloadThread.py",
        ]
        for c in candidates:
            try:
                with open(c, "r", encoding="utf-8") as fh:
                    txt = fh.read(4096)
                import re
                m = re.search(r"tmdb_api\s*=\s*['\"]([0-9a-fA-F]+)['\"]", txt)
                if m:
                    return m.group(1)
            except Exception:
                continue
        return None

    # --- TMDb helpers ---
    def search_tmdb(self, title):
        if not self.tmdb_api or not title:
            return None
        q = _urlquote(title)
        url = f"https://api.themoviedb.org/3/search/multi?api_key={self.tmdb_api}&query={q}"
        if self.lang:
            url += f"&language={self.lang}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()

    def get_detail(self, media_type, tmdb_id):
        if not self.tmdb_api or not media_type or not tmdb_id:
            return None
        url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={self.tmdb_api}"
        if self.lang:
            url += f"&language={self.lang}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()

    # --- build metadata dict from detail JSON ---
    def build_metadata(self, detail, media_type="movie"):
        if not isinstance(detail, dict):
            return {}
        md = {}
        if media_type == "movie":
            md["title"] = detail.get("title") or detail.get("original_title")
            release = detail.get("release_date")
            if release:
                md["release_date"] = release
                md["year"] = release[:4]
            md["runtime"] = detail.get("runtime")
        else:  # tv
            md["title"] = detail.get("name") or detail.get("original_name")
            first = detail.get("first_air_date")
            if first:
                md["first_air_date"] = first
                md["year"] = first[:4]
            if detail.get("episode_run_time"):
                try:
                    md["runtime"] = detail.get("episode_run_time")[0]
                except Exception:
                    md["runtime"] = None
        md["overview"] = detail.get("overview")
        md["genres"] = [g.get("name") for g in detail.get("genres", [])] if detail.get("genres") else []
        md["tmdb_id"] = detail.get("id")
        md["tmdb_vote_average"] = detail.get("vote_average")
        md["tmdb_vote_count"] = detail.get("vote_count")
        md["poster_path"] = detail.get("poster_path")
        md["backdrop_path"] = detail.get("backdrop_path")
        md["original_language"] = detail.get("original_language")
        md["adult"] = detail.get("adult", False)
        return md

    # --- atomic write / merge into existing JSON ---
    def save_for_slug(self, slug, metadata):
        if not slug or not metadata:
            return False
        path = os.path.join(self.INFO_FOLDER, slug + ".json")
        data = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception:
                data = {}
        # merge (metadata overwrites)
        data.update(metadata)
        tmp = path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
            return True
        except Exception:
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, ensure_ascii=False, indent=2)
                return True
            except Exception:
                return False

    # --- convenience: search -> detail -> build -> save ---
    def fetch_and_save(self, title, slug=None):
        """
        title: event title (string)
        slug: filename slug (if None, the caller should provide; if None, returns metadata only)
        Returns: metadata dict if found, else None
        """
        if not title:
            return None
        try:
            search = self.search_tmdb(title)
            if not search or not search.get("results"):
                return None
            first = search["results"][0]
            media_type = first.get("media_type") or ("movie" if "title" in first else "tv")
            tmdb_id = first.get("id")
            detail = None
            try:
                detail = self.get_detail(media_type, tmdb_id)
            except Exception:
                detail = first  # fallback to partial info
            md = self.build_metadata(detail, media_type)
            if slug:
                self.save_for_slug(slug, md)
            return md
        except Exception:
            return None

# CLI quicktest
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: GradientWQHD_event_info.py \"Title\" [slug]")
        sys.exit(1)
    title = sys.argv[1]
    slug = sys.argv[2] if len(sys.argv) > 2 else None
    g = GradientWQHD_event_info()
    md = g.fetch_and_save(title, slug)
    if md is None:
        print("No data found for", title)
    else:
        print("Found:", md.get("title"), md.get("year"))
        if slug:
            print("Saved to:", os.path.join(g.INFO_FOLDER, slug + ".json"))
