from pathlib import Path
import os
import re

from .theme import ACCENTS, SELECTED_TEXT_COLORS


TEMPLATE_PATH = Path("/usr/share/enigma2/PLi-FullNight-WQHD-stein17-Mod/skinTemplates.xml")
THEME_PATH = Path("/usr/share/enigma2/PLi-FullNight-WQHD-stein17-Mod/theme.xml")

# Config choice -> color token accepted by foregroundColorSelected.
# Semantic choices keep following their global FullNight colors.
CHANNEL_COLOR_TOKENS = {
	"selected": "selectedFG",
	"foreground": "foreground",
	"secondary": "secondary",
	"accent": "accent",
	"amber": "bernstein",
	"blue": "pliblue",
	"cyan": "cyan",
	"lightblue": "lightblue",
	"greyblue": "greyblue",
	"lightgreen": "greenlight",
	"green": "green",
	"silver": "SliderForeground",
	"white": "white",
}

CHANNEL_TEMPLATE_ROLES = {
	"service": ("ServiceName", "selected"),
	"title": ("Title1", "foreground"),
	"title2": ("Title2", "selected"),
	"title3": ("Title3", "selected"),
	"short": ("ShortDescription1", "secondary"),
	"time": ("StartEndTime1", "cyan"),
	"remain": ("Remain", "cyan"),
	"primetime": ("TitleP", "selected"),
}

FALLBACK_RGB = {
	"foreground": "f0f0f0",
	"secondary": "b6b6b6",
	"amber": "fcc000",
	"blue": "879ce1",
	"cyan": "2bfafa",
	"lightblue": "7fdcff",
	"greyblue": "8fa7bd",
	"lightgreen": "8bd48b",
	"green": "56c856",
	"silver": "c3c8cf",
	"white": "ffffff",
}


def _theme_color_rgb(text, color_name):
	pattern = re.compile(r'<color\s+name="%s"\s+value="([^"]+)"\s*/>' % re.escape(color_name))
	match = pattern.search(text)
	if not match:
		return None
	value = match.group(1)
	if value.startswith("#") and len(value) in (7, 9):
		return value[-6:].lower()
	return None


def channel_color_rgb(choice, accent="gold", selected_text="amber", theme_path=THEME_PATH):
	"""Resolve a setup choice for the live color preview."""
	if choice == "selected":
		return SELECTED_TEXT_COLORS.get(selected_text, SELECTED_TEXT_COLORS["amber"])
	if choice == "accent":
		return ACCENTS.get(accent, ACCENTS["gold"])

	theme_path = Path(theme_path)
	if theme_path.exists():
		text = theme_path.read_text(encoding="utf-8")
		token = CHANNEL_COLOR_TOKENS.get(choice)
		if token:
			rgb = _theme_color_rgb(text, token)
			if rgb:
				return rgb
	return FALLBACK_RGB.get(choice, "ffffff")


def _patch_index(text, index, color_token):
	pattern = re.compile(r'<text\b[^>]*\bindex="%s"[^>]*/>' % re.escape(index), re.S)

	def replace(match):
		tag = match.group(0)
		if "foregroundColorSelected=" in tag:
			return re.sub(
				r'foregroundColorSelected="[^"]*"',
				'foregroundColorSelected="%s"' % color_token,
				tag,
				count=1,
			)
		return tag[:-2].rstrip() + ' foregroundColorSelected="%s" />' % color_token

	return pattern.subn(replace, text)


def write_channel_template_colors(service="selected", title="foreground", title2="selected", title3="selected", short="secondary", time="cyan", remain="cyan", primetime="selected", target=TEMPLATE_PATH):
	"""Patch only selected-text colors in the modern service-list templates.

	No template is regenerated and no unrelated attribute is changed.
	ServiceListLegacy does not use skinTemplates.xml, so the classic mode is
	intentionally unaffected.
	"""
	target = Path(target)
	if not target.exists():
		raise OSError("FullNight skinTemplates.xml not found: %s" % target)

	text = target.read_text(encoding="utf-8")
	choices = {
		"service": service,
		"title": title,
		"title2": title2,
		"title3": title3,
		"short": short,
		"time": time,
		"remain": remain,
		"primetime": primetime,
	}
	for role, choice in choices.items():
		index = CHANNEL_TEMPLATE_ROLES[role][0]
		color_token = CHANNEL_COLOR_TOKENS.get(choice, CHANNEL_COLOR_TOKENS[CHANNEL_TEMPLATE_ROLES[role][1]])
		indices = (index,)
		# The following-event time belongs visually to its title. Keep both
		# selected colors coupled so no separate setup option is required.
		if role == "title2":
			indices = (index, "StartTime2", "StartEndTime2")
		elif role == "title3":
			indices = (index, "StartTime3")

		matched = 0
		for item_index in indices:
			text, count = _patch_index(text, item_index, color_token)
			matched += count
		if not matched:
			raise ValueError("No modern ChannelSelection template entries found for %s" % index)

	temporary = target.with_suffix(target.suffix + ".tmp")
	with temporary.open("w", encoding="utf-8", newline="\n") as handle:
		handle.write(text)
		handle.flush()
		os.fsync(handle.fileno())
	os.replace(str(temporary), str(target))
