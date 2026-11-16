"""Optional technical screen-name overlay for PLi FullNight FHD."""

from Components.Label import Label
from Screens.Screen import Screen


_OVERLAY_KEY = "FullNightScreenNameDebug"
_original_apply_skin = None


def _technical_screen_name(screen):
	"""Return the skin screen name Enigma2 uses for this Screen instance."""
	skin_name = getattr(screen, "skinName", None)
	if isinstance(skin_name, (list, tuple)):
		skin_name = next((name for name in skin_name if isinstance(name, str) and name), None)
	if not skin_name:
		skin_name = screen.__class__.__name__
	class_name = screen.__class__.__name__
	if skin_name != class_name:
		return "%s  [%s]" % (skin_name, class_name)
	return str(skin_name)


def _should_add_overlay(screen, enabled):
	if not enabled():
		return False
	if _OVERLAY_KEY in screen:
		return False
	if screen.__class__.__name__.endswith("Summary"):
		return False
	try:
		if screen.desktop and screen.desktop.size().width() < 1000:
			return False
	except Exception:
		pass
	return True


def install(enabled):
	"""Patch Screen.applySkin once; *enabled* is evaluated for every new screen."""
	global _original_apply_skin
	if _original_apply_skin is not None:
		return

	_original_apply_skin = Screen.applySkin

	def fullnight_apply_skin(screen):
		if _should_add_overlay(screen, enabled):
			label = Label(_technical_screen_name(screen))
			label.skinAttributes = [
				("position", "e-700,13"),
				("size", "550,36"),
				("font", "Regular;24"),
				("foregroundColor", "green"),
				("transparent", "1"),
				("halign", "right"),
				("valign", "center"),
				("noWrap", "1"),
				("shadowColor", "black"),
				("shadowOffset", "1,1"),
				("zPosition", "99"),
			]
			screen[_OVERLAY_KEY] = label
		return _original_apply_skin(screen)

	Screen.applySkin = fullnight_apply_skin
