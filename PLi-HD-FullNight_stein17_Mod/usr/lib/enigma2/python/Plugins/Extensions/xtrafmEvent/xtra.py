#!/usr/bin/env python
# -*- coding: utf-8 -*-
# by digiteng...06.2020, 11.2020, 11.2021, 12.2021, 01.2022
# Only posters and backdrops, fixed and minimized! (by stein17), 06.2024
# Special thanks go to@Villak from the OpenSpa team, who has fixed and improved many things.
# I have adapted his version here again to my needs.
from __future__ import absolute_import
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
import Tools.Notifications
import os
import re
import json
from Components.config import config, configfile, ConfigYesNo, ConfigSubsection, \
getConfigListEntry, ConfigSelection, ConfigText, ConfigInteger, ConfigSelectionNumber, \
ConfigDirectory, ConfigClock, NoSave
from Components.ConfigList import ConfigListScreen
from enigma import eTimer, eLabel, ePixmap, eSize, ePoint, loadJPG, eEPGCache, \
getDesktop, addFont, eServiceReference, eServiceCenter
from Components.Sources.StaticText import StaticText
from Screens.VirtualKeyBoard import VirtualKeyBoard
from PIL import Image
from Screens.LocationBox import LocationBox
import socket
import requests
from Components.ProgressBar import ProgressBar
from Screens.ChoiceBox import ChoiceBox
import shutil
from .xtraSelectionList import xtraSelectionList, xtraSelectionEntryComponent
from Plugins.Extensions.xtrafmEvent.skins.xtrafmSkins import *
from threading import Timer
from datetime import datetime
version = "v5.2.1"

pathLoc = ""
try:
	pathLoc = "{}xtrafmEvent/".format(config.plugins.xtrafmEvent.loc.value)
except:
	pass

try:
	import sys
	infoPY = sys.version_info[0]
	if infoPY == 3:
		from builtins import str
		from builtins import range
		from builtins import object
		from configparser import ConfigParser
		from _thread import start_new_thread
	else:
		from ConfigParser import ConfigParser
		from thread import start_new_thread
except:
	pass
try:
	if config.plugins.xtrafmEvent.tmdbAPI.value != "":
		tmdb_api = config.plugins.xtrafmEvent.tmdbAPI.value
	else:
		tmdb_api = "3c3efcf47c3577558812bb9d64019d65"
	if config.plugins.xtrafmEvent.tvdbAPI.value != "":
		tvdb_api = config.plugins.xtrafmEvent.tvdbAPI.value
	else:
		tvdb_api = "a99d487bb3426e5f3a60dea6d3d3c7ef"
	if config.plugins.xtrafmEvent.fanartAPI.value != "":
		fanart_api = config.plugins.xtrafmEvent.fanartAPI.value
	else:
		fanart_api = "6d231536dea4318a88cb2520ce89473b"
	if config.plugins.xtrafmEvent.googleAPI.value != "":
		google_api = config.plugins.xtrafmEvent.googleAPI.value
	else:
		google_api = "AIzaSyCayBp5fi66ZaUQOhHa5d9P7RPCYvvSnJ4"
except:
	pass

try:
	from Components.Language import language
	lang = language.getLanguage()
	lang = lang[:2]
except:
	try:
		lang = config.osd.language.value[:-3]
	except:
		lang = "en"

lang_path = r"/usr/lib/enigma2/python/Plugins/Extensions/xtrafmEvent/languages"
try:
	lng = ConfigParser()
	if infoPY == 3:
		lng.read(lang_path,	 encoding='utf8')
	else:
		lng.read(lang_path)
	lng.get(lang, "0")
except:
	try:
		lang="en"
		lng = ConfigParser()
		if infoPY == 3:
			lng.read(lang_path,	 encoding='utf8')
		else:
			lng.read(lang_path)
	except:
		pass

desktop_size = getDesktop(0).size().width()
epgcache = eEPGCache.getInstance()


config.plugins.xtrafmEvent = ConfigSubsection()
config.plugins.xtrafmEvent.onoff = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.skinSelect = ConfigSelection(default = "skin_1", choices = [("skin_1"), ("skin_2")])
config.plugins.xtrafmEvent.skinSelectColor = ConfigSelection(default = "#3478c1", choices = [
	("#3478c1", "Blue"), 
	("#4682B4","Steel Blue"),
	("#ea5b5b","Red"), 
	("#8B0000","Dark Red"),
	("#8B4513","Saddle Brown"),
	("#008080","Teal"),
	("#4F4F4F","Gray31"),
	("#4f5b66","Space Gray"),
	("#008B8B","Dark Cyan"),
	("#2E8B57","SeaGreen"),
	])
config.plugins.xtrafmEvent.loc = ConfigDirectory(default='/tmp/')
config.plugins.xtrafmEvent.searchMOD = ConfigSelection(default = lng.get(lang, '14'), choices = [(lng.get(lang, '13')), (lng.get(lang, '14')), (lng.get(lang, '14a'))])
config.plugins.xtrafmEvent.searchNUMBER = ConfigSelectionNumber(0, 999, 1, default=0)

# config.plugins.xtrafmEvent.timerMod = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.timerMod = ConfigSelection(default="-1", choices=[
	("-1", _("Disable")), 
	("Period"), 
	("Clock"), 
	])


config.plugins.xtrafmEvent.timerHour = ConfigSelectionNumber(1, 168, 1, default=1)
config.plugins.xtrafmEvent.timerClock = ConfigClock(default=0)

config.plugins.xtrafmEvent.searchMANUELnmbr = ConfigSelectionNumber(0, 999, 1, default=1)
config.plugins.xtrafmEvent.searchMANUELyear = ConfigInteger(default = 0, limits=(0, 9999))
config.plugins.xtrafmEvent.imgNmbr = ConfigSelectionNumber(0, 999, 1, default=1)
config.plugins.xtrafmEvent.searchModManuel = ConfigSelection(default = lng.get(lang, '16'), choices = [(lng.get(lang, '16')), (lng.get(lang, '17'))])
config.plugins.xtrafmEvent.EMCloc = ConfigDirectory(default='/tmp/')
config.plugins.xtrafmEvent.apis = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.tmdbAPI = ConfigText(default="", visible_width=100, fixed_size=False)
config.plugins.xtrafmEvent.tvdbAPI = ConfigText(default="", visible_width=100, fixed_size=False)
config.plugins.xtrafmEvent.omdbAPI = ConfigText(default="", visible_width=100, fixed_size=False)
config.plugins.xtrafmEvent.fanartAPI = ConfigText(default="", visible_width=100, fixed_size=False)
config.plugins.xtrafmEvent.googleAPI = ConfigText(default="", visible_width=100, fixed_size=False)
config.plugins.xtrafmEvent.searchMANUEL_EMC = ConfigText(default="movies name", visible_width=100, fixed_size=False)
config.plugins.xtrafmEvent.searchMANUEL = ConfigText(default="event name", visible_width=100, fixed_size=False)
# config.plugins.xtrafmEvent.searchLang = ConfigText(default="", visible_width=100, fixed_size=False)

config.plugins.xtrafmEvent.searchLang = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.tmdb = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.tvdb = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.maze = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.fanart = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.bing = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.extra = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.extra2 = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.extra3 = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.poster = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.banner = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.backdrop = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.info = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.infoOmdb = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.infoImdb = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.opt_Images = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.cnfg = ConfigYesNo(default = False)
config.plugins.xtrafmEvent.cnfgSel = ConfigSelection(default = "poster", choices = [("poster"), ("banner"), ("backdrop"), ("EMC")])
config.plugins.xtrafmEvent.TMDBpostersize = ConfigSelection(default="w185", choices = [
	("w92", "92x138"), 
	("w154", "154x231"), 
	("w185", "185x278"), 
	("w342", "342x513"), 
	("w500", "500x750"), 
	("w780", "780x1170"), 
	("original", "ORIGINAL")])
config.plugins.xtrafmEvent.TVDBpostersize = ConfigSelection(default="thumbnail", choices = [
	("thumbnail", "340x500"), 
	("fileName", "original(680x1000)")])
config.plugins.xtrafmEvent.TMDBbackdropsize = ConfigSelection(default="w300", choices = [
	("w300", "300x170"), 
	("w780", "780x440"), 
	("w1280", "1280x720"),
	("original", "ORIGINAL")])
config.plugins.xtrafmEvent.TVDBbackdropsize = ConfigSelection(default="thumbnail", choices = [
	("thumbnail", "640x360"), 
	("fileName", "original(1920x1080)")])
