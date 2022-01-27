#	GlamourBase converter
#	Modded and recoded by MCelliotG for use in Glamour skins or standalone, added Python3 support
#	codecs map based on PliExtraInfo
#	If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

from __future__ import absolute_import, division
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Converter.Poll import Poll 
import NavigationInstance
from ServiceReference import ServiceReference, resolveAlternate 
from enigma import iServiceInformation, iPlayableService, iPlayableServicePtr, eServiceCenter
from Tools.Transponder import ConvertToHumanReadable
from Components.config import config
import os.path


def sp(text):
	if text:
		text += " "
	return text

# codec map
codecs = {
	-1: "N/A",
	0: "MPEG2",
	1: "AVC",
	2: "H263",
	3: "VC1",
	4: "MPEG4-VC",
	5: "VC1-SM",
	6: "MPEG1",
	7: "HEVC",
	8: "VP8",
	9: "VP9",
	10: "XVID",
	11: "N/A 11",
	12: "N/A 12",
	13: "DIVX 3.11",
	14: "DIVX 4",
	15: "DIVX 5",
	16: "AVS",
	17: "N/A 17",
	18: "VP6",
	19: "N/A 19",
	20: "N/A 20",
	21: "SPARK",
}

satnames = (
	(179.7, 180.3, "Intelsat 18"),
	(173.5, 174.5, "Eutelsat 174A"),
	(171.7, 172.3, "Eutelsat 172B"),
	(168.7, 169.3, "Horizons 3e"),
	(165.7, 166.3, "Intelsat 19"),
	(163.7, 164.3, "Optus 10"),
	(161.7, 162.3, "Superbird B3"),
	(159.7, 160.3, "Optus D1"),
	(158.7, 159.3, "ABS 6"),
	(155.7, 156.3, "Optus 10,D3"),
	(153.7, 154.3, "JCSat 2B"),
	(151.7, 152.3, "Optus D2"),
	(150.4, 150.8, "BRIsat"),
	(149.7, 150.3, "JCSat 18/Kacific 1"),
	(145.7, 146.3, "Nasuntara Satu"),
	(143.7, 144.3, "Superbird C2"),
	(141.7, 142.3, "Apstar 9"),
	(139.7, 140.3, "Express AM5,AT2"),
	(137.7, 138.3, "Telstar 18 Vantage"),
	(135.7, 136.3, "JCSat 2A"),
	(133.7, 134.3, "Apstar 6C"),
	(131.7, 132.3, "Vinasat 1,2/JCSat 5A"),
	(129.7, 130.3, "Chinasat 6C"),
	(128.4, 128.8, "LaoSat 1"),
	(127.7, 128.3, "JCSat 3A,16"),
	(124.7, 125.3, "ChinaSat 6A"),
	(123.7, 124.3, "JCSat 4B"),
	(120.7, 122.5, "AsiaSat 9"),
	(119.8, 120.3, "AsiaSat 6/Thaicom 7"),
	(118.8, 119.7, "Bangabandhu 1/Thaicom 4"),
	(117.8, 118.3, "Telkom 3S"),
	(115.8, 116.3, "KoreaSat 6,7"),
	(115.3, 115.7, "ChinaSat 6B"),
	(112.7, 113.3, "Palapa D/KoreaSat 5,5A"),
	(110.3, 110.8, "ChinaSat 10"),
	(109.7, 110.2, "BSat 3A,3C,4A,4B/JCSat 15,110R"),
	(107.5, 108.5, "SES 7,9/Telkom 4"),
	(105.3, 105.8, "AsiaSat 7"),
	(104.8, 105.1, "Asiastar 1"),
	(103.4, 103.7, "ChinaSat 2C"),
	(102.7, 103.3, "Express AM3"),
	(100.0, 100.7, "AsiaSat 5"),
	(97.8, 98.4, "Chinasat 11"),
	(96.8, 97.7, "G-Sat 9"),
	(96.2, 96.7, "Express-103"),
	(94.7, 95.3, "SES 8,12"),
	(93.0, 93.8, "G-Sat 15,17"),
	(92.0, 92.5, "ChinaSat 9"),
	(91.3, 91.8, "Measat 3,3A,3B"),
	(88.8, 90.3, "Yamal 401"),
	(87.8, 88.3, "ST 2"),
	(87.2, 87.7, "ChinaSat 12"),
	(86.2, 86.8, "KazSat 2"),
	(84.8, 85.5, "Intelsat 15/Horizons 2"),
	(82.8, 83.3, "G-Sat 10,30"),
	(81.8, 82.3, "JCSat 4A"),
	(81.2, 81.7, "Chinasat 1C"),
	(79.8, 80.4, "Express-80"),
	(78.3, 78.8, "ThaiCom 6,8"),
	(76.3, 76.8, "Apstar 7"),
	(74.7, 75.4, "ABS 2,2A"),
	(73.7, 74.4, "G-Sat 11,18"),
	(71.7, 72.4, "Intelsat 22"),
	(70.3, 70.8, "Eutelsat 70B"),
	(69.8, 70.2, "Raduga-1M 3"),
	(68.0, 68.8, "Intelsat 20,36"),
	(65.8, 66.3, "Intelsat 17"),
	(64.8, 65.3, "Amos 4"),
	(63.8, 64.4, "Intelsat 39"),
	(63.2, 63.6, "Astra 1G"),
	(62.8, 63.1, "G-Sat 7A"),
	(62.4, 62.7, "Inmarsat GX1"),
	(61.7, 62.3, "Intelsat 39"),
	(60.8, 61.2, "ABS 4"),
	(60.2, 60.4, "WGS 2"),
	(59.4, 60.1, "Intelsat 33e"),
	(58.3, 58.7, "KazSat 3"),
	(56.8, 57.3, "NSS 12"),
	(56.4, 56.7, "Inmarsat GX4"),
	(55.7, 56.3, "Express AT1"),
	(55.0, 55.4, "Yamal 402/G-Sat 8,16"),
	(54.6, 54.9, "Yamal 402"),
	(52.8, 53.3, "Express AM6"),
	(52.3, 52.7, "Al Yah 1"),
	(51.8, 52.2, "TurkmenÄlem/MonacoSat"),
	(51.2, 51.7, "Belintersat 1"),
	(50.4, 50.7, "NSS 5"),
	(49.7, 50.3, "Türksat 4B"),
	(48.7, 49.3, "Yamal 601"),
	(47.8, 48.3, "G-Sat 19,31"),
	(47.6, 47.7, "Al Yah 2"),
	(45.7, 46.3, "AzerSpace 1/Africasat 1A"),
	(44.7, 45.3, "AzerSpace 2/Intelsat 38/Blagovest 1"),
	(42.4, 42.7, "Nigcomsat 1R"),
	(41.7, 42.3, "Türksat 3A,4A"),
	(39.8, 40.3, "Express AM7"),
	(38.7, 39.3, "HellasSat 3,4"),
	(37.9, 38.5, "Paksat 1R/MM1"),
	(37.6, 37.8, "Athena-Fidus"),
	(36.8, 37.3, "Sicral 2"),
	(35.7, 36.3, "Eutelsat 36B,36C"),
	(32.9, 33.3, "Eutelsat 33E"),
	(32.6, 32.8, "Intelsat 28"),
	(31.4, 31.8, "Astra 5B"),
	(31.1, 31.3, "Hylas 2,3"),
	(30.7, 31.0, "Türksat 5A"),
	(30.2, 30.6, "Arabsat 5A,6A"),
	(28.0, 28.8, "Astra 2E,2F,2G"),
	(25.2, 26.3, "Badr 4,5,6,7/Es'hail 1,2"),
	(23.0, 23.8, "Astra 3B"),
	(21.4, 21.8, "Eutelsat 21B"),
	(20.8, 21.2, "AfriStar 1"),
	(19.8, 20.5, "Arabsat 5C"),
	(18.8, 19.5, "Astra 1KR,1L,1M,1N"),
	(16.6, 17.3, "Amos 17"),
	(15.6, 16.3, "Eutelsat 16A"),
	(12.7, 13.5, "HotBird 13B,13C,13E"),
	(11.5, 11.9, "Sicral 1B"),
	(9.7, 10.3, "Eutelsat 10A"),
	(8.7, 9.3, "Eutelsat 9B,Ka-Sat"),
	(6.7, 7.3, "Eutelsat 7B,7C"),
	(5.7, 6.3, "WGS 1"),
	(4.5, 5.4, "Astra 4A/SES 5"),
	(3.0, 3.6, "Eutelsat 3B"),
	(2.5, 2.9, "Rascom QAF 1R"),
	(1.4, 2.4, "BulgariaSat 1"),
	(-0.5, -1.2, "Thor 5,6,7/Intelsat 10-02"),
	(-2.7, -3.3, "ABS 3A"),
	(-3.7, -4.4, "Amos 3,7"),
	(-4.7, -5.4, "Eutelsat 5WB"),
	(-6.7, -7.2, "Nilesat 201/Eutelsat 7WA"),
	(-7.3, -7.4, "Eutelsat 7 West A"),
	(-7.5, -7.7, "Eutelsat 7WA,8WB"),
	(-7.8, -8.3, "Eutelsat 8 West B"),
	(-10.7, -11.3, "Express AM44"),
	(-11.8, -12.3, "WGS 3"),
	(-13.8, -14.3, "Express AM8"),
	(-14.8, -15.3, "Telstar 12 Vantage"),
	(-17.8, -18.3, "Intelsat 37e"),
	(-19.8, -20.3, "NSS 7"),
	(-21.8, -22.4, "SES 4"),
	(-24.2, -24.6, "Intelsat 905"),
	(-24.7, -25.2, "AlcomSat 1"),
	(-27.2, -27.8, "Intelsat 901"),
	(-29.3, -29.7, "Intelsat 701"),
	(-29.8, -30.5, "Hispasat 30W-5,30W-6"),
	(-31.2, -31.8, "Intelsat 25"),
	(-33.3, -33.7, "Hylas 4"),
	(-34.2, -34.8, "Intelsat 35e"),
	(-35.7, -36.3, "Hispasat 36W-1"),
	(-37.2, -37.7, "Telstar 11N"),
	(-40.2, -40.8, "SES 6"),
	(-42.7, -43.5, "Intelsat 11/Sky Brasil 1"),
	(-44.7, -45.3, "Intelsat 14"),
	(-47.2, -47.8, "SES 14"),
	(-52.7, -53.3, "Intelsat 23"),
	(-53.7, -54.3, "Inmarsat-3 F5"),
	(-54.7, -55.2, "Inmarsat GX2"),
	(-55.3, -55.8, "Intelsat 34"),
	(-57.7, -58.3, "Intelsat 21"),
	(-59.7, -61.3, "Amazonas 2,3,5"),
	(-61.4, -61.7, "EchoStar 16,18"),
	(-62.8, -63.2, "Telstar 14R,19"),
	(-64.7, -65.3, "Eutelsat 65WA/Star One C1"),
	(-66.7, -67.5, "SES 10"),
	(-67.7, -68.3, "Echostar 23"),
	(-69.7, -70.3, "Star One C2,C4"),
	(-71.5, -72.3, "Arsat 1"),
	(-72.4, -72.8, "Nimiq 5"),
	(-73.7, -74.3, "Hispasat 74W-1"),
	(-74.7, -75.3, "Star One C3"),
	(-76.0, -76.5, "Intelsat 16"),
	(-76.7, -77.3, "QuetzSat 1"),
	(-78.5, -79.2, "Sky Mexico 1"),
	(-80.7, -81.3, "Arsat 2"),
	(-81.7, -82.3, "Nimiq 4"),
	(-82.7, -83.3, "AMC 18"),
	(-83.7, -84.3, "Star One D1"),
	(-84.7, -85.5, "Sirius XM3,XM5"),
	(-86.7, -87.5, "SES 2/TKSat 1"),
	(-88.7, -89.3, "Galaxy 28"),
	(-90.7, -91.3, "Nimiq 6/Galaxy 17"),
	(-92.7, -93.4, "Galaxy 25"),
	(-94.7, -95.4, "Galaxy 3C/Intelsat 30,31"),
	(-96.7, -97.4, "Galaxy 19/EchoStar 19"),
	(-98.8, -99.5, "Galaxy 16/T11,T14"),
	(-100.7, -101.4, "SES 1/T9S,T16"),
	(-102.9, -103.4, "SES 3/T10,T12"),
	(-104.7, -105.4, "AMC 15/SES-11/Echostar 105"),
	(-107.2, -107.6, "Anik F1R,G1"),
	(-109.7, -110.4, "EchoStar 10,11/T5"),
	(-110.8, -111.5, "Anik F2"),
	(-112.7, -113.4, "Eutelsat 113 West A"),
	(-114.6, -115.4, "Eutelsat 115 West B/XM 4"),
	(-115.8, -116.3, "Sirius FM6"),
	(-116.6, -117.4, "Eutelsat 117 West A,B"),
	(-118.7, -119.4, "Anik F3/T8/EchoStar 14"),
	(-120.7, -121.4, "EchoStar 9/Galaxy 23"),
	(-122.7, -123.4, "Galaxy 18"),
	(-124.7, -125.4, "AMC 21/Galaxy 30"),
	(-126.7, -127.4, "Galaxy 13/Horizons 1"),
	(-128.7, -129.4, "Ciel 2/SES 15"),
	(-130.7, -131.4, "AMC 11"),
	(-132.7, -133.4, "Galaxy 15"),
	(-134.7, -135.4, "AMC 10"),
	(-138.7, -139.4, "AMC 8"),
	(-176.7, -177.4, "NSS 9/Yamal 300K")
)


