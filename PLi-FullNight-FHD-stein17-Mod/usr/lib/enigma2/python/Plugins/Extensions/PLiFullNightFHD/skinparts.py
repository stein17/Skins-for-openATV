"""Discover and build the active FullNight skinpart include."""

import os
from pathlib import Path
from xml.etree import ElementTree as ET


SKIN_ROOT = Path("/usr/share/enigma2/PLi-FullNight-FHD-stein17-Mod")
ACTIVE_PATH = SKIN_ROOT / "active_skinparts.xml"

# Categories remain fixed because they define the setup rows and their behaviour.
# Variants inside these folders are discovered automatically at plugin startup.
CATEGORY_DIRS = {
	"caid": "caid",
	"vpn": "vpnip",
	"weather": "weather",
	"poster_epg": "poster_epg",
	"poster_infobar": "poster_infobar",
}

# Special on/off skinparts with extra plugin logic stay explicit.
STATIC_PARTS = {
	"weather_animated": {
		"enabled": "weather_animated/weather_Icons_Animiert.xml",
	},
}

# Keep the old config values valid after switching to automatic discovery.
LEGACY_PARTS = {
	"caid": {
		"version": "caid/caid_Softcam, CamVersion_Caid_ECM.xml",
		"version_server": "caid/caid_Softcam, CamVersion_Server_Caid_ECM.xml",
		"server": "caid/caid_Softcam, Server_Caid_ECM.xml",
	},
	"vpn": {
		"top_left": "vpnip/VPN_Infobar_left.xml",
		"bottom_left": "vpnip/VPN_Infobar_left_bottom.xml",
		"top_right": "vpnip/VPN_Infobar_right.xml",
		"bottom_right": "vpnip/VPN_Infobar_right_bottom.xml",
		"top_left_no_provider": "vpnip/VPN_Infobar_no_Provider_left.xml",
		"bottom_left_no_provider": "vpnip/VPN_Infobar_no_Provider_left_bottom.xml",
		"top_right_no_provider": "vpnip/VPN_Infobar_no_Provider_right.xml",
		"bottom_right_no_provider": "vpnip/VPN_Infobar_no_Provider_right_bottom.xml",
	},
	"weather": {
		"five_days": "weather/weather_5_Tage_Vorschau.xml",
		"top_left": "weather/weather_Kompakt_oben_links.xml",
		"top_right": "weather/weather_Kompakt_oben_rechts.xml",
		"bottom_right": "weather/weather_Kompakt_unten_rechts.xml",
	},
	"poster_epg": {
		"enabled": "poster_epg/poster_epg.xml",
	},
	"poster_infobar": {
		"poster": "poster_infobar/poster_infobar.xml",
		"backdrop": "poster_infobar/backdrop_infobar.xml",
		"poster_backdrop": "poster_infobar/poster_backdrop_infobar.xml",
	},
}

ORDER = ("poster_epg", "poster_infobar", "caid", "vpn", "weather", "weather_animated")
ALLOW_DISABLED = {
	"caid": True,
	"vpn": True,
	"weather": True,
	"weather_animated": True,
	"poster_epg": True,
	"poster_infobar": True,
}

KNOWN_LABELS = {
	("caid", "version_server"): "Softcam, version, server, CAID and ECM",
	("caid", "version"): "Softcam, version, CAID and ECM",
	("caid", "server"): "Softcam, server, CAID and ECM",
	("weather", "five_days"): "Five-day forecast",
	("weather", "top_left"): "Compact top left",
	("weather", "top_right"): "Compact top right",
	("weather", "bottom_right"): "Compact bottom right",
	("poster_epg", "enabled"): "Enabled",
	("poster_infobar", "poster"): "Poster",
	("poster_infobar", "backdrop"): "Backdrop",
	("poster_infobar", "poster_backdrop"): "Poster + Backdrop",
}


def _legacy_reverse(category):
	return {relative: key for key, relative in LEGACY_PARTS.get(category, {}).items()}


def _variant_sort_key(category, key, stem):
	known = {
		"caid": {"version_server": 0, "version": 1, "server": 2},
		"poster_epg": {"enabled": 0},
		"poster_infobar": {"poster": 0, "backdrop": 1, "poster_backdrop": 2},
	}.get(category, {})
	if key in known:
		return (0, known[key], stem.lower())
	name = stem.lower()
	if category == "weather":
		if "5_tage" in name or "5_day" in name:
			return (0, 0, name)
		position = _position_key(name)
		rank = {"top_left": 1, "top_right": 2, "bottom_left": 3, "bottom_right": 4}.get(position, 90)
		return (0, rank, name)
	if category == "vpn":
		position = _position_key(name)
		position_rank = {"top_left": 0, "bottom_left": 1, "top_right": 2, "bottom_right": 3}.get(position, 9)
		provider_rank = 1 if "no_provider" in name else 0
		return (0, provider_rank * 10 + position_rank, name)
	return (1, 0, name)


