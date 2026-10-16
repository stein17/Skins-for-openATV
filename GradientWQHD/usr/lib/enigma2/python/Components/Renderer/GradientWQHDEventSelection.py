# -*- coding: utf-8 -*-
"""Selected ChannelSelection service -> EPG event, 0..N or Primetime.
Only called from the Enigma2 GUI thread. No networking.
"""
from datetime import datetime, timedelta
from time import localtime, mktime, time
from Components.config import config
from enigma import eEPGCache, eServiceReference


def selected_service(source):
    if source is None:
        return None
    ref = getattr(source, 'service', None)
    if ref is None and hasattr(source, 'getCurrentService'):
        try:
            ref = source.getCurrentService()
        except Exception:
            pass
    if ref is None:
        return None
    try:
        value = ref.toString()
    except Exception:
        return None
    return eServiceReference(value) if value else None


def primetime_timestamp():
    now = localtime()
    try:
        h = int(config.epgselection.graph_primetimehour.value)
        m = int(config.epgselection.graph_primetimemins.value)
    except Exception:
        h, m = 20, 15
    if not (0 <= h <= 23 and 0 <= m <= 59):
        h, m = 20, 15
    return int(mktime(datetime(now.tm_year, now.tm_mon, now.tm_mday, h, m).timetuple()))


def get_event(source, index=0, prime=False):
    """Return an eServiceEvent or None for the selected service.
    lookupEventId resolves full descriptors (rating and description).
    """
    service = selected_service(source)
    if service is None:
        return None
    epg = eEPGCache.getInstance()
    try:
        ref = service.toString()
        if prime:
            rows = epg.lookupEvent(['IBDCTESX', (ref, 0, primetime_timestamp(), 0)])
            if not rows:
                return None
            event_id = int(rows[0][0])
        else:
            rows = epg.lookupEvent(['IBDCTESX', (ref, 0, -1, 1440)])
            n = int(index)
            if not rows or n < 0 or n >= len(rows):
                return None
            event_id = int(rows[n][0])
        return epg.lookupEventId(service, event_id)
    except Exception:
        return None
