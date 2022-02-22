# AlwaysTrue by 2boom 2012 v.0.1

from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Converter.Poll import Poll

class AMBAlwaysTrue(Poll, Converter, object):

	def __init__(self, type):
		Poll.__init__(self)
		Converter.__init__(self, type)
		self.poll_interval = 1000
		self.poll_enabled = True

	@cached
	def getBoolean(self):
		return True
		
	boolean = property(getBoolean)

	def changed(self, what):
		Converter.changed(self, what)


