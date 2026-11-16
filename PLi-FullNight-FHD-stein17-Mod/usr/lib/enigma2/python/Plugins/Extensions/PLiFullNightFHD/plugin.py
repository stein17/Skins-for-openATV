from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Console import Console
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.config import ConfigNothing, ConfigSelection, ConfigSubsection, ConfigYesNo, config, configfile, getConfigListEntry
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from skin import parseColor

from . import _
from .screen_names import install as install_screen_name_overlay
from .skinparts import preview_path, skinpart_choices, skinparts_bytes, write_skinparts
from .theme import ACCENTS, SELECTED_TEXT_COLORS, write_theme
from .channel_colors import channel_color_rgb, write_channel_template_colors
from .progress_theme import write_progress_theme


SKIN_ENTRY = "PLi-FullNight-FHD-stein17-Mod/skin.xml"
ANIMATED_WEATHER_RENDERER = "/usr/lib/enigma2/python/Components/Renderer/AnimatedWeatherPixmap.py"
ANIMATED_WEATHER_PLUGIN = "/usr/lib/enigma2/python/Plugins/Extensions/AnimatedWeather/plugin.py"
ANIMATED_WEATHER_IPK = "/tmp/enigma2-plugin-extensions-animatedweather_0.3-r5_all.ipk"
ANIMATED_WEATHER_URL = "https://github.com/stein17/Skins-for-openATV/releases/download/animated-weather-icons-v1.4.0/enigma2-plugin-extensions-animatedweather_0.3-r5_all.ipk"
E2MDB_PLUGIN_BASE = "/usr/lib/enigma2/python/Plugins/Extensions/e2MDB/plugin"
E2MDB_CONVERTER_BASE = "/usr/lib/enigma2/python/Components/Converter/E2MDBEventInfo"

config.plugins.PLiFullNightFHD = ConfigSubsection()
config.plugins.PLiFullNightFHD.palette = ConfigSelection(default="original", choices=[
	("original", _("FullNight original")),
	("midnight", _("Midnight blue")),
	("black", _("Night black")),
	("teal", _("Teal")),
	("taupe", _("Taupe")),
	("metrix", _("Metrix Color")),
])
config.plugins.PLiFullNightFHD.transparency = ConfigSelection(default="00", choices=[
	("00", _("Opaque")),
	("18", _("Low transparency")),
	("34", _("Original transparency")),
	("50", _("High transparency")),
	("68", _("Very high transparency")),
])
config.plugins.PLiFullNightFHD.accent = ConfigSelection(default="gold", choices=[
	("gold", _("Amber")),
	("blue", _("PLi blue")),
	("cyan", _("Cyan")),
	("lightblue", _("Light blue")),
	("greyblue", _("Grey blue")),
	("lightgreen", _("Light green")),
	("green", _("Green")),
	("silver", _("Silver")),
	("white", _("White")),
])
config.plugins.PLiFullNightFHD.selected_text = ConfigSelection(default="amber", choices=[
	("amber", _("Amber")),
	("blue", _("PLi blue")),
	("cyan", _("Cyan")),
	("lightblue", _("Light blue")),
	("greyblue", _("Grey blue")),
	("lightgreen", _("Light green")),
	("green", _("Green")),
	("silver", _("Silver")),
	("white", _("White")),
])

CHANNEL_COLOR_CHOICES = [
	("selected", _("Global selected text color")),
	("foreground", _("Normal text")),
	("secondary", _("Secondary text")),
	("accent", _("Accent color")),
	("amber", _("Amber")),
	("blue", _("PLi blue")),
	("cyan", _("Cyan")),
	("lightblue", _("Light blue")),
	("greyblue", _("Grey blue")),
	("lightgreen", _("Light green")),
	("green", _("Green")),
	("silver", _("Silver")),
	("white", _("White")),
]
config.plugins.PLiFullNightFHD.channel_service_selected = ConfigSelection(default="selected", choices=CHANNEL_COLOR_CHOICES)
config.plugins.PLiFullNightFHD.channel_title_selected = ConfigSelection(default="foreground", choices=CHANNEL_COLOR_CHOICES)
config.plugins.PLiFullNightFHD.channel_title2_selected = ConfigSelection(default="selected", choices=CHANNEL_COLOR_CHOICES)
config.plugins.PLiFullNightFHD.channel_title3_selected = ConfigSelection(default="selected", choices=CHANNEL_COLOR_CHOICES)
config.plugins.PLiFullNightFHD.channel_short_selected = ConfigSelection(default="secondary", choices=CHANNEL_COLOR_CHOICES)
config.plugins.PLiFullNightFHD.channel_time_selected = ConfigSelection(default="cyan", choices=CHANNEL_COLOR_CHOICES)
config.plugins.PLiFullNightFHD.channel_remain_selected = ConfigSelection(default="cyan", choices=CHANNEL_COLOR_CHOICES)
config.plugins.PLiFullNightFHD.channel_primetime_selected = ConfigSelection(default="selected", choices=CHANNEL_COLOR_CHOICES)
config.plugins.PLiFullNightFHD.progress_style = ConfigSelection(default="blue", choices=[
	("blue", _("Blue gradient")),
	("dark_yellow", _("Dark yellow gradient")),
	("dark_grey", _("Dark grey gradient")),
	("traffic", _("Color gradient (green-yellow-red)")),
	("teal", _("Teal gradient")),
	("taupe", _("Taupe gradient")),
])
config.plugins.PLiFullNightFHD.gradients = ConfigYesNo(default=True)
config.plugins.PLiFullNightFHD.screen_names = ConfigYesNo(default=False)
config.plugins.PLiFullNightFHD.caid = ConfigSelection(default="disabled", choices=skinpart_choices("caid", _))
config.plugins.PLiFullNightFHD.vpn = ConfigSelection(default="disabled", choices=skinpart_choices("vpn", _))
config.plugins.PLiFullNightFHD.weather = ConfigSelection(default="disabled", choices=skinpart_choices("weather", _))
config.plugins.PLiFullNightFHD.weather_animated = ConfigSelection(default="disabled", choices=[
	("disabled", _("Disabled")),
	("enabled", _("Enabled")),
])
config.plugins.PLiFullNightFHD.poster_epg = ConfigSelection(default="disabled", choices=skinpart_choices("poster_epg", _))
config.plugins.PLiFullNightFHD.poster_infobar = ConfigSelection(default="disabled", choices=skinpart_choices("poster_infobar", _))


