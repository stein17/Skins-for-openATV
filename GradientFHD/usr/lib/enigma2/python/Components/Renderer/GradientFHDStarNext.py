# -*- coding: utf-8 -*-
"""GradientFHDStarX with explicit EPG index for ChannelSelection."""
from Components.Renderer.GradientFHDStarX import GradientFHDStarX
from Components.Renderer.GradientFHDEventSelection import get_event


class GradientFHDStarNext(GradientFHDStarX):
    def __init__(self):
        GradientFHDStarX.__init__(self)
        self.event_index = 1

    def applySkin(self, desktop, parent):
        attrs = []
        for key, value in self.skinAttributes:
            if key == 'nexts':
                self.event_index = str(value).strip().upper() if str(value).strip().upper() == "P" else int(value)
            else:
                attrs.append((key, value))
        self.skinAttributes = attrs
        return GradientFHDStarX.applySkin(self, desktop, parent)

    def _update(self):
        if not self.instance:
            return
        event = get_event(self.source, prime=True) if self.event_index == "P" else get_event(self.source, self.event_index)
        if event is None:
            self._work_generation += 1
            self._last_key = None
            self._last_vote = None
            self.instance.hide()
            return
        title = (event.getEventName() or '').strip()
        if not title or title.lower() == 'sendepause':
            self._work_generation += 1
            self.instance.hide()
            return
        self._queue_worker({
            'file_path': None,
            'event_title': title,
            'last_key': self._last_key,
            'last_vote': self._last_vote,
        })
