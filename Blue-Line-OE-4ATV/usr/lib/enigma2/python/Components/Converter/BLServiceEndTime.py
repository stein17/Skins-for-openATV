from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from enigma import iPlayableService, iPlayableServicePtr, iServiceInformation, eTimer, eLabel
from Components.Element import cached, ElementError
from time import localtime, strftime, time, gmtime, asctime
from Components.Sources.Clock import Clock

class BLServiceEndTime(Poll, Converter, object):
    TYPE_ENDTIME = 0

    def __init__(self, type):
        Poll.__init__(self)
        Converter.__init__(self, type)
        if type == 'EndTime':
            self.type = self.TYPE_ENDTIME
        self.poll_enabled = True

    def getSeek(self):
        s = self.source.service
        return s and s.seek()

    @cached
    def getPosition(self):
        seek = self.getSeek()
        if seek is None:
            return
        else:
            pos = seek.getPlayPosition()
            if pos[0]:
                return 0
            return pos[1]

    @cached
    def getLength(self):
        seek = self.getSeek()
        if seek is None:
            return
        else:
            length = seek.getLength()
            if length[0]:
                return 0
            return length[1]

    @cached
    def getText(self):
        seek = self.getSeek()
        if seek is None:
            return ''
        elif self.type == self.TYPE_ENDTIME:
            e = self.length / 90000
            s = self.position / 90000
            return strftime('%H:%M', localtime(time() + (self.length / 90000 - self.position / 90000)))
        else:
            return

    range = 10000
    position = property(getPosition)
    length = property(getLength)
    text = property(getText)

    def changed(self, what):
        cutlist_refresh = what[0] != self.CHANGED_SPECIFIC or what[1] in (iPlayableService.evCuesheetChanged,)
        time_refresh = what[0] == self.CHANGED_POLL or what[0] == self.CHANGED_SPECIFIC and what[1] in (iPlayableService.evCuesheetChanged,)
        if time_refresh:
            self.downstream_elements.changed(what)
