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

	def loadFrames(self, code, animationPath):
		mapping = self.getWeatherMap(animationPath)
		entry = mapping.get(code, mapping.get("NA", {}))
		folder = entry.get("icon", "") if isinstance(entry, dict) else str(entry)
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
		animationPath = self.getAnimationPath()
		if code == self.code and animationPath == self.animationPath and self.frames:
			return
		_AnimationClock.remove(self)
		self.code = code
		self.animationPath = animationPath
		self.frames = self.loadFrames(code, animationPath)
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
