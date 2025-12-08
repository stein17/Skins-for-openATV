##############################################################################################################################   
#    <copyright>                                                                                                             #
#    <!-- !!!!!!! DIESEN BLOCK NICHT ENTFERNEN !!!!!!! -->                                                                   #
#    <!-- BootlogoSwitcher-Plugin, Idee und Skin von @stein17, erstellt mit Hilfe des PCG -->                                #
# <!-- BootlogoSwitcher-Plugin, Idee und Skin von @stein17, optimiert von@ Mr.Servo(danke), erstellt mit Hilfe des PCG -->   #          
#    <!-- Dieses Plugin ist Freeware und darf in anderen Images verwendet werden. -->                                        #
#	 <!-- Bei Veröffentlichungen in Foren bitte den Autor angeben. -->                                                       #
#	 <!-- Sie dürfen das Plugin modifizieren, aber nicht behaupten, dass es von Ihnen stammt, oder dass es Ihre Idee ist --> #
#    <!-- Lassen Sie die Informationen im Feld „Copyright“ unverändert, fügen Sie nur etwas hinzu -->                        #
#    </copyright>                                                                                                            #
#	                                                                                                                         #
#	 <copyright>                                                                                                             #
#	 <!-- !!!!!!! BUT DO NOT REMOVE OR THIS Copyright !!!!!!! -->                                                            #
#    <!-- BootlogoSwitcher plugin, idea and skin by @stein17, created with the help of PCG ->                                #
#    <!-- BootlogoSwitcher plugin, idea and skin by @stein17, optimized by @Mr.Servo(thanks), created with the help of PCG ->#
#    <!-- This plugin is freeware and may be used in other images. -->                                                       #
#	 <!-- When posting in forums, please cite the author. -->                                                                #                                                       
#	 <!-- You may modify the plugin, but do not claim that it originated from you or that it is your idea -->                #
#    <!-- Leave the information in the “Copyright field” unchanged, only add to it -->                                       #
#    </copyright>                                                                                                            #
##############################################################################################################################

"""
Bootlogo Switcher – Enigma2 Plugin

Mit dem Bootlogo Switcher kannst du bequem:
- das Bootlogo (/usr/share/bootlogo.mvi) und
- das Radiologo (/usr/share/enigma2/radio.mvi)
auswählen und setzen.

Quelle:
- Bootlogos:   /media/hdd/Bootlogos/bootlogo
- Radiologos:  /media/hdd/Bootlogos/radiologo
Unterstützt werden .mvi, .jpg, .jpeg und .png.

Bilder werden mit ffmpeg automatisch in .mvi konvertiert.
Umschalten zwischen Bootlogo/Radiologo per Gelb/Blau oder Menü.
Nach dem Setzen kann optional ein Neustart angeboten werden.
Plugin im Erweiterungsmenü unter „Bootlogo Switcher“.

*************************************************************

Boot Logo Switcher – Enigma2 Plugin

With the Boot Logo Switcher, you can easily:
- select and set the boot logo (/usr/share/bootlogo.mvi) and
- the radio logo (/usr/share/enigma2/radio.mvi).

Source:
- Boot logos:   /media/hdd/Bootlogos/bootlogo
- Radio logos:  /media/hdd/Bootlogos/radiologo
Supported formats are .mvi, .jpg, .jpeg, and .png.

Images are automatically converted to .mvi using ffmpeg.
Switch between boot logo/radio logo via yellow/blue or menu.
After setting, a restart can be offered optionally.
Plugin in the extension menu under “Bootlogo Switcher”.

"""

from os import listdir, makedirs, chmod, access, environ, X_OK
from os.path import join, isfile, isdir, exists
from requests import get, exceptions
from shutil import copy
from subprocess import call
from twisted.internet.reactor import callInThread

from enigma import getDesktop
from Components.config import config, ConfigSubsection, ConfigText
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_CONFIG
from Plugins.Plugin import PluginDescriptor
from Tools.LoadPixmap import LoadPixmap
from Screens.LocationBox import defaultInhibitDirs, LocationBox
from Screens.Setup import Setup

from . import __version__

config.plugins.bootlogoswitcher = ConfigSubsection()
config.plugins.bootlogoswitcher.storagepath = ConfigText(default="/media/hdd/")

RESOLUTION = "FHD" if getDesktop(0).size().width() > 1300 else "HD"


