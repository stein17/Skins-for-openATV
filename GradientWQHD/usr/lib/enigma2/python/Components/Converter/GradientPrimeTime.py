# -*- coding: utf-8 -*-
#
# =============================================================================
#  DEUTSCH / GERMAN
# =============================================================================
#  PrimeTime Converter for Enigma2 Skins
#
#  Copyright (c) 2026  @stein17
#
#  Freeware:
#  Dieses Projekt ist Freeware. Die private Nutzung ist erlaubt.
#  Anpassungen für eigene Skins/Setups (z.B. OpenATV/Enigma2) sind ausdrücklich
#  erlaubt.
#
#  Bedingungen:
#  1) Dieser Copyright-/Lizenz-Header muss in allen Kopien und abgeleiteten
#     Versionen vollständig erhalten bleiben und darf nicht entfernt oder
#     unkenntlich gemacht werden.
#  2) Eine Weitergabe (unverändert oder geändert) ist erlaubt, sofern dieser
#     Header erhalten bleibt und die ursprünglichen Urheber genannt werden.
#  3) Eine kommerzielle Nutzung (Verkauf, Paywall, bezahlte Images/Feeds,
#     kommerzielle Bundles) ist ohne vorherige schriftliche Zustimmung der
#     Urheber nicht gestattet.
#
#  Haftungsausschluss:
#  Die Software wird „wie sie ist“ bereitgestellt, ohne jegliche Garantie.
#  Die Nutzung erfolgt auf eigene Gefahr. Für Schäden oder Datenverlust wird
#  keine Haftung übernommen.
#
#
#  ENGLISH
# =============================================================================
#  PrimeTime Converter for Enigma2 Skins
#
#  Copyright (c) 2026  @stein17
#
#  Freeware:
#  This project is freeware. Private use is permitted.
#  Modifications for your own skins/setups (e.g. OpenATV/Enigma2) are explicitly
#  allowed.
#
#  Conditions:
#  1) This copyright/license header must be kept fully intact in all copies and
#     derivative works and must not be removed or obscured.
#  2) Redistribution (modified or unmodified) is permitted as long as this header
#     is retained and the original authors are credited.
#  3) Commercial use (sale, paywall, paid images/feeds, commercial bundles) is
#     not permitted without prior written consent from the authors.
#
#  Disclaimer:
#  This software is provided “as is”, without warranty of any kind.
#  Use at your own risk. The authors are not liable for any damages or data loss.
# =============================================================================
from Components.Converter.Converter import Converter
from Components.Element import cached, ElementError
from Components.config import config

from enigma import eEPGCache, eServiceReference

from time import localtime, strftime, mktime, time
from datetime import datetime


class GradientPrimeTime(Converter, object):
    """GradientPrimeTime

    Skin examples:
        <convert type="GradientPrimeTime">PrimeTime,noDuration</convert>
        <convert type="GradientPrimeTime">Event2,withDuration</convert>

    Modes:
        - Event1 / Event2 / Event3 : next events relative to current event
        - PrimeTime                : event that overlaps configured PrimeTime (hour/minute)

    Duration formats:
        - noDuration     -> "HH:MM - HH:MM  Title"
        - withDuration   -> "HH:MM - HH:MM  Title - xx min"
        - onlyDuration   -> "xx min"
    """

    Event1 = 0
    Event2 = 1
    Event3 = 2
    PrimeTime = 3

    noDuration = 10
    onlyDuration = 11
    withDuration = 12

    def __init__(self, type):
        Converter.__init__(self, type)
        self.epgcache = eEPGCache.getInstance()

        args = type.split(',')
        if len(args) != 2:
            raise ElementError('type must contain exactly 2 arguments')

        mode = args.pop(0)
        show = args.pop(0)

        if mode == 'Event2':
            self.type = self.Event2
        elif mode == 'Event3':
            self.type = self.Event3
        elif mode == 'PrimeTime':
            self.type = self.PrimeTime
        else:
            self.type = self.Event1

        if show == 'noDuration':
            self.showDuration = self.noDuration
        elif show == 'onlyDuration':
            self.showDuration = self.onlyDuration
        else:
            self.showDuration = self.withDuration

    def _getPrimeTimeHM(self):
        """Read PrimeTime hour/minute from config.plugins.GradientWQHD.*

        Defaults to 20:15 if config entries are missing.
        """
        hour = 20
        minute = 15

        try:
            sec = getattr(config.plugins, 'GradientWQHD', None)
            if sec is not None:
                h = getattr(sec, 'primeTimeHour', None)
                m = getattr(sec, 'primeTimeMinute', None)
                if h is not None:
                    hour = int(h.value)
                if m is not None:
                    minute = int(m.value)
        except Exception:
            pass

        # clamp safety
        if hour < 0:
            hour = 0
        elif hour > 23:
            hour = 23

        if minute < 0:
            minute = 0
        elif minute > 59:
            minute = 59

        return hour, minute

    def _getEventAtTime(self, service_ref, ts):
        """Return EPG event that is active at timestamp ts.

        We query from a few hours earlier so we can still catch events
        that started before PrimeTime.
        """
        start_ts = ts - 6 * 3600
        if start_ts < 0:
            start_ts = 0

        self.epgcache.startTimeQuery(service_ref, start_ts)

        while True:
            ev = self.epgcache.getNextTimeEntry()
            if not ev:
                return None

            begin = ev.getBeginTime()
            end = begin + ev.getDuration()

            # overlap check: event running at ts
            if begin <= ts < end:
                return ev

            # already beyond ts -> no overlap possible anymore
            if begin > ts:
                return None

    @cached
    def getText(self):
        ref = getattr(self.source, 'service', None)
        info = ref and getattr(self.source, 'info', None)
        if info is None or ref is None:
            return ''

        textvalue = ''

        # Event1 / Event2 / Event3 (next events)
        if self.type < self.PrimeTime:
            curEvent = self.source.getCurrentEvent()
            if curEvent:
                start = curEvent.getBeginTime() + curEvent.getDuration()
                self.epgcache.startTimeQuery(eServiceReference(ref.toString()), start)

                # skip N entries (Event1=0 means next event)
                for _ in range(self.type):
                    self.epgcache.getNextTimeEntry()

                nxt = self.epgcache.getNextTimeEntry()
                if nxt:
                    textvalue = self.formatEvent(nxt)

        # PrimeTime (configured hour/minute) -> event overlapping that time
        elif self.type == self.PrimeTime:
            now = localtime(time())
            hour, minute = self._getPrimeTimeHM()

            dt = datetime(now.tm_year, now.tm_mon, now.tm_mday, hour, minute)
            prime_ts = int(mktime(dt.timetuple()))

            service_ref = eServiceReference(ref.toString())
            ev = self._getEventAtTime(service_ref, prime_ts)
            if ev:
                textvalue = self.formatEvent(ev)

        return textvalue

    text = property(getText)

    def formatEvent(self, event):
        begin = strftime('%H:%M', localtime(event.getBeginTime()))
        end = strftime('%H:%M', localtime(event.getBeginTime() + event.getDuration()))
        title = event.getEventName() or ''
        duration = '%d min' % int(event.getDuration() // 60)

        if self.showDuration == self.withDuration:
            f = '{begin} - {end:10}{title:<} -  {duration}'
            return f.format(begin=begin, end=end, title=title, duration=duration)
        elif self.showDuration == self.onlyDuration:
            return duration
        elif self.showDuration == self.noDuration:
            f = '{begin} - {end:10}{title:<}'
            return f.format(begin=begin, end=end, title=title)
        return ''
