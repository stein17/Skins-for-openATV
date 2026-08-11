from Components.Converter.Converter import Converter
from enigma import iServiceInformation, iPlayableService, iPlayableServicePtr, eServiceCenter
from Components.Element import cached
from ServiceReference import resolveAlternate
from Tools.Transponder import ConvertToHumanReadable

try:
	from urllib.parse import unquote
except ImportError:
	from urllib import unquote


class BLWQHDTransponderInfo(Converter):
	def __init__(self, type):
		Converter.__init__(self, type)
		self.type = type.split(";")

	def _hasType(self, *names):
		items = [x.strip().lower() for x in self.type if x and x.strip()]
		names = [x.strip().lower() for x in names if x and x.strip()]
		return any(x in items for x in names)

	def _refToString(self, ref):
		if not ref:
			return ""
		try:
			ref = ref.toString()
		except Exception:
			try:
				ref = str(ref)
			except Exception:
				return ""
		try:
			ref = unquote(ref)
		except Exception:
			ref = ref.replace("%3a", ":").replace("%3A", ":")
		return ref

	def _getSourceRefString(self, info=None):
		# Important for source="session.CurrentService": IPTV has often no usable
		# iServiceInformation.sServiceref, but the Source still has the current ref.
		for attr in ("serviceref", "serviceReference", "ref"):
			try:
				ref = getattr(self.source, attr, None)
			except Exception:
				ref = None
			ref = self._refToString(ref)
			if ref and ref.lower() != "none":
				return ref
		if info:
			try:
				ref = info.getInfoString(iServiceInformation.sServiceref)
			except Exception:
				ref = ""
			return self._refToString(ref)
		return ""

	def _streamText(self, ref):
		if not ref or "://" not in ref:
			return ""
		try:
			host = ref.rsplit("://", 1)[1].split("/", 1)[0]
			# Do not show user:password@ in the skin.
			if "@" in host:
				host = host.rsplit("@", 1)[1]
			return _("Stream") + " " + host
		except Exception:
			return ""

	@cached
	def getText(self):
		service = self.source.service
		ref = None
		refstr = ""
		if isinstance(service, iPlayableServicePtr):
			info = service and service.info()
			refstr = self._getSourceRefString(info)
		else:  # reference, e.g. ChannelSelection/ServiceEvent
			info = service and self.source.info
			ref = service
		if not info:
			return ""
		if ref:
			nref = resolveAlternate(ref)
			if nref:
				ref = nref
				info = eServiceCenter.getInstance().info(ref)
			transponderraw = info.getInfoObject(ref, iServiceInformation.sTransponderData)
			refstr = self._refToString(ref)
		else:
			transponderraw = info.getInfoObject(iServiceInformation.sTransponderData)
			if not refstr:
				refstr = self._getSourceRefString(info)
		if transponderraw:
			transponderdata = ConvertToHumanReadable(transponderraw)
			try:
				[onid, tsid] = [int(x, 16) for x in refstr.split(':')[4:6]]  # Retrieve onid and tsid from service reference
			except Exception:
				onid, tsid = 0, 0
			if not transponderdata["system"]:
				transponderdata["system"] = transponderraw.get("tuner_type", "None")
			try:
				# Optional skin argument:
				# <convert type="TransponderInfo">no_ids</convert>
				# removes the TSID-ONID part like "1-1057" from the visible text.
				show_ids = not self._hasType("no_ids", "noids", "no_id", "noid")
				ids = show_ids and "%s-%s " % (tsid, onid) or ""
				if "DVB-T" in transponderdata["system"]:
					return "%s %s%s %d MHz %s" % (transponderdata["system"], ids, transponderdata["channel"], transponderdata["frequency"] / 1000000 + 0.5, transponderdata["bandwidth"])
				elif "DVB-C" in transponderdata["system"]:
					return "%s %s%d MHz %d %s %s" % (transponderdata["system"], ids, transponderdata["frequency"] / 1000 + 0.5, transponderdata["symbol_rate"] / 1000 + 0.5, transponderdata["fec_inner"],
						transponderdata["modulation"])
				elif "ATSC" in transponderdata["system"]:
					return "%s %s%d MHz %s" % (transponderdata["system"], ids, transponderdata["frequency"] / 1000 + 0.5, transponderdata["modulation"])
				return "%s %s%d %s %d %s %s %s" % (transponderdata["system"], ids, transponderdata["frequency"] / 1000 + 0.5, transponderdata["polarization_abbreviation"], transponderdata["symbol_rate"] / 1000 + 0.5,
					transponderdata["fec_inner"], transponderdata["modulation"], transponderdata[self._hasType("detailed_satpos") and "orbital_position" or "orb_pos"])
			except Exception:
				return ""
		return self._streamText(refstr)

	text = property(getText)

	@cached
	def getBoolean(self):
		# finds "DVB-S", "DVB-S2", "DVB-T", "DVB-T2", "DVB-C", "ATSC", "Stream" or combinations of these,
		# e.g. <convert type="TransponderInfo">DVB-S;DVB-S2</convert> to return True for either.
		s = self.getText()
		s = s and s.strip().split() and s.strip().split()[0].lower()  # Get the first group of characters, and, convert to lower case
		t = self.type and [x.lower() for x in self.type if x]  # Only populated entries, and, convert to lower case
		return bool(s and t and s in t)

	boolean = property(getBoolean)

	def changed(self, what):
		if what[0] != self.CHANGED_SPECIFIC or what[1] in (iPlayableService.evStart,):
			Converter.changed(self, what)
