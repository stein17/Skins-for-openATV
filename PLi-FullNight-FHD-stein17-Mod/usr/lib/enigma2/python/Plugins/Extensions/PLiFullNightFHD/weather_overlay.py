"""Follow OAWeather and the infobar lifecycle; never fetch or configure weather."""

from Components.config import config
from Screens.Screen import Screen
from twisted.internet import reactor

from .weather import weather_ready


class WeatherOverlay(Screen):
    noSkinReload = True

    def __init__(self, session, mode):
        Screen.__init__(self, session)
        self.skinName = {"current": "FullNightWeather", "details": "FullNightWeatherDetails",
                         "forecast": "FullNightWeatherForecast"}[mode]


class WeatherController:
    def __init__(self, parent, mode):
        self.parent, self.mode = parent, mode
        self.closed = False
        self.overlay = None
        self.handler = None
        self.source = parent.session.screen.get("OAWeather")
        if self.source is not None:
            try:
                from Plugins.Extensions.OAWeather.plugin import weatherhandler
                self.handler = weatherhandler
                self.handler.onUpdate.append(self.updated)
            except ImportError:
                self.source = None
        parent.onShown.append(self.show)
        parent.onShow.append(self.show)
        parent.onHide.append(self.hide)
        parent.onExecEnd.append(self.hide)
        parent.onClose.append(self.close)

    def updated(self, data):
        # OAWeather may notify from its worker; dialog operations belong to the GUI thread.
        reactor.callFromThread(self.show)

    def show(self):
        if self.closed:
            return
        cfg = getattr(config.plugins, "OAWeather", None)
        enabled = getattr(getattr(cfg, "enabled", None), "value", False)
        if not self.parent.shown or not self.parent.execing or not weather_ready(self.source, enabled):
            self.hide()
            return
        if self.overlay is None:
            self.overlay = self.parent.session.instantiateDialog(WeatherOverlay, self.mode)
        self.overlay.show()

    def hide(self):
        if self.overlay is not None:
            self.overlay.hide()

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.hide()
        if self.handler is not None and self.updated in self.handler.onUpdate:
            self.handler.onUpdate.remove(self.updated)
        for callbacks, method in ((self.parent.onShown, self.show), (self.parent.onShow, self.show),
                                  (self.parent.onHide, self.hide), (self.parent.onExecEnd, self.hide)):
            if method in callbacks:
                callbacks.remove(method)
        if self.overlay is not None:
            self.parent.session.deleteDialog(self.overlay)
            self.overlay = None


def install(parent, mode="off"):
    previous = getattr(parent, "_fullNightWeather", None)
    if previous:
        previous.close()
        if previous.close in parent.onClose:
            parent.onClose.remove(previous.close)
    parent._fullNightWeather = None
    if mode in ("current", "details", "forecast"):
        controller = parent._fullNightWeather = WeatherController(parent, mode)
        controller.show()
