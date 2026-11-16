
##############################################################################################################################
# <copyright>                                                                                                                #
#  <!-- !!!!!!! DIESEN BLOCK NICHT ENTFERNEN !!!!!!! -->                                                                     #
#  <!-- BootlogoSwitcher-Plugin, Idee und Skin von @stein17, optimiert von@ Mr.Servo(danke), erstellt mit Hilfe des PCG -->  #
#  <!-- Dieses Plugin ist Freeware und darf in anderen Images verwendet werden. -->                                          #
#  <!-- Bei Veröffentlichungen in Foren bitte die Autoren angeben. -->                                                       #
#  <!-- Sie dürfen das Plugin modifizieren, aber nicht behaupten, dass es von Ihnen stammt, oder dass es Ihre Idee ist -->   #
#  <!-- Lassen Sie die Informationen im Feld „Copyright“ unverändert, fügen Sie nur etwas hinzu -->                          #
# </copyright>                                                                                                               #
#
# <copyright>                                                                                                                #
#  <!-- !!!!!!! BUT DO NOT REMOVE OR THIS Copyright !!!!!!! -->                                                              #
#  <!-- BootlogoSwitcher plugin, idea and skin by @stein17, optimized by @Mr.Servo(thanks), created with the help of PCG ->  #
#  <!-- This plugin is freeware and may be used in other images. -->                                                         #
#  <!-- When posting in forums, please cite the author. -->                                                                  #
#  <!-- You may modify the plugin, but do not claim that it originated from you or that it is your idea -->                  #
#  <!-- Leave the information in the “Copyright field” unchanged, only add to it -->                                         #
# </copyright>                                                                                                               #
##############################################################################################################################
# Bootlogo Switcher 1.1-test13 – native schnelle Bildvorschau per ePicLoad.

# PYTHON IMPORTS
from glob import glob
from hashlib import sha256
from json import dump, load
from os import chmod, close, fdopen, fsync, listdir, makedirs, readlink, replace, symlink, unlink
from os.path import join, exists, dirname, getsize, isfile, islink, realpath, ismount, normpath, basename, splitext
from requests import get, RequestException
from shutil import copyfileobj, which
from subprocess import run
from tempfile import mkstemp
from time import strftime
from twisted.internet.reactor import callLater, callInThread, callFromThread

# ENIGMA IMPORTS
from enigma import getDesktop, ePicLoad
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigText
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Screens.Console import Console
from Screens.LocationBox import defaultInhibitDirs, LocationBox
from Screens.Setup import Setup
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Screens.ChoiceBox import ChoiceBox
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_GUISKIN
from Tools.LoadPixmap import LoadPixmap

# PLUGIN IMPORTS
from . import __version__

# Aktuelle OpenATV-Images zeigen bei DVB/SAT-Radio ein PNG ueber
# Screens.RdsDisplay.DABSlideDisplay (nicht zwingend die radio.mvi).
# Wir nutzen einen Skin-Override in /etc und aendern NICHT /usr/share.
BACKUP_DIR = "/etc/enigma2/BootlogoSwitcher"
TARGETS = {"boot": "/etc/enigma2/bootlogo.mvi", "radio": "/etc/enigma2/radio.mvi"}
GUI_RADIO_FACTORY = "/usr/share/enigma2/icons/default_radio.png"
GUI_RADIO_META = join(BACKUP_DIR, "radiologo_gui.json")
GUI_RADIO_ORIGINAL = join(BACKUP_DIR, "radiologo_gui_original.png")
GUI_RADIO_PREVIOUS = join(BACKUP_DIR, "radiologo_gui_vorheriger_override.png")


class BackupError(Exception):
	pass


def _hash(path):
	h = sha256()
	with open(path, "rb") as fh:
		for block in iter(lambda: fh.read(262144), b""):
			h.update(block)
	return h.hexdigest()


def _copy_atomic(source, target):
	parent = dirname(target)
	makedirs(parent, exist_ok=True)
	tmp = None
	try:
		fd, tmp = mkstemp(prefix=".bls-", dir=parent)
		with fdopen(fd, "wb") as out, open(source, "rb") as src:
			copyfileobj(src, out, 262144)
			out.flush()
			fsync(out.fileno())
		if getsize(tmp) == 0:
			raise BackupError(f"Quelldatei ist leer: {source}")
		chmod(tmp, 0o644)
		replace(tmp, target)
		tmp = None
	finally:
		if tmp and exists(tmp):
			unlink(tmp)


def _write_json_atomic(value, path):
	parent = dirname(path)
	makedirs(parent, exist_ok=True)
	fd, tmp = mkstemp(prefix=".bls-meta-", dir=parent)
	try:
		with fdopen(fd, "w") as out:
			dump(value, out, indent=2, ensure_ascii=False, sort_keys=True)
			out.flush()
			fsync(out.fileno())
		chmod(tmp, 0o600)
		replace(tmp, path)
		tmp = None
	finally:
		if tmp and exists(tmp):
			unlink(tmp)


def _paths(mode):
	if mode not in TARGETS:
		raise BackupError("Unbekannte Logo-Art")
	prefix = "bootlogo" if mode == "boot" else "radiologo"
	return (join(BACKUP_DIR, prefix + ".json"),
			join(BACKUP_DIR, prefix + "_original.mvi"),
			join(BACKUP_DIR, prefix + "_ziel_original.mvi"))


def _skin_name():
	try:
		skin = str(config.skin.primary_skin.value)
		path = dirname(skin.strip("/"))
		return path if path and ".." not in path.split("/") else ""
	except Exception:
		return ""


def effective_source(mode):
	"""Approximation der OpenATV-Suchreihenfolge; real vorhandene Quelle."""
	if mode == "radio":
		candidates = [TARGETS[mode]]
		try:
			candidates.append(resolveFilename(SCOPE_GUISKIN, "radio.mvi"))
		except Exception:
			pass
		candidates += ["/usr/share/enigma2/skin_default/radio.mvi", "/usr/share/enigma2/radio.mvi", "/usr/share/radio.mvi"]
	else:
		skin = _skin_name()
		cfg = "/etc/enigma2"
		share = "/usr/share/enigma2"
		candidates = []
		if skin:
			candidates.append(join(cfg, skin, "bootlogo.mvi"))
		candidates += [join(cfg, "skin_common", "bootlogo.mvi"), TARGETS[mode]]
		if skin:
			candidates.append(join(share, skin, "bootlogo.mvi"))
		candidates += [join(share, "skin_default", "bootlogo.mvi"), join(share, "bootlogo.mvi"), "/usr/share/bootlogo.mvi"]
	for candidate in candidates:
		if candidate and isfile(candidate) and getsize(candidate) > 0:
			return candidate
	return None


def current_image_bootlogo_source():
	"""Quelle nach Entfernung von /etc/enigma2/bootlogo.mvi.

	Entspricht der Suchreihenfolge in OpenATV tools/enigma2.sh.in,
	aber OHNE /etc-Ueberschreibungen. Der erste Treffer unter /usr/share
	ist das tatsaechlich wirksame Image-/Skin-Standardlogo.
	"""
	skin = _skin_name()
	share = "/usr/share/enigma2"
	candidates = []
	if skin:
		candidates.append(join(share, skin, "bootlogo.mvi"))
	candidates.extend((join(share, "skin_default", "bootlogo.mvi"), join(share, "bootlogo.mvi"), "/usr/share/bootlogo.mvi"))
	for path in candidates:
		if isfile(path):
			if getsize(path) == 0:
				raise BackupError(f"Image-Bootlogo ist leer: {path}")
			return path
	return None


def _blocking_config_bootlogos():
	"""Hoeher priorisierte /etc-Dateien duerfen nicht still entfernt werden."""
	skin = _skin_name()
	paths = []
	if skin:
		paths.append(join("/etc/enigma2", skin, "bootlogo.mvi"))
	paths.append("/etc/enigma2/skin_common/bootlogo.mvi")
	return [path for path in paths if isfile(path) or islink(path)]


def activate_current_image_bootlogo():
	"""Alten /etc-Override deaktivieren, OHNE ein altes Original einzuspielen.

	Die archivierte Originalsicherung (bootlogo_original.mvi) bleibt erhalten.
	Die aktuell eingesetzte /etc-Datei wird zusaetzlich gesichert.
	"""
	factory = current_image_bootlogo_source()
	if not factory:
		raise BackupError("Kein Bootlogo des aktuell installierten Images gefunden. Nichts veraendert.")
	blocking = _blocking_config_bootlogos()
	if blocking:
		blocking_paths = "\n".join(blocking)
		raise BackupError(f"Ein vorrangiges Bootlogo verhindert die Aktivierung des Image-Standards:\n{blocking_paths}\nBitte dieses zuerst separat pruefen. Es wurde nichts geaendert.")
	target = TARGETS["boot"]
	# Bestehende Backups validieren und beim allerersten Aufruf anlegen.
	ensure_backup("boot")
	if not (isfile(target) or islink(target)):
		return f"Der Image-Standard ist bereits aktiv: {factory}"
	if islink(target) and not isfile(target):
		raise BackupError(f"Defekter Bootlogo-Symlink: {target}. Nichts veraendert.")
	before_hash = _hash(target)
	makedirs(BACKUP_DIR, exist_ok=True)
	stamp = strftime("%Y%m%d-%H%M%S")
	# Mehrfache Aufrufe nie ueber dieselbe Sicherheitskopie schreiben lassen.
	for index in range(1, 1000):
		backup = join(BACKUP_DIR, f"bootlogo_vor_imagestandard_{stamp}_{index:03d}.mvi")
		if not exists(backup) and not islink(backup):
			break
	else:
		raise BackupError("Kein freier Dateiname fuer die Sicherheitskopie.")
	_copy_atomic(target, backup)
	if _hash(backup) != before_hash:
		raise BackupError("Sicherheitskopie konnte nicht geprueft werden. Nichts veraendert.")
	unlink(target)
	# Nach dem Deaktivieren muss wirklich die zuvor bestimmte Image-Quelle greifen.
	result = effective_source("boot")
	if not result or realpath(result) != realpath(factory):
		# Fehlerfall: bisherigen Override aus der Sicherheitskopie zurueckholen.
		_copy_atomic(backup, target)
		raise BackupError("Image-Standard konnte nicht eindeutig aktiviert werden. Die vorherige Bootlogo-Datei wurde wiederhergestellt.")
	return f"Image-Standard aktiviert: {factory}\nBisheriges Logo zusaetzlich gesichert: {backup}\nDie alte Originalsicherung bleibt unveraendert."


