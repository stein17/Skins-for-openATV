# -*- coding: utf-8 -*-
#
# Modifiziert von stein17
# Ich habe das Plugin vor vielen Jahren erheblich erweitert.
# Es wurde oft kopiert, aber nirgendwo wurde darauf hingewiesen.
# =============================================================================
#  DEUTSCH / GERMAN
# =============================================================================
#  GradientFHD Config for Enigma2 Skins
#
#  Copyright (c) 2026  @stein17
#
#  Freeware:
#  Dieses Projekt ist Freeware. Die private Nutzung ist erlaubt.
#  Anpassungen für eigene Skins/Setups (z.B. OpenATV/Enigma2) sind ausdrücklich
#  erlaubt.
#
#  Bedingungen:
#  1) Dieser Copyright-/Lizenz-Header muss in allen Kopien und abgeleiteten
#     Versionen vollständig erhalten bleiben und darf nicht entfernt oder
#     unkenntlich gemacht werden.
#  2) Eine Weitergabe (unverändert oder geändert) ist erlaubt, sofern dieser
#     Header erhalten bleibt und die ursprünglichen Urheber genannt werden.
#  3) Eine kommerzielle Nutzung (Verkauf, Paywall, bezahlte Images/Feeds,
#     kommerzielle Bundles) ist ohne vorherige schriftliche Zustimmung der
#     Urheber nicht gestattet.
#
#  Haftungsausschluss:
#  Die Software wird „wie sie ist“ bereitgestellt, ohne jegliche Garantie.
#  Die Nutzung erfolgt auf eigene Gefahr. Für Schäden oder Datenverlust wird
#  keine Haftung übernommen.
#
#
#  ENGLISH
# =============================================================================
#  GradientFHD Config for Enigma2 Skins
#
#  Copyright (c) 2026  @stein17
#
#  Freeware:
#  This project is freeware. Private use is permitted.
#  Modifications for your own skins/setups (e.g. OpenATV/Enigma2) are explicitly
#  allowed.
#
#  Conditions:
#  1) This copyright/license header must be kept fully intact in all copies and
#     derivative works and must not be removed or obscured.
#  2) Redistribution (modified or unmodified) is permitted as long as this header
#     is retained and the original authors are credited.
#  3) Commercial use (sale, paywall, paid images/feeds, commercial bundles) is
#     not permitted without prior written consent from the authors.
#
#  Disclaimer:
#  This software is provided “as is”, without warranty of any kind.
#  Use at your own risk. The authors are not liable for any damages or data loss.
# =============================================================================

###################################
# modify by stein17
# I greatly expanded the plugin many years ago.
# It was often copied, but there was no mention of it anywhere.
# 02.26 @stein17, Many new features and improvements

# for localized messages
from __future__ import absolute_import
from __future__ import print_function
from .__init__ import _


# ---------------------------------------------------------------------
# Built-in language fallback (no .mo needed)
# Default language is English. If GUI language starts with 'de', show German strings.
try:
    from Components.Language import language
    _LANG = (language.getLanguage() or 'en').lower()
except Exception:
    _LANG = 'en'

def tr(en, de=None):
    """Return translated string without requiring gettext files."""
    try:
        if de and _LANG.startswith('de'):
            return de
    except Exception:
        pass
    return en
# ---------------------------------------------------------------------

from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigYesNo, NoSave, ConfigNothing, ConfigNumber, configfile
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Tools.Directories import *
from Tools.LoadPixmap import LoadPixmap
from Tools.WeatherID import get_woeid_from_yahoo
from Tools.Notifications import AddPopup
from os import listdir, remove, rename, path, symlink, chdir, makedirs, mkdir
import shutil
import json
import re

# For background tasks that must update the GUI safely
import time
try:
    from twisted.internet import reactor
except Exception:
    reactor = None

cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')

config.plugins.GradientFHD = ConfigSubsection()
config.plugins.GradientFHD.refreshInterval = ConfigNumber(default=10)
config.plugins.GradientFHD.woeid = ConfigNumber(default=638242)


# PrimeTime (default 20:15)
config.plugins.GradientFHD.primeTimeHour = ConfigSelection(
    default="20",
    choices=[(str(i), "%02d" % i) for i in range(0, 24)]
)
config.plugins.GradientFHD.primeTimeMinute = ConfigSelection(
    default="15",
    choices=[(str(i), "%02d" % i) for i in range(0, 60)]
)

config.plugins.GradientFHD.tempUnit = ConfigSelection(default="Celsius", choices=[
                                ("Celsius", _("Celsius")),
                                ("Fahrenheit", _("Fahrenheit"))
                                ])

# ---------------------------------------------------------------------
# PosterX storage base path
#
# The user selects where the whole "xtra" folder should be stored.
# Example: base="/media/hdd" -> /media/hdd/xtra/... (poster/backdrop/Info/...)
#
# AUTO keeps the previous behaviour (auto-detect the first writable mount).
# ---------------------------------------------------------------------
config.plugins.GradientFHD.posterXPath = ConfigSelection(
    default="AUTO",
    choices=[
        ("AUTO", tr("Auto (recommended)", "Auto (empfohlen)")),
        ("/media/hdd", "HDD (/media/hdd)"),
        ("/media/usb", "USB (/media/usb)"),
        ("/media/mmc", "MMC (/media/mmc)"),
        ("/media/net", "NAS (/media/net)"),
    ]
)


def Plugins(**kwargs):
    return [PluginDescriptor(name=_("GradientFHD  Configtool"), description=_("Personalize your GradientFHD (Skin by stein17)"), where=[PluginDescriptor.WHERE_PLUGINMENU],
    icon="plugin.png", fnc=main)]


def main(session, **kwargs):
    if config.skin.primary_skin.value == "GradientFHD/skin.xml":
        session.open(GradientFHD_Config)
    else:
        AddPopup(_('Please activate GradientFHD Skin before run the Config Plugin'), type=MessageBox.TYPE_ERROR, timeout=10)
        return []


def isInteger(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


class WeatherLocationChoiceList(Screen):
    skin = """
            <screen name="WeatherLocationChoiceList" position="center,center" size="1280,720" title="Location list" >
                    <widget source="Title" render="Label" position="70,47" size="950,43" font="Regular;35" transparent="1" />
                    <widget name="choicelist" position="70,115" size="700,480" scrollbarMode="showOnDemand" scrollbarWidth="6" transparent="1" />
                    <eLabel position=" 55,675" size="290, 5" zPosition="-10" backgroundColor="red" />
                    <eLabel position="350,675" size="290, 5" zPosition="-10" backgroundColor="green" />
                    <eLabel position="645,675" size="290, 5" zPosition="-10" backgroundColor="yellow" />
                    <eLabel position="940,675" size="290, 5" zPosition="-10" backgroundColor="blue" />
                    <widget name="key_red" position="70,635" size="260,25" zPosition="1" font="Regular;20" halign="left" foregroundColor="foreground" transparent="1" />
                    <widget name="key_green" position="365,635" size="260,25" zPosition="1" font="Regular;20" halign="left" foregroundColor="foreground" transparent="1" />
            </screen>
            """

    def __init__(self, session, location_list):
        self.session = session
        self.location_list = location_list
        list = []
        Screen.__init__(self, session)
        self.title = _("Location list")
        self["choicelist"] = MenuList(list)
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("OK"))
        self["myActionMap"] = ActionMap(["SetupActions", "ColorActions"],
        {
                "ok": self.keyOk,
                "green": self.keyOk,
                "cancel": self.keyCancel,
                "red": self.keyCancel,
        }, -1)
        self.createChoiceList()

    def createChoiceList(self):
        list = []
        print(self.location_list)
        for x in self.location_list:
            list.append((str(x[1]), str(x[0])))
        self["choicelist"].l.setList(list)

    def keyOk(self):
        returnValue = self["choicelist"].l.getCurrentSelection()[1]
        if returnValue is not None:
            self.close(returnValue)
        else:
            self.keyCancel()

    def keyCancel(self):
        self.close(None)


