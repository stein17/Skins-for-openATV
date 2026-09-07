from Components.Converter.Converter import Converter
from Components.Element import cached


class BLWQHDNetworkAdapterIcon(Converter):
	"""Select the 80x80 adapter type icon for one NetworkOverview row."""

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
		if not row or len(row) <= 12 or row[0] != 1:
			return "99"

		adapter = row[12]
		if adapter is not None:
			return "1" if bool(getattr(adapter, "isWiFi", False)) else "0"

		# VPN rows do not contain an Adapter object. OpenATV supplies the
		# Vpn_key glyph at index 1 and the translated adapter type at index 3.
		if row[1] == "\uE9AF" or row[3] == "VPN":
			return "2"

		return "99"

	text = property(getText)

	def changed(self, what):
		Converter.changed(self, (self.CHANGED_DEFAULT,))

	def entry_changed(self, index):
		if self.rowIndex is None or index == self.rowIndex:
			Converter.changed(self, (self.CHANGED_DEFAULT,))