config.plugins.xtrafmEvent.FANART_Poster_Resize = ConfigSelection(default="10", choices = [
	("10", "100x142"), 
	("5", "200x285"), 
	("3", "333x475"), 
	("2", "500x713"), 
	("1", "1000x1426")])
config.plugins.xtrafmEvent.FANART_Backdrop_Resize = ConfigSelection(default="2", choices = [
	("2", "original/2"), 
	("1", "original")])
config.plugins.xtrafmEvent.imdb_Poster_size = ConfigSelection(default="185", choices = [
	("185", "185x278"), 
	("344", "344x510"), 
	("500", "500x750")])
config.plugins.xtrafmEvent.PB = ConfigSelection(default="posters", choices = [
	("posters", "Poster"), 
	("backdrops", "Backdrop")])
config.plugins.xtrafmEvent.srcs = ConfigSelection(default="TMDB", choices = [
	('TMDB', 'TMDB'), 
	('TVDB', 'TVDB'), 
	('FANART', 'FANART'), 
	('IMDB(poster)', 'IMDB(poster)'), 
	('Bing', 'Bing'), 
	('Google', 'Google')])
config.plugins.xtrafmEvent.searchType = ConfigSelection(default="tv", choices = [
	('tv', 'TV'), 
	('movie', 'MOVIE'), 
	('multi', 'MULTI')])
config.plugins.xtrafmEvent.FanartSearchType = ConfigSelection(default="tv", choices = [
	('tv', 'TV'),
	('movies', 'MOVIE')])
config.plugins.xtrafmEvent.TVDB_Banner_Size = ConfigSelection(default="1", choices = [
	("1", "758x140"), 
	("2", "379x70"),
	("4", "190x35")])
config.plugins.xtrafmEvent.FANART_Banner_Size = ConfigSelection(default="1", choices = [
	("1", "1000x185"), 
	("2", "500x92"),
	("4", "250x46"),
	("8", "125x23")
	])