class PLiFullNightFHDChannelColorsSetup(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Channel list colors (new mode)"))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Apply"))
		self["key_yellow"] = StaticText(_("Defaults"))
		self["preview"] = StaticText("")
		self["description"] = StaticText("")
		self["label_live_preview"] = StaticText(_("Live preview"))
		self["label_selected_channel_row"] = StaticText(_("Selected channel row"))
		self["label_current_color_values"] = StaticText(_("Current color values"))
		# Real reconstructed selected channel row.  These are eLabel-backed
		# widgets so the eight configured foreground colors can update live.
		self["service_preview"] = Label("ONE HD")
		self["title_preview"] = Label(_("Current programme"))
		self["short_preview"] = Label(_("Short description"))
		self["title2_preview"] = Label(_("09:05  Next programme 1"))
		self["title3_preview"] = Label(_("10:45  Next programme 2"))
		self["primetime_preview"] = Label(_("Primetime programme"))
		self["time_preview"] = Label("07:20 - 08:10")
		self["remain_preview"] = Label("+22 min")

		self.service_entry = getConfigListEntry(_("Service name (ServiceName)"), config.plugins.PLiFullNightFHD.channel_service_selected)
		self.title_entry = getConfigListEntry(_("Event title (Title1)"), config.plugins.PLiFullNightFHD.channel_title_selected)
		self.title2_entry = getConfigListEntry(_("Next event 1 (Title2)"), config.plugins.PLiFullNightFHD.channel_title2_selected)
		self.title3_entry = getConfigListEntry(_("Next event 2 (Title3)"), config.plugins.PLiFullNightFHD.channel_title3_selected)
		self.short_entry = getConfigListEntry(_("Short description (ShortDescription1)"), config.plugins.PLiFullNightFHD.channel_short_selected)
		self.time_entry = getConfigListEntry(_("Start/end time (StartEndTime1)"), config.plugins.PLiFullNightFHD.channel_time_selected)
		self.remain_entry = getConfigListEntry(_("Remaining time (Remain)"), config.plugins.PLiFullNightFHD.channel_remain_selected)
		self.primetime_entry = getConfigListEntry(_("Primetime event (TitleP)"), config.plugins.PLiFullNightFHD.channel_primetime_selected)
		self.entries = [self.service_entry, self.title_entry, self.title2_entry, self.title3_entry, self.short_entry, self.time_entry, self.remain_entry, self.primetime_entry]
		ConfigListScreen.__init__(self, self.entries, session=session, on_change=self.changedEntry)
		self.initial_values = tuple(entry[1].value for entry in self.entries)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keyApply,
			"yellow": self.keyDefaults,
			"ok": self.keyApply,
		}, -2)
		self["config"].onSelectionChanged.append(self.selectionChanged)
		self.onLayoutFinish.append(self.selectionChanged)

	def changedEntry(self):
		self.selectionChanged()

	def _rgb(self, element):
		try:
			return channel_color_rgb(
				element.value,
				accent=config.plugins.PLiFullNightFHD.accent.value,
				selected_text=config.plugins.PLiFullNightFHD.selected_text.value,
			)
		except Exception:
			return "ffffff"

	def _setTextPreviewColor(self, widget, rgb):
		try:
			instance = self[widget].instance
			if instance is not None:
				instance.setForegroundColor(parseColor("#00%s" % rgb))
				instance.invalidate()
		except Exception as error:
			print("[PLiFullNightFHDChannelColorsSetup] Text preview failed for %s: %s" % (widget, error))

	def selectionChanged(self):
		service_rgb = self._rgb(config.plugins.PLiFullNightFHD.channel_service_selected)
		title_rgb = self._rgb(config.plugins.PLiFullNightFHD.channel_title_selected)
		title2_rgb = self._rgb(config.plugins.PLiFullNightFHD.channel_title2_selected)
		title3_rgb = self._rgb(config.plugins.PLiFullNightFHD.channel_title3_selected)
		short_rgb = self._rgb(config.plugins.PLiFullNightFHD.channel_short_selected)
		time_rgb = self._rgb(config.plugins.PLiFullNightFHD.channel_time_selected)
		remain_rgb = self._rgb(config.plugins.PLiFullNightFHD.channel_remain_selected)
		primetime_rgb = self._rgb(config.plugins.PLiFullNightFHD.channel_primetime_selected)

		self._setTextPreviewColor("service_preview", service_rgb)
		self._setTextPreviewColor("title_preview", title_rgb)
		self._setTextPreviewColor("title2_preview", title2_rgb)
		self._setTextPreviewColor("title3_preview", title3_rgb)
		self._setTextPreviewColor("short_preview", short_rgb)
		self._setTextPreviewColor("time_preview", time_rgb)
		self._setTextPreviewColor("remain_preview", remain_rgb)
		self._setTextPreviewColor("primetime_preview", primetime_rgb)
		self["preview"].setText(
			_("Service: %s #%s    Title1: %s #%s\nTitle2: %s #%s    Title3: %s #%s\nShort info: %s #%s    Time: %s #%s\nRemain: %s #%s    Primetime: %s #%s") % (
				config.plugins.PLiFullNightFHD.channel_service_selected.getText(), service_rgb.upper(),
				config.plugins.PLiFullNightFHD.channel_title_selected.getText(), title_rgb.upper(),
				config.plugins.PLiFullNightFHD.channel_title2_selected.getText(), title2_rgb.upper(),
				config.plugins.PLiFullNightFHD.channel_title3_selected.getText(), title3_rgb.upper(),
				config.plugins.PLiFullNightFHD.channel_short_selected.getText(), short_rgb.upper(),
				config.plugins.PLiFullNightFHD.channel_time_selected.getText(), time_rgb.upper(),
				config.plugins.PLiFullNightFHD.channel_remain_selected.getText(), remain_rgb.upper(),
				config.plugins.PLiFullNightFHD.channel_primetime_selected.getText(), primetime_rgb.upper(),
			)
		)

		current = self["config"].getCurrent()
		if current == self.service_entry:
			description = _("Color of the selected service name (ServiceName).")
		elif current == self.title_entry:
			description = _("Color of the selected event title (Title1).")
		elif current == self.title2_entry:
			description = _("Color of the first selected next event (Title2). Its start time uses the same color automatically.")
		elif current == self.title3_entry:
			description = _("Color of the second selected next event (Title3). Its start time uses the same color automatically.")
		elif current == self.short_entry:
			description = _("Color of the selected short description (ShortDescription1).")
		elif current == self.time_entry:
			description = _("Color of the selected start/end time (StartEndTime1).")
		elif current == self.remain_entry:
			description = _("Color of the selected remaining time (Remain).")
		else:
			description = _("Color of the selected primetime event title (TitleP).")
		self["description"].setText("%s\n%s" % (description, _("Only the new channel-list mode is affected; legacy mode remains unchanged.")))

	def keyApply(self):
		# Keep changes in memory. The main FullNight setup will save them
		# together with other settings and ask once about the GUI restart.
		self.close(True)

	def keyDefaults(self):
		for entry in self.entries:
			entry[1].value = entry[1].default
		self["config"].invalidateCurrent()
		self.selectionChanged()

	def keyCancel(self):
		for entry, value in zip(self.entries, self.initial_values):
			entry[1].value = value
		self.close(False)


