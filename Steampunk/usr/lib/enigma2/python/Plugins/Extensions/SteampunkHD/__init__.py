from __future__ import print_function
# Embedded file name: /usr/lib/enigma2/python/Plugins/Extensions/SteampunkConfig/__init__.py
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import os, gettext
PluginLanguageDomain = 'SteampunkConfig'
PluginLanguagePath = 'Extensions/SteampunkConfig/locale'

def localeInit():
    lang = language.getLanguage()[:2]
    os.environ['LANGUAGE'] = lang
    print('[WebInterface] set language to ', lang)
    gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
    t = gettext.dgettext(PluginLanguageDomain, txt)
    if t == txt:
        print('[%s] fallback to default translation for %s' % (PluginLanguageDomain, txt))
        t = gettext.gettext(txt)
    return t


localeInit()
language.addCallback(localeInit)
