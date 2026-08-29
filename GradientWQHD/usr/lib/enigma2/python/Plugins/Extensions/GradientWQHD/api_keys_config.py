# -*- coding: utf-8 -*-
# 02.26 @stein17, Many new features and improvements
"""GradientWQHD - API Keys setup screen (TVDB v4 + TVDB legacy separate fields)

Filename: api_keys_config.py

Install to:
  /usr/lib/enigma2/python/Plugins/Extensions/GradientWQHD/api_keys_config.py

What you get
------------
- Separate fields:
    * TheTVDB v4 API Key (UUID)
    * TheTVDB Legacy API Key (32 hex)
    * TheTVDB PIN (v4 only, optional)
- "Test" button checks:
    * TMDb v3
    * OMDb
    * Fanart
    * TVDB v4 (login + search)
    * TVDB legacy (XML endpoint)

How keys are written
--------------------
Keys are written as compatibility files into the current skin folder:
  /usr/share/enigma2/<skin>/

- TMDb:   tmdbkey  + apikey
- OMDb:   omdbkey
- TVDB v4: thetvdbkey
- TVDB legacy: thetvdbkey_legacy
- TVDB PIN: thetvdbpin
- Fanart: fanartkey

If a field is empty, the corresponding file is removed and the renderers fall
back to their built-in defaults.

Security note
-------------
Keys are stored as plain text files on the box. Do not share your backups.
"""

from __future__ import absolute_import

import os
import re
import json

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.config import (
    config, ConfigSubsection, ConfigText, getConfigListEntry
)
from Components.ConfigList import ConfigListScreen
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

try:
    from .__init__ import _
except Exception:
    _ = lambda x: x

# ---------------------------------------------------------------------
# Simple EN/DE translation helper (without .mo)
try:
    from Components.Language import language
    _LANG = (language.getLanguage() or 'en').lower()
except Exception:
    _LANG = 'en'


def tr(en, de=None):
    try:
        if de and _LANG.startswith('de'):
            return de
    except Exception:
        pass
    return en


def _ensure_config():
    if not hasattr(config.plugins, 'GradientWQHD'):
        config.plugins.GradientWQHD = ConfigSubsection()

    # keep old names if they already exist; add new ones
    if not hasattr(config.plugins.GradientWQHD, 'tmdb_api'):
        config.plugins.GradientWQHD.tmdb_api = ConfigText(default="", fixed_size=False)
    if not hasattr(config.plugins.GradientWQHD, 'omdb_api'):
        config.plugins.GradientWQHD.omdb_api = ConfigText(default="", fixed_size=False)

    if not hasattr(config.plugins.GradientWQHD, 'thetvdb_v4_api'):
        config.plugins.GradientWQHD.thetvdb_v4_api = ConfigText(default="", fixed_size=False)
    if not hasattr(config.plugins.GradientWQHD, 'thetvdb_legacy_api'):
        config.plugins.GradientWQHD.thetvdb_legacy_api = ConfigText(default="", fixed_size=False)
    if not hasattr(config.plugins.GradientWQHD, 'thetvdb_pin'):
        config.plugins.GradientWQHD.thetvdb_pin = ConfigText(default="", fixed_size=False)

    if not hasattr(config.plugins.GradientWQHD, 'fanart_api'):
        config.plugins.GradientWQHD.fanart_api = ConfigText(default="", fixed_size=False)


def _skin_dir():
    try:
        skin = config.skin.primary_skin.value.replace('/skin.xml', '')
        return '/usr/share/enigma2/%s' % skin
    except Exception:
        return '/usr/share/enigma2/GradientWQHD'


def _read_file(p):
    try:
        if os.path.exists(p):
            with open(p, 'r') as f:
                return (f.read() or '').strip()
    except Exception:
        pass
    return ''


def _write_or_remove(p, value):
    value = (value or '').strip()
    try:
        if not value:
            if os.path.exists(p):
                os.remove(p)
            return True
        with open(p, 'w') as f:
            f.write(value + '\n')
        return True
    except Exception:
        return False


