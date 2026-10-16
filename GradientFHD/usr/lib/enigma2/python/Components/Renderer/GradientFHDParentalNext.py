# -*- coding: utf-8 -*-
"""GradientFHDParental with explicit EPG index for ChannelSelection."""
from Components.Renderer.GradientFHDParental import GradientFHDParental
from Components.Renderer.GradientFHDEventSelection import get_event


class GradientFHDParentalNext(GradientFHDParental):
    def __init__(self):
        GradientFHDParental.__init__(self)
        self.event_index = 1

    def applySkin(self, desktop, parent):
        attrs = []
        for key, value in self.skinAttributes:
            if key == 'nexts':
                self.event_index = str(value).strip().upper() if str(value).strip().upper() == "P" else int(value)
            else:
                attrs.append((key, value))
        self.skinAttributes = attrs
        return GradientFHDParental.applySkin(self, desktop, parent)

    def _get_event_and_path(self):
        # Do not fall back to currently playing service or a recording path.
        # Otherwise the selected channel could show another service's FSK.
        return get_event(self.source, prime=True) if self.event_index == "P" else get_event(self.source, self.event_index), None
