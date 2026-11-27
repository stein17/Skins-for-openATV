# -*- coding: utf-8 -*-
"""Time displays for EMC. Preserve EMC player-length fallback and polling."""
from Components.Converter.EMCServicePosition import EMCServicePosition
from Components.Element import cached
from Components.Language import language


class PLiWQHDFullNightEMCTime(EMCServicePosition):
    MODES = (
        "Length", "Elapsed", "Remaining", "LengthMinutes",
        "LengthMinutesLabel", "LengthReadable", "RemainingReadable",
    )

    def __init__(self, mode):
        self.display_mode = mode.strip()
        if self.display_mode not in self.MODES:
            raise ValueError("PLiWQHDFullNightEMCTime: invalid mode %s" % mode)
        # EMC supplies player.getLength() fallback. Position mode is suitable
        # for a Label and does not send Gauge cutlist events to the label.
        EMCServicePosition.__init__(self, "Position")

    @staticmethod
    def _ceil_minutes(ticks):
        minute = 60 * 90000
        return (ticks + minute - 1) // minute

    @staticmethod
    def _hms(ticks):
        secs = max(0, ticks // 90000)
        hours, remainder = divmod(secs, 3600)
        minutes, seconds = divmod(remainder, 60)
        return "%02d:%02d:%02d" % (hours, minutes, seconds)

    @staticmethod
    def _german():
        try:
            return (language.getLanguage() or "").lower().startswith("de")
        except Exception:
            return False

    def _readable(self, ticks, prefix=False, negative=False):
        mins = self._ceil_minutes(max(0, ticks))
        hours, minutes = divmod(mins, 60)
        de = self._german()
        hunit, munit = ("Std.", "Min.") if de else ("hr", "min")
        if hours:
            body = "%d %s %d %s" % (hours, hunit, minutes, munit) if minutes else "%d %s" % (hours, hunit)
        else:
            body = "%d %s" % (minutes, munit)
        if prefix:
            body = ("Dauer: " if de else "Duration: ") + body
        if negative:
            body = "-" + body
        return body

    @cached
    def getText(self):
        try:
            length = self.length
            position = self.position
            if length is None or int(length) <= 0:
                return ""
            length = int(length)
            position = max(0, min(length, int(position or 0)))
            mode = self.display_mode
            if mode == "LengthReadable":
                return self._readable(length, prefix=True)
            if mode == "RemainingReadable":
                return self._readable(length - position, negative=True)
            if mode in ("LengthMinutes", "LengthMinutesLabel"):
                mins = self._ceil_minutes(length)
                unit = "Min." if self._german() else "min"
                result = "%d %s" % (mins, unit)
                if mode == "LengthMinutesLabel":
                    return ("Dauer: " if self._german() else "Duration: ") + result
                return result
            ticks = length if mode == "Length" else (length - position if mode == "Remaining" else position)
            value = self._hms(ticks)
            return "- " + value if mode == "Remaining" else value
        except (TypeError, ValueError, OverflowError) as error:
            print("[PLiWQHDFullNightEMCTime] %s: %s" % (self.display_mode, error))
            return ""

    text = property(getText)
