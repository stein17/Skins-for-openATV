from Plugins.Plugin import PluginDescriptor


def main(session, **kwargs):
	from .ui import BLSmain
	session.open(BLSmain)


def Plugins(**kwargs):
	from enigma import getDesktop
	RESOLUTION = "FHD" if getDesktop(0).size().width() > 1300 else "HD"
	return [PluginDescriptor(name="Bootlogo Switcher",
		description="Bootlogo / Radiologo wechseln, Original sichern und wiederherstellen",
		icon=f"pics/{RESOLUTION}/plugin.png",
		where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main)]
