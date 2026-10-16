# -*- coding: utf-8 -*-
"""Primetime artwork via GradientWQHDBackdropX cache/download/decode logic.
The original GradientWQHDBackdropX renderer remains unchanged.
"""
import os
from Components.Renderer.GradientWQHDBackdropX import GradientWQHDBackdropX
from Components.Renderer import GradientWQHDBackdropX as backdrop_module
from Components.Renderer.GradientWQHDEventSelection import get_event


class GradientWQHDPrimeBackdrop(GradientWQHDBackdropX):
    def changed(self, what):
        if not self.instance:
            return
        if what[0] == self.CHANGED_CLEAR:
            self._clearPixmap()
            self.oldCanal = None
            return

        ev = get_event(self.source, prime=True)
        if ev is None:
            self.oldCanal = None
            self._clearPixmap()
            return
        title = ev.getEventName() or ''
        if not title:
            self.oldCanal = None
            self._clearPixmap()
            return

        short = ev.getShortDescription() or ''
        extended = ev.getExtendedDescription() or ''
        variants = backdrop_module.get_query_variants(title, short, extended)
        slug = backdrop_module.get_store_slug(variants.get('slug_title') or title)
        if not slug:
            self.oldCanal = None
            self._clearPixmap()
            return

        # BackdropX uses a PriorityQueue of 6-element lists. Every other
        # BackdropX entry has a string service name at index 0. None here
        # crashes Python 3 when the queue compares two entries.
        service_name = ''
        try:
            service = getattr(self.source, 'service', None)
            if service is not None:
                from ServiceReference import ServiceReference
                service_name = ServiceReference(service).getServiceName() or ''
        except Exception:
            pass
        service_name = str(service_name).replace('\xc2\x86', '').replace('\xc2\x87', '')

        canal = [service_name, int(ev.getBeginTime()), str(title), str(extended), str(short), str(slug)]
        key = '%s-%s-%s' % (service_name, canal[1], title)
        resolved, resolved_slug = backdrop_module._resolve_existing_backdrop_path(title, short, extended, slug)
        file_path = resolved or (backdrop_module.path_folder + slug + '.jpg')
        has_file = os.path.isfile(file_path) and os.path.getsize(file_path) > 0
        if key == self.oldCanal and has_file:
            return

        self.canal = canal
        self.oldCanal = key
        self._resolved_path = file_path
        self._resolved_slug = resolved_slug or slug
        if has_file:
            self._waiting_path = None
            self._waitBackdropPath = None
            self._waitBackdropQueued = False
            self.waitTimer.stop()
            self.timer.start(getattr(self, '_decode_delay_ms', 100), True)
        else:
            self._clearPixmap()
            self._dbg_last_path = None
            self._waiting_path = file_path
            self._waitBackdropPath = file_path
            self._waitBackdropQueued = True
            self._waitBackdropLoops = 180
            backdrop_module.pdb.put(canal)
            self.waitTimer.start(500, True)