class PLiFullNightFHDChannelListSetup(Screen, ConfigListScreen):
	"""Select native OpenATV channel screen and matching service-list template."""

	TEMPLATE_FILE = "/usr/share/enigma2/PLi-FullNight-FHD-stein17-Mod/skinTemplates.xml"

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Channel list design (screen / list)"))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Apply"))
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText("")
		self["description"] = StaticText("")
		self["footnote"] = StaticText("")

		# These are the ORIGINAL OpenATV settings, not plugin-specific copies.
		self.screenConfig = config.channelSelection.screenStyle
		self.listConfig = config.channelSelection.widgetStyle
		self.originalScreen = self.screenConfig.value
		self.originalList = self.listConfig.value
		self.originalListDefault = self.listConfig.default
		self.allListChoices = list(self.listConfig.getSelectionList())
		self.compatibleTemplates = self._readTemplates()
		self.lastScreen = self.screenConfig.value
		self.refreshing = False

		self.screenEntry = getConfigListEntry(_("Channel list / Screen"), self.screenConfig)
		self.listEntry = getConfigListEntry(_("Channel list / List"), self.listConfig)
		self._updateListChoices()
		ConfigListScreen.__init__(self, [self.screenEntry, self.listEntry], session=session, on_change=self.changedEntry)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keyApply,
			"ok": self.keyApply,
		}, -2)
		self["config"].onSelectionChanged.append(self.selectionChanged)
		self.onLayoutFinish.append(self.selectionChanged)

	def _readTemplates(self):
		from xml.etree.ElementTree import parse
		try:
			root = parse(self.TEMPLATE_FILE).getroot()
			result = {}
			for element in root.findall(".//template"):
				if element.get("component") != "serviceList":
					continue
				name = element.get("name", "").strip()
				if name:
					result[name] = tuple(v.strip() for v in element.get("screens", "").split(",") if v.strip())
			return result
		except Exception as error:
			print("[PLiFullNightFHDChannelListSetup] Could not read channel templates: %s" % error)
			return {}

	def _updateListChoices(self):
		# Apply only matching templates while this dialog is open. Restore the
		# native unfiltered choices on leaving so other ATV screens are unaffected.
		screen = str(self.screenConfig.value or "")
		choices = self.allListChoices
		if screen and self.compatibleTemplates:
			matching = [choice for choice in choices
				if screen in self.compatibleTemplates.get(str(choice[0]), ())]
			if matching:
				choices = matching
		value = self.listConfig.value
		default = value if any(choice[0] == value for choice in choices) else choices[0][0]
		self.listConfig.setChoices(choices, default=default)

	def changedEntry(self):
		if self.refreshing:
			return
		if self.screenConfig.value != self.lastScreen:
			self.refreshing = True
			try:
				self.lastScreen = self.screenConfig.value
				self._updateListChoices()
			finally:
				self.refreshing = False
			self["config"].invalidateCurrent()
		self.selectionChanged()

	def selectionChanged(self):
		if self["config"].getCurrent() == self.screenEntry:
			info = _("Select the channel-selection screen. Matching list layouts will be offered automatically.")
		else:
			info = _("Select a list layout compatible with the selected channel-selection screen.")
		self["description"].setText(info)
		if not self.screenConfig.value:
			self["footnote"].setText(_("Legacy mode uses the standard OpenATV service list. No FullNight preview is available."))
		else:
			self["footnote"].setText(_("Green applies the choice; save all FullNight settings later in the main setup. Red cancels."))

	def _restoreOriginalChoices(self):
		self.listConfig.setChoices(self.allListChoices, default=self.originalListDefault)

	def keyApply(self):
		self._restoreOriginalChoices()
		# Apply within the running setup only; no disk write or restart prompt.
		self.close(True)

	def keyCancel(self):
		self._restoreOriginalChoices()
		self.screenConfig.value = self.originalScreen
		self.listConfig.value = self.originalList
		self.close(False)


