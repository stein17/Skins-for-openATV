#	GlamourAccess converter
#	Modded and recoded by MCelliotG for use in Glamour skins or standalone, added Python3 support
#	Based on CaidInfo2 converter coded by bigroma & 2boom
#	If you use this Converter for other skins and rename it, please keep the lines above adding your credits below

from __future__ import absolute_import
from Components.Converter.Converter import Converter
from enigma import iServiceInformation, iPlayableService
from Components.Element import cached
from Components.config import config, ConfigText, ConfigSubsection
from Components.Converter.Poll import Poll
import os
from os import path
info = {}
old_ecm_mtime = None
try:
	config.softcam_actCam = ConfigText()
	config.softcam_actCam2 = ConfigText()
except:
	pass

cainfo = (
	("0100", "01FF", "Seca"),
	("0200", "02FF", "CCETT"),
	("0300", "03FF", "Kabel Deutschland"),
	("0400", "04FF", "Eurodec"),
	("0500", "05FF", "Viaccess"),
	("0600", "06FF", "Irdeto"),
	("0700", "07FF", "DigiChiper"),
	("0800", "08FF", "Matra"),
	("0900", "09FF", "NDS/Videoguard"),
	("0A00", "0AFF", "Nokia"),
	("0B00", "0BFF", "Conax"),
	("0C00", "0CFF", "NTL"),
	("0D00", "0DFF", "Cryptoworks"),
	("0E00", "0EFF", "PowerVu"),
	("0F00", "0FFF", "Sony"),
	("1000", "10FF", "Tandberg"),
	("1100", "11FF", "Thomson"),
	("1200", "12FF", "TV/Com"),
	("1300", "14FF", "HRT"),
	("1500", "15FF", "IBM"),
	("1600", "16FF", "Nera"),
	("1702", "1702", "Betacrypt"),
	("1722", "1722", "Betacrypt"),
	("1762", "1762", "Betacrypt"),
	("1700", "1701", "Verimatrix"),
	("1703", "1721", "Verimatrix"),
	("1723", "1761", "Verimatrix"),
	("1763", "17FF", "Verimatrix"),
	("1800", "18FF", "Nagravision"),
	("1900", "19FF", "Titan"),
	("1E00", "1E07", "Alticast"),
	("1EA0", "1EA0", "Monacrypt"),
	("1EB0", "1EB0", "TeleCast"),
	("1EC0", "1EC2", "Cryptoguard"),
	("1ED0", "1ED1", "Monacrypt"),
	("2000", "20FF", "Telefonica Servicios Audiovisuales"),
	("2100", "21FF", "Stendor"),
	("2200", "22FF", "Codicrypt"),
	("2300", "23FF", "Barco"),
	("2400", "24FF", "StarGuide"),
	("2500", "25FF", "Mentor"),
	("2600", "2601", "Biss"),
	("2602", "26FF", "Biss2"),
	("2700", "270F", "ExSet/PolyChipher"),
	("2710", "2711", "Extended Secure Technologies"),
	("2712", "2712", "Derincrypt"),
	("2713", "2714", "Wuhan"),
	("2715", "2715", "Network Broadcast"),
	("2716", "2716", "Bromteck"),
	("2717", "2718", "LogiWays"),
	("2719", "2719", "S-Curious"),
	("27A0", "27A4", "ByDesign India"),
	("2800", "2809", "LCS LLC"),
	("2810", "2810", "DeltaSat"),
	("4347", "4347", "Crypton"),
	("4348", "4348", "Secure TV"),
	("4700", "47FF", "General Instrument/Motorola"),
	("4825", "4825", "ChinaEPG"),
	("4855", "4856", "Intertrust"),
	("4800", "48FF", "AccessGate/Telemann"),
	("4900", "49FF", "Cryptoworks China"),
	("4A10", "4A1F", "EasyCas"),
	("4A20", "4A2F", "AlphaCrypt"),
	("4A30", "4A3F", "DVN Holdings"),
	("4A40", "4A4F", "ADT"),
	("4A50", "4A5F", "Shenzhen Kingsky"),
	("4A60", "4A6F", "@Sky"),
	("4A70", "4A7F", "DreamCrypt"),
	("4A80", "4A8F", "THALESCrypt"),
	("4A90", "4A9F", "Runcom"),
	("4AA0", "4AAF", "SIDSA"),
	("4AB0", "4ABF", "Beijing Compunicate"),
	("4AC0", "4ACF", "Latens"),
	("4AD0", "4AD1", "XCrypt"),
	("4AD2", "4AD3", "Beijing Digital"),
	("4AD4", "4AD5", "Widevine"),
	("4AD6", "4AD7", "SK Telecom"),
	("4AD8", "4AD9", "Enigma"),
	("4ADA", "4ADA", "Wyplay"),
	("4ADB", "4ADB", "Jinan Taixin"),
	("4ADC", "4ADC", "LogiWays"),
	("4ADD", "4ADD", "ATSC SRM"),
	("4ADE", "4ADE", "CerberCrypt"),
	("4ADF", "4ADF", "Caston"),
	("4AE0", "4AE1", "Cifra"),
	("4AE2", "4AE3", "Microsoft"),
	("4AE4", "4AE4", "Coretrust"),
	("4AE5", "4AE5", "IK SATPROF"),
	("4AE6", "4AE6", "SypherMedia"),
	("4AE7", "4AE7", "Guangzhou Ewider"),
	("4AE8", "4AE8", "FG Digital"),
	("4AE9", "4AE9", "Dreamer-i"),
	("4AEA", "4AEA", "Cryptoguard"),
	("4AEB", "4AEB", "Abel"),
	("4AEC", "4AEC", "FTS DVL SRL"),
	("4AED", "4AED", "Unitend"),
	("4AEE", "4AEE", "Bulcrypt"),
	("4AEF", "4AEF", "NetUP"),
	("4AF0", "4AF0", "ABV"),
	("4AF1", "4AF2", "China DTV"),
	("4AF3", "4AF3", "Baustem"),
	("4AF4", "4AF4", "Marlin"),
	("4AF5", "4AF5", "SecureMedia"),
	("4AF6", "4AF6", "Tongfang"),
	("4AF7", "4AF7", "MSA"),
	("4AF8", "4AF8", "Griffin"),
	("4AF9", "4AFA", "Beijing Topreal"),
	("4AFB", "4AFB", "NST"),
	("4AFC", "4AFC", "PanAccess"),
	("4AFD", "4AFD", "Comteza"),
	("4B00", "4B02", "Tongfang"),
	("4B03", "4B03", "DuoCrypt"),
	("4B04", "4B04", "Great Wall"),
	("4B05", "4B06", "Digicap"),
	("4B07", "4B07", "Wuhan"),
	("4B08", "4B08", "Philips"),
	("4B09", "4B09", "Ambernetas"),
	("4B0A", "4B0B", "Beijing Sumavision"),
	("4B0C", "4B0F", "Sichuan"),
	("4B10", "4B10", "Exterity"),
	("4B11", "4B12", "Merlin/Advanced Digital"),
	("4B13", "4B14", "Microsoft"),
	("4B19", "4B19", "RidSys"),
	("4B20", "4B22", "DeltaSat"),
	("4B23", "4B23", "SkyNLand"),
	("4B24", "4B24", "Prowill"),
	("4B25", "4B25", "SureSoft"),
	("4B26", "4B26", "Unitend"),
	("4B30", "4B31", "VTC"),
	("4B3A", "4B3A", "ipanel"),
	("4B3B", "4B3B", "Jinggangshan"),
	("4B40", "4B41", "ExCaf"),
	("4B42", "4B43", "CI Plus"),
	("4B4A", "4B4A", "Topwell"),
	("4B4B", "4B4D", "ABV"),
	("4B50", "4B53", "Safeview India"),
	("4B54", "4B54", "Telelynx"),
	("4B60", "4B60", "KiwiSat"),
	("4B61", "4B61", "O2 Cz."),
	("4B62", "4B62", "GMA"),
	("4B63", "4B63", "redCrypter"),
	("4B64", "4B64", "Samsung/TV Key"),
	("5347", "5347", "GkWare/StreamGuru"),
	("5448", "5448", "Gospell VisionCrypt"),
	("5501", "5580", "Griffin"),
	("5581", "55FF", "Bulcrypt"),
	("5601", "5604", "Verimatrix"),
	("5605", "5606", "Sichuan"),
	("5607", "5608", "Viewscenes"),
	("5609", "5609", "Power On"),
	("56A0", "56A0", "Laxmi"),
	("56A1", "56A1", "C-Dot"),
	("56B0", "56B0", "Laxmi"),
	("7AC8", "7AC8", "Gospell VisionCrypt"),
	("7BE0", "7BE1", "DreCrypt"),
	("AA00", "AA01", "Best CAS"),
	("A100", "A1FF", "RusCrypt"),
	("0001", "0001", "IPDC SPP"),
	("0002", "0002", "18Crypt"),
	("0004", "0006", "OMA"),
	("0007", "0007", "Open IPTV"),
	("0008", "0008", "Open Mobile Alliance"),
	("0000", "0000", "no or unknown")
)

