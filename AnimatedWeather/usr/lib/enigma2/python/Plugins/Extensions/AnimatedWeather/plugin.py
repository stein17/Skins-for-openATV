# -*- coding: utf-8 -*-
from __future__ import absolute_import

from Plugins.Plugin import PluginDescriptor

from . import _
from .constants import PLUGIN_NAME


def main(session, **kwargs):
    from .screens import AnimatedWeatherSetup
    session.open(AnimatedWeatherSetup)


def sessionstart(session=None, **kwargs):
    """Bindet den Renderer zur Laufzeit in aktuelle OAWeather-Versionen ein."""
    try:
        from .integration import install_oaweather_integration
        install_oaweather_integration()
    except Exception as error:
        print("[AnimatedWeather] OAWeather-Integration fehlgeschlagen: %s" % error)


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name=_(PLUGIN_NAME),
            where=PluginDescriptor.WHERE_SESSIONSTART,
            fnc=sessionstart,
            needsRestart=False,
        ),
        PluginDescriptor(
            name=_(PLUGIN_NAME),
            description=_("Skinunabhängige statische und animierte Wetter-Iconsets für OAWeather"),
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="plugin.png",
            fnc=main,
        )
    ]
