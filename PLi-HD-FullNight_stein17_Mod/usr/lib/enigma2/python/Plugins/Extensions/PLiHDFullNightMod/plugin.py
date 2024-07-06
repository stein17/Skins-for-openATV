# -*- coding: utf-8 -*-

#This plugin is free software, you are allowed to
#modify it (if you keep the license),
#but you are not allowed to distribute/publish
#it without source code (this version and your modifications).
#This means you also have to distribute
#source code of your modifications.


# for localized messages
from __future__ import absolute_import
from __future__ import print_function
from .__init__ import _

from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigYesNo, NoSave, ConfigNothing, ConfigNumber
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

cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')

config.plugins.PLiHDFullNightMod = ConfigSubsection()
config.plugins.PLiHDFullNightMod.refreshInterval = ConfigNumber(default=10)
config.plugins.PLiHDFullNightMod.woeid = ConfigNumber(default=638242)
config.plugins.PLiHDFullNightMod.tempUnit = ConfigSelection(default="Celsius", choices=[
                                ("Celsius", _("Celsius")),
                                ("Fahrenheit", _("Fahrenheit"))
                                ])


def Plugins(**kwargs):
    return [PluginDescriptor(name=_("PLi HD FullNight Mod  Configtool"), description=_("Personalize your PLi HD FullNight (Mod by stein17)"), where=[PluginDescriptor.WHERE_PLUGINMENU],
    icon="plugin.png", fnc=main)]


def main(session, **kwargs):
    if config.skin.primary_skin.value == "PLi-HD-FullNight_stein17_Mod/skin.xml":
        session.open(PLiHDFullNightMod_Config)
    else:
        AddPopup(_('Please activate PLi HD FullNight Mod Skin before run the Config Plugin'), type=MessageBox.TYPE_ERROR, timeout=10)
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


