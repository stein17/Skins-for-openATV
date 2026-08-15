# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
from importlib import import_module, invalidate_caches
from shlex import quote

from Components.config import config, configfile
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop

from . import _


CURRENT_TITLE = "Bundesliga FHD"
CURRENT_PACKAGE = "enigma2-plugin-skins-bundesligafhd"

TARGET_TITLE = "Bundesliga WQHD"
TARGET_RESOLUTION = "2560 × 1440"
TARGET_PACKAGE = "enigma2-plugin-skins-bundesligawqhd"
TARGET_SKIN_XML = "BundesligaWQHD/skin.xml"
TARGET_SKIN_DIR = "/usr/share/enigma2/BundesligaWQHD"
TARGET_MODULE = "Plugins.Extensions.BundesligaWQHD"
TARGET_SWITCHER = "/usr/lib/enigma2/python/Plugins/Extensions/BundesligaWQHD/resolution.py"
TARGET_IPK_PREFIX = TARGET_PACKAGE + "_"

LOCAL_IPK_DIRS = ("/tmp", "/media/hdd", "/media/usb", "/media/mmc")
OPKG_STATUS_FILES = ("/var/lib/opkg/status", "/usr/lib/opkg/status")


def package_is_installed(package_name):
    """Read OPKG's database and require an exact installed package match."""
    for status_file in OPKG_STATUS_FILES:
        try:
            with open(status_file, "r", encoding="utf-8", errors="ignore") as handle:
                content = handle.read()
        except (IOError, OSError):
            continue
        for block in content.split("\n\n"):
            fields = {}
            for line in block.splitlines():
                if ":" in line and not line[:1].isspace():
                    key, value = line.split(":", 1)
                    fields[key.strip()] = value.strip()
            if fields.get("Package") == package_name:
                return fields.get("Status") == "install ok installed"
    return False


def find_local_ipk():
    candidates = []
    for directory in LOCAL_IPK_DIRS:
        try:
            filenames = os.listdir(directory)
        except OSError:
            continue
        for filename in filenames:
            if filename.startswith(TARGET_IPK_PREFIX) and filename.endswith(".ipk"):
                path_value = os.path.join(directory, filename)
                if os.path.isfile(path_value):
                    try:
                        modified = os.path.getmtime(path_value)
                    except OSError:
                        modified = 0
                    candidates.append((modified, path_value))
    candidates.sort(reverse=True)
    return candidates[0][1] if candidates else ""


class ResolutionSwitcher(object):
    """Install the other resolution first and remove this package afterwards."""

    def __init__(self, session, transfer):
        self.session = session
        self.transfer = transfer or {}
        self.local_ipk = find_local_ipk()

    def start(self):
        if package_is_installed(TARGET_PACKAGE) and os.path.isfile(TARGET_SWITCHER):
            question = _(
                "%s ist aktiv. %s ist zusätzlich bereits als aktuelles Paket vorhanden.\n\n"
                "Soll zu %s gewechselt und %s anschließend vollständig entfernt werden?"
            ) % (CURRENT_TITLE, TARGET_TITLE, TARGET_TITLE, CURRENT_TITLE)
        else:
            source = _("dem lokalen Test-IPK") if self.local_ipk else _("dem openATV-Feed")
            question = _(
                "%s ist aktiv.\n\nSoll %s vollständig entfernt und durch %s (%s) aus %s ersetzt werden?\n\n"
                "Verein, Farben und Skinparts werden übernommen."
            ) % (CURRENT_TITLE, CURRENT_TITLE, TARGET_TITLE, TARGET_RESOLUTION, source)
        self.session.openWithCallback(
            self._confirmed,
            MessageBox,
            question,
            MessageBox.TYPE_YESNO,
            default=True
        )

    def _confirmed(self, answer):
        if not answer:
            return
        if package_is_installed(TARGET_PACKAGE) and os.path.isfile(TARGET_SWITCHER):
            self._activate_target()
            return
        if self.local_ipk:
            command = "opkg install --force-reinstall %s" % quote(self.local_ipk)
        else:
            command = "opkg update && opkg install --force-reinstall %s" % quote(TARGET_PACKAGE)
        self.session.openWithCallback(
            self._install_finished,
            Console,
            title=_("%s installieren") % TARGET_TITLE,
            cmdlist=[command],
            closeOnSuccess=True
        )

    def _install_finished(self, *args):
        invalidate_caches()
        if not (
            package_is_installed(TARGET_PACKAGE)
            and os.path.isdir(TARGET_SKIN_DIR)
            and os.path.isfile(TARGET_SWITCHER)
        ):
            self.session.open(
                MessageBox,
                _(
                    "Die Installation von %s ist fehlgeschlagen. %s bleibt unverändert aktiv.\n\n"
                    "Bitte die Ausgabe der Installationskonsole prüfen."
                ) % (TARGET_TITLE, CURRENT_TITLE),
                MessageBox.TYPE_ERROR
            )
            return
        self._activate_target()

    def _restore_target_settings(self):
        settings = import_module(TARGET_MODULE + ".settings")
        constants = import_module(TARGET_MODULE + ".constants")
        manager_module = import_module(TARGET_MODULE + ".manager")

        team = self.transfer.get("team", "")
        skinparts = self.transfer.get("skinparts", {})
        colors = self.transfer.get("colors", {})

        settings.save_team(team)
        settings.save_skinparts(skinparts)
        for key, _label, xml_name in constants.COLOR_ITEMS:
            settings.color_config(key).value = colors.get(xml_name, "team")
        settings.save_colors()

        manager = manager_module.SkinManager()
        manager.restore_from_values(team, colors, skinparts)

    def _activate_target(self):
        try:
            invalidate_caches()
            self._restore_target_settings()
            config.skin.primary_skin.value = TARGET_SKIN_XML
            config.skin.primary_skin.save()
            configfile.save()
        except Exception as error:
            self.session.open(
                MessageBox,
                _(
                    "%s wurde installiert, aber nicht aktiviert. %s bleibt erhalten.\n\nFehler: %s"
                ) % (TARGET_TITLE, CURRENT_TITLE, error),
                MessageBox.TYPE_ERROR
            )
            return

        self.session.openWithCallback(
            self._remove_finished,
            Console,
            title=_("%s vollständig entfernen") % CURRENT_TITLE,
            cmdlist=["opkg remove %s" % quote(CURRENT_PACKAGE)],
            closeOnSuccess=True
        )

    def _remove_finished(self, *args):
        if package_is_installed(CURRENT_PACKAGE):
            message = _(
                "%s wurde aktiviert, aber %s konnte nicht vollständig entfernt werden.\n\n"
                "Bitte die Ausgabe der Deinstallationskonsole prüfen. GUI trotzdem jetzt neu starten?"
            ) % (TARGET_TITLE, CURRENT_TITLE)
        else:
            message = _(
                "%s ist jetzt aktiv. %s sowie seine eigenen Converter, Renderer und das Config-Plugin wurden entfernt.\n\n"
                "GUI jetzt neu starten?"
            ) % (TARGET_TITLE, CURRENT_TITLE)
        self.session.openWithCallback(
            self._restart_answer,
            MessageBox,
            message,
            MessageBox.TYPE_YESNO,
            default=True
        )

    def _restart_answer(self, answer):
        if answer:
            self.session.open(TryQuitMainloop, 3)
