"""
BLWQHDServiceType.py
================

Eigener Enigma2 Converter fuer Skin-Widgets.

Zweck
-----
Dieser Converter ersetzt mehrere einzelne ServiceInfo-/FrontendInfo-Abfragen
durch eine gemeinsame, sauber getrennte Logik.

Er wurde erstellt, weil es bei uebereinanderliegenden Pixmap-Widgets sonst
zu falschen Mehrfachanzeigen kommen kann, zum Beispiel:

* IPTV + DVB-S gleichzeitig bei verschluesselten Sendern mit Oscam/SoftCSA.
* HD720 + FHD1080 gleichzeitig durch ueberlappende ValueRange-Bereiche.
* QHD1440 bei 720p, wenn faelschlich die VideoWidth statt VideoHeight
  ausgewertet wird. Beispiel: 1280x720 hat eine Breite von 1280 und passte
  dadurch in einen falschen QHD-Bereich.

Einbau
------
Datei kopieren nach:

	/usr/lib/enigma2/python/Components/Converter/BLWQHDServiceType.py

Danach Enigma2 neu starten:

	init 4 && sleep 3 && rm -f /usr/lib/enigma2/python/Components/Converter/BLWQHDServiceType.pyc && init 3

Wichtige Skin-Regel
-------------------
Bei allen Widgets mit diesem Converter bitte als Quelle verwenden:

	source="session.CurrentService"

Nicht mehr mischen mit:

	source="session.FrontendInfo"

Wenn alles ueber session.CurrentService laeuft, entscheidet der Converter
zentral und es bleibt pro Position nur das passende Icon sichtbar.


1) Empfangsart / Service-Typ
----------------------------
Der Converter erkennt zuerst, ob ein echter DVB-Tuner vorhanden ist.
Wenn DVB-S/C/T erkannt wird, wird der Sender nicht als IPTV gewertet.
Das ist wichtig bei verschluesselten Sendern mit Oscam oder SoftCSA, weil
service.streamed() auf manchen Images trotzdem einen Wert liefern kann.

Moegliche Argumente:

	IPTV
	IsIPTV
	Stream
	IsStream
	IsIPStream

	DVB-S
	DVBS
	SAT
	Satellite

	DVB-C
	DVBC
	Cable

	DVB-T
	DVBT
	Terrestrial

Beispiel:

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_iptv.png" position="110,1011" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">IPTV</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_dvb.s.png" position="110,1011" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">DVB-S</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_dvb.c.png" position="110,1011" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">DVB-C</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_dvb.t.png" position="110,1011" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">DVB-T</convert>
		<convert type="ConditionalShowHide" />
	</widget>


2) Aufloesungs-Icons
--------------------
Die Aufloesung wird bewusst ueber VideoHeight ausgewertet.
Dadurch wird 1280x720 korrekt als HD720 erkannt und nicht faelschlich
als QHD1440.

Bereiche:

	SD       = bis 699 Pixel Hoehe, z.B. 720x576
	HD720   = 700 bis 720 Pixel Hoehe, z.B. 1280x720
	FHD1080 = 721 bis 1080 Pixel Hoehe, z.B. 1920x1080
	QHD1440 = 1081 bis 1440 Pixel Hoehe, z.B. 2560x1440
	UHD4K   = 1441 bis 2160 Pixel Hoehe, z.B. 3840x2160

Moegliche Argumente:

	SD
	HD720
	FHD1080
	QHD1440
	UHD4K

Beispiel:

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_sd.png" position="1450,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">SD</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_hd720.png" position="1450,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">HD720</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_fhd1080.png" position="1450,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">FHD1080</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_qhd1440.png" position="1450,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">QHD1440</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_uhd4k.png" position="1450,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">UHD4K</convert>
		<convert type="ConditionalShowHide" />
	</widget>


3) Aufloesung als Text
----------------------
Fuer Textausgabe render="Label" verwenden.

Moegliche Argumente:

	VideoInfo         -> z.B. 1920x1080 50i
	Resolution        -> z.B. 1920x1080
	ResolutionShort   -> z.B. SD, HD, FHD, QHD, UHD

Beispiel:

	<widget source="session.CurrentService" render="Label" position="1450,980" size="220,35" font="Regular;24" foregroundColor="white" backgroundColor="transparent" transparent="1" zPosition="2">
		<convert type="BLWQHDServiceType">VideoInfo</convert>
	</widget>


4) HDR / HLG
------------
HDR sollte besser eine eigene Position bekommen und nicht direkt auf der
gleichen Position wie SD/HD/FHD/UHD liegen. Sonst koennen absichtlich zwei
Informationen gleichzeitig sichtbar sein: Aufloesung und HDR.

Moegliche Argumente:

	HDR
	HDR10
	HLG
	HDRANY       -> zeigt ein einziges HDR-Icon bei HDR, HDR10 oder HLG

Beispiel fuer drei einzelne Icons:

	<widget source="session.CurrentService" pixmap="icons/icon_hdr_on.png" render="Pixmap" position="1660,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">HDR</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" pixmap="icons/icon_hdr10_on.png" render="Pixmap" position="1660,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">HDR10</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" pixmap="icons/icon_hlg_on.png" render="Pixmap" position="1660,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">HLG</convert>
		<convert type="ConditionalShowHide" />
	</widget>

Beispiel fuer nur ein HDR-Icon:

	<widget source="session.CurrentService" pixmap="icons/icon_hdr_on.png" render="Pixmap" position="1660,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">HDRANY</convert>
		<convert type="ConditionalShowHide" />
	</widget>


5) Bildformat
-------------
Moegliche Argumente:

	16:9
	16-9
	Widescreen
	IsWidescreen

	4:3
	4-3
	NotWidescreen
	IsNotWidescreen

Beispiel:

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_16-9.png" position="1590,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">16:9</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_4-3.png" position="1590,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">4:3</convert>
		<convert type="ConditionalShowHide" />
	</widget>


6) Audio
--------
Moegliche Argumente:

	Dolby
	DolbyDigital
	Multichannel
	IsMultichannel

	Stereo
	IsStereo

Fuer Textausgabe mit render="Label":

	AudioInfo        -> z.B. Deutsch AC3 5.1
	AudioCodec       -> z.B. AC3
	AudioLanguage    -> z.B. Deutsch
	AudioTracks      -> z.B. 2
	AudioChannels    -> z.B. 5.1 oder Stereo
	AudioShort       -> z.B. Dolby oder Stereo

Beispiel:

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_dolbydigital.png" position="1520,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">Dolby</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_stereo.png" position="1520,1021" size="58,42" zPosition="1" alphatest="blend">
		<convert type="BLWQHDServiceType">Stereo</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" render="Label" position="1520,980" size="260,35" font="Regular;24" foregroundColor="white" backgroundColor="transparent" transparent="1" zPosition="2">
		<convert type="BLWQHDServiceType">AudioInfo</convert>
	</widget>


7) Verschluesselung / SoftCSA
-----------------------------
Moegliche Argumente:

	Crypted
	IsCrypted
	SoftCSA
	IsSoftCSA

Hinweis:
Crypted zeigt nur normale Verschluesselung ohne SoftCSA.
SoftCSA zeigt SoftCSA getrennt an.
Oscam wird normalerweise als verschluesselter Sender erkannt, nicht als SoftCSA.

Beispiel:

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_crypted.png" position="1240,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">Crypted</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_softcsa.png" position="1240,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">SoftCSA</convert>
		<convert type="ConditionalShowHide" />
	</widget>


8) Teletext, Untertitel und HbbTV
---------------------------------
Moegliche Argumente:

	Teletext
	HasTeletext
	HasTelext       -> Schreibfehler wird aus Kompatibilitaet akzeptiert
	TXT

	Subtitles
	Subtitle
	SubtitlesAvailable
	HasSubtitles

	HBBTV
	HasHBBTV

Wichtig:
HasTeletext / HasTelext ist Teletext.
Fuer Untertitel bitte Subtitles verwenden.

Beispiel:

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_subtitle.png" position="1310,1021" size="58,42" zPosition="2" alphatest="blend">
		<convert type="BLWQHDServiceType">Subtitles</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_hbbtv.png" position="1170,1021" size="58,42" zPosition="1" alphatest="blend">
		<convert type="BLWQHDServiceType">HBBTV</convert>
		<convert type="ConditionalShowHide" />
	</widget>

	<widget source="session.CurrentService" render="Pixmap" pixmap="icons/icon_teletext.png" position="1380,1021" size="58,42" zPosition="1" alphatest="blend">
		<convert type="BLWQHDServiceType">Teletext</convert>
		<convert type="ConditionalShowHide" />
	</widget>


Technische Hinweise
-------------------
* Der Converter hat boolean und text.
* Pixmap-Widgets verwenden boolean zusammen mit ConditionalShowHide.
* Label-Widgets verwenden text.
* Unbekannte Argumente zeigen absichtlich nichts an.
* Der Converter ist bewusst defensiv geschrieben, damit fehlende Werte nicht
  direkt einen Skin-Crash verursachen.
"""

