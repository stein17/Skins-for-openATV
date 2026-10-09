from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from Components.Element import cached
import NavigationInstance


class GradientFHDDVBIInfo(Poll, Converter):
	def __init__(self, type):
		Poll.__init__(self)
		Converter.__init__(self, type)
		self.poll_interval = 1000
		self.poll_enabled = True

	@cached
	def getBoolean(self):
		nav = NavigationInstance.instance
		return bool(nav and getattr(nav, "isCurrentServiceDVBI", False))

	boolean = property(getBoolean)
