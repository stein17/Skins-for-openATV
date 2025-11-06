# Components/Converter/BlueAVPNInfo.py
# Python 3 only
# Concept and design by stein17, with the assistance of Python Code Generator
# Please do not remove these lines; kindly request my permission before sharing or publishing.

from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from Components.Element import cached

import time
import json
import socket
import subprocess
import threading
import os

DEBUG = False
def _log(msg):
    if DEBUG:
        try:
            with open('/tmp/vpninfo.log', 'a') as f:
                f.write('%s\n' % msg)
        except Exception:
            pass

CACHE_PATH = '/tmp/vpninfo_cache.json'

def _run(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return out.decode('utf-8', 'ignore')
    except Exception:
        return ''

def _default_iface():
    out = _run("ip -4 route show default 2>/dev/null | head -n1") or _run("ip route show 0.0.0.0/0 2>/dev/null | head -n1")
    if out:
        parts = out.split()
        if 'dev' in parts:
            try:
                return parts[parts.index('dev') + 1]
            except Exception:
                pass
    # Fallback /proc
    try:
        with open('/proc/net/route', 'r') as f:
            for line in f:
                sp = line.split()
                if len(sp) >= 4:
                    iface = sp[0]
                    dest = sp[1]
                    try:
                        flags = int(sp[3], 16)
                    except Exception:
                        flags = 0
                    if dest == '00000000' and (flags & 0x2):
                        return iface
    except Exception:
        pass
    return None

def _iface_online(iface):
    if not iface:
        return False
    try:
        s = open('/sys/class/net/%s/operstate' % iface, 'r').read().strip()
        if s not in ('up', 'unknown'):
            return False
    except Exception:
        pass
    try:
        c = open('/sys/class/net/%s/carrier' % iface, 'r').read().strip()
        if c != '1':
            return False
    except Exception:
        pass
    return True

def _ip_for_iface(iface):
    try:
        out = _run('ip -4 addr show dev %s' % iface)
        for line in out.splitlines():
            line = line.strip()
            if line.startswith('inet '):
                return line.split()[1].split('/')[0]
    except Exception:
        pass
    # Fallback via Socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        pass
    return ''

def _conn_type_for_iface(iface):
    if not iface:
        return 'net_off'
    name = iface.lower()
    if name.startswith(('eth', 'en', 'br', 'lan')):
        return 'lan'
    if name.startswith(('wl', 'wlan', 'ra')):
        return 'wlan'
    if name.startswith(('ppp', 'wwan', 'usb', 'rmnet')):
        return 'modem'
    return 'lan'

def _list_up_ifaces(prefixes):
    up = []
    try:
        for name in os.listdir('/sys/class/net'):
            low = name.lower()
            if any(low.startswith(p) for p in prefixes):
                try:
                    st = open('/sys/class/net/%s/operstate' % name, 'r').read().strip()
                except Exception:
                    st = ''
                if st in ('up', 'unknown'):
                    up.append(name)
    except Exception:
        pass
    return up

def _vpn_detect():
    """
    Erkennung VPN:
      - WireGuard: wg* up
      - OpenVPN: tun*/tap* up
      - Default-Route-Device prüfen (ip route get 1.1.1.1), ob es wg/tun/tap ist
    Rückgabe: (active(bool), proto(str), iface(str|''))  proto: wireguard|openvpn|none
    """
    up_wg = _list_up_ifaces(('wg',))
    up_tun = _list_up_ifaces(('tun', 'tap', 'vpn'))
    # effektives Route-Device (nur bei VPNs relevant prüfen)
    route_dev = ''
    if up_wg or up_tun:
        out = _run("ip -4 route get 1.1.1.1 2>/dev/null | head -n1")
        if out:
            parts = out.split()
            if 'dev' in parts:
                try:
                    route_dev = parts[parts.index('dev') + 1]
                except Exception:
                    route_dev = ''

    # harte Zuordnung: wenn Route-Device vpn-Interface ist
    candidates = (up_wg + up_tun)
    if route_dev and route_dev in candidates:
        if route_dev.startswith('wg'):
            return True, 'wireguard', route_dev
        if route_dev.startswith(('tun', 'tap', 'vpn')):
            return True, 'openvpn', route_dev

    # softere Heuristik: irgendein VPN-IF up
    if up_wg:
        return True, 'wireguard', up_wg[0]
    if up_tun:
        return True, 'openvpn', up_tun[0]

    return False, 'none', ''

def _fetch_public_info(timeout=2.0):
    # bevorzugt http (keine CA nötig), dann https
    urls = [
        ('http://ip-api.com/json/', 'ip-api'),
        ('http://ipinfo.io/json', 'ipinfo'),
        ('https://ipapi.co/json/', 'ipapi'),
    ]
    for u, tag in urls:
        try:
            import urllib.request
            resp = urllib.request.urlopen(u, timeout=timeout)
            data = resp.read()
            js = json.loads(data.decode('utf-8', 'ignore'))
            if tag == 'ip-api':
                ip = js.get('query', '')
                cc = (js.get('countryCode', '') or '').upper()
                name = js.get('country', '')
            elif tag == 'ipinfo':
                ip = js.get('ip', '')
                cc = (js.get('country', '') or '').upper()
                name = js.get('country', '')
            else:
                ip = js.get('ip', '')
                cc = (js.get('country_code', '') or js.get('country', '') or '').upper()
                name = js.get('country_name', '') or js.get('country', '')
            return {'ip': ip or '', 'cc': cc or '', 'country': name or ''}
        except Exception:
            continue
    return {'ip': '', 'cc': '', 'country': ''}

GERMAN_NAMES = {'DE': 'Deutschland', 'AT': 'Österreich', 'CH': 'Schweiz'}

class BlueAVPNInfo(Poll, Converter):
    IP = 0
    CountryCode = 1
    CountryName = 2
    ReceiverIP = 3
    ConnType = 4
    VpnActive = 5
    CountryLabel = 6
    NetActive = 7       # neu: 'net_on' | 'net_off'
    VpnProto = 8        # neu: 'wireguard' | 'openvpn' | 'none'
    VpnIface = 9        # neu: z. B. 'wg0' | 'tun0' | ''

    def __init__(self, type):
        Poll.__init__(self)
        Converter.__init__(self, type)

        self.type = type
        if type in ('IP', 'PublicIP'):
            self.type = self.IP
        elif type == 'CountryCode':
            self.type = self.CountryCode
        elif type == 'CountryName':
            self.type = self.CountryName
        elif type == 'ReceiverIP':
            self.type = self.ReceiverIP
        elif type == 'ConnType':
            self.type = self.ConnType
        elif type == 'VpnActive':
            self.type = self.VpnActive
        elif type in ('CountryLabel', 'CountryText'):
            self.type = self.CountryLabel
        elif type == 'NetActive':
            self.type = self.NetActive
        elif type == 'VpnProto':
            self.type = self.VpnProto
        elif type == 'VpnIface':
            self.type = self.VpnIface

        # Poll moderat
        self.poll_interval = 2000
        self.poll_enabled = True

        # States
        self._last_public_ip = ''
        self._last_country_code = ''
        self._last_country_name = ''
        self._last_receiver_ip = ''
        self._last_conn_type = 'net_off'
        self._last_vpn_active = False
        self._last_net_active = False
        self._last_vpn_proto = 'none'
        self._last_vpn_iface = ''

        self._last_iface = None
        self._last_local_ip_ts = 0
        self._last_fast_ts = 0

        # Public-IP Fetch
        self._fetch_thread = None
        self._last_fetch_ts = 0
        self._min_fetch_interval = 60
        self._last_fetch_vpn_state = None
        self._offline_backoff = 30
        self._offline_until = 0

        self._load_cache()

    def _load_cache(self):
        try:
            if os.path.exists(CACHE_PATH):
                js = json.load(open(CACHE_PATH, 'r'))
                self._last_public_ip = js.get('ip', '') or ''
                self._last_country_code = (js.get('cc', '') or '').upper()
                self._last_country_name = js.get('country', '') or ''
        except Exception:
            pass

    def _save_cache(self):
        try:
            js = {'ip': self._last_public_ip, 'cc': self._last_country_code, 'country': self._last_country_name}
            json.dump(js, open(CACHE_PATH, 'w'))
        except Exception:
            pass

    # ---------- schnelle, synchrone Updates ----------
    def _update_fast(self):
        now = time.time()
        if now - self._last_fast_ts < 1.5:
            return

        # Default-IF + Online
        iface = _default_iface()
        net_on = bool(iface and _iface_online(iface))
        self._last_iface = iface
        self._last_net_active = net_on

        # Verbindungstyp + lokale IP (sparsam)
        self._last_conn_type = _conn_type_for_iface(iface)
        if iface and (now - self._last_local_ip_ts > 60):
            self._last_receiver_ip = _ip_for_iface(iface)
            self._last_local_ip_ts = now

        # VPN-Status/Proto/IF
        vpn_on, vpn_proto, vpn_if = _vpn_detect()
        self._last_vpn_active = vpn_on
        self._last_vpn_proto = vpn_proto
        self._last_vpn_iface = vpn_if

        self._last_fast_ts = now

    def _need_fetch_public(self):
        now = time.time()
        if now < self._offline_until:
            return False
        if not self._last_iface or not _iface_online(self._last_iface):
            return False
        if (now - self._last_fetch_ts) > self._min_fetch_interval:
            return True
        if self._last_vpn_active != self._last_fetch_vpn_state:
            return True
        return False

    def _start_fetch_thread(self):
        if self._fetch_thread and self._fetch_thread.is_alive():
            return
        def worker():
            info = _fetch_public_info(timeout=2.0)
            if info.get('ip'):
                cc = (info.get('cc', '') or '').upper()
                name = info.get('country', '')
                if cc in GERMAN_NAMES:
                    name = GERMAN_NAMES.get(cc, name)

                self._last_public_ip = info.get('ip', '')
                self._last_country_code = cc
                self._last_country_name = name
                self._last_fetch_ts = time.time()
                self._last_fetch_vpn_state = self._last_vpn_active
                self._offline_backoff = 30
                self._offline_until = 0
                self._save_cache()
            else:
                # Offline/Fehler -> Backoff
                self._offline_until = time.time() + self._offline_backoff
                self._offline_backoff = min(self._offline_backoff * 2, 600)
            try:
                Converter.changed(self, (self.CHANGED_POLL,))
            except Exception:
                pass

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        self._fetch_thread = t

    def poll(self):
        self._update_fast()
        if self._need_fetch_public():
            self._start_fetch_thread()
        Converter.changed(self, (self.CHANGED_POLL,))

    # ---------- Ausgaben ----------
    @cached
    def getText(self):
        if self.type == self.IP:
            return self._last_public_ip or ''
        elif self.type == self.CountryCode:
            return self._last_country_code or ''
        elif self.type == self.CountryName:
            return self._last_country_name or ''
        elif self.type == self.ReceiverIP:
            return self._last_receiver_ip or ''
        elif self.type == self.ConnType:
            return self._last_conn_type or 'net_off'
        elif self.type == self.VpnActive:
            return 'True' if self._last_vpn_active else 'False'
        elif self.type == self.CountryLabel:
            code = self._last_country_code or ''
            name = self._last_country_name or ''
            return ('%s – %s' % (code, name)) if (code and name) else (name or code)
        elif self.type == self.NetActive:
            return 'net_on' if self._last_net_active else 'net_off'
        elif self.type == self.VpnProto:
            return self._last_vpn_proto or 'none'
        elif self.type == self.VpnIface:
            return self._last_vpn_iface or ''
        return ''

    text = property(getText)

    @cached
    def getBoolean(self):
        if self.type == self.VpnActive:
            return bool(self._last_vpn_active)
        if self.type == self.NetActive:
            return bool(self._last_net_active)
        return False

    boolean = property(getBoolean)

    def changed(self, what):
        Converter.changed(self, what)
