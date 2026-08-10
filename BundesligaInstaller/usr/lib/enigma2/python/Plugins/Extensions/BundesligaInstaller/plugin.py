# -*- coding: utf-8 -*-
from __future__ import absolute_import

from importlib import import_module, invalidate_caches
from shlex import quote

from Components.config import config, configfile
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from enigma import getDesktop

from . import _
from .packages import PackageCatalog


PLUGIN_NAME = "Bundesliga Skin Installer"
PLUGIN_VERSION = "1.1"


class InstallerController(object):
    def __init__(self, session):
        self.session = session
        self.catalog = None
        self.target = None
        self.current = None
        self.transfer = None

    def open(self):
        try:
            self.catalog = PackageCatalog()
        except Exception as error:
            self.session.open(MessageBox, _("Installer konnte nicht gestartet werden:\n%s") % error, MessageBox.TYPE_ERROR)
            return
        desktop = getDesktop(0).size()
        recommended = "wqhd" if desktop.width() >= 2560 else "fhd"
        choices = []
        for variant in (recommended, "fhd" if recommended == "wqhd" else "wqhd"):
            entry = self.catalog.get(variant)
            suffix = _(" – empfohlen") if variant == recommended else ""
            installed = _(" – installiert") if self.catalog.installed(entry) else ""
            choices.append((
                "%s (%s)%s%s" % (entry["title"], entry["resolution"], suffix, installed),
                variant,
            ))
        choices.append((_("Abbrechen"), "cancel"))
        self.session.openWithCallback(
            self._choice,
            ChoiceBox,
            title=_("Welche Skin-Auflösung soll vom openATV-Feed installiert werden?\n\nAktuelle Enigma2-Oberfläche: %d × %d")
            % (desktop.width(), desktop.height()),
            list=choices
        )

    def _choice(self, answer):
        if not answer or answer[1] == "cancel":
            return
        self.target = self.catalog.get(answer[1])
        current_id = self.catalog.current_variant(config.skin.primary_skin.value)
        self.current = self.catalog.get(current_id) if current_id else None
        if self.current and self.current["id"] == self.target["id"]:
            self.session.openWithCallback(
                self._confirm_same,
                MessageBox,
                _("%s ist bereits installiert.\n\nSoll die aktuelle Version erneut vom openATV-Feed installiert werden?")
                % self.target["title"],
                MessageBox.TYPE_YESNO,
                default=False
            )
        elif self.current:
            self.session.openWithCallback(
                self._confirm_switch,
                MessageBox,
                _("%s ist installiert.\n\nSoll %s durch %s vom openATV-Feed ersetzt werden?")
                % (self.current["title"], self.current["title"], self.target["title"]),
                MessageBox.TYPE_YESNO,
                default=True
            )
        else:
            self._start_install()

    def _confirm_same(self, answer):
        if answer:
            self._start_install()

    def _confirm_switch(self, answer):
        if answer:
            self._start_install()

    def _capture_settings(self):
        if not self.current:
            return None
        try:
            prefix = "Plugins.Extensions.Bundesliga%s" % self.current["id"].upper()
            settings = import_module(prefix + ".settings")
            return {
                "team": settings.get_saved_team(),
                "skinparts": settings.get_saved_skinparts(),
                "colors": settings.get_overrides(),
            }
        except Exception as error:
            print("[BundesligaInstaller] Einstellungen konnten nicht gesichert werden: %s" % error)
            return None

    def _start_install(self):
        self.transfer = self._capture_settings()
        target_package = quote(self.target["package_name"])
        if self.current and self.current["id"] == self.target["id"]:
            command = "opkg update && opkg install --force-reinstall %s" % target_package
        elif self.current:
            current_package = quote(self.current["package_name"])
            command = "opkg update && opkg install %s && opkg remove %s" % (
                target_package,
                current_package,
            )
        else:
            command = "opkg update && opkg install %s" % target_package
        self.session.openWithCallback(
            self._console_finished,
            Console,
            title=_("%s vom openATV-Feed installieren") % self.target["title"],
            cmdlist=[command],
            closeOnSuccess=True
        )

    def _restore_settings(self):
        if self.transfer is None:
            return
        prefix = "Plugins.Extensions.Bundesliga%s" % self.target["id"].upper()
        settings = import_module(prefix + ".settings")
        constants = import_module(prefix + ".constants")
        settings.save_team(self.transfer.get("team", ""))
        settings.save_skinparts(self.transfer.get("skinparts", {}))
        colors = self.transfer.get("colors", {})
        for key, _label, xml_name in constants.COLOR_ITEMS:
            settings.color_config(key).value = colors.get(xml_name, "team")
        settings.save_colors()

    def _console_finished(self, *args):
        invalidate_caches()
        if not self.catalog.installed(self.target):
            self.session.open(
                MessageBox,
                _("Die Installation ist fehlgeschlagen. Das Paket ist möglicherweise noch nicht auf dem openATV-Feed verfügbar.\n\nBitte die Ausgabe der Installationskonsole prüfen."),
                MessageBox.TYPE_ERROR
            )
            return
        try:
            self._restore_settings()
            config.skin.primary_skin.value = self.target["skin_xml"]
            config.skin.primary_skin.save()
            configfile.save()
        except Exception as error:
            self.session.open(
                MessageBox,
                _("Der Skin wurde installiert, aber die Einstellungen konnten nicht vollständig übernommen werden:\n%s") % error,
                MessageBox.TYPE_ERROR
            )
            return
        self.session.openWithCallback(
            self._restart_answer,
            MessageBox,
            _("%s wurde vom openATV-Feed installiert und als aktiver Skin ausgewählt.\n\nGUI jetzt neu starten?")
            % self.target["title"],
            MessageBox.TYPE_YESNO,
            default=True
        )

    def _restart_answer(self, answer):
        if answer:
            self.session.open(TryQuitMainloop, 3)


def main(session, **kwargs):
    InstallerController(session).open()


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name=_(PLUGIN_NAME),
            description=_("BundesligaFHD oder BundesligaWQHD vom openATV-Feed installieren"),
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="plugin.png",
            fnc=main
        )
    ]
