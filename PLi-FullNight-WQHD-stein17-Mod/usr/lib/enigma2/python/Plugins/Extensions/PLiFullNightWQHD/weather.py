"""Validate the existing OAWeather source for the optional weather overlay."""

import math


def weather_ready(source, enabled):
    if source is None or not enabled:
        return False
    try:
        value = source.getCurrentVal("temp", None)
        return not isinstance(value, bool) and math.isfinite(float(value))
    except (AttributeError, TypeError, ValueError):
        return False
