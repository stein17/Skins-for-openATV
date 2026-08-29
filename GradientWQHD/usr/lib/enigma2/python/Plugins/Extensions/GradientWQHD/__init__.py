from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from gettext import bindtextdomain, gettext, dgettext


def localeInit():
    bindtextdomain("GradientWQHD", resolveFilename(SCOPE_PLUGINS, "Extensions/GradientWQHD/locale"))


def _(txt):
    t = dgettext("GradientWQHD", txt)
    if t == txt:
        t = gettext(txt)
    return t



localeInit()
language.addCallback(localeInit)
