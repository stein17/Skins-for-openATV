from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from gettext import bindtextdomain, gettext, dgettext


def localeInit():
    bindtextdomain("PLiHDFullNightMod", resolveFilename(SCOPE_PLUGINS, "Extensions/PLiHDFullNightMod/locale"))


def _(txt):
    t = dgettext("PLiHDFullNightMod", txt)
    if t == txt:
        t = gettext(txt)
    return t



localeInit()
language.addCallback(localeInit)
