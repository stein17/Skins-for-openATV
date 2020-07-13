#  GlamourExtra Converter
#  Modded and recoded by MCelliotG for use in Glamour skins or standalone
#  HDDtemp new detection added by betacentauri, many thanks!!!
#  If you use this Converter for other skins and rename it, please keep the first and second line adding your credits below

from Components.Converter.Converter import Converter 
from Components.Element import cached 
from Poll import Poll
from enigma import eConsoleAppContainer 
from os import system, path, popen
from Tools.Directories import fileExists

class UltimateTemp(Poll, Converter):
	CPU_CALC = 0
	CPU_ALL = 1
	CPU_TOTAL = 2
	TEMPERATURE = 3
	HDDTEMP = 4
	CPULOAD = 5
	CPUSPEED = 6
	FANINFO = 7

	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)
		self.container = eConsoleAppContainer()
		self.type = type
		self.short_list = True
		self.cpu_count = 0
		self.prev_info = self.getCpuInfo(self.CPU_CALC)
		if not type or type == "Total":
			self.type = self.CPU_TOTAL
			self.sfmt = "CPU: $0"
		else:
			self.type = self.CPU_ALL
			self.sfmt = txt = str(type)
			pos = 0
			while True:
				pos = self.sfmt.find("$", pos)
				if pos == -1:
					break
				if pos < len(self.sfmt) - 1 and self.sfmt[pos + 1].isdigit():
					x = int(self.sfmt[pos + 1])
					if x > self.cpu_count:
						self.sfmt = self.sfmt.replace("$" + self.sfmt[pos + 1], "n/a")
				pos += 1
		self.curr_info = self.getCpuInfo(self.type)
		self.list = []
		if "CPULoad" in type:
			self.type = self.CPULOAD
		elif "CPUSpeed" in type:
			self.type = self.CPUSPEED
		elif "Temperature" in type:
			self.type = self.TEMPERATURE
		elif "HDDTemp" in type:
			self.type = self.HDDTEMP
			self.hddtemp_output = ""
			self.hddtemp = "Waiting for HDD Temp Data..."
			self.container.appClosed.append(self.runFinished)
			self.container.dataAvail.append(self.dataAvail)
			self.container.execute("hddtemp -n -q /dev/sda")
		elif "FanInfo" in type:
			self.type = self.FANINFO
		if self.type in (self.CPU_TOTAL, self.CPU_ALL, self.HDDTEMP):
			self.poll_interval = 500
		else:
			self.poll_interval = 7000
		self.poll_enabled = True

	def dataAvail(self, strData):
		self.hddtemp_output = self.hddtemp_output + strData

	def runFinished(self, retval):
		temp = str(self.hddtemp_output)
		if "No such file or directory" in temp or "not found" in temp:
			htemp = ""
			self.hddtemp = "HDD Temp: N/A"
		else:
			htemp = str(int(temp))
			if htemp == "0" or htemp is None:
				self.hddtemp = "HDD idle or N/A"
			else:
				self.hddtemp = "HDD Temp: " + htemp + "°C"
	@cached
	def getText(self):
		res = self.sfmt
		self.prev_info, self.curr_info = self.curr_info, self.getCpuInfo(self.type)
		text = ""
		for i in range(len(self.curr_info)):
			try:
				p = 100 * (self.curr_info[i][2] - self.prev_info[i][2]) / (self.curr_info[i][1] - self.prev_info[i][1])
			except ZeroDivisionError:
				p = 0
			res = res.replace("$" + str(i), "% 3d%%" % p)
			text = res.replace("$?", "%d" % self.cpu_count)
		if (self.type == self.CPULOAD):
			cpuload = ""
			if fileExists("/proc/loadavg"):
				try:
					l = open("/proc/loadavg", "r")
					load = l.readline(4)
					l.close()
				except:
					load = ""
				cpuload = load.replace("\n", "").replace(" ","")
				return ("CPU Load: %s") % cpuload
		elif (self.type == self.TEMPERATURE):
			while True:
				systemp = ""
				cputemp = ""
				try:
					if fileExists("/proc/stb/sensors/temp0/value"):
						stemp = open("/proc/stb/sensors/temp0/value").readline()
						systemp = "Sys Temp: " + stemp.replace("\n", "") + "°C"
						stemp.close()
					elif fileExists("/proc/stb/fp/temp_sensor"):
						stemp = open("/proc/stb/fp/temp_sensor").readline()
						systemp = "Board: " + stemp.replace("\n", "") + "°C"
						stemp.close()
					if fileExists("/proc/stb/fp/temp_sensor_avs"):
						ctemp = open("/proc/stb/fp/temp_sensor_avs").readline()
						cputemp = ctemp.replace("\n", "") + "°C"
						ctemp.close()
					elif fileExists("/sys/devices/virtual/thermal/thermal_zone0/temp"):
						ctemp = open("/sys/devices/virtual/thermal/thermal_zone0/temp").read()[:2]
						cputemp = ctemp.replace("\n", "") + "°C"
						ctemp.close()
					elif fileExists("/proc/hisi/msp/pm_cpu"):
						for line in open("/proc/hisi/msp/pm_cpu").readlines():
							line = [x.strip() for x in line.strip().split(":")]
							if line[0] in ("Tsensor"):
								ctemp = line[1].split("=")
								ctemp = line[1].split(" ")
								cputemp = ctemp[2] + "°C"
				except:
					pass
				if systemp == "" and cputemp == "":
					return "Temperature: N/A"
				if systemp == "":
					return ("CPU Temperature: ") + cputemp
				if cputemp == "":
					return systemp
				return systemp + "  " + ("CPU: ") + cputemp
		elif (self.type == self.HDDTEMP):
			return self.hddtemp
		elif (self.type == self.CPUSPEED):
			try:
				cpuspeed = 0
				for line in open("/proc/cpuinfo").readlines():
					line = [x.strip() for x in line.strip().split(":")]
					if line[0] == "cpu MHz":
						cpuspeed = "%1.0f" % float(line[1])
				if not cpuspeed:
					try:
						cpuspeed = int(open("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq").read()) / 1000
					except:
						try:
							import binascii
							cpuspeed = int(int(binascii.hexlify(open('/sys/firmware/devicetree/base/cpus/cpu@0/clock-frequency', 'rb').read()), 16) / 100000000) * 100
						except:
							cpuspeed = "-"
				return ("CPU Speed: %s MHz") % cpuspeed
			except:
				return ""
		if (self.type == self.FANINFO):
			fs = ""
			fv = ""
			fp = ""
			try:
				if fileExists("/proc/stb/fp/fan_speed"):
					fs = str(open("/proc/stb/fp/fan_speed", "r").readline().strip())
					fs = ("Speed: %s  ") % fs
					fs.close()
				if fileExists("/proc/stb/fp/fan_vlt"):
					fv = int(open("/proc/stb/fp/fan_vlt", "r").readline().strip(), 16)
					fv = str(fv)
					fv = ("V: %s  ") % fv
					fv.close()
				if fileExists("/proc/stb/fp/fan_pwm"):
					fp = int(open("/proc/stb/fp/fan_pwm", "r").readline().strip(), 16)
					fp = str(fp)
					fp = ("PWM: %s  ") % fp
					fp.close()
			except:
				pass
			if fs == "":
				return "Fan Info: N/A"
			return fs + fv + fp
		return text
	text = property(getText)
	def getCpuInfo(self, cpu = -1):
		def validCpu(c):
			if cpu == self.CPU_CALC and c.isdigit():
				return True
			if cpu == self.CPU_ALL:
				return True
			if c == " " and cpu == self.CPU_TOTAL:
				return True
			if c == str(cpu):
				return True
			return False
		res = []
		calc_cpus = cpu == self.CPU_CALC and self.cpu_count == 0
		try:
			fd = open("/proc/stat", "r")
			for l in fd:
				if l[0] != "c":
					continue
				if l.find("cpu") == 0 and validCpu(l[3]):
					if calc_cpus:
						self.cpu_count += 1
						continue
					total = busy = 0
					tmp = l.split()
					for i in range(1, len(tmp)):
						tmp[i] = int(tmp[i])
						total += tmp[i]
					busy = total - tmp[4] - tmp[5]
					if self.short_list:
						res.append([tmp[0], total, busy])
					else:
						tmp.insert(1, total)
						tmp.insert(2, busy)
						res.append(tmp)
			fd.close()
		except:
			pass
		return res

	def doSuspend(self, suspended):
		if suspended:
			self.poll_enabled = False
		else:
			self.downstream_elements.changed((self.CHANGED_POLL,))
			self.poll_enabled = True

	def changed(self, what):
		if what[0] == self.CHANGED_POLL:
			self.downstream_elements.changed(what)