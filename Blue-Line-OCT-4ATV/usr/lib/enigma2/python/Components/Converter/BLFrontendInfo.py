# Embedded file name: /usr/lib/enigma2/python/Components/Converter/AXBlueFrontendInfo.py
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.config import config

class BLFrontendInfo(Converter, object):
    BER = 0
    SNR = 1
    AGC = 2
    LOCK = 3
    SNRdB = 4
    SLOT_NUMBER = 5
    TUNER_TYPE = 6

    def __init__(self, type):
        Converter.__init__(self, type)
        if type == 'BER':
            self.type = self.BER
        elif type == 'SNR':
            self.type = self.SNR
        elif type == 'SNRdB':
            self.type = self.SNRdB
        elif type == 'AGC':
            self.type = self.AGC
        elif type == 'NUMBER':
            self.type = self.SLOT_NUMBER
        elif type == 'TYPE':
            self.type = self.TUNER_TYPE
        else:
            self.type = self.LOCK

    @cached
    def getText(self):
        percent = None
        swapsnr = config.usage.swap_snr_on_osd.value
        if self.type == self.BER:
            count = self.source.ber
            if count is not None:
                return str(count)
            else:
                return 'N/A'
        elif self.type == self.AGC:
            percent = self.source.agc
        elif self.type == self.SNR and not swapsnr or self.type == self.SNRdB and swapsnr:
            percent = self.source.snr
        elif self.type == self.SNR or self.type == self.SNRdB:
            if self.source.snr_db is not None:
                return '%3.01f dB' % (self.source.snr_db / 100.0)
            if self.source.snr is not None:
                percent = self.source.snr
        elif self.type == self.TUNER_TYPE:
            return self.source.frontend_type and self.frontend_type or 'Unknown'
        if percent is None:
            return 'N/A'
        else:
            return '%d %%' % (percent * 100 / 65536)
            return

    @cached
    def getBool(self):
        if self.type == self.LOCK:
            lock = self.source.lock
            if lock is None:
                lock = False
            return lock
        else:
            ber = self.source.ber
            if ber is None:
                ber = 0
            return ber > 0
            return

    text = property(getText)
    boolean = property(getBool)

    @cached
    def getValue(self):
        if self.type == self.AGC:
            return self.source.agc or 0
        elif self.type == self.SNR:
            return self.source.snr or 0
        else:
            if self.type == self.BER:
                if self.BER < self.range:
                    return self.BER or 0
                else:
                    return self.range
            else:
                if self.type == self.TUNER_TYPE:
                    type = self.source.frontend_type
                    if type == 'DVB-S':
                        return 0
                    if type == 'DVB-C':
                        return 1
                    if type == 'DVB-T':
                        return 2
                    if type == 'ATSC':
                        return 3
                    return -1
                if self.type == self.SLOT_NUMBER:
                    num = self.source.slot_number
                    return num is None and -1 or num
            return None
            return None

    range = 65536
    value = property(getValue)