class xtra(Screen, ConfigListScreen):

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)

		if desktop_size <= 1280:
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_1':
				self.skin = xtra_720
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_2':
				self.skin = xtra_720_2			
		else:
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_1':
				self.skin = xtra_1080
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_2':
				self.skin = xtra_1080_2
	
		list = []
		ConfigListScreen.__init__(self, list, session=session)
		
		self['key_red'] = Label(_('Close'))
		self['key_green'] = Label(_(lng.get(lang, '40')))
		self['key_yellow'] = Label(_(lng.get(lang, '76')))
		self['key_blue'] = Label(_(lng.get(lang, '18')))
		self["actions"] = ActionMap(["xtrafmEventAction"],
		{
			"left": self.keyLeft,
			"down": self.keyDown,
			"up": self.keyUp,
			"right": self.keyRight,
			"red": self.exit,
			"green": self.search,
			"yellow": self.strg,
			"blue": self.ms,
			"cancel": self.exit,
			"ok": self.keyOK,
			"info": self.strg,
			"menu": self.menuS
		},-1)
		
		self.setTitle(_("xtrafmEvent {}".format(version)))
		self['status'] = Label()
		self['info'] = Label()
		self['int_statu'] = Label()
		self['help'] = StaticText()

		self.timer = eTimer()
		self.timer.callback.append(self.xtraList)
		self.onLayoutFinish.append(self.xtraList)
		self.intCheck()

	def intCheck(self):
		try:
			socket.setdefaulttimeout(2)
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
			self['int_statu'].setText("☻")
			return True
		except:
			self['int_statu'].hide()
			self['status'].setText(lng.get(lang, '68'))
			return False

	def strg(self):
		if config.plugins.xtrafmEvent.onoff.value:
			try:
				path_poster = "{}poster/".format(pathLoc)
				path_banner = "{}banner/".format(pathLoc)
				path_backdrop = "{}backdrop/".format(pathLoc)
				path_info = "{}infos/".format(pathLoc)
				folder_size=sum([sum(map(lambda fname: os.path.getsize(os.path.join(path_poster, fname)), files)) for path_poster, folders, files in os.walk(path_poster)])
				posters_sz = "%0.1f" % (folder_size//(1024*1024.0))
				poster_nmbr = len(os.listdir(path_poster))
				folder_size=sum([sum(map(lambda fname: os.path.getsize(os.path.join(path_banner, fname)), files)) for path_banner, folders, files in os.walk(path_banner)])
				banners_sz = "%0.1f" % (folder_size//(1024*1024.0))
				banner_nmbr = len(os.listdir(path_banner))
				folder_size=sum([sum(map(lambda fname: os.path.getsize(os.path.join(path_backdrop, fname)), files)) for path_backdrop, folders, files in os.walk(path_backdrop)])
				backdrops_sz = "%0.1f" % (folder_size//(1024*1024.0))
				backdrop_nmbr = len(os.listdir(path_backdrop))
				folder_size=sum([sum(map(lambda fname: os.path.getsize(os.path.join(path_info, fname)), files)) for path_info, folders, files in os.walk(path_info)])
				infos_sz = "%0.1f" % (folder_size//(1024*1024.0))
				info_nmbr = len(os.listdir(path_info))
				self['status'].setText(_(lng.get(lang, '48')))
				pstr = "Poster : {} poster {} MB".format(poster_nmbr, posters_sz)
				bnnr = "Banner : {} banner {} MB".format(banner_nmbr, banners_sz)
				bckdrp = "Backdrop : {} backdrop {} MB".format(backdrop_nmbr, backdrops_sz)
				inf = "Info : {} info {} MB".format(info_nmbr, infos_sz)
				pbbi = "\n".join([pstr, bnnr, bckdrp, inf])
				self['info'].setText(str(pbbi))
			except Exception as err:
				with open("/tmp/xtrafmEvent.log", "a+") as f:
					f.write("xtra-info-strg, %s\n"%(err))
		else:
			self.exit()

	def keyOK(self):
		if self['config'].getCurrent()[1] is config.plugins.xtrafmEvent.loc:
			self.session.openWithCallback(self.pathSelected, LocationBox, text=_('Default Folder'), currDir=config.plugins.xtrafmEvent.loc.getValue(), minFree=100)
		if self['config'].getCurrent()[1] is config.plugins.xtrafmEvent.cnfgSel:
			self.compressImg()

	def pathSelected(self, res):
		if res is not None:
			config.plugins.xtrafmEvent.loc.value = res
			pathLoc = "{}xtrafmEvent/".format(config.plugins.xtrafmEvent.loc.value)
			if not os.path.isdir(pathLoc):
				os.makedirs("{}poster".format(pathLoc))
				os.makedirs("{}banner".format(pathLoc))
				os.makedirs("{}backdrop".format(pathLoc))
				os.makedirs("{}infos".format(pathLoc))
				os.makedirs("{}mSearch".format(pathLoc))
				os.makedirs("{}EMC".format(pathLoc))
			self.updateFinish()

	def delay(self):
		self.timer.start(100, True)

	def xtraList(self):
		
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		on_color = "\\c0000??00"
		off_color = "\\c00??0000"
		list = []
# CONFIG_________________________________________________________________________________________________________________
		
		if config.plugins.xtrafmEvent.onoff.value:
			list.append(getConfigListEntry("{}◙ \\c00?????? {}".format(on_color, lng.get(lang, '0')), config.plugins.xtrafmEvent.onoff, _(lng.get(lang, '0'))))
			list.append(getConfigListEntry("♥  {}".format(lng.get(lang, '1')), config.plugins.xtrafmEvent.cnfg, _(lng.get(lang, '2'))))
			list.append(getConfigListEntry("—"*100))
			if config.plugins.xtrafmEvent.cnfg.value:
				if config.plugins.xtrafmEvent.loc.value:
					list.append(getConfigListEntry("{}".format(lng.get(lang, '3')), config.plugins.xtrafmEvent.loc, _(lng.get(lang, '4'))))
				else:
					list.append(getConfigListEntry("{}{}".format(off_color, lng.get(lang, '3')), config.plugins.xtrafmEvent.loc, _(lng.get(lang, '4'))))
#				list.append(getConfigListEntry(lng.get(lang, '5'), config.plugins.xtrafmEvent.skinSelect, _(lng.get(lang, '19'))))
#				if config.plugins.xtrafmEvent.skinSelect.value == 'skin_1':
#					list.append(getConfigListEntry("   {}".format(lng.get(lang, '69')), config.plugins.xtrafmEvent.skinSelectColor, _(lng.get(lang, '19'))))
				list.append(getConfigListEntry(lng.get(lang, '6'), config.plugins.xtrafmEvent.opt_Images, _(lng.get(lang, '7'))))
				if config.plugins.xtrafmEvent.opt_Images.value:
					list.append(getConfigListEntry("\t{}".format(lng.get(lang, '7')), config.plugins.xtrafmEvent.cnfgSel, _(lng.get(lang, '21'))))
				list.append(getConfigListEntry(lng.get(lang, '22'), config.plugins.xtrafmEvent.apis, _("...")))
				if config.plugins.xtrafmEvent.apis.value:
					list.append(getConfigListEntry("	TMDB API", config.plugins.xtrafmEvent.tmdbAPI, _(lng.get(lang, '23'))))
					list.append(getConfigListEntry("	TVDB API", config.plugins.xtrafmEvent.tvdbAPI, _(lng.get(lang, '23'))))
					list.append(getConfigListEntry("	OMDB API", config.plugins.xtrafmEvent.omdbAPI, _(lng.get(lang, '23'))))
					list.append(getConfigListEntry("	FANART API", config.plugins.xtrafmEvent.fanartAPI, _(lng.get(lang, '23'))))
					list.append(getConfigListEntry("	GOOGLE API", config.plugins.xtrafmEvent.googleAPI, _(lng.get(lang, '23'))))
				list.append(getConfigListEntry("—"*100))
				list.append(getConfigListEntry(lng.get(lang, '8'), config.plugins.xtrafmEvent.searchMOD, _(lng.get(lang, '24'))))		
				list.append(getConfigListEntry(lng.get(lang, '9'), config.plugins.xtrafmEvent.searchNUMBER, _(lng.get(lang, '25'))))
				list.append(getConfigListEntry(lng.get(lang, '10'), config.plugins.xtrafmEvent.searchLang, _(lng.get(lang, '26'))))
				
				list.append(getConfigListEntry(lng.get(lang, '11'), config.plugins.xtrafmEvent.timerMod, _(lng.get(lang, '27'))))
				if config.plugins.xtrafmEvent.timerMod.value:
					if config.plugins.xtrafmEvent.timerMod.value == "Period":
						list.append(getConfigListEntry(lng.get(lang, '46'), config.plugins.xtrafmEvent.timerHour, _(lng.get(lang, '67'))))
					elif config.plugins.xtrafmEvent.timerMod.value == "Clock":
						list.append(getConfigListEntry(lng.get(lang, '46'), config.plugins.xtrafmEvent.timerClock, _(lng.get(lang, '67'))))

					
				list.append(getConfigListEntry("—"*100))
			list.append(getConfigListEntry(" ▀ {}".format(lng.get(lang, '28'))))
			list.append(getConfigListEntry("_"*100))
	# poster__________________________________________________________________________________________________________________
			list.append(getConfigListEntry("POSTER", config.plugins.xtrafmEvent.poster, _("...")))
			if config.plugins.xtrafmEvent.poster.value == True:
				list.append(getConfigListEntry("\tTMDB", config.plugins.xtrafmEvent.tmdb, _(" "),))
				if config.plugins.xtrafmEvent.tmdb.value :
					list.append(getConfigListEntry("\t	Tmdb Poster {}".format(lng.get(lang, '49')), config.plugins.xtrafmEvent.TMDBpostersize, _(" ")))
					list.append(getConfigListEntry("\t	  {}".format(lng.get(lang, '63')), config.plugins.xtrafmEvent.searchType, _(" ")))
				list.append(getConfigListEntry("\tTVDB", config.plugins.xtrafmEvent.tvdb, _(lng.get(lang, '29'))))
				if config.plugins.xtrafmEvent.tvdb.value :
					list.append(getConfigListEntry("\t	Tvdb Poster {}".format(lng.get(lang, '49')), config.plugins.xtrafmEvent.TVDBpostersize, _(" ")))
#				list.append(getConfigListEntry("\tFANART", config.plugins.xtrafmEvent.fanart, _(lng.get(lang, '29'))))	
#				if config.plugins.xtrafmEvent.fanart.value:
#					list.append(getConfigListEntry("\t	Fanart Poster {}".format(lng.get(lang, '49')), config.plugins.xtrafmEvent.FANART_Poster_Resize, _(" ")))
#				list.append(getConfigListEntry("\tMAZE(TV SHOWS)", config.plugins.xtrafmEvent.maze, _(" ")))
				list.append(getConfigListEntry("_"*100))
	# banner__________________________________________________________________________________________________________________
#			list.append(getConfigListEntry("BANNER", config.plugins.xtrafmEvent.banner, _(" ")))
#			if config.plugins.xtrafmEvent.banner.value == True:
#				list.append(getConfigListEntry("\tTVDB", config.plugins.xtrafmEvent.tvdb, _(" ")))
#				if config.plugins.xtrafmEvent.tvdb.value :
#					list.append(getConfigListEntry("\t	Tvdb Banner {}".format(lng.get(lang, '49')), config.plugins.xtrafmEvent.TVDB_Banner_Size, _(" ")))
#				list.append(getConfigListEntry("\tFANART", config.plugins.xtrafmEvent.fanart, _(" ")))
#				if config.plugins.xtrafmEvent.fanart.value :
#					list.append(getConfigListEntry("\t	Fanart Banner {}".format(lng.get(lang, '49')), config.plugins.xtrafmEvent.FANART_Banner_Size, _(" ")))
#				list.append(getConfigListEntry("_"*100))
	# backdrop_______________________________________________________________________________________________________________
			list.append(getConfigListEntry("BACKDROP", config.plugins.xtrafmEvent.backdrop, _(" ")))
			if config.plugins.xtrafmEvent.backdrop.value == True:
				list.append(getConfigListEntry("\tTMDB", config.plugins.xtrafmEvent.tmdb, _(" ")))
				if config.plugins.xtrafmEvent.tmdb.value :
					list.append(getConfigListEntry("\t	Tmdb Backdrop {}".format(lng.get(lang, '49')), config.plugins.xtrafmEvent.TMDBbackdropsize, _(" ")))
					list.append(getConfigListEntry("\t	  {}".format(lng.get(lang, '63')), config.plugins.xtrafmEvent.searchType, _(" ")))
				list.append(getConfigListEntry("\tTVDB", config.plugins.xtrafmEvent.tvdb, _(" ")))
				if config.plugins.xtrafmEvent.tvdb.value :
					list.append(getConfigListEntry("\t	Tvdb Backdrop {}".format(lng.get(lang, '49')), config.plugins.xtrafmEvent.TVDBbackdropsize, _(" ")))
#				list.append(getConfigListEntry("\tFANART", config.plugins.xtrafmEvent.fanart, _(" ")))
#				if config.plugins.xtrafmEvent.fanart.value:
#					list.append(getConfigListEntry("\t	Fanart Backdrop {}".format(lng.get(lang, '49')), config.plugins.xtrafmEvent.FANART_Backdrop_Resize, _(" ")))
				list.append(getConfigListEntry("\tEXTRA", config.plugins.xtrafmEvent.extra, _(lng.get(lang, '30'))))
				list.append(getConfigListEntry("\tBING", config.plugins.xtrafmEvent.extra2, _(lng.get(lang, '31'))))
				list.append(getConfigListEntry("_"*100))
	# info___________________________________________________________________________________________________________________
			list.append(getConfigListEntry("INFO", config.plugins.xtrafmEvent.info, _(lng.get(lang, '32'))))
			# if config.plugins.xtrafmEvent.info.value == True:
				# list.append(getConfigListEntry("\tOMDB", config.plugins.xtrafmEvent.infoOmdb, _(" ")))
				# list.append(getConfigListEntry("\tIMDB", config.plugins.xtrafmEvent.infoImdb, _(" ")))
		# list.append(getConfigListEntry("EXTRA-3", config.plugins.xtrafmEvent.extra3, _(lng.get(lang, '64'))))
			list.append(getConfigListEntry("_"*100))
		else:
			list.append(getConfigListEntry("{}◙ \\c00?????? {}".format(off_color, lng.get(lang, '0')), config.plugins.xtrafmEvent.onoff, _(lng.get(lang, '0'))))

		

		# self["config"].l.setItemHeight(50)
		self["config"].list = list
		self["config"].l.setList(list)
		self.help()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.delay()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.delay()

	def keyDown(self):
		self["config"].instance.moveSelection(self["config"].instance.moveDown)
		self.delay()

	def keyUp(self):
		self["config"].instance.moveSelection(self["config"].instance.moveUp)
		self.delay()

	def pageUp(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)
		self.delay()

	def pageDown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)
		self.delay()

	def help(self):
		cur = self["config"].getCurrent()
		if cur:
			self["help"].text = cur[2]

	def menuS(self):
		if config.plugins.xtrafmEvent.onoff.value:
			list = [(_(lng.get(lang, '50')), self.brokenImageRemove), (_(lng.get(lang, '73')), self.removeImagesAll),\
		    (_(lng.get(lang, '35')), self.exit)]
			self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_('xtrafmEvent...'), list=list)
		else:
			self.exit()

	def update(self):
		try:
#			url = requests.get("https://api.github.com/repos/digiteng/xtra/releases/latest")
			new_version = url.json()["name"]
			if version != new_version:
				msg = url.json()["body"]
				up_msg = "Current version : {}\n\\c00bb?fbbNew version : {} \n\n\\c00bb?fee{}\n\n\\c00??????Do you want UPDATE PLUGIN ?..".format(version, new_version, msg)
				self.session.openWithCallback(self.instalUpdate(url), MessageBox, _(up_msg), MessageBox.TYPE_YESNO)
			else:
				self['info'].setText(lng.get(lang, '71'))
		except Exception as err:
			self['info'].setText(str(err))
			with open("/tmp/xtrafmEvent.log", "a+") as f:
				f.write("update %s\n\n"%err)
				
	def instalUpdate(self, url):
		try:
			update_url = url.json()["assets"][1]["browser_download_url"]
			up_name	 = url.json()["assets"][1]["name"]
			up_tmp = "/tmp/{}".format(up_name)
			if not os.path.exists(up_tmp):
				open(up_tmp, 'wb').write(requests.get(update_url, stream=True, allow_redirects=True).content)
			if os.path.exists(up_tmp):
				from enigma import eConsoleAppContainer
				cmd = ("rm -rf /usr/lib/enigma2/python/Components/Converter/xtra* \
				| rm -rf /usr/lib/enigma2/python/Components/Renderer/xtra* \
				| rm -rf /usr/lib/enigma2/python/Plugins/Extensions/xtrafmEvent \
				| rm -rf /usr/share/enigma2/xtra \
				")
				os.system(cmd)
				# os.popen(cmd)
				container = eConsoleAppContainer()
				container.execute("tar xf /tmp/xtrafmEvent.tar.gz -C /")
				self.updateFinish()

		except Exception as err:
			self['info'].setText(str(err))
			with open("/tmp/xtrafmEvent.log", "a+") as f:
				f.write("instalUpdate %s\n\n"%err)

	def updateFinish(self):
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		configfile.save()
		self.session.openWithCallback(self.restarte2, MessageBox, _(lng.get(lang, '70')), MessageBox.TYPE_YESNO)

	def restarte2(self, answer):
		if answer:
			self.session.open(TryQuitMainloop, 3)

	def removeImagesAll(self):
		self.session.openWithCallback(self.removeImagesAllYes, MessageBox, _(lng.get(lang, '70')), MessageBox.TYPE_YESNO)
		
	def removeImagesAllYes(self, answer):
		if answer:
			import shutil
			shutil.rmtree(pathLoc)
			self['info'].setText(lng.get(lang, '74'))

	def compressImg(self):
		try:
			filepath = "{}{}".format(pathLoc, config.plugins.xtrafmEvent.cnfgSel.value)
			folder_size = sum([sum([os.path.getsize(os.path.join(filepath, fname)) for fname in files]) for filepath, folders, files in os.walk(filepath)])
			old_size = "%0.1f" % (folder_size//1024)
			if os.path.exists(filepath):
				lstdr = os.listdir(filepath)
				for j in lstdr:
					try:
						filepath = "".join([filepath, "/", j])
						if os.path.isfile(filepath):
							im = Image.open(filepath)
							im.save(filepath, optimize=True, quality=80)
					except:
						pass
				folder_size = sum([sum([os.path.getsize(os.path.join(filepath, fname)) for fname in files]) for filepath, folders, files in os.walk(filepath)])
				new_size = "%0.1f" % (folder_size//1024)
				self['info'].setText(_("{} images optimization end...\nGain : {}KB to {}KB".format(len(lstdr), old_size, new_size)))
		except Exception as err:
			with open("/tmp/xtrafmEvent.log", "a+") as f:
				f.write("compressImg, %s\n"%(err))
			self['info'].setText(str(err))


	def brokenImageRemove(self):
		b = os.listdir(pathLoc)
		rmvd = 0
		try:
			for i in b:
				bb = "{}{}/".format(pathLoc, i)
				fc = os.path.isdir(bb)
				if fc != False:	
					for f in os.listdir(bb):
						if f.endswith('.jpg'):
							try:
								img = Image.open("{}{}".format(bb, f))
								img.verify()
							except:
								try:
									os.remove("{}{}".format(bb, f))
									rmvd += 1
								except:
									pass
		except:
			pass
		self['info'].setText(_("Removed Broken Images : {}".format(str(rmvd))))

	def menuCallback(self, ret = None):
		ret and ret[1]()

	def search(self):
		if config.plugins.xtrafmEvent.onoff.value:
			if pathLoc != "":
				from . import download
				if config.plugins.xtrafmEvent.searchMOD.value == lng.get(lang, '14'):
					self.session.open(download.downloads)
				if config.plugins.xtrafmEvent.searchMOD.value == lng.get(lang, '13'):
					self.session.open(selBouquets)
				elif config.plugins.xtrafmEvent.searchMOD.value == lng.get(lang, '14a'):
					self.session.open(selBouquets)
			else:
				self.session.open(MessageBox, _(lng.get(lang, '4')), MessageBox.TYPE_INFO, timeout = 10)
				self.session.open(selBouquets)
		else:
			self.exit()

	def ms(self):
		if config.plugins.xtrafmEvent.onoff.value:
			if pathLoc != "":
				self.session.open(manuelSearch)
			else:
				self.session.open(MessageBox, _(lng.get(lang, '4')), MessageBox.TYPE_INFO, timeout = 10)
		else:
			self.exit()

	def exit(self):
		if self['config'].getCurrent()[1] is config.plugins.xtrafmEvent.skinSelectColor or self['config'].getCurrent()[1] is config.plugins.xtrafmEvent.skinSelect:
			from Plugins.Extensions.xtrafmEvent.skins import xtrafmSkins
			from six.moves import reload_module
			reload_module(xtrafmSkins)
			for x in self["config"].list:
				if len(x)>1:
					x[1].save()
				configfile.save()
			self.close()
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		configfile.save()
		try:
			if config.plugins.xtrafmEvent.timerMod.value == "Clock":
				tc = config.plugins.xtrafmEvent.timerClock.value
				dt = datetime.today()
				setclk = dt.replace(day=dt.day+1, hour=tc[0], minute=tc[1], second=0, microsecond=0)
				ds = setclk - dt
				secs = ds.seconds + 1
				def startDownload():
					from . import download
					download.downloads("").save()

				t = Timer(secs, startDownload)
				t.start()
			self.close()
		except Exception as err:
			with open("/tmp/xtrafmEvent.log", "a+") as f:
				f.write("timer clock, %s\n"%(err))
	
class manuelSearch(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		if desktop_size <= 1280:
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_1':
				self.skin = manuel_720
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_2':
				self.skin = manuel_720_2
		else:
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_1':
				self.skin = manuel_1080
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_2':
				self.skin = manuel_1080_2
		self.title = ""
		self.year = ""
		self.evnt = ""
		list = []
		ConfigListScreen.__init__(self, list, session=session)
		self.setTitle(_(lng.get(lang, '18')))
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_(lng.get(lang, '40')))
		self["key_yellow"] = StaticText(_(lng.get(lang, '65')))
		self["key_blue"] = StaticText(_("Keyboard"))
		self["actions"] = ActionMap(["xtrafmEventAction"],
			{
				"left": self.keyLeft,
				"right": self.keyRight,
				"cancel": self.close,
				"red": self.close,
				"ok": self.keyOK,
				"green": self.mnlSrch,
				"yellow": self.append,
				"blue": self.vk
			}, -2)
		self['status'] = Label()
		self['info'] = Label()
		self['Picture'] = Pixmap()
		self['Picture2'] = Pixmap()
		self['int_statu'] = Label()
		self['progress'] = ProgressBar()
		self['progress'].setRange((0, 100))
		self['progress'].setValue(0)		

		self.timer = eTimer()
		self.timer.callback.append(self.msList)
		self.timer.callback.append(self.picShow)
		self.onLayoutFinish.append(self.msList)
		self.onLayoutFinish.append(self.intCheck)

	def intCheck(self):
		try:
			socket.setdefaulttimeout(2)
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
			self['int_statu'].setText("☻")
			return True
		except:
			self['int_statu'].hide()
			self['status'].setText(lng.get(lang, '68'))
			return False

	def keyOK(self):
		if self['config'].getCurrent()[1] is config.plugins.xtrafmEvent.EMCloc:
			self.session.openWithCallback(self.pathSelected, LocationBox, text=_('Default Folder'), currDir=config.plugins.xtrafmEvent.EMCloc.getValue(), minFree=100)

	def pathSelected(self, res):
		if res is not None:
			config.plugins.xtrafmEvent.EMCloc.value = res
			pathLoc = config.plugins.xtrafmEvent.EMCloc.value
		return

	def delay(self):
		self.timer.start(100, True)

	def msList(self):
		self["Picture2"].instance.setPixmapFromFile("/usr/lib/enigma2/python/Plugins/Extensions/xtrafmEvent/pic/film2.png")
		self["Picture2"].instance.setScale(1)
		self["Picture2"].show()
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		list = []
		list.append(getConfigListEntry(_(lng.get(lang, '59')), config.plugins.xtrafmEvent.searchModManuel))
		list.append(getConfigListEntry(_(lng.get(lang, '57')), config.plugins.xtrafmEvent.searchMANUELnmbr))
		if config.plugins.xtrafmEvent.searchModManuel.value == lng.get(lang, '17'):
			list.append(getConfigListEntry(_(lng.get(lang, '60')), config.plugins.xtrafmEvent.EMCloc))
		list.append(getConfigListEntry(_("Year"), config.plugins.xtrafmEvent.searchMANUELyear))
		list.append(getConfigListEntry(_(lng.get(lang, '10')), config.plugins.xtrafmEvent.searchLang))
		list.append(getConfigListEntry(_(lng.get(lang, '61')), config.plugins.xtrafmEvent.PB))
		list.append(getConfigListEntry(_(lng.get(lang, '62')), config.plugins.xtrafmEvent.srcs))
		if config.plugins.xtrafmEvent.srcs.value == "TMDB":
			list.append(getConfigListEntry(_(lng.get(lang, '63')), config.plugins.xtrafmEvent.searchType))
			if config.plugins.xtrafmEvent.PB.value == "posters":
				list.append(getConfigListEntry(_("\t{}".format(lng.get(lang, '49'))), config.plugins.xtrafmEvent.TMDBpostersize))
			else:
				list.append(getConfigListEntry(_("\t{}".format(lng.get(lang, '49'))), config.plugins.xtrafmEvent.TMDBbackdropsize))
		if config.plugins.xtrafmEvent.srcs.value == "TVDB":
			if config.plugins.xtrafmEvent.PB.value == "posters":
				list.append(getConfigListEntry(_("\t{}".format(lng.get(lang, '49'))), config.plugins.xtrafmEvent.TVDBpostersize))
			else:
				list.append(getConfigListEntry(_("\t{}".format(lng.get(lang, '49'))), config.plugins.xtrafmEvent.TVDBbackdropsize))
		if config.plugins.xtrafmEvent.srcs.value == "FANART":
			list.append(getConfigListEntry(_("\tSearch Type"), config.plugins.xtrafmEvent.FanartSearchType))
			if config.plugins.xtrafmEvent.PB.value == "posters":
				list.append(getConfigListEntry(_("\t{}".format(lng.get(lang, '49'))), config.plugins.xtrafmEvent.FANART_Poster_Resize))
			else:
				list.append(getConfigListEntry(_("\t{}".format(lng.get(lang, '49'))), config.plugins.xtrafmEvent.FANART_Backdrop_Resize))
		if config.plugins.xtrafmEvent.srcs.value == "IMDB(poster)":
			list.append(getConfigListEntry(_("\t{}".format(lng.get(lang, '49'))), config.plugins.xtrafmEvent.imdb_Poster_size))
		list.append(getConfigListEntry("—"*50))
		list.append(getConfigListEntry(_(lng.get(lang, '58')), config.plugins.xtrafmEvent.imgNmbr))
		list.append(getConfigListEntry("—"*50))
		self["config"].list = list
		self["config"].l.setList(list)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		if self['config'].getCurrent()[0] == lng.get(lang, '57'):
			self.curEpg()
		self.delay()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		if self['config'].getCurrent()[0] == lng.get(lang, '57'):
			self.curEpg()
		self.delay()

	def curEpg(self):
		if config.plugins.xtrafmEvent.searchModManuel.value == lng.get(lang, '16'):
			try:
				events = ""
				ref = self.session.nav.getCurrentlyPlayingServiceReference().toString()
				events = epgcache.lookupEvent(['IBDCTSERNX', (ref, 1, -1, -1)])
				if events:
					n = config.plugins.xtrafmEvent.searchMANUELnmbr.value
					self.evnt = events[int(n)][4]
					self.vkEdit("")
			except:
				pass
		if config.plugins.xtrafmEvent.searchModManuel.value == lng.get(lang, '17'):
			self.movieList()

	def movieList(self):
		pathLoc = config.plugins.xtrafmEvent.EMCloc.value
		try:
			mlst = os.listdir(pathLoc)
			if mlst:
				movieList = [x for x in mlst if x.endswith(".mvi") or x.endswith(".ts") or x.endswith(".mp4") or x.endswith(".avi") or x.endswith(".mkv") or x.endswith(".divx")]
				if movieList:
					n = config.plugins.xtrafmEvent.searchMANUELnmbr.value
					self.evnt = movieList[int(n)]
					self.vkEdit("")
		except:
			pass

	def vk(self):
		self.session.openWithCallback(self.vkEdit, VirtualKeyBoard, title=lng.get(lang, '39'), text = self.evnt)

	def vkEdit(self, text=None):
		if text:
			config.plugins.xtrafmEvent.searchMANUEL = ConfigText(default="{}".format(text), visible_width=100, fixed_size=False)
			config.plugins.xtrafmEvent.searchMANUEL_EMC = ConfigText(default="{}".format(text), visible_width=100, fixed_size=False)
			if config.plugins.xtrafmEvent.searchModManuel.value == lng.get(lang, '16'):
				self.title = config.plugins.xtrafmEvent.searchMANUEL.value
			if config.plugins.xtrafmEvent.searchModManuel.value == lng.get(lang, '17'):
				self.title = config.plugins.xtrafmEvent.searchMANUEL_EMC.value
				self.title = self.title.split('-')[-1].split(".")[0].strip()
			self['status'].setText(_("Buscar : {}".format(str(self.title))))
		else:
			config.plugins.xtrafmEvent.searchMANUEL = ConfigText(default="{}".format(self.evnt), visible_width=100, fixed_size=False)
			config.plugins.xtrafmEvent.searchMANUEL_EMC = ConfigText(default="{}".format(self.evnt), visible_width=100, fixed_size=False)
			if config.plugins.xtrafmEvent.searchModManuel.value == lng.get(lang, '16'):
				self.title = config.plugins.xtrafmEvent.searchMANUEL.value
			if config.plugins.xtrafmEvent.searchModManuel.value == lng.get(lang, '17'):
				self.title = config.plugins.xtrafmEvent.searchMANUEL_EMC.value
				self.title = self.title.split('-')[-1].split(".")[0].strip()
			self['status'].setText(_("Buscar : {}".format(str(self.title))))

	def mnlSrch(self):
		try:
			fs = os.listdir("{}mSearch/".format(pathLoc))
			for f in fs:
				os.remove("{}mSearch/{}".format(pathLoc, f))
		except:
			return
		if config.plugins.xtrafmEvent.PB.value == "posters":
			if config.plugins.xtrafmEvent.srcs.value == "TMDB":
				start_new_thread(self.tmdb, ())
			if config.plugins.xtrafmEvent.srcs.value == "TVDB":
				start_new_thread(self.tvdb, ())
			if config.plugins.xtrafmEvent.srcs.value == "FANART":
				start_new_thread(self.fanart, ())
			if config.plugins.xtrafmEvent.srcs.value == "IMDB(poster)":
				start_new_thread(self.imdb, ())
			if config.plugins.xtrafmEvent.srcs.value == "Bing":
				start_new_thread(self.bing, ())
			if config.plugins.xtrafmEvent.srcs.value == "Google":
				start_new_thread(self.google, ())
		if config.plugins.xtrafmEvent.PB.value == "backdrops":
			if config.plugins.xtrafmEvent.srcs.value == "TMDB":
				start_new_thread(self.tmdb, ())
			if config.plugins.xtrafmEvent.srcs.value == "TVDB":
				start_new_thread(self.tvdb, ())
			if config.plugins.xtrafmEvent.srcs.value == "FANART":
				start_new_thread(self.fanart, ())
			if config.plugins.xtrafmEvent.srcs.value == "Bing":
				start_new_thread(self.bing, ())
			if config.plugins.xtrafmEvent.srcs.value == "Google":
				start_new_thread(self.google, ())


	def picShow(self):
		self["Picture2"].hide()
		try:
			self.iNmbr = config.plugins.xtrafmEvent.imgNmbr.value
			sanitized_title = self.title.replace(":", "")
			self.path = "{}mSearch/{}-{}-{}.jpg".format(pathLoc, sanitized_title, config.plugins.xtrafmEvent.PB.value, self.iNmbr)
			
			if config.plugins.xtrafmEvent.srcs.value == "IMDB(poster)":
				self.path = "{}mSearch/{}-poster-1.jpg".format(pathLoc, sanitized_title)
			
			self["Picture"].instance.setPixmap(loadJPG(self.path))
			self["Picture"].instance.setScale(1)
			self["Picture"].show()
			if desktop_size <= 1280:
				if config.plugins.xtrafmEvent.PB.value == "posters":
					self["Picture"].instance.setScale(1)
					self["Picture"].instance.resize(eSize(185,278))
					self["Picture"].instance.move(ePoint(930,325))
				else:
					self["Picture"].instance.setScale(1)
					self["Picture"].instance.resize(eSize(300,170))
					self["Picture"].instance.move(ePoint(890,375))
			else:
				if config.plugins.xtrafmEvent.PB.value == "posters":
					self["Picture"].instance.setScale(1)
					self["Picture"].instance.resize(eSize(185,278))
					self["Picture"].instance.move(ePoint(1450,550))
				else:
					self["Picture"].instance.setScale(1)
					self["Picture"].instance.resize(eSize(300,170))
					self["Picture"].instance.move(ePoint(1400,600))				
			self['Picture'].show()
			self.inf()
		except:
			pass

	def inf(self):
		pb_path = ""
		pb_sz = ""
		tot = ""
		cur = ""
		try:
			msLoc = "{}mSearch/".format(pathLoc)
			n = 0
			for file in os.listdir(msLoc):
				if file.startswith("{}-{}".format(self.title, config.plugins.xtrafmEvent.PB.value)) == True:
					e = os.path.join(msLoc, file)
					n += 1
			tot = n
			cur = config.plugins.xtrafmEvent.imgNmbr.value
			pb_path = "{}mSearch/{}-{}-{}.jpg".format(pathLoc , self.title, config.plugins.xtrafmEvent.PB.value, self.iNmbr)
			pb_sz = "{} KB".format(os.path.getsize(pb_path)//1024)
			im = Image.open(pb_path)
			pb_res = im.size
			self['info'].setText(_("{}/{} - {} - {}".format(cur, tot, pb_sz, pb_res)))
		except:
			pass

	def append(self):
		try:
			self.title = self.title
			filepath = "/usr/lib/enigma2/python/Plugins/Extensions/PermanentEvent"
			targetp = ""
			sanitized_title = self.title.replace(":", "")
			if config.plugins.xtrafmEvent.PB.value == "posters":
				if config.plugins.xtrafmEvent.srcs.value == "bing":
					target = "{}poster/{}.jpg".format(pathLoc, sanitized_title)
				if config.plugins.xtrafmEvent.searchModManuel.value == lng.get(lang, '16'):
					target = "{}poster/{}.jpg".format(pathLoc, sanitized_title)
				else:
					target = "{}EMC/{}-poster.jpg".format(pathLoc, sanitized_title)
			else:
				if config.plugins.xtrafmEvent.searchModManuel.value == lng.get(lang, '16'):
					target = "{}backdrop/{}.jpg".format(pathLoc, sanitized_title)
					if os.path.exists(filepath):
						pathperma = config.plugins.PermanentEvent.loc.value
						targetp = "{}PermanentEvent/backdrop/{}.jpg".format(pathperma, sanitized_title)
					if config.plugins.xtrafmEvent.srcs.value == "bing":
						evntNm = re.sub("([\(\[]).*?([\)\]])|(: odc.\d+)|(\d+: odc.\d+)|(\d+ odc.\d+)|(:)|( -(.*?).*)|(,)|!|\*", "", sanitized_title).rstrip()
						target = "{}backdrop/{}.jpg".format(pathLoc, evntNm)
						if os.path.exists(filepath):
							pathperma = config.plugins.PermanentEvent.loc.value
							targetp = "{}PermanentEvent/backdrop/{}.jpg".format(pathperma, evntNm)
				else:
					target = "{}EMC/{}-backdrop.jpg".format(pathLoc, sanitized_title)
					if os.path.exists(filepath):
						pathperma = config.plugins.PermanentEvent.loc.value
						targetp = "{}PermanentEvent/backdrop/{}.jpg".format(pathperma, sanitized_title)
			import shutil
			if os.path.exists(self.path):
				print(f"Copying files from {self.path} to {target}")
				shutil.copyfile(self.path, target)
				if os.path.exists(target):
					print(f"File successfully copied to {target}")
					if config.plugins.xtrafmEvent.PB.value == "backdrops" and not config.plugins.xtrafmEvent.searchModManuel.value == lng.get(lang, '16'):
						print(f"Processing image to {target}")
			if targetp and os.path.exists(filepath):
				print(f"Copying files from {self.path} to {targetp}")
				shutil.copyfile(self.path, targetp)
				print(f"File successfully copied to {targetp}")
			self['status'].setText("Image copied successfully...")
			if os.path.exists(filepath):
				self['status'].setText("Image copied successfully...")
		except Exception as e:
			print(f"Error in the function append: {e}")
			return

	def tmdb(self):
		self['progress'].setValue(0)
		try:
			self.srch = config.plugins.xtrafmEvent.searchType.value
			self.year = config.plugins.xtrafmEvent.searchMANUELyear.value
			from requests.utils import quote
			url = "https://api.themoviedb.org/3/search/{}?api_key={}&query={}".format(self.srch, tmdb_api, quote(self.title))
			if self.year != "0":
				if config.plugins.xtrafmEvent.searchType.value == "tv":
					url += "&first_air_date_year={}".format(self.year)
				elif config.plugins.xtrafmEvent.searchType.value == "movie":
					url += "&year={}".format(self.year)
			id = requests.get(url).json()['results'][0]['id']
			url = "https://api.themoviedb.org/3/{}/{}?api_key={}&append_to_response=images".format(self.srch, int(id), tmdb_api)
			if config.plugins.xtrafmEvent.searchLang.value:
				url += "&language={}".format(lang)
			if config.plugins.xtrafmEvent.PB.value == "posters":
				sz = config.plugins.xtrafmEvent.TMDBpostersize.value
			else:
				sz = config.plugins.xtrafmEvent.TMDBbackdropsize.value
			p1 = requests.get(url).json()
			pb_no = p1['images'][config.plugins.xtrafmEvent.PB.value]
			n = len(pb_no)
			if n > 0:
				downloaded = 0
				for i in range(int(n)):
					poster = p1['images'][config.plugins.xtrafmEvent.PB.value][i]['file_path']
					if poster:
						url_poster = "https://image.tmdb.org/t/p/{}{}".format(sz, poster)
						dwnldFile = "{}mSearch/{}-{}-{}.jpg".format(pathLoc, self.title, config.plugins.xtrafmEvent.PB.value, i+1)
						open(dwnldFile, 'wb').write(requests.get(url_poster, stream=True, allow_redirects=True).content)
						downloaded += 1
						self.prgrs(downloaded, n)
			else:
				self['status'].setText(_("Image not found..."))
			config.plugins.xtrafmEvent.imgNmbr.value = 0
		except Exception as err:
			with open("/tmp/xtrafmEvent.log", "a+") as f:
				f.write("Manuel Search tmdb , %s, %s\n"%(self.title, err))
			self['status'].setText(_("Image not found..."))

	def tvdb(self):
		self['progress'].setValue(0)
		try:
			self.srch = config.plugins.xtrafmEvent.searchType.value
			self.year = config.plugins.xtrafmEvent.searchMANUELyear.value
			from requests.utils import quote
			url = "https://thetvdb.com/api/GetSeries.php?seriesname={}".format(quote(self.title))
			if self.year != 0:
				url += "%20{}".format(self.year)
			url_read = requests.get(url).text
			series_id = re.findall('<seriesid>(.*?)</seriesid>', url_read)[0]
			if config.plugins.xtrafmEvent.PB.value == "posters":
				keyType = "poster"
			else:
				keyType = "fanart"
			url = 'https://api.thetvdb.com/series/{}/images/query?keyType={}'.format(series_id, keyType)
			if config.plugins.xtrafmEvent.searchLang.value:
				try:
					u = requests.get(url, headers={"Accept-Language":"{}".format(lang)})
					u.raise_for_status()
#					print(u.text)
				except Exception as e:
					print(f"Error in request to {url}: {e}")
					self['status'].setText(_("Image not found..."))
					return
			try:
				pb_no = u.json()["data"]
				n = len(pb_no)
			except:
				self['status'].setText(_("Image not found..."))
				return
			if n > 0:
				downloaded = 0
				for i in range(int(n)):
					if config.plugins.xtrafmEvent.PB.value == "posters":
						img_pb = u.json()["data"][i]['{}'.format(config.plugins.xtrafmEvent.TVDBpostersize.value)]
					else:
						img_pb = u.json()["data"][i]['{}'.format(config.plugins.xtrafmEvent.TVDBbackdropsize.value)]
					url = "https://artworks.thetvdb.com/banners/{}".format(img_pb)
					dwnldFile = "{}mSearch/{}-{}-{}.jpg".format(pathLoc, self.title, config.plugins.xtrafmEvent.PB.value, i+1)
					open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
					downloaded += 1
					self.prgrs(downloaded, n)
			else:
				self['status'].setText(_("Image not found..."))
			config.plugins.xtrafmEvent.imgNmbr.value = 0
		except Exception as err:
			print(f"Function error tvdb: {err}")
			self['status'].setText(_("Image not found..."))
			return

	def fanart(self):
		id = "-"
		from requests.utils import quote
		image_found = False
		if config.plugins.xtrafmEvent.FanartSearchType.value == "tv":
			try:
				url_maze = "http://api.tvmaze.com/singlesearch/shows?q={}".format(quote(self.title))
				mj = requests.get(url_maze).json()
				id = (mj['externals']['thetvdb'])
			except Exception as err:
				with open("/tmp/xtrafmEvent.log", "a+") as f:
					f.write("fanart maze man.search, %s, %s\n"%(self.title, err))
		else:
			try:
				self.year = config.plugins.xtrafmEvent.searchMANUELyear.value
				url = "https://api.themoviedb.org/3/search/movie?api_key={}&query={}".format(tmdb_api, quote(self.title))
				if self.year != 0:
					url += "&primary_release_year={}&year={}".format(self.year, self.year)
				id = requests.get(url).json()['results'][0]['id']
			except Exception as err:
				with open("/tmp/xtrafmEvent.log", "a+") as f:
					f.write("fanart tvdb id man.search, %s, %s\n"%(self.title, err))
		try:
			m_type = config.plugins.xtrafmEvent.FanartSearchType.value
			url_fanart = "https://webservice.fanart.tv/v3/{}/{}?api_key={}".format(m_type, id, fanart_api)
			fjs = requests.get(url_fanart, verify=False, timeout=5).json()
			if config.plugins.xtrafmEvent.PB.value == "posters":
				if config.plugins.xtrafmEvent.FanartSearchType.value == "tv":
					pb_no = fjs['tvposter']
					n = len(pb_no)
				else:
					pb_no = fjs['movieposter']
					n = len(pb_no)
			elif config.plugins.xtrafmEvent.PB.value == "backdrops":
				if config.plugins.xtrafmEvent.FanartSearchType.value == "tv":
					pb_no = fjs['showbackground']
					n = len(pb_no)
				else:
					pb_no = fjs['moviebackground']
					n = len(pb_no)
			if n > 0:
				downloaded = 0
				for i in range(int(n)):
					try:
						if config.plugins.xtrafmEvent.PB.value == "posters":
							if config.plugins.xtrafmEvent.FanartSearchType.value == "tv":
								url = (fjs['tvposter'][i]['url'])
							else:
								url = (fjs['movieposter'][i]['url'])
						if config.plugins.xtrafmEvent.PB.value == "backdrops":
							if config.plugins.xtrafmEvent.FanartSearchType.value == "tv":
								url = (fjs['showbackground'][i]['url'])
							else:
								url = (fjs['moviebackground'][i]['url'])
						open("/tmp/url","a+").write("%s\n"%url)		
						dwnldFile = "{}mSearch/{}-{}-{}.jpg".format(pathLoc, self.title, config.plugins.xtrafmEvent.PB.value, i+1)
						open(dwnldFile, 'wb').write(requests.get(url, verify=False).content)
						downloaded += 1
						self.prgrs(downloaded, n)
						scl = 1
						im = Image.open(dwnldFile)
						if config.plugins.xtrafmEvent.PB.value == "posters":
							scl = config.plugins.xtrafmEvent.FANART_Poster_Resize.value
						if config.plugins.xtrafmEvent.PB.value == "backdrops":
							scl = config.plugins.xtrafmEvent.FANART_Backdrop_Resize.value
						im1 = im.resize((im.size[0] // int(scl), im.size[1] // int(scl)), Image.LANCZOS)
						im1.save(dwnldFile)
						image_found = True
					except Exception as err:
						with open("/tmp/xtrafmEvent.log", "a+") as f:
							f.write("fanart man.search save, %s, %s\n"%(self.title, err))
				self['status'].setText(_(lng.get(lang, '56')))
			config.plugins.xtrafmEvent.imgNmbr.value = 0
		except Exception as err:
			with open("/tmp/xtrafmEvent.log", "a+") as f:
				f.write("fanart man.search2, %s, %s\n"%(self.title, err))
		if image_found:
			self.prgrs(downloaded, n)
		else:
			self['status'].setText(_("Image not found..."))

	def imdb(self):
		downloaded = 0
		try:
			from requests.utils import quote
			sanitized_title = self.title.replace(":", "")
			url_find = 'https://m.imdb.com/find?q={}'.format(quote(sanitized_title))
			print(f"URL_FIND: {url_find}")
			headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
			response = requests.get(url_find, headers=headers)
			response.raise_for_status()
			ff = response.text
			start_index = ff.find('"url":"')
			end_index = ff.find('"', start_index + 7)
			json_fragment = ff[start_index + 7:end_index]
#			print(f"JSON_FRAGMENT: {json_fragment}")
			url = json_fragment
			if config.plugins.xtrafmEvent.PB.value == "posters" and url:
				dwnldFile = "{}mSearch/{}-poster-1.jpg".format(pathLoc, sanitized_title)
				open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
				downloaded += 1
				n = 1
				self.prgrs(downloaded, n)
			else:
				self['status'].setText(_("Download : No"))
			config.plugins.xtrafmEvent.imgNmbr.value = 0
		except requests.exceptions.RequestException as e:
#			print(f"Error in making the request: {e}")
			with open("/tmp/xtrafmEvent.log", "a+") as f:
				f.write("imdb, %s, %s, %s\n" % (sanitized_title, url_find, e))
			self['status'].setText(_("Image not found..."))

	def bing(self):
		try:
			url = "https://www.bing.com/images/search?q={}".format(self.title.replace(" ", "+"))
			if config.plugins.xtrafmEvent.PB.value == "posters":
				url += "+poster"
			else:
				url += "+backdrop"
			headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
			try:
				ff = requests.get(url, stream=True, headers=headers).text
				p = re.findall('ihk=\"\/th\?id=(.*?)&', ff)
			except:
				pass
			n = 9
			downloaded = 0
			for i in range(n):
				try:
					url = re.findall(',&quot;murl&quot;:&quot;(.*?)&', ff)[i]
					dwnldFile = "{}mSearch/{}-{}-{}.jpg".format(pathLoc, self.title, config.plugins.xtrafmEvent.PB.value, i+1)
					open(dwnldFile, 'wb').write(requests.get(url, stream=True, allow_redirects=True).content)
					downloaded += 1
					self.prgrs(downloaded, n)
				except:
					pass
			config.plugins.xtrafmEvent.imgNmbr.value = 0
		except Exception as err:
			self['status'].setText(_(str(err)))

	def google(self):
		try:
			query = self.title.replace(" ", "+")
			search_type = "poster" if config.plugins.xtrafmEvent.PB.value == "posters" else "backdrop"
			cx = "d4ac56566a5fc488c"
			url = f"https://www.googleapis.com/customsearch/v1?q={query}+{search_type}&key={google_api}&cx={cx}&searchType=image"
			print("APIKEYUSADA", url)
			headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
			try:
				response = requests.get(url, headers=headers)
				if response.status_code == 200:
					items = response.json().get("items", [])
					image_links = [item["link"] for item in items]
					n = 9
					downloaded = 0
					for i in range(n):
						try:
							image_url = image_links[i]
							download_file = f"{pathLoc}/mSearch/{self.title}-{config.plugins.xtrafmEvent.PB.value}-{i+1}.jpg"
							open(download_file, 'wb').write(requests.get(image_url, stream=True, allow_redirects=True).content)
							downloaded += 1
							self.prgrs(downloaded, n)
						except Exception as e:
							print(f"Error when downloading image {i+1}: {e}")
					config.plugins.xtrafmEvent.imgNmbr.value = 0
				else:
					print(f"Error in request to API: {response.status_code}")
			except Exception as e:
				print(f"Error when searching the API de Google: {e}")
		except Exception as err:
			self['status'].setText(_(str(err)))
			return

	def prgrs(self, downloaded, n):
		self['status'].setText("Download : {} / {}".format(downloaded, n))
		self['progress'].setValue(int(100*downloaded//n))

class selBouquets(Screen):
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		
		if desktop_size <= 1280:
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_1':
				self.skin = selbuq_720
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_2':
				self.skin = selbuq_720_2
		else:
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_1':
				self.skin = selbuq_1080
			if config.plugins.xtrafmEvent.skinSelect.value == 'skin_2':
				self.skin = selbuq_1080_2

		try:
			if config.plugins.xtrafmEvent.searchMOD.value == lng.get(lang, '13'):
				sl = self.getBouquetList()
			elif config.plugins.xtrafmEvent.searchMOD.value == lng.get(lang, '14a'):
				sl = self.getProviderList()
			else:
				pass
			list = []
			for i in sl:
				list.append(xtraSelectionEntryComponent(i[0], 1, 0, 0))
			self["list"] = xtraSelectionList(list)
		except:
			return
			
		self["list"].l.setItemHeight(70)
		self["actions"] = ActionMap(["xtrafmEventAction"],
			{
				"cancel": self.cancel,
				"red": self.close,
				"green": self.bqtinchannels,
				"yellow": self["list"].toggleSelection,
				"blue": self["list"].toggleAllSelection,
				"ok": self["list"].toggleSelection
			}, -1)
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Save"))
		self["key_yellow"] = Label(_(lng.get(lang, '43')))
		self["key_blue"] = Label(_(lng.get(lang, '44')))
		self.setTitle(_(lng.get(lang, '55')))
		self['status'] = Label()
		self['info'] = Label()

	def getBouquetList(self):
		try:
			bouquets = []
			service_types_tv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 22) || (type == 25) || (type == 31) || (type == 134) || (type == 195)'
			serviceHandler = eServiceCenter.getInstance()
			if config.usage.multibouquet.value:
				bouquet_root = eServiceReference('1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet')
				list = serviceHandler.list(bouquet_root)
				if list:
					while True:
						s = list.getNext()
						if not s.valid():
							break
						if s.flags & eServiceReference.isDirectory and not s.flags & eServiceReference.isInvisible:
							info = serviceHandler.info(s)
							if info:
								bouquets.append((info.getName(s), s))
					return bouquets
			else:
				bouquet_root = '%s FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet'%(service_types_tv)
				info = serviceHandler.info(bouquet_root)
				if info:
					bouquets.append((info.getName(bouquet_root), bouquet_root))
				return bouquets
			return None
		except Exception as err:
			with open("/tmp/xtrafmEvent.log", "a+") as f:
				f.write("getBouquetList, %s\n"%(err))

	def getProviderList(self):
		try:
			service_types_tv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 22) || (type == 25) || (type == 31) || (type == 134) || (type == 195)'
			self.root = eServiceReference('%s FROM PROVIDERS ORDER BY name' % (service_types_tv))
			serviceHandler = eServiceCenter.getInstance()
			services = serviceHandler.list(eServiceReference(self.root))
			providers = services and services.getContent("NS", True)

			plists = []
			for provider in providers:
				plists.append(provider)
			return plists
			
		except Exception as err:
			with open("/tmp/xtrafmEvent.log", "a+") as f:
				f.write("getProviderList, %s\n"%(err))
		
	def buqChList(self, bqtNm):
		try:
			channels = []
			serviceHandler = eServiceCenter.getInstance()
			chlist = serviceHandler.list(eServiceReference('1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet'))
			if chlist :
				while True:
					chh = chlist.getNext()
					if not chh.valid(): break
					info = serviceHandler.info(chh)
					if chh.flags & eServiceReference.isDirectory:
						info = serviceHandler.info(chh)
					if info.getName(chh) in bqtNm:
						chlist = serviceHandler.list(chh)
						while True:
							chhh = chlist.getNext()
							if not chhh.valid(): break
							channels.append((chhh.toString()))
				# open("/tmp/chList", "w").write(str(channels))
				return channels
			return
		except Exception as err:
			with open("/tmp/xtrafmEvent.log", "a+") as f:
				f.write("chList Bouquet, %s\n"%(err))

	def provChList(self, prvNm):
		try:
			service_types_tv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 22) || (type == 25) || (type == 31) || (type == 134) || (type == 195)'
			channels = []
			serviceHandler = eServiceCenter.getInstance()
			chlist = serviceHandler.list(eServiceReference('%s FROM PROVIDERS ORDER BY name' % (service_types_tv)))
			if chlist :
				while True:
					chh = chlist.getNext()
					if not chh.valid(): break
					info = serviceHandler.info(chh)
					if chh.flags & eServiceReference.isDirectory:
						info = serviceHandler.info(chh)
					if info.getName(chh) in prvNm:
						chlist = serviceHandler.list(chh)
						while True:
							chhh = chlist.getNext()
							if not chhh.valid(): break
							channels.append((chhh.toString()))
				# open("/tmp/chList", "w").write(str(channels))
				return channels
			return
		except Exception as err:
			with open("/tmp/xtrafmEvent.log", "a+") as f:
				f.write("chList Bouquet, %s\n"%(err))

	def bqtinchannels(self):
		try:
			if os.path.exists("{}bqts".format(pathLoc)):
				os.remove("{}bqts".format(pathLoc))

			bE = "{}bqts".format(pathLoc)
			blist = []
			for idx,item in enumerate(self["list"].list):
				item = self["list"].list[idx][0]
				if item[3]:
					blist.append(item[0])
			for p in blist:
				
				if config.plugins.xtrafmEvent.searchMOD.value == lng.get(lang, '13'):
					refs = self.buqChList(p)
					for ref in refs:
						open(bE, "a+").write("{}\n".format(ref))

				elif config.plugins.xtrafmEvent.searchMOD.value == lng.get(lang, '14a'):
					refs = self.provChList(p)
					for ref in refs:
						open(bE, "a+").write("{}\n".format(ref))

			else:
				list = [(_(lng.get(lang, '53')), self.withPluginDownload), (_(lng.get(lang, '54')), self.withTimerDownload), (_(lng.get(lang, '35')), self.cancel)]
				self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_('Download ?'), list=list)
		except Exception as err:
			with open("/tmp/xtrafmEvent.log", "a+") as f:
				f.write("bqtinchannels, %s\n"%(err))

	def withPluginDownload(self):
		from . import download
		self.session.open(download.downloads)

	def withTimerDownload(self):
		if config.plugins.xtrafmEvent.timerMod.value == False:
			self.session.open(MessageBox, _(lng.get(lang, '52')), MessageBox.TYPE_INFO, timeout = 10)
		else:
			self.session.openWithCallback(self.restart, MessageBox, _(lng.get(lang, '47')), MessageBox.TYPE_YESNO, timeout = 20)

	def menuCallback(self, ret = None):
		ret and ret[1]()

	def restart(self, answer):
		if answer is True:
			configfile.save()
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()

	def cancel(self):
		self.close(self.session, False)
