"""Update the FullNight master theme without rebuilding it from scratch.

The shipped theme.xml is the authoritative color table.  The setup only
updates the aliases that belong to the options exposed in the setup screen.
Unknown/manual colors (for example cyan/bernstein/lightblue) are preserved.
"""

from pathlib import Path
import os
import re


THEME_PATH = Path("/usr/share/enigma2/PLi-FullNight-FHD-stein17-Mod/theme.xml")

PALETTES = {
	"original": {
		"background": "000000",
		"backgroundTop": "111318",
		"surface": "090b0f",
		"selection": "343840",
		"rowShade": "14171c",
		"selectionShade": "252a31",
		# Original FullNight compatibility aliases intentionally use their
		# separately tuned values instead of mirroring the modern aliases.
		"backgroundtop": "0d0f16",
		"channelSurface": "090b0f",
		"selectedBG": "303240",
	},
	"midnight": {
		"background": "080b12",
		"backgroundTop": "001b3c",
		"surface": "090c12",
		"selection": "203a58",
		"rowShade": "101b2a",
		"selectionShade": "1b3550",
		"backgroundtop": "001b3c",
		"channelSurface": "090c12",
		"selectedBG": "203a58",
	},
	"black": {
		"background": "080808",
		"backgroundTop": "171717",
		"surface": "020202",
		"selection": "292929",
		"rowShade": "161616",
		"selectionShade": "242424",
		"backgroundtop": "171717",
		"channelSurface": "020202",
		"selectedBG": "292929",
	},
	"teal": {
		# Adapted from Gradient Teal.
		# Dark-teal base surfaces keep large/free areas visibly within
		# the Teal palette instead of looking neutral grey/brownish.
		# Very dark teal instead of black, so FullNightScreen
		# stays teal over its complete vertical gradient.
		"background": "061818",
		"backgroundTop": "0b3333",
		"surface": "0d2020",
		"selection": "1c8484",
		"rowShade": "0b3333",
		"selectionShade": "0b3333",
		"backgroundtop": "0b3333",
		"channelSurface": "0d2020",
		"selectedBG": "1c8484",
	},
	"metrix": {
		# MetrixHD: nearly black base; blue only on headers, bars and selections.
		"background": "0f0f0f",
		"backgroundTop": "27408b",
		"surface": "0f0f0f",
		"selection": "27408b",
		"rowShade": "101010",
		"selectionShade": "27408b",
		"backgroundtop": "27408b",
		"channelSurface": "0f0f0f",
		"selectedBG": "27408b",
	},
	"taupe": {
		# Taupe follows the same visual principle as Teal:
		# dark palette-colored base surfaces instead of neutral grey/black.
		"background": "100b09",
		"backgroundTop": "201815",
		"surface": "18120f",
		"selection": "5b443c",
		"rowShade": "201815",
		"selectionShade": "201815",
		# Stronger taupe upper edge for channel lists without PiG.
		"backgroundtop": "261d19",
		"channelSurface": "18120f",
		"selectedBG": "5b443c",
	},
}

# One shared visual palette for accent and selected-text choices.
# The configuration keys differ only for the historic default aliases
# (accent=gold, selected_text=amber) so existing user settings stay valid.
ACCENTS = {
	"gold": "fcc000",       # Bernstein / FullNight default
	"blue": "879ce1",       # brighter PLi blue; key_blue stays untouched
	"cyan": "2bfafa",
	"lightblue": "7fdcff",
	"greyblue": "8fa7bd",
	"lightgreen": "8bd48b",
	"green": "56c856",
	"silver": "c3c8cf",
	"white": "ffffff",
}

SELECTED_TEXT_COLORS = {
	"amber": "fcc000",      # Bernstein / default
	"blue": "879ce1",
	"cyan": "2bfafa",
	"lightblue": "7fdcff",
	"greyblue": "8fa7bd",
	"lightgreen": "8bd48b",
	"green": "56c856",
	"silver": "c3c8cf",
	"white": "ffffff",
}


def argb(alpha, rgb):
	return "#%s%s" % (alpha, rgb)


def palette_alpha(alpha, maximum="08"):
	"""Clamp palette transparency to maximum #08xxxxxx.

	Enigma2 uses 00 as opaque; larger alpha values are more transparent.
	Values already more opaque than 08 (for example 00 or 06) remain unchanged.
	"""
	try:
		return "%02x" % min(int(str(alpha), 16), int(maximum, 16))
	except (TypeError, ValueError):
		return maximum