class BLSglobals:
	RELEASE = f"v{__version__}"
	MODULE_NAME = __name__.split(".")[-2]
	TEMPPATH = "/tmp/Bootlogos_DL/"
	PLUGINPATH = resolveFilename(SCOPE_PLUGINS, "Extensions/BootlogoSwitcher/")  # z.B. /usr/lib/enigma2/python/Plugins/Extensions/Bootlogoswitcher/
	IMPORTFILE = join(PLUGINPATH, "downloadURLs.cfg")
	# Dauer & Bitrate ähnlich ATV .mvi
	BOOTLOGO_DURATION_SEC = 0.5      # halbe Sekunde reicht völlig
	BOOTLOGO_BITRATE_KBIT = 300      # ca. 300 kbit/s -> gute Qualität, kleine Datei

	def getUrlData(self, url, timeout=(3.05, 6), binary=False):
		errMsg, result = "", {} if binary else None
		headers = {"accept": "application/json"}
		try:
			response = get(url, headers=headers, timeout=timeout)
			errMsg, result = ("", response) if response.ok else (f"[{self.MODULE_NAME}] Server access ERROR, response code: {response.raise_for_status()}", None)
		except exceptions.RequestException as errMsg:
			return errMsg, result
		return errMsg, result.content if binary else result.json()

	def getStorageBasePath(self):  # z.B. /media/hdd/Bootlogos/ oder /media/usb/Bootlogos/ oder /tmp/Bootlogos/
		return f"/tmp/Bootlogos/" if config.plugins.bootlogoswitcher.storagepath.value == "/" else f"{config.plugins.bootlogoswitcher.storagepath.value}Bootlogos/"

	def getCurrentStoragePath(self):  # z.B. /media/hdd/Bootlogos/bootlogo/ oder /media/hdd/Bootlogos/radiologo/
		return f"{self.getStorageBasePath()}bootlogo/" if self.mode == "boot" else f"{self.getStorageBasePath()}radiologo/"

	def getCurrentConfigFile(self):  # z.B. /etc/enigma2/bootlogo.mvi oder /etc/enigma2/radio.mvi
		configPath = resolveFilename(SCOPE_CONFIG)  # /etc/enigma2/
		return f"{configPath}bootlogo.mvi" if self.mode == "boot" else f"{configPath}radio.mvi"  # z.B. /etc/enigma2/bootlogo.mvi

	def updateCurrentLogoLabel(self):
		target = self.getCurrentConfigFile()
		text = "Aktuelles Bootlogo:" if self.mode == "boot" else "Aktuelles Radiologo:"
		message = f"{text} {target}" if exists(target) else f"{text} (nicht gefunden)"
		self["currentLabel"].setText(message)

	def updateModeTexts(self, dirStr):
		sourcepath = self.getCurrentStoragePath()
		message = f"Bootlogos {dirStr} {sourcepath}" if self.mode == "boot" else f"Radiologos {dirStr} {sourcepath}"
		self["info"].setText(message)
		self.setTitle("Bootlogo Switcher – Radiologo")

	def switchToBootlogo(self, dirStr):
		self.mode = "boot"
		self.updateModeTexts(dirStr)
		self.updateCurrentLogoLabel()
		self.reloadLists()  # Beim Umschalten Liste aus dem Bootlogo-Ordner neu einlesen

	def switchToRadiologo(self, dirStr):
		self.mode = "radio"
		self.updateModeTexts(dirStr)
		self.updateCurrentLogoLabel()
		self.reloadLists()  # Beim Umschalten Liste aus dem Radiologo-Ordner neu einlesen


