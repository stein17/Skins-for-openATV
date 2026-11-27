# -*- coding: utf-8 -*-
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.config import config
import NavigationInstance


class PLiWQHDFullNightFrontendInfo(Converter):
    """Compatibility SNR/DVB-I text converter for older and newer OpenATV images."""

    def __init__(self, type):
        Converter.__init__(self, type)
        self.type = type

    @cached
    def getText(self):
        # New OpenATV DVB-I playback route. getattr keeps older images compatible.
        nav = NavigationInstance.instance
        if nav and getattr(nav, "isCurrentServiceDVBI", False):
            try:
                ref = nav.getCurrentlyPlayingServiceReference()
                if ref:
                    streamType = {0x100: "DASH", 0x200: "HLS"}.get(ref.getUnsignedData(7) & 0x300, "DVB-I")
                    return "IP: %s" % streamType
            except (AttributeError, TypeError, ValueError):
                return "IP: DVB-I"
            return "IP: DVB-I"

        # Normal DVB service: preserve the traditional SNR display.
        snr = getattr(self.source, "snr", None)
        snr_db = getattr(self.source, "snr_db", None)
        swap = getattr(getattr(config, "usage", None), "swap_snr_on_osd", None)
        swap = bool(swap and swap.value)

        if swap and snr_db is not None:
            return "SNR: %3.1f dB" % (snr_db / 100.0)
        if snr is None:
            return "SNR: N/A"
        return "SNR: %d %%" % int(snr * 100 / 65536)

    text = property(getText)
