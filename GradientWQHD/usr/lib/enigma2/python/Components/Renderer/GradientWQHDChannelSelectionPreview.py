from os.path import getmtime, isfile, join
from xml.etree.ElementTree import parse

from Components.config import config
from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, eTimer


class GradientWQHDChannelSelectionPreview(Renderer):
	"""Display a preview only for compatible ChannelSelection screen/list pairs."""

	GUI_WIDGET = ePixmap

	def __init__(self):
		Renderer.__init__(self)
		self.previewPath = "/usr/share/enigma2/GradientWQHD/preview/channelselection"
		self.templateFile = "/usr/share/enigma2/GradientWQHD/skinTemplates.xml"
		self.interval = 250
		self.showAfterChange = True
		self.templates = {}
		self.templateMtime = None
		self.lastState = None
		self.currentPreview = None
		self.activated = False
		self.timer = eTimer()
		self.timerConnection = None
		self.timerConnected = False

	def applySkin(self, desktop, parent):
		attributes = []
		for attribute, value in self.skinAttributes:
			if attribute == "previewPath":
				self.previewPath = value.rstrip("/")
			elif attribute == "templateFile":
				self.templateFile = value
			elif attribute == "interval":
				try:
					self.interval = max(200, int(value))
				except (TypeError, ValueError):
					pass
			elif attribute == "showAfterChange":
				self.showAfterChange = str(value).lower() not in ("0", "false", "no", "off")
			else:
				attributes.append((attribute, value))
		self.skinAttributes = attributes
		return Renderer.applySkin(self, desktop, parent)

	def postWidgetCreate(self, instance):
		Renderer.postWidgetCreate(self, instance)
		try:
			instance.setScale(1)
		except Exception:
			pass
		self._connectTimer()
		self._loadTemplates(force=True)
		self.lastState = self._getState()
		self.activated = not self.showAfterChange
		self._update()
		self._startTimer()

	def preWidgetRemove(self, instance):
		self._stopTimer()
		Renderer.preWidgetRemove(self, instance)

	def onShow(self):
		self._startTimer()
		self._update()

	def onHide(self):
		self._stopTimer()

	def changed(self, what):
		self._update()

	def _connectTimer(self):
		if self.timerConnected:
			return
		try:
			if hasattr(self.timer, "timeout") and hasattr(self.timer.timeout, "connect"):
				self.timerConnection = self.timer.timeout.connect(self._update)
				self.timerConnected = True
				return
		except Exception:
			pass
		try:
			self.timer.callback.append(self._update)
			self.timerConnected = True
		except Exception:
			pass

	def _startTimer(self):
		try:
			self.timer.start(self.interval, False)
		except Exception:
			pass

	def _stopTimer(self):
		try:
			self.timer.stop()
		except Exception:
			pass

	def _getState(self):
		try:
			screenName = str(config.channelSelection.screenStyle.value or "")
			templateName = str(config.channelSelection.widgetStyle.value or "")
			return screenName, templateName
		except Exception:
			return "", ""

	def _loadTemplates(self, force=False):
		try:
			mtime = getmtime(self.templateFile)
		except OSError:
			mtime = None
		if not force and mtime == self.templateMtime:
			return
		self.templateMtime = mtime
		self.templates = {}
		if mtime is None:
			return
		try:
			root = parse(self.templateFile).getroot()
			for element in root.findall(".//template"):
				if element.get("component") != "serviceList":
					continue
				name = element.get("name", "").strip()
				if not name:
					continue
				screens = tuple(item.strip() for item in element.get("screens", "").split(",") if item.strip())
				self.templates[name] = screens
		except Exception as error:
			print("[GradientWQHDChannelSelectionPreview] Unable to read templates: %s" % error)
			self.templates = {}

	def _findPreview(self, templateName):
		fileName = templateName.replace("/", "_").replace("\\", "_")
		for extension in (".png", ".jpg", ".jpeg"):
			path = join(self.previewPath, fileName + extension)
			if isfile(path):
				return path
		return None

	def _hidePreview(self):
		self.currentPreview = None
		if self.instance:
			self.instance.hide()

	def _update(self):
		if not self.instance:
			return
		state = self._getState()
		if self.lastState is None:
			self.lastState = state
		elif state != self.lastState:
			self.lastState = state
			self.activated = True
		if not self.activated:
			self._hidePreview()
			return
		self._loadTemplates()
		screenName, templateName = state
		validScreens = self.templates.get(templateName)
		if not screenName or validScreens is None or (validScreens and screenName not in validScreens):
			self._hidePreview()
			return
		preview = self._findPreview(templateName)
		if preview is None:
			self._hidePreview()
			return
		if preview != self.currentPreview:
			try:
				self.instance.setPixmapFromFile(preview)
			except Exception as error:
				print("[GradientWQHDChannelSelectionPreview] Unable to load preview '%s': %s" % (preview, error))
				self._hidePreview()
				return
			self.currentPreview = preview
		self.instance.show()
