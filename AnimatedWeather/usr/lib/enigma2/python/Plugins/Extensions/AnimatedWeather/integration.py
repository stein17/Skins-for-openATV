# -*- coding: utf-8 -*-
"""Laufzeit-Integration für OAWeather, ohne dessen Dateien zu verändern."""
from __future__ import absolute_import

from xml.etree.ElementTree import fromstring, tostring


PATCH_MARKER = "_animatedweather_skin_loader"
DETAIL_GUARD_MARKER = "_animatedweather_detail_guard"


def rewrite_oaweather_skin(skin_text):
    """Ersetzt ausschließlich echte OAWeather-Wetterbild-Renderer.

    Anbieterlogo, Mondphase und andere Pixmaps behalten OAWeatherPixmap.
    """
    if not skin_text or "OAWeatherPixmap" not in skin_text or "weathericon" not in skin_text:
        return skin_text, 0
    try:
        root = fromstring(skin_text)
    except Exception:
        return skin_text, 0

    changed = 0
    for widget in root.iter("widget"):
        if widget.get("render") != "OAWeatherPixmap":
            continue
        for converter in widget.findall("convert"):
            if converter.get("type") != "OAWeather":
                continue
            mode = (converter.text or "").strip().split(",", 1)[0].strip()
            if mode == "weathericon":
                widget.set("render", "AnimatedWeatherPixmap")
                changed += 1
                break
    if not changed:
        return skin_text, 0
    return tostring(root, encoding="unicode"), changed


def patch_oaweather_skin_loader(weatherhelper):
    """Umschließt OAWeathers internen Skin-Lader genau einmal."""
    if getattr(weatherhelper, PATCH_MARKER, False):
        return True

    original = weatherhelper.loadSkin

    def load_skin(skinName=""):
        skin_text = original(skinName)
        rewritten, count = rewrite_oaweather_skin(skin_text)
        if count:
            print(
                "[AnimatedWeather] OAWeather-Screen %s: %d Wetterwidgets aktiviert."
                % (skinName or "<unbekannt>", count)
            )
        return rewritten

    weatherhelper.loadSkin = load_skin
    setattr(weatherhelper, PATCH_MARKER, True)
    return True


def patch_oaweather_detail_view(oaweather_module):
    """Verhindert OAWeather-Absturz bei einem sehr schnellen zweiten OK.

    OAWeather 2.3 schaltet den Detailrahmen bereits um, obwohl die asynchron
    geladene Stundenliste noch leer sein kann. ``getCurrent()`` liefert dann
    ``None`` und OAWeather versucht daraus eine Liste zu erzeugen. Die
    OAWeather-Dateien werden nicht geaendert; der bekannte Leerlauf-Fall wird
    nur zur Laufzeit abgefangen.
    """
    detail_view = getattr(oaweather_module, "OAWeatherDetailview", None)
    if detail_view is None or not hasattr(detail_view, "updateDetailFrame"):
        return False
    if getattr(detail_view, DETAIL_GUARD_MARKER, False):
        return True

    original = detail_view.updateDetailFrame

    def update_detail_frame(self):
        if getattr(self, "detailFrameActive", False):
            current = self["detailList"].getCurrent()
            if current is None:
                print(
                    "[AnimatedWeather] OAWeather-Detailrahmen wartet auf Wetterdaten."
                )
                return
        return original(self)

    detail_view.updateDetailFrame = update_detail_frame
    setattr(detail_view, DETAIL_GUARD_MARKER, True)
    return True


def install_oaweather_integration():
    try:
        from Plugins.Extensions.OAWeather import plugin as oaweather_plugin
    except ImportError:
        print("[AnimatedWeather] OAWeather ist nicht installiert; Integration übersprungen.")
        return False
    patched = patch_oaweather_skin_loader(oaweather_plugin.weatherhelper)
    detail_guard = patch_oaweather_detail_view(oaweather_plugin)
    if patched:
        print("[AnimatedWeather] OAWeather-Laufzeitintegration ist aktiv.")
    if detail_guard:
        print("[AnimatedWeather] OAWeather-Detailansicht ist abgesichert.")
    return patched
