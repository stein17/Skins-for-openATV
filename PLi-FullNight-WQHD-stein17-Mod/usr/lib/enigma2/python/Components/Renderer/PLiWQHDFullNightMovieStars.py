# -*- coding: utf-8 -*-
"""e2MDB metadata rating -> user supplied starbar graphics. No network requests."""
from Components.Renderer.Renderer import Renderer
from Components.config import config
from enigma import ePixmap, loadPNG
import os
import re

class PLiWQHDFullNightMovieStars(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.filled = "icons/starsbar_filled.png"
        self.empty = "icons/starsbar_empty.png"

    def applySkin(self, desktop, parent):
        attrs = []
        for key, value in self.skinAttributes:
            if key == 'pixmap':
                self.filled = value
            elif key == 'backgroundPixmap':
                self.empty = value
            else:
                attrs.append((key, value))
        self.skinAttributes = attrs
        return Renderer.applySkin(self, desktop, parent)

    def changed(self, what):
        if self.instance is None:
            return
        self.instance.hide()
        if what[0] == self.CHANGED_CLEAR:
            return
        try:
            # e2MDB enriches ServiceEvent via the metadata interface.
            value = self.source.getMeta('rating')
            match = re.search(r'([0-9]+(?:[.,][0-9]+)?)', str(value or ''))
            if not match:
                return
            score = float(match.group(1).replace(',', '.'))
            if score <= 0:
                return
            if score > 10:
                score = min(score / 10.0, 10.0) if score <= 100 else 10.0
            skin = config.skin.primary_skin.value.split('/')[0]
            base = '/usr/share/enigma2/%s' % skin
            empty = os.path.join(base, self.empty)
            filled = os.path.join(base, self.filled)
            if not (os.path.isfile(empty) and os.path.isfile(filled)):
                return
            try:
                from PIL import Image
                with Image.open(empty) as bg0, Image.open(filled) as fg0:
                    w, h = self.instance.size().width(), self.instance.size().height()
                    if w <= 0 or h <= 0:
                        return
                    bg = bg0.convert('RGBA').resize((w, h), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
                    fg = fg0.convert('RGBA').resize((w, h), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
                    crop = max(0, min(w, int(w * score / 10.0)))
                    if crop:
                        part = fg.crop((0, 0, crop, h))
                        bg.paste(part, (0, 0), part)
                    tmp = '/tmp/PLiWQHDFullNightMovieStars_%d.png' % id(self)
                    bg.save(tmp)
                    self.instance.setPixmap(loadPNG(tmp))
                    self.instance.show()
                    try:
                        os.unlink(tmp)
                    except OSError:
                        pass
            except ImportError:
                # Never display an inaccurate full score if Pillow is unavailable.
                self.instance.hide()
        except Exception:
            self.instance.hide()