def _http_get(url, headers=None, timeout=10):
    headers = headers or {}
    try:
        import requests
        r = requests.get(url, headers=headers, timeout=timeout)
        return r.status_code, r.text
    except Exception:
        pass

    try:
        try:
            from urllib.request import urlopen, Request
        except Exception:
            from urllib2 import urlopen, Request
        req = Request(url)
        for k, v in headers.items():
            req.add_header(k, v)
        resp = urlopen(req, timeout=timeout)
        code = getattr(resp, 'code', 200)
        data = resp.read()
        try:
            txt = data.decode('utf-8', 'ignore')
        except Exception:
            txt = str(data)
        try:
            resp.close()
        except Exception:
            pass
        return code, txt
    except Exception as e:
        return 0, str(e)


def _http_post_json(url, payload, headers=None, timeout=10):
    headers = headers or {}
    try:
        import requests
        r = requests.post(url, json=payload, headers=headers, timeout=timeout)
        return r.status_code, r.text
    except Exception:
        pass

    try:
        try:
            from urllib.request import urlopen, Request
        except Exception:
            from urllib2 import urlopen, Request
        body = json.dumps(payload).encode('utf-8')
        req = Request(url, data=body)
        req.add_header('Content-Type', 'application/json')
        for k, v in headers.items():
            req.add_header(k, v)
        resp = urlopen(req, timeout=timeout)
        code = getattr(resp, 'code', 200)
        data = resp.read()
        try:
            txt = data.decode('utf-8', 'ignore')
        except Exception:
            txt = str(data)
        try:
            resp.close()
        except Exception:
            pass
        return code, txt
    except Exception as e:
        return 0, str(e)


