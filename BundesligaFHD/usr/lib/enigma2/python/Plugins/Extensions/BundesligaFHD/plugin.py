# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

from Components.config import config, configfile
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


def _install_weather_integration():
    """Aktiviert animierte Wetterbilder im OAWeather-Hauptfenster."""
    try:
        from .weatherintegration import install_oaweather_integration
        install_oaweather_integration()
    except Exception as error:
        print("[BundesligaFHDConfig] OAWeather-Integration fehlgeschlagen: %s" % error)


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
        print("[BundesligaFHDConfig] Startup restore failed: %s" % error)
    return None


def autostart(reason, **kwargs):
    if reason == 0:
        restore_runtime_state()


_restore_helper = None


def _openatv_version():
    """Return the OpenATV image version without requiring a new-only API."""
    try:
        from Components.SystemInfo import BoxInfo
        version = str(BoxInfo.getItem("imgversion") or "").strip()
        if version:
            return version
    except Exception:
        pass

    try:
        values = {}
        with open("/etc/image-version", "r") as version_file:
            for line in version_file:
                key, separator, value = line.strip().partition("=")
                if separator:
                    values[key] = value.strip().strip("\"'")
        return values.get("distro_version") or values.get("version") or ""
    except Exception:
        return ""


def _is_openatv_76():
    return _openatv_version().startswith("7.6")