class GradientFHD_Config(Screen, ConfigListScreen):

    skin = """
	<screen name="GradientFHD_Config" position="center,center" size="1920,1080" title="GradientFHD Setup" flags="wfNoBorder" backgroundColor="transparent">
		<eLabel text="/ Save" position="360,994" size="240,38" font="Gradient_Font;27" halign="center" backgroundColor="black" transparent="1" valign="center" />
		<widget name="hint_yellow" position="120,780" size="967,42" font="Gradient_Font; 34" halign="left" transparent="1" valign="center" foregroundColor="yellow" backgroundColor="background" />
		<widget name="hint_menu_weather" position="120,835" size="967,42" font="Gradient_Font; 34" halign="left" transparent="1" valign="center" foregroundColor="green" backgroundColor="background" />
		<widget name="hint_epg_autodb" position="120,890" size="967,72" font="Gradient_Font; 32" halign="left" transparent="1" valign="center" foregroundColor="green" backgroundColor="background" />
		<eLabel text="GradientFHD Config" position="45,15" size="1110,60" font="Italic; 42" halign="left" valign="center" transparent="1" foregroundColor="gradient_foreground_selection" backgroundColor="background" textBorderColor="black" textBorderWidth="1" zPosition="1" />		
		<widget name="config" position="30,90" size="1050,660" itemHeight="44" font="Gradient_Font;30" backgroundColor="gradient_background" foregroundColor="gradient_foreground" itemCornerRadiusSelected="12" itemGradientSelected="gradient_BGLM,gradient_BGLL,gradient_BGLL,horizontal" foregroundColorSelected="gradient_foreground_selection" scrollbarMode="showOnDemand" enableWrapAround="1" transparent="1" />
		<widget name="Picture" position="1100,100" size="782,484" alphatest="on" zPosition="2" />
		<eLabel name="Line_Setup" position="30,760" size="1050,2" zPosition="10" backgroundColor="gradient_BGLR,gradient_BGLM,gradient_BGLR,horizontal" />
        <ePixmap  name="QR" pixmap="icons/preview_with_QR-Code.png" position="1100,600" size="782,360" zPosition="10" alphatest="blend"/>
		<ePixmap position="48,837" size="60,36" zPosition="10" pixmap="buttons/menu.png" transparent="1" alphatest="blend" />
		<ePixmap position="1580,994" size="60,36" zPosition="10" pixmap="buttons/key_epg.png" transparent="1" alphatest="blend" /> 
		<ePixmap pixmap="buttons/key_yellow.png" position="65,786" size="30,30" alphatest="blend" transparent="1" />
		<ePixmap position="48,910" size="60,36" zPosition="10" pixmap="buttons/key_epg.png" transparent="1" alphatest="blend" />
		<panel name="Fullscreen_TopPanel" />
		<panel position="459,147" size="330,57">
			<panel name="Template_Text_Buttons_M_O_E" />
		</panel>
		<panel position="30,147" size="330,57">
			<panel name="TemplateButton_Red_Automatic_all" />
			<panel name="TemplateButton_Green_Automatic_all" />
			<panel name="TemplateButton_Yellow_Automatic_all" />
			<ePixmap pixmap="buttons/key_blue.png" position="930,850" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
			<eLabel text="Help Settings Color" position="965,846" size="255,38" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" halign="left" transparent="1" valign="center" zPosition="10" />
			<widget name="key_blue" position="735,846" size="1,1" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" zPosition="+1" valign="center" halign="left" objectTypes="key_blue,Button,Label" transparent="1" />
			<widget source="key_blue" render="Label" position="735,846" size="1,1" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" zPosition="+1" valign="center" halign="left" objectTypes="key_blue,StaticText" transparent="1" />
		</panel>
	</screen>
    """

    def __init__(self, session, args=0):
        self.session = session
        self.skin_lines = []
        self.changed_screens = False
        Screen.__init__(self, session)

        self.start_skin = config.skin.primary_skin.value

        if self.start_skin != "skin.xml":
            self.getInitConfig()

        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)

        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("OK"))
        self["key_yellow"] = Label()
        self["key_blue"] = Label(_("About"))
        # Dynamic hint texts (DE/EN fallback, no translation files needed)
        self["hint_yellow"] = Label(tr("Press YELLOW to select skinparts", "Gelbe Taste Drücken, um die Skinparts auszuwählen"))
        self["hint_menu_weather"] = Label(tr("Press MENU to configure weather", "Drücken Sie Menü, um das Wetter einzustellen"))
        self["hint_epg_autodb"] = Label(tr(
            "Press EPG to open AutoDB. Press INFO to edit API keys.",
            "Drücken Sie EPG, um AutoDB zu öffnen. INFO öffnet die API-Key-Einstellungen."
        ))
        self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "HelpActions", "InfobarActions", "ChannelSelectEPGActions"],
                {

                        "green": self.keyGreen,
                        "red": self.cancel,
                        "yellow": self.keyYellow,
                        "blue": self.about,
                        "cancel": self.cancel,
                        "ok": self.keyOk,
                        "menu": self.setWeather,
                        "showEPGList": self.openAutoDB,
                        "displayHelp": self.openApiKeys,
                        "showEventInfo": self.openApiKeys,
                        "info": self.openApiKeys,
                                }, -2)

        self["Picture"] = Pixmap()

        if not self.selectionChanged in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.append(self.selectionChanged)

        if self.start_skin != "skin.xml":
            self.createConfigList()

    def setWeather(self):
        try:
            from Plugins.Extensions.OAWeather.plugin import WeatherSettingsView
            self.session.open(WeatherSettingsView)
        except ImportError:
            self.session.open(MessageBox, _("OAWeather is not installed!, please install the OAWeather Plugin"), MessageBox.TYPE_INFO)

    def openAutoDB(self):
        # EPG in this config screen opens integrated AutoDB Manager
        try:
            from .autodb import AutoDBManager
        except Exception as e:
            self.session.open(MessageBox, _('AutoDB module not found: %s') % str(e), MessageBox.TYPE_ERROR)
            return
        self.session.open(AutoDBManager)


    def openApiKeys(self):
        """Open API key setup. Requires api_keys_config.py in the plugin folder."""
        try:
            from .api_keys_config import GradientFHD_APIKeysSetup
        except Exception as e:
            self.session.open(MessageBox, tr(
                'api_keys_config.py not found or import failed: %s' % str(e),
                'api_keys_config.py nicht gefunden oder Import fehlgeschlagen: %s' % str(e)
            ), MessageBox.TYPE_ERROR)
            return
        self.session.open(GradientFHD_APIKeysSetup)


    def openPrimeTime(self):
        try:
            self.session.open(GradientFHD_PrimeTimeSetup)
        except Exception as e:
            self.session.open(MessageBox, tr(
                'PrimeTime setup could not be opened: %s' % str(e),
                'PrimeTime Einstellungen konnten nicht geöffnet werden: %s' % str(e)
            ), MessageBox.TYPE_ERROR)

    def openMovieScanner(self):
        """Open Movie Scanner. Requires GradientMoviescanner.py in plugin folder."""
        try:
            from .GradientMoviescanner import MovieScannerMain
        except Exception as e:
            self.session.open(MessageBox, tr(
                'GradientMoviescanner.py not found: %s' % str(e),
                'GradientMoviescanner.py nicht gefunden: %s' % str(e)
            ), MessageBox.TYPE_ERROR)
            return
        self.session.open(MovieScannerMain)

    
    # ------------------------------
    # PosterX / BackdropX slug export
    # ------------------------------
    def _slugExportStart(self):
        """Start slug export.

        We intentionally run the export in the GUI thread (delayed via eTimer)
        because many Enigma2 images do NOT reliably render a second MessageBox
        when it is triggered from a worker thread. This caused the result box to
        appear only after EXIT.

        By delaying the work ~150ms, the "please wait" box is rendered
        immediately. The export itself is local file IO and completes quickly.
        """
        if getattr(self, '_slug_export_running', False):
            self.session.open(MessageBox, tr(
                'Slug export is already running.',
                'Slug-Export läuft bereits.'
            ), MessageBox.TYPE_INFO, timeout=3)
            return

        self._slug_export_running = True
        self._slug_export_waitbox = None
        self._slug_export_result = None

        # Remember start time (used to keep the wait box visible long enough)
        self._slug_export_started_at = time.time()

        # Open a "please wait" MessageBox immediately.
        try:
            self._slug_export_waitbox = self.session.open(
                MessageBox,
                tr('Slugs are being read... please wait', 'Slugs werden ausgelesen... bitte warten'),
                MessageBox.TYPE_INFO
            )
        except Exception:
            self._slug_export_waitbox = None

        # Run export after a short delay so the waitbox is visible immediately.
        try:
            from enigma import eTimer
            self._slug_export_work_timer = eTimer()
            self._slug_export_work_timer.callback.append(self._slugExportWorkMain)
            self._slug_export_work_timer.start(150, True)
        except Exception:
            # Fallback: run directly
            self._slugExportWorkMain()

    def _slugExportWorkMain(self):
        """Do the slug export work in the GUI thread (called by eTimer)."""
        self._slug_export_result = self._slugExportCollectAndWrite()
        # Continue with the normal "done" flow
        self._slugExportDone()

    def _slugExportCollectAndWrite(self):
        """Collect Title→slug mappings from json/info and logs and write to JSON files.

        Returns: (poster_count, backdrop_count, poster_out, backdrop_out, err)
        """
        poster_items = {}
        backdrop_items = {}
        try:
            base = self._getPosterXBasePath()
            if not base:
                raise Exception('Base path is empty')

            xtra = path.join(base, 'xtra')
            poster_info_dir = path.join(xtra, 'poster_info')
            backdrop_info_dir = path.join(xtra, 'backdrop_info')

            # output files directly in <BASE>/xtra
            poster_out = path.join(xtra, 'PosterX_slugs.json')
            backdrop_out = path.join(xtra, 'BackdropX_slugs.json')

            def _safe_int(v):
                try:
                    return int(v)
                except Exception:
                    return 0

            def _add(target, service, event_ts, title, slug):
                if not slug:
                    return
                if slug not in target:
                    target[slug] = {
                        'service': service or '',
                        'event_ts': _safe_int(event_ts),
                        'title': title or '',
                        'slug': slug,
                    }

            # 1) read <BASE>/xtra/*_info/*.json
            import json
            for info_dir, target in ((poster_info_dir, poster_items), (backdrop_info_dir, backdrop_items)):
                if path.isdir(info_dir):
                    for fn in sorted(listdir(info_dir)):
                        if not fn.endswith('.json'):
                            continue
                        fp = path.join(info_dir, fn)
                        try:
                            with open(fp, 'r') as f:
                                data = json.load(f)
                            _add(target, data.get('service', ''), data.get('event_ts', 0), data.get('title', ''), data.get('slug', ''))
                        except Exception:
                            continue

            # 2) parse AutoDB logs (queue lines)
            def _parse_autodb_log(logfile, target):
                if not path.exists(logfile):
                    return
                try:
                    import re
                    rx = re.compile(r"\[QUEUE\]\s*:\s*(?P<service>.+?)\s*:\s*(?P<ts>\d+)-(?P<title>.+?)\s*\((?P<slug>[^)]+)\)")
                    with open(logfile, 'r') as f:
                        for line in f:
                            m = rx.search(line)
                            if not m:
                                continue
                            _add(target, m.group('service').strip(), m.group('ts'), m.group('title').strip(), m.group('slug').strip())
                except Exception:
                    return

            _parse_autodb_log('/var/volatile/tmp/PosterAutoDB.log', poster_items)
            _parse_autodb_log('/var/volatile/tmp/BackdropAutoDB.log', backdrop_items)

            poster_list = sorted(poster_items.values(), key=lambda x: (x.get('title', '').lower(), x.get('slug', '')))
            backdrop_list = sorted(backdrop_items.values(), key=lambda x: (x.get('title', '').lower(), x.get('slug', '')))

            poster_count = len(poster_list)
            backdrop_count = len(backdrop_list)

            if not path.isdir(xtra):
                try:
                    makedirs(xtra)
                except Exception:
                    pass

            with open(poster_out, 'w') as f:
                json.dump(poster_list, f, indent=2, ensure_ascii=False)
            with open(backdrop_out, 'w') as f:
                json.dump(backdrop_list, f, indent=2, ensure_ascii=False)

            return (poster_count, backdrop_count, poster_out, backdrop_out, None)
        except Exception as e:
            return (0, 0, '', '', str(e))

    def _slugExportDone(self):
        """GUI thread callback after slug export finished.

        Important:
        - On many Enigma2 images, opening another MessageBox *immediately* after closing
          a previous one can result in the next box not being rendered at all.
        - Also, some platforms treat timeout=0 as "close immediately".

        Therefore we:
          1) Keep the "please wait" box visible at least ~0.8s
          2) Close it
          3) Schedule the result MessageBox a few ms later on the GUI loop.
        """

        # prevent double-firing
        if getattr(self, '_slug_export_done_scheduled', False):
            return
        self._slug_export_done_scheduled = True

        try:
            started = float(getattr(self, '_slug_export_started_at', 0.0) or 0.0)
        except Exception:
            started = 0.0

        try:
            elapsed = time.time() - started
        except Exception:
            elapsed = 0.0

        # ensure minimum visibility for the waitbox
        delay_ms = 0
        if elapsed < 0.8:
            delay_ms = int((0.8 - elapsed) * 1000)

        try:
            from enigma import eTimer
            self._slug_export_timer = eTimer()
            self._slug_export_timer.callback.append(self._slugExportShowResult)
            self._slug_export_timer.start(max(0, delay_ms), True)
        except Exception:
            # fallback: show immediately
            self._slugExportShowResult()


    def _slugExportShowResult(self):
        """Close waitbox and show the result popup (GUI thread)."""
        try:
            # Close the wait popup first.
            # NOTE: On many Enigma2 images it is unreliable to open a new MessageBox
            # immediately after closing the previous one. Therefore we close the
            # waitbox now and schedule the result box a little later via eTimer.
            if getattr(self, '_slug_export_waitbox', None) is not None:
                try:
                    self._slug_export_waitbox.close()
                except Exception:
                    pass

            poster_count, backdrop_count, poster_out, backdrop_out, err = self._slug_export_result or (0, 0, '', '', 'Unknown')

            if err:
                self._slug_export_msg = tr(
                    'Slug export failed: %s' % err,
                    'Slug-Export fehlgeschlagen: %s' % err
                )
                self._slug_export_msg_type = MessageBox.TYPE_ERROR
                self._slug_export_msg_timeout = 8
            else:
                self._slug_export_msg = tr(
                    'Slug export finished!\n\nPoster: %d\nBackdrop: %d\n\nSaved to:\n%s\n%s' % (poster_count, backdrop_count, poster_out, backdrop_out),
                    'Slug-Export fertig!\n\nPoster: %d\nBackdrop: %d\n\nGespeichert in:\n%s\n%s' % (poster_count, backdrop_count, poster_out, backdrop_out)
                )
                self._slug_export_msg_type = MessageBox.TYPE_INFO
                self._slug_export_msg_timeout = 10

            # Schedule result messagebox slightly later to avoid "only after EXIT".
            try:
                from enigma import eTimer
                self._slug_export_result_timer = eTimer()
                self._slug_export_result_timer.callback.append(self._slugExportOpenResultBox)
                self._slug_export_result_timer.start(250, True)
            except Exception:
                # fallback: open directly
                self._slugExportOpenResultBox()
        finally:
            self._slug_export_running = False
            self._slug_export_waitbox = None
            self._slug_export_timer = None
            self._slug_export_started_at = 0.0
            self._slug_export_done_scheduled = False


    def _slugExportOpenResultBox(self):
        """Open the final result messagebox (GUI thread)."""
        try:
            msg = getattr(self, '_slug_export_msg', None)
            if not msg:
                return
            mtype = getattr(self, '_slug_export_msg_type', MessageBox.TYPE_INFO)
            tout = getattr(self, '_slug_export_msg_timeout', 8)
            # Use session.open to keep the user in the plugin menu.
            self.session.open(MessageBox, msg, mtype, timeout=tout)
        except Exception:
            pass
        finally:
            self._slug_export_msg = None
            self._slug_export_msg_type = None
            self._slug_export_msg_timeout = None
            self._slug_export_result_timer = None


    def getInitConfig(self):

        global cur_skin
        self.is_atile = False
        if cur_skin == 'AtileHD':
            self.is_atile = True

        self.title = _("GradientFHD Setup")
        self.skin_base_dir = "/usr/share/enigma2/%s/" % cur_skin

        self.default_font_file = "font_atile_Roboto.xml"
        self.default_background_color_skin_file = "background_color_skin_Original.xml"
        self.default_event_name_color_file = "event_name_color_Original.xml"

        self.default_event_time_color_file = "event_time_color_Original.xml"
        self.default_foreground_color_channel_file = "foreground_color_channel_Original.xml"
        self.default_foreground_color_channel_selected_file = "foreground_color_channel_selected_Original.xml"
        self.default_foreground_color_event_file = "foreground_color_event_Original.xml"
        self.default_foreground_color_event_selected_file = "foreground_color_event_selected_Original.xml"
        self.default_weather_file = "weather_Original.xml"
        self.default_progressbar_color_skin_file = "progressbar_color_skin_Original.xml"
        self.default_background_color_channel_selected_file = "background_color_channel_selected_Original.xml"
        self.default_softcam_file = "softcam_Original.xml"
        self.default_weather_design_file = "weather_design_Original.xml"
        self.default_poster_infobar_file = "poster_infobar_Original.xml"
        self.default_poster_epg_file = "poster_epg_Original.xml"
        self.default_poster_movie_list_file = "poster_movie_list_Original.xml"
        self.default_pppppp_file = "pppppp_Original.xml"

        self.event_name_color_file = "skin_user_event_name_color.xml"
        self.event_time_color_file = "skin_user_event_time_color.xml"
        self.foreground_color_channel_file = "skin_user_foreground_color_channel.xml"
        self.foreground_color_channel_selected_file = "skin_user_foreground_color_channel_selected.xml"
        self.foreground_color_event_file = "skin_user_foreground_color_event.xml"
        self.foreground_color_event_selected_file = "skin_user_foreground_color_event_selected.xml"
        self.weather_file = "skin_user_weather.xml"
        self.progressbar_color_skin_file = "skin_user_progressbar_color_skin.xml"
        self.background_color_channel_selected_file = "skin_user_background_color_channel_selected.xml"
        self.softcam_file = "skin_user_softcam.xml"
        self.weather_design_file = "skin_user_weather_design.xml"
        self.background_color_skin_file = "skin_user_background_color_skin.xml"
        self.poster_infobar_file = "skin_user_poster_infobar.xml"
        self.poster_epg_file = "skin_user_poster_epg.xml"
        self.poster_movie_list_file = "skin_user_poster_movie_list.xml"
        self.pppppp_file = "skin_user_pppppp.xml"

        # event_name_color
        current, choices = self.getSettings(self.default_event_name_color_file, self.event_name_color_file)
        self.myAtileHD_event_name_color = NoSave(ConfigSelection(default=current, choices=choices))
        # event_time_color
        current, choices = self.getSettings(self.default_event_time_color_file, self.event_time_color_file)
        self.myAtileHD_event_time_color = NoSave(ConfigSelection(default=current, choices=choices))
        # foreground_color_channel
        current, choices = self.getSettings(self.default_foreground_color_channel_file, self.foreground_color_channel_file)
        self.myAtileHD_foreground_color_channel = NoSave(ConfigSelection(default=current, choices=choices))
        # foreground_color_channel_selected
        current, choices = self.getSettings(self.default_foreground_color_channel_selected_file, self.foreground_color_channel_selected_file)
        self.myAtileHD_foreground_color_channel_selected = NoSave(ConfigSelection(default=current, choices=choices))
        # foreground_color_event
        current, choices = self.getSettings(self.default_foreground_color_event_file, self.foreground_color_event_file)
        self.myAtileHD_foreground_color_event = NoSave(ConfigSelection(default=current, choices=choices))
        # foreground_color_event
        current, choices = self.getSettings(self.default_foreground_color_event_selected_file, self.foreground_color_event_selected_file)
        self.myAtileHD_foreground_color_event_selected = NoSave(ConfigSelection(default=current, choices=choices))
        # weather
        current, choices = self.getSettings(self.default_weather_file, self.weather_file)
        self.myAtileHD_weather = NoSave(ConfigSelection(default=current, choices=choices))
        # progressbar_color_skin
        current, choices = self.getSettings(self.default_progressbar_color_skin_file, self.progressbar_color_skin_file)
        self.myAtileHD_progressbar_color_skin = NoSave(ConfigSelection(default=current, choices=choices))
        # background_color_channel_selected
        current, choices = self.getSettings(self.default_background_color_channel_selected_file, self.background_color_channel_selected_file)
        self.myAtileHD_background_color_channel_selected = NoSave(ConfigSelection(default=current, choices=choices))
        # softcam
        current, choices = self.getSettings(self.default_softcam_file, self.softcam_file)
        self.myAtileHD_softcam = NoSave(ConfigSelection(default=current, choices=choices))
        # weather_design
        current, choices = self.getSettings(self.default_weather_design_file, self.weather_design_file)
        self.myAtileHD_weather_design = NoSave(ConfigSelection(default=current, choices=choices))
        # poster_infobar
        current, choices = self.getSettings(self.default_poster_infobar_file, self.poster_infobar_file)
        self.myAtileHD_poster_infobar = NoSave(ConfigSelection(default=current, choices=choices))
        # background_color_skin
        current, choices = self.getSettings(self.default_background_color_skin_file, self.background_color_skin_file)
        self.myAtileHD_background_color_skin = NoSave(ConfigSelection(default=current, choices=choices))
        # poster_epg
        current, choices = self.getSettings(self.default_poster_epg_file, self.poster_epg_file)
        self.myAtileHD_poster_epg = NoSave(ConfigSelection(default=current, choices=choices))
        # poster_movie_list
        current, choices = self.getSettings(self.default_poster_movie_list_file, self.poster_movie_list_file)
        self.myAtileHD_poster_movie_list = NoSave(ConfigSelection(default=current, choices=choices))
        # pppppp
        current, choices = self.getSettings(self.default_pppppp_file, self.pppppp_file)
        self.myAtileHD_pppppp = NoSave(ConfigSelection(default=current, choices=choices))
        # myatile
        myatile_active = self.getmyAtileState()
        self.myAtileHD_active = NoSave(ConfigYesNo(default=myatile_active))
        self.myAtileHD_fake_entry = NoSave(ConfigNothing())

    def getSettings(self, default_file, user_file):
        # default setting
        default = ("default", _("Default"))

        # search typ
        styp = default_file.replace('_Original.xml', '')
        if self.is_atile:
            search_str = '%s_atile_' % styp
        else:
            search_str = '%s_' % styp

        # possible setting
        choices = []
        files = listdir(self.skin_base_dir)
        if path.exists(self.skin_base_dir + 'allScreens/%s/' % styp):
            files += listdir(self.skin_base_dir + 'allScreens/%s/' % styp)
        for f in sorted(files, key=str.lower):
            if f.endswith('.xml') and f.startswith(search_str):
                friendly_name = f.replace(search_str, "").replace(".xml", "").replace("_", " ")
                if path.exists(self.skin_base_dir + 'allScreens/%s/%s' % (styp, f)):
                    choices.append((self.skin_base_dir + 'allScreens/%s/%s' % (styp, f), friendly_name))
                else:
                    choices.append((self.skin_base_dir + f, friendly_name))
        choices.append(default)

        # current setting
        myfile = self.skin_base_dir + "mySkin_off/" + user_file
        current = ''
        if not path.exists(myfile):
            if path.exists(self.skin_base_dir + default_file):
                if path.islink(myfile):
                    remove(myfile)
                chdir(self.skin_base_dir)
                symlink(default_file, user_file)
            elif path.exists(self.skin_base_dir + 'allScreens/%s/%s' % (styp, default_file)):
                if path.islink(myfile):
                    remove(myfile)
                chdir(self.skin_base_dir)
                symlink(self.skin_base_dir + 'allScreens/%s/%s' % (styp, default_file), user_file)
            else:
                current = None
        if current is None:
            current = default
        else:
            filename = path.realpath(myfile)
            friendly_name = path.basename(filename).replace(search_str, "").replace(".xml", "").replace("_", " ")
            current = (filename, friendly_name)

        return current[0], choices

    def createConfigList(self):
        self.set_event_name_color = getConfigListEntry(_("EventName Color:"), self.myAtileHD_event_name_color)
        self.set_event_time_color = getConfigListEntry(_("EventTime Color:"), self.myAtileHD_event_time_color)
        self.set_foreground_color_channel = getConfigListEntry(_("ForegroundColor Channel:"), self.myAtileHD_foreground_color_channel)
        self.set_foreground_color_channel_selected = getConfigListEntry(_("ForegroundColor ChannelSelected:"), self.myAtileHD_foreground_color_channel_selected)
        self.set_poster_movie_list = getConfigListEntry(_("Poster Movie/EMC List:"), self.myAtileHD_poster_movie_list)
        self.set_pppppp = getConfigListEntry(_("bla:"), self.myAtileHD_pppppp)
        self.set_background_color_skin = getConfigListEntry(_("BackgroundColor Skin:"), self.myAtileHD_background_color_skin)
        self.set_foreground_color_event = getConfigListEntry(_("ForegroundColor Event:"), self.myAtileHD_foreground_color_event)
        self.set_foreground_color_event_selected = getConfigListEntry(_("ForegroundColor EventSelected:"), self.myAtileHD_foreground_color_event_selected)
        self.set_weather = getConfigListEntry(_("Weather Infobar:"), self.myAtileHD_weather)
        self.set_progressbar_color_skin = getConfigListEntry(_("ProgressbarColor Skin:"), self.myAtileHD_progressbar_color_skin)
        self.set_background_color_channel_selected = getConfigListEntry(_("BackgroundColor ChannelSelected:"), self.myAtileHD_background_color_channel_selected)
        self.set_softcam = getConfigListEntry(_("Softcamdetails:"), self.myAtileHD_softcam)
        self.set_weather_design = getConfigListEntry(_("Weather Infobar Design:"), self.myAtileHD_weather_design)
        self.set_poster_infobar = getConfigListEntry(_("Poster Infobar:"), self.myAtileHD_poster_infobar)
        self.set_poster_epg = getConfigListEntry(_("Poster EPG:"), self.myAtileHD_poster_epg)
        self.set_myatile = getConfigListEntry(_("Enable %s Extentions:") % cur_skin, self.myAtileHD_active)
        self.find_woeid = getConfigListEntry(_("Search weather location ID"), ConfigNothing())
        self.api_keys_setup = getConfigListEntry(tr("API Keys setup", "API-Keys einstellen"), ConfigNothing())
        self.primetime_setup = getConfigListEntry(tr('PrimeTime setup', 'PrimeTime einstellen'), ConfigNothing())
        self.posterx_path_setup = getConfigListEntry(tr('PosterX storage path', 'PosterX Speicherpfad auswählen'), config.plugins.GradientFHD.posterXPath)
        self.posterx_show_slugs_setup = getConfigListEntry(
            tr('PosterX/BackdropX Export slugs', 'PosterX/BackdropX Slugs auslesen'),
            ConfigNothing()
        )
        self.moviescanner_setup = getConfigListEntry(tr("Movie Scanner", "MovieScanner"), ConfigNothing())
        self.list = []
        self.list.append(self.set_myatile)
        if self.myAtileHD_active.value:
            if len(self.myAtileHD_background_color_skin.choices) > 1:
                self.list.append(self.set_background_color_skin)
            if len(self.myAtileHD_progressbar_color_skin.choices) > 1:
                self.list.append(self.set_progressbar_color_skin)
            if len(self.myAtileHD_foreground_color_channel.choices) > 1:
                self.list.append(self.set_foreground_color_channel)
            if len(self.myAtileHD_foreground_color_channel_selected.choices) > 1:
                self.list.append(self.set_foreground_color_channel_selected)
            if len(self.myAtileHD_foreground_color_event.choices) > 1:
                self.list.append(self.set_foreground_color_event)
            if len(self.myAtileHD_foreground_color_event_selected.choices) > 1:
                self.list.append(self.set_foreground_color_event_selected)
            if len(self.myAtileHD_background_color_channel_selected.choices) > 1:
                self.list.append(self.set_background_color_channel_selected)
            if len(self.myAtileHD_event_time_color.choices) > 1:
                self.list.append(self.set_event_time_color)
            if len(self.myAtileHD_event_name_color.choices) > 1:
                self.list.append(self.set_event_name_color)
            if len(self.myAtileHD_softcam.choices) > 1:
                self.list.append(self.set_softcam)
            if len(self.myAtileHD_weather.choices) > 1:
                self.list.append(self.set_weather)
            if len(self.myAtileHD_weather_design.choices) > 1:
                self.list.append(self.set_weather_design)
            if len(self.myAtileHD_poster_movie_list.choices) > 1:
                self.list.append(self.set_poster_movie_list)
            if len(self.myAtileHD_pppppp.choices) > 1:
                self.list.append(self.set_pppppp)

            if len(self.myAtileHD_poster_epg.choices) > 1:
                self.list.append(self.set_poster_epg)
            if len(self.myAtileHD_poster_infobar.choices) > 1:
                self.list.append(self.set_poster_infobar)

        # API key setup entry
        self.list.append(self.api_keys_setup)

        # PrimeTime setup entry
        self.list.append(self.primetime_setup)

        # PosterX storage path (base for /xtra folder)
        # (append only once)
        self.list.append(self.posterx_path_setup)

        # PosterX slug viewer
        self.list.append(self.posterx_show_slugs_setup)

        # Movie Scanner
        self.list.append(self.moviescanner_setup)

        self["config"].list = self.list
        self["config"].l.setList(self.list)
        if self.myAtileHD_active.value:
            self["key_yellow"].setText("%s Config" % cur_skin)
        else:
            self["key_yellow"].setText("")

    def changedEntry(self):
        if self["config"].getCurrent() == self.set_background_color_skin:
            self.setPicture(self.myAtileHD_background_color_skin.value)
        elif self["config"].getCurrent() == self.set_event_name_color:
            self.setPicture(self.myAtileHD_event_name_color.value)
        elif self["config"].getCurrent() == self.set_event_time_color:
            self.setPicture(self.myAtileHD_event_time_color.value)
        elif self["config"].getCurrent() == self.set_foreground_color_channel:
            self.setPicture(self.myAtileHD_foreground_color_channel.value)
        elif self["config"].getCurrent() == self.set_foreground_color_channel_selected:
            self.setPicture(self.myAtileHD_foreground_color_channel_selected.value)
        elif self["config"].getCurrent() == self.set_foreground_color_event:
            self.setPicture(self.myAtileHD_foreground_color_event.value)
        elif self["config"].getCurrent() == self.set_foreground_color_event_selected:
            self.setPicture(self.myAtileHD_foreground_color_event_selected.value)
        elif self["config"].getCurrent() == self.set_weather:
            self.setPicture(self.myAtileHD_weather.value)
        elif self["config"].getCurrent() == self.set_progressbar_color_skin:
            self.setPicture(self.myAtileHD_progressbar_color_skin.value)
        elif self["config"].getCurrent() == self.set_background_color_channel_selected:
            self.setPicture(self.myAtileHD_background_color_channel_selected.value)
        elif self["config"].getCurrent() == self.set_softcam:
            self.setPicture(self.myAtileHD_softcam.value)
        elif self["config"].getCurrent() == self.set_weather_design:
            self.setPicture(self.myAtileHD_weather_design.value)
        elif self["config"].getCurrent() == self.set_poster_infobar:
            self.setPicture(self.myAtileHD_poster_infobar.value)
        elif self["config"].getCurrent() == self.set_poster_epg:
            self.setPicture(self.myAtileHD_poster_epg.value)
        elif self["config"].getCurrent() == self.set_poster_movie_list:
            self.setPicture(self.myAtileHD_poster_movie_list.value)
        elif self["config"].getCurrent() == self.set_pppppp:
            self.setPicture(self.myAtileHD_pppppp.value)
        elif self["config"].getCurrent() == self.set_myatile:
            if self.myAtileHD_active.value:
                self["key_yellow"].setText("%s Config" % cur_skin)
            else:
                self["key_yellow"].setText("")
            self.createConfigList()

    def selectionChanged(self):
        if self["config"].getCurrent() == self.set_background_color_skin:
            self.setPicture(self.myAtileHD_background_color_skin.value)
        elif self["config"].getCurrent() == self.set_event_name_color:
            self.setPicture(self.myAtileHD_event_name_color.value)
        elif self["config"].getCurrent() == self.set_event_time_color:
            self.setPicture(self.myAtileHD_event_time_color.value)
        elif self["config"].getCurrent() == self.set_foreground_color_channel:
            self.setPicture(self.myAtileHD_foreground_color_channel.value)
        elif self["config"].getCurrent() == self.set_foreground_color_channel_selected:
            self.setPicture(self.myAtileHD_foreground_color_channel_selected.value)
        elif self["config"].getCurrent() == self.set_foreground_color_event:
            self.setPicture(self.myAtileHD_foreground_color_event.value)
        elif self["config"].getCurrent() == self.set_foreground_color_event_selected:
            self.setPicture(self.myAtileHD_foreground_color_event_selected.value)
        elif self["config"].getCurrent() == self.set_weather:
            self.setPicture(self.myAtileHD_weather.value)
        elif self["config"].getCurrent() == self.set_progressbar_color_skin:
            self.setPicture(self.myAtileHD_progressbar_color_skin.value)
        elif self["config"].getCurrent() == self.set_background_color_channel_selected:
            self.setPicture(self.myAtileHD_background_color_channel_selected.value)
        elif self["config"].getCurrent() == self.set_softcam:
            self.setPicture(self.myAtileHD_softcam.value)
        elif self["config"].getCurrent() == self.set_weather_design:
            self.setPicture(self.myAtileHD_weather_design.value)
        elif self["config"].getCurrent() == self.set_poster_infobar:
            self.setPicture(self.myAtileHD_poster_infobar.value)
        elif self["config"].getCurrent() == self.set_poster_epg:
            self.setPicture(self.myAtileHD_poster_epg.value)
        elif self["config"].getCurrent() == self.set_poster_movie_list:
            self.setPicture(self.myAtileHD_poster_movie_list.value)
        elif self["config"].getCurrent() == self.set_pppppp:
            self.setPicture(self.myAtileHD_pppppp.value)
        elif self["config"].getCurrent() == self.api_keys_setup:
            self.setMenuPicture("api_keys")
        elif self["config"].getCurrent() == self.primetime_setup:
            self.setMenuPicture("primetime")
        elif self["config"].getCurrent() == self.posterx_path_setup:
            self.setMenuPicture("posterx_path")
        elif self["config"].getCurrent() == self.posterx_show_slugs_setup:
            self.setMenuPicture("slug_export")
        elif self["config"].getCurrent() == self.moviescanner_setup:
            self.setMenuPicture("moviescanner")
        else:
            self["Picture"].hide()

    def cancel(self):
        if self["config"].isChanged():
            self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"), MessageBox.TYPE_YESNO, default=False)
        else:
            for x in self["config"].list:
                x[1].cancel()
            if self.changed_screens:
                self.restartGUI()
            else:
                self.close()

    def cancelConfirm(self, result):
        if result is None or result is False:
            print("[%s]: Cancel confirmed." % cur_skin)
        else:
            print("[%s]: Cancel confirmed. Config changes will be lost." % cur_skin)
            for x in self["config"].list:
                x[1].cancel()
            self.close()

    def getmyAtileState(self):
        chdir(self.skin_base_dir)
        if path.exists("mySkin"):
            return True
        else:
            return False

    def setPicture(self, f):
        pic = f.split('/')[-1].replace(".xml", ".png")
        preview = self.skin_base_dir + "preview/preview_" + pic
        if path.exists(preview):
            self["Picture"].instance.setPixmapFromFile(preview)
            self["Picture"].show()
        else:
            self["Picture"].hide()

    def setMenuPicture(self, key):
        # Menu previews use the same preview folder as skin previews:
        #   <skin_base_dir>/preview/preview_menu_<key>.png
        preview = self.skin_base_dir + "preview/preview_menu_%s.png" % key
        try:
            if path.exists(preview):
                self["Picture"].instance.setPixmapFromFile(preview)
                self["Picture"].show()
            else:
                self["Picture"].hide()
        except Exception as e:
            print("[%s] Preview error: %s" % (cur_skin, e))

    def keyYellow(self):
        if self.myAtileHD_active.value:
            self.session.openWithCallback(self.GradientFHDScreenCB, GradientFHDScreens)
        else:
            self["config"].setCurrentIndex(0)

    def keyOk(self):
        sel = self["config"].getCurrent()
        if sel is not None and sel == self.find_woeid:
            self.session.openWithCallback(self.search_weather_id_callback, InputBox, title=_("Please enter search string for your location"), text="")
        elif sel is not None and sel == self.api_keys_setup:
            self.openApiKeys()
        elif sel is not None and sel == self.primetime_setup:
            self.openPrimeTime()
        elif sel is not None and sel == self.posterx_show_slugs_setup:
            self._slugExportStart()
        elif sel is not None and sel == self.moviescanner_setup:
            self.openMovieScanner()
        else:
            self.keyGreen()

    def search_weather_id_callback(self, res):
        if res:
            id_dic = get_woeid_from_yahoo(res)
            if 'error' in id_dic:
                error_txt = id_dic['error']
                self.session.open(MessageBox, _("Sorry, there was a problem:") + "\n%s" % error_txt, MessageBox.TYPE_ERROR)
            elif 'count' in id_dic:
                result_no = int(id_dic['count'])
                location_list = []
                for i in range(0, result_no):
                    location_list.append(id_dic[i])
                self.session.openWithCallback(self.select_weather_id_callback, WeatherLocationChoiceList, location_list)

    def select_weather_id_callback(self, res):
        if res and isInteger(res):
            print(res)
            config.plugins.GradientFHD.woeid.value = int(res)

    def skinChanged(self, ret=None):
        global cur_skin
        cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')
        if cur_skin == "skin.xml":
            self.restartGUI()
        else:
            self.getInitConfig()
            self.createConfigList()

    # -------------------------------------------------------------
    # PosterX storage handling
    # -------------------------------------------------------------
    def _isWritablePath(self, base_path):
        """Return True if base_path exists and we can create a folder inside."""
        try:
            if not base_path or not path.exists(base_path):
                return False
            test_dir = path.join(base_path, "xtra", ".rw_test")
            # try to create + remove a directory (no file I/O needed)
            makedirs(test_dir, exist_ok=True)
            shutil.rmtree(test_dir, ignore_errors=True)
            return True
        except Exception:
            return False

    def _getPosterXBasePath(self):
        """Return selected base path for /xtra. Falls back to auto detection."""
        try:
            sel = getattr(config.plugins.GradientFHD, "posterXPath", None)
            if sel is not None and sel.value and sel.value != "AUTO":
                return sel.value
        except Exception:
            pass

        # AUTO: prefer HDD -> USB -> MMC -> NAS
        for p in ("/media/hdd", "/media/usb", "/media/mmc", "/media/net"):
            if self._isWritablePath(p):
                return p
        # last resort
        return "/media/hdd"

    def _ensurePosterXTree(self, base_path):
        """Create the whole /xtra folder tree including custom poster/backdrop."""
        xtra = path.join(base_path, "xtra")
        folders = [
            xtra,
            path.join(xtra, "backdrop"),
            path.join(xtra, "backdrop_info"),
            path.join(xtra, "Info"),
            path.join(xtra, "poster"),
            path.join(xtra, "poster_info"),
            path.join(xtra, "custom"),
            path.join(xtra, "custom", "poster"),
            path.join(xtra, "custom", "backdrop"),
        ]
        for f in folders:
            makedirs(f, exist_ok=True)

    def keyGreen(self):
        if self["config"].isChanged():
            for x in self["config"].list:
                x[1].save()

            # Ensure PosterX storage tree exists (including custom folders)
            try:
                base = self._getPosterXBasePath()
                self._ensurePosterXTree(base)
                AddPopup(tr(
                    "PosterX storage path saved. Folders created.",
                    "PosterX Speicherpfad gespeichert. Ordner wurden angelegt."
                ), type=MessageBox.TYPE_INFO, timeout=5)
            except Exception as e:
                # Do not crash the setup if folder creation fails
                AddPopup(tr(
                    "PosterX: could not create folders: %s" % str(e),
                    "PosterX: Ordner konnten nicht angelegt werden: %s" % str(e)
                ), type=MessageBox.TYPE_ERROR, timeout=7)
            chdir(self.skin_base_dir)

            # event_name_color
            self.makeSettings(self.myAtileHD_event_name_color, self.event_name_color_file)
            # event_time_color
            self.makeSettings(self.myAtileHD_event_time_color, self.event_time_color_file)
            # foreground_color_channel
            self.makeSettings(self.myAtileHD_foreground_color_channel, self.foreground_color_channel_file)
            # foreground_color_channel_selected
            self.makeSettings(self.myAtileHD_foreground_color_channel_selected, self.foreground_color_channel_selected_file)
            # foreground_color_event
            self.makeSettings(self.myAtileHD_foreground_color_event, self.foreground_color_event_file)
            # foreground_color_event
            self.makeSettings(self.myAtileHD_foreground_color_event_selected, self.foreground_color_event_selected_file)
            # weather
            self.makeSettings(self.myAtileHD_weather, self.weather_file)
            # progressbar_color_skin
            self.makeSettings(self.myAtileHD_progressbar_color_skin, self.progressbar_color_skin_file)
            # background_color_channel_selected
            self.makeSettings(self.myAtileHD_background_color_channel_selected, self.background_color_channel_selected_file)
            # softcam
            self.makeSettings(self.myAtileHD_softcam, self.softcam_file)
            # weather_design
            self.makeSettings(self.myAtileHD_weather_design, self.weather_design_file)
            # poster_infobar
            self.makeSettings(self.myAtileHD_poster_infobar, self.poster_infobar_file)
            # poster_epg
            self.makeSettings(self.myAtileHD_poster_epg, self.poster_epg_file)
            # background_color_skin
            self.makeSettings(self.myAtileHD_background_color_skin, self.background_color_skin_file)
            # poster_movie_list
            self.makeSettings(self.myAtileHD_poster_movie_list, self.poster_movie_list_file)
            # pppppp
            self.makeSettings(self.myAtileHD_pppppp, self.pppppp_file)

            if not path.exists("mySkin_off"):
                mkdir("mySkin_off")
                print("makedir mySkin_off")
            if self.myAtileHD_active.value:
                if not path.exists("mySkin") and path.exists("mySkin_off"):
                    symlink("mySkin_off", "mySkin")
            else:
                if path.exists("mySkin"):
                    if path.exists("mySkin_off"):
                        if path.islink("mySkin"):
                            remove("mySkin")
                        else:
                            shutil.rmtree("mySkin")
                    else:
                        rename("mySkin", "mySkin_off")
            self.restartGUI()
        elif config.skin.primary_skin.value != self.start_skin:
            self.restartGUI()
        else:
            if self.changed_screens:
                self.restartGUI()
            else:
                self.close()

    def makeSettings(self, config_entry, user_file):
        if path.exists("mySkin_off/" + user_file) or path.islink("mySkin_off/" + user_file):
            remove("mySkin_off/" + user_file)
        if config_entry.value != 'default':
            symlink(config_entry.value, "mySkin_off/" + user_file)

    def GradientFHDScreenCB(self):
        self.changed_screens = True
        self["config"].setCurrentIndex(0)

    def restartGUI(self):
        restartbox = self.session.openWithCallback(self.restartGUIcb, MessageBox, _("Restart necessary, restart GUI now?"), MessageBox.TYPE_YESNO)
        restartbox.setTitle(_("Message"))

    def about(self):
        self.session.open(GradientFHD_About)

    def restartGUIcb(self, answer):
        if answer is True:
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close()


