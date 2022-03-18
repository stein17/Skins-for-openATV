#!/usr/bin/python
# -*- coding: utf-8 -*-
from Components.Renderer.Renderer import Renderer
from enigma import iServiceInformation
from enigma import ePixmap
from Tools.Directories import fileExists, SCOPE_GUISKIN, SCOPE_SKINS, resolveFilename
from Components.Converter.Poll import Poll

class BlueApiconEmu(Renderer, Poll):
	__module__ = __name__
	searchPaths = ('/usr/share/enigma2/%s/', '/usr/share/enigma2/BlueAccents-HD/%s/', '/media/sde1/%s/', '/media/cf/%s/', '/media/sdd1/%s/', '/media/hdd/%s/', '/media/usb/%s/', '/media/ba/%s/', '/mnt/ba/%s/', '/media/sda/%s/', '/etc/%s/')
	
	def __init__(self):
		Poll.__init__(self)
		Renderer.__init__(self)
		self.path = 'emu'
		self.nameCache = {}
		self.pngname = ''
		self.picon_default = "picon_default.png"
		
	def applySkin(self, desktop, parent):
		attribs = []
		for (attrib, value,) in self.skinAttributes:
			if (attrib == 'path'):
				self.path = value
			elif (attrib == 'picon_default'):
				self.picon_default = value
			else:
				attribs.append((attrib, value))
				
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)
		
	GUI_WIDGET = ePixmap
	
	def changed(self, what):
		self.poll_interval = 2000
		self.poll_enabled = True
		if self.instance:
			pngname = ''
			if (what[0] != self.CHANGED_CLEAR):
				cfgfile = "/tmp/ecm.info"
				sname = ""
				service = self.source.service
				if service:
					info = (service and service.info())
					if info:
						caids = info.getInfoObject(iServiceInformation.sCAIDs)    
						try:
							f = open(cfgfile, "r")
							content = f.read()
							f.close()
						except:
							content = ""
						contentInfo = content.split("\n")
						for line in contentInfo:
								if ("using" in line):
										sname = "CCcam"
								elif ("source" in line):
										sname = "Mgcamd"
								elif ("reader" in line):
										sname = "oscam"
								elif ("response time" in line):
										sname = "Wicardd"
								elif ("decode" in line):
										sname = "Gbox"
								elif ("CAID" in line):
										sname = "Camd3"
						if caids:
							if (len(caids) > 0):
								for caid in caids:
									caid = self.int2hex(caid)
									if (len(caid) == 3):
										caid = ("0%s" % caid)
									caid = caid[:2]
									caid = caid.upper()
									if (caid != "") and (sname == ""):
										sname = "Unknown"

			pngname = self.nameCache.get(sname, '')
			if (pngname == ''):
				pngname = self.findPicon(sname)
				if (pngname != ''):
					self.nameCache[sname] = pngname

			if (pngname == ''):
				pngname = self.nameCache.get('Fta', '')
				if (pngname == ''):
					pngname = self.findPicon('Fta')
					if (pngname == ''):
						tmp = resolveFilename(SCOPE_GUISKIN, 'picon_default.png')
						if fileExists(tmp):
							pngname = tmp
						else:
							pngname = resolveFilename(SCOPE_SKINS, 'skin_default/picon_default.png')
						self.nameCache['default'] = pngname
					
			if (self.pngname != pngname):
				self.pngname = pngname
				self.instance.setPixmapFromFile(self.pngname)

	def int2hex(self, int):
		return ("%x" % int)
				
	def findPicon(self, serviceName):
		for path in self.searchPaths:
			pngname = (((path % self.path) + serviceName) + '.png')
			if fileExists(pngname):
				return pngname
		return ''
