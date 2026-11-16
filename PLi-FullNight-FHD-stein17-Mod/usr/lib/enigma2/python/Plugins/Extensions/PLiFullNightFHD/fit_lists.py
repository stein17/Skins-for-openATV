# -*- coding: utf-8 -*-
"""Fit PLi FullNight eListboxes to whole rows using Umbra's event lifecycle.

No XML changes. Preserve list origin, width and native row height.
For unknown item counts, a fractional viewport is treated as a potential cut row.
"""
from enigma import eListbox, eSize, eTimer

EXCLUDED_SCREENS = frozenset(('EMCSelection', 'MovieSelection'))
UPPER_CONTENT_START = 109
LOWER_CONTENT_END = 1003

_detached = []
_detach_timer = eTimer()

def _flush_detached():
    while _detached:
        callbacks, callback = _detached.pop()
        try:
            if callback in callbacks:
                callbacks.remove(callback)
        except Exception:
            pass

_detach_timer.callback.append(_flush_detached)

def _detach(callbacks, callback):
    _detached.append((callbacks, callback))
    _detach_timer.start(0, True)


def _components(screen):
    return list(screen.values()) + list(getattr(screen, 'renderer', ()) or ())


def _rect(instance):
    p, s = instance.position(), instance.size()
    return p.x(), p.y(), p.x() + s.width(), p.y() + s.height()


def _overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _count(component, instance):
    for obj in (component, getattr(component, 'l', None), getattr(component, 'source', None)):
        if obj is None:
            continue
        for key in ('list', 'getList'):
            try:
                val = getattr(obj, key, None)
                if callable(val):
                    val = val()
                if isinstance(val, (list, tuple)):
                    return len(val)
            except Exception:
                pass
    try:
        content = instance.getContent()
        if content is not None:
            size = content.size()
            if isinstance(size, int) and size >= 0:
                return size
    except Exception:
        pass
    return None


def _can_grow(screen, component, instance, old_height, new_height):
    try:
        x1, y1, x2, _ = _rect(instance)
        screen_size = screen.instance.size()
        fullscreen = screen_size.width() == 1920 and screen_size.height() == 1080
        lower = LOWER_CONTENT_END if fullscreen else screen_size.height()
        upper = UPPER_CONTENT_START if fullscreen else 0
        if y1 < upper or y1 + new_height > lower:
            return False
        strip = (x1, y1 + old_height, x2, y1 + new_height)
        for other_comp in _components(screen):
            other = getattr(other_comp, 'instance', None)
            if other is None or other is instance:
                continue
            try:
                if not other.isVisible():
                    continue
                r = _rect(other)
            except Exception:
                return False
            # Full-screen backgrounds and large color panels are not obstacles.
            if (r[0] <= x1 and r[1] <= y1 and r[2] >= x2
                    and r[3] >= y1 + new_height):
                continue
            if _overlap(strip, r):
                return False
        return True
    except Exception:
        return False


class ListFitter:
    def __init__(self, screen):
        self.screen = screen
        self.bindings = []
        self.timer = eTimer()
        self.timer.callback.append(self.apply)
        seen = set()
        for component in _components(screen):
            instance = getattr(component, 'instance', None)
            if not isinstance(instance, eListbox) or id(instance) in seen:
                continue
            seen.add(id(instance))
            try:
                callbacks = instance.selectionChanged.get()
                width, limit = instance.size().width(), instance.size().height()
                self.bindings.append((component, width, limit, callbacks))
                callbacks.append(self.fit)
            except Exception as exc:
                print('[FullNightFitLists] BIND skipped: %s' % exc)
        screen.onShown.append(self.fit)
        screen.onClose.append(self.close)
        print('[FullNightFitLists] REGISTER %s: %d list(s)' %
              (screen.__class__.__name__, len(self.bindings)))
        self.fit()

    def fit(self):
        if self.bindings:
            self.timer.start(0, True)

    def apply(self):
        for binding in self.bindings[:]:
            component, width, original, callbacks = binding
            instance = getattr(component, 'instance', None)
            try:
                if not isinstance(instance, eListbox) or instance.selectionChanged.get() is not callbacks:
                    _detach(callbacks, self.fit)
                    self.bindings.remove(binding)
                    continue
                if instance.getOrientation() == eListbox.orHorizontal:
                    continue
                row = int(instance.getItemHeight())
                if row <= 0 or original < row:
                    continue
                rem = original % row
                if not rem:
                    continue
                count = _count(component, instance)
                if count is not None and count <= original // row:
                    continue
                up = original + (row - rem)
                down = original - rem
                if _can_grow(self.screen, component, instance, original, up):
                    target, reason = up, 'grow'
                elif down >= row:
                    target, reason = down, 'shrink'
                else:
                    continue
                if instance.size().height() != target:
                    instance.resize(eSize(width, target))
                    print('[FullNightFitLists] %s: %d -> %d (row=%d, %s, count=%s)' %
                          (self.screen.__class__.__name__, original, target, row, reason, count))
            except Exception as exc:
                print('[FullNightFitLists] APPLY skipped: %s' % exc)

    def close(self):
        self.timer.stop()
        for _, _, _, callbacks in self.bindings:
            _detach(callbacks, self.fit)
        self.bindings.clear()
        if self.fit in self.screen.onShown:
            self.screen.onShown.remove(self.fit)
        if self.close in self.screen.onClose:
            self.screen.onClose.remove(self.close)


def install(screen):
    names = getattr(screen, 'skinName', ()) or ()
    if isinstance(names, str):
        names = (names,)
    if screen.__class__.__name__ in EXCLUDED_SCREENS or any(n in EXCLUDED_SCREENS for n in names):
        return
    prior = getattr(screen, '_fullnightListFitter', None)
    if prior is not None:
        prior.close()
    screen._fullnightListFitter = ListFitter(screen)
