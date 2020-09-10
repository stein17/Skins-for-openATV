# -*- coding: utf-8 -*-

#  Movie Reference Converter
#
#  Coded/Modified/Adapted by örlgrey
#  Based on VTi and/or OpenATV image source code
#
#  This code is licensed under the Creative Commons
#  Attribution-NonCommercial-ShareAlike 3.0 Unported
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan
#  Abbott Way, Stanford, California 94305, USA.
#
#  If you think this license infringes any rights,
#  please contact me at ochzoetna@gmail.com

from Components.Converter.Converter import Converter
from Components.Element import cached
from enigma import iServiceInformation, eServiceReference, iPlayableServicePtr

class Steampunk_MovieReference(Converter, object):

    def __init__(self, type):
        Converter.__init__(self, type)

    @cached
    def getText(self):
        service = self.source.service
        if isinstance(service, eServiceReference):
            info = self.source.info
        elif isinstance(service, iPlayableServicePtr):
            info = service.info()
            service = None
        else:
            info = None
        if info is None:
            return ""

        if service is None:
            refstr = info.getInfoString(iServiceInformation.sServiceref)
            path = refstr and eServiceReference(refstr).getPath()
            if path:
                try:
                    fd = open("%s.meta"%(path), "r")
                    refstr = fd.readline().strip()
                    fd.close()
                except:
                    pass
            return refstr
        else:
            return info.getInfoString(service, iServiceInformation.sServiceref)

    text = property(getText)

