from Components.Converter.Converter import Converter
from os import statvfs
from Components.Element import cached, ElementError
from Components.Converter.Poll import Poll

class AMBDiskSpace(Poll, Converter, object):
    free = 0
    size = 1
    both = 2
    path = 3

    def __init__(self, type):
        Converter.__init__(self, type)
        Poll.__init__(self)
        if type == "free":
            self.type = self.free
        elif type == "size":
            self.type = self.size
        elif type == "both":
            self.type = self.both
        elif type == "path":
            self.type = self.path

        self.poll_interval = 2000
        self.poll_enabled = True


    @cached
    def getText(self):
        service = self.source.service
        if service:
            if self.type == self.free:
                try:
                    stat = statvfs(service.getPath().replace('Latest Recordings', ''))
                    hdd = stat.f_bfree * stat.f_bsize
                    if hdd > 1099511627776:
                        free = float(hdd/1099511627776.0)
                        return '%.2f TB' % free
                    elif hdd > 1073741824:
                        free = float(hdd/1073741824.0)
                        return '%.2f GB' % free
                    elif hdd > 1048576:
                        free = float(hdd/1048576.0)
                        return '%i MB' % free
                except OSError:
                    return 'N/A'

            elif self.type == self.size:
                try:
                    stat = statvfs(service.getPath().replace('Latest Recordings', ''))
                    hddsize = stat.f_blocks * stat.f_bsize
                    if hddsize > 1099511627776:
                        locks = float(hddsize/1099511627776.0)
                        return '(%.2f TB)' % locks
                    elif hddsize > 1073741824:
                        locks = float(hddsize/1073741824.0)
                        return '(%.2f GB)' % locks
                    elif hddsize > 1048576:
                        locks = float(hddsize/1048576.0)
                        return '(%i MB)' % locks
                except OSError:
                    return 'N/A'

            elif self.type == self.both:
                try:
                    stat = statvfs(service.getPath().replace('Latest Recordings', ''))
                    total = stat.f_blocks * stat.f_bsize
                    free = (stat.f_bavail or stat.f_bfree) * stat.f_bsize
                    if total == 0:
                        total = 1
                    percentage = free * 100 / total
                    return ('%s / %s (%d%%) ' + _('free')) % (self.bytes2human(free, 1), self.bytes2human(total, 1), percentage)
                except OSError:
                    return 'N/A'

            elif self.type == self.path:
                if "." in str(service.getPath()) or "@" in str(service.getPath()) or "Latest Recordings" in str(service.getPath()):
                    return service.getPath().rsplit('/', 1)[0]
                else:
                    return service.getPath().replace('/Latest Recordings', '')

        return ""

    text = property(getText)

    def changed(self, what):
        if what[0] is self.CHANGED_SPECIFIC:
            Converter.changed(self, what)
        elif what[0] is self.CHANGED_POLL:
            self.downstream_elements.changed(what)

    def bytes2human(self, n, digits = 2):
        symbols = ('KB', 'MB', 'GB', 'TB', 'PB')
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i + 1) * 10

        for s in reversed(symbols):
            if n >= prefix[s]:
                if digits > 0:
                    value = round(float(n) / prefix[s], digits)
                else:
                    value = n / prefix[s]
                return '%s %s' % (value, s)

        return '%s B' % n