class GradientFHD_PrimeTimeSetup(Screen, ConfigListScreen):

    skin = """
    <screen name="GradientFHD_PrimeTimeSetup" position="center,center" size="1280,460" title="PrimeTime Settings" flags="wfNoBorder" backgroundColor="transparent">
        <widget source="Title" render="Label" position="20,0" size="1060,60" font="Italic; 42" halign="left" valign="center" transparent="1" foregroundColor="gradient_foreground_selection" backgroundColor="background" textBorderColor="black" textBorderWidth="1" zPosition="1" />
        <widget name="config" position="20,80" size="1240,315" font="Regular;30" scrollbarMode="showOnDemand" itemHeight="45" transparent="1" />
        <eLabel name="menu_bg" position="0,60" size="1280,400" backgroundColor="gradient_BGO,gradient_BGM,gradient_BGU,vertical" zPosition="-8" />
        <eLabel name="title_bg" position="0,0" size="1280,70" backgroundColor="gradient_TBGL,gradient_BGO,gradient_BGU,horizontal" zPosition="-9" cornerRadius="12" />
        <eLabel name="title_line" position="0,60" size="1280,4" backgroundColor="gradient_background,gradient_BGLR,gradient_BGLM,horizontal" zPosition="10" />
        <eLabel name="Line_Menu" position="15,400" size="1250,2" backgroundColor="gradient_BGLR,gradient_BGLM,gradient_BGLR,horizontal" zPosition="10" />
        <ePixmap pixmap="buttons/key_red.png" position="20,415" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_green.png" position="260,415" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_yellow.png" position="500,415" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_blue.png" position="850,415" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <widget name="key_red" position="60,410" size="200,40" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" valign="center" halign="left" transparent="1" />
        <widget name="key_green" position="300,410" size="200,40" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" valign="center" halign="left" transparent="1" />
        <widget name="key_yellow" position="540,410" size="310,40" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" valign="center" halign="left" transparent="1" />
        <widget name="key_blue" position="890,410" size="200,40" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" valign="center" halign="left" transparent="1" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        self["key_red"] = Label(tr("Cancel", "Abbrechen"))
        self["key_green"] = Label(tr("OK / Save", "OK / Speichern"))
        self["key_yellow"] = Label(tr("Default 20:15", "Standard 20:15"))
        self["key_blue"] = Label(tr("Close", "Schließen"))

        self.list = []
        ConfigListScreen.__init__(self, self.list, session=session)

        self.list.append(getConfigListEntry(tr("Primetime: Hour", "Primetime: Stunde"), config.plugins.GradientFHD.primeTimeHour))
        self.list.append(getConfigListEntry(tr("Primetime: Minutes", "Primetime: Minuten"), config.plugins.GradientFHD.primeTimeMinute))

        self["config"].list = self.list
        self["config"].l.setList(self.list)

        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions"],
            {
                "red": self.cancel,
                "cancel": self.cancel,

                "green": self.save,
                "ok": self.save,

                "yellow": self.setDefault,
                "blue": self.close,
            },
            -2
        )

    def setDefault(self):
        config.plugins.GradientFHD.primeTimeHour.value = "20"
        config.plugins.GradientFHD.primeTimeMinute.value = "15"
        self["config"].l.setList(self.list)

        # 3 Sekunden Info anzeigen (ohne Schließen)
        msg = tr("PrimeTime set to default:", "PrimeTime auf Standard gesetzt:") + " 20:15"
        self.session.open(
            MessageBox,
            msg,
            MessageBox.TYPE_INFO,
            timeout=3
        )

    def save(self):
        # Werte speichern
        for x in self["config"].list:
            x[1].save()
        configfile.save()

        # PrimeTime Text bauen (schön formatiert)
        try:
            h = int(config.plugins.GradientFHD.primeTimeHour.value)
            m = int(config.plugins.GradientFHD.primeTimeMinute.value)
            primetime_str = "%02d:%02d" % (h, m)
        except Exception:
            primetime_str = "?"

        msg = tr("PrimeTime saved:", "PrimeTime gespeichert:") + " " + primetime_str

        # 3 Sekunden Message anzeigen -> danach Screen schließen
        self.session.openWithCallback(
            lambda *ret: self.close(),
            MessageBox,
            msg,
            MessageBox.TYPE_INFO,
            timeout=3
        )

    def cancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()


class GradientFHD_About(Screen):

    def __init__(self, session, args=0):
        self.session = session
        Screen.__init__(self, session)
        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
                {
                        "cancel": self.cancel,
                        "ok": self.keyOk,
                }, -2)

    def keyOk(self):
        self.close()

    def cancel(self):
        self.close()


class GradientFHDScreens(Screen):

    skin = """
	<screen name="GradientFHDScreens" position="center,center" size="1920,1080" title="GradientFHD Setup" flags="wfNoBorder" backgroundColor="transparent">
		<eLabel text="Configure GradientFHD-FHD Skin" position="45,15" size="1110,60" font="Italic; 42" halign="left" valign="center" transparent="1" foregroundColor="gradient_foreground_selection" backgroundColor="background" textBorderColor="black" textBorderWidth="1" zPosition="1" />
		<widget source="menu" render="Listbox" position="30,100" size="1050,855" backgroundColor="gradient_background" foregroundColor="gradient_foreground" itemCornerRadiusSelected="12" itemGradientSelected="gradient_BGLM,gradient_BGLL,gradient_BGLL,horizontal" foregroundColorSelected="gradient_foreground_selection" scrollbarMode="showOnDemand" enableWrapAround="1" transparent="1">
			<convert type="TemplatedMultiContent">{"template":
   [
    MultiContentEntryPixmapAlphaTest(pos = (8, 5), size = (45, 45), png = 2),
    MultiContentEntryText(pos = (60, 3), size = (920, 45), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1),
   ],
   "fonts": [gFont("Gradient_Font", 30),gFont("Gradient_Font", 24)],
   "itemHeight": 45
     }</convert>
		</widget>
		<ePixmap pixmap="preview/preview_background_color_skin_Gradient.png" position="1100,100" size="782,484" zPosition="1" />
		<widget name="Picture" position="1100,100" size="782,484" alphatest="on" zPosition="2" />
		<panel name="Template_FullScreen_Base2" />
		<panel position="459,147" size="330,57">
			<panel name="Template_Text_Buttons_E" />
		</panel>
	</screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        global cur_skin
        self.is_atile = False
        if cur_skin == 'GradientFHD':
            self.is_atile = True

        self.title = _("%s additional screens") % cur_skin
        try:
            self["title"] = StaticText(self.title)
        except:
            print('self["title"] was not found in skin')

        self["key_red"] = StaticText(_("Exit"))
        self["key_green"] = StaticText(_("on"))

        self["Picture"] = Pixmap()

        menu_list = []
        self["menu"] = List(menu_list)

        self["shortcuts"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"],
        {
                "ok": self.runMenuEntry,
                "cancel": self.keyCancel,
                "red": self.keyCancel,
                "green": self.runMenuEntry,
        }, -2)

        self.skin_base_dir = "/usr/share/enigma2/%s/" % cur_skin
        self.screen_dir = "allScreens"
        self.skinparts_dir = "skinparts"
        self.file_dir = "mySkin_off"
        my_path = resolveFilename(SCOPE_SKIN, "%s/icons/lock_on.png" % cur_skin)
        if not path.exists(my_path):
            my_path = resolveFilename(SCOPE_SKIN, "skin_default/icons/lock_on.png")
        self.enabled_pic = LoadPixmap(cached=True, path=my_path)
        my_path = resolveFilename(SCOPE_SKIN, "%s/icons/lock_off.png" % cur_skin)
        if not path.exists(my_path):
            my_path = resolveFilename(SCOPE_SKIN, "skin_default/icons/lock_off.png")
        self.disabled_pic = LoadPixmap(cached=True, path=my_path)

        if not self.selectionChanged in self["menu"].onSelectionChanged:
            self["menu"].onSelectionChanged.append(self.selectionChanged)

        self.onLayoutFinish.append(self.createMenuList)

    def selectionChanged(self):
        sel = self["menu"].getCurrent()
        if sel is not None:
            self.setPicture(sel[0])
            if sel[2] == self.enabled_pic:
                self["key_green"].setText(_("off"))
            elif sel[2] == self.disabled_pic:
                self["key_green"].setText(_("on"))

    def createMenuList(self):
        chdir(self.skin_base_dir)
        f_list = []
        dir_path = self.skin_base_dir + self.screen_dir
        if not path.exists(dir_path):
            makedirs(dir_path)
        dir_skinparts_path = self.skin_base_dir + self.skinparts_dir
        if not path.exists(dir_skinparts_path):
            makedirs(dir_skinparts_path)
        file_dir_path = self.skin_base_dir + self.file_dir
        if not path.exists(file_dir_path):
            makedirs(file_dir_path)
        dir_global_skinparts = resolveFilename(SCOPE_SKIN, "skinparts")
        if path.exists(dir_global_skinparts):
            for pack in listdir(dir_global_skinparts):
                if path.isdir(dir_global_skinparts + "/" + pack):
                    for f in listdir(dir_global_skinparts + "/" + pack):
                        if path.exists(dir_global_skinparts + "/" + pack + "/" + f + "/" + f + "_Atile.xml"):
                            if not path.exists(dir_path + "/skin_" + f + ".xml"):
                                symlink(dir_global_skinparts + "/" + pack + "/" + f + "/" + f + "_Atile.xml", dir_path + "/skin_" + f + ".xml")
                            if not path.exists(dir_skinparts_path + "/" + f):
                                symlink(dir_global_skinparts + "/" + pack + "/" + f, dir_skinparts_path + "/" + f)
        list_dir = sorted(listdir(dir_path), key=str.lower)
        for f in list_dir:
            if f.endswith('.xml') and f.startswith('skin_'):
                if (not path.islink(dir_path + "/" + f)) or os.path.exists(os.readlink(dir_path + "/" + f)):
                    friendly_name = f.replace("skin_", "")
                    friendly_name = friendly_name.replace(".xml", "")
                    friendly_name = friendly_name.replace("_", " ")
                    linked_file = file_dir_path + "/" + f
                    if path.exists(linked_file):
                        if path.islink(linked_file):
                            pic = self.enabled_pic
                        else:
                            remove(linked_file)
                            symlink(dir_path + "/" + f, file_dir_path + "/" + f)
                            pic = self.enabled_pic
                    else:
                        pic = self.disabled_pic
                    f_list.append((f, friendly_name, pic))
                else:
                    if path.islink(dir_path + "/" + f):
                        remove(dir_path + "/" + f)
        menu_list = []
        for entry in f_list:
            menu_list.append((entry[0], entry[1], entry[2]))
        self["menu"].updateList(menu_list)
        self.selectionChanged()

    def setPicture(self, f):
        pic = f.replace(".xml", ".png")
        preview = self.skin_base_dir + "preview/preview_" + pic
        if path.exists(preview):
            self["Picture"].instance.setPixmapFromFile(preview)
            self["Picture"].show()
        else:
            self["Picture"].hide()

    def keyCancel(self):
        self.close()

    def runMenuEntry(self):
        sel = self["menu"].getCurrent()
        if sel is not None:
            if sel[2] == self.enabled_pic:
                remove(self.skin_base_dir + self.file_dir + "/" + sel[0])
            elif sel[2] == self.disabled_pic:
                symlink(self.skin_base_dir + self.screen_dir + "/" + sel[0], self.skin_base_dir + self.file_dir + "/" + sel[0])
            self.createMenuList()