class BlueACamName(Poll, Converter):
	CAID = 0
	PID = 1
	BETACAS = 2
	IRDCAS = 3
	SECACAS = 4
	VIACAS = 5
	NAGRACAS = 6
	CRWCAS = 7
	NDSCAS = 8
	CONAXCAS = 9
	DRCCAS = 10
	BISSCAS = 11
	BULCAS = 12
	VMXCAS = 13
	PWVCAS = 14
	TBGCAS = 15
	TGFCAS = 16
	PANCAS = 17
	EXSCAS = 18
	CGDCAS = 19
	VCRCAS = 20
	BETAECM = 21
	IRDECM = 22
	SECAECM = 23
	VIAECM = 24
	NAGRAECM = 25
	CRWECM = 26
	NDSECM = 27
	CONAXECM = 28
	DRCECM = 29
	BISSECM = 30
	BULECM = 31
	VMXECM = 32
	PWVECM = 33
	TBGECM = 34
	TGFECM = 35
	PANECM = 36
	EXSECM = 37
	CGDECM = 38
	VCRECM = 39
	RUSCAS = 40
	CODICAS = 41
	AGTCAS = 42
	SAMCAS = 43
	CAIDINFO = 44
	PROV = 45
	NET = 46
	EMU = 47
	CRD = 48
	CRDTXT = 49
	FTA = 50
	CACHE = 51
	CRYPTINFO = 52
	CAMNAME = 53
	ADDRESS = 54
	ECMTIME = 55
	FORMAT = 56
	ECMINFO = 57
	SHORTINFO = 58
	CASINFO = 59
	ISCRYPTED = 60
	timespan = 1000

	def __init__(self, type):
		Poll.__init__(self)
		Converter.__init__(self, type)
		if type == "CaID":
			self.type = self.CAID
		elif type == "Pid":
			self.type = self.PID
		elif type == "BetaCaS":
			self.type = self.BETACAS
		elif type == "IrdCaS":
			self.type = self.IRDCAS
		elif type == "SecaCaS":
			self.type = self.SECACAS
		elif type == "ViaCaS":
			self.type = self.VIACAS
		elif type == "NagraCaS":
			self.type = self.NAGRACAS
		elif type == "CrwCaS":
			self.type = self.CRWCAS
		elif type == "NdsCaS":
			self.type = self.NDSCAS
		elif type == "ConaxCaS":
			self.type = self.CONAXCAS
		elif type == "DrcCaS":
			self.type = self.DRCCAS
		elif type == "BissCaS":
			self.type = self.BISSCAS
		elif type == "BulCaS":
			self.type = self.BULCAS
		elif type == "VmxCaS":
			self.type = self.VMXCAS
		elif type == "PwvCaS":
			self.type = self.PWVCAS
		elif type == "TbgCaS":
			self.type = self.TBGCAS
		elif type == "TgfCaS":
			self.type = self.TGFCAS
		elif type == "PanCaS":
			self.type = self.PANCAS
		elif type == "ExsCaS":
			self.type = self.EXSCAS
		elif type == "RusCaS":
			self.type = self.RUSCAS
		elif type == "BetaEcm":
			self.type = self.BETAECM
		elif type == "IrdEcm":
			self.type = self.IRDECM
		elif type == "SecaEcm":
			self.type = self.SECAECM
		elif type == "ViaEcm":
			self.type = self.VIAECM
		elif type == "NagraEcm":
			self.type = self.NAGRAECM
		elif type == "CrwEcm":
			self.type = self.CRWECM
		elif type == "NdsEcm":
			self.type = self.NDSECM
		elif type == "ConaxEcm":
			self.type = self.CONAXECM
		elif type == "DrcEcm":
			self.type = self.DRCECM
		elif type == "BissEcm":
			self.type = self.BISSECM
		elif type == "BulEcm":
			self.type = self.BULECM
		elif type == "VmxEcm":
			self.type = self.VMXECM
		elif type == "PwvEcm":
			self.type = self.PWVECM
		elif type == "TbgEcm":
			self.type = self.TBGECM
		elif type == "TgfEcm":
			self.type = self.TGFECM
		elif type == "PanEcm":
			self.type = self.PANECM
		elif type == "ExsEcm":
			self.type = self.EXSECM
		elif type == "CgdEcm":
			self.type = self.CGDECM
		elif type == "VcrEcm":
			self.type = self.VCRECM
		elif type == "CodiCaS":
			self.type = self.CODICAS
		elif type == "CgdCaS":
			self.type = self.CGDCAS
		elif type == "VcrCaS":
			self.type = self.VCRCAS
		elif type == "AgtCaS":
			self.type = self.AGTCAS
		elif type == "SamCaS":
			self.type = self.SAMCAS
		elif type == "CaidInfo":
			self.type = self.CAIDINFO
		elif type == "ProvID":
			self.type = self.PROV
		elif type == "Net":
			self.type = self.NET
		elif type == "Emu":
			self.type = self.EMU
		elif type == "Crd":
			self.type = self.CRD
		elif type == "CrdTxt":
			self.type = self.CRDTXT
		elif type == "Fta":
			self.type = self.FTA
		elif type == "Cache":
			self.type = self.CACHE
		elif type == "CryptInfo":
			self.type = self.CRYPTINFO
		elif type == "CamName":
			self.type = self.CAMNAME
		elif type == "Address":
			self.type = self.ADDRESS
		elif type == "EcmTime":
			self.type = self.ECMTIME
		elif type == "IsCrypted":
			self.type = self.ISCRYPTED
		elif type == "ShortInfo":
			self.type = self.SHORTINFO
		elif type == "CasInfo":
			self.type = self.CASINFO
		elif type == "EcmInfo" or type == "Default" or type == "" or type == None or type == "%":
			self.type = self.ECMINFO
		else:
			self.type = self.FORMAT
			self.sfmt = type[:]



	@cached
	def getBoolean(self):
		service = self.source.service
		info = service and service.info()
		ecm_info = self.ecmfile()
		protocol = str(ecm_info.get("protocol", ""))
		self.poll_interval = self.timespan
		self.poll_enabled = True
		if not info:
			return False
		caids = self.CaidList().strip(", ").split()

		if self.type == self.FTA:
			if not caids and not ecm_info:
				return True
			elif ecm_info:
				if "fta" in protocol:
					return True
			return False

		if self.type == self.ISCRYPTED:
			if caids:
				return True
			return False

		if caids or ecm_info:
			if self.type == self.BETACAS:
				for caid in caids:
					if caid == "1702" or caid == "1722" or caid == "1762":
						return True
				return False
			if self.type == self.IRDCAS:
				for caid in caids:
					if caid >= "0600" and caid <= "06FF":
						return True
				return False
			if self.type == self.SECACAS:
				for caid in caids:
					if caid >= "0100" and caid <= "01FF":
						return True
				return False
			if self.type == self.VIACAS:
				for caid in caids:
					if caid >= "0500" and caid <= "05FF":
						return True
				return False
			if self.type == self.NAGRACAS:
				for caid in caids:
					if caid >= "1800" and caid <= "18FF":
						return True
				return False
			if self.type == self.CRWCAS:
				for caid in caids:
					if caid >= "0D00" and caid <= "0DFF":
						return True
				return False
			if self.type == self.NDSCAS:
				for caid in caids:
					if caid >= "0900" and caid <= "09FF":
						return True
				return False
			if self.type == self.CONAXCAS:
				for caid in caids:
					if caid >= "0B00" and caid <= "0BFF":
						return True
				return False
			if self.type == self.DRCCAS:
				for caid in caids:
					if caid >= "4A00" and caid <= "4AE9" or caid >= "5000" and caid <= "50FF" or caid >= "7BE0" and caid <= "7BE1" or caid >= "0700" and caid <= "07FF" or caid >= "4700" and caid <= "47FF":
						return True
				return False
			if self.type == self.BISSCAS:
				for caid in caids:
					if caid >= "2600" and caid <= "26FF":
						return True
				return False
			if self.type == self.BULCAS:
				for caid in caids:
					if caid == "4AEE" or caid == "4AF8" or caid >= "5581" and caid <= "55FF":
						return True
				return False
			if self.type == self.VMXCAS:
				for caid in caids:
					if caid >= "5600" and caid <= "5604" or caid >= "1700" and caid <= "1701" or caid >= "1703" and caid <= "1721" or caid >= "1723" and caid <= "1761" or caid >= "1763" and caid <= "17FF":
						return True
				return False
			if self.type == self.PWVCAS:
				for caid in caids:
					if caid >= "0E00" and caid <= "0EFF":
						return True
				return False
			if self.type == self.TBGCAS:
				for caid in caids:
					if caid >= "1000" and caid <= "10FF":
						return True
				return False
			if self.type == self.TGFCAS:
				for caid in caids:
					if caid >= "4B00" and caid <= "4B09" or caid == "4AF6":
						return True
				return False
			if self.type == self.PANCAS:
				for caid in caids:
					if caid == "4AFC":
						return True
				return False
			if self.type == self.EXSCAS:
				for caid in caids:
					if caid >= "2700" and caid <= "27FF":
						return True
				return False
			if self.type == self.RUSCAS:
				for caid in caids:
					if caid >= "A100" and caid <= "A1FF":
						return True
				return False
			if self.type == self.CODICAS:
				for caid in caids:
					if caid >= "2200" and caid <= "22FF":
						return True
				return False
			if self.type == self.CGDCAS:
				for caid in caids:
					if caid == "4AEA" or caid >= "1EC0" and caid <= "1ECF":
						return True
				return False
			if self.type == self.VCRCAS:
				for caid in caids:
					if caid == "5448" or caid == "7AC8":
						return True
				return False
			if self.type == self.AGTCAS:
				for caid in caids:
					if caid >= "4800" and caid <= "48FF":
						return True
				return False
			if self.type == self.SAMCAS:
				for caid in caids:
					if caid == "4B64":
						return True
				return False

			if ecm_info:
				caid = ("%0.4X" % int(ecm_info.get("caid", ""), 16))[:4]
				if self.type == self.BETAECM:
					if caid == "1702" or caid == "1722" or caid == "1762":
						return True
					return False
				if self.type == self.IRDECM:
					if caid >= "0600" and caid <= "06FF":
						return True
					return False
				if self.type == self.SECAECM:
					if caid >= "0100" and caid <= "01FF":
						return True
					return False
				if self.type == self.VIAECM:
					if caid >= "0500" and caid <= "05FF":
						return True
					return False
				if self.type == self.NAGRAECM:
					if caid >= "1800" and caid <= "18FF":
						return True
					return False
				if self.type == self.CRWECM:
					if caid >= "0D00" and caid <= "0DFF" or caid >= "4900" and caid <= "49FF":
						return True
					return False
				if self.type == self.NDSECM:
					if caid >= "0900" and caid <= "09FF":
						return True
					return False
				if self.type == self.CONAXECM:
					if caid >= "0B00" and caid <= "0BFF":
						return True
					return False
				if self.type == self.DRCECM:
					if caid >= "4A00" and caid <= "4AE9" or caid >= "5000" and caid <= "50FF" or caid >= "7BE0" and caid <= "7BE1" or caid >= "0700" and caid <= "07FF" or caid >= "4700" and caid <= "47FF":
						return True
					return False
				if self.type == self.BISSECM:
					if caid >= "2600" and caid <= "26FF":
						return True
					return False
				if self.type == self.BULECM:
					if caid == "4AEE" or caid == "4AF8" or caid >= "5581" and caid <= "55FF":
						return True
					return False
				if self.type == self.VMXECM:
					if caid >= "5600" and caid <= "5604" or caid >= "1700" and caid <= "1701" or caid >= "1703" and caid <= "1721" or caid >= "1723" and caid <= "1761"  or caid >= "1763" and caid <= "17FF":
						return True
					return False
				if self.type == self.PWVECM:
					if caid >= "0E00" and caid <= "0EFF":
						return True
					return False
				if self.type == self.TBGECM:
					if caid >= "1000" and caid <= "10FF":
						return True
					return False
				if self.type == self.TGFECM:
					if caid >= "4B00" and caid <= "4B09" or caid == "4AF6":
						return True
					return False
				if self.type == self.PANECM:
					if caid == "4AFC":
						return True
					return False
				if self.type == self.EXSECM:
					if caid >= "2700" and caid <= "27FF":
						return True
					return False
				if self.type == self.CGDECM:
					if caid == "4AEA" or caid >= "1EC0" and caid <= "1ECF":
						return True
					return False
				if self.type == self.VCRECM:
					if caid == "5448" or caid == "7AC8":
						return True
					return False

				reader = str(ecm_info.get("reader", ""))
				protocol = str(ecm_info.get("protocol", ""))
				frm = str(ecm_info.get("from", ""))
				using = str(ecm_info.get("using", ""))
				source = str(ecm_info.get("source", ""))

				if self.type == self.CRD:
					if int(config.usage.show_cryptoinfo.value) > 0:
						if source == "sci":
							return True
						if source != "cache" and source != "net" and source.find("emu") == -1:
							return True
					return False
				if self.type == self.CACHE:
					if int(config.usage.show_cryptoinfo.value) > 0:
						if source == "cache" or reader == "Cache" or "cache" in frm:
							return True
					return False
				if self.type == self.EMU:
					if int(config.usage.show_cryptoinfo.value) > 0:
						return using == "emu" or source == "emu" or source == "card" or reader == "emu" or source.find("card") > -1 or source.find("emu") > -1 or source.find("biss") > -1 or source.find("tb") > -1 or reader.find("constant_cw") > -1 or protocol.find("constcw") > -1 or protocol.find("static") > -1
				if self.type == self.NET:
					if int(config.usage.show_cryptoinfo.value) > 0:
						if source == "net" and not "unsupported" in protocol and not "cache" in frm and not "static" in protocol and not "fta" in protocol:
							return True
					return False
		return False

	boolean = property(getBoolean)


	@cached
	def getText(self):
		ecminfo = ""
		server = ""
		caidlist = self.CaidList()
		caidtxt = "hidden or custom"
		caidname = self.CaidName()
		ecm_info = self.ecmfile()
		ecmpath = self.ecmpath()
		self.poll_interval = self.timespan
		self.poll_enabled = True
		service = self.source.service
		if service:
			info = service and service.info()

			if self.type == self.CRYPTINFO:
				if os.path.exists(ecmpath):
					try:
						caid = "%0.4X" % int(ecm_info.get("caid", ""), 16)
						return "%s" % caidname
					except:
						return "Unknown CA Info"
				else:
					return "CA Info not available"

			if info:
				caids = list(set(info.getInfoObject(iServiceInformation.sCAIDs)))

				if self.type == self.CAMNAME:
					return self.CamName()

				if self.type == self.CAIDINFO:
					return self.CaidInfo()

				if caids or ecm_info:
					if len(caids) > 0:
						caidtxt = self.CaidTxtList()
						for cas in caids:
							cas = self.int2hex(cas).upper().zfill(4)

					if ecm_info:
						caid = "%0.4X" % int(ecm_info.get("caid", ""), 16)

						if self.type == self.CAID:
							return caid

						try:
							pid = "%0.4X" % int(ecm_info.get("pid", ""), 16)
						except:
							pid = ""

						if self.type == self.PID:
							return pid

						try:
							prov = "%0.6X" % int(ecm_info.get("prov", ""), 16)
						except:
							prov = ecm_info.get("prov", "")

						if self.type == self.PROV:
							return prov

						if ecm_info.get("ecm time", "").find("msec") > -1:
							ecm_time = (ecm_info.get("ecm time", "")).replace("msec", "ms")
						else:
							ecm_time = "%s ms" % ecm_info.get("ecm time", "").replace(".", "").lstrip("0")

						if self.type == self.ECMTIME:
							return ecm_time

						csi = "Service with %s encryption" % (caidtxt)
						casi = "Service with %s encryption (%s)" % (caidtxt, caidlist)
						protocol = ecm_info.get("protocol", "")
						port = ecm_info.get("port", "")
						source = ecm_info.get("source", "")
						server = ecm_info.get("server", "")
						hops = hop = ecm_info.get("hops", "")
						if hops:
							if hops > "0":
								hops = " Hops: %s" % hops
								hop = "%s" % hop
							else:
								hops = hop = ""
						system = ecm_info.get("system", "")
						frm = ecm_info.get("from", "")
						if len(frm) > 36:
							frm = "%s..." % frm[:35]
						provider = ecm_info.get("provider", "")
						if provider:
							provider = "Prov: " + provider
						reader = ecm_info.get("reader", "")
						if len(reader) > 36:
							reader = "%s..." % reader[:35]

						if self.type == self.CRDTXT:
							info_card = "False"
							if source == "sci":
								info_card = "True"
							if source != "cache" and source != "net" and source.find("emu") == -1:
								info_card = "True"
							return info_card

						if self.type == self.ADDRESS:
							return server

						if self.type == self.FORMAT:
							ecminfo = ""
							params = self.sfmt.split(" ")
							for param in params:
								if param != "":
									if param[0] != "%":
										ecminfo += param
									elif param == "%S":
										ecminfo += server
									elif param == "%H":
										ecminfo += hops
									elif param == "%SY":
										ecminfo += system
									elif param == "%PV":
										ecminfo += provider
									elif param == "%SP":
										ecminfo += port
									elif param == "%PR":
										ecminfo += protocol
									elif param == "%C":
										ecminfo += caid
									elif param == "%P":
										ecminfo += pid
									elif param == "%p":
										ecminfo += prov
									elif param == "%O":
										ecminfo += source
									elif param == "%R":
										ecminfo += reader
									elif param == "%FR":
										ecminfo += frm
									elif param == "%T":
										ecminfo += ecm_time
									elif param == "%t":
										ecminfo += "\t"
									elif param == "%n":
										ecminfo += "\n"
									elif param[1:].isdigit():
										ecminfo = ecminfo.ljust(len(ecminfo) + int(param[1:]))
									if len(ecminfo) > 0:
										if ecminfo[-1] != "\t" and ecminfo[-1] != "\n":
											ecminfo += " "
							return ecminfo[:-1]

						if self.type == self.ECMINFO:
							if "fta" in protocol:
								ecminfo = "FTA service"
							elif int(config.usage.show_cryptoinfo.value) > 0:
								if source == "emu":
									ecminfo = "CA: %s:%s  PID:%s  Source: %s@%s  Ecm Time: %s" % (caid, prov, pid, source, frm, ecm_time)
								elif reader != "" and source == "net" and port != "":
									ecminfo = "CA: %s:%s  PID:%s  Reader: %s@%s  Prtc:%s (%s)  Source: %s:%s %s  Ecm Time: %s  %s" % (caid, prov, pid, reader, frm, protocol, source, server, port, hops, ecm_time, provider)
								elif reader != "" and source == "net" and not "fta" in protocol:
									ecminfo = "CA: %s:%s  PID:%s  Reader: %s@%s  Ptrc:%s (%s)  Source: %s %s  Ecm Time: %s  %s" % (caid, prov, pid, reader, frm, protocol, source, server, hops, ecm_time, provider)
								elif reader != "" and source != "net":
									ecminfo = "CA: %s:%s  PID:%s  Reader: %s@%s  Prtc:%s (local) - %s %s  Ecm Time: %s  %s" % (caid, prov, pid, reader, frm, protocol, source, hops, ecm_time, provider)
								elif server == "" and port == "" and protocol != "":
									ecminfo = "CA: %s:%s  PID:%s  Prtc: %s (%s) %s Ecm Time: %s" % (caid, prov, pid, protocol, source, hops, ecm_time)
								elif server == "" and port == "" and protocol == "":
									ecminfo = "CA: %s:%s  PID:%s  Source: %s  Ecm Time: %s" % (caid, prov, pid, source, ecm_time)
								else:
									try:
										ecminfo = "CA: %s:%s  PID:%s  Addr:%s:%s  Prtc: %s (%s) %s  Ecm Time: %s  %s" % (caid, prov, pid, server, port, protocol, source, hops, ecm_time, provider)
									except:
										pass
							else:
								ecminfo = casi

						if self.type == self.SHORTINFO:
							if "fta" in protocol:
								ecminfo = "FTA service"
							elif int(config.usage.show_cryptoinfo.value) > 0:
								if source == "emu":
									ecminfo = "%s:%s - %s - %s" % (caid, prov, source, caidname)
								elif server == "" and port == "":
									ecminfo = "%s:%s - %s - %s" % (caid, prov, source, ecm_time)
								else:
									try:
										if reader != "":
											if hop != "":
												ecminfo = "%s:%s - %s (%s) - %s" % (caid, prov, frm, hop, ecm_time)
											else:
												ecminfo = "%s:%s - %s - %s" % (caid, prov, frm, ecm_time)
										else:
											if hop != "":
												ecminfo = "%s:%s - %s (%s) - %s" % (caid, prov, server, hop, ecm_time)
											else:
												ecminfo = "%s:%s - %s - %s" % (caid, prov, server, ecm_time)
									except:
										pass
							else:
								ecminfo = csi

						if self.type == self.CASINFO:
							if "fta" in protocol:
								ecminfo = "FTA service"
							elif int(config.usage.show_cryptoinfo.value) > 0:
								if source == "emu" or server == "" and port == "":
									ecminfo = "%s [%s:%s - %s - %s]" % (csi, caid, prov, source, ecm_time)
								else:
									try:
										if reader != "":
											if hop != "":
												ecminfo = "%s [%s:%s - %s@%s - %s]" % (csi, caid, prov, reader, hop, ecm_time)
											else:
												ecminfo = "%s [%s:%s - %s - %s]" % (csi, caid, prov, reader, ecm_time)
										else:
											if hop != "":
												ecminfo = "%s [%s:%s - %s@%s - %s]" % (csi, caid, prov, server, hop, ecm_time)
											else:
												ecminfo = "%s [%s:%s - %s - %s]" % (csi, caid, prov, server, ecm_time)
									except:
										pass
							else:
								ecminfo = csi

					elif self.type == self.ECMINFO or self.type == self.FORMAT and self.sfmt.count("%") > 3:
						ecminfo = "Service with %s encryption (%s)" % (caidtxt, caidlist)
					elif self.type == self.SHORTINFO or self.type == self.CASINFO:
						ecminfo = "Service with %s encryption" % caidtxt
				elif self.type == self.ECMINFO or self.type == self.SHORTINFO or self.type == self.CASINFO or self.type == self.FORMAT and self.sfmt.count("%") > 3:
					ecminfo = "FTA service"
		return ecminfo

	text = property(getText)


	def CamName(self):
		cam1 = ""
		cam2 = ""
		serlist = None
		camdlist = None
		camdname = []
		sername = []
