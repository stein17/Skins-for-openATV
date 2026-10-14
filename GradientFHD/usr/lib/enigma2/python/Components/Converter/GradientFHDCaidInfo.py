# -*- coding: utf-8 -*-
#
#<convert type="xxxxCaidInfo">Server: %S * CAID: %C * ECM: %T</convert>
#<convert type="xxxxCaidInfo">OSCam: %K %v * CAID: %C * ECM: %T</convert>
#<convert type="xxxxCaidInfo">OSCam: %K %v * Server: %S * CAID: %C * ECM: %T</convert>
#
# =============================================================================
#  DEUTSCH / GERMAN
# =============================================================================
#  SoftCam-Info Converter for Enigma2 Skins
#
#  Copyright (c) 2026  @stein17
#
#  Freeware:
#  Dieses Projekt ist Freeware. Die private Nutzung ist erlaubt.
#  Anpassungen für eigene Skins/Setups (z.B. OpenATV/Enigma2) sind ausdrücklich
#  erlaubt.
#
#  Bedingungen:
#  1) Dieser Copyright-/Lizenz-Header muss in allen Kopien und abgeleiteten
#     Versionen vollständig erhalten bleiben und darf nicht entfernt oder
#     unkenntlich gemacht werden.
#  2) Eine Weitergabe (unverändert oder geändert) ist erlaubt, sofern dieser
#     Header erhalten bleibt und die ursprünglichen Urheber genannt werden.
#  3) Eine kommerzielle Nutzung (Verkauf, Paywall, bezahlte Images/Feeds,
#     kommerzielle Bundles) ist ohne vorherige schriftliche Zustimmung der
#     Urheber nicht gestattet.
#
#  Haftungsausschluss:
#  Die Software wird „wie sie ist“ bereitgestellt, ohne jegliche Garantie.
#  Die Nutzung erfolgt auf eigene Gefahr. Für Schäden oder Datenverlust wird
#  keine Haftung übernommen.
#
#
#  ENGLISH
# =============================================================================
#  SoftCam-Info Converter for Enigma2 Skins
#
#  Copyright (c) 2026  @stein17
#
#  Freeware:
#  This project is freeware. Private use is permitted.
#  Modifications for your own skins/setups (e.g. OpenATV/Enigma2) are explicitly
#  allowed.
#
#  Conditions:
#  1) This copyright/license header must be kept fully intact in all copies and
#     derivative works and must not be removed or obscured.
#  2) Redistribution (modified or unmodified) is permitted as long as this header
#     is retained and the original authors are credited.
#  3) Commercial use (sale, paywall, paid images/feeds, commercial bundles) is
#     not permitted without prior written consent from the authors.
#
#  Disclaimer:
#  This software is provided “as is”, without warranty of any kind.
#  Use at your own risk. The authors are not liable for any damages or data loss.
# =============================================================================
from Components.Converter.Converter import Converter
from enigma import iServiceInformation
from Tools.Directories import fileExists
from Components.Element import cached
from Components.Converter.Poll import Poll
import os
import re
import time
import subprocess
import threading
try:
    from urllib.request import urlopen
except:
    urlopen = None
info = {}
old_ecm_mtime = None

# Shared softcam cache. Thread workers never touch Enigma2 widgets/converters.
_SOFTCAM_LOCK = threading.Lock()
_SOFTCAM_STATE = {'kind': '', 'version': '', 'short': '', 'checked': 0.0, 'running': False}

def _softcam_find_running():
    """Find an actual running softcam using procfs, not an installed package list."""
    try:
        pids = sorted((p for p in os.listdir('/proc') if p.isdigit()), key=int)
    except OSError:
        return None
    known = ('oscam', 'ncam', 'cccam', 'mgcamd', 'gbox', 'scam')
    for pid in pids:
        try:
            with open('/proc/%s/cmdline' % pid, 'rb') as f:
                args = [x.decode('utf-8', 'replace') for x in f.read(8192).split(b'\0') if x]
            if not args:
                continue
            exe = args[0]
            name = os.path.basename(exe).lower()
            if not (name.startswith(('oscam', 'ncam', 'cccam', 'mgcamd', 'gbox', 'scam'))):
                continue
            # Prefer the process's exact executable, not a similarly named installed binary.
            actual = os.path.realpath('/proc/%s/exe' % pid)
            if os.path.isfile(actual):
                exe = actual
            return (exe, name, args)
        except (OSError, ValueError):
            continue
    return None

