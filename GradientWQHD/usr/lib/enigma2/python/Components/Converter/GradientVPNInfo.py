# Components/Converter/GradientVPNInfo.py
# Python 3 only
# Concept and design by stein17, with the assistance of Python Code Generator
# Please do not remove these lines; kindly request my permission before sharing or publishing.

# Was damit abgedeckt ist

# WireGuard: Interfaces beginnen mit wg (z. B. wg0, NordLynx).
# OVPN/OpenVPN-Erkennung: tun*/tap*/vpn*/ovpn* (z. B. tun0, tap0, ovpn0).
# Split-Tunneling: Auch wenn die Default-Route nicht über das VPN geht, gilt VPN als aktiv, sobald ein entsprechendes Interface up ist.
# Nützliche Keys im Converter
# VpnActive → Wahr/Falsch
# NetActive → net_on/net_off (für dein Net-Status-Icon)
# ConnType → lan/wlan/net_off
# VpnProto → wireguard/openvpn/none
# VpnIface → z. B. wg0/tun0
# Ländervorwahl → DE/US/TR
# CountryLabel → DE – Deutschland
# IP → Öffentliche IP (asynchron, mit Cache/Backoff)
# ReceiverIP → lokale IP
# VpnProto/VpnIface: wireguard | OffenVPN | none und z. B. wg0/tun0.
# Offline-sicher: Public-IP/Geodaten asynchron mit Backoff und Cache (/tmp/vpninfo_cache.json). Kein Blockieren der GUI.
# CHANGED_POLL wird als Tuple gemeldet (OpenATV kompatibel).

# Was ist neu

# OVPN/OpenVPN sicher erkannt: tun*/tap*/vpn*/ovpn* werden als openvpn gezählt.
# Router-VPN Heuristik: Wenn die Box selbst keine wg/tun/tap-Interfaces hat, aber der Public-IP-Provider nach VPN aussieht (z. B. Mullvad, NordVPN, OVPN, inkl. ofn/ofn101), setzt der Converter VpnActive auf ON.
# Neuer Key VpnProvider: z. B. mullvad, nordvpn, ovpn, ...
# Optionaler Proto-Override bei Router-VPN: Datei /etc/enigma2/vpnproto mit wireguard oder openvpn erzwingt VpnProto.
# NetActive Key für dein net_on/net_off Icon bleibt dabei.
# Public-IP/Geo-Fetch ist asynchron, mit Backoff und Cache (/tmp/vpninfo_cache.json).
# CHANGED_POLL wird korrekt als Tuple gemeldet.
# Eingebaute Provider-Indikatoren (Auszug)

# Mullvad, NordVPN, NordLynx, SurfShark, Ovpn, ovpn.com, OfN, OfN101, AirVPN, Proton, Pia (Private Internet Access), TorGuard, IVPN, VyprVPN, Windscribe, Perfect Privacy, Azire, ExpressVPN, Cyberghost, PureVPN, StrongVPN, hide.me, HideMyAss, Ipvanish, Tunnelbear, Mozilla VPN, Cryptostorm, WeVPN, PrivateVPN.

# Skin-Keys (Auszug)

# Geistiges Eigentum / Öffentliches Eigentum
# Ländercode, Ländername, Länderetikett
# EmpfängerIP
# ConnType → lan | WLAN | net_off
# NetActive → net_on | net_off
# VpnActive → wahr | FALSCH
# VpnProto → wireguard | OffenVPN | nichts
# VpnIface → z. B. wg0 | tun0
# VpnProvider → z. B. B. mullvad | NordVPN | ovpn

from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from Components.Element import cached

import time, json, socket, subprocess, threading, os, re

DEBUG = False

def _log(msg):
    if DEBUG:
        try:
            with open('/tmp/vpninfo.log', 'a') as f:
                f.write('%s\n' % msg)
        except Exception:
            pass

CACHE_PATH = '/tmp/vpninfo_cache.json'

