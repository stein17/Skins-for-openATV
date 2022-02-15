from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.Converter.Poll import Poll
import process
from urllib.request import urlopen
from urllib.parse import quote
import json
import re
import os
import glob
from time import time
# import time
import json, urllib
from Tools.LoadPixmap import LoadPixmap
from os import system, path, popen, remove
from datetime import datetime

myipdata = '/tmp/myipdata.txt'
myipfile = "/tmp/myip.txt"
myflagfile = "/tmp/myflag.png"
novpnfile = '/usr/share/enigma2/BlueAccents-HD/skinparts/novpn.txt'
isvpnfile = '/usr/share/enigma2/BlueAccents-HD/skinparts/isvpn.txt'
myipdataupdatepause = 300


# in seconds


def del_myipfiles():
    if os.path.isfile(myipfile):
        os.remove(myipfile)


def del_myflagfile():
    if os.path.exists(myflagfile):
        os.remove(myflagfile)


def del_myipdata():
    if os.path.exists(myipdata):
        os.remove(myipdata)


# Logfile erstellen fuer ablauf
def write_log(msg):
    with open("/tmp/mylog.txt", "a") as log:
        log.write(datetime.now().strftime("%Y/%d/%m, %H:%M:%S") + ": " + msg + "\n")


def get_myipdata():
    try:
        if not os.path.exists(myipdata) or time() - os.path.getmtime(r"%s" % myipdata) > myipdataupdatepause:
            url = "http://ip-api.com/json/"
            data = json.load(urllib.request.urlopen(url))
            json.dump(data, open(myipdata, 'w'))
            #write_log("json url ip contry")
        # hier in logfile schreiben

        else:
            data = json.loads(open(myipdata, 'r').read())

        country = data['countryCode']
        ip = data['query']


    except:

        country = ip = None

    return country, ip


del_myipfiles()
del_myflagfile()
del_myipdata()


class BlueASambaVpnIp_converter(Poll, Converter, object):

    def __init__(self, type):
        Converter.__init__(self, type)
        self.type = type
        Poll.__init__(self)
        self.poll_interval = 10000
        self.poll_enabled = True

    @cached
    def getBoolean(self):
        p = process.ProcessList()
        name = ""

        if self.type == 'samba':
            name = str(p.named('smbd')).strip('[]')
        elif self.type == 'vpn':
            name = str(p.named('openvpn')).strip('[]')
            country, ip = get_myipdata()
            if name and country and ip:
                ip = ip.split('.')[0] + '.'
                if os.path.exists(novpnfile):
                    novpn = open(novpnfile, 'r').readlines()
                    for line in novpn:
                        if not line.startswith('#') and (country in line or line.startswith(ip)):
                            name = ""

                            break
                if os.path.exists(isvpnfile):
                    isvpn = open(isvpnfile, 'r').readlines()
                    for line in isvpn:
                        if not line.startswith('#') and (country in line or line.startswith(ip)):
                            name = "ok"

                            break
        if name:
            return True
        return False

    @cached
    def getText(self):
        ret = "---.---.---.---"
        if 'n+' in self.type:
            type = self.type[2:]
            name = type + ': '
        # open("/tmp/3u-VPN-3.txt", "w").write(ablauf)
        elif 'c+' in self.type:
            type = self.type[2:]
            name = ''
        else:
            type = self.type
            name = ''

        if type == 'myip':
            # hier kommen wir rein
            country, ip = get_myipdata()
            # hier wird die funktion aufgerufen fuer ip und country holen

            if country and ip:

                if 'c+' in self.type:
                    ip = '(%s) ' % country + ip

                ip = ip + '|' + country

                if not os.path.exists(myipfile) or not os.path.exists(myflagfile) or not open(myipfile,
                                                                                              'r').readline().replace(
                    '\n', '').endswith(country):
                    os.system('wget -T 1 -O %s -q http://flags.fmcdn.net/data/flags/small/%s.png' % (
                        myflagfile, country.lower()))
                    #write_log("flag")
                if not os.path.exists(myipfile) or not ip in open(myipfile, 'r').readline():
                    f = open(myipfile, 'w')
                    f.write(ip)
                    f.close()

            else:
                del_myflagfile()

                if not os.path.exists(myipfile) or time() - os.path.getmtime(r"%s" % myipfile) > myipdataupdatepause:
                    p = os.system('wget -T 1 -O %s -q http://ipecho.net/plain' % myipfile)
                    if p:
                        p = os.system('wget -T 1 -O %s -q http://icanhazip.com' % myipfile)
                    if p:
                        del_myipfiles()

            if os.path.exists(myipfile):
                ret = name + open(myipfile, 'r').readline().replace('\n', '').split('|')[0]

            else:
                ret = 'ip server error'
        else:
            p = os.popen('ip address show').readlines()

            for line in p:
                if 'inet' in line and not 'inet6' in line and type in line:
                    ret = name + line.split()[1].split('/')[0]
                    break

        return ret

    @cached
    def getPixmap(self):
        if self.type == 'flag' and os.path.exists(myflagfile):
            return LoadPixmap(myflagfile)
        #write_log("ende ")
        return None

    pixmap = property(getPixmap)
    boolean = property(getBoolean)
    text = property(getText)
