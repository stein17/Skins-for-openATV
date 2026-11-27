"""FullNight's optional ECM row, using OpenATV's shared ECM reader/cache."""

import re

from enigma import iServiceInformation
from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from Components.Element import cached
from Components.config import config
from Tools.GetEcmInfo import GetEcmInfo


def ecm_time(value):
    value = str(value).strip()
    if re.fullmatch(r"\d+[.,]\d+", value):
        return value.replace(",", ".") + " s"
    if value.isdigit():
        return value + " ms"
    if re.fullmatch(r"\d+(?:[.,]\d+)?\s*(?:msec|ms|s)", value):
        return value
    return ""


def summary(ecm, hide_names=False):
    native, caid, provider, pid = ecm.getEcmData()[:4]
    try:
        if not int(caid, 16):
            return ""
    except (TypeError, ValueError):
        return ""
    protocol = ecm.getInfo("protocol") or ecm.getInfo("using")
    parts = [protocol] if protocol and protocol != "fta" else []
    if hide_names:
        # Native verbose text can include an address or reader even when 'from'
        # is masked. Keep all source names out when the OSD privacy option is set.
        timing = ecm_time(ecm.getInfo("ecm time"))
        if timing:
            parts.append(timing)
        hops = ecm.getInfo("hops")
        if hops.isdigit() and int(hops):
            parts.append("Hops " + hops)
    elif native:
        parts.append(" ".join(native.split()))
    try:
        if int(pid, 16):
            parts.append(f"PID {int(pid, 16):04X}")
    except (TypeError, ValueError):
        pass
    return "ECM: " + "  |  ".join(parts) if parts else ""


class PLiWQHDFullNightEcmInfo(Poll, Converter):
    def __init__(self, type):
        Converter.__init__(self, type)
        Poll.__init__(self)
        self.ecm = GetEcmInfo()
        self.poll_interval = 1000
        self.poll_enabled = True

    @cached
    def getText(self):
        if config.usage.show_cryptoinfo.value < 1:
            return ""
        service = self.source.service
        info = service and service.info()
        if not info or info.getInfo(iServiceInformation.sIsCrypted) != 1:
            return ""
        # Some softcams include a SID. Reject an ECM left over from another
        # service while tuning; older formats without a SID remain supported.
        sid = self.ecm.getInfo("sid")
        if sid:
            try:
                if int(sid, 16) != info.getInfo(iServiceInformation.sSID):
                    return ""
            except ValueError:
                return ""
        return summary(self.ecm, config.softcam.hideServerName.value)

    text = property(getText)
