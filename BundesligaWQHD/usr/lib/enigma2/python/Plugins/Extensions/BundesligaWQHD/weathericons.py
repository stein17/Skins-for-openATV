# -*- coding: utf-8 -*-
from __future__ import absolute_import

import hashlib
import json
import os
import re
import shutil
import struct
import tempfile
import zipfile
from urllib.request import Request, urlopen

from .constants import SKIN_BASE


DEFAULT_ICONSET_ID = "meteocons-2-fill"
RESOLUTION_KEY = "wqhd"
FRAME_COUNT = 24
MAX_ARCHIVE_SIZE = 25 * 1024 * 1024
MAX_UNPACKED_SIZE = 35 * 1024 * 1024
MAX_ARCHIVE_FILES = 1200
DOWNLOAD_CHUNK_SIZE = 128 * 1024
RELEASE_BASE_URL = (
    "https://github.com/stein17/Skins-for-openATV/releases/download/"
    "animated-weather-icons-v1.0.0/"
)
DEFAULT_PATH = os.path.join(SKIN_BASE, "weather", "Meteocons_Animated")
OPTIONAL_BASE = os.path.join(SKIN_BASE, "weather", "AnimatedWeatherSets")


ICONSETS = (
    {
        "id": DEFAULT_ICONSET_ID,
        "title": "Meteocons 2 Fill (Standard)",
        "bundled_default": True,
        "license": "MIT",
        "packages": {
            "fhd": {
                "file": "meteocons-2-fill-fhd-144.zip",
                "bytes": 1376503,
                "sha256": "3da6938875ac2640ba225399166714e90c4242ce3c3524bc713f36653195d27e",
                "archive_root": "meteocons-2-fill-fhd-144",
                "icon_size": 144,
            },
            "wqhd": {
                "file": "meteocons-2-fill-wqhd-192.zip",
                "bytes": 1211300,
                "sha256": "16febf503fb307d8335c1a0d32eaba396353d593b1d7cf29b563b14b8c938ccd",
                "archive_root": "meteocons-2-fill-wqhd-192",
                "icon_size": 192,
            },
        },
    },
    {
        "id": "stein17-animated-v1.0",
        "title": "stein17 Animated Weather v1.1",
        "bundled_default": False,
        "license": "Copyright stein17 - private Nutzung",
        "packages": {
            "fhd": {
                "file": "stein17-animated-v1.1-universal-180.zip",
                "bytes": 17897047,
                "sha256": "2888b41da28e38d1ad6478793c4de48d5f718a1968379bcc9389e473c9d1131f",
                "archive_root": "stein17-animated-v1.0",
                "icon_size": 180,
            },
            "wqhd": {
                "file": "stein17-animated-v1.1-universal-180.zip",
                "bytes": 17897047,
                "sha256": "2888b41da28e38d1ad6478793c4de48d5f718a1968379bcc9389e473c9d1131f",
                "archive_root": "stein17-animated-v1.0",
                "icon_size": 180,
            },
        },
    },
    {
        "id": "amcharts-1.0.0",
        "title": "amCharts 1.0.0",
        "bundled_default": False,
        "license": "CC BY 4.0",
        "packages": {
            "fhd": {
                "file": "amcharts-1.0.0-fhd-144.zip",
                "bytes": 990659,
                "sha256": "3dd443915e86cc97ce45d3812b6d0ff3c79fb5ac6b7c2082c70d159f5515da5a",
                "archive_root": "amcharts-1.0.0-fhd-144",
                "icon_size": 144,
            },
            "wqhd": {
                "file": "amcharts-1.0.0-wqhd-192.zip",
                "bytes": 952272,
                "sha256": "751cc1f00fe763f641e4211b930c925937cb3edcc41f36e3173c4c53601dcc72",
                "archive_root": "amcharts-1.0.0-wqhd-192",
                "icon_size": 192,
            },
        },
    },
    {
        "id": "meteocons-3-flat",
        "title": "Meteocons 3 Flat",
        "bundled_default": False,
        "license": "MIT",
        "packages": {
            "fhd": {
                "file": "meteocons-3-flat-fhd-144.zip",
                "bytes": 1186274,
                "sha256": "150c34cc1b0223c0469a5204b42dd5e805297bf7d4522988f72f87dd8e66ead7",
                "archive_root": "meteocons-3-flat-fhd-144",
                "icon_size": 144,
            },
            "wqhd": {
                "file": "meteocons-3-flat-wqhd-192.zip",
                "bytes": 898861,
                "sha256": "c0fd2076917189479d81093e60e771adde8782ad6a76c7c0d7252383ed9a02aa",
                "archive_root": "meteocons-3-flat-wqhd-192",
                "icon_size": 192,
            },
        },
    },
    {
        "id": "meteocons-3-line",
        "title": "Meteocons 3 Line",
        "bundled_default": False,
        "license": "MIT",
        "packages": {
            "fhd": {
                "file": "meteocons-3-line-fhd-144.zip",
                "bytes": 1445670,
                "sha256": "826aa39cedde036db62b690c7a75262dc02f56e95fb8303d12b9745ea0cf5a2d",
                "archive_root": "meteocons-3-line-fhd-144",
                "icon_size": 144,
            },
            "wqhd": {
                "file": "meteocons-3-line-wqhd-192.zip",
                "bytes": 1084915,
                "sha256": "e3c6b016b4c105f3496b7d913dba8fe0bf3ddf539a795af6d66cac5110123338",
                "archive_root": "meteocons-3-line-wqhd-192",
                "icon_size": 192,
            },
        },
    },
    {
        "id": "meteocons-3-monochrome-white",
        "title": "Meteocons 3 Monochrome Weiß",
        "bundled_default": False,
        "license": "MIT",
        "packages": {
            "fhd": {
                "file": "meteocons-3-monochrome-white-fhd-144.zip",
                "bytes": 908779,
                "sha256": "8d6a9a59a76cf7ad3dff9c1202004b77211f89c577136c0ac39ab59df2b1510a",
                "archive_root": "meteocons-3-monochrome-white-fhd-144",
                "icon_size": 144,
            },
            "wqhd": {
                "file": "meteocons-3-monochrome-white-wqhd-192.zip",
                "bytes": 820161,
                "sha256": "8c06821ad87280d0dfbbb712191d2c99d10ce89aef244c646de61badb97ed974",
                "archive_root": "meteocons-3-monochrome-white-wqhd-192",
                "icon_size": 192,
            },
        },
    },
)


