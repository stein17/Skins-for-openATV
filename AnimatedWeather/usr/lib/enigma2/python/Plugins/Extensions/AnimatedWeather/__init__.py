# -*- coding: utf-8 -*-
from __future__ import absolute_import

import gettext

from Components.Language import language
from Tools.Directories import SCOPE_PLUGINS, resolveFilename


PLUGIN_LANGUAGE_DOMAIN = "AnimatedWeather"
PLUGIN_LANGUAGE_PATH = "Extensions/AnimatedWeather/locale"


def localeInit():
    gettext.bindtextdomain(
        PLUGIN_LANGUAGE_DOMAIN,
        resolveFilename(SCOPE_PLUGINS, PLUGIN_LANGUAGE_PATH),
    )


def _(text):
    translated = gettext.dgettext(PLUGIN_LANGUAGE_DOMAIN, text)
    if translated == text:
        translated = gettext.gettext(text)
    return translated


localeInit()
language.addCallback(localeInit)
