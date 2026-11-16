# -*- coding: utf-8 -*-
"""Readable playback times for the standard Enigma2 MoviePlayer.

Uses the built-in ServicePosition position/length API, without changing
OpenATV time display settings.  This converter is not intended for EMC.
"""
from Components.Converter.ServicePosition import ServicePosition
from Components.Element import cached
from Components.Language import language


class PLiFullNightMovieTime(ServicePosition):
    MODES = ("Length", "Elapsed", "Remaining", "LengthReadable", "RemainingReadable")

    def __init__(self, mode):
        self.display_mode = (mode or "").strip()
        if self.display_mode not in self.MODES:
            raise ValueError("PLiFullNightMovieTime: invalid mode %s" % mode)
        # Do not use Gauge: a Label has no cutlist_changed method.
        ServicePosition.__init__(self, "Position")

    @staticmethod
    def _german():
        try:
            return (language.getLanguage() or "").lower().startswith("de")
        except Exception:
            return False

    @staticmethod
    def _hms(ticks):
        seconds = max(0, int(ticks) // 90000)
        hours, rem = divmod(seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return "%02d:%02d:%02d" % (hours, minutes, seconds)

    def _readable(self, ticks, prefix=False, negative=False):
        # Round an incomplete minute up (e.g. 60:01 -> 61 minutes).
        total_minutes = (max(0, int(ticks)) + 5400000 - 1) // 5400000
        hours, minutes = divmod(total_minutes, 60)
        german = self._german()
        hour_unit, minute_unit = ("Std.", "Min.") if german else ("hr", "min")
        if hours:
            value = ("%d %s %d %s" % (hours, hour_unit, minutes, minute_unit)
                     if minutes else "%d %s" % (hours, hour_unit))
        else:
            value = "%d %s" % (minutes, minute_unit)
        if prefix:
            value = ("Dauer: " if german else "Duration: ") + value
        if negative:
            value = "-" + value
        return value

    @cached
    def getText(self):
        try:
            length = self.length
            if length is None or int(length) <= 0:
                return ""
            length = int(length)
            position = self.position
            if position is None:
                return "" if self.display_mode not in ("Length", "LengthReadable") else (
                    self._readable(length, prefix=True) if self.display_mode == "LengthReadable" else self._hms(length))
            position = max(0, min(length, int(position)))
            if self.display_mode == "LengthReadable":
                return self._readable(length, prefix=True)
            if self.display_mode == "RemainingReadable":
                return self._readable(length - position, negative=True)
            if self.display_mode == "Length":
                return self._hms(length)
            if self.display_mode == "Elapsed":
                return self._hms(position)
            return "- " + self._hms(length - position)
        except (TypeError, ValueError, OverflowError, AttributeError) as error:
            print("[PLiFullNightMovieTime] %s: %s" % (self.display_mode, error))
            return ""

    text = property(getText)
