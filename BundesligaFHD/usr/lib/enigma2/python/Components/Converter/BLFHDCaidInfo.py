# -*- coding: utf-8 -*-
#
# =============================================================================
#  DEUTSCH / GERMAN
# =============================================================================
#  SoftCam Info Converter for Enigma2 Skins
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
#  SoftCam Info Converter for Enigma2 Skins
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
try:
    from urllib.request import urlopen
except:
    urlopen = None
info = {}
old_ecm_mtime = None

class BLFHDCaidInfo(Poll, Converter, object):
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

                                        sv = (server or '').strip().lower()

                                        if (not sv) or sv == 'local':

                                            # Local card: show provider label if known (e.g. CAID 1843 => HD+)

                                            local_label = ''

                                            try:

                                                if (caid or '').upper() == '1843':

                                                    local_label = 'HD+'

                                            except:

                                                pass

                                            if local_label:

                                                textvalue += '%s (local)' % local_label

                                            else:

                                                textvalue += 'local'

                                        else:

                                            textvalue += server


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

    # --- Softcam version (WebIF/title + fallback) ---
    def getSoftcamKind(self):
        # Returns "MASTER", "EMU" or "" (no OSCam prefix, so you can format in skin)
        try:
            out = subprocess.check_output(["ps", "-ef"], stderr=subprocess.STDOUT, timeout=1).decode("utf-8", "ignore").lower()
        except:
            out = ""
        if "oscam-master" in out:
            return "MASTER"
        if "oscam-emu" in out:
            return "EMU"
        return ""

    def _read_httpport(self, conf_path, default_port="8888"):
        port = default_port
        try:
            if fileExists(conf_path):
                with open(conf_path, "r") as f:
                    for line in f:
                        line_s = line.strip()
                        if not line_s or line_s.startswith("#") or "=" not in line_s:
                            continue
                        k, v = line_s.split("=", 1)
                        if k.strip().lower() == "httpport":
                            port = v.strip()
                            break
        except:
            pass
        return port

    def _webif_title(self, port):
        if urlopen is None:
            return ""
        try:
            html = urlopen("http://127.0.0.1:%s/status.html" % port, timeout=1).read().decode("utf-8", "ignore")
            m = re.search(r"<title>\s*([^<]+)\s*</title>", html, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        except:
            pass
        return ""

    def _detect_softcam_exec(self):
        # Returns (exe_path, name_hint)
        candidates = [
            ("oscam-emu", "/usr/bin/oscam-emu", "OSCam"),
            ("oscam", "/usr/bin/oscam", "OSCam"),
            ("ncam", "/usr/bin/ncam", "NCam"),
            ("cccam", "/usr/bin/CCcam", "CCcam"),
            ("mgcamd", "/usr/bin/mgcamd", "Mgcamd"),
            ("gbox", "/usr/bin/gbox", "Gbox"),
            ("scam", "/usr/bin/scam", "Scam"),
        ]
        try:
            out = subprocess.check_output(["ps", "-ef"], stderr=subprocess.STDOUT, timeout=1).decode("utf-8", "ignore")
        except:
            out = ""
        out_l = out.lower()

        for proc_name, exe_path, hint in candidates:
            if proc_name in out_l:
                if exe_path and fileExists(exe_path):
                    return (exe_path, hint)
                return ("", hint)
        return ("", "")

    def getSoftcamVersion(self):
        # Cache (avoid WebIF fetch each poll tick)
        now = time.time()
        cache = getattr(self, "_softcam_cache", None)
        if cache and (now - cache.get("ts", 0)) < 10:
            return cache.get("val", "")

        exe_path, hint = self._detect_softcam_exec()

        # OSCam / NCam prefer WebIF <title>
        conf_candidates = []
        if "oscam" in (exe_path or "").lower() or hint == "OSCam":
            conf_candidates = [
                ("/etc/tuxbox/config/oscam-emu/oscam.conf", "8888"),
                ("/etc/tuxbox/config/oscam/oscam.conf", "8888"),
                ("/etc/tuxbox/config/oscam-stable/oscam.conf", "8888"),
                ("/etc/tuxbox/config/oscam-smod/oscam.conf", "8888"),
                ("/etc/tuxbox/config/oscam-master/oscam.conf", "8888"),
            ]
        elif "ncam" in (exe_path or "").lower() or hint == "NCam":
            conf_candidates = [
                ("/etc/tuxbox/config/ncam/ncam.conf", "8888"),
                ("/etc/tuxbox/config/ncam/oscam.conf", "8888"),
            ]

        for conf_path, def_port in conf_candidates:
            port = self._read_httpport(conf_path, def_port)
            title = self._webif_title(port)
            if title:
                self._softcam_cache = {"ts": now, "val": title}
                return title

        # Fallback: try binary flags
        if exe_path and fileExists(exe_path):
            for arg in ("-V", "-v", "--version"):
                try:
                    out = subprocess.check_output([exe_path, arg], stderr=subprocess.STDOUT, timeout=1).decode("utf-8", "ignore")
                    m = re.search(r"(OSCam\s+[^\r\n]+|NCam\s+[^\r\n]+|CCcam\s+[^\r\n]+|Mgcamd\s+[^\r\n]+|Gbox\s+[^\r\n]+|Scam\s+[^\r\n]+)", out, re.IGNORECASE)
                    if m:
                        val = m.group(1).strip()
                        self._softcam_cache = {"ts": now, "val": val}
                        return val
                except:
                    pass

        # Last resort: name only
        self._softcam_cache = {"ts": now, "val": (hint or "")}
        return hint or ""

    
    def getSoftcamVersionShort(self):
        full = (self.getSoftcamVersion() or "").strip()
        full_l = full.lower()

        # detect smod by process name or title text
        try:
            psout = subprocess.check_output(["ps", "-ef"], stderr=subprocess.STDOUT, timeout=1).decode("utf-8", "ignore").lower()
        except:
            psout = ""
        is_smod = ("oscam-smod" in psout) or ("smod" in full_l)

        # Normalize SMOD: rsvn11726 / "Trunk rsvn11726" / r11726 -> "smod 11726"
        if is_smod:
            import re
            m = re.search(r"rsvn\s*([0-9]+)", full_l)
            if not m:
                m = re.search(r"\br\s*([0-9]{4,})\b", full_l)
            if m:
                return "SMOD " + m.group(1)

        # Default behavior: strip leading "OSCam " / "NCam "
        import re
        out = re.sub(r'^(OSCam|NCam)\s*', '', full, flags=re.IGNORECASE).strip()
        return out

    def ecmfile(self):
        global info
        global old_ecm_mtime
        ecm = None
        service = self.source.service
        if service:
            try:
                ecm_mtime = os.stat('/tmp/ecm.info').st_mtime
                if not os.stat('/tmp/ecm.info').st_size > 0:
                    info = {}
                if ecm_mtime == old_ecm_mtime:
                    return info
                old_ecm_mtime = ecm_mtime
                ecmf = open('/tmp/ecm.info', 'r')
                ecm = ecmf.readlines()
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

                ecmf.close()
        return info

    def changed(self, what):
        Converter.changed(self, (self.CHANGED_POLL,))