class PLiFullNightFHDSetup(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("PLi FullNight FHD Setup"))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Defaults"))
		self["key_blue"] = StaticText(_("About"))
		self["preview"] = StaticText("")
		self["description"] = StaticText("")
		self["label_palette"] = StaticText(_("Palette"))
		self["label_progress"] = StaticText(_("Progress"))
		self["label_accent"] = StaticText(_("Accent"))
		self["label_selection"] = StaticText(_("Selection"))
		# Live color swatches. Pixmaps are used because some Enigma2 builds do
		# not repaint an eLabel background reliably after setBackgroundColor().
		self["palette_preview"] = Pixmap()
		self["accent_preview"] = Pixmap()
		self["selected_preview"] = Pixmap()
		self["progress_preview"] = Pixmap()
		self["preview_pixmap"] = Pixmap()
		self._animated_weather_console = Console()
		self._animated_weather_installing = False
		self._animated_weather_question_open = False

		# Re-scan existing skinpart categories every time the setup is opened.
		# This allows new XML variants copied to allScreens/<category>/ to appear
		# immediately after closing/reopening this setup, without a GUI restart.
		self._refreshSkinpartChoices()

		self.palette_entry = getConfigListEntry(_("Color palette"), config.plugins.PLiFullNightFHD.palette)
		self.accent_entry = getConfigListEntry(_("Accent color"), config.plugins.PLiFullNightFHD.accent)
		self.selected_text_entry = getConfigListEntry(_("Selected text color"), config.plugins.PLiFullNightFHD.selected_text)
		self.channel_list_entry = getConfigListEntry("%s  >" % _("Channel list design (screen / list)"), ConfigNothing())
		self.channel_colors_entry = getConfigListEntry("%s  >" % _("Channel list colors (new mode)"), ConfigNothing())
		self.progress_entry = getConfigListEntry(_("Progress color"), config.plugins.PLiFullNightFHD.progress_style)
		self.screen_names_entry = getConfigListEntry(_("Show screen names"), config.plugins.PLiFullNightFHD.screen_names)
		self.caid_entry = getConfigListEntry(_("CAID information"), config.plugins.PLiFullNightFHD.caid)
		self.poster_epg_entry = getConfigListEntry(_("e2MDB poster/backdrop in EPG"), config.plugins.PLiFullNightFHD.poster_epg)
		self.poster_infobar_entry = getConfigListEntry(_("e2MDB poster/backdrop in infobar"), config.plugins.PLiFullNightFHD.poster_infobar)
		self.vpn_entry = getConfigListEntry(_("VPN and public IP"), config.plugins.PLiFullNightFHD.vpn)
		self.weather_entry = getConfigListEntry(_("Weather in infobar"), config.plugins.PLiFullNightFHD.weather)
		self.weather_animated_entry = getConfigListEntry(_("Animated weather icons"), config.plugins.PLiFullNightFHD.weather_animated)
		self.entries = [
			self.palette_entry, self.accent_entry, self.selected_text_entry, self.channel_list_entry, self.channel_colors_entry, self.progress_entry,
			 self.caid_entry, self.poster_epg_entry, self.poster_infobar_entry,
			self.vpn_entry, self.weather_entry, self.weather_animated_entry, self.screen_names_entry,
		]
		self.channel_color_entries = [
			getConfigListEntry(_("Service name (ServiceName)"), config.plugins.PLiFullNightFHD.channel_service_selected),
			getConfigListEntry(_("Event title (Title1)"), config.plugins.PLiFullNightFHD.channel_title_selected),
			getConfigListEntry(_("Next event 1 (Title2)"), config.plugins.PLiFullNightFHD.channel_title2_selected),
			getConfigListEntry(_("Next event 2 (Title3)"), config.plugins.PLiFullNightFHD.channel_title3_selected),
			getConfigListEntry(_("Short description (ShortDescription1)"), config.plugins.PLiFullNightFHD.channel_short_selected),
			getConfigListEntry(_("Start/end time (StartEndTime1)"), config.plugins.PLiFullNightFHD.channel_time_selected),
			getConfigListEntry(_("Remaining time (Remain)"), config.plugins.PLiFullNightFHD.channel_remain_selected),
			getConfigListEntry(_("Primetime event (TitleP)"), config.plugins.PLiFullNightFHD.channel_primetime_selected),
		]
		ConfigListScreen.__init__(self, self.entries, session=session, on_change=self.changedEntry)
		self.initial_theme_values = (
			config.plugins.PLiFullNightFHD.palette.value,
			config.plugins.PLiFullNightFHD.accent.value,
			config.plugins.PLiFullNightFHD.selected_text.value,
		)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow": self.keyDefaults,
			"blue": self.keyAbout,
			"ok": self.keyOK,
		}, -2)
		self["config"].onSelectionChanged.append(self.selectionChanged)
		self.onLayoutFinish.append(self.selectionChanged)

	def _refreshSkinpartChoices(self):
		for config_name, category in (
			("caid", "caid"),
			("vpn", "vpn"),
			("weather", "weather"),
			("poster_epg", "poster_epg"),
			("poster_infobar", "poster_infobar"),
		):
			entry = getattr(config.plugins.PLiFullNightFHD, config_name)
			current = entry.value
			choices = skinpart_choices(category, _)
			keys = [choice[0] if isinstance(choice, tuple) else choice for choice in choices]
			default = entry.default if entry.default in keys else ("disabled" if "disabled" in keys else keys[0])
			entry.setChoices(choices, default=default)
			if current in keys:
				entry.value = current

	def changedEntry(self):
		self.selectionChanged()
		current = self["config"].getCurrent()
		if (
			current == self.weather_animated_entry
			and config.plugins.PLiFullNightFHD.weather_animated.value == "enabled"
			and not self._animatedWeatherInstalled()
			and not self._animated_weather_installing
			and not self._animated_weather_question_open
		):
			self._askAnimatedWeatherInstall()

	def selectionChanged(self):
		current = self["config"].getCurrent()
		if current == self.palette_entry:
			description = _("Choose the dark FullNight base palette.")
		elif current == self.accent_entry:
			description = _("Choose the global accent color. This does not change the selected-text color.")
		elif current == self.selected_text_entry:
			description = _("Choose the global text color used for selected list entries independently of the accent color.")
		elif current == self.channel_list_entry:
			description = _("Choose the channel-selection screen and matching service-list layout with the existing FullNight preview. OK opens the options.")
		elif current == self.channel_colors_entry:
			description = _("Configure separate colors for service name, Title1/2/3, short description, times, remaining time and primetime in the new channel-list mode. OK opens the live preview.")
		elif current == self.progress_entry:
			description = _("Choose one global progress-bar style for EPG, infobar, player and channel list. The progress-bar border stays unchanged.")
		elif current == self.screen_names_entry:
			from Components.Language import language
			if language.getLanguage().lower().startswith('de'):
			    description = 'Nur für Support und Skin-Entwicklung. Zeigt oben rechts den technischen Enigma2-Screennamen an. Damit lassen sich Fehler im Skin schneller finden und gezielt beheben.'
			else:
			    description = 'For support and skin development only. Displays the technical Enigma2 screen name in the top-right corner. This helps identify and fix skin-related issues more quickly.'
		elif current == self.caid_entry:
			description = _("Choose which softcam and ECM details appear in the infobar.")
		elif current == self.poster_epg_entry:
			description = _("Enable the e2MDB poster/backdrop layouts in EPGSelection, Multi-EPG and the vertical EPG views.")
		elif current == self.poster_infobar_entry:
			description = _("Show e2MDB poster, backdrop or poster + backdrop in the infobar.")
		elif current == self.vpn_entry:
			description = _("Optionally show VPN state, country and public IP in the infobar.")
		elif current == self.weather_entry:
			description = _("Optionally show an OAWeather view in the infobar.")
		elif current == self.weather_animated_entry:
			description = _("Use Animated Weather by @stein17 for the FullNight weather icons. If the plugin is missing, it can be installed directly from the official GitHub release.")
		else:
			description = ""
		self["description"].setText(description)

		accent_rgb = ACCENTS.get(config.plugins.PLiFullNightFHD.accent.value, ACCENTS["gold"])
		selected_rgb = "ffffff" if config.plugins.PLiFullNightFHD.palette.value == "metrix" else SELECTED_TEXT_COLORS.get(config.plugins.PLiFullNightFHD.selected_text.value, SELECTED_TEXT_COLORS["amber"])
		self._setPalettePreview(config.plugins.PLiFullNightFHD.palette.value)
		self._setColorPreview("accent_preview", accent_rgb)
		self._setColorPreview("selected_preview", selected_rgb)
		self._setProgressPreview(config.plugins.PLiFullNightFHD.progress_style.value)
		self._setSkinpartPreview(current)

		self["preview"].setText(_("Accent: %s  #%s\nSelected text: %s  #%s\n%s · %s") % (
			config.plugins.PLiFullNightFHD.accent.getText(), accent_rgb.upper(),
			config.plugins.PLiFullNightFHD.selected_text.getText(), selected_rgb.upper(),
			config.plugins.PLiFullNightFHD.palette.getText(),
			config.plugins.PLiFullNightFHD.progress_style.getText(),
		))

	def _setPalettePreview(self, palette):
		try:
			instance = self["palette_preview"].instance
			if instance is not None:
				path = "/usr/share/enigma2/PLi-FullNight-FHD-stein17-Mod/preview/palette/%s.png" % palette
				instance.setPixmapFromFile(path)
				instance.show()
		except Exception as error:
			print("[PLiFullNightFHDSetup] Palette preview failed for %s: %s" % (palette, error))

	def _setColorPreview(self, widget, rgb):
		try:
			instance = self[widget].instance
			if instance is not None:
				path = "/usr/share/enigma2/PLi-FullNight-FHD-stein17-Mod/preview/colors/%s.png" % rgb.lower()
				instance.setPixmapFromFile(path)
				instance.show()
		except Exception as error:
			# Keep the setup usable and make a failed preview visible in debug logs.
			print("[PLiFullNightFHDSetup] Color preview failed for %s: %s" % (widget, error))

	def _setProgressPreview(self, style):
		try:
			instance = self["progress_preview"].instance
			if instance is not None:
				path = "/usr/share/enigma2/PLi-FullNight-FHD-stein17-Mod/preview/progress/%s.png" % style
				instance.setPixmapFromFile(path)
				instance.show()
		except Exception as error:
			print("[PLiFullNightFHDSetup] Progress preview failed for %s: %s" % (style, error))

	def _setSkinpartPreview(self, current):
		mapping = {
			self.caid_entry: ("caid", config.plugins.PLiFullNightFHD.caid.value),
			self.poster_epg_entry: ("poster_epg", config.plugins.PLiFullNightFHD.poster_epg.value),
			self.poster_infobar_entry: ("poster_infobar", config.plugins.PLiFullNightFHD.poster_infobar.value),
			self.vpn_entry: ("vpn", config.plugins.PLiFullNightFHD.vpn.value),
			self.weather_entry: ("weather", config.plugins.PLiFullNightFHD.weather.value),
			self.weather_animated_entry: ("weather_animated", config.plugins.PLiFullNightFHD.weather_animated.value),
		}
		try:
			instance = self["preview_pixmap"].instance
			if instance is None:
				return
			data = mapping.get(current)
			if data is None:
				instance.hide()
				return
			path = preview_path(data[0], data[1])
			if path is None:
				instance.hide()
				return
			instance.setPixmapFromFile(str(path))
			instance.show()
		except Exception as error:
			print("[PLiFullNightFHDSetup] Skinpart preview failed: %s" % error)

	def _e2MDBInstalled(self):
		try:
			from os.path import isfile
			plugin_ok = any(isfile(E2MDB_PLUGIN_BASE + suffix) for suffix in (".py", ".pyc"))
			converter_ok = any(isfile(E2MDB_CONVERTER_BASE + suffix) for suffix in (".py", ".pyc"))
			return plugin_ok and converter_ok
		except Exception:
			return False

	def _animatedWeatherInstalled(self):
		try:
			from os.path import isfile
			return isfile(ANIMATED_WEATHER_RENDERER) and isfile(ANIMATED_WEATHER_PLUGIN)
		except Exception:
			return False

	def _askAnimatedWeatherInstall(self):
		self._animated_weather_question_open = True
		self.session.openWithCallback(
			self._animatedWeatherInstallAnswer,
			MessageBox,
			_("Animated Weather by @stein17 is not installed.\nInstall it now?"),
			MessageBox.TYPE_YESNO,
			default=True,
		)

	def _animatedWeatherInstallAnswer(self, answer):
		self._animated_weather_question_open = False
		if not answer:
			config.plugins.PLiFullNightFHD.weather_animated.value = "disabled"
			self["config"].invalidateCurrent()
			self.selectionChanged()
			return
		self._animated_weather_installing = True
		self["description"].setText(_("Animated Weather is being downloaded and installed..."))
		command = (
			"rm -f '%s'; "
			"wget -O '%s' '%s' && "
			"opkg install --force-reinstall '%s'; "
			"rc=$?; rm -f '%s'; exit $rc"
		) % (ANIMATED_WEATHER_IPK, ANIMATED_WEATHER_IPK, ANIMATED_WEATHER_URL, ANIMATED_WEATHER_IPK, ANIMATED_WEATHER_IPK)
		self._animated_weather_console.ePopen(command, self._animatedWeatherInstallFinished)

	def _animatedWeatherInstallFinished(self, output, retval, extra_args=None):
		self._animated_weather_installing = False
		if retval == 0 and self._animatedWeatherInstalled():
			self.session.open(
				MessageBox,
				_("Animated Weather by @stein17 was installed successfully.\nThe animated weather skinpart can now be saved. A GUI restart is required afterwards."),
				MessageBox.TYPE_INFO,
			)
			self.selectionChanged()
			return
		config.plugins.PLiFullNightFHD.weather_animated.value = "disabled"
		self["config"].invalidateCurrent()
		self.selectionChanged()
		details = (output or "").strip()
		if len(details) > 800:
			details = details[-800:]
		message = _("Animated Weather could not be installed. The skinpart was disabled.")
		if details:
			message += "\n\n" + details
		self.session.open(MessageBox, message, MessageBox.TYPE_ERROR)

	def keyOK(self):
		if self["config"].getCurrent() == self.channel_list_entry:
			try:
				config.channelSelection.screenStyle
				config.channelSelection.widgetStyle
			except AttributeError:
				self.session.open(MessageBox, _("This OpenATV version does not provide the two new channel-selection settings."), MessageBox.TYPE_INFO)
				return
			self.session.openWithCallback(self.channelListClosed, PLiFullNightFHDChannelListSetup)
		elif self["config"].getCurrent() == self.channel_colors_entry:
			self.session.openWithCallback(self.channelColorsClosed, PLiFullNightFHDChannelColorsSetup)
		else:
			# OK on a regular setting must not save or request a restart.
			# Only the green button in the MAIN setup finalizes all changes.
			pass

	def channelListClosed(self, applied=False):
		# Changes stay in native config objects until main setup Save.
		# On cancel the sub-dialog has already restored its initial values.
		self.selectionChanged()

	def channelColorsClosed(self, applied=False):
		# A sub-dialog must never trigger keySave() or a restart prompt.
		self.selectionChanged()

	def keySave(self):
		try:
			parts = {
				"caid": config.plugins.PLiFullNightFHD.caid.value,
				"poster_epg": config.plugins.PLiFullNightFHD.poster_epg.value,
				"poster_infobar": config.plugins.PLiFullNightFHD.poster_infobar.value,
				"vpn": config.plugins.PLiFullNightFHD.vpn.value,
				"weather": config.plugins.PLiFullNightFHD.weather.value,
				"weather_animated": config.plugins.PLiFullNightFHD.weather_animated.value,
			}
			if (parts["poster_epg"] != "disabled" or parts["poster_infobar"] != "disabled") and not self._e2MDBInstalled():
				self.session.open(MessageBox, _("The e2MDB poster/backdrop skinparts require e2MDB and the E2MDBEventInfo converter. Please install/update e2MDB or disable the poster skinparts."), MessageBox.TYPE_ERROR)
				return
			if parts["weather_animated"] == "enabled" and not self._animatedWeatherInstalled():
				if self._animated_weather_installing:
					self.session.open(MessageBox, _("Animated Weather is still being installed. Please save again after the installation has finished."), MessageBox.TYPE_INFO)
				else:
					self._askAnimatedWeatherInstall()
				return
			# Validate every selected XML before changing either generated include.
			skinparts_bytes(parts)
			theme_values = (
				config.plugins.PLiFullNightFHD.palette.value,
				config.plugins.PLiFullNightFHD.accent.value,
				config.plugins.PLiFullNightFHD.selected_text.value,
			)
			# Native gradients are now the fixed FullNight rendering mode. The old
			# config key remains only for backward compatibility with existing settings.
			config.plugins.PLiFullNightFHD.gradients.value = True
			write_theme(theme_values[0], "00", True, theme_values[1], theme_values[2])
			# Background transparency is no longer user-selectable; keep old settings
			# compatible but normalize them to opaque on the next save.
			config.plugins.PLiFullNightFHD.transparency.value = "00"
			metrix_mode = config.plugins.PLiFullNightFHD.palette.value == "metrix"
			write_channel_template_colors(
service="selected" if metrix_mode else config.plugins.PLiFullNightFHD.channel_service_selected.value,
title="selected" if metrix_mode else config.plugins.PLiFullNightFHD.channel_title_selected.value,
title2="selected" if metrix_mode else config.plugins.PLiFullNightFHD.channel_title2_selected.value,
title3="selected" if metrix_mode else config.plugins.PLiFullNightFHD.channel_title3_selected.value,
short="selected" if metrix_mode else config.plugins.PLiFullNightFHD.channel_short_selected.value,
time="selected" if metrix_mode else config.plugins.PLiFullNightFHD.channel_time_selected.value,
remain="selected" if metrix_mode else config.plugins.PLiFullNightFHD.channel_remain_selected.value,
primetime="selected" if metrix_mode else config.plugins.PLiFullNightFHD.channel_primetime_selected.value,
			)
			write_progress_theme(config.plugins.PLiFullNightFHD.progress_style.value)
			write_skinparts(parts)
		except (OSError, ValueError) as error:
			self.session.open(MessageBox, _("The FullNight settings could not be saved:\n%s") % error, MessageBox.TYPE_ERROR)
			return
		for entry in self.entries + self.channel_color_entries:
			entry[1].save()
		config.plugins.PLiFullNightFHD.transparency.save()
		config.plugins.PLiFullNightFHD.gradients.save()
		# Keep support for older OpenATV versions without these native options.
		channel_config = getattr(config, "channelSelection", None)
		for name in ("screenStyle", "widgetStyle"):
			element = getattr(channel_config, name, None)
			if element is not None:
				element.save()
		configfile.save()
		self.session.openWithCallback(
			self.restartCallback,
			MessageBox,
			_("The new FullNight settings are ready. Restart the GUI now?"),
			MessageBox.TYPE_YESNO,
			default=True,
		)

	def restartCallback(self, answer):
		if answer:
			self.session.open(TryQuitMainloop, 3)
		else:
			self.close()

	def keyDefaults(self):
		for entry in self.entries:
			entry[1].value = entry[1].default
		self["config"].invalidateCurrent()
		self.selectionChanged()

	def keyAbout(self):
		self.session.open(
			MessageBox,
			_("PLi FullNight FHD by stein17\n\nA lightweight 1920 × 1080 OpenATV skin combining the original compact artwork and selectable classic layouts with native panels."),
			MessageBox.TYPE_INFO,
		)

	def keyCancel(self):
		for entry in self.entries + self.channel_color_entries:
			entry[1].cancel()
		channel_config = getattr(config, "channelSelection", None)
		for name in ("screenStyle", "widgetStyle"):
			element = getattr(channel_config, name, None)
			if element is not None:
				element.cancel()
		self.close()


