# -*- coding: utf-8 -*-
#
# PLiFullNightVerticalChannelNumber
# Channel number converter for OpenATV VerticalEPG piconCh1...piconCh5 sources.
#

from Components.Converter.Converter import Converter
from Components.Element import cached
from enigma import eServiceCenter, eServiceReference


class PLiFullNightVerticalChannelNumber(Converter):
    _number_cache = None

    def __init__(self, type):
        Converter.__init__(self, type)

    @classmethod
    def _build_cache(cls):
        cache = {}
        service_handler = eServiceCenter.getInstance()

        # OpenATV TV bouquet root.
        root = eServiceReference(
            '1:7:1:0:0:0:0:0:0:0:'
            'FROM BOUQUET "bouquets.tv" ORDER BY bouquet'
        )

        bouquet_list = service_handler.list(root)
        if bouquet_list is None:
            cls._number_cache = cache
            return cache

        while True:
            bouquet = bouquet_list.getNext()
            if not bouquet.valid():
                break
            if not (bouquet.flags & eServiceReference.isDirectory):
                continue

            services = service_handler.list(bouquet)
            if services is None:
                continue

            local_number = 0
            while True:
                service = services.getNext()
                if not service.valid():
                    break
                if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker):
                    continue

                local_number += 1

                # Prefer the real OpenATV channel number attached to the
                # service reference. Fall back to bouquet-local order.
                number = 0
                try:
                    number = service.getChannelNum()
                except Exception:
                    number = 0
                if not number:
                    number = local_number

                key = service.toString()
                # Keep the first occurrence if a service exists in several bouquets.
                if key not in cache:
                    cache[key] = number

        cls._number_cache = cache
        return cache

    @cached
    def getText(self):
        service = getattr(self.source, "service", None)
        if not service:
            return ""

        # First try the number carried by the source itself.
        try:
            number = service.getChannelNum()
            if number:
                return str(number)
        except Exception:
            pass

        # VerticalEPG recreates its picon service refs from strings, which can
        # lose the channel-number metadata. Resolve the same reference again
        # from the real bouquet list.
        cache = self.__class__._number_cache
        if cache is None:
            cache = self.__class__._build_cache()

        try:
            number = cache.get(service.toString(), "")
        except Exception:
            number = ""

        return str(number) if number else ""

    text = property(getText)

    def changed(self, what):
        Converter.changed(self, what)
