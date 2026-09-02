# -*- coding: utf-8 -*-
"""Skinunabhängiger statischer/animierter Renderer für die OAWeather-Quelle.

OAWeather selbst wird nicht verändert. Der Skin ersetzt lediglich
``render="OAWeatherPixmap"`` durch ``render="AnimatedWeatherPixmap"``.
"""
from __future__ import absolute_import

from json import load
from os.path import basename, exists, isdir, isfile, join, splitext
from Components.Renderer.Renderer import Renderer
from Tools.LoadPixmap import LoadPixmap
from enigma import (
    BT_HALIGN_CENTER,
    BT_KEEP_ASPECT_RATIO,
    BT_SCALE,
    BT_VALIGN_CENTER,
    ePixmap,
    eTimer,
)

try:
    from Plugins.Extensions.AnimatedWeather.constants import MAX_FRAMES, STATIC_ICONSET_ID
    from Plugins.Extensions.AnimatedWeather.settings import (
        animation_config,
        iconset_config,
        interval_config,
        manager_for_current_storage,
    )
except Exception:
    MAX_FRAMES = 60
    STATIC_ICONSET_ID = "static"
    animation_config = None
    iconset_config = None
    interval_config = None
    manager_for_current_storage = None


DEFAULT_FRAME_INTERVAL = 200


class _FrameCache(object):
    frames = {}

    @classmethod
    def get(cls, frame_path):
        if frame_path in cls.frames:
            return cls.frames[frame_path]
        result = []
        if isfile(frame_path):
            pixmap = LoadPixmap(frame_path, cached=False)
            if pixmap is not None:
                result.append(pixmap)
        elif isdir(frame_path):
            for index in range(MAX_FRAMES):
                filename = join(frame_path, "a%d.png" % index)
                if not isfile(filename):
                    break
                pixmap = LoadPixmap(filename, cached=False)
                if pixmap is not None:
                    result.append(pixmap)
        cls.frames[frame_path] = result
        return result


