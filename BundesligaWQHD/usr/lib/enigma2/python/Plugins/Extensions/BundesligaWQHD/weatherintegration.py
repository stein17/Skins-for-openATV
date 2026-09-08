# -*- coding: utf-8 -*-
"""Bindet den BundesligaWQHD-Wetterrenderer zur Laufzeit in OAWeather ein."""
from __future__ import absolute_import

from xml.etree.ElementTree import fromstring, tostring


RENDERER_NAME = "BLWQHDAnimatedWeatherPixmap"
PATCH_MARKER = "_bundesligawqhd_weather_skin_loader"
SKIN_CALLBACK_MARKER = "_bundesligawqhd_weather_registry_callback"


def rewrite_oaweather_element(root):
    """Ersetzt ausschließlich echte OAWeather-Wetterbilder."""
    if root is None or not hasattr(root, "iter"):
        return 0

    changed = 0
    for widget in root.iter("widget"):
        if widget.get("render") != "OAWeatherPixmap":
            continue
        for converter in widget.findall("convert"):
            if converter.get("type") != "OAWeather":
                continue
            mode = (converter.text or "").strip().split(",", 1)[0].strip()
            if mode == "weathericon":
                widget.set("render", RENDERER_NAME)
                changed += 1
                break
    return changed


def rewrite_oaweather_skin(skin_text):
    """Erhält das OAWeather-Layout und ändert nur Wetterbild-Renderer."""
    if not skin_text or "OAWeatherPixmap" not in skin_text or "weathericon" not in skin_text:
        return skin_text, 0
    try:
        root = fromstring(skin_text)
    except Exception:
        return skin_text, 0

    changed = rewrite_oaweather_element(root)
    if not changed:
        return skin_text, 0
    return tostring(root, encoding="unicode"), changed


def patch_oaweather_skin_loader(weatherhelper):
    """Umschließt OAWeathers internen Skin-Lader genau einmal."""
    if weatherhelper is None or not hasattr(weatherhelper, "loadSkin"):
        return False
    if getattr(weatherhelper, PATCH_MARKER, False):
        return True

    original = weatherhelper.loadSkin

    def load_skin(skinName=""):
        skin_text = original(skinName)
        rewritten, count = rewrite_oaweather_skin(skin_text)
        if count:
            print(
                "[BundesligaWQHD] OAWeather-Screen %s: %d Wetterwidgets aktiviert."
                % (skinName or "<unbekannt>", count)
            )
        return rewritten

    weatherhelper.loadSkin = load_skin
    setattr(weatherhelper, PATCH_MARKER, True)
    return True


def patch_registered_oaweather_screens():
    """Aktiviert bereits vom aktiven Skin registrierte OAWeather-Screens."""
    try:
        import skin as skin_module
    except ImportError:
        return False

    registry = getattr(skin_module, "domScreens", None)
    if registry is None:
        registry = getattr(skin_module, "dom_screens", None)
    if not isinstance(registry, dict):
        return False

    for screen_name, entry in list(registry.items()):
        if not str(screen_name).startswith("OAWeather"):
            continue
        root = entry[0] if isinstance(entry, (tuple, list)) and entry else entry
        rewrite_oaweather_element(root)

    if not getattr(skin_module, SKIN_CALLBACK_MARKER, False):
        def refresh_registered_screens():
            patch_registered_oaweather_screens()

        add_callback = getattr(skin_module, "addCallback", None)
        if callable(add_callback):
            add_callback(refresh_registered_screens)
            setattr(skin_module, SKIN_CALLBACK_MARKER, refresh_registered_screens)
    return True


def install_oaweather_integration():
    """Bindet den skininternen Renderer ein, ohne OAWeather-Dateien zu ändern."""
    registry_patched = patch_registered_oaweather_screens()
    try:
        from Plugins.Extensions.OAWeather import plugin as oaweather_plugin
    except ImportError:
        print("[BundesligaWQHD] OAWeather ist nicht installiert.")
        return registry_patched

    loader_patched = patch_oaweather_skin_loader(
        getattr(oaweather_plugin, "weatherhelper", None)
    )
    if loader_patched:
        print("[BundesligaWQHD] OAWeather-Wetteranimation ist aktiv.")
    return loader_patched or registry_patched

