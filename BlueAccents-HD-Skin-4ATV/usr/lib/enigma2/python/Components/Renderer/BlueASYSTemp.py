from Components.VariableText import VariableText
from enigma import eLabel
from Renderer import Renderer
from os import path, popen

class BlueASYSTemp(Renderer, VariableText):
	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
		
	GUI_WIDGET = eLabel

	def changed(self, what):
		if not self.suspended:
			systemp = "-- "
			try:
				if path.exists('/proc/stb/sensors/temp0/value'):
					out_line = popen("cat /proc/stb/sensors/temp0/value").readline()
					systemp = out_line.replace('\n', '')
				elif path.exists('/proc/stb/fp/temp_sensor'):
					out_line = popen("cat /proc/stb/fp/temp_sensor").readline()
					systemp = out_line.replace('\n', '')
				elif path.exists('/proc/stb/sensors/temp/value'):
					out_line = popen("cat /proc/stb/sensors/temp/value").readline()
					systemp = out_line.replace('\n', '')
				elif path.exists('/proc/stb/power/avs'):
					out_line = popen("cat /proc/stb/power/avs").readline()
					systemp = out_line.replace('\n', '')
				elif path.exists('/proc/stb/fp/temp_sensor_avs'):
					out_line = popen("cat /proc/stb/fp/temp_sensor_avs").readline()
					systemp = out_line.replace('\n', '').replace(' ','')
				elif path.exists('/proc/hisi/msp/pm_cpu'):
					try:
						for line in open('/proc/hisi/msp/pm_cpu').readlines():
							line = [x.strip() for x in line.strip().split(":")]
							if line[0] in ("Tsensor"):
								temp = line[1].split("=")
								temp = line[1].split(" ")
								systemp = temp[2]
					except:
						systemp = ""
				elif path.exists('/sys/devices/virtual/thermal/thermal_zone0/temp'):
					out_line = open('/sys/devices/virtual/thermal/thermal_zone0/temp', 'r')
					systemp = out_line.read()
					systemp = systemp[:-4]
				if not systemp == "-- " and len(systemp) > 2:
					systemp = systemp[:2]
			except:
				pass
			self.text = systemp + str('\xc2\xb0') + "C"
			
	def onShow(self):
		self.suspended = False
		self.changed(None)

	def onHide(self):
		self.suspended = True
