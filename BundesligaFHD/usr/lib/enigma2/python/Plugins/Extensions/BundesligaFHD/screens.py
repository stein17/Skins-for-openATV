# -*- coding: utf-8 -*-
from __future__ import absolute_import

from importlib import invalidate_caches
from os.path import basename, isdir, isfile, join
from threading import Thread

from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.config import ConfigNothing, ConfigSelection, NoSave, getConfigListEntry
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop

from . import _
from .constants import COLOR_ITEMS, PLUGIN_NAME, PLUGIN_VERSION, SKIN_BASE
from .manager import SkinManager
from .teamassets import format_bytes
from .weathericons import DEFAULT_ICONSET_ID, WeatherIconsetManager
from .settings import (
    cancel_weather_settings,
    cancel_colors,
    color_config,
    get_overrides,
    get_saved_team,
    overrides_active,
    reset_colors,
    save_colors,
    save_team,
    save_weather_settings,
    set_saved_skinpart,
    weather_animation_config,
    weather_animation_interval_config,
    weather_iconset_config,
)

MAIN_SKIN_GRADIENT = """
<screen name="BundesligaFHDConfig" position="0,0" size="1920,1080" title="BundesligaFHD Config" flags="wfNoBorder" backgroundColor="transparent">
    <widget name="config" position="305,125" size="1050,810" itemHeight="54" font="Regular;30" halign="left" valign="center" foregroundColor="bl_text" foregroundColorSelected="club_selection_fg" backgroundColor="bl_bg" selectionPixmap="Verein/select_54.png" borderWidth="1" borderColor="black" scrollbarMode="showOnDemand" enableWrapAround="1" />
    <widget name="key_menu_hint" position="1210,988" size="400,38" font="Regular; 26" halign="right" valign="center" backgroundColor="bl_bg" transparent="1" />
    <widget name="Picture" position="1386,543" size="460,260" alphatest="on" scale="1" zPosition="2" />
    <panel name="Template_Color_Button_Automatic_all" />
    <panel name="Template_Text_Buttons_M_O_E" />
    <panel name="Logo_Setup_Default" />
    <panel name="Header_Title_Clock_Setup" />
    <panel name="VideoPicture_Setup" />
    <panel name="Bundesliga_Basic_Setup_club_primary" />
    <panel name="Bundesliga_Setup_right_Pic_club_primary" />
    <panel name="Banner_Setup_Default" />
    <panel position="30,25" size="130,130">
      <panel name="Logo_Bundesliga_Default" />
    </panel>
</screen>
"""

SKINPART_SKIN_GRADIENT = """
<screen name="BundesligaFHDSkinParts" position="0,0" size="1920,1080" title="BundesligaFHD Skinparts" flags="wfNoBorder" backgroundColor="transparent">
    <widget name="config" position="305,125" size="1050,810" itemHeight="54" font="Regular;30" halign="left" valign="center" foregroundColor="bl_text" foregroundColorSelected="club_selection_fg" backgroundColor="bl_bg" selectionPixmap="Verein/select_54.png" borderWidth="1" borderColor="black" transparent="1" scrollbarMode="showOnDemand" enableWrapAround="1" />
    <widget name="Picture" position="1386,543" size="460,260" alphatest="on" scale="1" zPosition="2" />
    <panel name="Template_Color_Button_Automatic_all" />
    <panel name="Template_Text_Buttons_M_O_E" />
    <panel name="Logo_Setup_Default" />
    <panel name="Header_Title_Clock_Setup" />
    <panel name="VideoPicture_Setup" />
    <panel name="Bundesliga_Basic_Setup_club_primary" />
    <panel name="Bundesliga_Setup_right_Pic_club_primary" />
    <panel name="Banner_Setup_Default" />
    <panel position="30,25" size="130,130">
      <panel name="Logo_Bundesliga_Default" />
    </panel>
</screen>
"""

