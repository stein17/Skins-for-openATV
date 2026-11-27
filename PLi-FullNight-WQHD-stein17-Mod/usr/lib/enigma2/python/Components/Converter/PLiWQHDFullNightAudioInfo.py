from Plugins.Extensions.PLiFullNightWQHD import _
import re
from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from Components.Element import cached
from enigma import eServiceReference, iPlayableService, iServiceInformation


class PLiWQHDFullNightAudioInfo(Poll, Converter):
    GET_AUDIO_CODEC = 0

    def __init__(self, type):
        Converter.__init__(self, type)
        Poll.__init__(self)
        self.type = self.GET_AUDIO_CODEC
        self.poll_interval = 1000
        self.poll_enabled = True
        self.interesting_events = (iPlayableService.evUpdatedInfo,)

    def _isDAB(self, info):
        try:
            ref = info.getInfoString(iServiceInformation.sServiceref)
            return bool(ref and eServiceReference(ref).type == eServiceReference.idServiceDAB)
        except Exception:
            return False

    def _getDABAudio(self, info):
        try:
            codec = info.getInfoString(iServiceInformation.sTagCodec) or ""
        except Exception:
            codec = ""
        try:
            bitrate = info.getInfoString(iServiceInformation.sTagBitrate) or ""
        except Exception:
            bitrate = ""

        codec = codec.strip()
        bitrate = bitrate.strip()

        # Keep the 260 px InfoBar field compact. The separate DAB+ icon already
        # identifies the service, so only the useful codec name is shown here.
        if codec.startswith("DAB+ "):
            codec = codec[5:]
        elif codec == "DAB MPEG Audio Layer II":
            codec = "MP2"
        elif codec == "DAB (probing)":
            codec = "DAB+"

        if bitrate.startswith("0 "):
            bitrate = ""

        if codec and bitrate:
            return "%s  %s" % (codec, bitrate)
        return codec or bitrate or "DAB+"

    def _getNormalAudio(self, service):
        import re
        from Tools.ISO639 import LanguageCodes

        try:
            audio = service.audioTracks()
            if not audio:
                return _("unknown")

            index = audio.getCurrentTrack()
            if index < 0 or index >= audio.getNumberOfTracks():
                return _("unknown")

            track = audio.getTrackInfo(index)
            description = (track.getDescription() or "").strip()
            language = (track.getLanguage() or "").strip()
        except Exception:
            return _("unknown")

        # ISO639-Sprachen wie im originalen OpenATV TrackInfo.
        def language_name(code):
            code = code.strip().lower()
            if not code or code in ("und", "unknown", "qaa"):
                return ""
            entry = LanguageCodes.get(code)
            return _(entry[0]) if entry else code

        # Sprachangaben am Ende der Codec-Beschreibung erkennen.
        embedded = ""
        match = re.search(
            r"(?i)(?:^|\\s)(deutsch|german|english|francais|"
            r"deu|ger|eng|fra|fre|ara|tur|zho|chi|"
            r"de|en|fr|ar|tr|zh)\\s*$",
            description
        )
        if match:
            token = match.group(1).lower()
            aliases = {
                "deutsch": "deu",
                "german": "deu",
                "english": "eng",
                "francais": "fra",
            }
            embedded = aliases.get(token, token)
            description = description[:match.start()].strip()

        # Codec-Bezeichnung normalisieren.
        codecs = (
            (r"^(?:E[- ]?AC[- ]?3|AC[- ]?3\\+|DD\\+)(?=\\W|$)",
             "Dolby Digital Plus (E-AC-3)"),
            (r"^(?:AC[- ]?3|DD)(?=\\W|$)",
             "Dolby Digital (AC-3)"),
            (r"^AAC(?=\\W|$)", "AAC"),
            (r"^DTS(?=\\W|$)", "DTS"),
        )

        for pattern, name in codecs:
            m = re.match(pattern, description, re.I)
            if m:
                description = name + description[m.end():]
                break

        # Kanalzahl nur uebernehmen, wenn sie gemeldet wird.
        channel = re.search(
            r"(?<![0-9])(?:2[.,]0|5[.,]1|7[.,]1)(?![0-9])",
            description
        )

        if channel:
            channels = channel.group(0).replace(",", ".")
            description = (
                description[:channel.start()] +
                description[channel.end():]
            ).strip()
        elif re.search(r"\\bStereo\\b", description, re.I):
            channels = "2.0"
        else:
            channels = ""

        if channels:
            description = re.sub(
                r"\\bStereo\\b", "", description,
                flags=re.I
            ).strip()

            label = (
                "%s (2.0)" % _("Stereo")
                if channels == "2.0"
                else channels
            )
            description = ("%s %s" % (description, label)).strip()

        # Ausgewaehlte Audiosprache, nicht Image-Sprache.
        names = []
        for code in re.split(r"[/,;]", language):
            name = language_name(code)
            if name and name not in names:
                names.append(name)

        if not names and embedded:
            name = language_name(embedded)
            if name:
                names.append(name)

        if names:
            suffix = " / ".join(names)
            return (
                "%s · %s" % (description, suffix)
                if description else suffix
            )

        return description or _("unknown")

    @cached
    def getText(self):
        service = self.source.service
        if not service:
            return ""

        info = service.info()
        if not info:
            return ""

        if self._isDAB(info):
            return self._getDABAudio(info)

        return self._getNormalAudio(service)

    text = property(getText)

    def changed(self, what):
        if what[0] != self.CHANGED_SPECIFIC or what[1] in self.interesting_events:
            Converter.changed(self, what)
