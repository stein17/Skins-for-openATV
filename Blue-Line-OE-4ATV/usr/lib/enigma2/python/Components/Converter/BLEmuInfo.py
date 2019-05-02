from Components.Converter.Converter import Converter
from enigma import iServiceInformation, iPlayableService, eTimer, eServiceReference, eEPGCache
from Components.Element import cached
from Tools.Directories import fileExists
from os import path, popen
import re

class BLEmuInfo(Converter, object):
    TEMPERATURE = 1
    EMU = 2
    HOPS = 3
    SYSTEM = 4
    CAID = 5
    PROVID = 6
    ECMPID = 7
    ECMTIME = 8
    ADDRESS = 9

    def __init__(self, type):
        Converter.__init__(self, type)
        self.type = {'Temp': self.TEMPERATURE,
         'Emu': self.EMU,
         'Hops': self.HOPS,
         'System': self.SYSTEM,
         'Caid': self.CAID,
         'Provid': self.PROVID,
         'Ecmpid': self.ECMPID,
         'Ecmtime': self.ECMTIME,
         'Address': self.ADDRESS}[type]
        self.pat_caid = re.compile('CaID (.*),')
        self.DynamicTimer = eTimer()
        self.DynamicTimer.callback.append(self.doSwitch)

    def getCryptName(self, caID):
        caID = int(caID, 16)
        if caID >= 256 and caID <= 511:
            syID = 'Seca Mediaguard'
        elif caID >= 1280 and caID <= 1535:
            syID = 'Viaccess'
        elif caID >= 1536 and caID <= 1791:
            syID = 'Irdeto'
        elif caID >= 2304 and caID <= 2559:
            syID = 'NDS Videoguard'
        elif caID >= 2816 and caID <= 3071:
            syID = 'Conax'
        elif caID >= 3328 and caID <= 3583:
            syID = 'CryptoWorks'
        elif caID >= 3584 and caID <= 3839:
            syID = 'PowerVu'
        elif caID >= 5888 and caID <= 6143:
            syID = 'BetaCrypt'
        elif caID >= 6144 and caID <= 6399:
            syID = 'NagraVision'
        elif caID >= 8704 and caID <= 8959:
            syID = 'CodiCrypt'
        elif caID >= 9728 and caID <= 9983:
            syID = 'EBU Biss'
        elif caID >= 18944 and caID <= 19169:
            syID = 'DreamCrypt'
        elif caID >= 19182 and caID <= 19182:
            syID = 'BulCrypt 1'
        elif caID >= 21760 and caID < 21889:
            syID = 'Griffin'
        elif caID == 21889:
            syID = 'BulCrypt 2'
        elif caID > 21889 and caID <= 22015:
            syID = 'Griffin'
        elif caID >= 41216 and caID <= 41471:
            syID = 'RusCrypt'
        else:
            syID = 'Other'
        return syID

    def hex_str2dec(self, str):
        ret = 0
        try:
            ret = int(re.sub('0x', '', str), 16)
        except:
            pass

        return ret

    def getTemperature(self):
        while True:
            systemp = ''
            cputemp = ''
            try:
                if path.exists('/proc/stb/sensors/temp0/value'):
                    out_line = popen('cat /proc/stb/sensors/temp0/value').readline()
                    systemp = 'Sys Temp : ' + out_line.replace('\n', '') + str('\xc2\xb0') + 'C'
                elif path.exists('/proc/stb/fp/temp_sensor'):
                    out_line = popen('cat /proc/stb/fp/temp_sensor').readline()
                    systemp = 'Board : ' + out_line.replace('\n', '') + str('\xc2\xb0') + 'C'
                if path.exists('/proc/stb/fp/temp_sensor_avs'):
                    out_line2 = popen('cat /proc/stb/fp/temp_sensor_avs').readline()
                    cputemp = 'CPU : ' + out_line2.replace('\n', '') + str('\xc2\xb0') + 'C'
            except:
                pass

            if systemp == '' and cputemp == '':
                return 'No Temp. Sensors Detected'
            if systemp == '':
                return cputemp
            if cputemp == '':
                return systemp
            return systemp + '  -  ' + cputemp

    def getCryptInfo(self):
        service = self.source.service
        info = service and service.info()
        isCrypted = info.getInfo(iServiceInformation.sIsCrypted)
        if isCrypted == 1:
            id_ecm = ''
            caID = ''
            syID = ''
            try:
                file = open('/tmp/ecm.info', 'r')
            except:
                return ''

            while True:
                line = file.readline().strip()
                if line == '':
                    break
                x = line.split(':', 1)
                if x[0] == 'caid':
                    caID = x[1].strip()
                    sysID = self.getCryptName(caID)
                    return sysID
                cellmembers = line.split()
                for x in range(len(cellmembers)):
                    if 'ECM' in cellmembers[x]:
                        if x <= len(cellmembers):
                            caID = cellmembers[x + 3]
                            caID = caID.strip(',;.:-*_<>()[]{}')
                            sysID = self.getCryptName(caID)
                            return sysID
			file.close()
        else:
            return ''

    def getInfos(self, ltype):
        try:
            file = open('/tmp/ecm.info', 'r')
        except:
            return ''

        caid = '0000'
        provid = '000000'
        pid = '0'
        using = ''
        address = ''
        network = ''
        ecmtime = '1'
        ecmtime2 = 'Waiting...'
        source = ''
        hops = '---'
        emun = ''
        protocol = ''
        while True:
            line = file.readline().strip()
            if line == '':
                break
            x = line.split(':', 1)
            mo = self.pat_caid.search(line)
            if mo:
                caid = mo.group(1)
            if x[0] == 'prov':
                y = x[1].strip().split(',')
                provid = y[0]
            if x[0] == 'provid':
                provid = x[1].strip()
            if x[0] == 'caid':
                caid = x[1].strip()
            if x[0] == 'pid':
                pid = x[1].strip()
            if x[0] == 'source':
                source = x[1].strip()
                address = x[1].strip()
                if 'net (cccamd' in address:
                    address = address.lstrip('net (camd').rstrip(')')
                if 'net (newcamd' in address:
                    address = address.lstrip('net (wcamd').rstrip(')')
            if x[0] == 'address':
                address = x[1].strip()
            if x[0] == 'from':
                address = x[1].strip()
            if x[0] == 'using':
                using = x[1].strip()
                using2 = using
                if using == 'CCcam-s2s':
                    using2 = 'CCcam'
            if x[0] == 'ecm time':
                ecmtime = x[1].strip()
                ecmtime2 = ''
            if x[0] == 'hops':
                hops = x[1].strip()
            if x[0] == 'protocol':
                protocol = x[1].strip()
            if x[0] == 'reader':
                reader = x[1].strip()
            if x[0] == 'network':
                network = x[1].strip()
            if ecmtime2 != '':
                x = line.split('--', 1)
                msecIndex = x[0].find('msec')
                if msecIndex is not -1:
                    ecmtime = x[0].strip()
            ecmtime2 = ecmtime
            emun = 'Unknown EMU'
            if protocol != '' and reader != '':
                emun = 'EMU : OsCam'
                if float(ecmtime) >= 1:
                    ecmtime2 = str(ecmtime) + ' s'
                else:
                    ecmtime2 = str(int(float(ecmtime) * 1000)) + ' ms'
            if source != '':
                emun = 'EMU : Wicardd'
                ecmtime = ecmtime.rstrip('ce')
                if int(ecmtime.split()[0]) >= 1000:
                    ecmtime2 = str(float(ecmtime.split()[0]) / 1000) + ' s'
                else:
                    ecmtime2 = str(ecmtime)
            if len(provid) == 8 and using != '' or using == 'SBox':
                emun = 'EMU : SBox'
                if int(ecmtime.split()[0]) >= 1000:
                    ecmtime2 = str(float(ecmtime.split()[0]) / 1000) + ' s'
                else:
                    ecmtime2 = str(ecmtime)
            if len(provid) <= 7 and using != '':
                emun = 'EMU : CCcam'
                if float(ecmtime) >= 1:
                    ecmtime2 = str(ecmtime) + ' s'
                else:
                    ecmtime2 = str(int(float(ecmtime) * 1000)) + ' ms'

        file.close()
        if self.hex_str2dec(caid) == 0:
            return ' '
        elif ltype == self.CAID:
            datadec = int(caid[2:], 16)
            datahex = '0x%0.4X' % datadec
            data = str(datadec) + ' (' + datahex + ')'
            return 'CA ID : ' + data
        elif ltype == self.PROVID:
            datadec = int(provid[2:], 16)
            datahex = '0x%0.6X' % datadec
            data = str(datadec) + ' (' + datahex + ')'
            return 'Prov ID : ' + data
        elif ltype == self.ECMPID:
            datadec = int(pid[2:], 16)
            datahex = '0x%0.4X' % datadec
            data = str(datadec) + ' (' + datahex + ')'
            return 'ECM PID : ' + data
        elif ltype == self.EMU:
            return emun
        elif ltype == self.HOPS:
            return 'Hops : ' + str(hops)
        elif ltype == self.ECMTIME:
            return 'ECM Time : ' + str(ecmtime2)
        elif ltype == self.ADDRESS:
            return 'From : ' + str(address)
        else:
            return ' '

    @cached
    def getText(self):
        self.DynamicTimer.start(500)
        service = self.source.service
        info = service and service.info()
        if not info:
            return ''
        if self.type == self.TEMPERATURE:
            return self.getTemperature()
        if self.type == self.EMU and info.getInfo(iServiceInformation.sIsCrypted) == 1:
            return self.getInfos(self.type)
        if self.type == self.HOPS and info.getInfo(iServiceInformation.sIsCrypted) == 1:
            return self.getInfos(self.type)
        if self.type == self.SYSTEM and info.getInfo(iServiceInformation.sIsCrypted) == 1:
            return 'CA System : ' + str(self.getCryptInfo())
        if self.type == self.CAID and info.getInfo(iServiceInformation.sIsCrypted) == 1:
            return self.getInfos(self.type)
        if self.type == self.PROVID and info.getInfo(iServiceInformation.sIsCrypted) == 1:
            return self.getInfos(self.type)
        if self.type == self.ECMPID and info.getInfo(iServiceInformation.sIsCrypted) == 1:
            return self.getInfos(self.type)
        if self.type == self.ECMTIME and info.getInfo(iServiceInformation.sIsCrypted) == 1:
            return self.getInfos(self.type)
        if self.type == self.ADDRESS and info.getInfo(iServiceInformation.sIsCrypted) == 1:
            return self.getInfos(self.type)
        return ''

    text = property(getText)

    def changed(self, what):
        self.what = what
        Converter.changed(self, what)

    def doSwitch(self):
        self.DynamicTimer.stop()
        Converter.changed(self, self.what)