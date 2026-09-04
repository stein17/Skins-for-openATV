# Animierter OAWeather-Renderer fuer den BundesligaFHD Skin.
# Die SVG-Animationen von Meteocons werden als vorbereitete PNG-Frames geladen.

from json import load
from os.path import basename, exists, join, splitext
from weakref import WeakSet

from Components.Renderer.Renderer import Renderer
from Tools.LoadPixmap import LoadPixmap
try:
	from Plugins.Extensions.BundesligaFHD.settings import (
		weather_animation_config,
		weather_animation_interval_config,
		weather_iconset_config,
	)
	from Plugins.Extensions.BundesligaFHD.weathericons import (
		DEFAULT_ICONSET_ID,
		resolved_iconset_path,
	)
except ImportError:
	weather_animation_config = None
	weather_animation_interval_config = None
	weather_iconset_config = None
	DEFAULT_ICONSET_ID = "meteocons-2-fill"
	resolved_iconset_path = None
from enigma import (
	BT_HALIGN_CENTER,
	BT_KEEP_ASPECT_RATIO,
	BT_SCALE,
	BT_VALIGN_CENTER,
	ePixmap,
	eTimer,
)


DEFAULT_ANIMATION_PATH = "/usr/share/enigma2/BundesligaFHD/weather/Meteocons_Animated"
DEFAULT_FRAME_INTERVAL = 200
FRAME_COUNT = 24


class _AnimationClock:
	"""Ein gemeinsamer Taktgeber fuer alle fuenf Wetterwidgets."""

	instances = WeakSet()
	timer = None
	running = False
	interval = None

	@classmethod
	def add(cls, renderer):
		cls.instances.add(renderer)
		if cls.timer is None:
			cls.timer = eTimer()
			cls.timer.callback.append(cls.tick)
		interval = renderer.getFrameInterval()
		if not cls.running or cls.interval != interval:
			if cls.running:
				cls.timer.stop()
			cls.timer.start(interval, False)
			cls.running = True
			cls.interval = interval

	@classmethod
	def remove(cls, renderer):
		cls.instances.discard(renderer)
		if not cls.instances and cls.timer is not None:
			cls.timer.stop()
			cls.running = False
			cls.interval = None

	@classmethod
	def tick(cls):
		if not cls.instances:
			if cls.timer is not None:
				cls.timer.stop()
			cls.running = False
			cls.interval = None
			return
		for renderer in list(cls.instances):
			renderer.showNextFrame()


