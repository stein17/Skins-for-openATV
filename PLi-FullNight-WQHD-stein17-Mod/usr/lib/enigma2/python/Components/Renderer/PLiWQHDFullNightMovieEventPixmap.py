# -*- coding: utf-8 -*-
from time import localtime, mktime
from datetime import datetime
from Components.Renderer.Renderer import Renderer
from Components.config import config
from enigma import eEPGCache, ePixmap

class PLiWQHDFullNightMovieEventPixmap(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.eventNumber = '0'

    def applySkin(self, desktop, parent):
        attrs = []
        for attrib, value in self.skinAttributes:
            if attrib == 'eventNumber':
                self.eventNumber = str(value).strip().upper()
            else:
                attrs.append((attrib, value))
        self.skinAttributes = attrs
        return Renderer.applySkin(self, desktop, parent)

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
            return None, None
        epg = eEPGCache.getInstance()
        try:
            if self.eventNumber == 'P':
                now = localtime()
                try:
                    hour = config.epgselection.graph_primetimehour.value
                    minute = config.epgselection.graph_primetimemins.value
                except Exception:
                    hour, minute = 20, 15
                dt = datetime(now.tm_year, now.tm_mon, now.tm_mday, hour, minute)
                primetime = int(mktime(dt.timetuple()))
                events = epg.lookupEvent(['BDTSE', (service_ref, 0, primetime, 0)])
                return service_ref, (events and events[0] or None)
            idx = int(self.eventNumber or '0')
        except Exception:
            idx = 0
        try:
            events = epg.lookupEvent(['BDTSE', (service_ref, 0, -1, 1440)])
            return service_ref, (events[idx] if events and len(events) > idx else None)
        except Exception:
            return service_ref, None

    def changed(self, what):
        if not self.instance:
            return
        self.instance.hide()
        if what[0] == self.CHANGED_CLEAR:
            return
        try:
            service_ref, ev = self._query_event()
            if not service_ref or not ev:
                return
            begin = int(ev[0] or 0)
            duration = int(ev[1] or 0)
            title = ev[2] or ''
            short = ev[3] if len(ev) > 3 and ev[3] else ''
            ext = ev[4] if len(ev) > 4 and ev[4] else ''
            try:
                from Plugins.Extensions.e2MDB.E2MDBServiceListPreview import buildE2MDBServiceListPixmapFromValues
            except Exception:
                return
            size = None
            try:
                sz = self.instance.size()
                size = (sz.width(), sz.height())
            except Exception:
                size = None
            try:
                event_number = 0 if self.eventNumber == '0' else (1 if self.eventNumber == '1' else int(self.eventNumber))
            except Exception:
                event_number = 0
            pix = buildE2MDBServiceListPixmapFromValues(service_ref, begin_time=begin, duration=duration, title=title, short_desc=short, extended_desc=ext, size=size, event_number=event_number)
            if pix is not None:
                self.instance.setPixmap(pix)
                self.instance.show()
        except Exception:
            self.instance.hide()
