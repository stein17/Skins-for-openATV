
# -*- coding: utf-8 -*-
#
# BLWQHDEventTime
# ------------------------------------------------------------
# Universal Event/Time converter for Enigma2 Skins.
#
# This converter returns ready formatted text, so no extra
# ClockToText or RemainingToText converter is needed.
#
# =============================================================================
#  DEUTSCH / GERMAN
# =============================================================================
#  Universal Event/Time converter for Enigma2 Skins
#
#  Copyright (c) 2026  @stein17
#
#  Freeware:
#  Dieses Projekt ist Freeware. Die private Nutzung ist erlaubt.
#  Anpassungen für eigene Skins/Setups (z.B. OpenATV, OpenHDF/Enigma2) sind ausdrücklich
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
#  Universal Event/Time converter for Enigma2 Skins
#
#  Copyright (c) 2026  @stein17
#
#  Freeware:
#  This project is freeware. Private use is permitted.
#  Modifications for your own skins/setups (e.g. OpenATV, OpenHDF/Enigma2) are explicitly
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
#  This software is provided "as is", without warranty of any kind.
#  Use at your own risk. The authors are not liable for any damages or data loss.
# =============================================================================
#
# Supported sources
# ------------------------------------------------------------
# source="ServiceEvent"
# source="Event"
# source="session.Event_Now"
# source="session.Event_Next"
# source="session.CurrentService"
# source="Service"
#
# Supported tokens
# ------------------------------------------------------------
# StartTime           -> 12:30
# EndTime             -> 13:50
# Times               -> 12:30 - 13:50
#
# Duration            -> 80 min
# DurationMinutes     -> 80
#
# Remaining           -> -25 min
# RemainingMinutes    -> -25
#
# Elapsed             -> +55 min
# ElapsedMinutes      -> +55
#
# ElapsedRemaining    -> +55 / -25 min
# ElapsedDuration     -> 55 / 80 min
# RemainingDuration   -> -25 / 80 min
#
# TimesDuration       -> 12:30 - 13:50 | 80 min
# StartEndDuration    -> 12:30 - 13:50 (80 min)
# BeginRemain         -> 12:30 | -25 min
# EndRemain           -> 13:50 | -25 min
#
# Progress            -> 68%
#
# EMC / Movie playback note
# ------------------------------------------------------------
# If no valid event is available, this converter tries a seek-based
# fallback (service.seek -> position/length), so it also works in
# EMC / MoviePlayer / some source="Service" situations.
#
# Install
# ------------------------------------------------------------
# Copy file to:
# /usr/lib/enigma2/python/Components/Converter/BLWQHDEventTime.py
#
# Restart Enigma2:
# find /usr/lib/enigma2/python/Components/Converter/ -name 'BLWQHDEventTime*.pyc' -delete && init 4 && sleep 3 && init 3
#

from time import localtime, strftime, time

from enigma import eServiceCenter
from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from Components.Element import cached


