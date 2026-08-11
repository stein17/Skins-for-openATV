# Components/Renderer/BLFHDMapPixmap.py
# Python 3 only

from Components.Renderer.Renderer import Renderer
from enigma import ePixmap
import os

class BLFHDMapPixmap(Renderer):
    """
    Text -> Pixmap Mapping.
    Skin-Attribute:
      pixmap.lan="..."
      pixmap.wlan="..."
      pixmap.net_off="..."
      scaled="1|0" (optional, default 1)
    """
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.map = {}
        self.scaled = True

    def applySkin(self, desktop, parent):
        attribs = []
        for (attrib, value) in self.skinAttributes:
            if attrib.startswith('pixmap.'):
                key = attrib.split('.', 1)[1]
                self.map[key] = value
            elif attrib in ('scaled', 'scale'):
                self.scaled = value in ('1', 'true', 'True', 'yes')
            else:
                attribs.append((attrib, value))
        self.skinAttributes = attribs
        if self.instance:
            try:
                self.instance.setScale(1 if self.scaled else 0)
            except Exception:
                pass
        return Renderer.applySkin(self, desktop, parent)

    def changed(self, what):
        if not self.instance:
            return
        try:
            key = str(self.source.text).strip()
        except Exception:
            key = ''
        path = self.map.get(key) or self.map.get(key.lower(), '')
        if path and os.path.exists(path):
            try:
                self.instance.setScale(1 if self.scaled else 0)
            except Exception:
                pass
            self.instance.setPixmapFromFile(path)
            self.instance.show()
        else:
            self.instance.hide()