TEAM_DOWNLOAD_SKIN = """
<screen name="BundesligaFHDTeamDownload" position="0,0" size="1920,1080" title="Verein installieren" flags="wfNoBorder" backgroundColor="transparent">
    <widget name="status" position="305,125" size="1050,660" itemHeight="54" font="Regular;30" halign="left" valign="center" foregroundColor="bl_text" foregroundColorSelected="club_selection_fg" backgroundColor="bl_bg" selectionPixmap="Verein/select_54.png" borderWidth="1" borderColor="black" transparent="1" />
    <panel name="Template_Color_Button_Automatic_all" />
    <panel name="Template_Text_Buttons_M_O_E" />
    <panel name="Logo_Setup_Default" />
    <panel name="Header_Title_Clock_Setup" />
    <panel name="VideoPicture_Setup" />
    <panel name="Bundesliga_Basic_Setup_club_primary" />
    <panel name="Bundesliga_Setup_right_Pic_club_primary" />
    <panel name="Banner_Setup_Default" />
    <panel position="30,25" size="130,130">
      <panel name="Logo_Bundesliga_Default" />
    </panel>
</screen>
"""

TEAM_MANAGER_SKIN = """
<screen name="BundesligaFHDTeamManager" position="0,0" size="1920,1080" title="Installierte Vereine" flags="wfNoBorder" backgroundColor="transparent">
    <widget name="list" position="305,125" size="1050,760" itemHeight="54" font="Regular;30" halign="left" valign="center" foregroundColor="bl_text" foregroundColorSelected="club_selection_fg" backgroundColor="bl_bg" selectionPixmap="Verein/select_54.png" borderWidth="1" borderColor="black" scrollbarMode="showOnDemand" enableWrapAround="1" />
    <widget name="hint" position="305,925" size="1050,45" font="Regular;30" halign="center" valign="center" foregroundColor="club_primary" backgroundColor="bl_bg" transparent="1" />
    <panel name="Template_Color_Button_Automatic_all" />
    <panel name="Template_Text_Buttons_M_O_E" />
    <panel name="Logo_Setup_Default" />
    <panel name="Header_Title_Clock_Setup" />
    <panel name="VideoPicture_Setup" />
    <panel name="Bundesliga_Basic_Setup_club_primary" />
    <panel name="Bundesliga_Setup_right_Pic_club_primary" />
    <panel name="Banner_Setup_Default" />
    <panel position="30,25" size="130,130">
      <panel name="Logo_Bundesliga_Default" />
    </panel>
</screen>
"""

# ConfigList-Sonderstil für Teamprofile, die einen aktiven Screen
# <screen name="setup_config"> enthalten. Ohne itemGradientSelected werden
# die bsListboxEntry-Pixmaps von OpenATV wieder sichtbar.
_GRADIENT_MAIN_WIDGET = 'foregroundColorSelected="club_selection_fg" backgroundColor="bl_bg" itemGradientSelected="V_IGS_T,V_IGS_C,V_IGS_B,vertical" borderWidth="1" borderColor="black" transparent="1"'
_CONTRAST_MAIN_WIDGET = 'foregroundColorSelected="bl_text" backgroundColor="bl_bg" backgroundColorSelected="club_dark" transparent="1"'

MAIN_SKIN_CONTRAST = MAIN_SKIN_GRADIENT.replace(_GRADIENT_MAIN_WIDGET, _CONTRAST_MAIN_WIDGET)
SKINPART_SKIN_CONTRAST = SKINPART_SKIN_GRADIENT.replace(_GRADIENT_MAIN_WIDGET, _CONTRAST_MAIN_WIDGET)


def _set_preview(screen, preview):
    """Show a preview only after the Pixmap widget has been instantiated."""
    try:
        picture = screen["Picture"]
    except Exception:
        return False

    instance = getattr(picture, "instance", None)
    if instance is None:
        return False

    if preview:
        try:
            instance.setPixmapFromFile(preview)
            picture.show()
            return True
        except Exception as error:
            print("[BundesligaFHDConfig] Preview error: %s" % error)

    picture.hide()
    return False


