# -*- coding: utf-8 -*-
from __future__ import absolute_import

try:
    from Components.Language import language
    from Tools.Directories import resolveFilename, SCOPE_PLUGINS
    import gettext

    PluginLanguageDomain = "BundesligaFHD"
    PluginLanguagePath = "Extensions/BundesligaFHD/locale"

    def localeInit():
        gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

    localeInit()
    language.addCallback(localeInit)

    def _(txt):
        translated = gettext.dgettext(PluginLanguageDomain, txt)
        if translated == txt:
            translated = gettext.gettext(txt)
        return translated
except Exception:
    def _(txt):
        return txt