class BlueACodec(Poll, Converter, object):
	FREQINFO = 0
	ORBITAL = 1
	RESCODEC = 2
	PIDINFO = 3
	PIDHEXINFO = 4
	VIDEOCODEC = 5
	FPS = 6
	VIDEOSIZE = 7
	IS1080 = 8
	IS720 = 9
	IS576 = 10
	IS1440 = 11
	IS2160 = 12
	IS480 = 13
	IS360 = 14
	IS288 = 15
	IS240 = 16
	IS144 = 17
	ISPROGRESSIVE = 18
	ISINTERLACED = 19
	STREAMURL = 20
	STREAMTYPE = 21
	ISSTREAMING = 22
	HASMPEG2 = 23
	HASAVC = 24
	HASH263 = 25
	HASVC1 = 26
	HASMPEG4VC = 27
	HASHEVC = 28
	HASMPEG1 = 29
	HASVP8 = 30
	HASVP9 = 31
	HASVP6 = 32
	HASDIVX = 33
	HASXVID = 34
	HASSPARK = 35
	HASAVS = 36
	ISSDR = 37
	ISHDR = 38
	ISHDR10 = 39
	ISHLG = 40
	HDRINFO = 41


	def __init__(self, type):
		Converter.__init__(self, type)
		self.type = type
		self.short_list = True
		Poll.__init__(self)
		self.poll_interval = 1000
		self.poll_enabled = True
		self.list = []
		if "FreqInfo" in type:
			self.type = self.FREQINFO
		elif "Orbital" in type:
			self.type = self.ORBITAL
		elif "ResCodec" in type:
			self.type = self.RESCODEC 
		elif "VideoCodec" in type:
			self.type = self.VIDEOCODEC
		elif "Fps" in type:
			self.type = self.FPS
		elif "VideoSize" in type:
			self.type = self.VIDEOSIZE
		elif "PidInfo" in type:
			self.type = self.PIDINFO
		elif "PidHexInfo" in type:
			self.type = self.PIDHEXINFO
		elif "Is1080" in type:
			self.type = self.IS1080
		elif "Is720" in type:
			self.type = self.IS720
		elif "Is576" in type:
			self.type = self.IS576
		elif "Is1440" in type:
			self.type = self.IS1440
		elif "Is2160" in type:
			self.type = self.IS2160
		elif "Is480" in type:
			self.type = self.IS480
		elif "Is360" in type:
			self.type = self.IS360
		elif "Is288" in type:
			self.type = self.IS288
		elif "Is240" in type:
			self.type = self.IS240
		elif "Is144" in type:
			self.type = self.IS144
		elif "IsProgressive" in type:
			self.type = self.ISPROGRESSIVE
		elif "IsInterlaced" in type:
			self.type = self.ISINTERLACED
		elif "StreamUrl" in type:
			self.type = self.STREAMURL
		elif "StreamType" in type:
			self.type = self.STREAMTYPE
		elif "IsStreaming" in type:
			self.type = self.ISSTREAMING
		elif "HasMPEG2" in type:
			self.type = self.HASMPEG2
		elif "HasAVC" in type:
			self.type = self.HASAVC
		elif "HasH263" in type:
			self.type = self.HASH263
		elif "HasVC1" in type:
			self.type = self.HASVC1
		elif "HasMPEG4VC" in type:
			self.type = self.HASMPEG4VC
		elif "HasHEVC" in type:
			self.type = self.HASHEVC
		elif "HasMPEG1" in type:
			self.type = self.HASMPEG1
		elif "HasVP8" in type:
			self.type = self.HASVP8
		elif "HasVP9" in type:
			self.type = self.HASVP9
		elif "HasVP6" in type:
			self.type = self.HASVP6
		elif "HasDIVX" in type:
			self.type = self.HASDIVX
		elif "HasXVID" in type:
			self.type = self.HASXVID
		elif "HasSPARK" in type:
			self.type = self.HASSPARK
		elif "HasAVS" in type:
			self.type = self.HASAVS
		elif "IsSDR" in type:
			self.type = self.ISSDR
		elif "IsHDR" in type:
			self.type = self.ISHDR
		elif "IsHDR10" in type:
			self.type = self.ISHDR10
		elif "IsHLG" in type:
			self.type = self.ISHLG
		elif "HDRInfo" in type:
			self.type = self.HDRINFO


