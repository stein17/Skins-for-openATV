# -*- coding: utf-8 -*-
from __future__ import absolute_import

from gettext import bindtextdomain, dgettext

from Components.Language import language
from Tools.Directories import SCOPE_PLUGINS, resolveFilename


PLUGIN_DOMAIN = "BundesligaInstaller"
PLUGIN_LOCALE = resolveFilename(SCOPE_PLUGINS, "Extensions/BundesligaInstaller/locale")


def localeInit():
    bindtextdomain(PLUGIN_DOMAIN, PLUGIN_LOCALE)


def _(text):
    translated = dgettext(PLUGIN_DOMAIN, text)
    return translated if translated != text else text


localeInit()
language.addCallback(localeInit)
