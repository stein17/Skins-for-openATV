from time import localtime
from enigma import eLabel, eEPGCache
from Components.Renderer.Renderer import Renderer
from Components.VariableText import VariableText


class BLSingleEpgList(Renderer, VariableText):
	GUI_WIDGET = eLabel
	DEFAULT_MAX_EVENTS = 8

	def __init__(self):
		self.maxEvents = self.DEFAULT_MAX_EVENTS
		Renderer.__init__(self)
		VariableText.__init__(self)
		self.epgcache = eEPGCache.getInstance()

	def applySkin(self, desktop, parent):
		attribs = []
		configuredMaxEvents = None
		widgetHeight = None
		fontSize = None

		for (attrib, value) in self.skinAttributes:
			if attrib == "maxEvents":
				try:
					configuredMaxEvents = int(value)
				except (TypeError, ValueError):
					configuredMaxEvents = None
				continue
			elif attrib == "size":
				try:
					widgetHeight = int(value.split(",", 1)[1].strip())
				except (IndexError, TypeError, ValueError):
					widgetHeight = None
			elif attrib == "font":
				try:
					fontSize = int(value.rsplit(";", 1)[1].strip())
				except (IndexError, TypeError, ValueError):
					fontSize = None

			attribs.append((attrib, value))

		if configuredMaxEvents and configuredMaxEvents > 0:
			self.maxEvents = configuredMaxEvents
		elif widgetHeight and fontSize and widgetHeight > 0 and fontSize > 0:
			self.maxEvents = max(1, widgetHeight // fontSize)
		else:
			self.maxEvents = self.DEFAULT_MAX_EVENTS

		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	def changed(self, what):
		event = self.source.event
		text = []
		if event:
			service = self.source.service
			if self.epgcache:
				events = self.epgcache.lookupEvent(["IBDCT", (service.toString(), 0, -1, -1)])
				if events:
					for epgEvent in events[1:1 + self.maxEvents]:
						if epgEvent[4]:
							localTime = localtime(epgEvent[1])
							text.append(f"{localTime[3]:02d}:{localTime[4]:02d} {epgEvent[4]}")
						else:
							text.append("N/A")

		self.text = "\n".join(text)
