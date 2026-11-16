from Components.Renderer.Progress import Progress


class PLiFullNightProgress(Progress):
    """
    FullNight progress renderer.

    ServicePosition(Gauge) calls cutlist_changed() on its downstream renderer.
    The stock Progress renderer does not implement that method.  FullNight
    normally uses PositionGauge for Gauge, but this no-op keeps any accidental
    Gauge -> Progress connection from crashing Enigma2.
    """

    def cutlist_changed(self):
        pass
