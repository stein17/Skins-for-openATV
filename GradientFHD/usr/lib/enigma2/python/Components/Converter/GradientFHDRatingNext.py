# -*- coding: utf-8 -*-
"""Numeric TMDb rating matching GradientFHDStarX's Info JSON.
Usage: <convert type="GradientFHDRatingNext">0..5 or P</convert>
"""
from datetime import datetime
from time import localtime, mktime, monotonic
import threading
from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from Components.Element import cached
from Components.config import config
from Components.Renderer.GradientFHDStarX import load_tmdb_vote
from Components.Renderer.GradientFHDConverlibr import convtext, apply_title_mapping
from enigma import eEPGCache

_cache = {}
_pending = set()
_lock = threading.Lock()

def _worker(slug):
    try:
        value = load_tmdb_vote(slug)
    except Exception:
        value = None
    with _lock:
        _cache[slug] = (monotonic(), value)
        _pending.discard(slug)

def _rating(slug):
    with _lock:
        entry = _cache.get(slug)
        age = monotonic() - entry[0] if entry else 1e9
        ttl = 30 if entry and entry[1] is not None else 4
        if age < ttl:
            return entry[1]
        if slug not in _pending:
            _pending.add(slug)
            threading.Thread(target=_worker, args=(slug,), daemon=True).start()
        return entry[1] if entry else None

class GradientFHDRatingNext(Poll, Converter):
    def __init__(self, type):
        Poll.__init__(self)
        Converter.__init__(self, type)
        self.index = str(type or '0').strip().upper()
        self.poll_interval = 2000
        self.poll_enabled = True

    def _title(self):
        ref = getattr(self.source, 'service', None)
        try:
            ref = ref.toString() if ref else None
        except Exception:
            ref = None
        if not ref:
            return ''
        try:
            epg = eEPGCache.getInstance()
            if self.index == 'P':
                now = localtime()
                try:
                    hour = int(config.epgselection.graph_primetimehour.value)
                    minute = int(config.epgselection.graph_primetimemins.value)
                except Exception:
                    hour, minute = 20, 15
                when = int(mktime(datetime(now.tm_year, now.tm_mon, now.tm_mday, hour, minute).timetuple()))
                events = epg.lookupEvent(['BDTSE', (ref, 0, when, 0)])
                return str(events[0][2] or '') if events else ''
            i = int(self.index)
            if not 0 <= i <= 20:
                return ''
            events = epg.lookupEvent(['BDTSE', (ref, 0, -1, 1440)])
            return str(events[i][2] or '') if events and i < len(events) else ''
        except Exception:
            return ''

    @cached
    def getText(self):
        title = self._title()
        if not title:
            return ''
        try:
            slug = convtext(apply_title_mapping(title))
            if not slug:
                return ''
            vote = _rating(slug)
            if vote is None:
                return ''
            vote = float(vote)
            return '(%.1f)' % vote if 0 < vote <= 10 else ''
        except Exception:
            return ''
    text = property(getText)
