# -*- coding: utf-8 -*-
"""FSK from explicit event-age info. No approximation from US movie ratings."""
from Components.Renderer.Renderer import Renderer
from Components.config import config
from enigma import ePixmap, loadPNG
import os
import re

class PLiWQHDFullNightMovieFSK(Renderer):
    GUI_WIDGET = ePixmap

    def changed(self, what):
        if not self.instance:
            return
        self.instance.hide()
        if what[0] == self.CHANGED_CLEAR:
            return
        try:
            src = self.source
            age = None
            for key in ('fsk', 'age_rating', 'parental_rating', 'age'):
                try:
                    raw = src.getMeta(key)
                except Exception:
                    raw = None
                if raw is not None:
                    m = re.search(r'(?<!\d)(0|6|12|16|18)(?!\d)', str(raw))
                    if m:
                        age = m.group(1)
                        break
            if age is None:
                event = getattr(src, 'event', None)
                if event:
                    detail = ' '.join((event.getShortDescription() or '', event.getExtendedDescription() or ''))
                    m = re.search(r'(?i)\b(?:FSK\s*|ab\s*)(0|6|12|16|18)\b', detail)
                    if m:
                        age = m.group(1)
            if age is None:
                age = 'NA'
            skin = config.skin.primary_skin.value.split('/')[0]
            fn = '/usr/share/enigma2/%s/parental/FSK_%s.png' % (skin, age)
            if os.path.isfile(fn):
                self.instance.setPixmap(loadPNG(fn))
                self.instance.show()
        except Exception:
            self.instance.hide()
