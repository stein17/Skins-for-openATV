
# "SelectionList" Idea by @digiteng....newly adapted and new features by @stein17 with the help of Python Code Generator
from __future__ import absolute_import
from Components.MenuList import MenuList
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT
from Tools.LoadPixmap import LoadPixmap
import skin

selectiononpng = LoadPixmap(cached=True, path="/usr/share/enigma2/GradientFHD/icons/lock_on.png")
selectionoffpng = LoadPixmap(cached=True, path="/usr/share/enigma2/GradientFHD/icons/lock_off.png")


def GradientSelectionEntryComponent(description, value, index, selected):
	dx, dy, dw, dh = skin.parameters.get("GradientSelectionListDescr", (50, 6, 650, 40))
	res = [
		(description, value, index, selected),
		(eListboxPythonMultiContent.TYPE_TEXT, dx, dy, dw, dh, 0, RT_HALIGN_LEFT, description)
	]
	if selected:
		ix, iy, iw, ih = skin.parameters.get("GradientSelectionListLock", (5, 2, 40, 40))
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, ix, iy, iw, ih, selectiononpng))
	else:
		ix, iy, iw, ih = skin.parameters.get("GradientSelectionListLockOff", (5, 2, 40, 40))
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, ix, iy, iw, ih, selectionoffpng))
	return res


class GradientSelectionList(MenuList):
	def __init__(self, list=None, enableWrapAround=False):
		MenuList.__init__(self, list or [], enableWrapAround, content=eListboxPythonMultiContent)
		font = skin.fonts.get("GradientSelectionList", ("Regular", 27, 32))
		self.l.setFont(0, gFont(font[0], font[1]))
		self.l.setItemHeight(font[2])

	def addSelection(self, description, value, index, selected=True):
		self.list.append(GradientSelectionEntryComponent(description, value, index, selected))
		self.setList(self.list)

	def toggleSelection(self):
		if len(self.list) > 0:
			idx = self.getSelectedIndex()
			item = self.list[idx][0]
			self.list[idx] = GradientSelectionEntryComponent(item[0], item[1], item[2], not item[3])
			self.setList(self.list)

	def getSelectionsList(self):
		return [(item[0][0], item[0][1], item[0][2]) for item in self.list if item[0][3]]

	def toggleAllSelection(self):
		for idx, item in enumerate(self.list):
			item = self.list[idx][0]
			self.list[idx] = GradientSelectionEntryComponent(item[0], item[1], item[2], not item[3])
		self.setList(self.list)

	def sort(self, sortType=False, flag=False):
		# sorting by sortType:
		# 0 - description
		# 1 - value
		# 2 - index
		# 3 - selected
		self.list.sort(key=lambda x: x[0][sortType], reverse=flag)
		self.setList(self.list)
