# -*- coding: utf-8 -*-
"""GradientWQHDParental with explicit EPG index for ChannelSelection."""
from Components.Renderer.GradientWQHDParental import GradientWQHDParental
from Components.Renderer.GradientWQHDEventSelection import get_event


class GradientWQHDParentalNext(GradientWQHDParental):
    def __init__(self):
        GradientWQHDParental.__init__(self)
        self.event_index = 1

    def applySkin(self, desktop, parent):
        attrs = []
        for key, value in self.skinAttributes:
            if key == 'nexts':
                self.event_index = str(value).strip().upper() if str(value).strip().upper() == "P" else int(value)
            else:
                attrs.append((key, value))
        self.skinAttributes = attrs
        return GradientWQHDParental.applySkin(self, desktop, parent)

    def _get_event_and_path(self):
        # Do not fall back to currently playing service or a recording path.
        # Otherwise the selected channel could show another service's FSK.
        return get_event(self.source, prime=True) if self.event_index == "P" else get_event(self.source, self.event_index), None
