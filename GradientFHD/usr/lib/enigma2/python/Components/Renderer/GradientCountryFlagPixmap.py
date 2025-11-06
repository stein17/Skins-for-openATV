# Components/Renderer/GradientCountryFlagPixmap.py
# Python 3 only
# Concept and design by stein17, with the assistance of Python Code Generator
# Please do not remove these lines; kindly request my permission before sharing or publishing.

from Components.Renderer.Renderer import Renderer
from enigma import ePixmap
import os

class GradientCountryFlagPixmap(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.basePath = '/usr/share/enigma2/skin_default/countries'
        self.missing = 'missing.png'
        self.scaled = True

    def applySkin(self, desktop, parent):
        attribs = []
        for (attrib, value) in self.skinAttributes:
            if attrib == 'basePath':
                self.basePath = value.rstrip('/')
            elif attrib == 'missing':
                self.missing = value
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

    def _resolvePath(self, code):
        filename = (code or '').lower() + '.png'
        p1 = '%s/%s' % (self.basePath, filename)
        if os.path.exists(p1):
            return p1
        p2 = '%s/countries/%s' % (self.basePath, filename)
        if os.path.exists(p2):
            return p2
        p3 = '%s/%s' % (self.basePath, self.missing)
        return p3 if os.path.exists(p3) else ''

    def changed(self, what):
        if not self.instance:
            return
        try:
            code = str(self.source.text or '').strip()
        except Exception:
            code = ''
        path = self._resolvePath(code) if code else ''
        if path and os.path.exists(path):
            try:
                self.instance.setScale(1 if self.scaled else 0)
            except Exception:
                pass
            self.instance.setPixmapFromFile(path)
            self.instance.show()
        else:
            self.instance.hide()
