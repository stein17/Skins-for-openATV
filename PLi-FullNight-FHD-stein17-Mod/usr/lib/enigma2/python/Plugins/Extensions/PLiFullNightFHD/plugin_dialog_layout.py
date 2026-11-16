"""Bounded FullNight geometry for the two plugin-driven Metrix layout applets."""


def config_split(screen):
    screen['config'].l.setSeperation(screen['config'].instance.size().width() // 2)


def choice_layout(screen):
    from enigma import eLabel, ePoint, eSize, getDesktop

    desktop = getDesktop(0).size()
    factor = desktop.width() / 1280.0
    params = getattr(screen, 'params', None) or {}

    def bounded(key, fallback, minimum, maximum):
        try:
            value = int(float(params.get(key, fallback)) * factor)
        except (TypeError, ValueError, OverflowError):
            value = int(fallback * factor)
        return max(int(minimum * factor), min(maximum, value))

    width = bounded('width', 760, 420, desktop.width() - int(48 * factor))
    height = bounded('height', 500, 192, desktop.height() - int(48 * factor))
    screen.instance.resize(eSize(width, height))
    screen.instance.move(ePoint((desktop.width() - width) // 2, (desktop.height() - height) // 2))
    listing = screen['list'].instance
    listing.move(ePoint(int(16 * factor), int(78 * factor)))
    listing.resize(eSize(width - int(32 * factor), height - int(102 * factor)))
    for widget in getattr(screen, 'additionalWidgets', ()):
        instance = widget.instance
        if isinstance(instance, eLabel) and instance.position().x() == instance.position().y() == 0:
            instance.resize(eSize(width, height))
    for renderer in getattr(screen, 'renderer', ()):
        if isinstance(renderer.instance, eLabel) and renderer.instance.position().y() < int(60 * factor):
            renderer.instance.resize(eSize(width - int(48 * factor), int(40 * factor)))