VPN_PROVIDER_KEYS = {
    'mullvad': 'mullvad',
    'nordvpn': 'nordvpn',
    'nord lynx': 'nordvpn',
    'nordlynx': 'nordvpn',
    'protonvpn': 'protonvpn',
    'proton': 'protonvpn',
    'expressvpn': 'expressvpn',
    'surfshark': 'surfshark',
    'ipvanish': 'ipvanish',
    'cyberghost': 'cyberghost',
    'ovpn': 'ovpn', 'ovpn.com': 'ovpn', 'ofn': 'ovpn', 'ofn101': 'ovpn',
}

PROVIDER_DOMAIN_KEYS = {
    'nordvpn.com': 'nordvpn', 'mullvad.net': 'mullvad', 'ovpn.com': 'ovpn',
    'surfshark.com': 'surfshark', 'protonvpn.com': 'protonvpn', 'expressvpn.com': 'expressvpn',
    'ipvanish.com': 'ipvanish', 'cyberghostvpn.com': 'cyberghost',
    'privateinternetaccess.com': 'private internet access', 'airvpn.org': 'airvpn',
    'ivpn.net': 'ivpn', 'vyprvpn.com': 'vyprvpn', 'windscribe.com': 'windscribe',
    'perfect-privacy.com': 'perfect privacy', 'azirevpn.com': 'azirevpn',
    'hide.me': 'hide.me', 'hidemyass.com': 'hidemyass', 'tunnelbear.com': 'tunnelbear',
    'mozilla.org': 'mozilla vpn', 'cryptostorm.is': 'cryptostorm', 'wevpn.com': 'wevpn',
    'privatevpn.com': 'privatevpn', 'nordlynx': 'nordvpn',
}

PROVIDER_PRETTY = {
    'mullvad': 'Mullvad VPN', 'nordvpn': 'NordVPN', 'protonvpn': 'ProtonVPN',
    'expressvpn': 'ExpressVPN', 'surfshark': 'Surfshark VPN', 'ipvanish': 'IPVanish VPN',
    'cyberghost': 'CyberGhost VPN', 'ovpn': 'OVPN'
}

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

def _vpn_detect_by_interfaces():
    up_wg = _list_up_ifaces(('wg',))
    up_tun = _list_up_ifaces(('tun', 'tap', 'vpn', 'ovpn'))
    if up_wg:
        return True, 'wireguard', up_wg[0]
    if up_tun:
        return True, 'openvpn', up_tun[0]
    return False, 'none', ''

def _load_forced_proto():
    for p in ('/etc/enigma2/vpnproto', '/etc/vpnproto'):
        try:
            if os.path.exists(p):
                v = open(p, 'r').read().strip().lower()
                if v.startswith('wg'):
                    return 'wireguard'
                if v in ('openvpn', 'ovpn') or v.startswith('ovpn'):
                    return 'openvpn'
        except Exception:
            pass
    return ''

def _looks_like_vpn_provider(fields):
    text = ' '.join([
        fields.get('isp', '') or '', fields.get('org', '') or '',
        fields.get('asn', '') or '', fields.get('rdns', '') or '',
    ]).lower()
    for k, slug in VPN_PROVIDER_KEYS.items():
        if k in text:
            return slug
    return ''

def _scan_local_vpn_configs():
    paths = ['/etc/wireguard','/etc/openvpn','/etc/enigma2/wireguard','/etc/enigma2/openvpn']
    found = ''
    for base in paths:
        if not os.path.isdir(base):
            continue
        try:
            for root, _, files in os.walk(base):
                for fn in files:
                    if not fn.lower().endswith(('.conf','.ovpn','.cfg','.txt')):
                        continue
                    try:
                        data = open(os.path.join(root, fn), 'r', errors='ignore').read().lower()
                    except Exception:
                        continue
                    for m in re.findall(r'(?:(?:endpoint|remote)\s*=\s*|remote\s+)([^\s:]+)', data):
                        for key, slug in PROVIDER_DOMAIN_KEYS.items():
                            if key in m:
                                return slug
                    if '103.86.96.100' in data or '103.86.99.100' in data:
                        return 'nordvpn'
                    if 'nordlynx' in data:
                        return 'nordvpn'
        except Exception:
            pass
    return found

