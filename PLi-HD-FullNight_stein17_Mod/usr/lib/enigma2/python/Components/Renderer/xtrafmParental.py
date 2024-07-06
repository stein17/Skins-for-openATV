# -*- coding: utf-8 -*-
# by digiteng...
# 07.2020 - 11.2020 - 11.2021
#ChannelSelection
# <widget source="session.Event_Now" render="xtrafmParental"  position="0,0" size="60,60" alphatest="blend" zPosition="2" transparent="1" />
#Second -InfoBar
#<widget source="session.Event_Now" render="xtrafmParental" position="1306,568" size="60,60" alphatest="blend" zPosition="5" transparent="1" />
#<widget source="session.Event_Next" render="xtrafmParental" position="715,831" size="60,60" alphatest="blend" zPosition="5" transparent="1" />
    
#Movieselection
#<widget source="Service" render="xtrafmParental" position="1253,905" size="60,60" alphatest="blend" zPosition="12" transparent="1" />
      
#EPG Eventview
#<widget source="Event" render="xtrafmParental" position="1242,770" size="60,60" alphatest="blend" zPosition="3" transparent="1" />
from __future__ import absolute_import
from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, loadPNG
from Components.config import config
import re
import json
import os

try:
	import sys
	if sys.version_info[0] == 3:
		from builtins import str
except:
	pass

pratePath = "/usr/lib/enigma2/python/Plugins/Extensions/xtrafmEvent/pic/parental/"
try:
	pathLoc = config.plugins.xtrafmEvent.loc.value
except:
	pathLoc = ""

REGEX = re.compile(
		r'([\(\[]).*?([\)\]])|'
		r'(: odc.\d+)|'
		r'(\d+: odc.\d+)|'
		r'(\d+ odc.\d+)|(:)|'
		r'( -(.*?).*)|(,)|'
		r'!|'
		r'/.*|'
		r'\|\s[0-9]+\+|'
		r'[0-9]+\+|'
		r'\s\d{4}\Z|'
		r'([\(\[\|].*?[\)\]\|])|'
		r'(\"|\"\.|\"\,|\.)\s.+|'
		r'\"|:|'
		r'\*|'
		r'Премьера\.\s|'
		r'(х|Х|м|М|т|Т|д|Д)/ф\s|'
		r'(х|Х|м|М|т|Т|д|Д)/с\s|'
		r'\s(с|С)(езон|ерия|-н|-я)\s.+|'
		r'\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
		r'\.\s\d{1,3}\s(ч|ч\.|с\.|с)\s.+|'
		r'\s(ч|ч\.|с\.|с)\s\d{1,3}.+|'
		r'\d{1,3}(-я|-й|\sс-н).+|', re.DOTALL)

class xtrafmParental(Renderer):

	def __init__(self):
		Renderer.__init__(self)
		self.rateNm = ''

	GUI_WIDGET = ePixmap
	def changed(self, what):
		if not self.instance:
			return
		else:
			rate = ""
			prate = ""
			parentName = ""
			event = self.source.event
			if event:
				fd = "{}{}{}".format(event.getEventName(), event.getShortDescription(), event.getExtendedDescription())
				ppr = ["[aA]b ((\d+))", "[+]((\d+))", "Od lat: ((\d+))"]
				for i in ppr:
					prr = re.search(i, fd)
					if prr:
						try:
							parentName = prr.group(1)
							parentName = parentName.replace("7", "6")
							break
						except:
							pass
				else:
					evnt = event.getEventName()
					evntNm = REGEX.sub('', evnt).strip()
					rating_json = "{}xtrafmEvent/infos/{}.json".format(pathLoc, evntNm)
					if os.path.exists(rating_json):
						try:
							with open(rating_json) as f:
								prate = json.load(f)['Rated']
						except:
							pass

					if prate == "TV-Y7":
						rate = "6"
					elif prate == "TV-Y":
						rate = "6"
					elif prate == "TV-14":
						rate = "12"
					elif prate == "TV-PG":
						rate = "16"
					elif prate == "TV-G":
						rate = "0"
					elif prate == "TV-MA":
						rate = "18"
					elif prate == "PG-13":
						rate = "16"
					elif prate == "R":
						rate = "18"
					elif prate == "G":
						rate = "0"
					else:
						pass
					if rate:	
						parentName = str(rate)

				if parentName:
					rateNm = "{}FSK_{}.png".format(pratePath, parentName)
					self.instance.setPixmap(loadPNG(rateNm))
					self.instance.setScale(1)
					self.instance.show()
				else:
					self.instance.setPixmap(loadPNG("{}FSK_NA.png".format(pratePath)))
					self.instance.setScale(1)
					self.instance.show()
			else:
				self.instance.setPixmap(loadPNG("FSK_NA.png".format(pratePath)))
				self.instance.setScale(1)
				self.instance.show()				
			return