#OpenPLI/SatDreamGr
		if os.path.exists("/etc/init.d/softcam") and not os.path.exists("/etc/image-version") or os.path.exists("/etc/init.d/cardserver") and not os.path.exists("/etc/image-version"):
			try:
				for line in open("/etc/init.d/softcam"):
					if line.startswith("CAMNAME="):
						cam1 = "%s" % line.split('"')[1]
					elif line.find("echo") > -1:
						camdname.append(line)
				cam2 = "%s" % camdname[1].split('"')[1]
				if not cam1:
					camdlist = cam2
				else:
					camdlist = cam1
				return camdlist
			except:
				pass
			try:
				for line in open("/etc/init.d/cardserver"):
					if line.find("echo") > -1:
						sername.append(line)
				serlist = "%s" % sername[1].split('"')[1]
			except:
				pass
			if serlist is None:
				serlist = ""
			elif camdlist is None:
				camdlist = ""
			elif serlist is None and camdlist is None:
				serlist = ""
				camdlist = ""
			return "%s %s" % (serlist, camdlist)
#OE-A
		if os.path.exists("/etc/image-version") and not os.path.exists("/etc/.emustart"):
			for line in open("/etc/image-version"):
				if "=openATV" in line:
					try:
						if config.softcam.actCam.value:
							cam1 = config.softcam.actCam.value
							if " CAM 1" in cam1 or "no cam" in cam1:
								cam1 = "No CAM active"
						if config.softcam.actCam2.value:
							cam2 = config.softcam.actCam2.value
							if " CAM 2" in cam2 or "no cam" in cam2 or " CAM" in cam2:
								cam2 = ""
							else:
								cam2 = "+" + cam2
					except:
						pass
					try:
						if os.path.exists("/tmp/.oscam/oscam.version"):
							for line in open("/tmp/.oscam/oscam.version"):
								if line.startswith("Version:"):
									cam1 = "%s" % line.split(':')[1].replace(" ", "")
						elif os.path.exists("/tmp/.ncam/ncam.version"):
							for line in open("/tmp/.ncam/ncam.version"):
								if line.startswith("Version:"):
									cam1 = "%s" % line.split(':')[1].replace(" ", "")
						else:
							for line in open("/etc/init.d/softcam"):
								if "Short-Description" in line:
									cam1 = "%s" % line.split(':')[1].replace(" ", "")
								if line.startswith("CAMNAME="):
									cam1 = "%s" % line.split('"')[1]
								elif line.find("echo") > -1:
									camdname.append(line)
							cam2 = "%s" % camdname[1].split('"')[1]
						if not cam1:
							return cam2
						else:
							return cam1
					except:
						pass
					try:
						for line in open("/etc/init.d/cardserver"):
							if line.find("echo") > -1:
								sername.append(line)
						cam2 = " %s" % sername[1].split('"')[1]
						if not cam2 or cam2 == "None":
							cam2 = ""
					except:
						pass
				elif "=opendroid" in line:
					try:
						cam1 = config.softcam_actCam.value
						if cam1:
							if " CAM 1" in cam1 or "no cam" in cam1:
								cam1 = "No CAM active"
						cam2 = config.softcam_actCam2.value
						if cam2:
							if " CAM 2" in cam2 or "no cam" in cam2 or " CAM" in cam2:
								cam2 = ""
							else:
								cam2 = "/" + cam2
					except:
						pass
			return "%s%s" % (cam1, cam2)