import re

from enigma import eAVControl, iPlayableService, iServiceInformation

from Components.Converter.Converter import Converter
from Components.Element import cached

WIDESCREEN = (1, 3, 4, 7, 8, 11, 12, 15, 16)


class BLWQHDServiceType(Converter):
	UNKNOWN = -1
	IPTV = 0
	DVBS = 1
	DVBC = 2
	DVBT = 3
	SD = 10
	HD720 = 11
	FHD1080 = 12
	QHD1440 = 13
	UHD4K = 14
	SDR = 20
	HDR = 21
	HDR10 = 22
	HLG = 23
	HDHDR = 24
	HDRANY = 25
	WIDESCREEN_TYPE = 30
	NOT_WIDESCREEN = 31
	TELETEXT = 40
	SUBTITLES = 41
	HBBTV = 42
	MULTICHANNEL = 50
	STEREO = 51
	CRYPTED = 60
	SOFTCSA = 61
	VIDEO_TEXT = 70
	RESOLUTION_TEXT = 71
	RESOLUTION_SHORT = 72
	AUDIO_TEXT = 80
	AUDIO_CODEC = 81
	AUDIO_LANGUAGE = 82
	AUDIO_TRACKS = 83
	AUDIO_CHANNELS = 84
	AUDIO_SHORT = 85

	VIDEO_INFO_WIDTH = 0
	VIDEO_INFO_HEIGHT = 1
	VIDEO_INFO_FRAME_RATE = 2
	VIDEO_INFO_PROGRESSIVE = 3
	VIDEO_INFO_ASPECT = 4
	VIDEO_INFO_GAMMA = 5

	def __init__(self, argument):
		Converter.__init__(self, argument)
		self.argument = argument
		self.type = {
			"IPTV": self.IPTV,
			"IsIPTV": self.IPTV,
			"Stream": self.IPTV,
			"IsStream": self.IPTV,
			"IsIPStream": self.IPTV,
			"DVB-S": self.DVBS,
			"DVBS": self.DVBS,
			"SAT": self.DVBS,
			"Satellite": self.DVBS,
			"DVB-C": self.DVBC,
			"DVBC": self.DVBC,
			"Cable": self.DVBC,
			"DVB-T": self.DVBT,
			"DVBT": self.DVBT,
			"Terrestrial": self.DVBT,
			"SD": self.SD,
			"IsSD": self.SD,
			"HD": self.HD720,
			"HD720": self.HD720,
			"720": self.HD720,
			"720p": self.HD720,
			"FHD": self.FHD1080,
			"FullHD": self.FHD1080,
			"FHD1080": self.FHD1080,
			"1080": self.FHD1080,
			"1080i": self.FHD1080,
			"1080p": self.FHD1080,
			"QHD": self.QHD1440,
			"QHD1440": self.QHD1440,
			"1440": self.QHD1440,
			"1440p": self.QHD1440,
			"UHD": self.UHD4K,
			"UHD4K": self.UHD4K,
			"4K": self.UHD4K,
			"2160": self.UHD4K,
			"2160p": self.UHD4K,
			"SDR": self.SDR,
			"IsSDR": self.SDR,
			"HDR": self.HDR,
			"IsHDR": self.HDR,
			"HDR10": self.HDR10,
			"IsHDR10": self.HDR10,
			"HLG": self.HLG,
			"IsHLG": self.HLG,
			"HDHDR": self.HDHDR,
			"IsHDHDR": self.HDHDR,
			"HDRANY": self.HDRANY,
			"IsHDRANY": self.HDRANY,
			"16:9": self.WIDESCREEN_TYPE,
			"16-9": self.WIDESCREEN_TYPE,
			"Widescreen": self.WIDESCREEN_TYPE,
			"IsWidescreen": self.WIDESCREEN_TYPE,
			"4:3": self.NOT_WIDESCREEN,
			"4-3": self.NOT_WIDESCREEN,
			"NotWidescreen": self.NOT_WIDESCREEN,
			"IsNotWidescreen": self.NOT_WIDESCREEN,
			"Teletext": self.TELETEXT,
			"HasTeletext": self.TELETEXT,
			"HasTelext": self.TELETEXT,
			"TXT": self.TELETEXT,
			"Subtitles": self.SUBTITLES,
			"Subtitle": self.SUBTITLES,
			"SubtitlesAvailable": self.SUBTITLES,
			"HasSubtitles": self.SUBTITLES,
			"HBBTV": self.HBBTV,
			"HasHBBTV": self.HBBTV,
			"Multichannel": self.MULTICHANNEL,
			"IsMultichannel": self.MULTICHANNEL,
			"Dolby": self.MULTICHANNEL,
			"DolbyDigital": self.MULTICHANNEL,
			"Stereo": self.STEREO,
			"IsStereo": self.STEREO,
			"Crypted": self.CRYPTED,
			"IsCrypted": self.CRYPTED,
			"SoftCSA": self.SOFTCSA,
			"IsSoftCSA": self.SOFTCSA,
			"VideoInfo": self.VIDEO_TEXT,
			"VideoText": self.VIDEO_TEXT,
			"ResolutionInfo": self.VIDEO_TEXT,
			"Resolution": self.RESOLUTION_TEXT,
			"VideoResolution": self.RESOLUTION_TEXT,
			"ResolutionShort": self.RESOLUTION_SHORT,
			"VideoResolutionShort": self.RESOLUTION_SHORT,
			"AudioInfo": self.AUDIO_TEXT,
			"AudioText": self.AUDIO_TEXT,
			"Audio": self.AUDIO_TEXT,
			"AudioCodec": self.AUDIO_CODEC,
			"Codec": self.AUDIO_CODEC,
			"AudioLanguage": self.AUDIO_LANGUAGE,
			"AudioLang": self.AUDIO_LANGUAGE,
			"Language": self.AUDIO_LANGUAGE,
			"AudioTracks": self.AUDIO_TRACKS,
			"AudioTrackCount": self.AUDIO_TRACKS,
			"AudioChannels": self.AUDIO_CHANNELS,
			"Channels": self.AUDIO_CHANNELS,
			"AudioShort": self.AUDIO_SHORT,
		}.get(argument, self.UNKNOWN)
		self.interestingEvents = tuple(x for x in (
			getattr(iPlayableService, "evStart", None),
			getattr(iPlayableService, "evUpdatedInfo", None),
			getattr(iPlayableService, "evUpdatedEventInfo", None),
			getattr(iPlayableService, "evHBBTVInfo", None),
			getattr(iPlayableService, "evTunedIn", None),
			getattr(iPlayableService, "evVideoSizeChanged", None),
			getattr(iPlayableService, "evVideoFramerateChanged", None),
			getattr(iPlayableService, "evVideoProgressiveChanged", None),
			getattr(iPlayableService, "evVideoGammaChanged", None),
			getattr(iPlayableService, "evEnd", None),
		) if x is not None)

	def _getFrontendType(self, service):
		try:
			frontend = service and service.frontendInfo()
			raw = frontend and frontend.getAll(False)
		except Exception:
			raw = None
		if not raw:
			return None

		tunerType = str(raw.get("tuner_type", "")).upper()
		if tunerType.startswith("DVB-S"):
			return self.DVBS
		if tunerType.startswith("DVB-C"):
			return self.DVBC
		if tunerType.startswith("DVB-T"):
			return self.DVBT
		return None

	def _isSoftCSA(self, info):
		try:
			return info and info.getInfo(iServiceInformation.sIsSoftCSA) == 1
		except Exception:
			return False

	def _isIPTVReference(self, ref):
		if not ref:
			return False
		ref = str(ref)
		return ref.startswith(("4097:", "5001:", "5002:", "8193:", "8739:")) or "%3a//" in ref.lower() or "://" in ref

	def _isStreamed(self, service):
		try:
			return service and service.streamed() is not None
		except Exception:
			return False

	def _getVideoInfo(self, info):
		videoData = [-1, -1, -1, -1, -1, -1]
		try:
			value = info and info.getInfoString(iServiceInformation.sVideoInfo) or ""
			if value:
				parts = [int(x) for x in value.split("|")]
				videoData[:len(parts[:6])] = parts[:6]
		except Exception:
			pass

		width = videoData[self.VIDEO_INFO_WIDTH]
		height = videoData[self.VIDEO_INFO_HEIGHT]
		frameRate = videoData[self.VIDEO_INFO_FRAME_RATE]
		progressive = videoData[self.VIDEO_INFO_PROGRESSIVE]
		gamma = videoData[self.VIDEO_INFO_GAMMA]

		if width in (-1, 0):
			try:
				width = eAVControl.getInstance().getResolutionX(0)
			except Exception:
				width = 0
		if height in (-1, 0):
			try:
				height = eAVControl.getInstance().getResolutionY(0)
			except Exception:
				height = 0

		aspect = videoData[self.VIDEO_INFO_ASPECT]
		if aspect == -1:
			try:
				aspect = eAVControl.getInstance().getAspect(0)
			except Exception:
				aspect = -1

		if frameRate in (-1, 0):
			try:
				frameRate = eAVControl.getInstance().getFrameRate(0)
			except Exception:
				frameRate = 0

		if progressive == -1:
			try:
				progressive = eAVControl.getInstance().getProgressive()
			except Exception:
				progressive = -1

		return width, height, frameRate, progressive, gamma, aspect

	def _formatFrameRate(self, frameRate):
		if not frameRate or frameRate <= 0:
			return ""
		if frameRate >= 1000:
			rate = int((frameRate + 500) // 1000)
		else:
			rate = int(frameRate)
		return str(rate) if rate > 0 else ""

	def _formatProgressive(self, progressive):
		if progressive == 0:
			return "i"
		if progressive == 1:
			return "p"
		return ""

	def _getResolutionText(self, info, short=False, withRate=True):
		width, height, frameRate, progressive, gamma, aspect = self._getVideoInfo(info)
		if not width or not height or width <= 0 or height <= 0:
			return ""

		if short:
			resolutionType = self._getResolutionType(height)
			resolutionName = {
				self.SD: "SD",
				self.HD720: "HD",
				self.FHD1080: "FHD",
				self.QHD1440: "QHD",
				self.UHD4K: "UHD",
			}.get(resolutionType, "")
			return resolutionName

		result = "%sx%s" % (width, height)
		if withRate:
			rate = self._formatFrameRate(frameRate)
			scan = self._formatProgressive(progressive)
			if rate or scan:
				result += " %s%s" % (rate, scan)
		return result

	def _getResolutionType(self, height):
		if height <= 0:
			return None
		if height <= 699:
			return self.SD
		if height <= 720:
			return self.HD720
		if height <= 1080:
			return self.FHD1080
		if height <= 1440:
			return self.QHD1440
		if height <= 2160:
			return self.UHD4K
		return self.UHD4K

	def _getHDRType(self, width, height, gamma):
		# Gamma-Werte wie in der originalen ServiceInfo:
		# 0 / -1 = SDR oder unbekannt, 1 = HDR, 2 = HDR10, 3 = HLG.
		if gamma == 3:
			return self.HLG
		if gamma == 2:
			return self.HDR10
		if gamma == 1:
			return self.HDR
		if gamma > 0 and height and height <= 1080 and width and width > 720:
			return self.HDHDR
		return self.SDR

	def _isMultichannelAudio(self, service):
		try:
			audio = service and service.audioTracks()
			if audio and audio.getNumberOfTracks():
				currentTrack = audio.getCurrentTrack()
				if currentTrack > -1:
					description = audio.getTrackInfo(currentTrack).getDescription()
					return bool(description and description.split()[0] in ("AC3", "AC3+", "DTS", "DTS-HD", "AC4", "LPCM", "Dolby", "HE-AAC", "AAC+", "WMA"))
		except Exception:
			pass
		return False

	def _getAudioData(self, service):
		description = ""
		language = ""
		count = 0
		currentTrack = -1

		try:
			audio = service and service.audioTracks()
			if audio:
				count = audio.getNumberOfTracks()
				currentTrack = audio.getCurrentTrack()
				if count and currentTrack > -1:
					trackInfo = audio.getTrackInfo(currentTrack)
					description = trackInfo.getDescription() or ""
					try:
						language = trackInfo.getLanguage() or ""
					except Exception:
						language = ""
		except Exception:
			pass

		return description.strip(), language.strip(), count, currentTrack

	def _cleanAudioLanguage(self, language):
		if not language:
			return ""

		language = language.strip()
		code = language.lower().replace("_", "-")
		code = code.split("-")[0]
		code = code.split("/")[0].strip()

		names = {
			"de": "Deutsch",
			"deu": "Deutsch",
			"ger": "Deutsch",
			"en": "English",
			"eng": "English",
			"fr": "Français",
			"fre": "Français",
			"fra": "Français",
			"it": "Italiano",
			"ita": "Italiano",
			"es": "Español",
			"spa": "Español",
			"nl": "Nederlands",
			"dut": "Nederlands",
			"nld": "Nederlands",
			"pl": "Polski",
			"pol": "Polski",
			"tr": "Türkçe",
			"tur": "Türkçe",
			"und": "",
			"qaa": "",
		}
		return names.get(code, language)

	def _normalizeAudioCodec(self, description):
		if not description:
			return ""

		value = description.upper().replace("_", " ").replace("-", "")
		if "TRUEHD" in value:
			return "TrueHD"
		if "ATMOS" in value:
			return "Atmos"
		if "DTSHD" in value:
			return "DTS-HD"
		if "DTS" in value:
			return "DTS"
		if "EAC3" in value or "AC3+" in value or "DD+" in value or "DOLBY DIGITAL+" in value:
			return "AC3+"
		if "AC4" in value:
			return "AC4"
		if "AC3" in value or "DOLBY DIGITAL" in value:
			return "AC3"
		if "HEAAC" in value:
			return "HE-AAC"
		if "AAC+" in value:
			return "AAC+"
		if "AAC" in value:
			return "AAC"
		if "LPCM" in value:
			return "LPCM"
		if "PCM" in value:
			return "PCM"
		if "MP3" in value:
			return "MP3"
		if "MP2" in value or "MPEG" in value:
			return "MPEG"
		return description.split()[0] if description.split() else description

	def _extractAudioChannels(self, description, isMultichannel):
		if description:
			match = re.search(r"(?<!\d)([1-9]\.[0-9])(?:\s|$)", description)
			if match:
				return match.group(1)
			value = description.upper()
			if "STEREO" in value:
				return "Stereo"
			if "MONO" in value:
				return "Mono"
			if "5.1" in value:
				return "5.1"
			if "7.1" in value:
				return "7.1"
			if "2.0" in value:
				return "2.0"
		return "Mehrkanal" if isMultichannel else "Stereo"

	def _getAudioText(self, service, mode):
		description, language, count, currentTrack = self._getAudioData(service)
		isMultichannel = self._isMultichannelAudio(service)
		codec = self._normalizeAudioCodec(description)
		language = self._cleanAudioLanguage(language)
		channels = self._extractAudioChannels(description, isMultichannel)

		if mode == self.AUDIO_CODEC:
			return codec
		if mode == self.AUDIO_LANGUAGE:
			return language
		if mode == self.AUDIO_TRACKS:
			return str(count) if count else ""
		if mode == self.AUDIO_CHANNELS:
			return channels
		if mode == self.AUDIO_SHORT:
			return "Dolby" if isMultichannel else "Stereo"

		parts = []
		if language:
			parts.append(language)
		if codec:
			parts.append(codec)
		if channels and channels not in parts:
			parts.append(channels)
		if not parts and description:
			parts.append(description)
		return " ".join(parts)

	@cached
	def getBoolean(self):
		service = self.source.service
		if not service or self.type == self.UNKNOWN:
			return False

		info = service.info()

		if self.type in (self.SD, self.HD720, self.FHD1080, self.QHD1440, self.UHD4K):
			width, height, frameRate, progressive, gamma, aspect = self._getVideoInfo(info)
			return self.type == self._getResolutionType(height)

		if self.type in (self.SDR, self.HDR, self.HDR10, self.HLG, self.HDHDR, self.HDRANY):
			width, height, frameRate, progressive, gamma, aspect = self._getVideoInfo(info)
			hdrType = self._getHDRType(width, height, gamma)
			if self.type == self.HDRANY:
				return gamma > 0
			if self.type == self.HDHDR:
				return gamma > 0 and height and height <= 1080 and width and width > 720
			if self.type == self.SDR:
				return gamma in (-1, 0)
			return self.type == hdrType

		if self.type in (self.WIDESCREEN_TYPE, self.NOT_WIDESCREEN):
			width, height, frameRate, progressive, gamma, aspect = self._getVideoInfo(info)
			isWidescreen = aspect in WIDESCREEN
			return isWidescreen if self.type == self.WIDESCREEN_TYPE else not isWidescreen

		if self.type == self.TELETEXT:
			try:
				return info and info.getInfo(iServiceInformation.sTXTPID) != -1
			except Exception:
				return False

		if self.type == self.SUBTITLES:
			try:
				subtitle = service.subtitle()
				return bool(subtitle and subtitle.getSubtitleList())
			except Exception:
				return False

		if self.type == self.HBBTV:
			try:
				return info and info.getInfoString(iServiceInformation.sHBBTVUrl) != ""
			except Exception:
				return False

		if self.type in (self.MULTICHANNEL, self.STEREO):
			isMultichannel = self._isMultichannelAudio(service)
			return isMultichannel if self.type == self.MULTICHANNEL else not isMultichannel

		if self.type == self.CRYPTED:
			try:
				return info and info.getInfo(iServiceInformation.sIsCrypted) == 1 and not self._isSoftCSA(info)
			except Exception:
				return False

		if self.type == self.SOFTCSA:
			return self._isSoftCSA(info)

		frontendType = self._getFrontendType(service)

		# Wichtig:
		# Wenn ein echter DVB-Tuner erkannt wird, ist es kein IPTV.
		# Das verhindert falsches IPTV bei verschlüsselten Sendern über Oscam/SoftCSA.
		if frontendType is not None:
			return self.type == frontendType

		# SoftCSA darf nicht als IPTV gewertet werden, auch wenn service.streamed()
		# bei manchen Images nicht None liefert.
		if self._isSoftCSA(info):
			return False

		ref = ""
		try:
			ref = info and info.getInfoString(iServiceInformation.sServiceref) or ""
		except Exception:
			ref = ""

		isIPTV = self._isIPTVReference(ref) or self._isStreamed(service)
		return self.type == self.IPTV and isIPTV

	boolean = property(getBoolean)

	@cached
	def getText(self):
		service = self.source.service
		if not service:
			return ""

		info = service.info()
		if self.type == self.VIDEO_TEXT:
			return self._getResolutionText(info, short=False, withRate=True)
		if self.type == self.RESOLUTION_TEXT:
			return self._getResolutionText(info, short=False, withRate=False)
		if self.type == self.RESOLUTION_SHORT:
			return self._getResolutionText(info, short=True, withRate=False)
		if self.type in (self.AUDIO_TEXT, self.AUDIO_CODEC, self.AUDIO_LANGUAGE, self.AUDIO_TRACKS, self.AUDIO_CHANNELS, self.AUDIO_SHORT):
			return self._getAudioText(service, self.type)
		return ""

	text = property(getText)
