from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from gettext import bindtextdomain, gettext, dgettext


def localeInit():
    bindtextdomain("GradientFHD", resolveFilename(SCOPE_PLUGINS, "Extensions/GradientFHD/locale"))


def _(txt):
    t = dgettext("GradientFHD", txt)
    if t == txt:
        t = gettext(txt)
    return t



localeInit()
language.addCallback(localeInit)