def current_image_radiologo_source():
	"""SAT-Radio-PNG des gerade installierten Images, ohne /etc-Overrides.
	Der tatsaechliche Suchpfad in SCOPE_GUISKIN kann zuerst Dateien aus
	dem aktiven Skin und seinem Fallback unter /usr/share aufloesen.
	"""
	skin = _skin_name()
	share = "/usr/share/enigma2"
	candidates = []
	if skin:
		candidates.append(join(share, skin, "icons", "default_radio.png"))
	height = getDesktop(0).size().height()
	candidates.extend((join(share, f"skin_fallback_{height}", "icons", "default_radio.png"), join(share, "skin_default", "icons", "default_radio.png"), GUI_RADIO_FACTORY))
	for source in candidates:
		if isfile(source):
			if getsize(source) <= 0:
				raise BackupError(f"Image-Radiologo ist leer: {source}")
			return source
	return None


def _blocking_gui_radiologos():
	"""Nur /etc/skin_common kann nach Entfernen des Skin-Overrides blockieren."""
	common = "/etc/enigma2/skin_common/icons/default_radio.png"
	return [common] if isfile(common) or islink(common) else []


def latest_radio_user_archive():
	"""Letzte beim Wechsel zum Image-Standard gesicherte PNG-Datei.

	Falls es noch keine solche gibt, das vor dem ersten Plugin-Einsatz
	archivierte Benutzer-Radiologo anbieten. Niemals das alte Factory-PNG
	faelschlich als *User-Radiologo* ausgeben.
	"""
	candidates = sorted(glob(join(BACKUP_DIR, "radiologo_vor_imagestandard_*.png")), reverse=True)
	for source in candidates:
		if isfile(source) and getsize(source) > 0:
			return source
	data = _load_gui_backup()
	if data and data.get("previous_present"):
		return GUI_RADIO_PREVIOUS
	return None


def activate_current_image_radiologo():
	"""Aktuelle Image-PNG fuer SAT-Radio aktivieren, niemals alte Sicherung.

	Eine vorhandene eigene PNG im aktiven Skin wird mit einem einmaligen
	Zeitstempel archiviert und erst danach geloescht. DAB+ bleibt unveraendert.
	"""
	standard = current_image_radiologo_source()
	if not standard:
		raise BackupError("Kein SAT-Radiologo des aktuellen Images vorhanden. Nichts veraendert.")
	blocking = _blocking_gui_radiologos()
	if blocking:
		blocking_paths = "\n".join(blocking)
		raise BackupError(f"Vorrangiges Radiologo im gemeinsamen Skin-Verzeichnis gefunden:\n{blocking_paths}\nBitte zuerst separat pruefen. Nichts veraendert.")
	ensure_gui_backup()
	target = gui_radio_target()
	if not (isfile(target) or islink(target)):
		return f"Das aktuelle Image-Radiologo ist bereits aktiv: {standard}"
	if islink(target) and not isfile(target):
		raise BackupError(f"Defekter Skin-Radiologo-Symlink: {target}. Nichts veraendert.")
	before_hash = _hash(target)
	stamp = strftime("%Y%m%d-%H%M%S")
	for index in range(1, 1000):
		backup = join(BACKUP_DIR, f"radiologo_vor_imagestandard_{stamp}_{index:03d}.png")
		if not exists(backup) and not islink(backup):
			break
	else:
		raise BackupError("Kein freier Dateiname fuer die Radio-Sicherheitskopie.")
	_copy_atomic(target, backup)
	if _hash(backup) != before_hash:
		raise BackupError("Radio-Sicherheitskopie konnte nicht verifiziert werden. Nichts veraendert.")
	unlink(target)
	# Ohne /etc-Skin-Override wird der aktuelle Standard geladen.
	if not isfile(standard) or not getsize(standard):
		_copy_atomic(backup, target)
		raise BackupError("Image-Radiologo nicht mehr vorhanden. Bisheriges PNG wiederhergestellt.")
	return f"Aktuelles Image-Radiologo aktiviert: {standard}\nBisheriges User-Radiologo gesichert: {backup}\nAlte Original-Sicherungen bleiben unveraendert."


def gui_radio_available():
	return isfile(GUI_RADIO_FACTORY) and getsize(GUI_RADIO_FACTORY) > 0


def gui_radio_target():
	skin = _skin_name()
	if not skin:
		raise BackupError("Kein gueltiger aktiver Skin gefunden. SAT-Radiologo nicht veraendert.")
	return join("/etc/enigma2", skin, "icons", "default_radio.png")


def _load_gui_backup():
	if not exists(GUI_RADIO_META):
		if exists(GUI_RADIO_ORIGINAL) or exists(GUI_RADIO_PREVIOUS):
			raise BackupError("Unvollstaendige SAT-Radiologo-Sicherung gefunden. Kein Ueberschreiben.")
		return None
	try:
		with open(GUI_RADIO_META) as f:
			data = load(f)
		if data.get("version") != 1 or not data.get("factory_sha256"):
			raise ValueError("Ungueltige Sicherungsdaten")
		if not isfile(GUI_RADIO_ORIGINAL) or _hash(GUI_RADIO_ORIGINAL) != data["factory_sha256"]:
			raise ValueError("Original-PNG fehlt oder wurde veraendert")
		if data.get("previous_present"):
			if not isfile(GUI_RADIO_PREVIOUS) or _hash(GUI_RADIO_PREVIOUS) != data.get("previous_sha256"):
				raise ValueError("Vorheriger Skin-Override fehlt oder wurde veraendert")
		return data
	except (OSError, ValueError, TypeError, KeyError) as error:
		raise BackupError(f"SAT-Radiologo-Sicherung fehlerhaft ({error}). Keine Aenderung.")


def ensure_gui_backup():
	"""PNG-Original und den bereits vorhandenen Skin-Override einmalig sichern.
	Die MVI-Sicherungen aus test7 bleiben vollstaendig unangetastet.
	"""
	if not gui_radio_available():
		return False
	previous = _load_gui_backup()
	if previous is not None:
		return False
	target = gui_radio_target()
	makedirs(BACKUP_DIR, exist_ok=True)
	if islink(target) and not isfile(target):
		raise BackupError(f"Skin-Radiobild ist ein defekter Symlink: {target}")
	had_previous = isfile(target)
	if had_previous and getsize(target) == 0:
		raise BackupError("Vorhandenes Skin-Radiobild ist leer; Sicherung abgebrochen.")
	# Kein stilles Ueberschreiben einer unterbrochenen Sicherung.
	for path in (GUI_RADIO_ORIGINAL, GUI_RADIO_PREVIOUS):
		if exists(path):
			raise BackupError(f"Unvollstaendige SAT-Radiobild-Sicherung gefunden: {path}")
	_copy_atomic(GUI_RADIO_FACTORY, GUI_RADIO_ORIGINAL)
	if had_previous:
		_copy_atomic(target, GUI_RADIO_PREVIOUS)
	info = {
		"version": 1,
		"factory_source": GUI_RADIO_FACTORY,
		"factory_sha256": _hash(GUI_RADIO_ORIGINAL),
		"skin_override_at_first_use": target,
		"previous_present": had_previous,
		"previous_sha256": _hash(GUI_RADIO_PREVIOUS) if had_previous else None,
		"previous_link": readlink(target) if islink(target) else None,
		"note": "Vorheriger Override separat gesichert; Original wiederherstellen aktiviert das Image-PNG."
	}
	_write_json_atomic(info, GUI_RADIO_META)
	_load_gui_backup()
	return True


def gui_original_source():
	info = _load_gui_backup()
	if info:
		return GUI_RADIO_ORIGINAL
	return GUI_RADIO_FACTORY if gui_radio_available() else None


def install_gui_radio(source):
	"""Installiert ein PNG als SAT-Radiobild im aktiven Skin (nicht DAB+)."""
	if not gui_radio_available():
		raise BackupError("Kein OpenATV-SAT-Radio-PNG verfuegbar.")
	if not isfile(source) or not source.lower().endswith(".png") or getsize(source) == 0:
		raise BackupError("Gueltige PNG-Datei fuer das SAT-Radiologo fehlt.")
	# Beide Originale sichern, BEVOR etwas installiert wird.
	ensure_backup("radio")
	ensure_gui_backup()
	target = gui_radio_target()
	_copy_atomic(source, target)
	if _hash(target) != _hash(source):
		raise BackupError("Das installierte SAT-Radiobild konnte nicht verifiziert werden.")
	return target


