# -*- coding: utf-8 -*-
"""Gradient FHD MovieGuide events for selected ChannelSelection ServiceEvent.
Modes: Title, Desc, Start, End, TimeRange, Duration, TimeDuration, Remain.
Event index: 0=current, 1=next, 2=next-next, P=primetime.
"""
from datetime import datetime
from time import localtime, mktime, strftime, time
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.config import config
from enigma import eEPGCache

class GradientFHDMovieGuideInfo(Converter):
    def __init__(self, type):
        Converter.__init__(self, type)
        args = [i.strip() for i in str(type or '').split(',')]
        self.mode = (args[0] if args else 'Title').lower()
        self.index = (args[1] if len(args) > 1 else '0').upper()

    def _service_ref(self):
        ref = getattr(self.source, 'service', None)
        try:
            return ref.toString() if ref else None
        except Exception:
            return None

    def _event(self):
        ref = self._service_ref()
        if not ref:
            return None
        epg = eEPGCache.getInstance()
        try:
            if self.index == 'P':
                clock = localtime()
                try:
                    hour = int(config.epgselection.graph_primetimehour.value)
                    minute = int(config.epgselection.graph_primetimemins.value)
                except Exception:
                    hour, minute = 20, 15
                t = int(mktime(datetime(clock.tm_year, clock.tm_mon, clock.tm_mday, hour, minute).timetuple()))
                events = epg.lookupEvent(['BDTSE', (ref, 0, t, 0)])
                return events[0] if events else None
            index = int(self.index)
            events = epg.lookupEvent(['BDTSE', (ref, 0, -1, 1440)])
            return events[index] if events and 0 <= index < len(events) else None
        except Exception:
            return None

    @cached
    def getText(self):
        ev = self._event()
        if not ev:
            return ''
        try:
            start, duration, title = int(ev[0]), int(ev[1]), ev[2] or ''
            short = ev[3] or '' if len(ev) > 3 else ''
            long = ev[4] or '' if len(ev) > 4 else ''
            begin_text = strftime('%H:%M', localtime(start))
            end_text = strftime('%H:%M', localtime(start + duration))
            mins = int(round(duration / 60.0))
            mode = self.mode
            if mode == 'title': return title
            if mode == 'desc': return (short + (' ' + long if long and long != short else '')).strip()
            if mode == 'start': return begin_text
            if mode == 'end': return end_text
            if mode == 'timerange': return '%s - %s' % (begin_text, end_text)
            if mode == 'duration': return '%d Min.' % mins
            if mode == 'timeduration': return '%s  |  %d Min.' % (begin_text, mins)
            if mode == 'remain': return '+%d Min.' % max(0, int((start + duration - time()) / 60.0))
        except Exception:
            return ''
        return ''

    text = property(getText)
