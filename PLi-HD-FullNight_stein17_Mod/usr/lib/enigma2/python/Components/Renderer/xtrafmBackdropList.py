# -*- coding: utf-8 -*-
# by digiteng...11.2021, 12.2021
# for channellist,
# <widget source="ServiceEvent" render="xtraBackdropList" mode="trio" position="651,517" size="600,150" backgroundColor="background" zPosition="99" />
# mode="trio" or mode="single"
from __future__ import absolute_import
from Components.Renderer.Renderer import Renderer
from enigma import ePoint, eWidget, eLabel, eSize, gFont, ePixmap, loadJPG, eEPGCache, eTimer
from Components.config import config
from skin import parseColor
import re
import os
import json
from time import localtime

try:
	import sys
	if sys.version_info[0] == 3:
		from builtins import str
except:
	pass

NoImage = "/usr/lib/enigma2/python/Plugins/Extensions/xtrafmEvent/pic/film.jpg"

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
		
class xtrafmBackdropList(Renderer):

	def __init__(self):
		Renderer.__init__(self)
		self.fontSize = 24
		self.epgcache = eEPGCache.getInstance()
		self.timer = eTimer()
		self.timer.callback.append(self.showImages)
		
	def applySkin(self, desktop, screen):
		attribs = self.skinAttributes[:]
		for attrib, value in self.skinAttributes:
			if attrib == 'position':
				self.px = int(value.split(',')[0])
				self.py = int(value.split(',')[1])
			elif attrib == 'size':
				self.szX = int(value.split(',')[0])
				self.szY = int(value.split(',')[1])
			elif attrib == 'backgroundColor':
				self.backgroundColor = value
			elif attrib == 'mode':
				self.mode = value
			elif attrib == 'fontSize':
				self.fontSize = int(value)
			
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, screen)


	GUI_WIDGET = eWidget
	def changed(self, what):
		if not self.instance:
			return
		else:
			if what[0] != self.CHANGED_CLEAR:
				self.timer.start(500, True)

	def showImages(self):
		evnt = ''
		pstrNm = ''
		evntNm = ''
		ref = ''
		events = None
		ref = self.source.service
		events = self.epgcache.lookupEvent(['IBDCT', (ref.toString(), 0, -1, 480)])
		px, py = self.szX // 3, self.szY - (self.szY // 4)
		nx, ny = px, self.szY // 4
		
		if self.mode == "trio":
			if self.epgcache is not None and events:
				try:
					# event 1
					evnt = events[1][4]
					evntNm = REGEX.sub('', evnt).strip()
					bt = localtime(events[1][1])
					evntNm1 = "%02d:%02d - %s\n"%(bt[3], bt[4], evnt)
					pstrNm = "{}xtrafmEvent/backdrop/{}.jpg".format(pathLoc, evntNm)

					if os.path.exists(pstrNm):
						self.eventPxmp1.setPixmap(loadJPG(pstrNm))
						self.eventPxmp1.resize(eSize(px, py))
						self.eventPxmp1.move(ePoint(0,0))
						self.eventPxmp1.setTransparent(0)
						self.eventPxmp1.setZPosition(9)
						self.eventPxmp1.setScale(1)
						self.eventPxmp1.show()

					else:
						self.eventPxmp1.setPixmap(loadJPG(NoImage))

					self.eventName1.setText(str(evntNm1))
					self.eventName1.setBackgroundColor(parseColor(self.backgroundColor))
					self.eventName1.resize(eSize(nx, ny))
					self.eventName1.move(ePoint(0, py+5))
					self.eventName1.setFont(gFont("xtraRegular", self.fontSize))
					self.eventName1.setHAlign(eLabel.alignLeft)
					self.eventName1.setTransparent(0)
					self.eventName1.setZPosition(99)
					self.eventName1.show()
				except:
					self.eventPxmp1.hide()
					self.eventName1.hide()
				try:
					# event 2
					evnt = events[2][4]
					evntNm = REGEX.sub('', evnt).strip()
					bt = localtime(events[2][1])
					evntNm2 = "%02d:%02d - %s\n"%(bt[3], bt[4], evnt)
					pstrNm = "{}xtrafmEvent/backdrop/{}.jpg".format(pathLoc, evntNm)
					if os.path.exists(pstrNm):
						self.eventPxmp2.setPixmap(loadJPG(pstrNm))
						self.eventPxmp2.resize(eSize(px, py))
						self.eventPxmp2.move(ePoint((px) + 5, 0))
						self.eventPxmp2.setTransparent(0)
						self.eventPxmp2.setZPosition(3)
						self.eventPxmp2.setScale(1)
						self.eventPxmp2.show()

					else:
						self.eventPxmp2.setPixmap(loadJPG(NoImage))

					self.eventName2.setText(str(evntNm2))
					self.eventName2.setBackgroundColor(parseColor(self.backgroundColor))
					self.eventName2.resize(eSize(nx, ny))
					self.eventName2.move(ePoint(px + 5, py+5))
					self.eventName2.setFont(gFont("xtraRegular", self.fontSize))
					self.eventName2.setHAlign(eLabel.alignLeft)
					self.eventName2.setTransparent(0)
					self.eventName2.setZPosition(99)
					self.eventName2.show()
				except:
					self.eventPxmp2.hide()
					self.eventName2.hide()
				try:
					# event 3
					evnt = events[3][4]
					evntNm = REGEX.sub('', evnt).strip()
					bt = localtime(events[3][1])
					evntNm3 = "%02d:%02d - %s\n"%(bt[3], bt[4], evnt)
					pstrNm = "{}xtrafmEvent/backdrop/{}.jpg".format(pathLoc, evntNm)
					if os.path.exists(pstrNm):
						self.eventPxmp3.setPixmap(loadJPG(pstrNm))
						self.eventPxmp3.resize(eSize(px, py))
						self.eventPxmp3.move(ePoint(((px)*2) + 10, 0))
						self.eventPxmp3.setTransparent(0)
						self.eventPxmp3.setZPosition(3)
						self.eventPxmp3.setScale(1)
						self.eventPxmp3.show()

					else:
						self.eventPxmp3.setPixmap(loadJPG(NoImage))

					self.eventName3.setText(str(evntNm3))
					self.eventName3.setBackgroundColor(parseColor(self.backgroundColor))
					self.eventName3.resize(eSize(nx, ny))
					self.eventName3.move(ePoint(((px)*2) + 10, py+5))
					self.eventName3.setFont(gFont("xtraRegular", self.fontSize))
					self.eventName3.setHAlign(eLabel.alignLeft)
					self.eventName3.setTransparent(0)
					self.eventName3.setZPosition(99)
					self.eventName3.show()

				except:
					self.eventPxmp3.hide()
					self.eventName3.hide()
			else:
				self.eventPxmp1.hide()
				self.eventPxmp2.hide()
				self.eventPxmp3.hide()
				self.eventName1.hide()
				self.eventName2.hide()
				self.eventName3.hide()
		elif self.mode == "single":
			if self.epgcache is not None and events:
				evnt=[]
				event = events[1][4]
				evntNm = REGEX.sub('', event).strip()
				bt = localtime(events[1][1])
				et = localtime(events[1][1] + events[1][2])
				rating_json = "{}xtrafmEvent/infos/{}.json".format(pathLoc, evntNm)
				if os.path.exists(rating_json):
					with open(rating_json) as f:
						read_json = json.load(f)
				try:
					Genre = read_json["Genre"]
					if Genre:
						Genre = Genre.split(",")
						evnt.append("{}".format(Genre[0]))
				except:
					pass
				try:
					year = read_json["Year"]
					if year:
						evnt.append("{}".format(year))
				except:
					pass

				try:
					Rated = read_json["Rated"]
					if Rated != "Not Rated":
						evnt.append("{}+".format(Rated))
				except:
					pass
				try:
					imdbRating = read_json["imdbRating"]
					if imdbRating:
						# evnt.append("\\c00????00")
						evnt.append('\\c00????00▐ \\c00??????{}'.format(imdbRating))
				except:
					pass
				duration = ""
				try:
					duration = "%d min" % (events[1][2] // 60)
				except:
					pass


				tc = '\\c0000???? • '
				tc += '\\c00??????'
				tc = tc.join(evnt)

				evntNm1 = "%02d:%02d - %02d:%02d \n%s\n%s\n%s"%(bt[3], bt[4], et[3], et[4], event, tc, duration)
				pstrNm = "{}xtrafmEvent/backdrop/{}.jpg".format(pathLoc, evntNm)
				if os.path.exists(pstrNm):
					self.eventPxmp1.setPixmap(loadJPG(pstrNm))
					self.eventPxmp1.resize(eSize(px, py))
					self.eventPxmp1.move(ePoint(0,0))
					self.eventPxmp1.setTransparent(0)
					self.eventPxmp1.setZPosition(9)
					self.eventPxmp1.setScale(1)
					self.eventPxmp1.show()
				else:
					self.eventPxmp1.setPixmap(loadJPG(NoImage))
					
				self.eventName1.setText(str(evntNm1))
				self.eventName1.setBackgroundColor(parseColor(self.backgroundColor))
				self.eventName1.resize(eSize((px)*2, self.szY))
				self.eventName1.move(ePoint((px) + 10, 0))
				self.eventName1.setFont(gFont("xtraRegular", self.fontSize))
				self.eventName1.setHAlign(eLabel.alignLeft)
				self.eventName1.setTransparent(0)
				self.eventName1.setZPosition(99)
				self.eventName1.show()
			else:
				self.eventPxmp1.hide()
				self.eventName1.hide()								

	def GUIcreate(self, parent):
		self.instance = eWidget(parent)
		self.eventName1 = eLabel(self.instance)
		self.eventName2 = eLabel(self.instance)
		self.eventName3 = eLabel(self.instance)
		self.eventPxmp1 = ePixmap(self.instance)
		self.eventPxmp2 = ePixmap(self.instance)
		self.eventPxmp3 = ePixmap(self.instance)

