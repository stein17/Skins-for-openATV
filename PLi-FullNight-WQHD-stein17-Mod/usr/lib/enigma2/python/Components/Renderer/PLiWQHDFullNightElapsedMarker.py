# -*- coding: utf-8 -*-
"""Moving elapsed-time marker for EMC and MoviePlayer.

Pixmap and label are sibling widgets under the actual Screen parent,
not children of a large eWidget overlay. The progress bar is untouched.
"""

from os.path import isfile

from enigma import ePixmap, eLabel, ePoint, eSize, gFont
from Components.Renderer.Renderer import Renderer
from skin import parseColor


class PLiWQHDFullNightElapsedMarker(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.bar_x = 256
        self.bar_y = 1324
        self.bar_width = 2037
        self.flag_width = 187
        self.flag_height = 91
        self.flag_gap = 5
        self.flag_pixmap = "/usr/share/enigma2/PLi-FullNight-WQHD-stein17-Mod/progress/elapsed_flag.png"
        self.label = None
        self._screen_parent = None
        self._origin_x = 0
        self._origin_y = 0
        self._last_pos = None

    def createWidget(self, parent):
        # Use separate siblings, as in the e2iplayer pointer+label layout.
        self._screen_parent = parent
        return ePixmap(parent)

    def postWidgetCreate(self, instance):
        self.label = eLabel(self._screen_parent)
        self.label.setFont(gFont("Regular", 36))
        self.label.setForegroundColor(parseColor("white"))
        self.label.setHAlign(eLabel.alignCenter)
        self.label.setVAlign(eLabel.alignCenter)
        self.label.setTransparent(1)
        # The text must be ABOVE the PNG; both are siblings on the Screen.
        self.label.setZPosition(13)
        self.label.setWrap(0)
        self.label.hide()
        instance.hide()

    def preWidgetRemove(self, instance):
        if self.label is not None:
            self.label.hide()
        self.label = None
        self._screen_parent = None
        self._last_pos = None

    def applySkin(self, desktop, parent):
        attributes = []
        for key, value in self.skinAttributes or []:
            if key in ("barX", "barY", "barWidth", "flagWidth", "flagHeight", "flagGap"):
                try:
                    number = int(value)
                    if key == "barX":
                        self.bar_x = number
                    elif key == "barY":
                        self.bar_y = number
                    elif key == "barWidth":
                        self.bar_width = max(1, number)
                    elif key == "flagWidth":
                        self.flag_width = max(1, number)
                    elif key == "flagHeight":
                        self.flag_height = max(1, number)
                    else:
                        self.flag_gap = number
                except ValueError:
                    print("[PLiWQHDFullNightElapsedMarker] Invalid %s=%r" % (key, value))
            elif key == "flagPixmap":
                self.flag_pixmap = value
            elif key == "position":
                try:
                    px, py = value.split(",", 1)
                    self._origin_x = int(px.strip())
                    self._origin_y = int(py.strip())
                except (ValueError, AttributeError):
                    print("[PLiWQHDFullNightElapsedMarker] Invalid position=%r" % value)
                attributes.append((key, value))
            else:
                attributes.append((key, value))

        # Enigma2 applies the PNG alpha channel through the skin's alphatest.
        if not any(key == "alphatest" for key, _ in attributes):
            attributes.append(("alphatest", "blend"))
        self.skinAttributes = attributes
        result = Renderer.applySkin(self, desktop, parent)

        if self.instance is not None and self.label is not None:
            self.instance.resize(eSize(self.flag_width, self.flag_height))
            self.label.resize(eSize(max(1, self.flag_width - 8), max(1, self.flag_height - 36)))
            if isfile(self.flag_pixmap):
                self.instance.setScale(1)
                self.instance.setPixmapFromFile(self.flag_pixmap)
            else:
                print("[PLiWQHDFullNightElapsedMarker] Missing image: %s" % self.flag_pixmap)
                self.instance.hide()
                self.label.hide()
                return result
            self.changed((self.CHANGED_DEFAULT,))
        return result

    def cutlist_changed(self):
        # ServicePosition('Gauge') requires this callback.
        pass

    def changed(self, what):
        if self.instance is None or self.label is None:
            return
        if what[0] == self.CHANGED_CLEAR or self.source is None:
            self.instance.hide()
            self.label.hide()
            return
        try:
            position = self.source.position
            length = self.source.length
            if position is None or length is None or length <= 0:
                self.instance.hide()
                self.label.hide()
                return

            position = max(0, min(int(position), int(length)))
            length = int(length)
            seconds_total = position // 90000
            hours, rem = divmod(seconds_total, 3600)
            minutes, seconds = divmod(rem, 60)
            time_text = "%02d:%02d:%02d" % (hours, minutes, seconds)

            # barX/barY remain relative to XML widget position, unchanged.
            x = (self._origin_x + self.bar_x
                 + int(round(self.bar_width * position / length))
                 - self.flag_width // 2)
            y = self._origin_y + self.bar_y - self.flag_gap - self.flag_height
            self.instance.move(ePoint(x, y))
            self.label.move(ePoint(x + 4, y + 7))
            self.label.setText(time_text)
            self.instance.show()
            self.label.show()
        except Exception as err:
            print("[PLiWQHDFullNightElapsedMarker] Update failed: %s" % err)
            self.instance.hide()
            self.label.hide()
