from Components.Converter.Converter import Converter
from Components.Element import cached
from enigma import eTimer
from socket import socket, AF_INET, SOCK_STREAM


class BlueANetConnection(Converter, object):
	def __init__(self, type):
		Converter.__init__(self, type)
		self.testOK    = False
		self.testTime  = 1.0		# 1 seconds
		self.testPause = 10		# 10 seconds
		self.testHost  = "77.88.21.3"	# www.yandex.ru
		self.testPort  = 80		# www port
		
		if len(type):
			p = type[:].find("://")
			if p != -1:
				type = type[p+3:]
			type = type[:].split(":")
			if len(type[0]) > 0:
				self.testHost = type[0]
			if len(type) > 1 and type[1].isdigit():
				self.testPort = int(type[1])
			if len(type) > 2 and type[2].isdigit():
				self.testPause = max(1, int(type[2]))
			
		self.testTimer = eTimer()
		self.testTimer.callback.append(self.test)
		self.testTimer.start(100, True) 

	def test(self):
		s = socket(AF_INET, SOCK_STREAM)
		s.settimeout(self.testTime)
		try:
			self.testOK = not bool(s.connect_ex((self.testHost, self.testPort)))
		except:
			self.testOK = False
		s.close()
		self.testTimer.start(self.testPause * 1000, True)

	@cached
	def getBoolean(self):
		return self.testOK

	boolean = property(getBoolean)
