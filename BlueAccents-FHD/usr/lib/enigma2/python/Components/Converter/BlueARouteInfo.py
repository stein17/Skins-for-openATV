# -*- coding: utf-8 -*-

#  RouteInfo Converter
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

# RouteInfo
# Copyright (c) 2boom 2012-13
# v.0.8
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from Components.Converter.Converter import Converter
from Components.Element import cached
from Tools.Directories import fileExists
from Screens.InfoBar import InfoBar
from Components.Converter.Poll import Poll
from Plugins.Extensions.BlueAccentsFHD import ping

infotext = ""

class BlueARouteInfo(Poll, Converter, object):
	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)
		self.poll_interval = 1000
		self.poll_enabled = True
		self.type = type
		self.info = False
		InfoBar.instance.onShow.append(self.checkState)
		InfoBar.instance.onHide.append(self.writeFile)

	@cached
	def getBoolean(self):
		return self.info

	boolean = property(getBoolean)

	def checkState(self):
		global infotext
		self.info = False

		try:
			r = ping.doOne("8.8.8.8", 1.5)
			if r != None and r <= 1.5:
				for line in open("/proc/net/route"):
					if self.type == "Lan" and line.split()[0] == "eth0" and line.split()[3] == "0003":
						infotext = "Lan"
						self.info = True
					elif self.type == "Wifi" and (line.split()[0] == "wlan0" or line.split()[0] == "ra0") and line.split()[3] == "0003":
						infotext = "Wifi"
						self.info = True
		except:
			pass

	def writeFile(self):
		global infotext

		open("/tmp/sib_routeinfo", 'a').close()
		with open("/tmp/sib_routeinfo", 'w') as wf:
			wf.write(infotext)
