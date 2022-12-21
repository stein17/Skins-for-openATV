# -*- coding: utf-8 -*-

#  RouteInfoSIB Converter
#
#  Coded/Modified/Adapted by oerlgrey
#  Based on openATV image source code
#
#  This code is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ 
#  or send a letter to Creative Commons, 559 Nathan 
#  Abbott Way, Stanford, California 94305, USA.
#
#  If you think this license infringes any rights,
#  please contact me at ochzoetna@gmail.com

from Components.Converter.Converter import Converter
from Components.Element import cached
from Tools.Directories import fileExists
from Components.Converter.Poll import Poll

class BlueARouteInfoSIB(Poll, Converter, object):
	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)
		self.poll_interval = 1000
		self.poll_enabled = True
		self.type = type

	@cached
	def getBoolean(self):
		if fileExists("/tmp/sib_routeinfo"):
			file = open("/tmp/sib_routeinfo", 'r')
			for line in file:
				if line == "Lan" and self.type == "Lan":
					return True
				elif line == "Wifi" and self.type == "Wifi":
					return True
		else:
			return False

	boolean = property(getBoolean)