class BundesligaFHDTeamDownload(Screen):
    skin = TEAM_DOWNLOAD_SKIN

    def __init__(self, session, assets, entry):
        self.session = session
        self.assets = assets
        self.entry = entry
        self._started = False
        Screen.__init__(self, session)
        self["headline"] = Label(_("%s installieren") % entry["title"])
        self["status"] = Label(_("Download wird vorbereitet …"))
        self["actions"] = ActionMap(["SetupActions"], {"cancel": self._ignore_cancel}, -2)
        self.onLayoutFinish.append(self._start)

    def _ignore_cancel(self):
        return

    def _start(self):
        if self._started:
            return
        self._started = True
        try:
            from twisted.internet import reactor
            self._reactor = reactor
        except Exception as error:
            self.close({"ok": False, "error": _("Downloaddienst nicht verfügbar: %s") % error})
            return
        worker = Thread(target=self._worker, name="BundesligaFHD-TeamDownload")
        worker.daemon = True
        worker.start()

    def _progress_from_thread(self, text):
        self._reactor.callFromThread(self._set_status, _(text))

    def _set_status(self, text):
        self["status"].setText(text)

    def _worker(self):
        try:
            self.assets.install(self.entry, progress=self._progress_from_thread)
            result = {"ok": True, "error": ""}
        except Exception as error:
            result = {"ok": False, "error": str(error)}
        self._reactor.callFromThread(self.close, result)


class BundesligaFHDWeatherIconsetDownload(Screen):
    skin = TEAM_DOWNLOAD_SKIN

    def __init__(self, session, manager, entry):
        self.session = session
        self.manager = manager
        self.entry = entry
        self._started = False
        Screen.__init__(self, session)
        self["headline"] = Label(_("Wetter-Iconset installieren"))
        self["status"] = Label(_("Download wird vorbereitet …"))
        self["actions"] = ActionMap(["SetupActions"], {"cancel": self._ignore_cancel}, -2)
        self.onLayoutFinish.append(self._start)

    def _ignore_cancel(self):
        return

    def _start(self):
        if self._started:
            return
        self._started = True
        try:
            from twisted.internet import reactor
            self._reactor = reactor
        except Exception as error:
            self.close({"ok": False, "error": _("Downloaddienst nicht verfügbar: %s") % error})
            return
        worker = Thread(target=self._worker, name="BundesligaFHD-WeatherIconsetDownload")
        worker.daemon = True
        worker.start()

    def _progress_from_thread(self, status):
        self._reactor.callFromThread(self["status"].setText, _(status))

    def _worker(self):
        try:
            self.manager.install(self.entry["id"], progress=self._progress_from_thread)
            result = {"ok": True, "error": ""}
        except Exception as error:
            result = {"ok": False, "error": str(error)}
        self._reactor.callFromThread(self.close, result)


