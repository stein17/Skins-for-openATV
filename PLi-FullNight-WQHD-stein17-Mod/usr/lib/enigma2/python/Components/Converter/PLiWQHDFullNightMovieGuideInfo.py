# -*- coding: utf-8 -*-
from time import localtime, mktime, strftime
from datetime import datetime
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.config import config
from enigma import eEPGCache

class PLiWQHDFullNightMovieGuideInfo(Converter):
    TITLE = 'title'
    TIMERANGE = 'timerange'
    DESC = 'desc'
    SHORTDESC = 'shortdesc'

    def __init__(self, type):
        Converter.__init__(self, type)
        parts = [x.strip() for x in str(type or '').split(',')]
        self.mode = (parts[0].lower() if parts else self.TITLE)
        self.index_token = (parts[1] if len(parts) > 1 else '0').upper()

    def _get_service_ref(self):
        try:
            service = getattr(self.source, 'service', None)
            if service:
                return service.toString()
        except Exception:
            pass
        return None

    def _query_event(self):
        service_ref = self._get_service_ref()
        if not service_ref:
            return None
        epg = eEPGCache.getInstance()
        try:
            if self.index_token == 'P':
                now = localtime()
                try:
                    hour = config.epgselection.graph_primetimehour.value
                    minute = config.epgselection.graph_primetimemins.value
                except Exception:
                    hour, minute = 20, 15
                dt = datetime(now.tm_year, now.tm_mon, now.tm_mday, hour, minute)
                primetime = int(mktime(dt.timetuple()))
                events = epg.lookupEvent(['BDTSE', (service_ref, 0, primetime, 0)])
                return events and events[0] or None
            idx = int(self.index_token)
        except Exception:
            idx = 0
        try:
            events = epg.lookupEvent(['BDTSE', (service_ref, 0, -1, 1440)])
            if events and len(events) > idx:
                return events[idx]
        except Exception:
            pass
        return None

    def _fmt_time_range(self, begin, duration):
        try:
            b = strftime('%H:%M', localtime(int(begin)))
            e = strftime('%H:%M', localtime(int(begin) + int(duration)))
            return '%s - %s' % (b, e)
        except Exception:
            return ''

    @cached
    def getText(self):
        ev = self._query_event()
        if not ev:
            return ''
        try:
            begin = ev[0]
            duration = ev[1]
            title = ev[2] or ''
            short = ev[3] if len(ev) > 3 and ev[3] else ''
            ext = ev[4] if len(ev) > 4 and ev[4] else ''
        except Exception:
            return ''
        if self.mode == self.TIMERANGE:
            return self._fmt_time_range(begin, duration)
        if self.mode == self.SHORTDESC:
            return short
        if self.mode == self.DESC:
            txt = short or ext
            if short and ext and ext != short:
                txt = short + ' ' + ext
            return (txt or '').replace('\n', ' ').strip()
        return title

    text = property(getText)
