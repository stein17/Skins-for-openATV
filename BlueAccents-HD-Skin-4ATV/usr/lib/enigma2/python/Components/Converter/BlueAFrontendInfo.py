from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from Components.Element import cached
import NavigationInstance

class BlueAFrontendInfo(Poll, Converter, object):
	BER = 0
	SNR = 1
	AGC = 2
	LOCK = 3
	SNRdB = 4
	SLOT_NUMBER = 5
	TUNER_TYPE = 6
	REC_TUNER = 7

	def __init__(self, type):
		Poll.__init__(self)
		Converter.__init__(self, type)
		self.poll_interval = 1000
		self.poll_enabled = True
		if type == "BER":
			self.type = self.BER
		elif type == "SNR":
			self.type = self.SNR
		elif type == "SNRdB":
			self.type = self.SNRdB
		elif type == "AGC":
			self.type = self.AGC
		elif type == "NUMBER":
			self.type = self.SLOT_NUMBER
		elif type == "TYPE":
			self.type = self.TUNER_TYPE
		elif type.split("_")[0] == "REC":
			self.type = self.REC_TUNER
			self.tunernum = type.split("_")[1]
		else:
			self.type = self.LOCK

	@cached
	def getText(self):
		assert self.type not in (self.LOCK, self.SLOT_NUMBER), "the text output of FrontendInfo cannot be used for lock info"
		percent = None
		if self.type == self.BER: # as count
			count = self.source.ber
			if count is not None:
				return str(count)
			else:
				return "N/A"
		elif self.type == self.AGC:
			percent = self.source.agc
		elif self.type == self.SNR:
			percent = self.source.snr
		elif self.type == self.SNRdB:
			if self.source.snr_db is not None:
				return "%3.01f" % (self.source.snr_db / 100.0) + _("dB")
			elif self.source.snr is not None: #fallback to normal SNR...
				percent = self.source.snr
		elif self.type == self.TUNER_TYPE:
			return self.source.frontend_type and self.frontend_type or "Unknown"
		if percent is None:
			return "N/A"
		return "%d%%" % (percent * 100 / 65536)

	@cached
	def getBool(self):
		assert self.type in (self.LOCK, self.BER, self.REC_TUNER), "the boolean output of FrontendInfo can only be used for lock or BER info or Tuner-Rec"
		if self.type == self.LOCK:
			lock = self.source.lock
			if lock is None:
				lock = False
			return lock
		elif self.type == self.BER:
			ber = self.source.ber
			if ber is None:
				ber = 0
			return ber > 0
		elif self.type == self.REC_TUNER:
			for timer in NavigationInstance.instance.RecordTimer.timer_list:
				if timer.isRunning() and not timer.justplay:
					service = timer.record_service
					feinfo = service and service.frontendInfo()
					data = feinfo and feinfo.getFrontendData()
					if data:
						tuner = data.get('tuner_number', -1)
						if tuner is not None and tuner > -1 and tuner == int(self.tunernum):
							return True
			return False

	text = property(getText)
	boolean = property(getBool)

	@cached
	def getValue(self):
		assert self.type != self.LOCK, "the value/range output of FrontendInfo can not be used for lock info"
		if self.type == self.AGC:
			return self.source.agc or 0
		elif self.type == self.SNR:
			return self.source.snr or 0
		elif self.type == self.BER:
			if self.BER < self.range:
				return self.BER or 0
			else:
				return self.range
		elif self.type == self.TUNER_TYPE:
			type = self.source.frontend_type
			if type == 'DVB-S':
				return 0
			elif type == 'DVB-C':
				return 1
			elif type == 'DVB-T':
				return 2
			return -1
		elif self.type == self.SLOT_NUMBER:
			num = self.source.slot_number
			return num is None and -1 or num

	range = 65536
	value = property(getValue)