######### COMMON VARIABLES #################
	def videowidth(self, info):
		width = 0
		if os.path.exists("/proc/stb/vmpeg/0/xres"):
			with open("/proc/stb/vmpeg/0/xres", "r") as w:
				try:
					width = int(w.read(),16)
				except:
					pass
		if (width > 0) and not (width == 4294967295):
			return width
		else:
			return ""

	def videoheight(self, info):
		height = 0
		if os.path.exists("/proc/stb/vmpeg/0/yres"):
			with open("/proc/stb/vmpeg/0/yres", "r") as h:
				try:
					height = int(h.read(),16)
				except:
					pass
		if (height > 0) and not (height == 4294967295):
			return height
		else:
			return ""

	def proginfo(self, info):
		progrs = ""
		if os.path.exists("/proc/stb/vmpeg/0/progressive"):
			with open("/proc/stb/vmpeg/0/progressive", "r") as prog:
				try:
					progrs = "p" if int(prog.read(),16) else "i"
				except:
					pass
		return progrs

	def videosize(self, info):
		xresol = str(self.videowidth(info))
		yresol = str(self.videoheight(info))
		progrs = self.proginfo(info)
		if (xresol > "0"):
			videosize = "%sx%s%s" % (xresol, yresol, progrs)
			return videosize
		else:
			return ""

	def framerate(self, info):
		fps = 0
		if os.path.exists("/proc/stb/vmpeg/0/framerate"):
			with open("/proc/stb/vmpeg/0/framerate", "r") as fp:
				try:
					fps = int(fp.read())
				except:
					pass
			if (fps < 0) or (fps == -1):
				return ""
			fps = "%6.3f" % (fps/1000.)
		return "%s fps" % (fps.replace(".000", ""))

	def videocodec(self, info):
		vcodec = codecs.get(info.getInfo(iServiceInformation.sVideoType), "N/A")
		return "%s" % (vcodec)

	def hdr(self, info):
		gamma = info.getInfo(iServiceInformation.sGamma)
		if gamma == 0:
			return "SDR"
		elif gamma == 1:
			return "HDR"
		elif gamma == 2:
			return "HDR10"
		elif gamma == 3:
			return "HLG"
		else:
			return ""

	def frequency(self, tp):
		freq = (tp.get("frequency") + 500)
		if freq:
			frequency = str(int(freq) // 1000)
			return frequency
		else:
			return ""

	def terrafreq(self, tp):
		return str(int(tp.get("frequency") + 1) // 1000000)

	def channel(self, tpinfo):
		return str(tpinfo.get("channel")) or ""

	def symbolrate(self, tp):
		return str(int(tp.get("symbol_rate", 0) // 1000))

	def polarization(self, tpinfo):
		return str(tpinfo.get("polarization_abbreviation")) or ""

	def fecinfo(self, tpinfo):
		return str(tpinfo.get("fec_inner")) or ""

	def tunernumber(self, tpinfo):
		return str(tpinfo.get("tuner_number")) or ""

	def system(self, tpinfo):
		return str(tpinfo.get("system")) or ""

	def modulation(self, tpinfo):
		return str(tpinfo.get("modulation")) or ""

	def constellation(self, tpinfo):
		return str(tpinfo.get("constellation"))

	def tunersystem(self, tpinfo):
		return str(tpinfo.get("system")) or ""

	def tunertype(self, tp):
		return str(tp.get("tuner_type")) or ""

	def terrafec(self, tpinfo):
		return "LP:%s HP:%s GI:%s" % (tpinfo.get("code_rate_lp"), tpinfo.get("code_rate_hp"), tpinfo.get("guard_interval"))

	def plpid(self, tpinfo):
		plpid = str(tpinfo.get("plp_id", 0))
		if plpid == "None" or plpid == "-1":
			return ""
		else:
			return "PLP ID:%s" % plpid

	def t2mi_info(self, tpinfo):
		try:
			t2mi_id = str(tpinfo.get("t2mi_plp_id",-1))
			t2mi_pid = str(tpinfo.get("t2mi_pid"))
			if t2mi_id == "None" or t2mi_id == "-1" or t2mi_pid == "0":
				t2mi_id = ""
				t2mi_pid = ""
			else:
				t2mi_id = "T2MI PLP %s" % t2mi_id
				if t2mi_pid == "None":
					t2mi_pid = ""
				else:
					t2mi_pid = "PID %s" % t2mi_pid
			return sp(t2mi_id) + sp(t2mi_pid)
		except:
			return ""

	def multistream(self, tpinfo):
		isid = str(tpinfo.get("is_id", 0)) 
		plscode = str(tpinfo.get("pls_code", 0))
		plsmode = str(tpinfo.get("pls_mode", None))
		if plsmode == "None" or plsmode == "Unknown" or (plsmode != "None" and plscode == "0"):
			plsmode = ""
		if isid == "None" or isid == "-1" or isid == "0":
			isid = ""
		else:
			isid = "IS:%s" % (isid)
		if plscode == "None" or plscode == "-1" or plscode == "0":
			plscode = ""
		if (plscode == "0" and plsmode == "Gold") or (plscode == "1" and plsmode == "Root"):
			return isid
		else:
			return sp(isid) + sp(plsmode) + sp(plscode)

	def satname(self, tp):
		sat = "Satellite:"
		orb = int(tp.get("orbital_position"))
		orbe = float(orb) / 10.0
		orbw = float(orb - 3600) / 10.0
		for sn in satnames:
			try:
				if sn[0] <= orbe <= sn[1] or sn[1] <= orbw <= sn[0]:
					sat = sn[2]
			except:
				pass
		return sat

	def orbital(self, tp):
		orbp = tp.get("orbital_position")
		if orbp > 1800:
			orbp = str((float(3600 - orbp)) / 10.0) + "°W"
		else:
			orbp = str((float(orbp)) / 10.0) + "°E"
		return orbp

	def reference(self):
		playref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
		if playref:
			refstr = playref.toString() or ""
			return refstr

	def streamtype(self):
		playref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
		if playref:
			refstr = playref.toString()
			strtype = refstr.replace("%3a", ":")
			if "0.0.0.0:" in strtype and (strtype.startswith("1:0:")) or "127.0.0.1:" in strtype and (strtype.startswith("1:0:")) or "localhost:" in strtype and (strtype.startswith("1:0:")):
				return "Internal TS Relay"
			if not (strtype.startswith("1:0:")):
				return "IPTV/Non-TS Stream"
			if "%3a/" in refstr and (strtype.startswith("1:0:")):
				return "IPTV/TS Stream"
			if (strtype.startswith("1:134:")):
				return "Alternative"
			else:
				return ""

	def streamurl(self):
		playref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
		if playref:
			refstr = playref.toString()
			if "%3a/" in refstr or ":/" in refstr:
				strurl = refstr.split(":")
				streamurl = strurl[10].replace("%3a", ":")
				if len(streamurl) > 80:
					streamurl = "%s..." % streamurl[:79]
				return streamurl
			else:
				return ""

	def pidstring(self, info):
		vpid = info.getInfo(iServiceInformation.sVideoPID)
		if (vpid < 0):
			vpid = ""
		else:
			vpid = "VPID:" + str(vpid).zfill(4)
		apid = info.getInfo(iServiceInformation.sAudioPID)
		if (apid < 0):
			apid = ""
		else:
			apid = "APID:" + str(apid).zfill(4)
		sid = info.getInfo(iServiceInformation.sSID)
		if (sid < 0):
			sid = ""
		else:
			sid = "SID:" + str(sid).zfill(4)
		pcrpid = info.getInfo(iServiceInformation.sPCRPID)
		if (pcrpid < 0):
			pcrpid = ""
		else:
			pcrpid = "PCR:" + str(pcrpid).zfill(4)
		pmtpid = info.getInfo(iServiceInformation.sPMTPID)
		if (pmtpid < 0):
			pmtpid = ""
		else:
			pmtpid = "PMT:" + str(pmtpid).zfill(4)
		tsid = info.getInfo(iServiceInformation.sTSID)
		if (tsid < 0):
			tsid = ""
		else:
			tsid = "TSID:" + str(tsid).zfill(4)
		onid = info.getInfo(iServiceInformation.sONID)
		if (onid < 0):
			onid = ""
		else:
			onid = "ONID:" + str(onid).zfill(4)
		pidinfo = sp(vpid) + sp(apid) + sp(sid) + sp(pcrpid) + sp(pmtpid) + sp(tsid) + onid
		return pidinfo


	def pidhexstring(self, info):
		vpid = info.getInfo(iServiceInformation.sVideoPID)
		if (vpid < 0):
			vpid = ""
		else:
			vpid = "VPID:" + str(hex(vpid)[2:]).upper().zfill(4)
		apid = info.getInfo(iServiceInformation.sAudioPID)
		if (apid < 0):
			apid = ""
		else:
			apid = "APID:" + str(hex(apid)[2:]).upper().zfill(4)
		sid = info.getInfo(iServiceInformation.sSID)
		if (sid < 0):
			sid = ""
		else:
			sid = "SID:" + str(hex(sid)[2:]).upper().zfill(4)
		pcrpid = info.getInfo(iServiceInformation.sPCRPID)
		if (pcrpid < 0):
			pcrpid = ""
		else:
			pcrpid = "PCR:" + str(hex(pcrpid)[2:]).upper().zfill(4)
		pmtpid = info.getInfo(iServiceInformation.sPMTPID)
		if (pmtpid < 0):
			pmtpid = ""
		else:
			pmtpid = "PMT:" + str(hex(pmtpid)[2:]).upper().zfill(4)
		tsid = info.getInfo(iServiceInformation.sTSID)
		if (tsid < 0):
			tsid = ""
		else:
			tsid = "TSID:" + str(hex(tsid)[2:]).upper().zfill(4)
		onid = info.getInfo(iServiceInformation.sONID)
		if (onid < 0):
			onid = ""
		else:
			onid = "ONID:" + str(hex(onid)[2:]).upper().zfill(4)
		pidhexinfo = sp(vpid) + sp(apid) + sp(sid) + sp(pcrpid) + sp(pmtpid) + sp(tsid) + onid
		return pidhexinfo


	@cached
	def getText(self):
		service = self.source.service
		info = service and service.info()
		if not info:
			return ""
		feinfo = service.frontendInfo()
		if feinfo:
			tp = feinfo.getAll(config.usage.infobar_frontend_source.value == "settings")
			if tp:
				tpinfo = ConvertToHumanReadable(tp)
			if not tp:
				tp = info.getInfoObject(iServiceInformation.sTransponderData)
				tpinfo = ConvertToHumanReadable(tp)


		if self.type == self.FREQINFO:
			refstr = str(self.reference())
			if "%3a/" in refstr or ":/" in refstr:
				return self.streamurl()
			else:
				if "DVB-S" in self.tunertype(tp):
					satf = "%s %s %s %s %s %s" % (self.system(tpinfo), self.modulation(tpinfo), self.frequency(tp), self.polarization(tpinfo), self.symbolrate(tp), self.fecinfo(tpinfo))
					if "is_id" in tpinfo or "pls_code" in tpinfo or "pls_mode" in tpinfo or "t2mi_plp_id" in tp:
						return sp(satf) + self.multistream(tpinfo) + self.t2mi_info(tpinfo)
					else:
						return satf
				elif "DVB-C" in self.tunertype(tp):
					return "%s Mhz %s SR: %s FEC: %s" % (self.frequency(tp), self.modulation(tpinfo), self.symbolrate(tp), self.fecinfo(tpinfo))
				elif self.tunertype(tp) == "DVB-T":
					terf = "%s (%s Mhz)  %s  %s" % (self.channel(tpinfo), self.terrafreq(tp), self.constellation(tpinfo), self.terrafec(tpinfo))
					return terf
				elif self.tunertype(tp) == "DVB-T2":
					return sp(terf) + self.plpid(tpinfo)
				elif "ATSC" in self.tunertype(tp):
					return "%s (Mhz) %s" % (self.terrafreq(tp), self.modulation(tpinfo))
				return ""

		elif self.type == self.ORBITAL:
			refstr = str(self.reference())
			if "%3a/" in refstr or ":/" in refstr:
				return self.streamtype()
			else:
				if "DVB-S" in self.tunertype(tp):
					return "%s (%s)" % (self.satname(tp), self.orbital(tp))
				elif "DVB-C" in self.tunertype(tp) or "DVB-T" in self.tunertype(tp) or "ATSC" in self.tunertype(tp):
					return self.system(tpinfo)
				return ""

		elif self.type == self.VIDEOCODEC:
			return self.videocodec(info)

		elif self.type == self.FPS:
			return self.framerate(info)

		elif self.type == self.VIDEOSIZE:
			return self.videosize(info)

		elif self.type == self.RESCODEC:
			vidsize = self.videosize(info)
			fps = self.framerate(info)
			vidcodec = self.videocodec(info)
			return "%s   %s   %s" % (vidsize, fps, vidcodec)

		elif self.type == self.PIDINFO:
			return self.pidstring(info)

		elif self.type == self.PIDHEXINFO:
			return self.pidhexstring(info)

		elif self.type == self.STREAMURL:
			return str(self.streamurl())

		elif self.type == self.PIDHEXINFO:
			return str(self.streamtype())

		elif self.type == self.HDRINFO:
			return self.hdr(info)

	text = property(getText)


	@cached
	def getBoolean(self):
		service = self.source.service
		info = service and service.info()
		if not info:
			return False
		else:
			xresol = info.getInfo(iServiceInformation.sVideoWidth)
			yresol = info.getInfo(iServiceInformation.sVideoHeight)
			progrs = self.proginfo(info)
			vcodec = self.videocodec(info)
			streamurl = self.streamurl()
			gamma = self.hdr(info)
			if self.type == self.IS1080:
				if (1880 <= xresol <= 2000 ) or (900 <= yresol <= 1090):
					return True
				return False
			elif (self.type == self.IS720):
				if (601 <= yresol <= 740) or (900 <= xresol <= 1300):
					return True
				return False
			elif (self.type == self.IS576):
				if (501 <= yresol <= 600) and (xresol <= 1030):
					return True
				return False
			elif self.type == self.IS1440:
				if (2550 <= xresol <= 2570) or (1430 <= yresol <= 1450):
					return True
				return False
			elif self.type == self.IS2160:
				if (3820 <= xresol <= 4100) or (2150 <= yresol <= 2170):
					return True
				return False
			elif self.type == self.IS480:
				if (380 <= yresol <= 500):
					return True
				return False
			elif self.type == self.IS360:
				if (300 <= yresol <= 379):
					return True
				return False
			elif self.type == self.IS288:
				if (261 <= yresol <= 299):
					return True
				return False
			elif self.type == self.IS240:
				if (181 <= yresol <= 260):
					return True
				return False
			elif self.type == self.IS144:
				if (120 <= yresol <= 180):
					return True
				return False
			elif self.type == self.ISPROGRESSIVE:
				if progrs == "p":
					return True
				return False
			elif self.type == self.ISINTERLACED:
				if progrs == "i":
					return True
				return False
			elif self.type == self.ISSTREAMING:
				if streamurl:
					return True
				return False
			elif self.type == self.HASMPEG2:
				if vcodec == "MPEG2":
					return True
				return False
			elif self.type == self.HASAVC:
				if vcodec == "AVC" or vcodec == "MPEG4":
					return True
				return False
			elif self.type == self.HASH263:
				if vcodec == "H263":
					return True
				return False
			elif self.type == self.HASVC1:
				if "VC1" in vcodec:
					return True
				return False
			elif self.type == self.HASMPEG4VC:
				if vcodec == "MPEG4-VC":
					return True
				return False
			elif self.type == self.HASHEVC:
				if vcodec == "HEVC" or vcodec == "H265":
					return True
				return False
			elif self.type == self.HASMPEG1:
				if vcodec == "MPEG1":
					return True
				return False
			elif self.type == self.HASVP8:
				if vcodec == "VB8" or vcodec == "VP8":
					return True
				return False
			elif self.type == self.HASVP9:
				if vcodec == "VB9" or vcodec == "VP9":
					return True
				return False
			elif self.type == self.HASVP6:
				if vcodec == "VB6" or vcodec == "VP6":
					return True
				return False
			elif self.type == self.HASDIVX:
				if "DIVX" in vcodec:
					return True
				return False
			elif self.type == self.HASXVID:
				if "XVID" in vcodec:
					return True
				return False
			elif self.type == self.HASSPARK:
				if vcodec == "SPARK":
					return True
				return False
			elif self.type == self.HASAVS:
				if "AVS" in vcodec:
					return True
				return False
			elif self.type == self.ISSDR:
				if gamma == "SDR":
					return True
				return False
			elif self.type == self.ISHDR:
				if gamma == "HDR":
					return True
				return False
			elif self.type == self.ISHDR10:
				if gamma == "HDR10":
					return True
				return False
			elif self.type == self.ISHLG:
				if gamma == "HLG":
					return True
				return False

	boolean = property(getBoolean)

	def changed(self, what):
		if what[0] == self.CHANGED_SPECIFIC and what[1] == iPlayableService.evUpdatedInfo or what[0] == self.CHANGED_POLL:
			Converter.changed(self, what)