def _fetch_public_info(timeout=2.0):
    urls = [
        ('http://ip-api.com/json/?fields=status,message,query,country,countryCode,isp,org,as,reverse','ip-api'),
        ('http://ipinfo.io/json','ipinfo'),
        ('https://ipapi.co/json/','ipapi'),
    ]
    for u, tag in urls:
        try:
            import urllib.request
            js = json.loads(urllib.request.urlopen(u, timeout=timeout).read().decode('utf-8','ignore'))
            if tag == 'ip-api':
                return {'ip': js.get('query',''), 'cc': (js.get('countryCode','') or '').upper(), 'country': js.get('country',''), 'isp': js.get('isp',''), 'org': js.get('org',''), 'asn': js.get('as',''), 'rdns': js.get('reverse','')}
            elif tag == 'ipinfo':
                return {'ip': js.get('ip',''), 'cc': (js.get('country','') or '').upper(), 'country': js.get('country',''), 'isp': '', 'org': js.get('org',''), 'asn': js.get('org',''), 'rdns': js.get('hostname','')}
            else:
                return {'ip': js.get('ip',''), 'cc': (js.get('country_code','') or js.get('country','') or '').upper(), 'country': js.get('country_name','') or js.get('country',''), 'isp': js.get('org',''), 'org': js.get('org',''), 'asn': js.get('asn',''), 'rdns': ''}
        except Exception:
            continue
    return {'ip':'','cc':'','country':'','isp':'','org':'','asn':'','rdns':''}

GERMAN_NAMES = {'DE':'Deutschland','AT':'Österreich','CH':'Schweiz'}