def restore_gui_radio():
	"""Image-Original durch Entfernen des Skin-Overrides wieder aktivieren.

	Ein vor dem ersten Plugin-Einsatz vorhandener benutzerdefinierter Override
	wurde getrennt gesichert und ist nicht verloren; er wird bewusst NICHT als
	'OpenATV-Original' ausgegeben.
	"""
	if not gui_radio_available():
		return ""
	ensure_gui_backup()
	info = _load_gui_backup()
	target = gui_radio_target()
	if info and target != info.get("skin_override_at_first_use"):
		# Falls der Skin zwischen Backup und Restore gewechselt wurde,
		# koennte sonst eine nicht gesicherte Datei entfernt werden.
		if isfile(target) or islink(target):
			raise BackupError(f"Aktiver Skin hat ein nicht gesichertes Radiobild: {target}. Bitte zuerst separat sichern.")
	if isfile(target) or islink(target):
		unlink(target)
	# Nur den aktiven Skin-Override anpassen; DAB-Rahmen und System-PNG bleiben unberuehrt.
	return " SAT-Radio: Skin-Override entfernt, Image-PNG wieder aktiv."


def _load(mode):
	meta, original, target_backup = _paths(mode)
	if not exists(meta):
		if exists(original) or exists(target_backup):
			raise BackupError(f"Alte Sicherungsdateien ohne Statusdatei gefunden. Nicht ueberschreiben: {BACKUP_DIR}")
		return None
	try:
		with open(meta) as fh:
			data = load(fh)
		if not isinstance(data, dict) or data.get("mode") != mode or data.get("version") != 1:
			raise ValueError("ungueltige Sicherungsdaten")
		if data.get("original_present"):
			if not isfile(original) or _hash(original) != data.get("original_sha256"):
				raise ValueError("Originalsicherung fehlt oder ist beschaedigt")
		if data.get("target_present"):
			if not isfile(target_backup) or _hash(target_backup) != data.get("target_sha256"):
				raise ValueError("Sicherung der bisherigen Zieldatei fehlt oder ist beschaedigt")
		return data
	except (OSError, ValueError, TypeError) as error:
		raise BackupError(f"Sicherung nicht verwendbar ({error}). Keine Logos veraendern.")


def backup_status(mode):
	data = _load(mode)
	if not data:
		return "Original noch nicht gesichert"
	if mode == "radio" and gui_radio_available():
		radio_gui = _load_gui_backup()
		if not radio_gui:
			return "MVI gesichert – SAT-Radio-PNG noch nicht gesichert"
		image = current_image_radiologo_source()
		if image and radio_gui.get("factory_sha256") != _hash(image):
			return "Gesichertes Radio-Original weicht vom aktuellen Image-Standard ab"
	if mode == "boot" and data.get("original_present"):
		image = current_image_bootlogo_source()
		if image and _hash(image) != data.get("original_sha256"):
			return "Gesichertes User-Bootlogo weicht vom aktuellen Image-Standard ab"
	return "Original gesichert" if data.get("original_present") else "Urspruenglich kein Logo vorhanden (Zustand gesichert)"


def ensure_backup(mode):
	"""Einmalig anlegen. Niemals vorhandene Sicherungen still ersetzen."""
	# Bestehende radio.mvi-Sicherung aus aelteren Testversionen nicht ersetzen.
	# Die separate GUI-PNG-Sicherung ergaenzen wir bei Bedarf.
	if mode == "radio" and gui_radio_available():
		ensure_gui_backup()
	data = _load(mode)
	if data is not None:
		return False
	makedirs(BACKUP_DIR, exist_ok=True)
	meta, original, target_backup = _paths(mode)
	target = TARGETS[mode]
	src = effective_source(mode)
	original_present = bool(src)
	target_present = isfile(target)
	target_link = readlink(target) if islink(target) else None
	# Die eigentliche Quelle und eine ggf. bisherige Benutzer-Ueberschreibung separat sichern.
	if original_present:
		_copy_atomic(src, original)
	if target_present:
		_copy_atomic(target, target_backup)
	obj = {
		"version": 1, "mode": mode, "original_present": original_present,
		"original_source": src, "original_sha256": _hash(original) if original_present else None,
		"target_present": target_present,
		"target_sha256": _hash(target_backup) if target_present else None,
		"target_link": target_link,
	}
	_write_json_atomic(obj, meta)
	# Nach der Erstellung gleiche Validierung wie bei jedem spaeteren Aufruf.
	_load(mode)
	return True


def check_writable_target(mode):
	"""Skin-eigene Logos haben in OpenATV Vorrang vor /etc/enigma2/bootlogo.mvi."""
	target = TARGETS[mode]
	if mode == "boot":
		src = effective_source(mode)
		if src and realpath(src) != realpath(target) and src.startswith("/etc/enigma2/"):
			raise BackupError(f"Der aktive Skin verwendet ein vorrangiges Bootlogo:\n{src}\nDas Plugin wuerde mit /etc/enigma2/bootlogo.mvi keine sichtbare Aenderung erzielen.")


def install_logo(mode, source):
	"""Erst sichern, dann atomar ersetzen."""
	if not isfile(source) or getsize(source) == 0:
		raise BackupError("Neue MVI-Datei fehlt oder ist leer.")
	check_writable_target(mode)
	ensure_backup(mode)
	_copy_atomic(source, TARGETS[mode])


def restore_original(mode):
	"""MVI-Vorzustand und (bei aktuellem OpenATV) SAT-Radio-PNG zuruecksetzen."""
	data = _load(mode)
	if data is None:
		raise BackupError("Keine Originalsicherung vorhanden.")
	if mode == "radio" and gui_radio_available():
		# Erst GUI-PNG-Sicherung und alle Pfade vorpruefen; erst danach MVI aendern.
		ensure_gui_backup()
		gui_data = _load_gui_backup()
		gui_target = gui_radio_target()
		if gui_data and (gui_target != gui_data.get("skin_override_at_first_use") and (isfile(gui_target) or islink(gui_target))):
			raise BackupError(f"Aktiver Skin hat ein nicht gesichertes Radiobild: {gui_target}")
	meta, original, target_backup = _paths(mode)
	target = TARGETS[mode]
	if data["target_present"]:
		_copy_atomic(target_backup, target)
		old_link = data.get("target_link")
		if old_link:
			intended = old_link if old_link.startswith("/") else join(dirname(target), old_link)
			if isfile(intended) and _hash(intended) == data["target_sha256"]:
				unlink(target)
				symlink(old_link, target)
		message = "Urspruengliche MVI-Datei wiederhergestellt."
	else:
		if exists(target) or islink(target):
			unlink(target)
		if data["original_present"]:
			now = effective_source(mode)
			if not now or _hash(now) != data["original_sha256"]:
				check_writable_target(mode)
				_copy_atomic(original, target)
				message = "Gesichertes Original-MVI wiederhergestellt."
			else:
				message = "Urspruenglichen MVI-Image-Zustand wiederhergestellt."
		else:
			message = "Urspruenglichen MVI-Image-Zustand wiederhergestellt."
	if mode == "radio" and gui_radio_available():
		message += restore_gui_radio()
	return message


config.plugins.bootlogoswitcher = ConfigSubsection()
config.plugins.bootlogoswitcher.storagepath = ConfigText(default="/media/hdd/")
RESOLUTION = "FHD" if getDesktop(0).size().width() > 1300 else "HD"


class BLSglobals:
	RELEASE = f"v{__version__}"
	MODULE_NAME = "BootlogoSwitcher"
	TEMPPATH = "/tmp/Bootlogos_DL/"
	PLUGINPATH = resolveFilename(SCOPE_PLUGINS, "Extensions/BootlogoSwitcher/")
	IMPORTFILE = join(PLUGINPATH, "downloadURLs.cfg")
	BOOTLOGO_DURATION_SEC = 0.5
	BOOTLOGO_BITRATE_KBIT = 300

	def getStorageBasePath(self):
		# In den Einstellungen ist das Basisverzeichnis auszuwaehlen.
		# Sowohl /media/hdd als auch /media/hdd/Bootlogos werden akzeptiert.
		path = normpath(config.plugins.bootlogoswitcher.storagepath.value or "/")
		if path == "/":
			path = "/tmp"
		return path if basename(path).lower() == "bootlogos" else join(path, "Bootlogos")

	def getStoragePathForMode(self, mode):
		if mode not in ("boot", "radio"):
			raise ValueError("Ungueltiger Logo-Modus")
		return join(self.getStorageBasePath(), "bootlogo" if mode == "boot" else "radiologo")

	def getCurrentStoragePath(self):
		return self.getStoragePathForMode(self.mode)

	def getCurrentConfigFile(self):
		return TARGETS[self.mode]

	def updateModeTexts(self, dirStr):
		which = "Bootlogos" if self.mode == "boot" else "Radiologos"
		self["info"].setText(f"{which} {dirStr} {self.getCurrentStoragePath()}")
		self.setTitle(f"Bootlogo Switcher – {'Bootlogo' if self.mode == 'boot' else 'Radiologo'}")

	def updateCurrentLogoLabel(self):
		# Die obere (gruene) Zeile zeigt nur Aktionen, keinen dauerhaften Pfad.
		try:
			status = backup_status(self.mode)
		except BackupError as error:
			status = f"FEHLER Sicherung: {error}"
		self["backupLabel"].setText(status)

	def switchToBootlogo(self, dirStr):
		self.mode = "boot"
		self["statusLabel"].setText("")
		self.updateModeTexts(dirStr)
		self.updateCurrentLogoLabel()
		self.reloadLists()

	def switchToRadiologo(self, dirStr):
		self.mode = "radio"
		self["statusLabel"].setText("")
		self.updateModeTexts(dirStr)
		try:
			# Bestehende Sicherung nur ergaenzen; vor der ersten Aenderung
			# des PNG den aktuellen Skin-Override als Sicherheitskopie halten.
			if gui_radio_available():
				ensure_gui_backup()
		except (OSError, BackupError) as error:
			print(f"[BootlogoSwitcher] Radio-GUI-Sicherung: {error}")
		self.updateCurrentLogoLabel()
		self.reloadLists()

	def createStoragePaths(self):
		storagePath = self.getStorageBasePath()
		try:
			configured = normpath(config.plugins.bootlogoswitcher.storagepath.value or "/")
			# Verhindert unbemerktes Schreiben in den Flash, wenn HDD/USB nicht eingehaengt ist.
			for medium in ("/media/hdd", "/media/usb"):
				if configured == medium or configured.startswith(medium + "/"):
					if not ismount(realpath(medium)):
						raise OSError(f"Datentraeger {medium} ist nicht eingehaengt")
			for path in (storagePath, join(storagePath, "bootlogo"), join(storagePath, "radiologo"), self.TEMPPATH):
				makedirs(path, exist_ok=True)
			return True
		except OSError as error:
			print(f"[BootlogoSwitcher] Speicherort nicht verfuegbar: {error}")
			return False

	def message(self, text, error=False, timeout=7):
		self.session.open(MessageBox, str(text), MessageBox.TYPE_ERROR if error else MessageBox.TYPE_INFO, timeout=timeout, close_on_any_key=True)