class BLSmain(Screen, BLSglobals):
	skin = """
	<screen name="BLSmain" position="center,center" size="1140,644" title="Bootlogo Switcher" resolution="1280,720" flags="wfNoBorder" backgroundColor="#20000000">
		<eLabel name="Background" position="0,0" size="1140,644" zPosition="-10" backgroundColor="#20000000" halign="center" />
		<widget font="Regular; 22" halign="right" position="920,10" render="Label" size="200,40" source="global.CurrentTime" transparent="1" foregroundColor="white" backgroundColor="#20000000">
			<convert type="ClockToText">Format:%a %d.%m. %H:%M</convert>
		</widget>
		<widget name="info" position="140,10" size="800,40" font="Regular;22" halign="left" valign="center" transparent="1" foregroundColor="white" backgroundColor="#20000000" />
		<widget source="logoList" render="Listbox" position="20,70" size="640,450" itemHeight="28" font="Regular; 22" scrollbarMode="showOnDemand" transparent="1" foregroundColor="white" backgroundColor="#20000000" backgroundColorSelected="white" foregroundColorSelected="black">
			<convert type="StringList" />
		</widget>
		<widget name="previewLabel" position="680,70" size="440,80" font="Regular;22" transparent="1" foregroundColor="white" backgroundColor="#20000000" halign="left" valign="bottom" />
		<widget name="preview" position="680,170" size="440,248" zPosition="2" alphatest="on" scale="1" />
		<widget name="currentLabel" position="680,440" size="440,60" font="Regular;20" transparent="1" foregroundColor="white" backgroundColor="#20000000" />
		<ePixmap position="26,10" size="100, 40" pixmap="~logo.png" zPosition="2" alphatest="blend" scale="1" />
		<eLabel name="line" position="0,60" size="1140, 1" zPosition="2" backgroundColor="#999999" halign="center" />
		<eLabel name="line" position="0,586" size="1140, 1" zPosition="2" backgroundColor="#999999" halign="center" />
		<widget source="key_red" render="Label" position="20,600" size="200,30" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel name="red_bg" position="18,598" size="204,34" backgroundColor="red" cornerRadius="4" zPosition="-2" />
		<eLabel name="red_bg_center" position="20,600" size="200,30" backgroundColor="black" cornerRadius="4" zPosition="-1" />
		<widget source="key_green" render="Label" position="250,600" size="200,30" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel name="green_bg" position="248,598" size="204,34" backgroundColor="green" cornerRadius="4" zPosition="-2" />
		<eLabel name="green_bg_center" position="250,600" size="200,30" backgroundColor="black" cornerRadius="4" zPosition="-1" />
		<widget source="key_yellow" render="Label" position="480,600" size="200,30" zPosition="1" font="Regular; 20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel name="yellow_bg" position="478,598" size="204,34" backgroundColor="yellow" cornerRadius="4" zPosition="-2" />
		<eLabel name="yellow_bg_center" position="480,600" size="200,30" backgroundColor="black" cornerRadius="4" zPosition="-1" />
		<widget source="key_blue" render="Label" position="710,600" size="200,30" zPosition="1" font="Regular; 20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel name="blue_bg" position="708,598" size="204,34" backgroundColor="blue" cornerRadius="4" zPosition="-2" />
		<eLabel name="blue_bg_center" position="710,600" size="200,30" backgroundColor="black" cornerRadius="4" zPosition="-1" />
		<ePixmap position="940,602" size="45,26" zPosition="10" pixmap="~ok.png" transparent="1" alphatest="blend" scale="1" />
		<ePixmap position="1010,602" size="45,26" zPosition="10" pixmap="~menu.png" transparent="1" alphatest="blend" scale="1" />
		<ePixmap position="1080,602" size="45,26" zPosition="10" pixmap="~exit.png" transparent="1" alphatest="blend" scale="1" />
	</screen>
	"""

	def __init__(self, session):
		self.skin = self.skin.replace("~", f"{self.PLUGINPATH}pics/{RESOLUTION}/")
		Screen.__init__(self, session)
		self.session = session
		self.list = []
		self.mode = "boot"
		self["info"] = Label("")
		self["previewLabel"] = Label("Vorschau")
		self["preview"] = Pixmap()
		self["currentLabel"] = Label("")
		self["key_red"] = StaticText("Download")
		self["key_green"] = StaticText("Menü")
		self["key_yellow"] = StaticText("Modus Bootlogo")
		self["key_blue"] = StaticText("Modus Radiologo")
		self["logoList"] = List([])
		self["logoList"].onSelectionChanged.append(self.updatePreview)
		self["actions"] = ActionMap(["OkCancelActions", "MenuActions", "ColorActions"], {
			"ok": self.applyLogo,
			"cancel": self.close,
			"menu": self.openModeMenu,   # Modus/Liste
			"red": self.keyRed,
			"green": self.keyGreen,
			"yellow": self.keyYellow,
			"blue": self.keyBlue
			},
			-1,
		)
		self.downloadUrls = self.readDownloadUrls()
		self.createStoragePaths()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.switchToBootlogo("aus")
		self.reloadLists()

	def readDownloadUrls(self):
		downloadUrls = []
		if isfile(self.IMPORTFILE):
			try:
				with open(self.IMPORTFILE) as file:
					for line in file.read().split("\n"):
						if line.startswith("http") and "#" not in line:
							downloadUrls.append(line.strip())
			except OSError as errMsg:
				print(f"[{self.MODULE_NAME}] ERROR in class 'BLSglobals:readDownloadUrls': {errMsg}!")
		else:
			print(f"[{self.MODULE_NAME}] ERROR in class 'BLSglobals:readDownloadUrls': file '{self.IMPORTFILE}' not found!")
		return downloadUrls

	def createStoragePaths(self):  # Verzeichnisse erstellen falls sie fehlen
		try:
			storagePath = self.getStorageBasePath()
			for path in (storagePath, f"{storagePath}bootlogo/", f"{storagePath}radiologo/", self.TEMPPATH):
				if not isdir(path):
					makedirs(path, exist_ok=True)
		except OSError as errMsg:
			print(f"[{self.MODULE_NAME}] ERROR in class 'BLSmain:createStoragePaths': {errMsg}!")
			return errMsg
		return ""

	def openModeMenu(self):
		opts = [
			("Bootlogo ändern (bootlogo.mvi)", "boot"),
			("Radiologo ändern (radio.mvi)", "radio"),
			("Liste neu einlesen", "reload"),
			("Einstellungen", "config")]
		self.session.openWithCallback(self.onModeMenuChoice, ChoiceBox, title="Was möchten Sie ändern?", list=opts)

	def onModeMenuChoice(self, choice):
		if choice and len(choice) > 1:
			action = choice[1]
			if action == "boot":
				self.switchToBootlogo("aus")
				self.reloadLists()
			elif action == "radio":
				self.switchToRadiologo("aus")
				self.reloadLists()
			elif action == "reload":
				self.reloadLists()
			elif action == "config":
				self.session.open(BLSsetup)

	def reloadLists(self):  # Listen / Vorschau
		entries = []
		self.list = []
		sourcepath = self.getCurrentStoragePath()
		try:
			files = listdir(sourcepath)
		except OSError:
			files = []
		for fname in sorted(files, key=lambda x: x.lower()):
			full = join(sourcepath, fname)
			if not isfile(full):
				continue
			lower = fname.lower()
			if lower.endswith(".mvi"):
				ftype = "mvi"
				desc = "MVI Logo"
				preview = None  # keine echte Vorschau für MVI
			elif lower.endswith(".jpg") or lower.endswith(".jpeg") or lower.endswith(".png"):
				ftype = "image"
				desc = "Bild (wird in .mvi umgewandelt)"
				preview = full
			else:
				continue
			display = f"{fname}  [{'MVI' if ftype == 'mvi' else 'Bild'}]"
			data = (fname, full, ftype, preview, desc)
			entries.append((display, desc))
			self.list.append(data)
		if not entries:
			entries = [("Keine Dateien gefunden", f"Bitte lege .mvi / .jpg / .png in {sourcepath} ab.")]
		self["logoList"].setList(entries)
		self.updatePreview()

	def getCurrentEntry(self):
		idx = self["logoList"].getIndex()
		if idx is None:
			return None
		if idx < 0 or idx >= len(self.list):
			return None
		return self.list[idx]

	def updatePreview(self):
		entry = self.getCurrentEntry()
		if not entry:
			self["preview"].hide()
			self["previewLabel"].setText("Vorschau")
			return
		fname, full, ftype, preview, desc = entry
		self["previewLabel"].setText(f"Vorschau: {fname}")
		if ftype == "image" and preview and exists(preview):
			try:
				pix = LoadPixmap(preview)
				if pix and self["preview"].instance is not None:  # Pixmap wird vom Skin auf 440x248 skaliert
					self["preview"].instance.setPixmap(pix)
					self["preview"].instance.show()
			except Exception:
				self["preview"].hide()
		else:  # Keine Vorschau verfügbar (z.B. MVI)
			self["preview"].hide()

	def updateCurrentLogoLabel(self):
		target = self.getCurrentConfigFile()
		text = "Aktuelles Bootlogo:" if self.mode == "boot" else "Aktuelles Radiologo:"
		message = f"{text} {target}" if exists(target) else f"{text} (nicht gefunden)"
		self["currentLabel"].setText(message)

	def applyLogo(self):  # Anwenden / Konvertieren
		entry = self.getCurrentEntry()
		if not entry:
			self.session.open(MessageBox, "Keine gültige Datei ausgewählt.", MessageBox.TYPE_ERROR, timeout=3, close_on_any_key=True)
			return
		fname, full, ftype, preview, desc = entry
		if ftype == "mvi":
			self.copyTarget(full)
		else:
			self.convertImageToMvi(full)

	def copyTarget(self, source):
		target = self.getCurrentConfigFile()
		try:
			copy(source, target)
			chmod(target, 0o644)
		except OSError as errMsg:
			self.session.open(MessageBox, f"Konnte Logo nicht kopieren:\n{errMsg}", MessageBox.TYPE_ERROR, timeout=5, close_on_any_key=True)
			return
		self.updateCurrentLogoLabel()
		self.askForReboot()

	def convertImageToMvi(self, src):
		ffmpeg = self.findFFmpeg()
		if not ffmpeg:  # ffmpeg nicht gefunden -> Installationsdialog anbieten
			self.installFFmpeg()
			return
		tmp_mvi = "/tmp/bootlogo_tmp.mvi"
		duration = str(self.BOOTLOGO_DURATION_SEC)  # Dauer und Bitrate aus den Konstanten nehmen
		bitrate = f"{self.BOOTLOGO_BITRATE_KBIT}k"
		cmd = [
			ffmpeg,
			"-y",
			"-loop", "1",
			"-i", src,
			"-t", duration,
			"-r", "25",
			"-s", "1920x1080" if RESOLUTION == "FHD" else "1280x720",
			"-pix_fmt", "yuv420p",
			"-vcodec", "mpeg1video",
			"-b:v", bitrate,
			"-maxrate", bitrate,
			"-bufsize", "2000k",
			"-an",
			"-f", "mpeg1video",
			tmp_mvi
		]
		try:
			ret = call(cmd)
		except Exception as errMsg:
			self.session.open(MessageBox, f"Fehler beim Ausführen von ffmpeg:\n{errMsg}", MessageBox.TYPE_ERROR, timeout=5, close_on_any_key=True)
			return
		if ret != 0 or not exists(tmp_mvi):
			self.session.open(MessageBox, f"ffmpeg konnte kein gültiges .mvi erzeugen.\nRückgabecode: {ret}", MessageBox.TYPE_ERROR, timeout=5)
			return
		self.copyTarget(tmp_mvi)

	def findFFmpeg(self):  # ffmpeg / Installation
		paths = ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/bin/ffmpeg"]
		for path in environ.get("PATH", "").split(":"):  # zusätzliche PATH-Suche
			if path:
				paths.append(join(path, "ffmpeg"))
				break
		for candidate in paths:
			if candidate and exists(candidate) and access(candidate, X_OK):
				return candidate

	def installFFmpeg(self):
		def doInstall():
			cmd = "opkg update && opkg install ffmpeg"
			ret = call(cmd, shell=True)
			if ret == 0:
				self.session.open(MessageBox, "ffmpeg wurde erfolgreich installiert.", MessageBox.TYPE_INFO, timeout=4, close_on_any_key=True)
			else:
				self.session.open(MessageBox, f"Installation von ffmpeg ist fehlgeschlagen.\nFehlercode: {ret}", MessageBox.TYPE_ERROR, timeout=6, close_on_any_key=True)
		self.session.openWithCallback(lambda ans: doInstall() if ans else None, MessageBox, "ffmpeg ist nicht installiert.\nSoll es jetzt automatisch installiert werden?", MessageBox.TYPE_YESNO)

	def askForReboot(self):  # Neustart
		which = "Bootlogo" if self.mode == "boot" else "Radiologo"
		self.session.openWithCallback(self.onRebootAnswer, MessageBox, f"{which} wurde gesetzt.\nSoll die Box jetzt neu gestartet werden?", MessageBox.TYPE_YESNO, timeout=10, close_on_any_key=True)

	def onRebootAnswer(self, answer):
		if answer:
			self.session.open(TryQuitMainloop, 2)

	def keyRed(self):
		if self.downloadUrls:
			self.session.open(BLSdownload, self.downloadUrls)
		else:
			self.session.open(MessageBox, f"FEHLER: Datei '{self.IMPORTFILE} nicht gefunden!\n\n Somit ist keine Downloadadresse verfügbar.", MessageBox.TYPE_ERROR, timeout=5, close_on_any_key=True)

	def keyGreen(self):
		self.openModeMenu()

	def keyYellow(self):
		self.switchToBootlogo("aus")

	def keyBlue(self):
		self.switchToRadiologo("aus")


