# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

from Components.config import config
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from enigma import eTimer

from . import _
from .constants import PLUGIN_NAME, SKIN_XML
from .manager import SkinManager
from .settings import (
    get_overrides,
    get_saved_skinparts,
    get_saved_team,
    save_skinparts,
    save_team,
)


def restore_runtime_state():
    """Synchronize the backed-up state with the installed skin files."""
    try:
        manager = SkinManager()

        team_filename = get_saved_team()
        if not team_filename:
            team_filename = manager.current_team_filename()
            if not team_filename:
                default_team = manager.default_team()
                team_filename = os.path.basename(default_team) if default_team else ""
            if team_filename:
                save_team(team_filename)

        skinparts = get_saved_skinparts()
        if not skinparts:
            skinparts = manager.active_categories()
            if skinparts:
                save_skinparts(skinparts)

        return manager.restore_from_values(team_filename, get_overrides(), skinparts)
    except Exception as error:
        print("[BundesligaWQHDConfig] Startup restore failed: %s" % error)
    return None


def autostart(reason, **kwargs):
    if reason == 0:
        restore_runtime_state()


_restore_helper = None


class _RestoreTeamHelper(object):
    def __init__(self, session, entry):
        self.session = session
        self.entry = entry
        self.manager = SkinManager()
        self.timer = eTimer()
        self._timer_connection = None
        if hasattr(self.timer, "callback"):
            self.timer.callback.append(self._show_question)
        else:
            self._timer_connection = self.timer.timeout.connect(self._show_question)
        self.timer.start(3000, True)

    def _show_question(self):
        self.session.openWithCallback(
            self._answer,
            MessageBox,
            _("Nach der Wiederherstellung fehlt das Bildpaket für den gespeicherten Verein %s.\n\nJetzt von GitHub herunterladen und wieder installieren?")
            % self.entry["title"],
            MessageBox.TYPE_YESNO,
            default=True
        )

    def _answer(self, answer):
        global _restore_helper
        if not answer:
            _restore_helper = None
            return
        from .screens import BundesligaWQHDTeamDownload
        self.session.openWithCallback(
            self._download_finished,
            BundesligaWQHDTeamDownload,
            self.manager.assets,
            self.entry
        )

    def _download_finished(self, result):
        global _restore_helper
        if not result or not result.get("ok"):
            error = result.get("error") if result else _("Unbekannter Fehler")
            self.session.open(
                MessageBox,
                _("Der gespeicherte Verein konnte nicht wiederhergestellt werden. Das Default-Design bleibt vorläufig aktiv.\n\n%s")
                % error,
                MessageBox.TYPE_ERROR
            )
            _restore_helper = None
            return
        try:
            missing = self.manager.restore_from_values(
                get_saved_team(),
                get_overrides(),
                get_saved_skinparts()
            )
            if missing:
                raise IOError(_("Das installierte Vereinspaket wurde nicht erkannt."))
        except Exception as error:
            self.session.open(
                MessageBox,
                _("Vereinspaket wurde installiert, konnte aber nicht aktiviert werden:\n%s") % error,
                MessageBox.TYPE_ERROR
            )
            _restore_helper = None
            return
        self.session.openWithCallback(
            self._restart_answer,
            MessageBox,
            _("%s wurde wieder installiert und aktiviert.\n\nGUI jetzt neu starten?") % self.entry["title"],
            MessageBox.TYPE_YESNO,
            default=True
        )

    def _restart_answer(self, answer):
        global _restore_helper
        if answer:
            self.session.open(TryQuitMainloop, 3)
        _restore_helper = None


def sessionstart(reason, session=None, **kwargs):
    global _restore_helper
    if reason != 0:
        return
    session = session or kwargs.get("session")
    if session is None or config.skin.primary_skin.value != SKIN_XML:
        return
    missing = restore_runtime_state()
    if missing and _restore_helper is None:
        _restore_helper = _RestoreTeamHelper(session, missing)


def main(session, **kwargs):
    if config.skin.primary_skin.value != SKIN_XML:
        session.open(
            MessageBox,
            _("Bitte zuerst den BundesligaWQHD aktivieren."),
            MessageBox.TYPE_ERROR,
            timeout=8
        )
        return

    # Late safety net in case a restore happened after plugin discovery.
    restore_runtime_state()
    from .screens import BundesligaWQHDConfig
    session.open(BundesligaWQHDConfig)


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name=_(PLUGIN_NAME),
            description=_("BundesligaWQHD personalisieren"),
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="plugin.png",
            fnc=main
        ),
        PluginDescriptor(
            where=PluginDescriptor.WHERE_AUTOSTART,
            fnc=autostart
        ),
        PluginDescriptor(
            where=PluginDescriptor.WHERE_SESSIONSTART,
            fnc=sessionstart
        ),
    ]