#BLACKHOLE
		if os.path.exists("/etc/CurrentDelCamName"):
			try:
				camdlist = open("/etc/CurrentDelCamName", "r")
			except:
				return None
		if os.path.exists("/etc/CurrentBhCamName"):
			try:
				camdlist = open("/etc/CurrentBhCamName", "r")
			except:
				return None
# DE-OpenBlackHole
		if os.path.exists("/etc/BhFpConf"):
			try:
				camdlist = open("/etc/BhCamConf", "r")
			except:
				return None
#HDMU
		if os.path.exists("/etc/.emustart") and os.path.exists("/etc/image-version"):
			try:
				for line in open("/etc/.emustart"):
					return line.split()[0].split("/")[-1]
			except:
				return None
# Domica
		if os.path.exists("/etc/active_emu.list"):
			try:
				camdlist = open("/etc/active_emu.list", "r")
			except:
				return None
# Egami 
		if os.path.exists("/tmp/egami.inf", "r"):
			try:
				lines = open("/tmp/egami.inf", "r").readlines()
				for line in lines:
					item = line.split(":", 1)
					if item[0] == "Current emulator":
						return item[1].strip()
			except:
				return None
# OoZooN
		if os.path.exists("/tmp/cam.info"):
			try:
				camdlist = open("/tmp/cam.info", "r")
			except:
				return None