def part_map(category, skin_root=SKIN_ROOT):
	"""Return {choice_key: relative_xml_path} for one category.

	Existing legacy keys are retained. New XML files receive their filename stem
	as the stable key, so adding a variant to an existing category requires no
	Python change.
	"""
	if category in STATIC_PARTS:
		return dict(STATIC_PARTS[category])
	folder = CATEGORY_DIRS.get(category)
	if not folder:
		return {}
	base = Path(skin_root) / "allScreens" / folder
	if not base.is_dir():
		return {}
	reverse = _legacy_reverse(category)
	result = {}
	items = []
	for path in base.glob("*.xml"):
		relative = "%s/%s" % (folder, path.name)
		key = reverse.get(relative, path.stem)
		items.append((key, relative, path.stem))
	for key, relative, stem in sorted(items, key=lambda item: _variant_sort_key(category, item[0], item[2])):
		result[key] = relative
	return result


def _position_key(name):
	if "left_bottom" in name or "unten_links" in name or "bottom_left" in name:
		return "bottom_left"
	if "right_bottom" in name or "unten_rechts" in name or "bottom_right" in name:
		return "bottom_right"
	if name.endswith("_left") or "oben_links" in name or "top_left" in name:
		return "top_left"
	if name.endswith("_right") or "oben_rechts" in name or "top_right" in name:
		return "top_right"
	return None


def _vpn_label(stem, translate):
	name = stem.lower()
	position = _position_key(name)
	if not position:
		return None
	source = {
		("top_left", False): "Top left - with provider",
		("bottom_left", False): "Bottom left - with provider",
		("top_right", False): "Top right - with provider",
		("bottom_right", False): "Bottom right - with provider",
		("top_left", True): "Top left - without provider",
		("bottom_left", True): "Bottom left - without provider",
		("top_right", True): "Top right - without provider",
		("bottom_right", True): "Bottom right - without provider",
	}[(position, "no_provider" in name)]
	return translate(source)


def _weather_label(stem, translate):
	name = stem.lower()
	if "5_tage" in name or "5_day" in name:
		return translate("Five-day forecast")
	if "kompakt" not in name and "compact" not in name:
		return None
	position = _position_key(name)
	if not position:
		return None
	source = {
		"top_left": "Compact top left",
		"top_right": "Compact top right",
		"bottom_left": "Compact bottom left",
		"bottom_right": "Compact bottom right",
	}[position]
	return translate(source)


def choice_label(category, key, relative, translate=lambda text: text):
	known = KNOWN_LABELS.get((category, key))
	if known:
		return translate(known)
	stem = Path(relative).stem
	if category == "vpn":
		label = _vpn_label(stem, translate)
		if label:
			return label
	elif category == "weather":
		label = _weather_label(stem, translate)
		if label:
			return label
	# Generic fallback for future files in existing categories.
	for prefix in ("weather_", "caid_", "VPN_Infobar_", "poster_"):
		if stem.lower().startswith(prefix.lower()):
			stem = stem[len(prefix):]
			break
	return stem.replace("_", " ").strip()


def skinpart_choices(category, translate=lambda text: text, skin_root=SKIN_ROOT):
	choices = []
	if ALLOW_DISABLED.get(category, True):
		choices.append(("disabled", translate("Disabled")))
	for key, relative in part_map(category, skin_root).items():
		choices.append((key, choice_label(category, key, relative, translate)))
	return choices


def selected_files(values, skin_root=SKIN_ROOT):
	base = Path(skin_root) / "allScreens"
	for category in ORDER:
		choice = values.get(category, "disabled")
		if choice == "disabled":
			continue
		relative = part_map(category, skin_root).get(choice)
		if relative is None:
			raise ValueError("Unknown %s skinpart: %s" % (category, choice))
		path = base / relative
		if not path.is_file():
			raise ValueError("Missing FullNight skinpart: %s" % path)
		yield category, path


def preview_path(category, choice, skin_root=SKIN_ROOT):
	"""Return a matching preview whose folder and basename mirror allScreens."""
	if not choice or choice == "disabled":
		return None
	relative = part_map(category, skin_root).get(choice)
	if relative is None:
		return None
	relative = Path(relative)
	base = Path(skin_root) / "preview" / relative.parent
	for suffix in (".png", ".jpg", ".jpeg"):
		candidate = base / (relative.stem + suffix)
		if candidate.is_file():
			return candidate
	return None


def skinparts_bytes(values, skin_root=SKIN_ROOT):
	root = ET.Element("skin")
	root.append(ET.Comment("Generated by PLi FullNight FHD Setup"))
	for category, path in selected_files(values, skin_root):
		root.append(ET.Comment("%s: %s" % (category, path.name)))
		try:
			part_root = ET.parse(path).getroot()
		except ET.ParseError as error:
			raise ValueError("Invalid FullNight skinpart %s: %s" % (path.name, error))
		for child in list(part_root):
			root.append(child)
	if hasattr(ET, "indent"):
		ET.indent(root, space="\t")
	return ET.tostring(root, encoding="UTF-8", xml_declaration=True)


def write_skinparts(values, target=ACTIVE_PATH, skin_root=SKIN_ROOT):
	target = Path(target)
	target.parent.mkdir(parents=True, exist_ok=True)
	temporary = target.with_suffix(target.suffix + ".tmp")
	with temporary.open("wb") as handle:
		handle.write(skinparts_bytes(values, skin_root))
		handle.flush()
		os.fsync(handle.fileno())
	os.replace(str(temporary), str(target))