class BundesligaFHDTeamManager(Screen):
    skin = TEAM_MANAGER_SKIN

    def __init__(self, session, manager):
        self.session = session
        self.manager = manager
        self.assets = manager.assets
        self._entry_by_text = {}
        Screen.__init__(self, session)
        self["headline"] = Label(_("Installierte Vereinsbilder"))
        self["list"] = MenuList([], enableWrapAround=True)
        self["hint"] = Label(_("Der aktive Verein und das Default-Design sind geschützt."))
        self["key_red"] = Label(_("Löschen"))
        self["key_green"] = Label(_("Schließen"))
        self["key_blue"] = Label(_("Aktualisieren"))
        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions"],
            {
                "cancel": self.close,
                "green": self.close,
                "red": self.keyDelete,
                "blue": self.keyUpdate,
                "ok": self.keyInfo,
            },
            -2
        )
        self._refresh()

    def _refresh(self):
        active = self.manager.current_team_filename()
        rows = []
        self._entry_by_text = {}
        for entry in self.assets.installed_teams():
            status = _("Standard – geschützt") if self.assets.is_default(entry) else _("Installiert")
            if entry["profile"] == active:
                status = _("Aktiv – geschützt")
            row = "%s   |   %s   |   %s" % (
                entry["title"],
                format_bytes(self.assets.installed_size(entry)),
                status,
            )
            rows.append(row)
            self._entry_by_text[row] = entry
        if not rows:
            rows = [_("Keine Vereinsbilder installiert")]
        self["list"].setList(rows)

    def _current_entry(self):
        return self._entry_by_text.get(self["list"].getCurrent())

    def keyDelete(self):
        entry = self._current_entry()
        if not entry:
            return
        if self.assets.is_default(entry):
            self.session.open(
                MessageBox,
                _("Das Default-Design gehört zum Basis-Skin und kann nicht gelöscht werden."),
                MessageBox.TYPE_INFO,
                timeout=7
            )
            return
        if entry["profile"] == self.manager.current_team_filename():
            self.session.open(
                MessageBox,
                _("%s ist zurzeit aktiv und kann deshalb nicht gelöscht werden.") % entry["title"],
                MessageBox.TYPE_INFO,
                timeout=7
            )
            return
        self.session.openWithCallback(
            lambda answer: self._delete_answer(answer, entry),
            MessageBox,
            _("Sollen die heruntergeladenen Bilder von %s wirklich gelöscht werden?") % entry["title"],
            MessageBox.TYPE_YESNO,
            default=False
        )

    def _delete_answer(self, answer, entry):
        if not answer:
            return
        try:
            self.assets.remove(entry, self.manager.current_team_filename())
        except Exception as error:
            self.session.open(MessageBox, _("Löschen fehlgeschlagen:\n%s") % error, MessageBox.TYPE_ERROR)
            return
        self._refresh()

    def keyInfo(self):
        entry = self._current_entry()
        if not entry:
            return
        self.session.open(
            MessageBox,
            _("%s\n\nBelegter Speicher: %s\nQuelle: %s\nProfil: %s") % (
                entry["title"],
                format_bytes(self.assets.installed_size(entry)),
                _("openATV-Feed") if self.assets.is_default(entry) else _("GitHub python3"),
                entry["profile"],
            ),
            MessageBox.TYPE_INFO
        )

    def keyUpdate(self):
        entry = self._current_entry()
        if not entry:
            return
        if self.assets.is_default(entry):
            self.session.open(
                MessageBox,
                _("Das Default-Design gehört zum Basis-Skin und wird automatisch über den openATV-Feed aktualisiert."),
                MessageBox.TYPE_INFO,
                timeout=8
            )
            return
        self.session.openWithCallback(
            lambda answer: self._update_answer(answer, entry),
            MessageBox,
            _("Sollen die Bilder von %s jetzt neu aus dem GitHub-Ordner geladen werden?") % entry["title"],
            MessageBox.TYPE_YESNO,
            default=True
        )

    def _update_answer(self, answer, entry):
        if answer:
            self.session.openWithCallback(
                lambda result: self._update_finished(result, entry),
                BundesligaFHDTeamDownload,
                self.assets,
                entry
            )

    def _update_finished(self, result, entry):
        if not result or not result.get("ok"):
            error = result.get("error") if result else _("Unbekannter Fehler")
            self.session.open(
                MessageBox,
                _("Die Vereinsbilder konnten nicht aktualisiert werden.\n\n%s") % error,
                MessageBox.TYPE_ERROR
            )
            return
        self._refresh()
        self.session.openWithCallback(
            self._restart_after_update,
            MessageBox,
            _("Die Bilder von %s wurden direkt aus GitHub aktualisiert.\n\nGUI jetzt neu starten?") % entry["title"],
            MessageBox.TYPE_YESNO,
            default=entry["profile"] == self.manager.current_team_filename()
        )

    def _restart_after_update(self, answer):
        if answer:
            self.session.open(TryQuitMainloop, 3)


