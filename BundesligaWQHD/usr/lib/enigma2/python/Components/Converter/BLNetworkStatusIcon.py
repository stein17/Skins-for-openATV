from Components.Converter.Converter import Converter
from Components.NetworkManager import networkManager
from Components.Element import cached


class BLWQHDNetworkStatusIcon(Converter):
	"""Select the 43x43 LAN, WLAN or VPN status icon for one overview row."""

	VERSION = 4

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
			isWiFi = bool(getattr(adapter, "isWiFi", False))
			adapterEnabled = bool(getattr(adapter, "adapterEnabled", False))
			netInfo = getattr(adapter, "netInfo", None)
			link = bool(getattr(netInfo, "link", False)) if netInfo is not None else False
			connected = adapterEnabled and link
			if isWiFi:
				return "3" if connected else "2"
			return "0" if connected else "1"

		if row[1] == "\uE9AF" or row[3] == "VPN":
			vpn = networkManager.vpnInterfaces.get(row[2])
			return "5" if vpn is not None and bool(getattr(vpn, "up", False)) else "4"

		return "99"

	text = property(getText)

	def changed(self, what):
		Converter.changed(self, (self.CHANGED_DEFAULT,))

	def entry_changed(self, index):
		if self.rowIndex is None or index == self.rowIndex:
			Converter.changed(self, (self.CHANGED_DEFAULT,))
