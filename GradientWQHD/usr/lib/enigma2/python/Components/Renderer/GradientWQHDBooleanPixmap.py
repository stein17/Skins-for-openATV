# Components/Renderer/GradientWQHDBooleanPixmap.py
# Python 3 only

from Components.Renderer.Renderer import Renderer
from enigma import ePixmap
import os

class GradientWQHDBooleanPixmap(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.pix_on = ''
        self.pix_off = ''
        self.scaled = True

    def applySkin(self, desktop, parent):
        attribs = []
        for (attrib, value) in self.skinAttributes:
            if attrib == 'pixmapOn':
                self.pix_on = value
            elif attrib == 'pixmapOff':
                self.pix_off = value
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
        s = self.source
        val = False
        try:
            val = bool(getattr(s, 'boolean', False))
        except Exception:
            try:
                val = str(getattr(s, 'text', '')).lower() in ('1', 'true', 'yes')
            except Exception:
                val = False
        path = self.pix_on if val else self.pix_off
        if path and os.path.exists(path):
            try:
                self.instance.setScale(1 if self.scaled else 0)
            except Exception:
                pass
            self.instance.setPixmapFromFile(path)
            self.instance.show()
        else:
            self.instance.hide()