class BLSmain(Screen, BLSglobals):
	skin = """
	<screen name="BLSmain" position="center,center" size="1140,644" title="Bootlogo Switcher" resolution="1280,720" flags="wfNoBorder" backgroundColor="#20000000">
		<eLabel name="Background" position="0,0" size="1140,644" zPosition="-10" backgroundColor="#20000000" halign="center" />
		<widget font="Regular; 22" halign="right" position="920,10" render="Label" size="200,40" source="global.CurrentTime" transparent="1" foregroundColor="white" backgroundColor="#20000000"><convert type="ClockToText">Format:%a %d.%m. %H:%M</convert></widget>
		<widget name="info" position="140,10" size="800,40" font="Regular;22" halign="left" valign="center" transparent="1" foregroundColor="white" backgroundColor="#20000000" />
		<widget source="logoList" render="Listbox" position="20,70" size="640,450" itemHeight="28" font="Regular; 22" scrollbarMode="showOnDemand" transparent="1" foregroundColor="white" backgroundColor="#20000000" backgroundColorSelected="white" foregroundColorSelected="black"><convert type="StringList" /></widget>
		<widget name="previewLabel" position="680,70" size="440,80" font="Regular;22" transparent="1" foregroundColor="white" backgroundColor="#20000000" halign="left" valign="bottom" />
		<widget name="preview" position="680,170" size="440,248" zPosition="2" alphatest="on" scale="1" />
		<widget name="statusLabel" position="680,440" size="440,36" font="Regular;20" transparent="1" foregroundColor="#32E66A" backgroundColor="#20000000" />
		<widget name="backupLabel" position="680,481" size="440,80" font="Regular;20" transparent="1" foregroundColor="#FFD700" backgroundColor="#20000000" />
		<ePixmap position="26,10" size="100,40" pixmap="~logo.png" zPosition="2" alphatest="blend" scale="1" />
		<eLabel name="line" position="0,60" size="1140,1" zPosition="2" backgroundColor="#999999" />
		<eLabel name="line" position="0,586" size="1140,1" zPosition="2" backgroundColor="#999999" />
		<widget source="key_red" render="Label" position="20,600" size="200,30" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel position="18,598" size="204,34" backgroundColor="red" cornerRadius="6" zPosition="-2" />
		<eLabel position="20,600" size="200,30" backgroundColor="black" cornerRadius="6" zPosition="-1" />
		<widget source="key_green" render="Label" position="250,600" size="200,30" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel position="248,598" size="204,34" backgroundColor="green" cornerRadius="6" zPosition="-2" />
		<eLabel position="250,600" size="200,30" backgroundColor="black" cornerRadius="6" zPosition="-1" />
		<widget source="key_yellow" render="Label" position="480,600" size="200,30" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel position="478,598" size="204,34" backgroundColor="yellow" cornerRadius="6" zPosition="-2" />
		<eLabel position="480,600" size="200,30" backgroundColor="black" cornerRadius="6" zPosition="-1" />
		<widget source="key_blue" render="Label" position="710,600" size="200,30" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel position="708,598" size="204,34" backgroundColor="blue" cornerRadius="6" zPosition="-2" />
		<eLabel position="710,600" size="200,30" backgroundColor="black" cornerRadius="6" zPosition="-1" />
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
		self.busy = False
		self._closed = False
		self._previewGeneration = 0
		# Native Enigma2-Vorschau (derselbe Decoder wie im PicturePlayer).
		# Alte direkte LoadPixmap-Variante bleibt nur als Fallback erhalten.
		self._picLoader = ePicLoad()
		self._picLoader.PictureData.get().append(self.nativePreviewReady)
		self._picConfigured = False
		self._picPending = None
		self._picInFlight = None
		self._picRetry = None
		self["info"] = Label("")
		self["previewLabel"] = Label("Vorschau")
		self["preview"] = Pixmap()
		self["statusLabel"] = Label("")
		self["backupLabel"] = Label("")
		self["key_red"] = StaticText("Download")
		self["key_green"] = StaticText("Menü")
		self["key_yellow"] = StaticText("Modus Bootlogo")
		self["key_blue"] = StaticText("Modus Radiologo")
		self["logoList"] = List([])
		self["logoList"].onSelectionChanged.append(self.updatePreview)
		self["actions"] = ActionMap(["OkCancelActions", "MenuActions", "ColorActions"], {
			"ok": self.applyLogo, "cancel": self.keyCancel, "menu": self.openModeMenu,
			"red": self.keyRed, "green": self.openModeMenu,
			"yellow": self.keyYellow, "blue": self.keyBlue}, -1)
		self.downloadUrls = self.readDownloadUrls()
		self.onClose.append(self.onScreenClose)
		self.onLayoutFinish.append(self.layoutFinished)

	def onScreenClose(self):
		self._closed = True
		self._previewGeneration += 1
		self._picPending = None
		if self._picRetry is not None and self._picRetry.active():
			self._picRetry.cancel()
		self._picRetry = None
		try:
			self._picLoader.PictureData.get().remove(self.nativePreviewReady)
		except (ValueError, AttributeError):
			pass

	def keyCancel(self):
		if not self.busy:
			self.close()

	def layoutFinished(self):
		if not self.createStoragePaths():
			self.message("Speicherpfad nicht verfuegbar. Bitte Einstellungen pruefen.", True)
		try:
			widget = self["preview"].instance
			w = max(1, widget.size().width())
			h = max(1, widget.size().height())
			# ePicLoad skaliert bereits beim Dekodieren; kein FFmpeg-Thumbnail.
			self._picLoader.setPara((w, h, 1, 1, False, 1, "#00000000"))
			self._picConfigured = True
		except Exception as error:
			print(f"[BootlogoSwitcher] Nativer Decoder nicht konfiguriert: {error}")
		self.switchToBootlogo("aus")

	def readDownloadUrls(self):
		urls = []
		if isfile(self.IMPORTFILE):
			try:
				with open(self.IMPORTFILE) as fh:
					for line in fh:
						line = line.strip()
						if line.startswith("https://") and not line.startswith("#"):
							urls.append(line)
			except OSError as error:
				print(f"[BootlogoSwitcher] URL-Datei: {error}")
		return urls

	def openModeMenu(self):
		if self.busy:
			return
		opts = [
			("Bootlogo ändern (bootlogo.mvi)", "boot"),
			("Radiologo ändern (SAT-Radio-PNG / radio.mvi)", "radio"),
			(f"Original {'Bootlogo' if self.mode == 'boot' else 'Radiologo'} sichern", "backup"),
			(f"Gesichertes Original {'Bootlogo' if self.mode == 'boot' else 'Radiologo'} wiederherstellen", "restore"),
			("Liste neu einlesen", "reload"),
			("Einstellungen", "config")]
		if self.mode == "boot":
			opts.insert(2, ("Aktuelles Image-Bootlogo verwenden", "image_default"))
		elif gui_radio_available():
			opts.insert(2, ("Aktuelles Image-Radiologo verwenden (SAT-Radio)", "image_default"))
			opts[4] = ("Gesichertes MVI-Radiologo wiederherstellen (Archiv)", "restore")
		self.session.openWithCallback(self.onModeMenuChoice, ChoiceBox, title=f"Bootlogo Switcher v{__version__} – Aktionen", list=opts)

	def onModeMenuChoice(self, choice):
		if not choice:
			return
		action = choice[1]
		if action == "boot":
			self.switchToBootlogo("aus")
		elif action == "radio":
			self.switchToRadiologo("aus")
		elif action == "backup":
			try:
				created = ensure_backup(self.mode)
				self.reloadLists()  # Original sofort als ersten Eintrag anzeigen.
				self.updateCurrentLogoLabel()
				self["statusLabel"].setText("Original wurde gesichert." if created else "Sicherung ist bereits vorhanden.")
				self.message("Original dauerhaft gesichert." if created else "Original ist bereits gesichert. Sicherung bleibt unveraendert.")
			except (OSError, BackupError) as error:
				self.message(f"Original konnte NICHT gesichert werden:\n{error}", True, 12)
		elif action == "image_default":
			self.confirmImageDefault()
		elif action == "restore":
			if self.mode == "radio" and gui_radio_available():
				msg = ("Gesicherten MVI-Radiologo-Zustand aus dem Archiv wiederherstellen?\nDadurch wird auch der SAT-Radio-PNG-Override entfernt.\nDas Archiv kann aus einem aelteren Image stammen!")
			else:
				msg = f"Gesichertes Original-{'Bootlogo' if self.mode == 'boot' else 'Radiologo'} wiederherstellen?\nACHTUNG: Die Sicherung kann aus einem aelteren Image stammen.\nFuer das aktuelle Image-Bootlogo den Eintrag 'Aktuelles Image-Bootlogo' verwenden."
			self.session.openWithCallback(self.onRestoreAnswer, MessageBox,
				msg, MessageBox.TYPE_YESNO)
		elif action == "reload":
			self.reloadLists()
		elif action == "config":
			self.session.openWithCallback(self.afterSetup, BLSsetup)

	def confirmImageDefault(self):
		if self.busy:
			return
		if self.mode == "radio" and gui_radio_available():
			question = ("Aktuelles SAT-Radiologo des installierten Images aktivieren?\n\n"
						"Das vorhandene Benutzer-PNG wird zuerst gesichert und dann "
						"als Skin-Override deaktiviert.\n"
						"DAB+ und alte Sicherungen bleiben unveraendert.")
		else:
			question = ("Aktuelles Bootlogo des installierten Images aktivieren?\n\n"
						"Eine vorhandene /etc/enigma2/bootlogo.mvi wird vorher "
						"zusaetzlich gesichert und danach deaktiviert.\n"
						"Alte Originalsicherungen bleiben erhalten.")
		mode = self.mode
		self.session.openWithCallback(lambda answer: self.onImageDefaultAnswer(answer, mode), MessageBox, question, MessageBox.TYPE_YESNO)

	def onImageDefaultAnswer(self, answer, mode):
		if not answer or self.busy:
			return
		try:
			if mode == "radio" and gui_radio_available():
				result = activate_current_image_radiologo()
				label = "Aktuelles Image-Radiologo aktiviert."
			else:
				result = activate_current_image_bootlogo()
				label = "Aktuelles Image-Bootlogo aktiviert."
			self.reloadLists()
			self.updateCurrentLogoLabel()
			self["statusLabel"].setText(label)
			self.session.openWithCallback(self.onRebootAnswer, MessageBox,
				f"{result}\n\nBox jetzt vollstaendig neu starten?",
				MessageBox.TYPE_YESNO)
		except (OSError, BackupError) as error:
			self.message(f"Image-Standard konnte nicht aktiviert werden:\n{error}", True, 12)

	def onRestoreAnswer(self, answer):
		if not answer:
			return
		try:
			result = restore_original(self.mode)
			self.updateCurrentLogoLabel()
			self["statusLabel"].setText("Original wiederhergestellt.")
			self.session.openWithCallback(self.onRebootAnswer, MessageBox,
				f"{result}\nSoll die Box neu gestartet werden?", MessageBox.TYPE_YESNO)
		except (OSError, BackupError) as error:
			self.message(f"Original konnte nicht wiederhergestellt werden:\n{error}", True, 12)

	def afterSetup(self, *args):
		if not self._closed:
			self.createStoragePaths()
			self.updateModeTexts("aus")
			self.reloadLists()

	def reloadLists(self):
		sourcepath = self.getCurrentStoragePath()
		entries = []
		self.list = []
		try:
			data = _load(self.mode)
		except (BackupError, OSError) as error:
			data = None
			print(f"[BootlogoSwitcher] Originalsicherung: {error}")
		if self.mode == "boot":
			try:
				standard = current_image_bootlogo_source()
			except (OSError, BackupError) as error:
				standard = None
				print(f"[BootlogoSwitcher] Image-Bootlogo-Vorschau: {error}")
			if standard:
				self.list.append(("Aktuelles Image-Bootlogo", standard, "image_default", standard, "Image-Standard aktivieren (keine alte Sicherung)"))
				entries.append(("★ Aktuelles Image-Bootlogo [Standard]", "OK = Image-Standard aktivieren"))
		elif gui_radio_available():
			try:
				radio_standard = current_image_radiologo_source()
				if radio_standard:
					self.list.append(("Aktuelles Image-Radiologo", radio_standard, "image_default", radio_standard, "Aktuelles Image-PNG fuer SAT-Radio verwenden (DAB+ bleibt unveraendert)"))
					entries.append(("★ Aktuelles Image-Radiologo [Standard]", "OK = SAT-Radio-Standard aktivieren"))
				radio_user = latest_radio_user_archive()
				if radio_user:
					title = "Gesichertes User-Radiologo"
					self.list.append((title, radio_user, "radio_archive", radio_user, "Benutzer-Radiologo aus dem Archiv installieren"))
					entries.append((f"★ {title} [Gesichert]", "OK = Benutzer-Radiologo installieren"))
				gui_data = _load_gui_backup()
				if gui_data and radio_standard and _hash(GUI_RADIO_ORIGINAL) != _hash(radio_standard):
					title = "Gesichertes Radio-Image (Archiv)"
					self.list.append((title, GUI_RADIO_ORIGINAL, "radio_archive", GUI_RADIO_ORIGINAL, "Altes Original-PNG aus dem Image-Archiv installieren"))
					entries.append((f"★ {title} [Gesichert]", "OK = altes Image-PNG installieren"))
			except (OSError, BackupError) as error:
				print(f"[BootlogoSwitcher] Radio-Archiv: {error}")
		if data is not None and (self.mode == "boot" or not gui_radio_available()):
			_, original, _ = _paths(self.mode)
			if data.get("original_present"):
				title = "Gesichertes User-Bootlogo" if self.mode == "boot" else "Gesichertes MVI-Radiologo (Archiv)"
				source = original
			else:
				title = "Originalzustand (ohne Logo-Datei)"
				source = None
			self.list.append((title, source, "original", source, "Archivierte Sicherung wiederherstellen"))
			entries.append((f"★ {title} [Gesichert]", "OK = Wiederherstellen"))
		try:
			filenames = listdir(sourcepath)
		except OSError:
			filenames = []
		for fname in sorted(filenames, key=str.lower):
			full = join(sourcepath, fname)
			if not isfile(full):
				continue
			lower = fname.lower()
			if lower.endswith(".mvi"):
				ftype, preview, desc = "mvi", None, "MVI Logo"
			elif lower.endswith((".jpg", ".jpeg", ".png")):
				ftype, preview, desc = "image", full, "Bild (wird konvertiert)"
			else:
				continue
			self.list.append((fname, full, ftype, preview, desc))
			entries.append((f"{fname}  [{'MVI' if ftype == 'mvi' else 'Bild'}]", desc))
		if not entries:
			entries = [("Keine Dateien gefunden", f"Bitte .mvi/.jpg/.png nach {sourcepath} kopieren")]
		self["logoList"].setList(entries)
		self.updatePreview()

	def getCurrentEntry(self):
		index = self["logoList"].getIndex()
		return self.list[index] if index is not None and 0 <= index < len(self.list) else None

	def updatePreview(self):
		self._previewGeneration += 1
		generation = self._previewGeneration
		entry = self.getCurrentEntry()
		self["preview"].hide()
		if not entry:
			self["previewLabel"].setText("Vorschau")
			return
		fname, full, ftype, preview, desc = entry
		# Der Vorschautitel bleibt bei allen Aktionen weiss.
		self["previewLabel"].setText(f"Vorschau: {fname}")
		if ftype in ("original", "image_default", "radio_archive") and preview and isfile(preview):
			if preview.lower().endswith((".png", ".jpg", ".jpeg")):
				self.showLocalPreview(preview)
			else:
				self.previewOriginal(generation, preview)
		elif ftype == "image" and preview and exists(preview):
			self.showLocalPreview(preview)

	def showLocalPreview(self, path):
		"""Lokale Bilder schnell durch Enigma2 in Vorschaugroesse dekodieren."""
		generation = self._previewGeneration
		if self._closed:
			return
		self._picPending = (generation, path)
		if self._picRetry is not None and self._picRetry.active():
			self._picRetry.cancel()
		self._picRetry = None
		if self._picConfigured:
			self.startNativePreview()
		else:
			self.directPreviewFallback(path, generation)

	def startNativePreview(self):
		"""Nur eine Dekodierung gleichzeitig; beim Scrollen die letzte Auswahl laden."""
		self._picRetry = None
		if self._closed or not self._picConfigured or self._picInFlight is not None:
			return
		if self._picPending is None:
			return
		generation, path = self._picPending
		if generation != self._previewGeneration:
			return
		self._picInFlight = (generation, path)
		try:
			result = self._picLoader.getThumbnail(path)
			if result == 1:  # Enigma2-Decoder ist noch beschaeftigt
				self._picInFlight = None
				self._picRetry = callLater(0.12, self.startNativePreview)
			elif result not in (0, None):
				self._picInFlight = None
				self.directPreviewFallback(path, generation)
		except Exception as error:
			self._picInFlight = None
			print(f"[BootlogoSwitcher] ePicLoad: {error}")
			self.directPreviewFallback(path, generation)

	def nativePreviewReady(self, info=""):
		request = self._picInFlight
		self._picInFlight = None
		if request is None or self._closed:
			return
		generation, path = request
		try:
			ptr = self._picLoader.getData()
			if generation == self._previewGeneration and ptr is not None:
				widget = self["preview"].instance
				if widget is not None:
					widget.setPixmap(ptr.__deref__())
					widget.show()
			elif generation == self._previewGeneration:
				self.directPreviewFallback(path, generation)
		except Exception as error:
			print(f"[BootlogoSwitcher] Thumbnail: {error}")
			self.directPreviewFallback(path, generation)
		# Zwischenzeitlich weitergescrollt? Nur die neueste Auswahl anzeigen.
		if self._picPending is not None and self._picPending != request:
			self.startNativePreview()

	def directPreviewFallback(self, path, generation):
		"""Altbewaehrtes LoadPixmap nur benutzen, wenn ePicLoad versagt."""
		if self._closed or generation != self._previewGeneration:
			return
		try:
			pix = LoadPixmap(path, cached=False, autoDetect=True)
			if pix and self["preview"].instance is not None:
				self["preview"].instance.setPixmap(pix)
				self["preview"].instance.show()
		except Exception as error:
			print(f"[BootlogoSwitcher] Fallback-Vorschau: {path} ({error})")

	def previewOriginal(self, generation, source):
		"""Standbild aus der MVI erzeugen; alles Zeitaufwendige im Hintergrund."""
		ffmpeg = which("ffmpeg")
		if not ffmpeg:
			return  # MVI-Vorschau optional; Wiederherstellung bleibt nutzbar.
		try:
			cache_name = f"original_{self.mode}_{_hash(source)[:12]}.png"
			target = join(self.TEMPPATH, cache_name)
			if isfile(target) and getsize(target) > 0:
				self.showLocalPreview(target)
			else:
				callInThread(self.originalPreviewWorker, generation, ffmpeg, source, target)
		except OSError as error:
			print(f"[BootlogoSwitcher] Original-Vorschau: {error}")

	def originalPreviewWorker(self, generation, ffmpeg, source, target):
		temp = None
		error = None
		try:
			fd, temp = mkstemp(prefix=".bls-preview-", suffix=".png", dir=self.TEMPPATH)
			close(fd)
			# .mvi kann bei ffmpeg faelschlich als Motion-Pixels-MVI erkannt
			# werden. OpenATV .mvi ist rohes MPEG-Video: Demuxer erzwingen.
			cmd = [ffmpeg, "-nostdin", "-y", "-loglevel", "error", "-f", "mpegvideo", "-i", source, "-frames:v", "1", "-vf", "scale=440:248", "-update", "1", temp]
			result = run(cmd, capture_output=True, timeout=25, check=False)
			if result.returncode or not isfile(temp) or getsize(temp) == 0:
				raise ValueError("ffmpeg konnte die MVI-Vorschau nicht erzeugen")
			replace(temp, target)
			temp = None
		except Exception as exc:
			error = str(exc)
		finally:
			if temp and exists(temp):
				try:
					unlink(temp)
				except OSError:
					pass
		callFromThread(self.originalPreviewFinished, generation, target, error)

	def originalPreviewFinished(self, generation, target, error):
		if self._closed or generation != self._previewGeneration:
			return
		if error:
			print(f"[BootlogoSwitcher] Original-Vorschau: {error}")
		else:
			self.showLocalPreview(target)

	def applyLogo(self):
		if self.busy:
			return
		entry = self.getCurrentEntry()
		if not entry:
			self.message("Keine gueltige Datei ausgewaehlt.", True)
			return
		fname, full, ftype, _, _ = entry
		mode = self.mode
		if ftype == "image_default":
			self.confirmImageDefault()
		elif ftype == "radio_archive":
			self.session.openWithCallback(lambda answer: self.onRadioArchiveAnswer(answer, full),
				MessageBox, "Gesichertes Radiologo aus dem Archiv als SAT-Radiologo installieren?\n"
				"Das aktive SAT-Radiologo wird ersetzt; DAB+ bleibt unveraendert.",
				MessageBox.TYPE_YESNO)
		elif ftype == "original":
			self.session.openWithCallback(self.onRestoreAnswer, MessageBox,
				f"Gesichertes Original-{'Bootlogo' if mode == 'boot' else 'Radiologo'} wiederherstellen?\n"
				"ACHTUNG: Dieses Archiv kann aus einer aelteren Image-Version stammen.", MessageBox.TYPE_YESNO)
		else:
			self.installFromFile(mode, full)

	def onRadioArchiveAnswer(self, answer, source):
		if answer and not self.busy:
			self.installFromFile("radio", source)

	def installFromFile(self, mode, source):
		"""Gemeinsamer Installationsweg fuer lokale und heruntergeladene Logos."""
		if self.busy:
			return
		if mode not in TARGETS or not isfile(source):
			self.message("Logo-Datei nicht gefunden. Bitte den Download pruefen.", True)
			return
		if mode == "radio" and gui_radio_available():
			suffix = splitext(source)[1].lower()
			if suffix not in (".png", ".jpg", ".jpeg", ".mvi"):
				self.message("Nicht unterstuetztes Radiologo-Format.", True)
				return
			ffmpeg = None if suffix == ".png" else which("ffmpeg")
			if suffix != ".png" and not ffmpeg:
				self.installFFmpeg()
				return
			self.busy = True
			self["statusLabel"].setText("SAT-Radiologo wird installiert …")
			callInThread(self.radioGuiWorker, source, ffmpeg, suffix)
			return
		if source.lower().endswith(".mvi"):
			self.applyMvi(mode, source)
		elif source.lower().endswith((".png", ".jpg", ".jpeg")):
			ffmpeg = which("ffmpeg")
			if not ffmpeg:
				self.installFFmpeg()
				return
			self.busy = True
			self["statusLabel"].setText("Bild wird umgewandelt …")
			callInThread(self.convertWorker, ffmpeg, source, mode)
		else:
			self.message("Nicht unterstuetztes Logo-Format.", True)

	def radioGuiWorker(self, source, ffmpeg, suffix):
		"""PNG installieren, bei JPG/MVI ein Einzelbild konvertieren; blockiert GUI nicht."""
		temporary = None
		try:
			png_source = source
			if suffix != ".png":
				fd, temporary = mkstemp(prefix="bls-sat-radio-", suffix=".png")
				close(fd)
				cmd = [ffmpeg, "-nostdin", "-y", "-loglevel", "error"]
				if suffix == ".mvi":
					cmd += ["-f", "mpegvideo"]
				cmd += ["-i", source, "-frames:v", "1", "-update", "1", temporary]
				proc = run(cmd, capture_output=True, timeout=90, check=False)
				if proc.returncode or not isfile(temporary) or getsize(temporary) == 0:
					detail = proc.stderr.decode("utf-8", "replace")[-350:]
					raise BackupError(f"Konvertierung ins PNG fehlgeschlagen: {detail}")
				png_source = temporary
			target = install_gui_radio(png_source)
			result = (True, f"SAT-Radio-PNG installiert: {target}")
		except Exception as error:
			result = (False, str(error))
		finally:
			if temporary and exists(temporary):
				try:
					unlink(temporary)
				except OSError:
					pass
		callFromThread(self.radioGuiFinished, result)

	def radioGuiFinished(self, result):
		if self._closed:
			return
		self.busy = False
		self.updateCurrentLogoLabel()
		if result[0]:
			self["statusLabel"].setText("SAT-Radiologo installiert. DAB+ bleibt unveraendert.")
			self.askForReboot("radio")
		else:
			self["statusLabel"].setText("")
			self.message(f"SAT-Radiologo konnte nicht installiert werden:\n{result[1]}", True, 12)

	def applyMvi(self, mode, source):
		self["statusLabel"].setText("Logo wird installiert …")
		try:
			install_logo(mode, source)
			self.updateCurrentLogoLabel()
			self["statusLabel"].setText("Logo erfolgreich installiert.")
			self.askForReboot(mode)
		except (OSError, BackupError) as error:
			self["statusLabel"].setText("")
			self.message(f"Logo nicht installiert. Original bleibt erhalten.\n{error}", True, 12)

	def convertWorker(self, ffmpeg, src, mode):
		fd, tmp = mkstemp(prefix="bls-convert-", suffix=".mvi")
		close(fd)
		try:
			resolution = "1920x1080" if RESOLUTION == "FHD" else "1280x720"
			cmd = [ffmpeg, "-nostdin", "-y", "-loglevel", "error", "-loop", "1", "-i", src,
				"-t", str(self.BOOTLOGO_DURATION_SEC), "-r", "25", "-s", resolution,
				"-pix_fmt", "yuv420p", "-vcodec", "mpeg1video",
				"-b:v", f"{self.BOOTLOGO_BITRATE_KBIT}k",
				"-maxrate", f"{self.BOOTLOGO_BITRATE_KBIT}k",
				"-bufsize", "2000k", "-an", "-f", "mpeg1video", tmp
			]
			proc = run(cmd, capture_output=True, timeout=120, check=False)
			if proc.returncode:
				raise BackupError(f"ffmpeg Fehler {proc.returncode}: {proc.stderr.decode('utf-8', 'replace')[-400:]}")
			install_logo(mode, tmp)
			result = (True, "")
		except Exception as error:
			result = (False, str(error))
		finally:
			try:
				unlink(tmp)
			except OSError:
				pass
		callFromThread(self.convertFinished, mode, result)

	def convertFinished(self, mode, result):
		if self._closed:
			return
		self.busy = False
		self.updatePreview()
		self.updateCurrentLogoLabel()
		success, error = result
		if success:
			self["statusLabel"].setText("Logo erfolgreich installiert.")
			self.askForReboot(mode)
		else:
			self["statusLabel"].setText("")
			self.message(f"Logo wurde nicht installiert:\n{error}", True, 12)

	def installFFmpeg(self):
		self.session.openWithCallback(self.onInstallFFmpegAnswer, MessageBox,
			"ffmpeg ist nicht installiert. Jetzt installieren?", MessageBox.TYPE_YESNO)

	def onInstallFFmpegAnswer(self, answer):
		if not answer:
			return
		# Screens.Console ist asynchron und blockiert nicht die Fernbedienung.
		try:
			self.session.openWithCallback(self.afterInstallFFmpeg, Console,
				title="ffmpeg Installation", cmdlist=["opkg update && opkg install ffmpeg"], closeOnSuccess=True)
		except Exception as error:
			self.message(f"Installation konnte nicht gestartet werden:\n{error}", True)

	def afterInstallFFmpeg(self, *args):
		if not self._closed:
			self.message("Installation beendet. Bitte ffmpeg ggf. erneut pruefen und Bild nochmals auswaehlen.")

	def askForReboot(self, mode):
		which = "Bootlogo" if mode == "boot" else "Radiologo"
		self.session.openWithCallback(self.onRebootAnswer, MessageBox,
			f"{which} wurde gesetzt.\nSoll die Box jetzt neu gestartet werden?",
			MessageBox.TYPE_YESNO, timeout=10, close_on_any_key=True)

	def onRebootAnswer(self, answer):
		if answer:
			self.session.open(TryQuitMainloop, 2)

	def keyRed(self):
		if self.busy:
			return
		if self.downloadUrls:
			# Den bereits gewaehlten Modus in die Download-Ansicht mitnehmen.
			self.session.openWithCallback(self.afterDownload, BLSdownload, self.downloadUrls, self.mode)
		else:
			self.message("Keine Downloadadresse in downloadURLs.cfg vorhanden.", True)

	def afterDownload(self, result=None):
		if self._closed:
			return
		if not result:
			self.reloadLists()
			return
		# (Modus, gespeicherter Pfad, direkt installieren?)
		try:
			mode, source, install_now = result
		except (ValueError, TypeError):
			self.reloadLists()
			return
		if mode not in ("boot", "radio"):
			self.reloadLists()
			return
		if mode == "radio":
			self.switchToRadiologo("aus")
		else:
			self.switchToBootlogo("aus")
		# Auswahl in der lokalen Sammlung wiederfinden. Das Original bleibt
		# erster Listeneintrag, aber der neue Download wird markiert.
		for index, entry in enumerate(self.list):
			if entry[1] == source:
				try:
					self["logoList"].setIndex(index)
				except (AttributeError, IndexError, ValueError):
					pass
				break
		if install_now:
			base = realpath(self.getCurrentStoragePath())
			if (not isfile(source) or realpath(dirname(source)) != base):
				self.message("Dateipfad der heruntergeladenen Vorlage ungueltig.", True)
				return
			self.installFromFile(mode, source)
		elif source is None:
			self["statusLabel"].setText("Logos gespeichert – Datei mit OK installieren.")
		else:
			self["statusLabel"].setText("Vorlage gespeichert – mit OK installieren.")

	def keyYellow(self):
		if not self.busy:
			self.switchToBootlogo("aus")

	def keyBlue(self):
		if not self.busy:
			self.switchToRadiologo("aus")


class BLSsetup(Setup):
	def __init__(self, session):
		Setup.__init__(self, session, "BLSsetup", plugin="Extensions/BootlogoSwitcher", PluginLanguageDomain="BootlogoSwitcher")

	def keySelect(self):
		if self.getCurrentItem() == config.plugins.bootlogoswitcher.storagepath:
			self.session.openWithCallback(self.keySelectCB, BLSlocationBox,
				currDir=config.plugins.bootlogoswitcher.storagepath.value)
			return
		Setup.keySelect(self)

	def keySelectCB(self, path):
		if path is not None:
			config.plugins.bootlogoswitcher.storagepath.value = join(path, "")
		self["config"].invalidateCurrent()
		self.changedEntry()


class BLSdownload(Screen, BLSglobals):
	skin = """
	<screen name="BLSdownload" position="center,center" size="1160,644" title="Bootlogo Switcher" resolution="1280,720" flags="wfNoBorder" backgroundColor="#20000000">
		<eLabel name="Background" position="0,0" size="1160,644" zPosition="-10" backgroundColor="#20000000" />
		<widget font="Regular;22" halign="right" position="940,10" render="Label" size="200,40" source="global.CurrentTime" transparent="1" foregroundColor="white" backgroundColor="#20000000"><convert type="ClockToText">Format:%a %d.%m. %H:%M</convert></widget>
		<widget name="info" position="140,10" size="800,40" font="Regular;22" halign="left" valign="center" transparent="1" foregroundColor="white" backgroundColor="#20000000" />
		<widget source="logoList" render="Listbox" position="20,80" size="660,480" foregroundColor="white" backgroundColor="#20000000" backgroundColorSelected="white" foregroundColorSelected="black" transparent="1" scrollbarMode="showOnDemand"><convert type="TemplatedMultiContent">{"template": [
			MultiContentEntryText(pos=(4,2), size=(420,30), font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=0),
			MultiContentEntryText(pos=(430,2), size=(70,30), font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=2),
			MultiContentEntryText(pos=(500,2), size=(100,30), font=0, flags=RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text=1),
			MultiContentEntryPixmapAlphaBlend(pos=(620,4), size=(24,24), flags=BT_SCALE, png="~checkbox.png"),
			MultiContentEntryText(pos=(622,7), size=(16,16), font=1, color=MultiContentTemplateColor(4), color_sel=MultiContentTemplateColor(4), flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=3)
			], "fonts": [gFont("Regular",20),gFont("Regular",22)], "itemHeight":32}</convert></widget>
		<widget name="previewLabel" position="700,70" size="440,80" font="Regular;22" transparent="1" foregroundColor="white" backgroundColor="#20000000" halign="left" valign="bottom" />
		<widget name="preview" position="700,170" size="440,248" zPosition="2" alphatest="on" scale="1" />
		<widget name="statusLabel" position="700,440" size="440,36" font="Regular;20" transparent="1" foregroundColor="#32E66A" backgroundColor="#20000000" />
		<widget name="backupLabel" position="700,481" size="440,80" font="Regular;20" transparent="1" foregroundColor="#FFD700" backgroundColor="#20000000" />
		<ePixmap position="26,10" size="100,40" pixmap="~logo.png" zPosition="2" alphatest="blend" scale="1" />
		<eLabel name="line" position="0,60" size="1160,1" zPosition="2" backgroundColor="#999999" />
		<eLabel name="line" position="0,586" size="1160,1" zPosition="2" backgroundColor="#999999" />
		<widget source="key_red" render="Label" position="20,600" size="200,30" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel position="18,598" size="204,34" backgroundColor="red" cornerRadius="6" zPosition="-2" />
		<eLabel position="20,600" size="200,30" backgroundColor="black" cornerRadius="6" zPosition="-1" />
		<widget source="key_green" render="Label" position="250,600" size="200,30" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel position="248,598" size="204,34" backgroundColor="green" cornerRadius="6" zPosition="-2" />
		<eLabel position="250,600" size="200,30" backgroundColor="black" cornerRadius="6" zPosition="-1" />
		<widget source="key_yellow" render="Label" position="480,600" size="200,30" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel position="478,598" size="204,34" backgroundColor="yellow" cornerRadius="6" zPosition="-2" />
		<eLabel position="480,600" size="200,30" backgroundColor="black" cornerRadius="6" zPosition="-1" />
		<widget source="key_blue" render="Label" position="710,600" size="200,30" zPosition="1" font="Regular;20" halign="center" valign="center" foregroundColor="white" backgroundColor="black" transparent="1" />
		<eLabel position="708,598" size="204,34" backgroundColor="blue" cornerRadius="6" zPosition="-2" />
		<eLabel position="710,600" size="200,30" backgroundColor="black" cornerRadius="6" zPosition="-1" />
		<ePixmap position="960,602" size="45,26" zPosition="10" pixmap="~ok.png" transparent="1" alphatest="blend" scale="1" />
		<ePixmap position="1030,602" size="45,26" zPosition="10" pixmap="~menu.png" transparent="1" alphatest="blend" scale="1" />
		<ePixmap position="1100,602" size="45,26" zPosition="10" pixmap="~exit.png" transparent="1" alphatest="blend" scale="1" />
	</screen>
	"""

	def __init__(self, session, downloadUrls, startMode="boot"):
		self.skin = self.skin.replace("~", f"{self.PLUGINPATH}pics/{RESOLUTION}/")
		Screen.__init__(self, session)
		self.session = session
		self.downloadUrls = list(downloadUrls)
		self.logoLists = []  # [Dateiname, Groesse, URL, markiert]
		self.mode = startMode if startMode in ("boot", "radio") else "boot"
		self.downloadActive = False
		self._downloadMode = self.mode
		self._downloadTargetPath = None
		self._savedAny = False
		self._closed = False
		self._previewGeneration = 0
		self["info"] = Label("")
		self["previewLabel"] = Label("Vorschau")
		self["preview"] = Pixmap()
		self["statusLabel"] = Label("")
		self["backupLabel"] = Label("")
		self["key_red"] = StaticText("Alle auswählen")
		self["key_green"] = StaticText("Auswahl laden")
		self["key_yellow"] = StaticText("Bootlogo")
		self["key_blue"] = StaticText("Radiologo")
		self["logoList"] = List([])
		self["logoList"].onSelectionChanged.append(self.updatePreview)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {
			"ok": self.keyOk, "cancel": self.keyCancel,
			"red": self.keyRed, "green": self.keyGreen,
			"yellow": self.keyYellow, "blue": self.keyBlue}, -1)
		self.onClose.append(self.onScreenClose)
		self.onLayoutFinish.append(self.layoutFinished)

	def onScreenClose(self):
		self._closed = True
		self._previewGeneration += 1

	def keyCancel(self):
		if not self.downloadActive:
			# Nach Mehrfachdownload zur passenden lokalen Sammlung springen.
			if self._savedAny:
				self.close((self._downloadMode, None, False))
			else:
				self.close()

	def layoutFinished(self):
		if not self.createStoragePaths():
			self.message("Speicherpfad nicht verfuegbar.", True)
		self.updateModeTexts("nach")
		self.updateCurrentLogoLabel()
		self["statusLabel"].setText("Online-Liste wird geladen …")
		callInThread(self.reloadWorker)

	def reloadWorker(self):
		entries = []
		errors = []
		for url in self.downloadUrls:
			try:
				res = get(url, headers={"Accept": "application/vnd.github+json"}, timeout=(5, 20))
				res.raise_for_status()
				picDicts = res.json()
				if not isinstance(picDicts, list):
					raise ValueError("Antwort ist keine Dateiliste")
				for pic in picDicts:
					if pic.get("type") != "file":
						continue
					name = pic.get("name", "")
					size = pic.get("size", 0)
					picUrl = pic.get("download_url", "")
					if (not self.validName(name) or not picUrl.startswith("https://") or
							not isinstance(size, int) or size < 1 or size > 50 * 1024 * 1024):
						continue
					entries.append([name, size, picUrl, False])
			except (RequestException, ValueError, TypeError) as error:
				errors.append(f"{url}: {error}")
		callFromThread(self.reloadFinished, entries, errors)

	@staticmethod
	def validName(name):
		return (isinstance(name, str) and name not in ("", ".", "..") and
				len(name) <= 200 and "/" not in name and "\\" not in name and
				"\x00" not in name and name.lower().endswith((".png", ".jpg", ".jpeg", ".mvi")))

	def reloadFinished(self, entries, errors):
		if self._closed:
			return
		self.logoLists = entries
		self.updateSkinList()
		self.updatePreview()
		self["statusLabel"].setText("OK markieren; GRUEN Zielordner waehlen")
		if errors:
			self.message("Online-Liste unvollstaendig:\n" + "\n".join(errors)[:850], True, 12)

	def updateSkinList(self):
		skinList = []
		for name, size, url, checked in self.logoLists:
			suffix = splitext(name)[1].upper().lstrip(".")
			color = 0x0004c81b if checked else 0x00f50808
			skinList.append((name, f"{(size + 1023) // 1024} KB", suffix, "✔" if checked else "✘", color))
		self["logoList"].updateList(skinList)
		self["key_red"].setText("Alle abwählen" if skinList and all(x[3] for x in self.logoLists) else "Alle auswählen")
		self["key_green"].setText("Auswahl laden")

	def getCurrentEntry(self):
		index = self["logoList"].getIndex()
		return self.logoLists[index] if index is not None and 0 <= index < len(self.logoLists) else None

	@staticmethod
	def _getFile(url, path, expected):
		"""Vollstaendig empfangen, Groesse verifizieren, dann atomar als Datei ablegen."""
		if isfile(path) and getsize(path) == expected:
			return
		makedirs(dirname(path), exist_ok=True)
		fd, tmp = mkstemp(prefix=".bls-dl-", dir=dirname(path))
		try:
			count = 0
			with fdopen(fd, "wb") as dest, get(url, stream=True, timeout=(5, 25)) as res:
				res.raise_for_status()
				for block in res.iter_content(chunk_size=65536):
					if block:
						count += len(block)
						if count > expected or count > 50 * 1024 * 1024:
							raise ValueError("Datei ist groesser als erwartet")
						dest.write(block)
				dest.flush()
				fsync(dest.fileno())
			if count != expected:
				raise ValueError(f"Dateigroesse falsch: {count} statt {expected} Bytes")
			chmod(tmp, 0o644)
			replace(tmp, path)
			tmp = None
		finally:
			if tmp and exists(tmp):
				unlink(tmp)

	def updatePreview(self):
		self._previewGeneration += 1
		generation = self._previewGeneration
		self["preview"].hide()
		entry = self.getCurrentEntry()
		if not entry:
			self["previewLabel"].setText("Keine Vorschau")
			return
		name, size, url, checked = entry
		self["previewLabel"].setText(f"Vorschau: {name}")
		if name.lower().endswith(".mvi"):
			return
		target = join(self.TEMPPATH, name)
		if isfile(target) and getsize(target) == size:
			self.showPreview(generation, target, None)
		else:
			callInThread(self.previewWorker, generation, url, target, size)

	def previewWorker(self, generation, url, target, size):
		try:
			self._getFile(url, target, size)
			error = None
		except Exception as exc:
			error = str(exc)
		callFromThread(self.showPreview, generation, target, error)

	def showPreview(self, generation, target, error):
		if self._closed or generation != self._previewGeneration:
			return
		if error:
			self["previewLabel"].setText("Vorschau nicht verfuegbar")
			return
		try:
			pix = LoadPixmap(target)
			if pix and self["preview"].instance is not None:
				self["preview"].instance.setPixmap(pix)
				self["preview"].instance.show()
		except Exception as exc:
			print(f"[BootlogoSwitcher] Download-Vorschau: {exc}")

	def keyOk(self):
		if self.downloadActive:
			return
		entry = self.getCurrentEntry()
		if entry:
			entry[3] = not entry[3]
			self.updateSkinList()

	def keyRed(self):
		if self.downloadActive or not self.logoLists:
			return
		mark = not all(entry[3] for entry in self.logoLists)
		for entry in self.logoLists:
			entry[3] = mark
		self.updateSkinList()

	def keyGreen(self):
		if self.downloadActive:
			return
		if not any(entry[3] for entry in self.logoLists):
			self.message("Bitte zuerst mit OK Logos auswaehlen.")
			return
		# Das Ziel wird IMMER vor dem Speichern explizit bestaetigt.
		# So landet z.B. radio_1.png nicht unbemerkt unter bootlogo/.
		mode_names = ("Radiologo", "Bootlogo") if self.mode == "radio" else ("Bootlogo", "Radiologo")
		options = []
		for name in mode_names:
			mode = "radio" if name == "Radiologo" else "boot"
			options.append((f"Als {name} speichern: {self.getStoragePathForMode(mode)}", mode))
		self.session.openWithCallback(self.onTargetChosen, ChoiceBox,
			title="Wohin sollen die ausgewaehlten Bilder gespeichert werden?", list=options)

	def onTargetChosen(self, choice):
		if not choice or self.downloadActive:
			return
		mode = choice[1]
		if mode not in ("boot", "radio"):
			return
		if not self.createStoragePaths():
			self.message("Speicherpfad nicht verfuegbar.", True)
			return
		chosen = [list(entry) for entry in self.logoLists if entry[3]]
		if not chosen:
			self.message("Es sind keine Logos ausgewaehlt.")
			return
		self.mode = mode
		self._downloadMode = mode
		self._downloadTargetPath = self.getStoragePathForMode(mode)
		self.updateModeTexts("nach")
		self.updateCurrentLogoLabel()
		self.downloadActive = True
		self["statusLabel"].setText(f"Lade {len(chosen)} Dateien nach {'Radiologos' if mode == 'radio' else 'Bootlogos'} …")
		callInThread(self.downloadWorker, chosen, self._downloadTargetPath)

	def downloadWorker(self, chosen, targetPath):
		saved, cached, failed = [], [], []
		for name, size, url, checked in chosen:
			target = join(targetPath, name)
			try:
				if isfile(target) and getsize(target) == size:
					cached.append(name)
					continue
				self._getFile(url, target, size)
				saved.append(name)
			except Exception as error:
				failed.append(f"{name}: {error}")
		callFromThread(self.downloadFinished, saved, cached, failed)

	def downloadFinished(self, saved, cached, failed):
		if self._closed:
			return
		self.downloadActive = False
		self.updatePreview()
		finished = saved + cached
		if finished:
			self._savedAny = True
		self["statusLabel"].setText("Download abgeschlossen." if not failed else "Download teilweise fehlgeschlagen.")
		if len(finished) == 1 and not failed:
			name = finished[0]
			target_path = self._downloadTargetPath
			if target_path is None:
				self["statusLabel"].setText("Downloadziel nicht verfuegbar.")
				return
			self._downloadResult = (self._downloadMode, join(target_path, name))
			which = "Bootlogo" if self._downloadMode == "boot" else "Radiologo"
			# OK im Dialog startet die Installation; NEIN behaelt die Vorlage
			# und zeigt sie nach Rueckkehr in der lokalen Liste an.
			self.session.openWithCallback(self.onDownloadInstallDecision, MessageBox, f"{name} wurde gespeichert.\n\nJetzt als {which} installieren?\nDas Original bleibt gesichert.", MessageBox.TYPE_YESNO)
			return
		msg = f"Heruntergeladen: {len(saved)}\nBereits vorhanden: {len(cached)}\nFehlgeschlagen: {len(failed)}"
		if failed:
			msg += "\n\n" + "\n".join(failed)[:800]
		else:
			msg += "\n\nMit EXIT zurueck zur lokalen Logo-Liste."
		self.message(msg, bool(failed), 12)

	def onDownloadInstallDecision(self, answer):
		if self._closed:
			return
		result = getattr(self, "_downloadResult", None)
		self._downloadResult = None
		if not result:
			return
		mode, path = result
		# Nach dem Schliessen aktualisiert BLSmain die Liste und installiert
		# optional im GUI-Hauptscreen (ffmpeg laeuft dort im Thread).
		self.close((mode, path, bool(answer)))

	def keyYellow(self):
		if not self.downloadActive:
			self.mode = "boot"
			self["statusLabel"].setText("")
			self.updateModeTexts("nach")
			self.updateCurrentLogoLabel()

	def keyBlue(self):
		if not self.downloadActive:
			self.mode = "radio"
			self["statusLabel"].setText("")
			self.updateModeTexts("nach")
			self.updateCurrentLogoLabel()


class BLSlocationBox(LocationBox):
	def __init__(self, session, currDir):
		inhibit = defaultInhibitDirs[:]
		for path in ("/usr", "/share"):
			if path in inhibit:
				inhibit.remove(path)
		LocationBox.__init__(self, session,
			text="Wo sollen die Vorlagen der Bootlogos gespeichert werden?",
			currDir=currDir or None, inhibitDirs=inhibit)
		self.skinName = ["LocationBox"]
