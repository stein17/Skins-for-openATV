# -*- coding: utf-8 -*-
# by digiteng...07.2021, 
# 08.2021(stb lang support),
# 09.2021 mini fixes
# © Provided that digiteng rights are protected, all or part of the code can be used, modified...
# russian and py3 support by sunriser...
# downloading in the background while zaping...
# by beber...03.2022,
# 03.2022 specific for EMC plugin ...
#
# for emc plugin,
# <widget source="Service" render="GradientiPosterXEMC" position="100,100" size="185,278" />

from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, eTimer, loadJPG, eEPGCache

from ServiceReference import ServiceReference
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.CurrentService import CurrentService
from Components.Sources.EventInfo import EventInfo
from Components.Sources.Event import Event

from Components.Renderer.GradientiPosterXDownloadThread import GradientiPosterXDownloadThread

import NavigationInstance
import os
import sys
import re
import time
import socket

PY3 = (sys.version_info[0] == 3)
try:
	if PY3:
		import queue
		from _thread import start_new_thread
	else:
		import Queue
		from thread import start_new_thread
except:
	pass

epgcache = eEPGCache.getInstance()
try:
	from Components.config import config
	lng = config.osd.language.value
except:
	lng = None
	pass

path_folder = ""
if os.path.isdir("/media/hdd"):
	path_folder = "/media/hdd/imovie/"
elif not os.path.isdir("/media/usb"):
	path_folder = "/media/usb/imovie/"
else:
	path_folder = "/tmp/imovie/"


if PY3:
	pdbemc = queue.LifoQueue()
else:
	pdbemc = Queue.LifoQueue()

class PosterDBEMC(GradientiPosterXDownloadThread):
	def __init__(self):
		GradientiPosterXDownloadThread.__init__(self)
		self.logdbg = None
			
	def run(self):
		self.logDB("[QUEUE] : Initialized")
		while True:
			canal = pdbemc.get()
			self.logDB("[QUEUE] : {} : {}-{} ({})".format(canal[0],canal[1],canal[2],canal[5]))
			if os.path.exists(canal[5]):
				os.utime(canal[5], (time.time(), time.time()))
			if lng == "fr_FR":
				if not os.path.exists(canal[5]):
					val, log = self.search_molotov_google(canal[5],canal[2],canal[4],canal[3],canal[0])
					self.logDB(log)
				if not os.path.exists(canal[5]):
					val, log = self.search_programmetv_google(canal[5],canal[2],canal[4],canal[3],canal[0])
					self.logDB(log)
			if not os.path.exists(canal[5]):
				val, log = self.search_imdb(canal[5],canal[2],canal[4],canal[3])		
				self.logDB(log)	
			if not os.path.exists(canal[5]):
				val, log = self.search_tmdb(canal[5],canal[2],canal[4],canal[3])		
				self.logDB(log)	
			if not os.path.exists(canal[5]):
				val, log = self.search_tvdb(canal[5],canal[2],canal[4],canal[3])		
				self.logDB(log)	
			if not os.path.exists(canal[5]):
				val, log = self.search_google(canal[5],canal[2],canal[4],canal[3],canal[0])
				self.logDB(log)
			pdbemc.task_done()

	def logDB(self, logmsg):
		if self.logdbg:
			w = open(path_folder + "GradientiPosterXEMC.log", "a+")
			w.write("%s\n"%logmsg)
			w.close()

threadDBemc = PosterDBEMC()
threadDBemc.start()
			
class GradientiPosterXEMC(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.canal = [None,None,None,None,None,None]
		self.intCheck()
		self.timer = eTimer()
		self.timer.callback.append(self.showPoster)
		self.logdbg = None

	def applySkin(self, desktop, parent):
		attribs = []
		for (attrib, value,) in self.skinAttributes:
			attribs.append((attrib, value))
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)
		
	def intCheck(self):
		try:
			socket.setdefaulttimeout(1)
			socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
			return True
		except:
			return
			
	GUI_WIDGET = ePixmap
	def changed(self, what):
		if not self.instance:
			return
		if what[0] == self.CHANGED_CLEAR:
			self.instance.hide()
		if what[0] != self.CHANGED_CLEAR:
			try:
				if isinstance(self.source, ServiceEvent): # source="Service"
					self.canal[0] = None
					self.canal[1] = self.source.event.getBeginTime()
					self.canal[2] = self.source.event.getEventName()
					self.canal[3] = self.source.event.getExtendedDescription()
					self.canal[4] = self.source.event.getShortDescription()
					self.canal[5] = self.source.service.getPath().split(".ts")[0]+".jpg"
				elif isinstance(self.source, CurrentService): # source="session.CurrentService"
					self.canal[0] = None
					self.canal[1] = None
					self.canal[2] = None
					self.canal[3] = None
					self.canal[4] = None
					self.canal[5] = self.source.getCurrentServiceReference().getPath().split(".ts")[0]+".jpg"
				else:
					self.logPoster("Service : Others")
					self.canal = [None,None,None,None,None,None]
					self.instance.hide()
					return
			except Exception as e:
				self.logPoster("Error (service) : "+str(e))
				self.instance.hide()
				return
			try:
				cn = re.findall(".*? - (.*?) - (.*?).jpg",self.canal[5])
				if cn and len(cn)>0 and len(cn[0])>1:
					self.canal[0] = cn[0][0].strip()
					if not self.canal[2]:
						self.canal[2] = cn[0][1].strip()
				self.logPoster("Service : {} - {} => {}".format(self.canal[0],self.canal[2],self.canal[5])) 
				if os.path.exists(self.canal[5]):
					self.timer.start(100, True)
				elif self.canal[0] and self.canal[2]:
					self.logPoster("Downloading poster...")
					canal = self.canal[:]
					pdbemc.put(canal)
					start_new_thread(self.waitPoster, ())
				else:
					self.logPoster("Not detected...")
					self.instance.hide()
					return
			except Exception as e:
				self.logPoster("Error (reading file) : "+str(e))
				self.instance.hide()
				return
				
			
	def showPoster(self):
		self.instance.hide()
		if self.canal[5]:
			if os.path.exists(self.canal[5]):
				self.logPoster("[LOAD : showPoster] {}".format(self.canal[5]))
				self.instance.setPixmap(loadJPG(self.canal[5]))
				self.instance.setScale(2)
				self.instance.show()
			
	def waitPoster(self):
		self.instance.hide()
		if self.canal[5]:
			loop = 180
			found = None
			self.logPoster("[LOOP : waitPoster] {}".format(self.canal[5]))
			while loop>=0:
				if os.path.exists(self.canal[5]):
					if os.path.getsize(self.canal[5]) > 0:
						loop = 0
						found = True
				time.sleep(0.5)
				loop = loop - 1
			if found:
				self.timer.start(10, True)		

	def logPoster(self, logmsg):
		if self.logdbg:
			w = open(path_folder + "GradientiPosterXEMC.log", "a+")
			w.write("%s\n"%logmsg)
			w.close()		
		