# Dream Elite
		if os.path.exists("/usr/bin/emuactive"):
			try:
				camdlist = open("/usr/bin/emuactive", "r")
			except:
				return None
# Merlin2
		if os.path.exists("/etc/clist.list"):
			try:
				camdlist = open("/etc/clist.list", "r")
			except:
				return None
# TS-Panel
		if os.path.exists("/etc/startcam.sh"):
			try:
				for line in open("/etc/startcam.sh"):
					if line.find("script") > -1:
						return "%s" % line.split("/")[-1].split()[0][:-3]
			except:
				camdlist = None
#  GlassSysUtil
		if os.path.exists("/tmp/ucm_cam.info"):
			try:
				return open("/tmp/ucm_cam.info").read()
			except:
				return None
# Others
		if serlist != None:
			try:
				cardserver = ""
				for current in serlist.readlines():
					cardserver = current
				serlist.close()
			except:
				pass
		else:
			cardserver = "N/A"
		if camdlist != None:
			try:
				emu = ""
				for current in camdlist.readlines():
					emu = current
				camdlist.close()
			except:
				pass
		else:
			emu = "N/A"
		return "%s %s" % (cardserver.split("\n")[0], emu.split("\n")[0])



	def int2hex(self, int):
		return "%x" % int


	def Caids(self):
		caids = ""
		service = self.source.service
		if service:
			info = service and service.info()
			if info:
				caids = list(set(info.getInfoObject(iServiceInformation.sCAIDs)))
		return sorted(caids)


	def CaidList(self):
		caids = self.Caids()
		caidlist = ""
		if caids:
			for caid in caids:
				caid = self.int2hex(caid).upper().zfill(4)
				if len(caids) > 1:
					caidlist = ", ".join(("{:04x}".format(x) for x in caids)).upper()
				else:
					caidlist += caid
		return caidlist


	def CaidName(self):
		ecm_info = self.ecmfile()
		caidname = ""
		if ecm_info:
			caidr = ("%0.4X" % int(ecm_info.get("caid", ""), 16))[:4]
			for ce in cainfo:
				try:
					if ce[0] <= caidr <= ce[1] or caidr.startswith(ce[0]):
						caidname = ce[2]
				except:
					pass
		return caidname


	def CaidNames(self):
		caidnames = ""
		caids = self.CaidList().strip(",").split()
		if caids:
			for caid in caids:
				for ce in cainfo:
					if ce[0] <= caid <= ce[1] or caid.startswith(ce[0]):
						caid = ce[2]
				if len(caids) > 1:
					caidnames += ", " + caid
				else:
					caidnames = caid
		return caidnames.lstrip(", ")


	def CaidTxtList(self):
		caidtxt = ""
		caidnames = self.CaidNames()
		if caidnames:
			for caidname in caidnames:
				caidtxt = caidnames.strip(", ").split(", ")
				calist = []
				for ca in caidtxt:
					if ca not in calist:
						calist.append(ca)
						calist = list(calist)
						if len(calist) > 1:
							caidtxt = ", ".join(calist[:-1]) + " & " + calist[-1]
						else:
							caidtxt = calist[0]
		return caidtxt


	def CaidInfo(self):
		caids = self.CaidList()
		caidnames = self.CaidNames()
		caidlist = ""
		if caids and caidnames:
			caidlist = "%s (%s)" % (caids, caidnames)
			if config.osd.language.value == "el_GR":
				caidlist = "Συστήματα κωδικοποίησης: " + caidlist
			else:
				caidlist = "Coding systems: " + caidlist
			return caidlist
		if not caids:
			if config.osd.language.value == "el_GR":
				return "Χωρίς κωδικοποίηση ή αναγνωριστικό"
			else:
				return "Free to air or no descriptor"


	def ecmpath(self):
		ecmpath = None
		if os.path.exists("/tmp/ecm7.info"):
			ecmpath = "/tmp/ecm7.info"
		elif os.path.exists("/tmp/ecm6.info") and not os.path.exists("tmp/ecm7.info"):
			ecmpath = "/tmp/ecm6.info"
		elif os.path.exists("/tmp/ecm5.info") and not os.path.exists("tmp/ecm6.info"):
			ecmpath = "/tmp/ecm5.info"
		elif os.path.exists("/tmp/ecm4.info") and not os.path.exists("tmp/ecm5.info"):
			ecmpath = "/tmp/ecm4.info"
		elif os.path.exists("/tmp/ecm3.info") and not os.path.exists("tmp/ecm4.info"):
			ecmpath = "/tmp/ecm3.info"
		elif os.path.exists("/tmp/ecm2.info") and not os.path.exists("tmp/ecm3.info"):
			ecmpath = "/tmp/ecm2.info"
		elif os.path.exists("/tmp/ecm1.info") and not os.path.exists("tmp/ecm2.info"):
			ecmpath = "/tmp/ecm1.info"
		elif os.path.exists("/tmp/ecm0.info") and os.path.exists("/tmp/ecm.info"):
			ecmpath = "/tmp/ecm.info"
		elif os.path.exists("/tmp/ecm0.info") and not os.path.exists("/tmp/ecm.info"):
			ecmpath = None
		else:
			try:
				ecmpath = "/tmp/ecm.info"
			except:
				pass
		return ecmpath


	def ecmfile(self):
		global info
		global old_ecm_mtime
		ecm = None
		ecmpath = self.ecmpath()
		service = self.source.service
		if service:
			try:
				ecm_mtime = os.stat(ecmpath).st_mtime
				if not os.stat(ecmpath).st_size > 0:
					info = {}
				if ecm_mtime == old_ecm_mtime:
					return info
				old_ecm_mtime = ecm_mtime
				ecmf = open(ecmpath, "r")
				ecm = ecmf.readlines()
			except:
				old_ecm_mtime = None
				info = {}
				return info
			if ecm:
				for line in ecm:
					x = line.lower().find("msec")
					if x != -1:
						info["ecm time"] = line[0:x + 4]
					else:
						item = line.split(":", 1)
						if len(item) > 1:
							if item[0] == "Provider":
								item[0] = "prov"
								item[1] = item[1].strip()[2:]
							elif item[0] == "ECM PID":
								item[0] = "pid"
							elif item[0] == "response time":
								info["source"] = "net"
								it_tmp = item[1].strip().split(" ")
								info["ecm time"] = "%s msec" % it_tmp[0]
								y = it_tmp[-1].find("[")
								if y != -1:
									info["server"] = it_tmp[-1][:y]
									info["protocol"] = it_tmp[-1][y + 1:-1]
								y = it_tmp[-1].find("(")
								if y != -1:
									info["server"] = it_tmp[-1].split("(")[-1].split(":")[0]
									info["port"] = it_tmp[-1].split("(")[-1].split(":")[-1].rstrip(")")
								elif y == -1:
									item[0] = "source"
									item[1] = "sci"
								if it_tmp[-1].find("emu") > -1 or it_tmp[-1].find("card") > -1 or it_tmp[-1].find("biss") > -1 or it_tmp[-1].find("tb") > -1:
									item[0] = "source"
									item[1] = "emu"
							elif item[0] == "hops":
								item[1] = item[1].strip("\n")
							elif item[0] == "from":
								item[1] = item[1].strip("\n")
							elif item[0] == "system":
								item[1] = item[1].strip("\n")
							elif item[0] == "provider":
								item[1] = item[1].strip("\n")
							elif item[0][:2] == "cw" or item[0] == "ChID" or item[0] == "Service":
								pass
							elif item[0] == "source":
								if item[1].strip()[:3] == "net":
									it_tmp = item[1].strip().split(" ")
									info["protocol"] = it_tmp[1][1:]
									if ":" in it_tmp[-1]:
										info["server"] = it_tmp[-1].split(":", 1)[0]
										info["port"] = it_tmp[-1].split(":", 1)[1][:-1]
									elif ":" not in it_tmp[-1]:
										try:
											info["server"] = it_tmp[3].split(":", 1)[0]
											info["port"] = it_tmp[3].split(":", 1)[1][:-1]
										except:
											pass
									else:
										info["server"] == ""
										info["port"] == ""
									item[1] = "net"
							elif item[0] == "prov":
								y = item[1].find(",")
								if y != -1:
									item[1] = item[1][:y]
							elif item[0] == "reader":
								if item[1].strip() == "emu":
									item[0] = "source"
							elif item[0] == "protocol":
								if item[1].strip() == "emu" or item[1].strip() == "constcw":
									item[1] = "emu"
									item[0] = "source"
								elif item[1].strip() == "internal":
									item[1] = "sci"
									item[0] = "source"
								else:
									info["source"] = "net"
									item[0] = "server"
							elif item[0] == "provid":
								item[0] = "prov"
							elif item[0] == "using":
								if item[1].strip() == "emu" or item[1].strip() == "sci":
									item[0] = "source"
								else:
									info["source"] = "net"
									item[0] = "protocol"
							elif item[0] == "address":
								tt = item[1].find(":")
								if tt != -1:
									info["server"] = item[1][:tt].strip()
									item[0] = "port"
									item[1] = item[1][tt + 1:]
							info[item[0].strip().lower()] = item[1].strip()
						else:
							if "caid" not in info:
								x = line.lower().find("caid")
								if x != -1:
									y = line.find(",")
									if y != -1:
										info["caid"] = line[x + 5:y]
							if "pid" not in info:
								x = line.lower().find("pid")
								if x != -1:
									y = line.find(" =")
									z = line.find(" *")
									if y != -1:
										info["pid"] = line[x + 4:y]
									elif z != -1:
										info["pid"] = line[x + 4:z]
				ecmf.close()
		return info


	def changed(self, what):
		Converter.changed(self, (self.CHANGED_POLL,))