from gettext import bindtextdomain, dgettext, gettext

from Components.Language import language
from Tools.Directories import SCOPE_PLUGINS, resolveFilename


DOMAIN = "PLiFullNightFHD"
LOCALE_PATH = resolveFilename(SCOPE_PLUGINS, "Extensions/PLiFullNightFHD/locale")


def localeInit():
	bindtextdomain(DOMAIN, LOCALE_PATH)


def _(text):
	translated = dgettext(DOMAIN, text)
	return gettext(text) if translated == text else translated


localeInit()
language.addCallback(localeInit)