class PLiHDFullNightMod_Config(Screen, ConfigListScreen):

    skin = """
            <screen name="PLiHDFullNightMod_Config" position="center,center" size="1280,720" title="PLiHDFullNightMod Setup" >
                    <widget source="Title" render="Label" position="70,47" size="950,43" font="Regular;35" transparent="1" />
                    <widget name="config" position="70,115" size="700,480" scrollbarMode="showOnDemand" scrollbarWidth="6" transparent="1" />
                    <widget name="Picture" position="808,342" size="400,225" alphatest="on" />
                    <eLabel position=" 55,675" size="290, 5" zPosition="-10" backgroundColor="red" />
                    <eLabel position="350,675" size="290, 5" zPosition="-10" backgroundColor="green" />
                    <eLabel position="645,675" size="290, 5" zPosition="-10" backgroundColor="yellow" />
                    <eLabel position="940,675" size="290, 5" zPosition="-10" backgroundColor="blue" />
                    <widget name="key_red" position="70,635" size="260,25" zPosition="1" font="Regular;20" halign="left" foregroundColor="foreground" transparent="1" />
                    <widget name="key_green" position="365,635" size="260,25" zPosition="1" font="Regular;20" halign="left" foregroundColor="foreground" transparent="1" />
                    <widget name="key_yellow" position="660,635" size="260,25" zPosition="1" font="Regular;20" halign="left" foregroundColor="foreground" transparent="1" />
                    <widget name="key_blue" position="955,635" size="260,25" zPosition="0" font="Regular;20" halign="left" foregroundColor="foreground" transparent="1" />
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
        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
                {
                        "green": self.keyGreen,
                        "red": self.cancel,
                        "yellow": self.keyYellow,
                        "blue": self.about,
                        "cancel": self.cancel,
                        "ok": self.keyOk,
                        "menu": self.setWeather,
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

    def getInitConfig(self):

        global cur_skin
        self.is_atile = False
        if cur_skin == 'AtileHD':
            self.is_atile = True

        self.title = _("PLi HD FullNight Mod Setup")
        self.skin_base_dir = "/usr/share/enigma2/%s/" % cur_skin

        self.default_font_file = "font_atile_Roboto.xml"
        self.default_poster_infobar_file = "poster_infobar_Original.xml"
        self.default_background_file = "background_Original.xml"

        self.default_poster_epg_file = "poster_epg_Original.xml"
        self.default_pig_file = "pig_Original.xml"
        self.default_caid_file = "caid_Original.xml"
        self.default_colors_file = "colors_Original.xml"
        self.default_ch_se_file = "ch_se_Original.xml"
        self.default_poster_ch_sel_file = "poster_ch_sel_Original.xml"
        self.default_poster_sec_infobar_file = "poster_sec_infobar_Original.xml"
        self.default_poster_emc_movie_sel_file = "poster_emc_movie_sel_Original.xml"
        self.default_emc_mov_sel_file = "emc_mov_sel_Original.xml"
        self.default_vpnip_file = "vpnip_Original.xml"
        self.default_poster_player_file = "poster_player_Original.xml"
        self.default_player_file = "player_Original.xml"
        self.default_weather_file = "weather_Original.xml"
        self.default_weather_icons_file = "weather_icons_Original.xml"

        self.background_file = "skin_user_background.xml"
        self.poster_epg_file = "skin_user_poster_epg.xml"
        self.pig_file = "skin_user_pig.xml"
        self.caid_file = "skin_user_caid.xml"
        self.colors_file = "skin_user_colors.xml"
        self.ch_se_file = "skin_user_ch_se.xml"
        self.poster_ch_sel_file = "skin_user_poster_ch_sel.xml"
        self.poster_sec_infobar_file = "skin_user_poster_sec_infobar.xml"
        self.poster_emc_movie_sel_file = "skin_user_poster_emc_movie_sel.xml"
        self.emc_mov_sel_file = "skin_user_emc_mov_sel.xml"
        self.vpnip_file = "skin_user_vpnip.xml"
        self.poster_infobar_file = "skin_user_poster_infobar.xml"
        self.poster_player_file = "skin_user_poster_player.xml"
        self.player_file = "skin_user_player.xml"
        self.weather_file = "skin_user_weather.xml"
        self.weather_icons_file = "skin_user_weather_icons.xml"

        # background
        current, choices = self.getSettings(self.default_background_file, self.background_file)
        self.myAtileHD_background = NoSave(ConfigSelection(default=current, choices=choices))
        # poster_epg
        current, choices = self.getSettings(self.default_poster_epg_file, self.poster_epg_file)
        self.myAtileHD_poster_epg = NoSave(ConfigSelection(default=current, choices=choices))
        # pig
        current, choices = self.getSettings(self.default_pig_file, self.pig_file)
        self.myAtileHD_pig = NoSave(ConfigSelection(default=current, choices=choices))
        # caid
        current, choices = self.getSettings(self.default_caid_file, self.caid_file)
        self.myAtileHD_caid = NoSave(ConfigSelection(default=current, choices=choices))
        # colors
        current, choices = self.getSettings(self.default_colors_file, self.colors_file)
        self.myAtileHD_colors = NoSave(ConfigSelection(default=current, choices=choices))
        # ch_se
        current, choices = self.getSettings(self.default_ch_se_file, self.ch_se_file)
        self.myAtileHD_ch_se = NoSave(ConfigSelection(default=current, choices=choices))
        # poster_ch_sel
        current, choices = self.getSettings(self.default_poster_ch_sel_file, self.poster_ch_sel_file)
        self.myAtileHD_poster_ch_sel = NoSave(ConfigSelection(default=current, choices=choices))
        # poster_sec_infobar
        current, choices = self.getSettings(self.default_poster_sec_infobar_file, self.poster_sec_infobar_file)
        self.myAtileHD_poster_sec_infobar = NoSave(ConfigSelection(default=current, choices=choices))
        # poster_emc_movie_sel
        current, choices = self.getSettings(self.default_poster_emc_movie_sel_file, self.poster_emc_movie_sel_file)
        self.myAtileHD_poster_emc_movie_sel = NoSave(ConfigSelection(default=current, choices=choices))
        # emc_mov_sel
        current, choices = self.getSettings(self.default_emc_mov_sel_file, self.emc_mov_sel_file)
        self.myAtileHD_emc_mov_sel = NoSave(ConfigSelection(default=current, choices=choices))
        # vpnip
        current, choices = self.getSettings(self.default_vpnip_file, self.vpnip_file)
        self.myAtileHD_vpnip = NoSave(ConfigSelection(default=current, choices=choices))
        # poster_player
        current, choices = self.getSettings(self.default_poster_player_file, self.poster_player_file)
        self.myAtileHD_poster_player = NoSave(ConfigSelection(default=current, choices=choices))
        # poster_infobar
        current, choices = self.getSettings(self.default_poster_infobar_file, self.poster_infobar_file)
        self.myAtileHD_poster_infobar = NoSave(ConfigSelection(default=current, choices=choices))
        # player
        current, choices = self.getSettings(self.default_player_file, self.player_file)
        self.myAtileHD_player = NoSave(ConfigSelection(default=current, choices=choices))
        # weather
        current, choices = self.getSettings(self.default_weather_file, self.weather_file)
        self.myAtileHD_weather = NoSave(ConfigSelection(default=current, choices=choices))
        # weather_icons
        current, choices = self.getSettings(self.default_weather_icons_file, self.weather_icons_file)
        self.myAtileHD_weather_icons = NoSave(ConfigSelection(default=current, choices=choices))
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
        self.set_background = getConfigListEntry(_("Set background transparency:"), self.myAtileHD_background)
        self.set_poster_epg = getConfigListEntry(_("Poster EPG:"), self.myAtileHD_poster_epg)
        self.set_pig = getConfigListEntry(_("Switch Mini TV on/off:"), self.myAtileHD_pig)
        self.set_caid = getConfigListEntry(_("Caid Info Infobar:"), self.myAtileHD_caid)
        self.set_weather = getConfigListEntry(_("Weather Info:"), self.myAtileHD_weather)
        self.set_weather_icons = getConfigListEntry(_("Weather Icons style:"), self.myAtileHD_weather_icons)
        self.set_poster_infobar = getConfigListEntry(_("Poster Infobar:"), self.myAtileHD_poster_infobar)
        self.set_colors = getConfigListEntry(_("Selected Foreground Color:"), self.myAtileHD_colors)
        self.set_ch_se = getConfigListEntry(_("Channelselection:"), self.myAtileHD_ch_se)
        self.set_poster_ch_sel = getConfigListEntry(_("Poster Channelselection:"), self.myAtileHD_poster_ch_sel)
        self.set_poster_sec_infobar = getConfigListEntry(_("Poster 2. Infobar:"), self.myAtileHD_poster_sec_infobar)
        self.set_poster_emc_movie_sel = getConfigListEntry(_("Poster EMC/Movie Selection:"), self.myAtileHD_poster_emc_movie_sel)
        self.set_emc_mov_sel = getConfigListEntry(_("EMC/Movie Selection:"), self.myAtileHD_emc_mov_sel)
        self.set_vpnip = getConfigListEntry(_("display VPN IP address:"), self.myAtileHD_vpnip)
        self.set_poster_player = getConfigListEntry(_("Poster Player:"), self.myAtileHD_poster_player)
        self.set_player = getConfigListEntry(_("Movie Player:"), self.myAtileHD_player)
        self.set_myatile = getConfigListEntry(_("Enable %s Extentions:") % cur_skin, self.myAtileHD_active)
        self.find_woeid = getConfigListEntry(_("Search weather location ID"), ConfigNothing())
        self.list = []
        self.list.append(self.set_myatile)
        if self.myAtileHD_active.value:
            if len(self.myAtileHD_background.choices) > 1:
                self.list.append(self.set_background)
            if len(self.myAtileHD_pig.choices) > 1:
                self.list.append(self.set_pig)
            if len(self.myAtileHD_caid.choices) > 1:
                self.list.append(self.set_caid)
            if len(self.myAtileHD_vpnip.choices) > 1:
                self.list.append(self.set_vpnip)
            if len(self.myAtileHD_colors.choices) > 1:
                self.list.append(self.set_colors)
            if len(self.myAtileHD_ch_se.choices) > 1:
                self.list.append(self.set_ch_se)
            if len(self.myAtileHD_weather.choices) > 1:
                self.list.append(self.set_weather)
            if len(self.myAtileHD_weather_icons.choices) > 1:
                self.list.append(self.set_weather_icons)
            if len(self.myAtileHD_emc_mov_sel.choices) > 1:
                self.list.append(self.set_emc_mov_sel)
            if len(self.myAtileHD_player.choices) > 1:
                self.list.append(self.set_player)
            if len(self.myAtileHD_poster_infobar.choices) > 1:
                self.list.append(self.set_poster_infobar)
            if len(self.myAtileHD_poster_sec_infobar.choices) > 1:
                self.list.append(self.set_poster_sec_infobar)
            if len(self.myAtileHD_poster_epg.choices) > 1:
                self.list.append(self.set_poster_epg)
            if len(self.myAtileHD_poster_ch_sel.choices) > 1:
                self.list.append(self.set_poster_ch_sel)
            if len(self.myAtileHD_poster_emc_movie_sel.choices) > 1:
                self.list.append(self.set_poster_emc_movie_sel)
            if len(self.myAtileHD_poster_player.choices) > 1:
                self.list.append(self.set_poster_player)

        self["config"].list = self.list
        self["config"].l.setList(self.list)
        if self.myAtileHD_active.value:
            self["key_yellow"].setText("%s Config" % cur_skin)
        else:
            self["key_yellow"].setText("")

    def changedEntry(self):
        if self["config"].getCurrent() == self.set_poster_infobar:
            self.setPicture(self.myAtileHD_poster_infobar.value)
        elif self["config"].getCurrent() == self.set_background:
            self.setPicture(self.myAtileHD_background.value)
        elif self["config"].getCurrent() == self.set_poster_epg:
            self.setPicture(self.myAtileHD_poster_epg.value)
        elif self["config"].getCurrent() == self.set_pig:
            self.setPicture(self.myAtileHD_pig.value)
        elif self["config"].getCurrent() == self.set_caid:
            self.setPicture(self.myAtileHD_caid.value)
        elif self["config"].getCurrent() == self.set_colors:
            self.setPicture(self.myAtileHD_colors.value)
        elif self["config"].getCurrent() == self.set_ch_se:
            self.setPicture(self.myAtileHD_ch_se.value)
        elif self["config"].getCurrent() == self.set_poster_ch_sel:
            self.setPicture(self.myAtileHD_poster_ch_sel.value)
        elif self["config"].getCurrent() == self.set_poster_sec_infobar:
            self.setPicture(self.myAtileHD_poster_sec_infobar.value)
        elif self["config"].getCurrent() == self.set_poster_emc_movie_sel:
            self.setPicture(self.myAtileHD_poster_emc_movie_sel.value)
        elif self["config"].getCurrent() == self.set_emc_mov_sel:
            self.setPicture(self.myAtileHD_emc_mov_sel.value)
        elif self["config"].getCurrent() == self.set_vpnip:
            self.setPicture(self.myAtileHD_vpnip.value)
        elif self["config"].getCurrent() == self.set_poster_player:
            self.setPicture(self.myAtileHD_poster_player.value)
        elif self["config"].getCurrent() == self.set_player:
            self.setPicture(self.myAtileHD_player.value)
        elif self["config"].getCurrent() == self.set_weather:
            self.setPicture(self.myAtileHD_weather.value)
        elif self["config"].getCurrent() == self.set_weather_icons:
            self.setPicture(self.myAtileHD_weather_icons.value)
        elif self["config"].getCurrent() == self.set_myatile:
            if self.myAtileHD_active.value:
                self["key_yellow"].setText("%s Config" % cur_skin)
            else:
                self["key_yellow"].setText("")
            self.createConfigList()

    def selectionChanged(self):
        if self["config"].getCurrent() == self.set_poster_infobar:
            self.setPicture(self.myAtileHD_poster_infobar.value)
        elif self["config"].getCurrent() == self.set_background:
            self.setPicture(self.myAtileHD_background.value)
        elif self["config"].getCurrent() == self.set_poster_epg:
            self.setPicture(self.myAtileHD_poster_epg.value)
        elif self["config"].getCurrent() == self.set_pig:
            self.setPicture(self.myAtileHD_pig.value)
        elif self["config"].getCurrent() == self.set_caid:
            self.setPicture(self.myAtileHD_caid.value)
        elif self["config"].getCurrent() == self.set_colors:
            self.setPicture(self.myAtileHD_colors.value)
        elif self["config"].getCurrent() == self.set_ch_se:
            self.setPicture(self.myAtileHD_ch_se.value)
        elif self["config"].getCurrent() == self.set_poster_ch_sel:
            self.setPicture(self.myAtileHD_poster_ch_sel.value)
        elif self["config"].getCurrent() == self.set_poster_sec_infobar:
            self.setPicture(self.myAtileHD_poster_sec_infobar.value)
        elif self["config"].getCurrent() == self.set_poster_emc_movie_sel:
            self.setPicture(self.myAtileHD_poster_emc_movie_sel.value)
        elif self["config"].getCurrent() == self.set_emc_mov_sel:
            self.setPicture(self.myAtileHD_emc_mov_sel.value)
        elif self["config"].getCurrent() == self.set_vpnip:
            self.setPicture(self.myAtileHD_vpnip.value)
        elif self["config"].getCurrent() == self.set_poster_player:
            self.setPicture(self.myAtileHD_poster_player.value)
        elif self["config"].getCurrent() == self.set_player:
            self.setPicture(self.myAtileHD_player.value)
        elif self["config"].getCurrent() == self.set_weather:
            self.setPicture(self.myAtileHD_weather.value)
        elif self["config"].getCurrent() == self.set_weather_icons:
            self.setPicture(self.myAtileHD_weather_icons.value)
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

    def keyYellow(self):
        if self.myAtileHD_active.value:
            self.session.openWithCallback(self.PLiHDFullNightModScreenCB, PLiHDFullNightModScreens)
        else:
            self["config"].setCurrentIndex(0)

    def keyOk(self):
        sel = self["config"].getCurrent()
        if sel is not None and sel == self.find_woeid:
            self.session.openWithCallback(self.search_weather_id_callback, InputBox, title=_("Please enter search string for your location"), text="")
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
            config.plugins.PLiHDFullNightMod.woeid.value = int(res)

    def skinChanged(self, ret=None):
        global cur_skin
        cur_skin = config.skin.primary_skin.value.replace('/skin.xml', '')
        if cur_skin == "skin.xml":
            self.restartGUI()
        else:
            self.getInitConfig()
            self.createConfigList()

    def keyGreen(self):
        if self["config"].isChanged():
            for x in self["config"].list:
                x[1].save()
            chdir(self.skin_base_dir)

            # background
            self.makeSettings(self.myAtileHD_background, self.background_file)
            # poster_epg
            self.makeSettings(self.myAtileHD_poster_epg, self.poster_epg_file)
            # pig
            self.makeSettings(self.myAtileHD_pig, self.pig_file)
            # caid
            self.makeSettings(self.myAtileHD_caid, self.caid_file)
            # colors
            self.makeSettings(self.myAtileHD_colors, self.colors_file)
            # ch_se
            self.makeSettings(self.myAtileHD_ch_se, self.ch_se_file)
            # poster_ch_sel
            self.makeSettings(self.myAtileHD_poster_ch_sel, self.poster_ch_sel_file)
            # poster_sec_infobar
            self.makeSettings(self.myAtileHD_poster_sec_infobar, self.poster_sec_infobar_file)
            # poster_emc_movie_sel
            self.makeSettings(self.myAtileHD_poster_emc_movie_sel, self.poster_emc_movie_sel_file)
            # emc_mov_sel
            self.makeSettings(self.myAtileHD_emc_mov_sel, self.emc_mov_sel_file)
            # vpnip
            self.makeSettings(self.myAtileHD_vpnip, self.vpnip_file)
            # poster_player
            self.makeSettings(self.myAtileHD_poster_player, self.poster_player_file)
            # player
            self.makeSettings(self.myAtileHD_player, self.player_file)
            # poster_infobar
            self.makeSettings(self.myAtileHD_poster_infobar, self.poster_infobar_file)
            # weather
            self.makeSettings(self.myAtileHD_weather, self.weather_file)
            # weather_icons
            self.makeSettings(self.myAtileHD_weather_icons, self.weather_icons_file)

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

    def PLiHDFullNightModScreenCB(self):
        self.changed_screens = True
        self["config"].setCurrentIndex(0)

    def restartGUI(self):
        restartbox = self.session.openWithCallback(self.restartGUIcb, MessageBox, _("Restart necessary, restart GUI now?"), MessageBox.TYPE_YESNO)
        restartbox.setTitle(_("Message"))

    def about(self):
        self.session.open(PLiHDFullNightMod_About)

    def restartGUIcb(self, answer):
        if answer is True:
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close()


class PLiHDFullNightMod_About(Screen):

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


class PLiHDFullNightModScreens(Screen):

    skin = """
            <screen name="PLiHDFullNightModScreens" position="center,center" size="1280,720" title="PLiHDFullNightMod Setup">
                    <widget source="Title" render="Label" position="70,47" size="950,43" font="Regular;35" transparent="1" />
                    <widget source="menu" render="Listbox" position="70,115" size="700,480" scrollbarMode="showOnDemand" scrollbarWidth="6" scrollbarSliderBorderWidth="1" enableWrapAround="1" transparent="1">
                            <convert type="TemplatedMultiContent">
                                    {"template":
                                            [
                                                    MultiContentEntryPixmapAlphaTest(pos = (2, 2), size = (25, 24), png = 2),
                                                    MultiContentEntryText(pos = (35, 4), size = (500, 24), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1),
                                            ],
                                            "fonts": [gFont("Regular", 22),gFont("Regular", 16)],
                                            "itemHeight": 30
                                    }
                            </convert>
                    </widget>
                    <widget name="Picture" position="808,342" size="400,225" alphatest="on" />
                    <eLabel position=" 55,675" size="290, 5" zPosition="-10" backgroundColor="red" />
                    <eLabel position="350,675" size="290, 5" zPosition="-10" backgroundColor="green" />
                    <widget source="key_red" render="Label" position="70,635" size="260,25" zPosition="1" font="Regular;20" halign="left" transparent="1" />
                    <widget source="key_green" render="Label" position="365,635" size="260,25" zPosition="1" font="Regular;20" halign="left" transparent="1" />
            </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session

        global cur_skin
        self.is_atile = False
        if cur_skin == 'PLiHDFullNightMod':
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
