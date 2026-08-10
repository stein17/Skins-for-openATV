# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import os
import shutil
import tempfile
from urllib.parse import quote
from urllib.request import Request, urlopen

from .constants import DEFAULT_TEAM_TITLE, SKIN_BASE, TEAM_CATALOG


MARKER_FILENAME = ".bundesliga_team_asset.json"
DOWNLOAD_CHUNK_SIZE = 128 * 1024
MAX_FILE_SIZE = 12 * 1024 * 1024
MAX_TEAM_SIZE = 40 * 1024 * 1024
ALLOWED_BASE_URL = "https://raw.githubusercontent.com/stein17/Skins-for-openATV/"


class TeamAssetError(Exception):
    pass


def format_bytes(value):
    value = int(value or 0)
    if value >= 1024 * 1024:
        return "%.1f MiB" % (float(value) / (1024 * 1024))
    if value >= 1024:
        return "%.0f KiB" % (float(value) / 1024)
    return "%d B" % value


class TeamAssetManager(object):
    """Install and remove team images stored as ordinary files on GitHub.

    Only FC Bayern Munich is delivered by the OpenATV feed package. All other
    clubs are downloaded file-by-file from the python3 branch. Replacing an
    image in Git therefore needs only a normal commit and no new ZIP or IPK.
    """

    def __init__(self, skin_base=SKIN_BASE, catalog_path=TEAM_CATALOG):
        self.skin_base = skin_base
        self.verein_dir = os.path.join(skin_base, "Verein")
        self.catalog_path = catalog_path
        self.catalog = self._load_catalog()
        self.base_url = self.catalog["base_url"].rstrip("/")
        self.teams = self.catalog.get("teams", [])
        self.by_profile = dict((item["profile"], item) for item in self.teams)
        self.by_id = dict((item["id"], item) for item in self.teams)

    def _load_catalog(self):
        try:
            with open(self.catalog_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (IOError, OSError, ValueError) as error:
            raise TeamAssetError("Vereinskatalog konnte nicht gelesen werden: %s" % error)

        base_url = str(data.get("base_url") or "")
        if (
            data.get("schema") != 2
            or not isinstance(data.get("teams"), list)
            or not base_url.startswith(ALLOWED_BASE_URL)
            or "?" in base_url
            or "#" in base_url
        ):
            raise TeamAssetError("Vereinskatalog hat ein unbekanntes Format.")

        seen_ids = set()
        seen_profiles = set()
        for item in data["teams"]:
            required_keys = ("id", "title", "profile", "asset_dir", "required")
            if any(not item.get(key) for key in required_keys):
                raise TeamAssetError("Vereinskatalog enthält einen unvollständigen Eintrag.")
            if item["id"] in seen_ids or item["profile"] in seen_profiles:
                raise TeamAssetError("Vereinskatalog enthält doppelte Vereine.")
            self._safe_asset_dir(item["asset_dir"])
            if not isinstance(item["required"], list) or not item["required"]:
                raise TeamAssetError("Im Vereinskatalog fehlen Bilddateien.")
            for relative in item["required"]:
                if not self._safe_relative(relative):
                    raise TeamAssetError("Vereinskatalog enthält einen ungültigen Bildpfad.")
            seen_ids.add(item["id"])
            seen_profiles.add(item["profile"])
        return data

    @staticmethod
    def _safe_asset_dir(asset_dir):
        if (
            not asset_dir
            or asset_dir in (".", "..", "Logos")
            or asset_dir.startswith(".")
            or "/" in asset_dir
            or "\\" in asset_dir
            or "\x00" in asset_dir
        ):
            raise TeamAssetError("Ungültiger Vereinsordner im Katalog.")
        return asset_dir

    @staticmethod
    def _safe_relative(relative):
        if not relative or "\\" in relative or "\x00" in relative or relative.startswith("/"):
            return False
        parts = relative.split("/")
        return all(part not in ("", ".", "..") for part in parts)

    def team_for_profile(self, source_or_filename):
        filename = os.path.basename(source_or_filename or "")
        return self.by_profile.get(filename)

    def team_by_id(self, team_id):
        return self.by_id.get(team_id)

    @staticmethod
    def is_default(entry):
        return bool(entry and (entry.get("bundled") or entry.get("title") == DEFAULT_TEAM_TITLE))

    def team_path(self, entry):
        asset_dir = self._safe_asset_dir(entry["asset_dir"])
        target = os.path.abspath(os.path.join(self.verein_dir, asset_dir))
        root = os.path.abspath(self.verein_dir) + os.sep
        if not target.startswith(root):
            raise TeamAssetError("Ungültiger Zielordner für den Verein.")
        return target

    def is_installed(self, entry):
        if not entry:
            return False
        target = self.team_path(entry)
        if not os.path.isdir(target) or os.path.islink(target):
            return False
        for relative in entry.get("required", []):
            if not self._safe_relative(relative):
                return False
            if not os.path.isfile(os.path.join(target, *relative.split("/"))):
                return False
        return True

    def installed_teams(self):
        return [item for item in self.teams if self.is_installed(item)]

    def installed_size(self, entry):
        total = 0
        target = self.team_path(entry)
        if not os.path.isdir(target):
            return total
        for root, _dirs, files in os.walk(target):
            for filename in files:
                try:
                    total += os.path.getsize(os.path.join(root, filename))
                except OSError:
                    pass
        return total

    def _remote_url(self, entry, relative):
        path_value = "Verein/%s/%s" % (entry["asset_dir"], relative)
        return "%s/%s" % (self.base_url, quote(path_value, safe="/"))

    @staticmethod
    def _validate_image(path_value):
        try:
            with open(path_value, "rb") as handle:
                header = handle.read(16)
        except (IOError, OSError) as error:
            raise TeamAssetError("Heruntergeladenes Bild konnte nicht geprüft werden: %s" % error)
        valid = (
            header.startswith(b"\xff\xd8\xff")
            or header.startswith(b"\x89PNG\r\n\x1a\n")
            or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
        )
        if not valid:
            raise TeamAssetError("GitHub lieferte keine gültige Bilddatei.")

    def _download_file(self, entry, relative, destination):
        request = Request(
            self._remote_url(entry, relative),
            headers={"User-Agent": "BundesligaWQHD/0.4"}
        )
        total = 0
        try:
            response = urlopen(request, timeout=45)
            try:
                with open(destination, "wb") as output:
                    while True:
                        chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_FILE_SIZE:
                            raise TeamAssetError("Eine Vereinsdatei ist unerwartet groß.")
                        output.write(chunk)
            finally:
                response.close()
        except TeamAssetError:
            raise
        except Exception as error:
            raise TeamAssetError("Download fehlgeschlagen: %s" % error)
        if total <= 0:
            raise TeamAssetError("GitHub lieferte eine leere Bilddatei.")
        self._validate_image(destination)
        return total

    def _download_to_staging(self, entry, staging, progress):
        files = entry["required"]
        total = 0
        for index, relative in enumerate(files, 1):
            destination = os.path.abspath(os.path.join(staging, *relative.split("/")))
            staging_root = os.path.abspath(staging) + os.sep
            if not destination.startswith(staging_root):
                raise TeamAssetError("Unsicherer Zielpfad beim Herunterladen.")
            parent = os.path.dirname(destination)
            if not os.path.isdir(parent):
                os.makedirs(parent)
            progress("Bild %d von %d wird von GitHub geladen …" % (index, len(files)))
            total += self._download_file(entry, relative, destination)
            if total > MAX_TEAM_SIZE:
                raise TeamAssetError("Die Vereinsbilder sind unerwartet groß.")

    def install(self, entry, progress=None):
        if not entry:
            raise TeamAssetError("Verein wurde im Katalog nicht gefunden.")
        if self.is_default(entry):
            if self.is_installed(entry):
                return
            raise TeamAssetError("Das geschützte Standardpaket ist nicht vollständig installiert.")

        progress = progress or (lambda _text: None)
        if not os.path.isdir(self.verein_dir):
            os.makedirs(self.verein_dir)
        staging = tempfile.mkdtemp(prefix=".team-install-", dir=self.verein_dir)
        backup = ""
        target = self.team_path(entry)
        try:
            self._download_to_staging(entry, staging, progress)
            marker = {
                "id": entry["id"],
                "title": entry["title"],
                "profile": entry["profile"],
                "source": "github-python3",
                "files": list(entry["required"]),
            }
            with open(os.path.join(staging, MARKER_FILENAME), "w", encoding="utf-8") as handle:
                json.dump(marker, handle, ensure_ascii=False, sort_keys=True)
                handle.write("\n")

            progress("Vereinsbilder werden sicher installiert …")
            if os.path.lexists(target):
                if os.path.islink(target) or not os.path.isdir(target):
                    raise TeamAssetError("Der vorhandene Vereinsordner ist kein sicheres Verzeichnis.")
                backup = target + ".old-%d" % os.getpid()
                if os.path.lexists(backup):
                    raise TeamAssetError("Temporärer Sicherungsordner ist bereits vorhanden.")
                os.rename(target, backup)
            os.rename(staging, target)
            staging = ""
            if backup:
                shutil.rmtree(backup)
                backup = ""
        except Exception:
            if backup and os.path.isdir(backup) and not os.path.lexists(target):
                os.rename(backup, target)
                backup = ""
            raise
        finally:
            if staging and os.path.isdir(staging):
                shutil.rmtree(staging)
            if backup and os.path.isdir(backup) and not os.path.islink(backup):
                try:
                    shutil.rmtree(backup)
                except OSError:
                    pass

    def remove(self, entry, active_profile=""):
        if not entry:
            raise TeamAssetError("Verein wurde im Katalog nicht gefunden.")
        if self.is_default(entry):
            raise TeamAssetError("FC Bayern München ist das geschützte Standardpaket.")
        if os.path.basename(active_profile or "") == entry["profile"]:
            raise TeamAssetError("Der aktive Verein kann nicht gelöscht werden.")
        target = self.team_path(entry)
        if not os.path.isdir(target) or os.path.islink(target):
            raise TeamAssetError("Der Vereinsordner ist nicht installiert oder ungültig.")
        shutil.rmtree(target)
