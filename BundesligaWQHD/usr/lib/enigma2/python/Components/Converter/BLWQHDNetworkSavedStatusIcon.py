from Components.Converter.Converter import Converter
from Components.Element import cached


class BLWQHDNetworkSavedStatusIcon(Converter):
	"""Select WLAN on/off for one visible saved-network row."""

	VERSION = 1

	def __init__(self, arguments):
		Converter.__init__(self, arguments)
		try:
			self.rowIndex = int(arguments.strip())
		except (AttributeError, TypeError, ValueError):
			self.rowIndex = None

	def getRow(self):
		if self.source is None:
			return None
		if self.rowIndex is None:
			return self.source.current
		rows = self.source.getList()
		return rows[self.rowIndex] if 0 <= self.rowIndex < len(rows) else None

	@cached
	def getText(self):
		row = self.getRow()
		if not row or len(row) <= 9 or row[0] != 1:
			return "99"

		# Only the currently associated WLAN entry receives real BSSID data.
		# All other saved connections contain an em dash at this position.
		bssid = row[2]
		connected = bool(bssid and bssid != "—")
		return "1" if connected else "0"

	text = property(getText)

	def changed(self, what):
		Converter.changed(self, (self.CHANGED_DEFAULT,))

	def entry_changed(self, index):
		if self.rowIndex is None or index == self.rowIndex:
			Converter.changed(self, (self.CHANGED_DEFAULT,))