def sessionstart(session, *args, **kwargs):
	if config.skin.primary_skin.value == SKIN_ENTRY:
		install_screen_name_overlay(lambda: config.plugins.PLiFullNightFHD.screen_names.value)


def main(session, **kwargs):
	if config.skin.primary_skin.value != SKIN_ENTRY:
		session.open(
			MessageBox,
			_("Please activate PLi-FullNight-FHD-stein17-Mod before opening its setup."),
			MessageBox.TYPE_INFO,
		)
		return
	session.open(PLiFullNightFHDSetup)


def plifullnight_system_menu(menuid, **kwargs):
        if menuid == "system" and config.skin.primary_skin.value == SKIN_ENTRY:
                return [
                        (
                                _("Einstellungen - PLi-FullNight-FHD-stein17-Mod"),
                                main,
                                "plifullnightfhd_setup",
                                50,
                        )
                ]
        return []


def Plugins(**kwargs):
        try:
                from Plugins.Extensions.AtileHD.plugin import atileHelper
                atileHelper.EXCLUDED_SKINS.add(SKIN_ENTRY)
        except Exception as err:
                print("[PLiFullNightFHD] AtileHD exclusion:", err)

        return [
                PluginDescriptor(
                        name=_("PLi FullNight FHD System Setup"),
                        where=PluginDescriptor.WHERE_MENU,
                        fnc=plifullnight_system_menu,
                ),
                PluginDescriptor(
                        name=_("PLi FullNight FHD Setup"),
                        description=_("Configure the PLi FullNight FHD appearance"),
                        where=PluginDescriptor.WHERE_PLUGINMENU,
                        icon="plugin.png",
                        fnc=main,
                ),
                PluginDescriptor(
                        where=PluginDescriptor.WHERE_SESSIONSTART,
                        fnc=sessionstart,
                ),
        ]
