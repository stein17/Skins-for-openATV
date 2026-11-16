# -*- coding: utf-8 -*-

import NavigationInstance

from Components.Converter.Converter import Converter
from Components.Element import cached
from enigma import iPlayableService, iServiceInformation


class PLiFullNightServiceOrbitalPosition(Converter):

    def __init__(self, type):
        Converter.__init__(self, type)

    @staticmethod
    def getSystem(system, prefix):
        if system is None:
            return prefix

        value = str(system).upper().replace("_", "").replace("-", "")

        if value in ("1", "S2", "DVBS2", "T2", "DVBT2"):
            return prefix + "2"

        if value in ("0", "S", "DVBS", "T", "DVBT"):
            return prefix

        return prefix

    @staticmethod
    def getReference(nav):
        try:
            ref = nav and nav.getCurrentlyPlayingServiceReference()
            if ref:
                return ref.toString().lower()
        except Exception:
            pass
        return ""

    @staticmethod
    def isDAB(refstr):
        return (
            refstr.startswith("4115:")
            or "dab%3a//" in refstr
            or "dab://" in refstr
        )

    @staticmethod
    def isDVBI(nav):
        try:
            flag = nav and getattr(
                nav, "isCurrentServiceDVBI", False
            )
            if callable(flag):
                flag = flag()
            return bool(flag)
        except Exception:
            return False

    @staticmethod
    def getTransponder(service):
        try:
            info = service and service.info()
            tp = info and info.getInfoObject(
                iServiceInformation.sTransponderData
            )
            if isinstance(tp, dict):
                return tp
        except Exception:
            pass
        return {}

    @staticmethod
    def getSatellitePosition(tp):
        try:
            raw = tp.get("orbital_position")
            if raw is None:
                return ""

            pos = int(raw)
            direction = "E"

            if pos > 1800:
                pos = 3600 - pos
                direction = "W"

            if pos < 0 or pos > 1800:
                return ""

            return "%d.%d %s" % (
                pos // 10,
                pos % 10,
                direction
            )
        except Exception:
            return ""

    @cached
    def getText(self):
        nav = NavigationInstance.instance
        service = self.source.service
        refstr = self.getReference(nav)

        # 1. DAB+ over DVB
        if self.isDAB(refstr):
            return "DAB+"

        # 2. Echtes DVB-I
        if self.isDVBI(nav):
            return "DVB-I: Internet"

        # 3. DVB-Tuner
        tp = self.getTransponder(service)

        if tp:
            tuner = str(tp.get("tuner_type", "")).upper()
            system = tp.get("system")

            if tuner.startswith("DVB-S"):
                typ = self.getSystem(system, "DVB-S")
                position = self.getSatellitePosition(tp)

                if position:
                    return "%s: %s" % (typ, position)

                return typ

            if tuner.startswith("DVB-T"):
                typ = self.getSystem(system, "DVB-T")
                return "%s: Terrestrial" % typ

            if tuner.startswith("DVB-C"):
                return "DVB-C: Cable"

        # 4. IPTV / Netzwerkstreams
        stream_markers = (
            "http%3a//",
            "https%3a//",
            "rtsp%3a//",
            "rtmp%3a//",
            "http://",
            "https://",
            "rtsp://",
            "rtmp://"
        )

        if any(marker in refstr for marker in stream_markers):
            return "IPTV: Stream"

        return ""

    text = property(getText)

    def changed(self, what):
        if (
            what[0] != self.CHANGED_SPECIFIC
            or what[1] == iPlayableService.evStart
        ):
            Converter.changed(self, what)
