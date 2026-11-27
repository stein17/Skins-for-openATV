"""Content-sized FullNight message boxes using native text measurement and list rows."""

from enigma import ePoint, eSize, getDesktop


def geometry(measured, rows, row_height, scale=1):
    top, gap, margin, limit = (round(n * scale) for n in (84, 18, 24, 480))
    icon_height = round(53 * scale)
    minimum_rows = min(rows, 2)
    text_limit = limit - top - margin - (gap + minimum_rows * row_height if rows else 0)
    text_height = min(max(measured, round(30 * scale)), text_limit)
    content_bottom = top + max(text_height, icon_height)
    list_top = content_bottom + gap
    visible = min(rows, max(1, (limit - list_top - margin) // row_height)) if rows else 0
    height = list_top + visible * row_height + margin if rows else content_bottom + margin
    return text_height, list_top, visible * row_height, height


def fit(dialog):
    previous = getattr(dialog, "_fullNightListFitter", None)
    if previous:
        previous.close()
        if previous.close in dialog.onClose:
            dialog.onClose.remove(previous.close)
        del dialog._fullNightListFitter
    text = dialog["text"].instance
    choices = dialog["list"].instance
    width = dialog.instance.size().width()
    scale = width / 840
    rows = len(dialog.list or ())
    row_height = max(1, choices.getItemHeight())
    text_height, list_top, list_height, height = geometry(text.calculateSize().height(), rows, row_height, scale)
    text.resize(eSize(text.size().width(), text_height))
    choices.move(ePoint(choices.position().x(), list_top))
    choices.resize(eSize(choices.size().width(), list_height))
    desktop = getDesktop(0).size()
    dialog.instance.resize(eSize(width, height))
    dialog.instance.move(ePoint((desktop.width() - width) // 2, (desktop.height() - height) // 2))