def _contains_e2mdb(*values):
    return any("e2mdb" in str(value or "").lower() for value in values)


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
        from .screens import BundesligaFHDTeamDownload
        self.session.openWithCallback(
            self._download_finished,
            BundesligaFHDTeamDownload,
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
    _install_weather_integration()

    # OpenATV 7.6 has no e2MDB support.  Replace its globally generated
    # ChannelSelection choices with the filtered choices for this skin.
    if _is_openatv_76():
        _sync_channel_selection()

    missing = restore_runtime_state()
    if missing and _restore_helper is None:
        _restore_helper = _RestoreTeamHelper(session, missing)


def _channel_selection_choices():
    """Read the ChannelSelection choices belonging to the newly loaded skin."""
    try:
        from skin import domScreens
        from xml.etree.ElementTree import parse

        filter_e2mdb = _is_openatv_76()
        hidden_screens = set()
        screen_choices = [("", _("Legacy mode"))]
        for screen_name in domScreens:
            element, _source = domScreens.get(screen_name, (None, None))
            if element is not None and element.get("base") == "ChannelSelection":
                label = element.get("label", screen_name)
                if filter_e2mdb and _contains_e2mdb(screen_name, label):
                    hidden_screens.add(screen_name)
                    continue
                screen_choices.append((screen_name, label))

        skin_directory = os.path.dirname(config.skin.primary_skin.value)
        template_file = os.path.join(
            "/usr/share/enigma2",
            skin_directory,
            "skinTemplates.xml"
        )
        if not os.path.isfile(template_file):
            return None, None

        template_choices = []
        for element in parse(template_file).getroot().findall(".//template"):
            if element.get("component") != "serviceList":
                continue
            name = element.get("name", "").strip()
            if not name:
                continue
            template_screens = {
                item.strip()
                for item in element.get("screens", "").split(",")
                if item.strip()
            }
            if filter_e2mdb and (
                _contains_e2mdb(name) or hidden_screens.intersection(template_screens)
            ):
                continue
            template_choices.append((name, name))
        return screen_choices, template_choices
    except Exception as error:
        print("[BundesligaFHDConfig] Senderlisten-Auswahl konnte nicht gelesen werden: %s" % error)
        return None, None


def _sync_channel_selection():
    """Update the choices and replace values unavailable in the active image."""
    channel_config = getattr(config, "channelSelection", None)
    if channel_config is None or not hasattr(channel_config, "screenStyle") or not hasattr(channel_config, "widgetStyle"):
        return

    screen_choices, template_choices = _channel_selection_choices()
    if not screen_choices or not template_choices:
        return

    screen_config = channel_config.screenStyle
    template_config = channel_config.widgetStyle
    old_screen = str(screen_config.value or "")
    old_template = str(template_config.value or "")
    valid_screens = [item[0] for item in screen_choices]
    valid_templates = [item[0] for item in template_choices]
    primary_skin = config.skin.primary_skin.value

    if primary_skin == SKIN_XML:
        screen_map = {
            "GradientChannelSelectionPIG": "BundesligaChannelSelectionPIG",
            "GradientChannelSelection": "BundesligaChannelSelection",
            "ChannelSelection_4_Backdrops": "BundesligaChannelSelectionPIG",
            "ChannelSelection_5_Poster": "BundesligaChannelSelection",
            "ChannelSelection3_Fields_Poster": "BundesligaChannelSelectionPIG",
            "ChannelSelection3_Fields": "BundesligaChannelSelectionPIG",
        }
        template_map = {
            "Gradient Standard": "Bundesliga Standard",
            "Gradient Standard 3 Lines": "Bundesliga Standard",
            "Gradient Standard 3 Lines + Next": "Bundesliga Standard",
            "Gradient 3 Fields": "Bundesliga Standard",
            "Gradient 3 Fields_Poster": "Bundesliga Standard",
            "Gradient 4 Backdrops": "Bundesliga Standard",
            "Gradient 5 Poster": "Bundesliga Standard",
        }
        fallback_screen = "BundesligaChannelSelection"
        fallback_template = "Bundesliga Standard"
    elif primary_skin in ("GradientFHD/skin.xml", "GradientWQHD/skin.xml"):
        screen_map = {
            "BundesligaChannelSelectionPIG": "GradientChannelSelectionPIG",
            "BundesligaChannelSelection": "GradientChannelSelection",
        }
        template_map = {"Bundesliga Standard": "Gradient Standard"}
        fallback_screen = "GradientChannelSelection"
        fallback_template = "Gradient Standard"
    else:
        screen_map = {}
        template_map = {}
        fallback_screen = ""
        fallback_template = valid_templates[0]

    new_screen = old_screen if old_screen in valid_screens else screen_map.get(old_screen, fallback_screen)
    new_template = old_template if old_template in valid_templates else template_map.get(old_template, fallback_template)
    if new_screen not in valid_screens:
        new_screen = fallback_screen if fallback_screen in valid_screens else ""
    if new_template not in valid_templates:
        new_template = fallback_template if fallback_template in valid_templates else valid_templates[0]

    screen_config.setChoices(screen_choices, default=new_screen)
    template_config.setChoices(template_choices, default=new_template)
    screen_config.value = new_screen
    template_config.value = new_template
    screen_config.save()
    template_config.save()
    configfile.save()
    print("[BundesligaFHDConfig] Senderlisten-Auswahl synchronisiert: %s / %s" % (new_screen, new_template))


def skinchange(session=None, **kwargs):
    """Keep ChannelSelection screen/list values valid during fast skin reload."""
    try:
        # OpenATV keeps component templates globally.  Clear the templates from
        # the previous skin before the ChannelSelection dialog is rebuilt.
        from skin import reloadSkinTemplates
        reloadSkinTemplates(clear=True)
    except Exception as error:
        print("[BundesligaFHDConfig] Senderlisten-Templates konnten nicht neu geladen werden: %s" % error)

    _sync_channel_selection()


def main(session, **kwargs):
    if config.skin.primary_skin.value != SKIN_XML:
        session.open(
            MessageBox,
            _("Bitte zuerst den BundesligaFHD aktivieren."),
            MessageBox.TYPE_ERROR,
            timeout=8
        )
        return

    # Late safety net in case a restore happened after plugin discovery.
    restore_runtime_state()
    from .screens import BundesligaFHDConfig
    session.open(BundesligaFHDConfig)


def Plugins(**kwargs):
    descriptors = [
        PluginDescriptor(
            name=_(PLUGIN_NAME),
            description=_("BundesligaFHD personalisieren"),
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="plugin.png",
            fnc=main
        ),
        PluginDescriptor(
            where=PluginDescriptor.WHERE_AUTOSTART,
            fnc=autostart
        ),
    ]

    # OpenATV 7.6 does not provide WHERE_SKINCHANGE. OpenATV 8.0 uses the
    # hook for its fast skin reload, so register it only when available.
    skinchange_where = getattr(PluginDescriptor, "WHERE_SKINCHANGE", None)
    if skinchange_where is not None:
        descriptors.append(PluginDescriptor(where=skinchange_where, fnc=skinchange))

    descriptors.append(PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart))

    return descriptors