class GradientVPNInfo(Poll, Converter):
    IP=0; CountryCode=1; CountryName=2; ReceiverIP=3; ConnType=4; VpnActive=5; CountryLabel=6; NetActive=7; VpnProto=8; VpnIface=9; VpnProvider=10; VpnProviderPretty=11
    def __init__(self, type):
        Poll.__init__(self); Converter.__init__(self, type)
        self.type = {'IP':0,'PublicIP':0,'CountryCode':1,'CountryName':2,'ReceiverIP':3,'ConnType':4,'VpnActive':5,'CountryLabel':6,'CountryText':6,'NetActive':7,'VpnProto':8,'VpnIface':9,'VpnProvider':10,'VpnProviderPretty':11}.get(type, type)
        self.poll_interval=2000; self.poll_enabled=True
        self._last_public_ip=''; self._last_country_code=''; self._last_country_name=''; self._last_receiver_ip=''; self._last_conn_type='net_off'; self._last_vpn_active=False; self._last_net_active=False; self._last_vpn_proto='none'; self._last_vpn_iface=''
        self._prov_local=''; self._prov_public=''
        self._last_iface=None; self._last_local_ip_ts=0; self._last_fast_ts=0
        self._fetch_thread=None; self._last_fetch_ts=0; self._min_fetch_interval=60; self._last_fetch_vpn_state=None; self._offline_backoff=30; self._offline_until=0
        self._load_cache()
    def _load_cache(self):
        try:
            if os.path.exists(CACHE_PATH):
                js=json.load(open(CACHE_PATH,'r'))
                self._last_public_ip=js.get('ip','') or ''
                self._last_country_code=(js.get('cc','') or '').upper()
                self._last_country_name=js.get('country','') or ''
        except Exception: pass
    def _save_cache(self):
        try:
            json.dump({'ip':self._last_public_ip,'cc':self._last_country_code,'country':self._last_country_name}, open(CACHE_PATH,'w'))
        except Exception: pass
    def _update_fast(self):
        now = time.time()
        if now - self._last_fast_ts < 1.5:
            return

        iface = _default_iface()
        iface_online = bool(iface and _iface_online(iface))
        self._last_iface = iface

        # record interface type (lan/wlan/modem) regardless of internet availability
        self._last_conn_type = _conn_type_for_iface(iface)

        # local receiver IP (throttled)
        if iface and (now - self._last_local_ip_ts > 60):
            self._last_receiver_ip = _ip_for_iface(iface)
            self._last_local_ip_ts = now

        vpn_on, vpn_proto, vpn_if = _vpn_detect_by_interfaces()
        self._last_vpn_active = vpn_on
        self._last_vpn_proto = vpn_proto
        self._last_vpn_iface = vpn_if

        # refresh local provider each time (fast scan)
        self._prov_local = _scan_local_vpn_configs() or ''

        # Determine net_active: prefer confirmed public IP; respect offline backoff; otherwise fallback to interface link
        if self._last_public_ip:
            self._last_net_active = True
        elif time.time() < self._offline_until:
            self._last_net_active = False
        else:
            self._last_net_active = iface_online

        # Router-VPN heuristic: only if provider detected from public lookup and no local provider
        if not self._last_vpn_active and self._last_net_active and self._prov_public and not self._prov_local:
            self._last_vpn_active = True
            forced = _load_forced_proto()
            if forced:
                self._last_vpn_proto = forced

        self._last_fast_ts = now

    def _need_fetch_public(self):
        now=time.time()
        if now < self._offline_until: return False
        if not self._last_iface or not _iface_online(self._last_iface): return False
        if (now - self._last_fetch_ts) > self._min_fetch_interval: return True
        if self._last_vpn_active != self._last_fetch_vpn_state: return True
        return False
    def _start_fetch_thread(self):
        if self._fetch_thread and self._fetch_thread.is_alive(): return
        def worker():
            info=_fetch_public_info(timeout=2.0)
            if info.get('ip'):
                cc=(info.get('cc','') or '').upper(); name=info.get('country','');
                if cc in GERMAN_NAMES: name=GERMAN_NAMES.get(cc,name)
                self._last_public_ip=info.get('ip',''); self._last_country_code=cc; self._last_country_name=name
                provider=_looks_like_vpn_provider(info); self._prov_public=provider or ''
                self._last_fetch_ts=time.time(); self._last_fetch_vpn_state=self._last_vpn_active; self._offline_backoff=30; self._offline_until=0; self._save_cache()
                # Router‑VPN heuristic: only if provider from PUBLIC and no local provider
                if not self._last_vpn_active and self._prov_public and not self._prov_local and self._last_net_active:
                    self._last_vpn_active=True
                    forced=_load_forced_proto();
                    if forced: self._last_vpn_proto=forced
            else:
                self._offline_until=time.time()+self._offline_backoff; self._offline_backoff=min(self._offline_backoff*2,600)
            try:
                Converter.changed(self,(self.CHANGED_POLL,))
            except Exception: pass
        t=threading.Thread(target=worker, daemon=True); t.start(); self._fetch_thread=t
    def poll(self):
        self._update_fast()
        if self._need_fetch_public(): self._start_fetch_thread()
        Converter.changed(self,(self.CHANGED_POLL,))
    @cached
    def getText(self):
        if self.type==self.IP: return self._last_public_ip or ''
        elif self.type==self.CountryCode: return self._last_country_code or ''
        elif self.type==self.CountryName: return self._last_country_name or ''
        elif self.type==self.ReceiverIP: return self._last_receiver_ip or ''
        elif self.type==self.ConnType:
            if not self._last_net_active:
                return 'net_off'
            return self._last_conn_type or 'lan'
        elif self.type==self.VpnActive: return 'True' if self._last_vpn_active else 'False'
        elif self.type==self.CountryLabel:
            code=self._last_country_code or ''; name=self._last_country_name or ''
            return ('%s – %s' % (code,name)) if (code and name) else (name or code)
        elif self.type==self.NetActive: return 'net_on' if self._last_net_active else 'net_off'
        elif self.type==self.VpnProto: return self._last_vpn_proto or 'none'
        elif self.type==self.VpnIface: return self._last_vpn_iface or ''
        elif self.type==self.VpnProvider:
            if not self._last_vpn_active: return 'none'
            slug=self._prov_local or self._prov_public
            return slug or 'unknown'
        elif self.type==self.VpnProviderPretty:
            if not self._last_vpn_active: return 'None'
            slug=self._prov_local or self._prov_public
            if not slug: return 'Unknown'
            return PROVIDER_PRETTY.get(slug, slug.capitalize())
        return ''
    text=property(getText)
    @cached
    def getBoolean(self):
        if self.type==self.VpnActive: return bool(self._last_vpn_active)
        if self.type==self.NetActive: return bool(self._last_net_active)
        return False
    boolean=property(getBoolean)
    def changed(self, what):
        Converter.changed(self, what)