class BLSsetup(Setup):
	def __init__(self, session):
		Setup.__init__(self, session, "BLSsetup", plugin="Extensions/BootlogoSwitcher", PluginLanguageDomain="BootlogoSwitcher")

	def keySelect(self):
		if self.getCurrentItem() == config.plugins.bootlogoswitcher.storagepath:
			self.session.openWithCallback(self.keySelectCB, BLSlocationBox, currDir=config.plugins.bootlogoswitcher.storagepath.value)
			return
		Setup.keySelect(self)

	def keySelectCB(self, path):
		if path is not None:
			path = join(path, "")
			config.plugins.bootlogoswitcher.storagepath.value = path
		self["config"].invalidateCurrent()
		self.changedEntry()


class BLSdownload(Screen, BLSglobals):
	skin = """
	<screen name="BLSdownload" position="center,center" size="1160,644" title="Bootlogo Switcher" resolution="1280,720" flags="wfNoBorder" backgroundColor="#20000000">
		<eLabel name="Background" position="0,0" size="1160,644" zPosition="-10" backgroundColor="#20000000" halign="center" />
		<widget font="Regular; 22" halign="right" position="940,10" render="Label" size="200,40" source="global.CurrentTime" transparent="1" foregroundColor="white" backgroundColor="#20000000">
			<convert type="ClockToText">Format:%a %d.%m. %H:%M</convert>
		</widget>
		<widget name="info" position="140,10" size="800,40" font="Regular;22" halign="left" valign="center" transparent="1" foregroundColor="white" backgroundColor="#20000000" />
		<widget source="logoList" render="Listbox" position="20,70" size="650,450"  foregroundColor="white" backgroundColor="#20000000" backgroundColorSelected="white" foregroundColorSelected="black" transparent="1" scrollbarMode="showOnDemand" >
			<convert type="TemplatedMultiContent">{"template": [
				MultiContentEntryText(pos=(4,2), size=(440,30), font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=0),  # picName
				MultiContentEntryText(pos=(430,2), size=(70,30), font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=2),  # fileType
				MultiContentEntryText(pos=(500,2), size=(100,30), font=0, flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=1),  # picSize
				MultiContentEntryPixmapAlphaBlend(pos=(620,4), size=(24,24), flags=BT_SCALE, png="~checkbox.png"),  # checkbox
				MultiContentEntryText(pos=(622,7), size=(16,16), font=1, color=MultiContentTemplateColor(4), color_sel=MultiContentTemplateColor(4), flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=3)  # checkmark
				],
				"fonts": [gFont("Regular",20),gFont("Regular",22)],
				"itemHeight":32
				}</convert>
		</widget>
		<widget name="previewLabel" position="700,70" size="440,80" font="Regular;22" transparent="1" foregroundColor="white" backgroundColor="#20000000" halign="left" valign="bottom" />
		<widget name="preview" position="700,170" size="440,248" zPosition="2" alphatest="on" scale="1" />
		<widget name="currentLabel" position="700,440" size="440,60" font="Regular;20" transparent="1" foregroundColor="white" backgroundColor="#20000000" />
		<ePixmap position="26,10" size="100, 40" pixmap="~logo.png" zPosition="2" alphatest="blend" scale="1" />
		<eLabel name="line" position="0,60" size="1160, 1" zPosition="2" backgroundColor="#999999" halign="center" />
		<eLabel name="line" position="0,586" size="1160, 1" zPosition="2" backgroundColor="#999999" halign="center" />
		<widget source="key_red" render="Label" position="20,600" size="200,30" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel name="red_bg" position="18,598" size="204,34" backgroundColor="red" cornerRadius="4" zPosition="-2" />
		<eLabel name="red_bg_center" position="20,600" size="200,30" backgroundColor="black" cornerRadius="4" zPosition="-1" />
		<widget source="key_green" render="Label" position="250,600" size="200,30" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel name="green_bg" position="248,598" size="204,34" backgroundColor="green" cornerRadius="4" zPosition="-2" />
		<eLabel name="green_bg_center" position="250,600" size="200,30" backgroundColor="black" cornerRadius="4" zPosition="-1" />
		<widget source="key_yellow" render="Label" position="480,600" size="200,30" zPosition="1" font="Regular; 20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel name="yellow_bg" position="478,598" size="204,34" backgroundColor="yellow" cornerRadius="4" zPosition="-2" />
		<eLabel name="yellow_bg_center" position="480,600" size="200,30" backgroundColor="black" cornerRadius="4" zPosition="-1" />
		<widget source="key_blue" render="Label" position="710,600" size="200,30" zPosition="1" font="Regular; 20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel name="blue_bg" position="708,598" size="204,34" backgroundColor="blue" cornerRadius="4" zPosition="-2" />
		<eLabel name="blue_bg_center" position="710,600" size="200,30" backgroundColor="black" cornerRadius="4" zPosition="-1" />
		<ePixmap position="960,602" size="45,26" zPosition="10" pixmap="~ok.png" transparent="1" alphatest="blend" scale="1" />
		<ePixmap position="1030,602" size="45,26" zPosition="10" pixmap="~menu.png" transparent="1" alphatest="blend" scale="1" />
		<ePixmap position="1100,602" size="45,26" zPosition="10" pixmap="~exit.png" transparent="1" alphatest="blend" scale="1" />
	</screen>
	"""

	def __init__(self, session, downloadUrls):
		self.skin = self.skin.replace("~", f"{self.PLUGINPATH}pics/{RESOLUTION}/")
		Screen.__init__(self, session)
		self.session = session
		self.downloadUrls = downloadUrls
		self.deselect, self.downloadActive = True, False
		self.logoLists = [["", 0, "", False]]  # [picName, picSize, picUrl, checked]
		self.mode = "boot"
		self["info"] = Label("")
		self["previewLabel"] = Label("Vorschau")
		self["preview"] = Pixmap()
		self["currentLabel"] = Label("")
		self["key_red"] = StaticText("Alle auswählen")
		self["key_green"] = StaticText("Auswahl kopieren")
		self["key_yellow"] = StaticText("Bootlogo")
		self["key_blue"] = StaticText("Radiologo")
		self["logoList"] = List()
		self["logoList"].onSelectionChanged.append(self.updatePreview)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {
			"ok": self.keyOk,
			"cancel": self.close,
			"red": self.keyRed,
			"green": self.keyGreen,
			"yellow": self.keyYellow,
			"blue": self.keyBlue
			},
			-1,
		)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		callInThread(self.reloadLists)
		self.switchToBootlogo("nach")
		self.updateSkinList()
		self.updatePreview()

	def reloadLists(self):  # threaded
		if self.downloadUrls:
			logoLists = []
			for downloadUrl in self.downloadUrls:
				errMsg, picDicts = self.getUrlData(downloadUrl)
				if not errMsg:
					if picDicts:
						for picDict in picDicts:
							if picDict.get("type", "") == "file":
								logoLists.append([picDict.get("name", ""), picDict.get("size", 0), picDict.get("download_url", ""), False])
				else:
					print(f"[{self.MODULE_NAME}] ERROR in class 'BLSdownload:reloadLists': {errMsg}!")
			self.logoLists = logoLists
			self.downloadUrls = []
		self.updateSkinList(initial=True)
		self.updatePreview()

	def updateSkinList(self, initial=False):
		skinList = []
		for index, picData in enumerate(self.logoLists):  # (picName, picSize, picUrl, checked)
			picName = picData[0]
			picSize = f"{round(int(picData[1]) / 1024)} KB"
			checked = False if initial else self.logoLists[index][3]
			checkmark = "✔" if checked else "✘"  # alternatively "✓", "✗"
			color = int("0x0004c81b", 0) if checked else int("0x00f50808", 0)
			skinList.append((picName, picSize, "[Bild]", checkmark, color))
		self["logoList"].updateList(skinList)

	def getCurrentEntry(self):
		index = self["logoList"].getIndex()
		if index is None:
			return None
		if index < 0 or index >= len(self.logoLists):
			return None
		return self.logoLists[index]

	def updatePreview(self):
		entry = self.getCurrentEntry()
		if not entry:
			self["preview"].hide()
			self["previewLabel"].setText("Vorschau")
			return
		picName, picUrl = entry[0], entry[2]
		callInThread(self.updateEntry, picName, picUrl)

	def updateEntry(self, picName, picUrl):  # threaded
		self.downloadActive = True
		fileName = join(self.TEMPPATH, picName)
		if not isfile(fileName):
			errMsg, pixmap = self.getUrlData(picUrl, binary=True)
			if pixmap:
				try:
					with open(fileName, "wb") as file:
						file.write(pixmap)
				except OSError as errMsg:
					print(f"[{self.MODULE_NAME}] ERROR in class 'BLSdownload:updateEntry': {errMsg}!")
		if isfile(fileName):
			try:
				pixmap = LoadPixmap(fileName)
				if pixmap and self["preview"].instance is not None:  # Pixmap wird vom Skin auf 440x248 skaliert
					self["preview"].instance.setPixmap(pixmap)
					self["preview"].instance.show()
			except Exception:
				self["preview"].hide()
			self["previewLabel"].setText(f"Vorschau: {picName}")
		else:  # Keine Vorschau verfügbar (z.B. MVI)
			self["preview"].hide()
		self.downloadActive = False

	def keyOk(self):
		currIndex = self["logoList"].getCurrentIndex()
		if self.logoLists:
			currList = list(self.logoLists[currIndex])  # Workaround, because tuples cannot be modified
			currList[3] = not currList[3]
			self.logoLists[currIndex] = tuple(currList)
		self.updateSkinList()

	def keyRed(self):
		if self.logoLists:
			if self.deselect:
				for index in range(len(self.logoLists)):
					self.logoLists[index][3] = True
				self["key_red"].setText("Alle auswählen")
			else:
				for index in range(len(self.logoLists)):
					self.logoLists[index][3] = False
				self["key_red"].setText("Alle abwählen")
		self.deselect = not self.deselect
		self.updateSkinList()

	def keyGreen(self):
		if self.downloadActive:
			self.session.open(MessageBox, "Download ist gerade in Arbeit!\n\nBitte gleich nochmal versuchen.", MessageBox.TYPE_ERROR, timeout=1, close_on_any_key=True)
		else:
			success, cached, failed = [], [], []
			for logoList in self.logoLists:
				picName, checked = logoList[0], logoList[3]
				if checked:
					target = join(self.getCurrentStoragePath(), picName)
					if not isfile(target):
						source = join(self.TEMPPATH, picName)
						try:
							copy(source, target)
							chmod(target, 0o644)
							success.append(picName)
						except OSError as errMsg:
							failed.append((picName, str(errMsg)))
							self.session.open(MessageBox, f"Konnte Logo nicht kopieren:\n{errMsg}", MessageBox.TYPE_ERROR, timeout=5, close_on_any_key=True)
					else:
						cached.append(picName)
			msg = ""
			if success:
				msg += f"ERFOLGREICH HERUNTERGELADENE LOGOS:\n{'\n'.join(success)}\n\n"
			if cached:
				msg += f"BEREITS IM CACHE VORHANDENE LOGOS:\n{"\n".join(cached)}\n\n"
			if failed:
				msg += f"NICHT HERUNTERLADBARE LOGOS:\n{'\n'.join(failed)}\n\n"
			self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout=30, close_on_any_key=True)

	def keyYellow(self):
		self.switchToBootlogo("nach")

	def keyBlue(self):
		self.switchToRadiologo("nach")


class BLSlocationBox(LocationBox):
	def __init__(self, session, currDir):
		inhibit = defaultInhibitDirs[:]
		inhibit.remove("/usr")
		inhibit.remove("/share")
		if currDir == "":
			currDir = None
		LocationBox.__init__(self, session, text="Wo sollen die Vorlagen der Bootlogos gespeichert werden?", currDir=currDir, inhibitDirs=inhibit)
		self.skinName = ["LocationBox"]


def main(session, **kwargs):
	session.open(BLSmain)


def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name="Bootlogo Switcher",
			description="Bootlogo / Radiologo auswählen oder aus Bild erzeugen",
			icon=f"pics/{RESOLUTION}/plugin.png",
			where=PluginDescriptor.WHERE_PLUGINMENU,
			fnc=main,
		)
	]
