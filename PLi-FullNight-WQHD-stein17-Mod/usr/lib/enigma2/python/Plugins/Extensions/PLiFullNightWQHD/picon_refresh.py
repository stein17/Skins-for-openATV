"""Refresh FullNight's native Picon binding after initial layout or a live reload."""


def prime_picons(screen):
    from Components.Renderer.Picon import Picon
    for renderer in screen.renderer:
        if isinstance(renderer, Picon) and renderer.instance is not None:
            # Picon ignores CHANGED_DEFAULT sent by Screen.reloadSkin().
            renderer.changed((renderer.CHANGED_ALL,))