class BundesligaFHDConfig(Screen, ConfigListScreen):
    skin = MAIN_SKIN_GRADIENT

    def __init__(self, session):
        self.session = session
        self.manager = SkinManager()
        self.weather_icons = WeatherIconsetManager()
        self._layout_ready = False
        self.skinparts_changed = False
        self.pending_replace = None
        self.teams = self.manager.list_teams()
        self.start_team = self.manager.current_team()
        if not self.start_team:
            self.start_team = self.manager.source_for_team_filename(get_saved_team())
        if not self.start_team:
            self.start_team = self.manager.default_team(self.teams)

        # Der aktuell aktive Team-Skin entscheidet automatisch über den
        # ConfigList-Stil. Teamprofile mit aktivem setup_config verwenden
        # die kontrastreiche, einfarbige Auswahl ohne Gradient.
        self.skin = (
            MAIN_SKIN_CONTRAST
            if self.manager.team_uses_special_config_style(self.start_team)
            else MAIN_SKIN_GRADIENT
        )
        Screen.__init__(self, session)

        team_choices = self.teams or [("", _("Keine Teamprofile gefunden"))]
        self.team_config = NoSave(ConfigSelection(default=self.start_team, choices=team_choices))
        self.skinparts_action = NoSave(ConfigNothing())

        self.list = []
        self._build_list()
        ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changedEntry)

        self["key_red"] = Label(_("Abbrechen"))
        self["key_green"] = Label(_("Speichern"))
        self["key_yellow"] = Label(_("Skinparts"))
        self["key_blue"] = Label(_("Vereine"))
        self["Picture"] = Pixmap()
        self["key_menu_hint"] = Label(_("MENU: OAWeather einstellen"))

        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions", "MenuActions"],
            {
                "cancel": self.keyCancel,
                "red": self.keyCancel,
                "green": self.keySave,
                "yellow": self.openSkinparts,
                "blue": self.openTeamManager,
                "ok": self.keyOK,
                "menu": self.openWeatherSettings,
            },
            -2
        )

        self.onLayoutFinish.append(self._layoutFinished)

    def _layoutFinished(self):
        self._layout_ready = True
        if self.selectionChanged not in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.append(self.selectionChanged)
        self.selectionChanged()

    def _build_list(self):
        self.team_entry = getConfigListEntry(_("Bundesliga Verein:"), self.team_config)
        self.list.append(self.team_entry)
        self.list.append(getConfigListEntry(_("──────── Senderliste ────────"), NoSave(ConfigNothing())))
        for key, label, _xml_name in COLOR_ITEMS[:5]:
            self.list.append(getConfigListEntry(_(label), color_config(key)))
        self.list.append(getConfigListEntry(_("──────── Infobar ────────"), NoSave(ConfigNothing())))
        for key, label, _xml_name in COLOR_ITEMS[5:8]:
            self.list.append(getConfigListEntry(_(label), color_config(key)))
        self.list.append(getConfigListEntry(_("──────── Wetteranimation ────────"), NoSave(ConfigNothing())))
        self.list.append(getConfigListEntry(_("Wetteranimation:"), weather_animation_config()))
        self.list.append(getConfigListEntry(_("Bildwechsel (kleiner = schneller):"), weather_animation_interval_config()))
        self.weather_iconset_entry = getConfigListEntry(
            _("Animiertes Wetter-Iconset:"),
            weather_iconset_config()
        )
        self.list.append(self.weather_iconset_entry)
        self.list.append(getConfigListEntry(_("──────── Menü / Setup ────────"), NoSave(ConfigNothing())))
        for key, label, _xml_name in COLOR_ITEMS[8:12]:
            self.list.append(getConfigListEntry(_(label), color_config(key)))
        self.list.append(getConfigListEntry(_("──────── Allgemein ────────"), NoSave(ConfigNothing())))
        for key, label, _xml_name in COLOR_ITEMS[12:]:
            self.list.append(getConfigListEntry(_(label), color_config(key)))
        if self.manager.discover_categories():
            self.skinparts_entry = getConfigListEntry(_("Zusätzliche Skinparts öffnen"), self.skinparts_action)
            self.list.append(self.skinparts_entry)
        else:
            self.skinparts_entry = None

    def changedEntry(self):
        self.selectionChanged()

    def selectionChanged(self):
        if not self._layout_ready:
            return
        if self["config"].getCurrent() == self.weather_iconset_entry:
            preview = join(
                SKIN_BASE,
                "weather",
                "IconsetPreviews",
                "%s.png" % weather_iconset_config().value
            )
            if not isfile(preview):
                preview = ""
        else:
            source = self.team_config.value
            preview = self.manager.preview_for_source(source, "team_colors")
        _set_preview(self, preview)

    def keyOK(self):
        if self.skinparts_entry is not None and self["config"].getCurrent() == self.skinparts_entry:
            self.openSkinparts()

    def openWeatherSettings(self):
        """Open OAWeather settings and return here when the screen is closed."""
        try:
            from Plugins.Extensions.OAWeather.plugin import WeatherSettingsView
        except ImportError as error:
            if isdir("/usr/lib/enigma2/python/Plugins/Extensions/OAWeather"):
                self.session.open(
                    MessageBox,
                    _("OAWeather ist vorhanden, konnte aber nicht geladen werden:\n%s") % error,
                    MessageBox.TYPE_ERROR
                )
            else:
                self.session.openWithCallback(
                    self._installOAWeatherAnswer,
                    MessageBox,
                    _("OAWeather ist nicht installiert.\n\nJetzt aus dem OpenATV-Feed installieren?"),
                    MessageBox.TYPE_YESNO,
                    default=True
                )
            return
        except Exception as error:
            self.session.open(
                MessageBox,
                _("Die OAWeather-Einstellungen konnten nicht geöffnet werden:\n%s") % error,
                MessageBox.TYPE_ERROR
            )
            return

        self.session.open(WeatherSettingsView)

    def _installOAWeatherAnswer(self, answer):
        if not answer:
            return
        try:
            from Screens.Console import Console
        except ImportError as error:
            self.session.open(
                MessageBox,
                _("Die Installationskonsole konnte nicht geöffnet werden:\n%s") % error,
                MessageBox.TYPE_ERROR
            )
            return

        commands = [
            "opkg update",
            "opkg install enigma2-plugin-extensions-oaweather"
        ]
        self.session.openWithCallback(
            self._oaWeatherInstallFinished,
            Console,
            title=_("OAWeather installieren"),
            cmdlist=commands,
            closeOnSuccess=True
        )

    def _oaWeatherInstallFinished(self, *args):
        invalidate_caches()
        if isdir("/usr/lib/enigma2/python/Plugins/Extensions/OAWeather"):
            self.session.openWithCallback(
                self._oaWeatherRestartAnswer,
                MessageBox,
                _("OAWeather wurde installiert.\n\nDamit Wetterquelle und Plugin vollständig geladen werden, muss die GUI neu gestartet werden.\n\nJetzt neu starten?"),
                MessageBox.TYPE_YESNO,
                default=True
            )
        else:
            self.session.open(
                MessageBox,
                _("OAWeather wurde nicht installiert. Bitte die Ausgabe der Installationskonsole prüfen."),
                MessageBox.TYPE_ERROR
            )

    def _oaWeatherRestartAnswer(self, answer):
        if answer:
            self.session.open(TryQuitMainloop, 3)

    def openSkinparts(self):
        if not self.manager.discover_categories():
            self.session.open(
                MessageBox,
                _("Zurzeit sind außer den Teamprofilen noch keine zusätzlichen Skinpart-Ordner vorhanden."),
                MessageBox.TYPE_INFO,
                timeout=8
            )
            return
        self.session.openWithCallback(self.skinpartsCallback, BundesligaFHDSkinParts, self.manager)

    def skinpartsCallback(self, changed=False):
        if changed:
            self.skinparts_changed = True

    def openTeamManager(self):
        self.session.open(BundesligaFHDTeamManager, self.manager)

    def keySave(self):
        self.pending_replace = None
        selected_team = self.team_config.value
        team_changed = bool(selected_team and selected_team != self.manager.current_team())
        selected_entry = self.manager.assets.team_for_profile(selected_team)
        if selected_entry and not self.manager.assets.is_installed(selected_entry):
            self._ask_team_download(selected_entry)
            return
        self._check_iconset_download(team_changed)

    def _ask_team_download(self, selected_entry):
        current_entry = self.manager.assets.team_for_profile(self.manager.current_team())
        if (
            current_entry
            and current_entry["id"] != selected_entry["id"]
            and not self.manager.assets.is_default(current_entry)
            and self.manager.assets.is_installed(current_entry)
        ):
            choices = [
                (
                    _("%s installieren und %s behalten")
                    % (selected_entry["title"], current_entry["title"]),
                    "keep"
                ),
                (
                    _("%s löschen und durch %s ersetzen")
                    % (current_entry["title"], selected_entry["title"]),
                    "replace"
                ),
                (_("Abbrechen"), "cancel"),
            ]
            self.session.openWithCallback(
                lambda answer: self._team_download_choice(answer, selected_entry, current_entry),
                ChoiceBox,
                title=_("%s ist noch nicht installiert.\n\nWas soll mit %s geschehen?")
                % (selected_entry["title"], current_entry["title"]),
                list=choices
            )
            return

        self.session.openWithCallback(
            lambda answer: self._simple_download_answer(answer, selected_entry),
            MessageBox,
            _("Die Bilder für %s sind noch nicht installiert.\n\nJetzt von GitHub herunterladen und installieren?")
            % selected_entry["title"],
            MessageBox.TYPE_YESNO,
            default=True
        )

    def _team_download_choice(self, answer, selected_entry, current_entry):
        if not answer or answer[1] == "cancel":
            return
        replace_entry = current_entry if answer[1] == "replace" else None
        self._start_team_download(selected_entry, replace_entry)

    def _simple_download_answer(self, answer, selected_entry):
        if answer:
            self._start_team_download(selected_entry, None)

    def _start_team_download(self, selected_entry, replace_entry):
        self.pending_replace = replace_entry
        self.session.openWithCallback(
            self._team_download_finished,
            BundesligaFHDTeamDownload,
            self.manager.assets,
            selected_entry
        )

    def _team_download_finished(self, result):
        if not result or not result.get("ok"):
            self.pending_replace = None
            error = result.get("error") if result else _("Unbekannter Fehler")
            self.session.open(
                MessageBox,
                _("Der Verein wurde nicht installiert. Die bisherige Auswahl bleibt unverändert.\n\n%s") % error,
                MessageBox.TYPE_ERROR
            )
            return
        selected_team = self.team_config.value
        team_changed = bool(selected_team and selected_team != self.manager.current_team())
        self._check_iconset_download(team_changed)

    def _check_iconset_download(self, team_changed):
        iconset_id = weather_iconset_config().value
        if iconset_id == DEFAULT_ICONSET_ID or self.weather_icons.is_installed(iconset_id):
            self._continue_save(team_changed)
            return
        entry = self.weather_icons.entry(iconset_id)
        if not entry:
            self.session.open(
                MessageBox,
                _("Das ausgewählte Wetter-Iconset ist unbekannt."),
                MessageBox.TYPE_ERROR
            )
            return
        self.session.openWithCallback(
            lambda answer: self._iconset_download_answer(answer, team_changed, entry),
            MessageBox,
            _("%s ist noch nicht installiert.\n\nJetzt %s von GitHub herunterladen?\n\nDas Standardset bleibt als Rückfall erhalten.")
            % (entry["title"], self.weather_icons.package_size_text(entry)),
            MessageBox.TYPE_YESNO,
            default=True
        )

    def _iconset_download_answer(self, answer, team_changed, entry):
        if not answer:
            return
        self.session.openWithCallback(
            lambda result: self._iconset_download_finished(result, team_changed),
            BundesligaFHDWeatherIconsetDownload,
            self.weather_icons,
            entry
        )

    def _iconset_download_finished(self, result, team_changed):
        if not result or not result.get("ok"):
            error = result.get("error") if result else _("Unbekannter Fehler")
            self.session.open(
                MessageBox,
                _("Das Wetter-Iconset wurde nicht installiert. Die bisherige Auswahl bleibt erhalten.\n\n%s") % error,
                MessageBox.TYPE_ERROR
            )
            return
        self._continue_save(team_changed)

    def _continue_save(self, team_changed):
        if team_changed and (overrides_active() or self.manager.color_override_exists()):
            self.session.openWithCallback(
                self._confirm_team_change,
                MessageBox,
                _("Mit dem Vereinswechsel werden alle individuellen Farbanpassungen auf Vereinsstandard zurückgesetzt.\n\nFortfahren?"),
                MessageBox.TYPE_YESNO,
                default=True
            )
            return
        self._apply_settings(team_changed)

    def _confirm_team_change(self, answer):
        if answer:
            self._apply_settings(True)
        else:
            self.pending_replace = None

    def _apply_settings(self, team_changed):
        try:
            selected_team = self.team_config.value
            if selected_team:
                self.manager.apply_team(selected_team)
                save_team(basename(selected_team))
            if team_changed:
                reset_colors(save=True)
                self.manager.write_color_overrides({})
            else:
                save_colors()
                self.manager.write_color_overrides(get_overrides())
            save_weather_settings()
        except Exception as error:
            self.pending_replace = None
            self.session.open(MessageBox, _("Speichern fehlgeschlagen:\n%s") % error, MessageBox.TYPE_ERROR)
            return
        remove_error = ""
        if self.pending_replace:
            try:
                self.manager.assets.remove(self.pending_replace, self.manager.current_team_filename())
            except Exception as error:
                remove_error = str(error)
            self.pending_replace = None
        if remove_error:
            self.session.openWithCallback(
                self._remove_warning_closed,
                MessageBox,
                _("Der neue Verein wurde installiert und aktiviert. Der bisherige Verein konnte jedoch nicht gelöscht werden:\n\n%s")
                % remove_error,
                MessageBox.TYPE_ERROR
            )
            return
        self._ask_restart()

    def _remove_warning_closed(self, *args):
        self._ask_restart()

    def keyCancel(self):
        self.pending_replace = None
        changed = self["config"].isChanged()
        if changed:
            self.session.openWithCallback(
                self._cancel_confirmed,
                MessageBox,
                _("Änderungen ohne Speichern verwerfen?"),
                MessageBox.TYPE_YESNO,
                default=False
            )
        else:
            cancel_colors()
            cancel_weather_settings()
            if self.skinparts_changed:
                self._ask_restart()
            else:
                self.close()

    def _cancel_confirmed(self, answer):
        if answer:
            cancel_colors()
            cancel_weather_settings()
            if self.skinparts_changed:
                self._ask_restart()
            else:
                self.close()

    def _ask_restart(self):
        box = self.session.openWithCallback(
            self._restart_callback,
            MessageBox,
            _("Die GUI muss neu gestartet werden, damit die Änderungen wirksam werden.\n\nJetzt neu starten?"),
            MessageBox.TYPE_YESNO,
            default=True
        )
        box.setTitle(_("GUI-Neustart"))

    def _restart_callback(self, answer):
        if answer:
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close()

    def about(self):
        text = "%s\nVersion %s\n\n%s" % (
            PLUGIN_NAME,
            PLUGIN_VERSION,
            _("Eigenständige Verwaltung der Bundesliga-Teamprofile, individuellen Farben und zusätzlichen Skinparts.")
        )
        self.session.open(MessageBox, text, MessageBox.TYPE_INFO)


