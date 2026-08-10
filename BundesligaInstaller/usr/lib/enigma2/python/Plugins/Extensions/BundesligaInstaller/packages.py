# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json
import os
import re


PLUGIN_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/BundesligaInstaller"
CATALOG_PATH = os.path.join(PLUGIN_PATH, "packages.json")


class PackageError(Exception):
    pass


class PackageCatalog(object):
    """Stable OpenATV feed package names for the two skin variants."""

    def __init__(self, path=CATALOG_PATH):
        self.path = path
        self.data = self._load()
        self.packages = self.data["packages"]
        self.by_id = dict((item["id"], item) for item in self.packages)

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (IOError, OSError, ValueError) as error:
            raise PackageError("Installationskatalog konnte nicht gelesen werden: %s" % error)
        if data.get("schema") != 2 or not isinstance(data.get("packages"), list):
            raise PackageError("Installationskatalog hat ein unbekanntes Format.")
        seen = set()
        for item in data["packages"]:
            required = ("id", "title", "resolution", "package_name", "skin_xml", "install_path")
            if any(not item.get(key) for key in required):
                raise PackageError("Installationskatalog enthält einen unvollständigen Eintrag.")
            if item["id"] in seen or not re.match(r"^[a-z0-9_-]+$", item["id"]):
                raise PackageError("Installationskatalog enthält eine ungültige Kennung.")
            if not re.match(r"^[a-z0-9+._-]+$", item["package_name"]):
                raise PackageError("Installationskatalog enthält einen ungültigen Paketnamen.")
            seen.add(item["id"])
        if seen != set(("fhd", "wqhd")):
            raise PackageError("Installationskatalog muss FHD und WQHD enthalten.")
        return data

    def get(self, variant):
        return self.by_id.get(variant)

    @staticmethod
    def installed(entry):
        return bool(entry and os.path.isdir(entry["install_path"]))

    def current_variant(self, primary_skin=""):
        primary = (primary_skin or "").lower()
        for entry in self.packages:
            if entry["skin_xml"].lower() == primary and self.installed(entry):
                return entry["id"]
        installed = [entry for entry in self.packages if self.installed(entry)]
        return installed[0]["id"] if len(installed) == 1 else ""