class AnimatedWeatherPixmap(Renderer):
    GUI_WIDGET = ePixmap
    weatherMaps = {}

    def __init__(self):
        Renderer.__init__(self)
        self.code = ""
        self.conditionText = ""
        self.animationPath = ""
        self.frames = []
        self.frameIndex = 0
        self.timer = eTimer()
        self.timerConnection = None
        try:
            self.timerConnection = self.timer.timeout.connect(self.showNextFrame)
        except Exception:
            self.timer.callback.append(self.showNextFrame)

    def startTimer(self):
        self.stopTimer()
        if self.animationEnabled() and len(self.frames) > 1:
            self.timer.start(self.getFrameInterval(), False)

    def stopTimer(self):
        try:
            self.timer.stop()
        except Exception:
            pass

    def postWidgetCreate(self, instance):
        Renderer.postWidgetCreate(self, instance)
        instance.setPixmapScaleFlags(
            BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER
        )
        self.changed((self.CHANGED_DEFAULT,))

    def preWidgetRemove(self, instance):
        self.stopTimer()
        self.frames = []
        Renderer.preWidgetRemove(self, instance)

    def onShow(self):
        Renderer.onShow(self)
        if not self.getAnimationPath():
            self.stopTimer()
            self.frames = []
            self.showStaticFallback()
            return
        if not self.frames:
            self.code = ""
            self.changed((self.CHANGED_DEFAULT,))
        self.startTimer()

    def onHide(self):
        self.stopTimer()
        Renderer.onHide(self)

    def animationEnabled(self):
        if animation_config is None:
            return False
        try:
            return bool(animation_config().value)
        except Exception:
            return False

    def getFrameInterval(self):
        if interval_config is None:
            return DEFAULT_FRAME_INTERVAL
        try:
            value = int(interval_config().value)
        except Exception:
            value = DEFAULT_FRAME_INTERVAL
        return max(100, min(500, value))

    def getAnimationPath(self):
        if iconset_config is None or manager_for_current_storage is None:
            return ""
        try:
            iconset_id = iconset_config().value
            if iconset_id == STATIC_ICONSET_ID:
                return ""
            return manager_for_current_storage().selected_path(iconset_id)
        except Exception:
            return ""

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
        code = code.upper() if code else "NA"
        return code if code in [str(value) for value in range(48)] + ["NA"] else "NA"

    def getConditionText(self):
        try:
            converter = self.source
            index = getattr(converter, "index", None)
            weatherSource = getattr(converter, "source", None)
            if index is not None and weatherSource is not None:
                return str(weatherSource.getKeyforDay("text", index, "") or "").strip()
        except Exception:
            pass
        return ""

    @classmethod
    def getWeatherMap(cls, animationPath):
        if animationPath not in cls.weatherMaps:
            try:
                with open(join(animationPath, "mapping.json"), "r", encoding="utf-8") as source:
                    cls.weatherMaps[animationPath] = load(source)
            except (OSError, ValueError, TypeError):
                cls.weatherMaps[animationPath] = None
        return cls.weatherMaps[animationPath]

    def _normalizedText(self, conditionText):
        return (
            (conditionText or "")
            .casefold()
            .replace("ä", "ae")
            .replace("ö", "oe")
            .replace("ü", "ue")
            .replace("ß", "ss")
        )

    def _existingTarget(self, animationPath, preferred, fallback):
        target = join(animationPath, preferred) if preferred else ""
        return preferred if target and (isdir(target) or isfile(target)) else fallback

    def getMappedFolder(self, code, animationPath, conditionText=""):
        mapping = self.getWeatherMap(animationPath)
        text = self._normalizedText(conditionText)
        if isinstance(mapping, dict):
            entry = mapping.get(code, mapping.get("NA", {}))
            folder = entry.get("icon", "") if isinstance(entry, dict) else str(entry)

            if code in ("30", "34") and text:
                if any(word in text for word in ("sonnig", "heiter", "sunny", "fair")):
                    folder = self._existingTarget(animationPath, "mostly-sunny-day", folder)
                elif any(word in text for word in ("bewoelkt", "cloudy")):
                    folder = self._existingTarget(animationPath, "partly-cloudy-day", folder)

            if text:
                if any(word in text for word in ("gefrierender regen", "gefrierender nieselregen", "freezing rain", "freezing drizzle")):
                    folder = self._existingTarget(animationPath, "freezing-rain", folder)
                elif any(word in text for word in ("starker regen", "starkregen", "heavy rain", "heavy rainfall")):
                    folder = self._existingTarget(animationPath, "heavy-rain", folder)
                elif any(word in text for word in ("leichter regen", "leichter regenfall", "light rain", "light rainfall")):
                    folder = self._existingTarget(animationPath, "light-rain", folder)
                elif any(word in text for word in ("nieselregen", "spruehregen", "drizzle")):
                    folder = self._existingTarget(animationPath, "drizzle", folder)
                elif text.strip(" .,-") in ("regen", "regenfall", "rain", "rainfall"):
                    folder = self._existingTarget(animationPath, "rain", folder)
            return folder

        # Klassische Sets verwenden Code-Ordner; flache statische Sets direkt
        # 0.png bis 47.png. NA/na ist optional und fällt sonst auf Code 0 zurück.
        if isfile(join(animationPath, "%s.png" % code.lower())):
            folder = "%s.png" % code.lower()
        elif isfile(join(animationPath, "%s.png" % code)):
            folder = "%s.png" % code
        elif isdir(join(animationPath, code)):
            folder = code
        elif isfile(join(animationPath, "na.png")):
            folder = "na.png"
        elif isdir(join(animationPath, "NA")):
            folder = "NA"
        else:
            folder = "0.png" if isfile(join(animationPath, "0.png")) else "0"
        if code in ("30", "34") and text:
            if any(word in text for word in ("sonnig", "heiter", "sunny", "fair")):
                preferred = "34.png" if isfile(join(animationPath, "34.png")) else "34"
                folder = self._existingTarget(animationPath, preferred, folder)
            elif any(word in text for word in ("bewoelkt", "cloudy")):
                preferred = "30.png" if isfile(join(animationPath, "30.png")) else "30"
                folder = self._existingTarget(animationPath, preferred, folder)
        return folder

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
            self.stopTimer()
            self.code = ""
            self.conditionText = ""
            self.animationPath = ""
            self.frames = []
            self.instance.hide()
            return

        animationPath = self.getAnimationPath()
        if not animationPath:
            self.stopTimer()
            self.frames = []
            self.frameIndex = 0
            self.showStaticFallback()
            return

        code = self.getWeatherCode()
        conditionText = self.getConditionText()
        if (
            code == self.code
            and conditionText == self.conditionText
            and animationPath == self.animationPath
            and self.frames
        ):
            return

        self.stopTimer()
        self.code = code
        self.conditionText = conditionText
        self.animationPath = animationPath
        folder = self.getMappedFolder(code, animationPath, conditionText)
        self.frames = _FrameCache.get(join(animationPath, folder)) if folder else []
        self.frameIndex = 0
        if not self.frames:
            self.showStaticFallback()
            return
        self.instance.setPixmap(self.frames[0])
        self.instance.show()
        # OAWeather 2.3 liefert seine Daten häufig schon vor dem sichtbaren
        # Screen. Deshalb startet jedes Wetterwidget seinen eigenen Timer
        # unmittelbar nach dem Laden der Frames. onHide/preWidgetRemove stoppen
        # ihn zuverlässig wieder.
        self.startTimer()

    def showNextFrame(self):
        if not self.animationEnabled() or self.instance is None or len(self.frames) < 2:
            return
        self.frameIndex = (self.frameIndex + 1) % len(self.frames)
        self.instance.setPixmap(self.frames[self.frameIndex])