class WeatherIconsetError(Exception):
    pass


def iconset_choices():
    return [(entry["id"], entry["title"]) for entry in ICONSETS]


def iconset_entry(iconset_id):
    for entry in ICONSETS:
        if entry["id"] == iconset_id:
            return entry
    return None


def iconset_path(iconset_id):
    if iconset_id == DEFAULT_ICONSET_ID:
        return DEFAULT_PATH
    if not re.match(r"^[a-z0-9][a-z0-9.-]+$", iconset_id or ""):
        return DEFAULT_PATH
    return os.path.join(OPTIONAL_BASE, iconset_id)


def resolved_iconset_path(iconset_id):
    selected = iconset_path(iconset_id)
    if os.path.isfile(os.path.join(selected, "mapping.json")):
        return selected
    return DEFAULT_PATH


def _format_bytes(value):
    value = int(value or 0)
    if value >= 1024 * 1024:
        return "%.1f MiB" % (float(value) / (1024 * 1024))
    if value >= 1024:
        return "%.0f KiB" % (float(value) / 1024)
    return "%d B" % value


class WeatherIconsetManager(object):
    def __init__(self):
        self.resolution = RESOLUTION_KEY

    def entry(self, iconset_id):
        return iconset_entry(iconset_id)

    def package(self, entry):
        return (entry or {}).get("packages", {}).get(self.resolution, {})

    def package_size_text(self, entry):
        return _format_bytes(self.package(entry).get("bytes", 0))

    def is_installed(self, iconset_id):
        return self._validate_installation(iconset_path(iconset_id), quiet=True)

    def _download(self, url, destination, expected_size):
        if not url.startswith(RELEASE_BASE_URL):
            raise WeatherIconsetError("Unsichere Downloadadresse im Wetterkatalog.")
        request = Request(url, headers={"User-Agent": "BundesligaWQHD-WeatherIconsets/1.0"})
        total = 0
        try:
            response = urlopen(request, timeout=35)
            try:
                length = response.headers.get("Content-Length")
                if length and int(length) > MAX_ARCHIVE_SIZE:
                    raise WeatherIconsetError("Das Wetterpaket ist unerwartet groß.")
                with open(destination, "wb") as output:
                    while True:
                        chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_ARCHIVE_SIZE:
                            raise WeatherIconsetError("Das Wetterpaket überschreitet die Größenbegrenzung.")
                        output.write(chunk)
            finally:
                response.close()
        except WeatherIconsetError:
            raise
        except Exception as error:
            raise WeatherIconsetError("Download fehlgeschlagen: %s" % error)
        if total <= 0:
            raise WeatherIconsetError("GitHub lieferte eine leere Datei.")
        if expected_size and total != int(expected_size):
            raise WeatherIconsetError("Die Dateigröße stimmt nicht mit dem Katalog überein.")

    def _verify_sha256(self, filename, expected):
        digest = hashlib.sha256()
        with open(filename, "rb") as source:
            while True:
                chunk = source.read(DOWNLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                digest.update(chunk)
        if digest.hexdigest().lower() != (expected or "").lower():
            raise WeatherIconsetError("SHA-256-Prüfung des Wetterpakets fehlgeschlagen.")

    def _safe_members(self, archive, archive_root):
        members = archive.infolist()
        if not members or len(members) > MAX_ARCHIVE_FILES:
            raise WeatherIconsetError("Ungültige Anzahl Dateien im Wetterpaket.")
        root_prefix = archive_root.rstrip("/") + "/"
        total = 0
        for member in members:
            name = member.filename.replace("\\", "/")
            normalized = os.path.normpath(name).replace("\\", "/")
            if normalized.startswith("../") or normalized.startswith("/"):
                raise WeatherIconsetError("Unsicherer Dateipfad im Wetterpaket.")
            if normalized != archive_root and not normalized.startswith(root_prefix):
                raise WeatherIconsetError("Unerwarteter Hauptordner im Wetterpaket.")
            mode = (member.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise WeatherIconsetError("Verknüpfungen sind im Wetterpaket nicht erlaubt.")
            total += int(member.file_size or 0)
            if total > MAX_UNPACKED_SIZE:
                raise WeatherIconsetError("Das entpackte Wetterpaket ist unerwartet groß.")
        return members

    def _extract(self, archive_filename, destination, archive_root):
        try:
            with zipfile.ZipFile(archive_filename, "r") as archive:
                members = self._safe_members(archive, archive_root)
                for member in members:
                    archive.extract(member, destination)
        except WeatherIconsetError:
            raise
        except Exception as error:
            raise WeatherIconsetError("Wetterpaket konnte nicht entpackt werden: %s" % error)
        return os.path.join(destination, archive_root)

    def _png_dimensions(self, filename):
        with open(filename, "rb") as source:
            header = source.read(24)
        if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            raise WeatherIconsetError("Ungültige PNG-Datei im Wetterpaket.")
        return struct.unpack(">II", header[16:24])

    def _validate_installation(self, directory, quiet=False):
        try:
            mapping_path = os.path.join(directory, "mapping.json")
            with open(mapping_path, "r", encoding="utf-8") as source:
                mapping = json.load(source)
            expected_codes = set([str(value) for value in range(48)] + ["NA"])
            if set(mapping.keys()) != expected_codes:
                raise WeatherIconsetError("Das Wetter-Mapping ist unvollständig.")
            expected_size = int(self.package(self.entry_from_directory(directory)).get("icon_size", 0) or 0)
            if not expected_size:
                expected_size = 144 if self.resolution == "fhd" else 192
            checked = set()
            for code in expected_codes:
                value = mapping.get(code, {})
                folder = value.get("icon", "") if isinstance(value, dict) else str(value)
                if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*$", folder):
                    raise WeatherIconsetError("Ungültiger Motivordner im Wetter-Mapping.")
                if folder in checked:
                    continue
                checked.add(folder)
                icon_directory = os.path.join(directory, folder)
                if not os.path.isdir(icon_directory) or os.path.islink(icon_directory):
                    raise WeatherIconsetError("Motivordner fehlt: %s" % folder)
                for index in range(FRAME_COUNT):
                    filename = os.path.join(icon_directory, "a%d.png" % index)
                    if not os.path.isfile(filename) or os.path.getsize(filename) <= 0:
                        raise WeatherIconsetError("Animationsframe fehlt: %s/a%d.png" % (folder, index))
                    if self._png_dimensions(filename) != (expected_size, expected_size):
                        raise WeatherIconsetError("Falsche Bildgröße in %s/a%d.png" % (folder, index))
            return True
        except Exception:
            if quiet:
                return False
            raise

    def entry_from_directory(self, directory):
        base = os.path.basename(os.path.normpath(directory))
        if os.path.normpath(directory) == os.path.normpath(DEFAULT_PATH):
            return self.entry(DEFAULT_ICONSET_ID)
        return self.entry(base)

    def _remove_other_optional_sets(self, keep_id):
        if not os.path.isdir(OPTIONAL_BASE):
            return
        for name in os.listdir(OPTIONAL_BASE):
            path = os.path.join(OPTIONAL_BASE, name)
            if name != keep_id and iconset_entry(name) and os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)

    def install(self, iconset_id, progress=None):
        progress = progress or (lambda _text: None)
        entry = self.entry(iconset_id)
        if not entry:
            raise WeatherIconsetError("Unbekanntes Wetter-Iconset.")
        if entry.get("bundled_default"):
            if self.is_installed(iconset_id):
                return
            raise WeatherIconsetError("Das enthaltene Standardset ist nicht vollständig installiert.")
        package = self.package(entry)
        if not package:
            raise WeatherIconsetError("Für diese Skin-Auflösung fehlt das Downloadpaket.")
        if not os.path.isdir(OPTIONAL_BASE):
            os.makedirs(OPTIONAL_BASE)
        work = tempfile.mkdtemp(prefix=".weather-install-", dir=OPTIONAL_BASE)
        archive_filename = os.path.join(work, package["file"])
        target = iconset_path(iconset_id)
        backup = ""
        try:
            progress("Wetterpaket wird von GitHub geladen …")
            self._download(RELEASE_BASE_URL + package["file"], archive_filename, package.get("bytes"))
            progress("SHA-256-Prüfsumme wird kontrolliert …")
            self._verify_sha256(archive_filename, package.get("sha256"))
            unpack_directory = os.path.join(work, "unpacked")
            os.makedirs(unpack_directory)
            progress("Wetterpaket wird sicher entpackt …")
            extracted = self._extract(archive_filename, unpack_directory, package["archive_root"])
            progress("24 Frames je Wetterzustand werden geprüft …")
            self._validate_installation(extracted)
            if os.path.lexists(target):
                if os.path.islink(target) or not os.path.isdir(target):
                    raise WeatherIconsetError("Der vorhandene Iconset-Pfad ist unsicher.")
                backup = target + ".old-%d" % os.getpid()
                if os.path.lexists(backup):
                    raise WeatherIconsetError("Temporärer Sicherungsordner ist bereits vorhanden.")
                os.rename(target, backup)
            os.rename(extracted, target)
            if backup:
                shutil.rmtree(backup)
                backup = ""
            self._remove_other_optional_sets(iconset_id)
        except Exception:
            if backup and os.path.isdir(backup) and not os.path.lexists(target):
                os.rename(backup, target)
                backup = ""
            raise
        finally:
            if os.path.isdir(work):
                shutil.rmtree(work)
            if backup and os.path.isdir(backup) and not os.path.islink(backup):
                try:
                    shutil.rmtree(backup)
                except OSError:
                    pass
