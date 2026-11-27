from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from Components.Element import cached
from enigma import iServiceInformation


class PLiWQHDFullNightVideoInfo(Poll, Converter):
    """Codec, decoded video dimensions and frame rate of currently playing service."""

    def __init__(self, type):
        Converter.__init__(self, type)
        Poll.__init__(self)
        self.poll_interval = 500
        self.poll_enabled = True

    @cached
    def getText(self):
        service = self.source.service
        if not service:
            return ""
        try:
            info = service.info()
            if not info:
                return ""

            def number(key):
                field = getattr(iServiceInformation, key, None)
                if field is None:
                    return -1
                value = info.getInfo(field)
                return value if isinstance(value, int) and value >= 0 else -1

            # Video codec identifiers are image-dependent; unsupported types
            # are deliberately omitted rather than displayed incorrectly.
            codec_id = number("sVideoType")
            codec = {0: "MPEG-2", 1: "H.264", 2: "H.263", 3: "VC-1",
                     4: "MPEG-4", 5: "VP8", 6: "VP9", 7: "H.265"}.get(codec_id, "")
            width = number("sVideoWidth")
            height = number("sVideoHeight")
            fps_raw = number("sFrameRate")
            pieces = []
            if codec:
                pieces.append(codec)
            if width > 0 and height > 0:
                pieces.append("%d x %d" % (width, height))
            if 1000 <= fps_raw <= 240000:
                fps = fps_raw / 1000.0
                pieces.append("%g fps" % fps)
            return "  |  ".join(pieces)
        except Exception:
            return ""

    text = property(getText)