class BLWQHDEventTime(Converter, Poll):
    STARTTIME = 0
    ENDTIME = 1
    TIMES = 2

    DURATION = 3
    DURATION_MINUTES = 4

    REMAINING = 5
    REMAINING_MINUTES = 6

    ELAPSED = 7
    ELAPSED_MINUTES = 8

    ELAPSED_REMAINING = 9
    ELAPSED_DURATION = 10
    REMAINING_DURATION = 11

    TIMES_DURATION = 12
    START_END_DURATION = 13
    BEGIN_REMAIN = 14
    END_REMAIN = 15

    PROGRESS = 16

    def __init__(self, token):
        Converter.__init__(self, token)
        Poll.__init__(self)

        token = (token or "").strip()

        mapping = {
            "StartTime": self.STARTTIME,
            "EndTime": self.ENDTIME,
            "Times": self.TIMES,

            "Duration": self.DURATION,
            "DurationMinutes": self.DURATION_MINUTES,

            "Remaining": self.REMAINING,
            "RemainingMinutes": self.REMAINING_MINUTES,

            "Elapsed": self.ELAPSED,
            "ElapsedMinutes": self.ELAPSED_MINUTES,

            "ElapsedRemaining": self.ELAPSED_REMAINING,
            "ElapsedDuration": self.ELAPSED_DURATION,
            "RemainingDuration": self.REMAINING_DURATION,

            "TimesDuration": self.TIMES_DURATION,
            "StartEndDuration": self.START_END_DURATION,
            "BeginRemain": self.BEGIN_REMAIN,
            "EndRemain": self.END_REMAIN,

            "Progress": self.PROGRESS,
        }

        self.token = mapping.get(token, self.TIMES)

        # changing values
        if self.token in (
            self.REMAINING,
            self.REMAINING_MINUTES,
            self.ELAPSED,
            self.ELAPSED_MINUTES,
            self.ELAPSED_REMAINING,
            self.ELAPSED_DURATION,
            self.REMAINING_DURATION,
            self.BEGIN_REMAIN,
            self.END_REMAIN,
            self.PROGRESS,
            self.ENDTIME,
            self.TIMES,
            self.TIMES_DURATION,
            self.START_END_DURATION,
        ):
            self.poll_interval = 1000
            self.poll_enabled = True
        else:
            self.poll_enabled = False

    def _fmt_clock(self, ts):
        try:
            if ts and int(ts) > 0:
                return strftime("%H:%M", localtime(int(ts)))
        except Exception:
            pass
        return ""

    def _mins_floor(self, sec):
        try:
            sec = int(sec)
            if sec < 0:
                sec = 0
            return sec // 60
        except Exception:
            return 0

    def _mins_round_up(self, sec):
        try:
            sec = int(sec)
            if sec < 0:
                sec = 0
            return (sec + 59) // 60
        except Exception:
            return 0

    def _extract_event_from_service(self, service):
        if service is None:
            return None
        try:
            info = service.info()
            if info is not None:
                event = info.getEvent(0)
                if event is not None:
                    return event
        except Exception:
            pass
        return None

    def _extract_event_from_ref(self, serviceref):
        if serviceref is None:
            return None
        try:
            info = eServiceCenter.getInstance().info(serviceref)
            if info is not None:
                event = info.getEvent(serviceref)
                if event is not None:
                    return event
        except Exception:
            pass
        return None

    def _get_event(self):
        src = getattr(self, "source", None)
        if src is None:
            return None

        for attr in ("event", "evt"):
            try:
                event = getattr(src, attr, None)
                if event is not None:
                    return event
            except Exception:
                pass

        for method_name in ("getEvent",):
            try:
                method = getattr(src, method_name, None)
                if callable(method):
                    try:
                        event = method()
                    except TypeError:
                        event = method(0)
                    if event is not None:
                        return event
            except Exception:
                pass

        for attr in ("service", "currentService"):
            try:
                service = getattr(src, attr, None)
                event = self._extract_event_from_service(service)
                if event is not None:
                    return event
            except Exception:
                pass

        for attr in ("serviceref", "service_ref", "serviceRef", "ref"):
            try:
                serviceref = getattr(src, attr, None)
                event = self._extract_event_from_ref(serviceref)
                if event is not None:
                    return event
            except Exception:
                pass

        for method_name in ("getCurrentService", "getService"):
            try:
                method = getattr(src, method_name, None)
                if callable(method):
                    service = method()
                    event = self._extract_event_from_service(service)
                    if event is not None:
                        return event
            except Exception:
                pass

        for method_name in ("getCurrentServiceRef", "getServiceRef"):
            try:
                method = getattr(src, method_name, None)
                if callable(method):
                    serviceref = method()
                    event = self._extract_event_from_ref(serviceref)
                    if event is not None:
                        return event
            except Exception:
                pass

        try:
            nested = getattr(src, "source", None)
            if nested is not None and nested is not src:
                old_source = self.source
                try:
                    self.source = nested
                    return self._get_event()
                finally:
                    self.source = old_source
        except Exception:
            pass

        return None

    def _get_seek(self):
        src = getattr(self, "source", None)
        if src is None:
            return None

        # common paths for source="Service" etc.
        candidates = []

        try:
            service = getattr(src, "service", None)
            if service is not None:
                candidates.append(service)
        except Exception:
            pass

        try:
            current_service = getattr(src, "currentService", None)
            if current_service is not None:
                candidates.append(current_service)
        except Exception:
            pass

        for method_name in ("getCurrentService", "getService"):
            try:
                method = getattr(src, method_name, None)
                if callable(method):
                    svc = method()
                    if svc is not None:
                        candidates.append(svc)
            except Exception:
                pass

        for svc in candidates:
            try:
                seek = svc and svc.seek()
                if seek is not None:
                    return seek
            except Exception:
                pass

        return None

    def _get_times_from_event(self):
        event = self._get_event()
        if event is None:
            return (0, 0, 0, 0, 0, False)

        try:
            begin = int(event.getBeginTime() or 0)
        except Exception:
            begin = 0

        try:
            duration = int(event.getDuration() or 0)
        except Exception:
            duration = 0

        if begin <= 0 or duration <= 0:
            return (begin, 0, duration, 0, 0, False)

        end = begin + duration
        now = int(time())

        if now < begin:
            elapsed = 0
            remaining = duration
        elif now >= end:
            elapsed = duration
            remaining = 0
        else:
            elapsed = now - begin
            remaining = end - now

        return (begin, end, duration, elapsed, remaining, True)

    def _get_times_from_seek(self):
        seek = self._get_seek()
        if seek is None:
            return (0, 0, 0, 0, 0, False)

        try:
            pos = seek.getPlayPosition()
            if pos[0]:
                return (0, 0, 0, 0, 0, False)
            position_pts = int(pos[1])
        except Exception:
            return (0, 0, 0, 0, 0, False)

        try:
            length = seek.getLength()
            if length[0]:
                return (0, 0, 0, 0, 0, False)
            length_pts = int(length[1])
        except Exception:
            return (0, 0, 0, 0, 0, False)

        if position_pts < 0 or length_pts <= 0:
            return (0, 0, 0, 0, 0, False)

        elapsed = position_pts // 90000
        duration = length_pts // 90000

        if duration <= 0:
            return (0, 0, 0, 0, 0, False)

        remaining = duration - elapsed
        if remaining < 0:
            remaining = 0
        if elapsed < 0:
            elapsed = 0
        if elapsed > duration:
            elapsed = duration

        now = int(time())
        begin = now - elapsed
        end = begin + duration

        return (begin, end, duration, elapsed, remaining, True)

    def _get_times(self):
        # 1) normal event path
        begin, end, duration, elapsed, remaining, valid = self._get_times_from_event()
        if valid:
            return (begin, end, duration, elapsed, remaining, True)

        # 2) EMC / playback fallback
        return self._get_times_from_seek()

    @cached
    def getText(self):
        begin, end, duration, elapsed, remaining, valid = self._get_times()

        if self.token == self.STARTTIME:
            return self._fmt_clock(begin)

        elif self.token == self.ENDTIME:
            return self._fmt_clock(end)

        elif self.token == self.TIMES:
            s = self._fmt_clock(begin)
            e = self._fmt_clock(end)
            if s and e:
                return "%s - %s" % (s, e)
            return s or e or ""

        elif not valid:
            return ""

        elif self.token == self.DURATION:
            return "%d min" % self._mins_round_up(duration)

        elif self.token == self.DURATION_MINUTES:
            return str(self._mins_round_up(duration))

        elif self.token == self.REMAINING:
            return "-%d min" % self._mins_floor(remaining)

        elif self.token == self.REMAINING_MINUTES:
            return "-%d" % self._mins_floor(remaining)

        elif self.token == self.ELAPSED:
            return "+%d min" % self._mins_floor(elapsed)

        elif self.token == self.ELAPSED_MINUTES:
            return "+%d" % self._mins_floor(elapsed)

        elif self.token == self.ELAPSED_REMAINING:
            return "+%d / -%d min" % (
                self._mins_floor(elapsed),
                self._mins_floor(remaining)
            )

        elif self.token == self.ELAPSED_DURATION:
            return "%d / %d min" % (
                self._mins_floor(elapsed),
                self._mins_round_up(duration)
            )

        elif self.token == self.REMAINING_DURATION:
            return "-%d / %d min" % (
                self._mins_floor(remaining),
                self._mins_round_up(duration)
            )

        elif self.token == self.TIMES_DURATION:
            return "%s - %s | %d min" % (
                self._fmt_clock(begin),
                self._fmt_clock(end),
                self._mins_round_up(duration)
            )

        elif self.token == self.START_END_DURATION:
            return "%s - %s (%d min)" % (
                self._fmt_clock(begin),
                self._fmt_clock(end),
                self._mins_round_up(duration)
            )

        elif self.token == self.BEGIN_REMAIN:
            return "%s | -%d min" % (
                self._fmt_clock(begin),
                self._mins_floor(remaining)
            )

        elif self.token == self.END_REMAIN:
            return "%s | -%d min" % (
                self._fmt_clock(end),
                self._mins_floor(remaining)
            )

        elif self.token == self.PROGRESS:
            try:
                return "%d%%" % int((elapsed * 100) / duration)
            except Exception:
                return "0%"

        return ""

    text = property(getText)