def _softcam_httpport(conf):
    """Read only the [webif] section; OSCam's +port TLS syntax is deliberately skipped."""
    section = ''
    try:
        with open(conf, 'r') as f:
            for raw in f:
                line = raw.split('#', 1)[0].split(';', 1)[0].strip()
                if line.startswith('[') and line.endswith(']'):
                    section = line.lower()
                elif section == '[webif]' and '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip().lower() == 'httpport':
                        value = value.strip()
                        if value.isdigit() and 0 < int(value) < 65536:
                            return value
    except OSError:
        pass
    return ''

def _softcam_title(port):
    if not port or urlopen is None:
        return ''
    try:
        with urlopen('http://127.0.0.1:%s/status.html' % port, timeout=0.7) as response:
            html = response.read(16384).decode('utf-8', 'ignore')
        match = re.search(r'<title>\s*([^<]+?)\s*</title>', html, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            if re.search(r'\b(OSCam|NCam|CCcam|Mgcamd|Gbox|Scam)\b', title, re.IGNORECASE):
                return title
    except Exception:
        pass
    return ''

def _softcam_version(exe, hint):
    if not exe or not os.path.isfile(exe):
        return hint
    for arg in ('-V', '-v', '--version'):
        try:
            out = subprocess.check_output([exe, arg], stderr=subprocess.STDOUT, timeout=0.8).decode('utf-8', 'ignore')
            m = re.search(r'(OSCam\s+[^\r\n]+|NCam\s+[^\r\n]+|CCcam\s+[^\r\n]+|Mgcamd\s+[^\r\n]+|Gbox\s+[^\r\n]+|Scam\s+[^\r\n]+)', out, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        except Exception:
            pass
    return hint

def _softcam_worker():
    kind = version = short = ''
    try:
        found = _softcam_find_running()
        if found:
            exe, name, args = found
            if name.startswith('oscam'):
                family = 'OSCam'
                suffix = name[5:].lstrip('-_')
                kind = suffix.upper() if suffix else ''
            elif name.startswith('ncam'):
                family = 'NCam'
                kind = name[4:].lstrip('-_').upper()
            else:
                family = {'cccam': 'CCcam', 'mgcamd': 'Mgcamd', 'gbox': 'Gbox', 'scam': 'Scam'}.get(name.split('-')[0], name)
                kind = ''
            confdir = ''
            for i, arg in enumerate(args):
                if arg == '--config-dir' and i + 1 < len(args):
                    confdir = args[i + 1]
                    break
                if arg.startswith('--config-dir='):
                    confdir = arg.partition('=')[2]
                    break
            if confdir and family in ('OSCam', 'NCam'):
                conf = os.path.join(confdir, 'oscam.conf' if family == 'OSCam' else 'ncam.conf')
                if family == 'NCam' and not os.path.isfile(conf):
                    conf = os.path.join(confdir, 'oscam.conf')
                version = _softcam_title(_softcam_httpport(conf))
            if not version:
                version = _softcam_version(exe, family)
            short = re.sub(r'^(OSCam|NCam)\s*', '', version, flags=re.IGNORECASE).strip()
            if kind == 'SMOD':
                m = re.search(r'rsvn\s*([0-9]+)|\br\s*([0-9]{4,})\b', short, re.IGNORECASE)
                if m:
                    short = 'SMOD ' + next(x for x in m.groups() if x)
    except Exception:
        pass
    finally:
        with _SOFTCAM_LOCK:
            _SOFTCAM_STATE.update(kind=kind, version=version, short=short, checked=time.monotonic(), running=False)


class GradientFHDCaidInfo(Poll, Converter, object):
    CAID = 0
    PID = 1
    PROV = 2
    ALL = 3
    IS_NET = 4
    IS_EMU = 5
    CRYPT = 6
    BETA = 7
    CONAX = 8
    CRW = 9
    DRE = 10
    IRD = 11
    NAGRA = 12
    NDS = 13
    SECA = 14
    VIA = 15
    BETA_C = 16
    CONAX_C = 17
    CRW_C = 18
    DRE_C = 19
    IRD_C = 20
    NAGRA_C = 21
    NDS_C = 22
    SECA_C = 23
    VIA_C = 24
    BISS = 25
    BISS_C = 26
    EXS = 27
    EXS_C = 28
    HOST = 29
    DELAY = 30
    FORMAT = 31
    CRYPT2 = 32
    CRD = 33
    CRDTXT = 34
    SHORT = 35
    my_interval = 1000

    def __init__(self, type):
        Poll.__init__(self)
        Converter.__init__(self, type)
        if type == 'CAID':
            self.type = self.CAID
        elif type == 'PID':
            self.type = self.PID
        elif type == 'ProvID':
            self.type = self.PROV
        elif type == 'Delay':
            self.type = self.DELAY
        elif type == 'Host':
            self.type = self.HOST
        elif type == 'Net':
            self.type = self.IS_NET
        elif type == 'Emu':
            self.type = self.IS_EMU
        elif type == 'CryptInfo':
            self.type = self.CRYPT
        elif type == 'CryptInfo2':
            self.type = self.CRYPT2
        elif type == 'BetaCrypt':
            self.type = self.BETA
        elif type == 'ConaxCrypt':
            self.type = self.CONAX
        elif type == 'CrwCrypt':
            self.type = self.CRW
        elif type == 'DreamCrypt':
            self.type = self.DRE
        elif type == 'ExsCrypt':
            self.type = self.EXS
        elif type == 'IrdCrypt':
            self.type = self.IRD
        elif type == 'NagraCrypt':
            self.type = self.NAGRA
        elif type == 'NdsCrypt':
            self.type = self.NDS
        elif type == 'SecaCrypt':
            self.type = self.SECA
        elif type == 'ViaCrypt':
            self.type = self.VIA
        elif type == 'BetaEcm':
            self.type = self.BETA_C
        elif type == 'ConaxEcm':
            self.type = self.CONAX_C
        elif type == 'CrwEcm':
            self.type = self.CRW_C
        elif type == 'DreamEcm':
            self.type = self.DRE_C
        elif type == 'ExsEcm':
            self.type = self.EXS_C
        elif type == 'IrdEcm':
            self.type = self.IRD_C
        elif type == 'NagraEcm':
            self.type = self.NAGRA_C
        elif type == 'NdsEcm':
            self.type = self.NDS_C
        elif type == 'SecaEcm':
            self.type = self.SECA_C
        elif type == 'ViaEcm':
            self.type = self.VIA_C
        elif type == 'BisCrypt':
            self.type = self.BISS
        elif type == 'BisEcm':
            self.type = self.BISS_C
        elif type == 'Crd':
            self.type = self.CRD
        elif type == 'CrdTxt':
            self.type = self.CRDTXT
        elif type == 'Short':
            self.type = self.SHORT
        elif type == 'Default' or type == '' or type == None or type == '%' :
            self.type = self.ALL
        else:
            self.type = self.FORMAT
            self.sfmt = type[:]
        self.systemTxtCaids = {'26': 'BiSS',
         '01': 'Seca Mediaguard',
         '06': 'Irdeto',
         '17': 'BetaCrypt',
         '05': 'Viacces',
         '18': 'Nagravision',
         '09': 'NDS-Videoguard',
         '0B': 'Conax',
         '0D': 'Cryptoworks',
         '4A': 'DRE-Crypt',
         '27': 'ExSet',
         '0E': 'PowerVu',
         '22': 'Codicrypt',
         '07': 'DigiCipher',
         '56': 'Verimatrix',
         '7B': 'DRE-Crypt',
         'A1': 'Rosscrypt'}
        self.systemCaids = {'26': 'BiSS',
         '01': 'SEC',
         '06': 'IRD',
         '17': 'BET',
         '05': 'VIA',
         '18': 'NAG',
         '09': 'NDS',
         '0B': 'CON',
         '0D': 'CRW',
         '27': 'EXS',
         '7B': 'DRE',
         '4A': 'DRE'}
        return

    @cached
    def getBoolean(self):
        service = self.source.service
        info = service and service.info()
        if not info:
            return False
        else:
            caids = info.getInfoObject(iServiceInformation.sCAIDs)
            if caids:
                if self.type == self.SECA:
                    for caid in caids:
                        if ('%0.4X' % int(caid))[:2] == '01':
                            return True

                    return False
                if self.type == self.BETA:
                    for caid in caids:
                        if ('%0.4X' % int(caid))[:2] == '17':
                            return True

                    return False
                if self.type == self.CONAX:
                    for caid in caids:
                        if ('%0.4X' % int(caid))[:2] == '0B':
                            return True

                    return False
                if self.type == self.CRW:
                    for caid in caids:
                        if ('%0.4X' % int(caid))[:2] == '0D':
                            return True

                    return False
                if self.type == self.DRE:
                    for caid in caids:
                        if ('%0.4X' % int(caid))[:2] == '7B' or ('%0.4X' % int(caid))[:2] == '4A':
                            return True

                    return False
                if self.type == self.EXS:
                    for caid in caids:
                        if ('%0.4X' % int(caid))[:2] == '27':
                            return True

                if self.type == self.NAGRA:
                    for caid in caids:
                        if ('%0.4X' % int(caid))[:2] == '18':
                            return True

                    return False
                if self.type == self.NDS:
                    for caid in caids:
                        if ('%0.4X' % int(caid))[:2] == '09':
                            return True

                    return False
                if self.type == self.IRD:
                    for caid in caids:
                        if ('%0.4X' % int(caid))[:2] == '06':
                            return True

                    return False
                if self.type == self.VIA:
                    for caid in caids:
                        if ('%0.4X' % int(caid))[:2] == '05':
                            return True

                    return False
                if self.type == self.BISS:
                    for caid in caids:
                        if ('%0.4X' % int(caid))[:2] == '26':
                            return True

                    return False
                self.poll_interval = self.my_interval
                self.poll_enabled = True
                ecm_info = self.ecmfile()
                if ecm_info:
                    caid = ('%0.4X' % int(ecm_info.get('caid', ''), 16))[:2]
                    if self.type == self.SECA_C:
                        if caid == '01':
                            return True
                        return False
                    if self.type == self.BETA_C:
                        if caid == '17':
                            return True
                        return False
                    if self.type == self.CONAX_C:
                        if caid == '0B':
                            return True
                        return False
                    if self.type == self.CRW_C:
                        if caid == '0D':
                            return True
                        return False
                    if self.type == self.DRE_C:
                        if caid == '4A' or caid == '7B':
                            return True
                        return False
                    if self.type == self.EXS_C:
                        if caid == '27':
                            return True
                        return False
                    if self.type == self.NAGRA_C:
                        if caid == '18':
                            return True
                        return False
                    if self.type == self.NDS_C:
                        if caid == '09':
                            return True
                        return False
                    if self.type == self.IRD_C:
                        if caid == '06':
                            return True
                        return False
                    if self.type == self.VIA_C:
                        if caid == '05':
                            return True
                        return False
                    if self.type == self.BISS_C:
                        if caid == '26':
                            return True
                        return False
                    reader = ecm_info.get('reader', None)
                    using = ecm_info.get('using', '')
                    source = ecm_info.get('source', '')
                    if self.type == self.CRD:
                        if source == 'sci':
                            return True
                        if source != 'cache' and source != 'net' and source.find('emu') == -1:
                            return True
                        return False
                    source = ecm_info.get('source', '')
                    if self.type == self.IS_EMU:
                        return using == 'emu' or source == 'emu' or source == 'card' or reader == 'emu' or source.find('card') > -1 or source.find('emu') > -1 or source.find('biss') > -1 or source.find('cache') > -1
                    source = ecm_info.get('source', '')
                    if self.type == self.IS_NET:
                        if using == 'CCcam-s2s':
                            return 1
                        if source != 'cache' and source == 'net' and source.find('emu') == -1:
                            return True
                    else:
                        return False
            return False

    boolean = property(getBoolean)

    @cached
    def getText(self):
        textvalue = ''
        server = ''
        service = self.source.service
        if service:
            if self.type == self.CRYPT2:
                self.poll_interval = self.my_interval
                self.poll_enabled = True
                ecm_info = self.ecmfile()
                if fileExists('/tmp/ecm.info'):
                    try:
                        caid = '%0.4X' % int(ecm_info.get('caid', ''), 16)
                        return '%s' % self.systemTxtCaids.get(caid[:2])
                    except:
                        return 'nondecode'

                else:
                    return 'nondecode'
        if service:
            info = service and service.info()
            if info:
                if info.getInfoObject(iServiceInformation.sCAIDs):
                    self.poll_interval = self.my_interval
                    self.poll_enabled = True
                    ecm_info = self.ecmfile()
                    if ecm_info:
                        caid = '%0.4X' % int(ecm_info.get('caid', ''), 16)
                        if self.type == self.CAID:
                            return caid
                        if self.type == self.CRYPT:
                            return '%s' % self.systemTxtCaids.get(caid[:2].upper())
                        try:
                            pid = '%0.4X' % int(ecm_info.get('pid', ''), 16)
                        except:
                            pid = ''

                        if self.type == self.PID:
                            return pid
                        try:
                            prov = '%0.6X' % int(ecm_info.get('prov', ''), 16)
                        except:
                            prov = ecm_info.get('prov', '')

                        if self.type == self.PROV:
                            return prov
                        if ecm_info.get('ecm time', '').find('msec') > -1:
                            ecm_time = ecm_info.get('ecm time', '')
                        else:
                            ecm_time = ecm_info.get('ecm time', '').replace('.', '').lstrip('0')
                        if self.type == self.DELAY:
                            return ecm_time
                        protocol = ecm_info.get('protocol', '')
                        port = ecm_info.get('port', '')
                        source = ecm_info.get('source', '')
                        server = ecm_info.get('server', '')
                        hops = ecm_info.get('hops', '')
                        system = ecm_info.get('system', '')
                        provider = ecm_info.get('provider', '')
                        reader = ecm_info.get('reader', '')
                        if self.type == self.CRDTXT:
                            info_card = 'False'
                            if source == 'sci':
                                info_card = 'True'
                            if source != 'cache' and source != 'net' and source.find('emu') == -1:
                                info_card = 'True'
                            return info_card
                        if self.type == self.HOST:
                            return server
                        if self.type == self.FORMAT:
                            textvalue = ''
                            params = self.sfmt.split(' ')
                            for param in params:
                                if param != '':
                                    before_len = len(textvalue)
                                    if param[0] != '%':
                                        textvalue += param

                                    elif param == '%S':
                                        # Prefer the local reader when this ECM was decoded
                                        # by an internal card, never a stale network server.
                                        reader_name = (ecm_info.get('reader', '') or '').strip()
                                        ecm_from = (ecm_info.get('from', '') or '').strip().lower()
                                        ecm_source = (ecm_info.get('source', '') or '').strip().lower()
                                        ecm_protocol = (ecm_info.get('protocol', '') or '').strip().lower()
                                        local_card = (
                                            ecm_from.startswith('local') or
                                            ecm_source == 'sci' or
                                            ecm_protocol == 'internal'
                                        )
                                        if local_card:
                                            if reader_name:
                                                textvalue += '%s (local)' % reader_name
                                            elif (caid or '').upper() == '1843':
                                                textvalue += 'HD+ (local)'
                                            else:
                                                textvalue += 'local'
                                        elif reader_name:
                                            # The actual ECM reader is more reliable than
                                            # the upstream host name stored in "from".
                                            textvalue += reader_name
                                        elif server and server.strip().lower() != 'local':
                                            textvalue += server
                                        else:
                                            textvalue += 'unknown'

                                    elif param == '%H':
                                        textvalue += hops
                                    elif param == '%SY':
                                        textvalue += system
                                    elif param == '%PV':
                                        textvalue += provider
                                    elif param == '%SP':
                                        textvalue += port
                                    elif param == '%PR':
                                        textvalue += protocol
                                    elif param == '%C':
                                        textvalue += caid
                                    elif param == '%P':
                                        textvalue += pid
                                    elif param == '%p':
                                        textvalue += prov
                                    elif param == '%O':
                                        textvalue += source
                                    elif param == '%R':
                                        textvalue += reader
                                    elif param == '%T':
                                        textvalue += ecm_time
                                    elif param == '%V':
                                        textvalue += self.getSoftcamVersion()
                                    elif param == '%v':
                                        textvalue += self.getSoftcamVersionShort()
                                    elif param == '%K':
                                        textvalue += self.getSoftcamKind()
                                    elif param == '%t':
                                        textvalue += '\t'
                                    elif param == '%n':
                                        textvalue += '\n'
                                    elif param[1:].isdigit():
                                        textvalue = textvalue.ljust(len(textvalue) + int(param[1:]))
                                    if len(textvalue) > 0 and len(textvalue) != before_len:
                                        if textvalue[-1] != '\t' and textvalue[-1] != '\n':
                                            textvalue += ' '

                            return textvalue[:-1]
                        if self.type == self.ALL:
                            if source == 'emu':
                                textvalue = '%s - %s (Prov: %s, Caid: %s)' % (source,
                                 self.systemTxtCaids.get(caid[:2]),
                                 prov,
                                 caid)
                            elif reader != '' and source == 'net' and port != '':
                                textvalue = '%s - Prov: %s, Caid: %s, Reader: %s, %s (%s:%s) - %s' % (source,
                                 prov,
                                 caid,
                                 reader,
                                 protocol,
                                 server,
                                 port,
                                 ecm_time.replace('msec', 'ms'))
                            elif reader != '' and source == 'net':
                                textvalue = '%s - Prov: %s, Caid: %s, Reader: %s, %s (%s) - %s' % (source,
                                 prov,
                                 caid,
                                 reader,
                                 protocol,
                                 server,
                                 ecm_time.replace('msec', 'ms'))
                            elif reader != '' and source != 'net':
                                textvalue = '%s - Prov: %s, Caid: %s, Reader: %s, %s (local) - %s' % (source,
                                 prov,
                                 caid,
                                 reader,
                                 protocol,
                                 ecm_time.replace('msec', 'ms'))
                            elif server == '' and port == '' and protocol != '':
                                textvalue = '%s - Prov: %s, Caid: %s, %s - %s' % (source,
                                 prov,
                                 caid,
                                 protocol,
                                 ecm_time.replace('msec', 'ms'))
                            elif server == '' and port == '' and protocol == '':
                                textvalue = '%s - Prov: %s, Caid: %s - %s' % (source,
                                 prov,
                                 caid,
                                 ecm_time.replace('msec', 'ms'))
                            else:
                                try:
                                    textvalue = '%s - Prov: %s, Caid: %s, %s (%s:%s) - %s' % (source,
                                     prov,
                                     caid,
                                     protocol,
                                     server,
                                     port,
                                     ecm_time.replace('msec', 'ms'))
                                except:
                                    pass

                        if self.type == self.SHORT:
                            if source == 'emu':
                                textvalue = '%s - %s (Prov: %s, Caid: %s)' % (source,
                                 self.systemTxtCaids.get(caid[:2]),
                                 prov,
                                 caid)
                            elif server == '' and port == '':
                                textvalue = '%s - Prov: %s, Caid: %s - %s' % (source,
                                 prov,
                                 caid,
                                 ecm_time.replace('msec', 'ms'))
                            else:
                                try:
                                    textvalue = '%s - Prov: %s, Caid: %s, %s:%s - %s' % (source,
                                     prov,
                                     caid,
                                     server,
                                     port,
                                     ecm_time.replace('msec', 'ms'))
                                except:
                                    pass

                    elif self.type == self.ALL or self.type == self.SHORT or self.type == self.FORMAT and self.sfmt.count('%') > 3:
                        textvalue = 'No parse cannot emu'
                elif self.type == self.ALL or self.type == self.SHORT or self.type == self.FORMAT and self.sfmt.count('%') > 3:
                    textvalue = 'Free-to-air'
        return textvalue

    text = property(getText)

    # Softcam metadata are shared across converter instances and collected off the GUI thread.
    # ECM data and CAID formatting remain synchronous and unchanged.
    def _softcam_snapshot(self):
        now = time.monotonic()
        with _SOFTCAM_LOCK:
            snapshot = dict(_SOFTCAM_STATE)
            if not snapshot['running'] and now - snapshot['checked'] >= 60:
                _SOFTCAM_STATE['running'] = True
                t = threading.Thread(target=_softcam_worker, name='PLiModSoftcamInfo', daemon=True)
                t.start()
        return snapshot

    def getSoftcamKind(self):
        return self._softcam_snapshot()['kind']

    def getSoftcamVersion(self):
        return self._softcam_snapshot()['version']

    def getSoftcamVersionShort(self):
        return self._softcam_snapshot()['short']

    def ecmfile(self):
        global info
        global old_ecm_mtime
        ecm = None
        service = self.source.service
        if service:
            try:
                st = os.stat('/tmp/ecm.info')
                if st.st_size == 0:
                    old_ecm_mtime = None
                    info = {}
                    return info
                # Nanosecond timestamp + size + inode protect against rapid rewrites.
                ecm_signature = (getattr(st, 'st_mtime_ns', int(st.st_mtime * 1e9)),
                                 st.st_size, st.st_ino)
                if ecm_signature == old_ecm_mtime:
                    return info
                with open('/tmp/ecm.info', 'r') as ecmf:
                    ecm = ecmf.readlines()
                old_ecm_mtime = ecm_signature
                # A new ECM file must never inherit values from the previous ECM.
                info = {}
            except:
                old_ecm_mtime = None
                info = {}
                return info

            if ecm:
                for line in ecm:
                    x = line.lower().find('msec')
                    if x != -1:
                        info['ecm time'] = line[0:x + 4]
                    else:
                        item = line.split(':', 1)
                        if len(item) > 1:
                            if item[0] == 'Provider':
                                item[0] = 'prov'
                                item[1] = item[1].strip()[2:]
                            elif item[0] == 'ECM PID':
                                item[0] = 'pid'
                            elif item[0] == 'response time':
                                info['source'] = 'net'
                                it_tmp = item[1].strip().split(' ')
                                info['ecm time'] = '%s msec' % it_tmp[0]
                                y = it_tmp[-1].find('[')
                                if y != -1:
                                    info['server'] = it_tmp[-1][:y]
                                    info['protocol'] = it_tmp[-1][y + 1:-1]
                                y = it_tmp[-1].find('(')
                                if y != -1:
                                    info['server'] = it_tmp[-1].split('(')[-1].split(':')[0]
                                    info['port'] = it_tmp[-1].split('(')[-1].split(':')[-1].rstrip(')')
                                elif y == -1:
                                    item[0] = 'source'
                                    item[1] = 'sci'
                                if it_tmp[-1].find('emu') > -1 or it_tmp[-1].find('cache') > -1 or it_tmp[-1].find('card') > -1 or it_tmp[-1].find('biss') > -1:
                                    item[0] = 'source'
                                    item[1] = 'emu'
                            elif item[0] == 'hops':
                                item[1] = item[1].strip('\n')
                            elif item[0] == 'system':
                                item[1] = item[1].strip('\n')
                            elif item[0] == 'provider':
                                item[1] = item[1].strip('\n')
                            elif item[0][:2] == 'cw' or item[0] == 'ChID' or item[0] == 'Service':
                                pass
                            elif item[0] == 'source':
                                if item[1].strip()[:3] == 'net':
                                    it_tmp = item[1].strip().split(' ')
                                    info['protocol'] = it_tmp[1][1:]
                                    info['server'] = it_tmp[-1].split(':', 1)[0]
                                    info['port'] = it_tmp[-1].split(':', 1)[1][:-1]
                                    item[1] = 'net'
                            elif item[0] == 'prov':
                                y = item[1].find(',')
                                if y != -1:
                                    item[1] = item[1][:y]
                            elif item[0] == 'reader':
                                if item[1].strip() == 'emu':
                                    item[0] = 'source'
                            elif item[0] == 'from':
                                if item[1].strip().lower().startswith('local'):
                                    item[1] = 'sci'
                                    item[0] = 'source'
                                else:
                                    info['source'] = 'net'
                                    item[0] = 'server'
                            elif item[0] == 'provid':
                                item[0] = 'prov'
                            elif item[0] == 'using':
                                if item[1].strip() == 'emu' or item[1].strip() == 'sci':
                                    item[0] = 'source'
                                else:
                                    info['source'] = 'net'
                                    item[0] = 'protocol'
                            elif item[0] == 'address':
                                tt = item[1].find(':')
                                if tt != -1:
                                    info['server'] = item[1][:tt].strip()
                                    item[0] = 'port'
                                    item[1] = item[1][tt + 1:]
                            info[item[0].strip().lower()] = item[1].strip()
                        else:
                            if 'caid' not in info or 'CaID' not in info:
                                x = line.lower().find('caid')
                                if x != -1:
                                    y = line.find(',')
                                    if y != -1:
                                        info['caid'] = line[x + 5:y]
                            if 'pid' not in info:
                                x = line.lower().find('pid')
                                if x != -1:
                                    y = line.find(' =')
                                    z = line.find(' *')
                                    if y != -1:
                                        info['pid'] = line[x + 4:y]
                                    elif z != -1:
                                        info['pid'] = line[x + 4:z]

        return info

    def changed(self, what):
        Converter.changed(self, (self.CHANGED_POLL,))