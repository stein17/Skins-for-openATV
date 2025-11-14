# -*- coding: utf-8 -*-

#This plugin is free software, you are allowed to
#modify it (if you keep the license),
#but you are not allowed to distribute/publish
#it without source code (this version and your modifications).
#This means you also have to distribute
#source code of your modifications.
###################################
#modify by stein17
#I greatly expanded the plugin many years ago.
#It was often copied, but there was no mention of it anywhere.


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

config.plugins.GradientFHD = ConfigSubsection()
config.plugins.GradientFHD.refreshInterval = ConfigNumber(default=10)
config.plugins.GradientFHD.woeid = ConfigNumber(default=638242)
config.plugins.GradientFHD.tempUnit = ConfigSelection(default="Celsius", choices=[
                                ("Celsius", _("Celsius")),
                                ("Fahrenheit", _("Fahrenheit"))
                                ])


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
            <screen name="GradientFHD_Config" position="center,center" size="1280,720" title="GradientFHD Setup" >
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
        self.default_mmmmmm_file = "mmmmmm_Original.xml"
        self.default_nnnnnn_file = "nnnnnn_Original.xml"
        self.default_oooooo_file = "oooooo_Original.xml"
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
        self.mmmmmm_file = "skin_user_mmmmmm.xml"
        self.nnnnnn_file = "skin_user_nnnnnn.xml"
        self.oooooo_file = "skin_user_oooooo.xml"
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
        # mmmmmm
        current, choices = self.getSettings(self.default_mmmmmm_file, self.mmmmmm_file)
        self.myAtileHD_mmmmmm = NoSave(ConfigSelection(default=current, choices=choices))
        # background_color_skin
        current, choices = self.getSettings(self.default_background_color_skin_file, self.background_color_skin_file)
        self.myAtileHD_background_color_skin = NoSave(ConfigSelection(default=current, choices=choices))
        # nnnnnn
        current, choices = self.getSettings(self.default_nnnnnn_file, self.nnnnnn_file)
        self.myAtileHD_nnnnnn = NoSave(ConfigSelection(default=current, choices=choices))
        # oooooo
        current, choices = self.getSettings(self.default_oooooo_file, self.oooooo_file)
        self.myAtileHD_oooooo = NoSave(ConfigSelection(default=current, choices=choices))
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
        self.set_oooooo = getConfigListEntry(_("blabla:"), self.myAtileHD_oooooo)
        self.set_pppppp = getConfigListEntry(_("bla:"), self.myAtileHD_pppppp)
        self.set_background_color_skin = getConfigListEntry(_("BackgroundColor Skin:"), self.myAtileHD_background_color_skin)
        self.set_foreground_color_event = getConfigListEntry(_("ForegroundColor Event:"), self.myAtileHD_foreground_color_event)
        self.set_foreground_color_event_selected = getConfigListEntry(_("ForegroundColor EventSelected:"), self.myAtileHD_foreground_color_event_selected)
        self.set_weather = getConfigListEntry(_("Weather Infobar:"), self.myAtileHD_weather)
        self.set_progressbar_color_skin = getConfigListEntry(_("ProgressbarColor Skin:"), self.myAtileHD_progressbar_color_skin)
        self.set_background_color_channel_selected = getConfigListEntry(_("BackgroundColor ChannelSelected:"), self.myAtileHD_background_color_channel_selected)
        self.set_softcam = getConfigListEntry(_("Softcamdetails:"), self.myAtileHD_softcam)
        self.set_weather_design = getConfigListEntry(_("Weather Infobar Design:"), self.myAtileHD_weather_design)
        self.set_mmmmmm = getConfigListEntry(_("Poster:"), self.myAtileHD_mmmmmm)
        self.set_nnnnnn = getConfigListEntry(_("Movie:"), self.myAtileHD_nnnnnn)
        self.set_myatile = getConfigListEntry(_("Enable %s Extentions:") % cur_skin, self.myAtileHD_active)
        self.find_woeid = getConfigListEntry(_("Search weather location ID"), ConfigNothing())
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
            if len(self.myAtileHD_oooooo.choices) > 1:
                self.list.append(self.set_oooooo)
            if len(self.myAtileHD_pppppp.choices) > 1:
                self.list.append(self.set_pppppp)

            if len(self.myAtileHD_nnnnnn.choices) > 1:
                self.list.append(self.set_nnnnnn)
            if len(self.myAtileHD_mmmmmm.choices) > 1:
                self.list.append(self.set_mmmmmm)

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
        elif self["config"].getCurrent() == self.set_mmmmmm:
            self.setPicture(self.myAtileHD_mmmmmm.value)
        elif self["config"].getCurrent() == self.set_nnnnnn:
            self.setPicture(self.myAtileHD_nnnnnn.value)
        elif self["config"].getCurrent() == self.set_oooooo:
            self.setPicture(self.myAtileHD_oooooo.value)
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
        elif self["config"].getCurrent() == self.set_mmmmmm:
            self.setPicture(self.myAtileHD_mmmmmm.value)
        elif self["config"].getCurrent() == self.set_nnnnnn:
            self.setPicture(self.myAtileHD_nnnnnn.value)
        elif self["config"].getCurrent() == self.set_oooooo:
            self.setPicture(self.myAtileHD_oooooo.value)
        elif self["config"].getCurrent() == self.set_pppppp:
            self.setPicture(self.myAtileHD_pppppp.value)
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
            self.session.openWithCallback(self.GradientFHDScreenCB, GradientFHDScreens)
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
            config.plugins.GradientFHD.woeid.value = int(res)

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
            # mmmmmm
            self.makeSettings(self.myAtileHD_mmmmmm, self.mmmmmm_file)
            # nnnnnn
            self.makeSettings(self.myAtileHD_nnnnnn, self.nnnnnn_file)
            # background_color_skin
            self.makeSettings(self.myAtileHD_background_color_skin, self.background_color_skin_file)
            # oooooo
            self.makeSettings(self.myAtileHD_oooooo, self.oooooo_file)
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
            <screen name="GradientFHDScreens" position="center,center" size="1280,720" title="GradientFHD Setup">
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