def _is_tvdb_v4_key(key):
    key = (key or '').strip()
    return bool(re.match(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$', key))


def _is_tvdb_legacy_key(key):
    key = (key or '').strip()
    return bool(re.match(r'^[0-9a-fA-F]{32}$', key))


def _tvdb_v4_login_and_search(api_key, pin=None):
    api_key = (api_key or '').strip()
    pin = (pin or '').strip() or None
    if not api_key:
        return False, 'EMPTY'

    payload = {'apikey': api_key}
    if pin:
        payload['pin'] = pin

    code, txt = _http_post_json('https://api4.thetvdb.com/v4/login', payload, timeout=10)
    if code != 200:
        return False, 'LOGIN FAIL (HTTP %s)' % code

    try:
        j = json.loads(txt)
        token = (((j or {}).get('data') or {}).get('token') or '').strip()
    except Exception:
        token = ''

    if not token:
        return False, 'LOGIN FAIL (no token)'

    hdr = {'Authorization': 'Bearer %s' % token, 'Accept': 'application/json'}
    code2, txt2 = _http_get('https://api4.thetvdb.com/v4/search?query=Simpsons&type=series&language=deu&limit=5', headers=hdr, timeout=10)
    if code2 != 200:
        return False, 'SEARCH FAIL (HTTP %s)' % code2

    try:
        j2 = json.loads(txt2)
        data = j2.get('data') or []
        if isinstance(data, list) and len(data) > 0:
            return True, 'OK'
    except Exception:
        pass

    return True, 'OK (no results?)'


def _tvdb_legacy_xml_test(legacy_key):
    legacy_key = (legacy_key or '').strip()
    if not legacy_key:
        return False, 'EMPTY'

    code, txt = _http_get('https://thetvdb.com/api/%s/series/80379/en.xml' % legacy_key, timeout=10)
    if code != 200:
        return False, 'FAIL (HTTP %s)' % code

    ok = ('<Series>' in txt) or ('<SeriesName>' in txt)
    return (ok, 'OK' if ok else 'FAIL (bad xml)')


class GradientWQHD_APIKeysSetup(Screen, ConfigListScreen):
    skin = """
    <screen name="GradientWQHD_APIKeysSetup" position="center,center" size="1707,613" title="API Keys" flags="wfNoBorder" backgroundColor="transparent">
        <widget source="Title" render="Label" position="27,0" size="1413,80" font="Italic; 56" halign="left" valign="center" transparent="1" foregroundColor="gradient_foreground_selection" backgroundColor="background" textBorderColor="black" textBorderWidth="1" zPosition="1" />
        <widget name="config" position="27,107" size="1653,420" font="Regular;40" scrollbarMode="showOnDemand" itemHeight="60" transparent="1" />
        <eLabel name="menu_bg" position="0,80" size="1707,533" backgroundColor="gradient_BGO,gradient_BGM,gradient_BGU,vertical" zPosition="-8" />
        <eLabel name="title_bg" position="0,0" size="1707,93" backgroundColor="gradient_TBGL,gradient_BGO,gradient_BGU,horizontal" zPosition="-9" cornerRadius="16" />
        <eLabel name="title_line" position="0,80" size="1707,5" backgroundColor="gradient_background,gradient_BGLR,gradient_BGLM,horizontal" zPosition="10" />
        <eLabel name="Line_Menu" position="20,533" size="1667,3" backgroundColor="gradient_BGLR,gradient_BGLM,gradient_BGLR,horizontal" zPosition="10" />
        <ePixmap pixmap="buttons/key_red.png" position="27,553" size="40,40" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_green.png" position="347,553" size="40,40" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_yellow.png" position="667,553" size="40,40" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_blue.png" position="1133,553" size="40,40" alphatest="blend" zPosition="10" transparent="1" />
        <widget name="key_red" position="80,547" size="267,53" font="Regular;32" valign="center" halign="left" transparent="1" />
        <widget name="key_green" position="400,547" size="267,53" font="Regular;32" valign="center" halign="left" transparent="1" />
        <widget name="key_yellow" position="720,547" size="413,53" font="Regular;32" valign="center" halign="left" transparent="1" />
        <widget name="key_blue" position="1187,547" size="267,53" font="Regular;32" valign="center" halign="left" transparent="1" />   
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        _ensure_config()

        sd = _skin_dir()

        # Load existing key files
        tmdb_from_file = _read_file(os.path.join(sd, 'tmdbkey')) or _read_file(os.path.join(sd, 'apikey'))
        omdb_from_file = _read_file(os.path.join(sd, 'omdbkey'))

        tvdb_v4_from_file = _read_file(os.path.join(sd, 'thetvdbkey'))
        tvdb_legacy_from_file = _read_file(os.path.join(sd, 'thetvdbkey_legacy'))
        tvdb_pin_from_file = _read_file(os.path.join(sd, 'thetvdbpin'))

        fanart_from_file = _read_file(os.path.join(sd, 'fanartkey'))

        if tmdb_from_file:
            config.plugins.GradientWQHD.tmdb_api.value = tmdb_from_file
        if omdb_from_file:
            config.plugins.GradientWQHD.omdb_api.value = omdb_from_file

        # If thetvdbkey contains a legacy key, show it in legacy field.
        if tvdb_v4_from_file:
            if _is_tvdb_v4_key(tvdb_v4_from_file):
                config.plugins.GradientWQHD.thetvdb_v4_api.value = tvdb_v4_from_file
            elif _is_tvdb_legacy_key(tvdb_v4_from_file):
                config.plugins.GradientWQHD.thetvdb_legacy_api.value = tvdb_v4_from_file

        if tvdb_legacy_from_file:
            config.plugins.GradientWQHD.thetvdb_legacy_api.value = tvdb_legacy_from_file

        if tvdb_pin_from_file:
            config.plugins.GradientWQHD.thetvdb_pin.value = tvdb_pin_from_file

        if fanart_from_file:
            config.plugins.GradientWQHD.fanart_api.value = fanart_from_file

        self.list = []
        self.list.append(getConfigListEntry(tr('TMDb API key (v3)', 'TMDb API-Key (v3)'), config.plugins.GradientWQHD.tmdb_api))
        self.list.append(getConfigListEntry(tr('OMDb API key', 'OMDb API-Key'), config.plugins.GradientWQHD.omdb_api))

        self.list.append(getConfigListEntry(tr('TheTVDB v4 API key (UUID)', 'TheTVDB v4 API-Key (UUID)'), config.plugins.GradientWQHD.thetvdb_v4_api))
        self.list.append(getConfigListEntry(tr('TheTVDB PIN (v4 only, optional)', 'TheTVDB PIN (nur v4, optional)'), config.plugins.GradientWQHD.thetvdb_pin))
        self.list.append(getConfigListEntry(tr('TheTVDB Legacy API key (32 hex, optional fallback)', 'TheTVDB Legacy API-Key (32 Hex, optionaler Fallback)'), config.plugins.GradientWQHD.thetvdb_legacy_api))

        self.list.append(getConfigListEntry(tr('Fanart.tv API key (optional)', 'Fanart.tv API-Key (optional)'), config.plugins.GradientWQHD.fanart_api))

        ConfigListScreen.__init__(self, self.list, session=session)

        self['key_red'] = Label(tr('Cancel', 'Abbrechen'))
        self['key_green'] = Label(tr('Save', 'Speichern'))
        self['key_yellow'] = Label(tr('Clear', 'Leeren'))
        self['key_blue'] = Label(tr('Test', 'Test'))

        self['help'] = Label(tr(
            'OK=Virtual Keyboard | GREEN=Save | BLUE=Test | Empty fields => use built-in defaults',
            'OK=Virtuelle Tastatur | GRÜN=Speichern | BLAU=Test | Leere Felder => Defaults'
        ))

        self['actions'] = ActionMap(['SetupActions', 'ColorActions'], {
            'ok': self.keyEdit,
            'green': self.keySave,
            'red': self.keyCancel,
            'cancel': self.keyCancel,
            'yellow': self.keyClear,
            'blue': self.keyTest,
        }, -2)

    def _current_entry(self):
        try:
            cur = self['config'].getCurrent()
            if cur and len(cur) >= 2:
                return cur[0], cur[1]
        except Exception:
            pass
        return None, None

    def keyEdit(self):
        title, cfg = self._current_entry()
        if cfg is None:
            return
        try:
            from Screens.VirtualKeyBoard import VirtualKeyBoard
        except Exception:
            self.session.open(MessageBox, tr('VirtualKeyBoard not available', 'Virtuelle Tastatur nicht verfügbar'), MessageBox.TYPE_ERROR)
            return
        self.session.openWithCallback(lambda txt: self._vk_cb(cfg, txt), VirtualKeyBoard, title=title, text=cfg.value)

    def _vk_cb(self, cfg, txt):
        if txt is None:
            return
        cfg.value = txt.strip()
        self['config'].invalidateCurrent()

    def keyClear(self):
        config.plugins.GradientWQHD.tmdb_api.value = ''
        config.plugins.GradientWQHD.omdb_api.value = ''
        config.plugins.GradientWQHD.thetvdb_v4_api.value = ''
        config.plugins.GradientWQHD.thetvdb_legacy_api.value = ''
        config.plugins.GradientWQHD.thetvdb_pin.value = ''
        config.plugins.GradientWQHD.fanart_api.value = ''
        self['config'].setList(self.list)

    def keySave(self):
        sd = _skin_dir()

        tmdb = (config.plugins.GradientWQHD.tmdb_api.value or '').strip()
        omdb = (config.plugins.GradientWQHD.omdb_api.value or '').strip()
        tvdb_v4 = (config.plugins.GradientWQHD.thetvdb_v4_api.value or '').strip()
        tvdb_legacy = (config.plugins.GradientWQHD.thetvdb_legacy_api.value or '').strip()
        tvdb_pin = (config.plugins.GradientWQHD.thetvdb_pin.value or '').strip()
        fanart = (config.plugins.GradientWQHD.fanart_api.value or '').strip()

        # Validation (soft)
        if tvdb_v4 and (not _is_tvdb_v4_key(tvdb_v4)):
            self.session.open(MessageBox, tr(
                'TheTVDB v4 key does not look like a UUID. It may not work.',
                'TheTVDB v4 Key sieht nicht wie eine UUID aus. Funktion evtl. nicht.'
            ), MessageBox.TYPE_INFO, timeout=6)

        if tvdb_legacy and (not _is_tvdb_legacy_key(tvdb_legacy)):
            self.session.open(MessageBox, tr(
                'TheTVDB legacy key does not look like 32 hex chars. It may not work.',
                'TheTVDB Legacy Key sieht nicht wie 32 Hex-Zeichen aus. Funktion evtl. nicht.'
            ), MessageBox.TYPE_INFO, timeout=6)

        ok = True
        ok &= _write_or_remove(os.path.join(sd, 'tmdbkey'), tmdb)
        ok &= _write_or_remove(os.path.join(sd, 'apikey'), tmdb)
        ok &= _write_or_remove(os.path.join(sd, 'omdbkey'), omdb)

        # v4 main key (used by patched download threads)
        ok &= _write_or_remove(os.path.join(sd, 'thetvdbkey'), tvdb_v4)
        ok &= _write_or_remove(os.path.join(sd, 'thetvdbpin'), tvdb_pin)

        # legacy fallback key (optional)
        ok &= _write_or_remove(os.path.join(sd, 'thetvdbkey_legacy'), tvdb_legacy)

        ok &= _write_or_remove(os.path.join(sd, 'fanartkey'), fanart)

        if ok:
            self.session.open(MessageBox, tr(
                'Saved. Re-run AutoDB to refresh artwork.',
                'Gespeichert. AutoDB neu starten um Artwork zu aktualisieren.'
            ), MessageBox.TYPE_INFO, timeout=6)
        else:
            self.session.open(MessageBox, tr(
                'Could not write one or more key files (permission / read-only filesystem).',
                'Konnte eine oder mehrere Key-Dateien nicht schreiben (Rechte / read-only).'
            ), MessageBox.TYPE_ERROR)

    def keyTest(self):
        tmdb = (config.plugins.GradientWQHD.tmdb_api.value or '').strip()
        omdb = (config.plugins.GradientWQHD.omdb_api.value or '').strip()
        tvdb_v4 = (config.plugins.GradientWQHD.thetvdb_v4_api.value or '').strip()
        tvdb_legacy = (config.plugins.GradientWQHD.thetvdb_legacy_api.value or '').strip()
        tvdb_pin = (config.plugins.GradientWQHD.thetvdb_pin.value or '').strip()
        fanart = (config.plugins.GradientWQHD.fanart_api.value or '').strip()

        lines = []

        # TMDb
        if tmdb:
            code, _ = _http_get('https://api.themoviedb.org/3/configuration?api_key=%s' % tmdb)
            lines.append('TMDb: %s' % ('OK' if code == 200 else 'FAIL (HTTP %s)' % code))
        else:
            lines.append('TMDb: %s' % tr('EMPTY (default)', 'LEER (Default)'))

        # OMDb
        if omdb:
            code, txt = _http_get('http://www.omdbapi.com/?apikey=%s&t=Matrix' % omdb)
            ok = (code == 200 and '"Response":"True"' in txt)
            lines.append('OMDb: %s' % ('OK' if ok else 'FAIL (HTTP %s)' % code))
        else:
            lines.append('OMDb: %s' % tr('EMPTY (default)', 'LEER (Default)'))

        # TVDB v4
        if tvdb_v4:
            if not _is_tvdb_v4_key(tvdb_v4):
                lines.append('TVDB v4: %s' % tr('INVALID FORMAT (UUID expected)', 'FALSCHES FORMAT (UUID erwartet)'))
            else:
                ok, msg = _tvdb_v4_login_and_search(tvdb_v4, pin=tvdb_pin)
                lines.append('TVDB v4: %s' % msg)
        else:
            lines.append('TVDB v4: %s' % tr('EMPTY', 'LEER'))

        # TVDB legacy
        if tvdb_legacy:
            if not _is_tvdb_legacy_key(tvdb_legacy):
                lines.append('TVDB legacy: %s' % tr('INVALID FORMAT (32 hex expected)', 'FALSCHES FORMAT (32 Hex erwartet)'))
            else:
                ok, msg = _tvdb_legacy_xml_test(tvdb_legacy)
                lines.append('TVDB legacy: %s' % msg)
        else:
            # If legacy empty, attempt to test renderer built-in default (optional)
            try:
                from Components.Renderer import GradientPosterXDownloadThread as t
                k = getattr(t, 'TVDB_LEGACY_DEFAULT_KEY', None)
                if k:
                    ok, msg = _tvdb_legacy_xml_test(str(k))
                    lines.append('TVDB legacy (renderer default): %s' % msg)
                else:
                    lines.append('TVDB legacy: %s' % tr('EMPTY', 'LEER'))
            except Exception:
                lines.append('TVDB legacy: %s' % tr('EMPTY', 'LEER'))

        # Fanart
        if fanart:
            code, _ = _http_get('https://webservice.fanart.tv/v3/tv/121361?api_key=%s' % fanart)
            lines.append('Fanart: %s' % ('OK' if code == 200 else 'FAIL (HTTP %s)' % code))
        else:
            lines.append('Fanart: %s' % tr('EMPTY', 'LEER'))

        self.session.open(MessageBox, '\n'.join(lines), MessageBox.TYPE_INFO)

    def keyCancel(self):
        self.close()
