# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Converter.Poll import Poll

import os


class BLWQHDSystemInfo(Poll, Converter):
	CPU = 0
	MEMUSEDPCT = 1
	MEMFREE = 2
	SWAPUSEDPCT = 3
	TEMP = 4
	LOAD = 5
	MEMFREETXT = 6
	FLASHUSEDPCT = 7
	FLASHFREETXT = 8
	HDDUSEDPCT = 9
	HDDFREETXT = 10
	USBUSEDPCT = 11
	USBFREETXT = 12

	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)

		self.poll_interval = 2000
		self.poll_enabled = True

		t = (type or "").strip().upper()
		self.arg = t
		if t == "CPU":
			self.type = self.CPU
		elif t == "MEMUSEDPCT":
			self.type = self.MEMUSEDPCT
		elif t == "MEMFREE":
			self.type = self.MEMFREE
		elif t == "MEMFREETXT":
			self.type = self.MEMFREETXT
		elif t == "SWAPUSEDPCT":
			self.type = self.SWAPUSEDPCT
		elif t == "TEMP":
			self.type = self.TEMP
		elif t == "LOAD":
			self.type = self.LOAD
		elif t == "FLASHUSEDPCT":
			self.type = self.FLASHUSEDPCT
		elif t == "FLASHFREETXT":
			self.type = self.FLASHFREETXT
		elif t == "HDDUSEDPCT":
			self.type = self.HDDUSEDPCT
		elif t == "HDDFREETXT":
			self.type = self.HDDFREETXT
		elif t == "USBUSEDPCT":
			self.type = self.USBUSEDPCT
		elif t == "USBFREETXT":
			self.type = self.USBFREETXT
		else:
			self.type = None

		self._last_total = 0
		self._last_idle = 0
		self._cpu_percent = 0

	def _read_first_line(self, path):
		try:
			with open(path, "r") as f:
				return f.readline().strip()
		except Exception:
			return ""

	def _read_all_lines(self, path):
		try:
			with open(path, "r") as f:
				return f.readlines()
		except Exception:
			return []

	def _get_cpu_percent(self):
		try:
			line = self._read_first_line("/proc/stat")
			if not line.startswith("cpu "):
				return self._cpu_percent

			parts = line.split()
			if len(parts) < 5:
				return self._cpu_percent

			values = [int(x) for x in parts[1:]]
			total = sum(values)
			idle = values[3]
			if len(values) > 4:
				idle += values[4]  # iowait

			if self._last_total == 0:
				self._last_total = total
				self._last_idle = idle
				return self._cpu_percent

			delta_total = total - self._last_total
			delta_idle = idle - self._last_idle

			self._last_total = total
			self._last_idle = idle

			if delta_total <= 0:
				return self._cpu_percent

			used = delta_total - delta_idle
			pct = int((100 * used) / delta_total)
			if pct < 0:
				pct = 0
			elif pct > 100:
				pct = 100

			self._cpu_percent = pct
			return pct
		except Exception:
			return self._cpu_percent

	def _parse_meminfo(self):
		info = {}
		try:
			for line in self._read_all_lines("/proc/meminfo"):
				if ":" not in line:
					continue
				k, v = line.split(":", 1)
				val = v.strip().split()[0]
				try:
					info[k] = int(val)  # kB
				except Exception:
					info[k] = 0
		except Exception:
			pass
		return info

	def _get_mem_used_pct(self):
		info = self._parse_meminfo()
		total = info.get("MemTotal", 0)
		avail = info.get("MemAvailable", 0)
		if not avail:
			free = info.get("MemFree", 0)
			buffers = info.get("Buffers", 0)
			cached = info.get("Cached", 0)
			avail = free + buffers + cached
		if total <= 0:
			return 0
		used = total - avail
		pct = int((100 * used) / total)
		if pct < 0:
			pct = 0
		elif pct > 100:
			pct = 100
		return pct

	def _get_mem_free_mb(self):
		info = self._parse_meminfo()
		avail = info.get("MemAvailable", 0)
		if not avail:
			free = info.get("MemFree", 0)
			buffers = info.get("Buffers", 0)
			cached = info.get("Cached", 0)
			avail = free + buffers + cached
		return int(avail / 1024)

	def _get_swap_used_pct(self):
		info = self._parse_meminfo()
		total = info.get("SwapTotal", 0)
		free = info.get("SwapFree", 0)
		if total <= 0:
			return 0
		used = total - free
		pct = int((100 * used) / total)
		if pct < 0:
			pct = 0
		elif pct > 100:
			pct = 100
		return pct

	def _read_temp_raw(self, path):
		try:
			val = self._read_first_line(path)
			if not val:
				return None
			n = int(val)
			if n > 1000:
				n = int(n / 1000)
			return n
		except Exception:
			return None

	def _get_temp(self):
		paths = [
			"/proc/stb/sensors/temp0/value",
			"/proc/stb/fp/temp_sensor",
			"/sys/class/thermal/thermal_zone0/temp",
			"/sys/devices/virtual/thermal/thermal_zone0/temp",
			"/proc/hisi/msp/pm_cpu",
		]

		for p in paths:
			v = self._read_temp_raw(p)
			if v is not None and v > 0 and v < 200:
				return v

		try:
			if os.path.exists("/proc/hisi/msp/pm_cpu"):
				for line in self._read_all_lines("/proc/hisi/msp/pm_cpu"):
					line = line.strip().lower()
					if "temperature" in line or "temp" in line:
						num = "".join(ch for ch in line if ch.isdigit())
						if num:
							v = int(num)
							if v > 0 and v < 200:
								return v
		except Exception:
			pass

		return 0

	def _get_load(self):
		try:
			s = self._read_first_line("/proc/loadavg")
			if not s:
				return "0.00"
			return s.split()[0]
		except Exception:
			return "0.00"

	def _get_cpu_count(self):
		try:
			count = 0
			for line in self._read_all_lines("/proc/stat"):
				parts = line.split()
				if not parts:
					continue
				name = parts[0]
				if name.startswith("cpu") and name[3:].isdigit():
					count += 1
			return count if count > 0 else 1
		except Exception:
			return 1

	def _get_load_percent(self):
		try:
			load = float(self._get_load())
			cores = self._get_cpu_count()
			pct = int(round((load / cores) * 100))
			if pct < 0:
				pct = 0
			elif pct > 100:
				pct = 100
			return pct
		except Exception:
			return 0

	def _get_mount_stats(self, path):
		try:
			st = os.statvfs(path)
			block = st.f_frsize or st.f_bsize or 0
			total = st.f_blocks * block
			free = st.f_bavail * block
			used = total - (st.f_bfree * block)
			if total < 0:
				total = 0
			if free < 0:
				free = 0
			if used < 0:
				used = 0
			return total, free, used
		except Exception:
			return 0, 0, 0

	def _get_used_pct_for_path(self, path):
		total, free, used = self._get_mount_stats(path)
		if total <= 0:
			return 0
		pct = int((100 * used) / total)
		if pct < 0:
			pct = 0
		elif pct > 100:
			pct = 100
		return pct

	def _format_size(self, size_bytes):
		try:
			size_bytes = int(size_bytes)
		except Exception:
			size_bytes = 0
		if size_bytes <= 0:
			return "0 MB"
		gb = 1024.0 * 1024.0 * 1024.0
		mb = 1024.0 * 1024.0
		if size_bytes >= gb:
			return "%.1f GB" % (size_bytes / gb)
		return "%d MB" % int(size_bytes / mb)

	def _get_free_text_for_path(self, path):
		total, free, used = self._get_mount_stats(path)
		return self._format_size(free)

	@cached
	def getText(self):
		try:
			if self.type == self.CPU:
				return "%d%%" % self._get_cpu_percent()
			elif self.type == self.MEMUSEDPCT:
				return "%d%%" % self._get_mem_used_pct()
			elif self.type == self.MEMFREE:
				return "%d MB" % self._get_mem_free_mb()
			elif self.type == self.MEMFREETXT:
				return "%d MB" % self._get_mem_free_mb()
			elif self.type == self.SWAPUSEDPCT:
				return "%d%%" % self._get_swap_used_pct()
			elif self.type == self.TEMP:
				t = self._get_temp()
				return "%d°C" % t if t > 0 else "n/a"
			elif self.type == self.LOAD:
				return "%s / %d" % (self._get_load(), self._get_cpu_count())
			elif self.type == self.FLASHFREETXT:
				return self._get_free_text_for_path("/")
			elif self.type == self.HDDFREETXT:
				return self._get_free_text_for_path("/media/hdd")
			elif self.type == self.USBFREETXT:
				return self._get_free_text_for_path("/media/usb")
		except Exception:
			pass
		return ""

	text = property(getText)

	@cached
	def getValue(self):
		try:
			if self.type == self.CPU:
				return self._get_cpu_percent()
			elif self.type == self.LOAD:
				return self._get_load_percent()
			elif self.type == self.MEMUSEDPCT:
				return self._get_mem_used_pct()
			elif self.type == self.SWAPUSEDPCT:
				return self._get_swap_used_pct()
			elif self.type == self.TEMP:
				t = self._get_temp()
				if t < 0:
					t = 0
				elif t > 100:
					t = 100
				return t
			elif self.type == self.FLASHUSEDPCT:
				return self._get_used_pct_for_path("/")
			elif self.type == self.HDDUSEDPCT:
				return self._get_used_pct_for_path("/media/hdd")
			elif self.type == self.USBUSEDPCT:
				return self._get_used_pct_for_path("/media/usb")
		except Exception:
			pass
		return 0

	value = property(getValue)

	range = 100

	def changed(self, what):
		Converter.changed(self, what)