class BLFHDAnimatedWeatherPixmap(Renderer):
	GUI_WIDGET = ePixmap
	weatherMaps = {}

	def __init__(self):
		Renderer.__init__(self)
		self.code = ""
		self.frames = []
		self.frameIndex = 0
		self.animationPath = ""
		self.conditionText = ""

	@classmethod
	def getWeatherMap(cls, animationPath):
		if animationPath not in cls.weatherMaps:
			try:
				with open(join(animationPath, "mapping.json"), "r", encoding="utf-8") as mappingFile:
					cls.weatherMaps[animationPath] = load(mappingFile)
			except (OSError, ValueError, TypeError):
				cls.weatherMaps[animationPath] = {}
		return cls.weatherMaps[animationPath]

	def getAnimationPath(self):
		iconset = DEFAULT_ICONSET_ID
		if weather_iconset_config is not None:
			try:
				iconset = weather_iconset_config().value
			except Exception:
				pass
		if resolved_iconset_path is not None:
			try:
				return resolved_iconset_path(iconset)
			except Exception:
				pass
		return DEFAULT_ANIMATION_PATH

	def postWidgetCreate(self, instance):
		Renderer.postWidgetCreate(self, instance)
		instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
		self.changed((self.CHANGED_DEFAULT,))

	def preWidgetRemove(self, instance):
		_AnimationClock.remove(self)
		self.frames = []
		Renderer.preWidgetRemove(self, instance)

	def onShow(self):
		Renderer.onShow(self)
		if not self.animationEnabled():
			_AnimationClock.remove(self)
			self.frames = []
			self.showStaticFallback()
			return
		if not self.frames:
			self.code = ""
			self.changed((self.CHANGED_DEFAULT,))
		if len(self.frames) > 1:
			_AnimationClock.add(self)

	def onHide(self):
		_AnimationClock.remove(self)
		Renderer.onHide(self)

	def getWeatherCode(self):
		try:
			code = str(self.source.text).strip()
		except Exception:
			code = ""
		if not code:
			try:
				code = splitext(basename(self.source.iconfilename))[0]
			except Exception:
				code = ""
		return code.upper() if code else "NA"

	def getConditionText(self):
		"""Liest den zum Widget gehoerenden OAWeather-Beschreibungstext.

		MSN liefert gelegentlich fuer "teilweise sonnig" und "teilweise
		bewoelkt" denselben Yahoo-Code. Der Text bleibt aber verschieden und
		erlaubt dem Renderer deshalb eine eindeutige Motivauswahl.
		"""
		try:
			converter = self.source
			index = getattr(converter, "index", None)
			weatherSource = getattr(converter, "source", None)
			if index is not None and weatherSource is not None:
				return str(weatherSource.getKeyforDay("text", index, "") or "").strip()
		except Exception:
			pass
		return ""

	def getMappedFolder(self, code, animationPath, conditionText=""):
		mapping = self.getWeatherMap(animationPath)
		entry = mapping.get(code, mapping.get("NA", {}))
		folder = entry.get("icon", "") if isinstance(entry, dict) else str(entry)
		text = ""
		if conditionText:
			text = conditionText.casefold().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")

		# Die beiden verwechselbaren Tagesvarianten anhand des Textes trennen.
		if code in ("30", "34") and text:
			if any(word in text for word in ("sonnig", "heiter", "sunny", "fair")):
				folder = "mostly-sunny-day"
			elif any(word in text for word in ("bewoelkt", "cloudy")):
				folder = "partly-cloudy-day"

		# MSN/OAWeather kann auch bei Regenlagen unterschiedliche Codes mit
		# demselben sichtbaren Text liefern. Nur eindeutig benannte Regenstufen
		# werden deshalb textbasiert vereinheitlicht; Schauer und Gewitter
		# bleiben weiterhin vollständig mapping.json-gesteuert.
		if text:
			if any(word in text for word in ("gefrierender regen", "gefrierender nieselregen", "freezing rain", "freezing drizzle")):
				folder = "freezing-rain"
			elif any(word in text for word in ("starker regen", "starkregen", "heavy rain", "heavy rainfall")):
				folder = "heavy-rain"
			elif any(word in text for word in ("leichter regen", "leichter regenfall", "light rain", "light rainfall")):
				folder = "light-rain"
			elif any(word in text for word in ("nieselregen", "spruehregen", "drizzle")):
				folder = "drizzle"
			elif text.strip(" .,-") in ("regen", "regenfall", "rain", "rainfall"):
				folder = "rain"
		return folder

	def animationEnabled(self):
		if weather_animation_config is None:
			return True
		try:
			return bool(weather_animation_config().value)
		except Exception:
			return True

	def getFrameInterval(self):
		if weather_animation_interval_config is None:
			return DEFAULT_FRAME_INTERVAL
		try:
			value = int(weather_animation_interval_config().value)
		except Exception:
			value = DEFAULT_FRAME_INTERVAL
		return max(100, min(500, value))

	def loadFrames(self, code, animationPath, conditionText=""):
		folder = self.getMappedFolder(code, animationPath, conditionText)
		framePath = join(animationPath, folder)
		frames = []
		if folder and exists(framePath):
			for index in range(FRAME_COUNT):
				filename = join(framePath, "a%d.png" % index)
				if not exists(filename):
					break
				pixmap = LoadPixmap(filename, cached=False)
				if pixmap is not None:
					frames.append(pixmap)
		return frames

	def showStaticFallback(self):
		try:
			filename = self.source.iconfilename
		except Exception:
			filename = ""
		if filename and exists(filename):
			self.instance.setPixmapFromFile(filename)
			self.instance.show()
		else:
			self.instance.hide()

	def changed(self, what):
		if self.instance is None:
			return
		if what[0] == self.CHANGED_CLEAR:
			_AnimationClock.remove(self)
			self.code = ""
			self.animationPath = ""
			self.conditionText = ""
			self.frames = []
			self.instance.hide()
			return
		if not self.animationEnabled():
			_AnimationClock.remove(self)
			self.code = self.getWeatherCode()
			self.frames = []
			self.frameIndex = 0
			self.showStaticFallback()
			return

		code = self.getWeatherCode()
		conditionText = self.getConditionText()
		animationPath = self.getAnimationPath()
		if code == self.code and animationPath == self.animationPath and conditionText == self.conditionText and self.frames:
			return
		_AnimationClock.remove(self)
		self.code = code
		self.animationPath = animationPath
		self.conditionText = conditionText
		self.frames = self.loadFrames(code, animationPath, conditionText)
		self.frameIndex = 0
		if not self.frames:
			self.showStaticFallback()
			return
		self.instance.setPixmap(self.frames[0])
		self.instance.show()
		if len(self.frames) > 1 and not getattr(self, "suspended", False):
			_AnimationClock.add(self)

	def showNextFrame(self):
		if self.instance is None or len(self.frames) < 2 or getattr(self, "suspended", False):
			return
		self.frameIndex = (self.frameIndex + 1) % len(self.frames)
		self.instance.setPixmap(self.frames[self.frameIndex])


# Wenn das eigenständige Animated-Weather-Plugin installiert ist, verwendet
# der Bundesliga-Skin dessen zentrale Auswahl, Speicherort und Renderer. Ohne
# das Plugin bleibt der bisherige skininterne Renderer als Rückfall erhalten.
try:
	from Components.Renderer.AnimatedWeatherPixmap import (
		AnimatedWeatherPixmap as _CentralAnimatedWeatherPixmap,
	)
except (ImportError, AttributeError):
	_CentralAnimatedWeatherPixmap = None

if _CentralAnimatedWeatherPixmap is not None:
	BLFHDAnimatedWeatherPixmap = _CentralAnimatedWeatherPixmap
