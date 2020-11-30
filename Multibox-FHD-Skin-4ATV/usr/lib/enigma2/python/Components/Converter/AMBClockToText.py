from Components.Converter.Converter import Converter
from time import localtime, strftime
from Components.Element import cached
from Components.config import config

class AMBClockToText(Converter, object):
    DEFAULT = 0
    WITH_SECONDS = 1
    IN_MINUTES = 2
    DATE = 3
    FORMAT = 4
    AS_LENGTH = 5
    TIMESTAMP = 6
    FULL = 7
    SHORT_DATE = 8
    LONG_DATE = 9
    VFD = 10
    AS_LENGTHHOURS = 11
    AS_LENGTHSECONDS = 12
    FULL_DATE = 13

    def __init__(self, type):
        Converter.__init__(self, type)
        self.fix = ''
        if ';' in type:
            (type, self.fix,) = type.split(';')
        if type == 'WithSeconds':
            self.type = self.WITH_SECONDS
        elif type == 'InMinutes':
            self.type = self.IN_MINUTES
        elif type == 'Date':
            self.type = self.DATE
        elif type == 'AsLength':
            self.type = self.AS_LENGTH
        elif type == 'AsLengthHours':
            self.type = self.AS_LENGTHHOURS
        elif type == 'AsLengthSeconds':
            self.type = self.AS_LENGTHSECONDS
        elif type == 'Timestamp':
            self.type = self.TIMESTAMP
        elif type == 'Full':
            self.type = self.FULL
        elif type == 'ShortDate':
            self.type = self.SHORT_DATE
        elif type == 'LongDate':
            self.type = self.LONG_DATE
        elif type == 'VFD':
            self.type = self.VFD
        elif type == 'FullDate':
            self.type = self.FULL_DATE
        elif 'Format' in type:
            self.type = self.FORMAT
            self.fmt_string = type[7:]
        else:
            self.type = self.DEFAULT



    @cached
    def getText(self):
        time = self.source.time
        if time is None:
            return ''

        def fix_space(string):
            if 'Proportional' in self.fix and t.tm_hour < 10:
                return ' ' + string
            if 'NoSpace' in self.fix:
                return string.lstrip(' ')
            return string

        if self.type == self.IN_MINUTES:
            return ngettext('%d Min', '%d Mins', time / 60) % (time / 60)
        if self.type == self.AS_LENGTH:
            if time < 0:
                return ''
            return '%d:%02d' % (time / 60, time % 60)
        if self.type == self.AS_LENGTHHOURS:
            if time < 0:
                return ''
            return '%d:%02d' % (time / 3600, time / 60 % 60)
        if self.type == self.AS_LENGTHSECONDS:
            if time < 0:
                return ''
            return '%d:%02d:%02d' % (time / 3600, time / 60 % 60, time % 60)
        if self.type == self.TIMESTAMP:
            return str(time)
        t = localtime(time)
        if self.type == self.WITH_SECONDS:
            return _('%02d:%02d:%02d') % (t.tm_hour, t.tm_min, t.tm_sec)
        if self.type == self.DEFAULT:
            return _('%02d:%02d') % (t.tm_hour, t.tm_min)
        if self.type == self.DATE:
            d = _('%A %e %B %Y')
        elif self.type == self.FULL:
            d = _('%a %e/%m  %-H:%M')
        elif self.type == self.SHORT_DATE:
            d = _('%a %e/%m')
        elif self.type == self.LONG_DATE:
            d = _('%A %e %B')
        elif self.type == self.FULL_DATE:
            d = _('%a %e %B %Y')
        elif self.type == self.VFD:
            d = _('%k:%M %e/%m')
        elif self.type == self.FORMAT:
            d = self.fmt_string
        else:
            return '???'
        if config.osd.language.value == 'de_DE':
            t1 = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][t.tm_wday]
            t2 = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'][t.tm_wday]
            m1 = ['Jan', 'Feb', 'Mrz', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'][(t.tm_mon - 1)]
            m2 = ['Januar', 'Februar', u'M\xe4rz', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'][(t.tm_mon - 1)]
            d = d.replace('%a', t1)
            d = d.replace('%A', t2)
            d = d.replace('%b', m1)
            d = d.replace('%B', m2)
        return strftime(d, t)

    text = property(getText)