def theme_updates(palette="original", transparency="00", gradients=True, accent="gold", selected_text="amber"):
	"""Return only setup-controlled theme values.

	Everything else in theme.xml is deliberately left untouched.
	"""
	data = PALETTES.get(palette, PALETTES["original"])
	accent_rgb = ACCENTS.get(accent, ACCENTS["gold"])
	selected_rgb = "ffffff" if palette == "metrix" else SELECTED_TEXT_COLORS.get(selected_text, SELECTED_TEXT_COLORS["amber"])

	# Global palette rule: no setup-controlled background/surface color may
	# be more transparent than #08xxxxxx. More opaque values such as #00/#06 stay.
	global_alpha = palette_alpha(transparency)
	surface_alpha = "00" if transparency == "00" else "08"

	colors = {
		"background": argb(global_alpha, data["background"]),
		"backgroundTop": argb(global_alpha, data["backgroundTop"]),
		"surface": argb(surface_alpha, data["surface"]),
		"selection": argb("00" if palette == "metrix" else "06", data["selection"]),
		"rowShade": argb("08", data["rowShade"]),
		"selectionShade": argb("08", data["selectionShade"]),
		"channelShadeStrong": argb("08", data["background"]),
		"channelShadeLight": argb("08", data["background"]),
		"key_back": argb("08", data["surface"]),
		"FullNightKeyboardKey": "#00293444",
		"backgroundtop": argb("00", data["backgroundtop"]),
		# Opaque copy of the palette surface for the channel-list frame only.
		"channelSurface": argb("00", data["channelSurface"]),
		"background_Pig_template": argb(global_alpha, data["background"]),
		"transpBlack": argb(global_alpha, data["background"]),
		"selectedBG": argb("00" if palette == "metrix" else "06", data["selectedBG"]),
		"secondBG": argb("08", data["surface"]),
		"infobarBG": argb("00", data["backgroundTop"]),
		# Accent and selected foreground are intentionally independent.
		"accent": argb("00", accent_rgb),
		"selectedFG": argb("00", selected_rgb),
		# Fixed text-button tones. Kept as named colors so SkinDesigner can parse the gradient.
		"FullNightButtonLight": "#006b7078",
		"FullNightButtonMiddle": "#00444a53",
		"foreground": "#00ffffff" if palette == "metrix" else "#00f0f0f0",
		"secondary": "#00bdbdbd" if palette == "metrix" else "#00b6b6b6",
	}

	if gradients:
		colors.update({
			"FullNightScreen": "surface,background,vertical",
			"FullNightChannelScreen": "backgroundtop,channelSurface,vertical",
			"FullNightChannelPanel": "backgroundtop,channelSurface,vertical",
			"FullNightPanel": "backgroundTop,surface,vertical",
			"FullNightMenuTile": "background,surface,vertical",
			"FullNightMenuTileSelected": "selection,background,surface,vertical",
			"FullNightRow": "background,rowShade,vertical",
			"FullNightSelection": "selection,selectionShade,vertical",
			"FullNightListSelection": "selection,selectionShade,vertical",
			"FullNightFade": "transparent,surface,vertical",
			"FullNightInfoFade": "transparent,overlay,vertical",
			"FullNightInfoShade": "overlay,surface,vertical",
			"FullNightVolume": "muted,accent,vertical",
			"FullNightChannelShade": "channelShadeStrong,channelShadeLight,horizontal",
			"FullNightLineHorizontal": "FullNightLineDark,FullNightLineLight,FullNightLineDark,horizontal",
			"FullNightLineVertical": "FullNightLineDark,FullNightLineLight,FullNightLineDark,vertical",
			"FullNightButtonGradient": "FullNightButtonLight,FullNightButtonMiddle,FullNightButtonLight,vertical",
		})
	else:
		colors.update({
			"FullNightScreen": "background",
			"FullNightChannelScreen": "channelSurface",
			"FullNightChannelPanel": "channelSurface",
			"FullNightPanel": "surface",
			"FullNightMenuTile": "background",
			"FullNightMenuTileSelected": "selection",
			"FullNightRow": "background",
			"FullNightSelection": "selection",
			"FullNightListSelection": "selection",
			"FullNightFade": "surface",
			"FullNightInfoFade": "overlay",
			"FullNightInfoShade": "surface",
			"FullNightVolume": "accent",
			"FullNightChannelShade": "channelShadeStrong",
			"FullNightLineHorizontal": "FullNightLineDark",
			"FullNightLineVertical": "FullNightLineDark",
			"FullNightButtonGradient": "FullNightButtonLight,FullNightButtonMiddle,FullNightButtonLight,vertical",
		})
	if palette == "metrix":
		colors.update({
			"FullNightScreen": "background",
			"FullNightSelection": "selection,selection,vertical",
			"FullNightListSelection": "selection,selection,vertical",
			"FullNightMenuTileSelected": "selection",
		})
	return colors


def _replace_or_add_color(text, name, value):
	pattern = re.compile(r'(<color\s+name="%s"\s+value=")[^"]*("\s*/>)' % re.escape(name))
	text, count = pattern.subn(r'\g<1>%s\2' % value, text, count=1)
	if count:
		return text
	marker = "\t</colors>"
	if marker not in text:
		raise ValueError("theme.xml has no </colors> section")
	return text.replace(marker, '\t\t<color name="%s" value="%s" />\n%s' % (name, value, marker), 1)


def write_theme(palette="original", transparency="00", gradients=True, accent="gold", selected_text="amber", target=THEME_PATH):
	"""Patch setup-controlled aliases in the existing master theme.

	The file is never regenerated wholesale.  This guarantees that custom
	colors and manually tuned aliases remain present across setup changes.
	"""
	target = Path(target)
	if not target.exists():
		raise OSError("FullNight master theme not found: %s" % target)

	text = target.read_text(encoding="utf-8")
	for name, value in theme_updates(palette, transparency, gradients, accent, selected_text).items():
		text = _replace_or_add_color(text, name, value)

	temporary = target.with_suffix(target.suffix + ".tmp")
	with temporary.open("w", encoding="utf-8", newline="\n") as handle:
		handle.write(text)
		handle.flush()
		os.fsync(handle.fileno())
	os.replace(str(temporary), str(target))
