# -*- coding: utf-8 -*-
from Components.Renderer.Renderer import Renderer
from enigma import ePixmap

class PliModSambaVpnIp_renderer(Renderer):
	def __init__(self):
		Renderer.__init__(self)

	GUI_WIDGET = ePixmap

	def postWidgetCreate(self, instance):
		self.changed((self.CHANGED_DEFAULT,))

	def changed(self, what):
		if what[0] != self.CHANGED_CLEAR:
			if self.source and hasattr(self.source, "pixmap"):
				if self.instance:
					self.instance.setScale(1)
					self.instance.setPixmap(self.source.pixmap)
