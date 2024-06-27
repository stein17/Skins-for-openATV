# -*- coding: utf-8 -*-
# by digiteng...07.2020 - 08.2020 - 10.2021
# <widget source="Service" render="xtraEmcPoster" delayPic="500" position="0,0" size="185,278" zPosition="0"
from __future__ import absolute_import
from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, loadJPG
import os
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.CurrentService import CurrentService
from Components.config import config
import re

try:
	pathLoc = config.plugins.xtrafmEvent.loc.value
	
except:
	pathLoc = ""
	

REGEX = re.compile(
		r'([\(\[]).*?([\)\]])|'
		r'(: odc.\d+)|'
		r'(\d+: odc.\d+)|'
		r'(\d+ odc.\d+)|(:)|'
		
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
		
class xtrafmEmcPoster(Renderer):

	def __init__(self):
		Renderer.__init__(self)
		self.piconsize = (0,0)

	GUI_WIDGET = ePixmap
	def changed(self, what):
		if not self.instance:
			return
		else:
			if what[0] != self.CHANGED_CLEAR:
				
				movieNm = ""
				try:
					service = self.source.getCurrentService()
					if service:
						evnt = service.getPath()
						movieNm = evnt.split('-')[-1].split(".")[0].strip()
						movieNm = REGEX.sub('', movieNm).strip()
						pstrNm = "{}xtrafmEvent/EMC/{}-poster.jpg".format(pathLoc, movieNm.strip())
						if os.path.exists(pstrNm):
							self.instance.setScale(1)
							self.instance.setPixmap(loadJPG(pstrNm))
							self.instance.show()
						else:
							self.instance.hide()
					else:
						self.instance.hide()
				except:
					pass
			else:
				self.instance.hide()
				return
					