class BundesligaFHDSkinParts(Screen, ConfigListScreen):
    skin = SKINPART_SKIN_GRADIENT

    def __init__(self, session, manager):
        self.session = session
        self.manager = manager
        self.skin = (
            SKINPART_SKIN_CONTRAST
            if self.manager.team_uses_special_config_style()
            else SKINPART_SKIN_GRADIENT
        )
        Screen.__init__(self, session)
        self._layout_ready = False
        self.categories = manager.discover_categories()
        self.entries = []
        self.start_values = {}
        self.list = []

        for category, title in self.categories:
            choices = manager.category_choices(category)
            current = manager.active_category_value(category)
            if current not in [item[0] for item in choices]:
                current = "default"
            cfg = NoSave(ConfigSelection(default=current, choices=choices))
            entry = getConfigListEntry(_(title) + ":", cfg)
            self.entries.append((category, cfg, entry))
            self.start_values[category] = current
            self.list.append(entry)

        ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changedEntry)
        self["key_red"] = Label(_("Abbrechen"))
        self["key_green"] = Label(_("Speichern"))
        self["Picture"] = Pixmap()
        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions"],
            {
                "cancel": self.keyCancel,
                "red": self.keyCancel,
                "green": self.keySave,
                "ok": self.keySave,
            },
            -2
        )
        self.onLayoutFinish.append(self._layoutFinished)

    def _layoutFinished(self):
        self._layout_ready = True
        if self.selectionChanged not in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.append(self.selectionChanged)
        self.selectionChanged()

    def changedEntry(self):
        self.selectionChanged()

    def _current_data(self):
        current = self["config"].getCurrent()
        for category, cfg, entry in self.entries:
            if current == entry:
                return category, cfg
        return None, None

    def selectionChanged(self):
        if not self._layout_ready:
            return
        category, cfg = self._current_data()
        preview = self.manager.preview_for_source(cfg.value, category) if cfg is not None else ""
        _set_preview(self, preview)

    def keySave(self):
        changed = False
        try:
            for category, cfg, _entry in self.entries:
                if cfg.value != self.start_values.get(category):
                    self.manager.apply_category(category, cfg.value)
                    filename = "" if cfg.value == "default" else basename(cfg.value)
                    set_saved_skinpart(category, filename)
                    changed = True
        except Exception as error:
            self.session.open(MessageBox, _("Skinpart konnte nicht gespeichert werden:\n%s") % error, MessageBox.TYPE_ERROR)
            return
        self.close(changed)

    def keyCancel(self):
        self.close(False)