# -------------------------------------------------------------
# PosterX Slug Viewer (Title → slug)
# Reads from:
#   <BASE>/xtra/poster_info/*.json
#   <BASE>/xtra/backdrop_info/*.json
#   /var/volatile/tmp/PosterAutoDB.log
#   /var/volatile/tmp/BackdropAutoDB.log
# Writes cache (created only when opened):
#   <BASE>/xtra/slug_cache_poster.json
#   <BASE>/xtra/slug_cache_backdrop.json
# -------------------------------------------------------------


class PosterXSlugViewer(Screen):
    skin = """
        <screen name="PosterXSlugViewer" position="center,center" size="1200,700" title="PosterX Slugs">
            <widget name="title" position="10,10" size="1180,40" font="Regular;30" />
            <widget name="list" position="10,60" size="1180,570" scrollbarMode="showOnDemand" />
            <widget name="hint" position="10,640" size="1180,45" font="Regular;20" />
        </screen>
    """

    MODE_POSTER = 'poster'
    MODE_BACKDROP = 'backdrop'

    def __init__(self, session, base_path):
        Screen.__init__(self, session)
        self.base_path = base_path or '/media/hdd'
        self.xtra_dir = path.join(self.base_path, 'xtra')

        self["title"] = Label('')
        self["hint"] = Label('')
        self["list"] = MenuList([])

        self.mode = self.MODE_POSTER

        self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "cancel": self.close,
                "ok": self.toggleMode,
                "green": self.toggleMode,
                "yellow": self.reload,
                "left": self.toggleMode,
                "right": self.toggleMode,
            }, -1)

        self.onLayoutFinish.append(self.reload)

    # -----------------------------
    # Collect / parse
    # -----------------------------
    def _safe_read_lines(self, f):
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
                return fp.read().splitlines()
        except Exception:
            return []

    def _collect_from_info_dir(self, info_dir):
        """Return mapping slug -> title from poster_info/backdrop_info json files."""
        mapping = {}
        try:
            if not path.exists(info_dir):
                return mapping
            for fn in sorted(listdir(info_dir), key=str.lower):
                if not fn.endswith('.json'):
                    continue
                slug = fn[:-5]
                fpath = path.join(info_dir, fn)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                        data = json.load(fp)
                except Exception:
                    data = {}

                title = data.get('title') or data.get('original_title') or data.get('name')
                if not title:
                    title = slug.replace('_', ' ')
                # keep first meaningful title
                if slug not in mapping or (mapping[slug].strip() == slug.replace('_', ' ')):
                    mapping[slug] = str(title)
        except Exception:
            pass
        return mapping

    def _collect_from_log(self, log_path):
        """Return mapping slug -> title from AutoDB log QUEUE lines."""
        mapping = {}
        lines = self._safe_read_lines(log_path)
        # Example:
        # [2026-01-19 16:08:33] [QUEUE] : RTL HD : 1768885200-Punkt 6 (punkt_6)
        rx = re.compile(r"\[QUEUE\].*?:\s*\d+-(.*?)\s*\(([^)]+)\)")
        for ln in lines:
            if '[QUEUE]' not in ln:
                continue
            m = rx.search(ln)
            if not m:
                continue
            title = m.group(1).strip()
            slug = m.group(2).strip()
            if slug and title:
                mapping[slug] = title
        return mapping

    def _merge(self, *maps):
        out = {}
        for mp in maps:
            for slug, title in (mp or {}).items():
                if slug not in out:
                    out[slug] = title
                else:
                    # prefer longer / more descriptive titles
                    if title and len(title) > len(out[slug]):
                        out[slug] = title
        return out

    def _to_menu(self, mapping):
        items = []
        for slug, title in mapping.items():
            items.append((title, slug))
        items.sort(key=lambda x: (x[0] or '').lower())
        return ["%s  →  %s" % (t, s) for (t, s) in items]

    def _write_cache(self, mapping, cache_file):
        try:
            makedirs(self.xtra_dir, exist_ok=True)
            data = [{"title": t, "slug": s} for t, s in sorted(((v, k) for k, v in mapping.items()), key=lambda x: (x[0] or '').lower())]
            with open(cache_file, 'w', encoding='utf-8') as fp:
                json.dump(data, fp, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # -----------------------------
    # UI
    # -----------------------------
    def reload(self):
        poster_info_dir = path.join(self.xtra_dir, 'poster_info')
        backdrop_info_dir = path.join(self.xtra_dir, 'backdrop_info')

        poster_map = self._merge(
            self._collect_from_info_dir(poster_info_dir),
            self._collect_from_log('/var/volatile/tmp/PosterAutoDB.log'),
        )
        backdrop_map = self._merge(
            self._collect_from_info_dir(backdrop_info_dir),
            self._collect_from_log('/var/volatile/tmp/BackdropAutoDB.log'),
        )

        # cache files are generated only when the viewer is opened
        self._write_cache(poster_map, path.join(self.xtra_dir, 'slug_cache_poster.json'))
        self._write_cache(backdrop_map, path.join(self.xtra_dir, 'slug_cache_backdrop.json'))

        self.poster_menu = self._to_menu(poster_map)
        self.backdrop_menu = self._to_menu(backdrop_map)

        self._applyMode()

    def _applyMode(self):
        if self.mode == self.MODE_POSTER:
            self['title'].setText(tr('Poster Slugs (Title → slug)', 'Poster-Slugs (Titel → slug)'))
            self['list'].setList(self.poster_menu)
            self['hint'].setText(tr(
                'GREEN/OK: switch list | YELLOW: reload | Files: <BASE>/xtra/custom/poster/<slug>.jpg',
                'GRUEN/OK: Liste wechseln | GELB: neu laden | Dateien: <BASE>/xtra/custom/poster/<slug>.jpg'
            ))
        else:
            self['title'].setText(tr('Backdrop Slugs (Title → slug)', 'Backdrop-Slugs (Titel → slug)'))
            self['list'].setList(self.backdrop_menu)
            self['hint'].setText(tr(
                'GREEN/OK: switch list | YELLOW: reload | Files: <BASE>/xtra/custom/backdrop/<slug>.jpg',
                'GRUEN/OK: Liste wechseln | GELB: neu laden | Dateien: <BASE>/xtra/custom/backdrop/<slug>.jpg'
            ))

    def toggleMode(self):
        self.mode = self.MODE_BACKDROP if self.mode == self.MODE_POSTER else self.MODE_POSTER
        self._applyMode()
