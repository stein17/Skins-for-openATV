"""Give long timer descriptions priority over the optional native video preview."""

from enigma import ePoint, eSize


def geometry(measured, scale=1):
    preview = measured <= round(316 * scale)
    return preview, round((326 if preview else 90) * scale), round((316 if preview else 552) * scale)


class TimerPreview:
    def __init__(self, screen, video):
        self.screen, self.video = screen, video
        self.callbacks = []
        for name in ("onSelectionChanged", "onShown"):
            callbacks = getattr(screen, name, None)
            if callbacks is not None:
                callbacks.append(self.update)
                self.callbacks.append(callbacks)
        screen.onClose.append(self.close)
        self.update()

    def update(self, *summary):
        description = self.screen["description"].instance
        if description is None or self.video.instance is None:
            return
        scale = self.screen.instance.size().width() / 1280
        preview, top, height = geometry(description.calculateSize().height(), scale)
        description.move(ePoint(description.position().x(), top))
        description.resize(eSize(description.size().width(), height))
        if preview:
            self.video.show()
            if self.screen.shown:
                self.video.onShow()
        else:
            self.video.hide()
            if self.screen.shown:
                self.video.onHide()

    def close(self):
        for callbacks in self.callbacks:
            if self.update in callbacks:
                callbacks.remove(self.update)


def install(screen):
    previous = getattr(screen, "_fullNightTimerPreview", None)
    if previous:
        previous.close()
        if previous.close in screen.onClose:
            screen.onClose.remove(previous.close)
    video = next((r for r in screen.renderer if r.__class__.__name__ == "Pig"), None)
    if video is not None and "description" in screen:
        screen._fullNightTimerPreview = TimerPreview(screen, video)
