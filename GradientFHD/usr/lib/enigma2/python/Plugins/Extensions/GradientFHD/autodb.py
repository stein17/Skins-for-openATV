# -*- coding: utf-8 -*-
# Integrated AutoDB module (extracted from AutoDBManager v19)
# This file is meant to be imported from the GradientFHD Configtool.
# 02.26 @stein17, Many new features and improvements

# -*- coding: utf-8 -*-
from __future__ import absolute_import
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox


# ---------------------------------------------------------------------
# Built-in language fallback (no .mo needed)
# Default language is English. If GUI language starts with 'de', show German strings.
try:
    from Components.Language import language
    _LANG = (language.getLanguage() or "en").lower()
except Exception:
    _LANG = "en"

def tr(en, de=None):
    """Return translated string without requiring gettext files."""
    try:
        if de and _LANG.startswith("de"):
            return de
    except Exception:
        pass
    return en
# ---------------------------------------------------------------------

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Button import Button

from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Tools.LoadPixmap import LoadPixmap

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER, eTimer

import os
import re
import time

try:
    from Tools import Notifications
except Exception:
    Notifications = None

try:
    from enigma import eActionMap
except Exception:
    eActionMap = None

print('[AutoDBManager] plugin loaded (v19)')

BOUQUET_FILE = '/etc/enigma2/poster_autodb_bouquets.txt'
BOUQUET_DIR = '/etc/enigma2'
BOUQUETS_TV = os.path.join(BOUQUET_DIR, 'bouquets.tv')

LOGDIR = '/var/volatile/tmp' if os.path.isdir('/var/volatile/tmp') else '/tmp'
POSTER_LOG = os.path.join(LOGDIR, 'PosterAutoDB.log')
BACKDROP_LOG = os.path.join(LOGDIR, 'BackdropAutoDB.log')
STATUS_FILE = os.path.join(LOGDIR, 'autodb_last_run.txt')

TRIG_POSTER = '/tmp/run_poster_autodb_once'
TRIG_BACKDROP = '/tmp/run_backdrop_autodb_once'

STOP_POSTER = '/tmp/stop_poster_autodb'
STOP_BACKDROP = '/tmp/stop_backdrop_autodb'

SW_ON = '/usr/share/enigma2/GradientFHD/icons/menu_on.png'
SW_OFF = '/usr/share/enigma2/GradientFHD/icons/menu_off.png'


HINT_TEXT = (
    'DE: Bitte aktiviere nur Bouquets, für die das EPG bereits geladen ist.\n'
    '    Nur bei geladenem EPG kann AutoDB im Hintergrund nach Sendungen scannen (nächste 24h).\n'
    '    Tipp: Einmal kurz durch die gewünschten Bouquets zappen und ein paar Sekunden warten.\n\n'
    'EN: Please enable only bouquets with loaded EPG data.\n'
    '    AutoDB can scan programmes (next 24h) only when the EPG cache is filled.\n'
    '    Tip: zap through selected bouquets once and wait a few seconds.\n\n'
)

def _fmt_mb(num_bytes):
    try:
        return '%.1f MB' % (float(num_bytes) / 1024.0 / 1024.0)
    except Exception:
        return '0.0 MB'


def _scan_cache_dir(path):
    count = 0
    size = 0
    if not os.path.isdir(path):
        return count, size
    try:
        for root, dirs, files in os.walk(path):
            for fn in files:
                fp = os.path.join(root, fn)
                count += 1
                try:
                    size += os.path.getsize(fp)
                except Exception:
                    pass
    except Exception:
        pass
    return count, size


def build_autodb_info_text():
    items = [
        (tr('Poster', 'Poster'), '/media/hdd/xtra/poster'),
        (tr('Backdrop', 'Backdrop'), '/media/hdd/xtra/backdrop'),
        (tr('Info-json', 'Info-json'), '/media/hdd/xtra/Info'),
    ]

    lines = [HINT_TEXT.strip(), '']
    total_size = 0

    lines.append(tr('Current TV cache:', 'Aktueller TV-Cache:'))
    for label, path in items:
        cnt, sz = _scan_cache_dir(path)
        total_size += sz
        lines.append('%s: %d (~%s)' % (label, cnt, _fmt_mb(sz)))

    lines.append('')
    lines.append('%s ~%s' % (tr('Total TV cache:', 'Gesamt TV-Cache:'), _fmt_mb(total_size)))
    return '\n'.join(lines)


def _notify(text, timeout=5, mtype=None):
    # Prefer non-modal popup if available; AddNotification(MessageBox, ...) can block keys on some images.
    try:
        if Notifications is None:
            return
        if mtype is None:
            mtype = MessageBox.TYPE_INFO

        # Newer/most images: AddPopup is non-blocking.
        if hasattr(Notifications, 'AddPopup'):
            try:
                Notifications.AddPopup(text, mtype, int(timeout))
                return
            except Exception:
                pass

        # Fallback (may be modal on some images)
        Notifications.AddNotification(MessageBox, text, type=mtype, timeout=int(timeout))
    except Exception:
        pass



def _write_status(text):
    try:
        with open(STATUS_FILE, 'w') as f:
            f.write(text.strip() + '\n')
    except Exception:
        pass


def _load_switch(enabled):
    path = SW_ON if enabled else SW_OFF
    try:
        return LoadPixmap(path=path)
    except Exception:
        return None


def _read_lines(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            return [ln.rstrip('\n') for ln in f]
    except Exception:
        return []


def _parse_bouquet_file(lines):
    out = []
    for ln in lines:
        s = (ln or '').strip()
        if not s or s.startswith('#'):
            continue
        if '|' not in s:
            continue
        flag, rest = s.split('|', 1)
        enabled = (flag.strip() != '0')
        parts = rest.strip().split()
        if not parts:
            continue
        bid = parts[0].strip()
        name = bid
        if '#NAME' in rest:
            try:
                name = rest.split('#NAME', 1)[1].strip()
            except Exception:
                name = bid
        out.append({'enabled': enabled, 'bouquet_id': bid, 'name': name})
    return out


def _read_first_bouquet_name(bouquet_path):
    """Return the bouquet display name from '#NAME ...' inside the bouquet file."""
    if not bouquet_path or not os.path.exists(bouquet_path):
        return None
    # Bouquet files are usually UTF-8, but some setups still contain legacy encodings.
    for enc in ('utf-8', 'latin-1'):
        try:
            with open(bouquet_path, 'r', encoding=enc, errors='ignore') as f:
                for ln in f:
                    if ln.startswith('#NAME'):
                        return ln[5:].strip() or None
        except Exception:
            pass
    return None


_RE_FROM_BOUQUET = re.compile(r'FROM\s+BOUQUET\s+"([^"]+)"', re.IGNORECASE)


def _discover_bouquets_from_bouquets_tv():
    """Build bouquet entries from /etc/enigma2/bouquets.tv.

    We extract userbouquet filenames and open each file to read its '#NAME'.
    """
    lines = _read_lines(BOUQUETS_TV)
    bouquet_ids = []

    for ln in lines:
        if not ln or 'FROM BOUQUET' not in ln:
            continue
        m = _RE_FROM_BOUQUET.search(ln)
        if not m:
            continue
        bid = (m.group(1) or '').strip()
        if not bid:
            continue
        # Deduplicate while keeping order
        if bid not in bouquet_ids:
            bouquet_ids.append(bid)

    # Fallback: if bouquets.tv is missing or contains no bouquet references,
    # list all userbouquet*.tv files in /etc/enigma2.
    if not bouquet_ids:
        try:
            for fn in sorted(os.listdir(BOUQUET_DIR)):
                low = fn.lower()
                if not (low.startswith('userbouquet.') and low.endswith('.tv')):
                    continue
                # Skip helper/temporary bouquets if present
                if 'lastscanned' in low:
                    continue
                if fn not in bouquet_ids:
                    bouquet_ids.append(fn)
        except Exception:
            pass

    out = []
    for bid in bouquet_ids:
        bpath = os.path.join(BOUQUET_DIR, bid)
        name = _read_first_bouquet_name(bpath) or bid

        # Safe defaults: enable favourites by default, keep others disabled.
        low = bid.lower()
        enabled = ('favourites' in low) or ('favoriten' in low)
        if 'lastscanned' in low:
            enabled = False

        out.append({'enabled': bool(enabled), 'bouquet_id': bid, 'name': name})

    return out


def _enrich_entries_with_names(entries):
    """Fill missing/placeholder names by reading the bouquet files."""
    changed = False
    for e in entries or []:
        bid = e.get('bouquet_id')
        if not bid:
            continue
        name = (e.get('name') or '').strip()
        if (not name) or (name == bid):
            bpath = os.path.join(BOUQUET_DIR, bid)
            new_name = _read_first_bouquet_name(bpath)
            if new_name and new_name != name:
                e['name'] = new_name
                changed = True
    return changed


def _write_bouquet_file(entries):
    try:
        with open(BOUQUET_FILE, 'w') as f:
            f.write('# ==============================================\n')
            f.write('# Poster/Backdrop-AutoDB Bouquets\n')
            f.write('# ==============================================\n')
            f.write('# DE: 1=aktiv, 0=aus.\n')
            f.write('# EN: 1=enabled, 0=disabled.\n')
            f.write('#\n')
            for ln in HINT_TEXT.split('\n'):
                f.write('# ' + ln + '\n')
            f.write('# ==============================================\n\n')

            for e in entries:
                flag = '1' if e.get('enabled') else '0'
                bid = e.get('bouquet_id') or ''
                name = e.get('name') or ''
                if name and name != bid:
                    f.write('%s|%s  #NAME %s\n' % (flag, bid, name))
                else:
                    f.write('%s|%s\n' % (flag, bid))
        return True
    except Exception:
        return False


def _count_services(entries):
    services = set()
    active_bq = 0

    for e in entries:
        if not e.get('enabled'):
            continue
        active_bq += 1
        bid = e.get('bouquet_id')
        if not bid:
            continue
        fn = os.path.join(BOUQUET_DIR, bid)
        if not os.path.exists(fn):
            continue
        try:
            with open(fn, 'r') as f:
                for ln in f:
                    if not ln.startswith('#SERVICE'):
                        continue
                    if 'FROM BOUQUET' in ln:
                        continue
                    ref = ln[9:].strip().split('::', 1)[0].strip()
                    if not ref:
                        continue
                    parts = ref.split(':')
                    if len(parts) >= 11:
                        ref = ':'.join(parts[:11])
                    services.add(ref)
        except Exception:
            pass

    return active_bq, len(services)


def _touch(path):
    try:
        with open(path, 'w') as f:
            f.write('1')
        return True
    except Exception:
        try:
            open(path, 'a').close()
            return True
        except Exception:
            return False


def _remove(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _return_to_livetv(session):
    try:
        stack = list(getattr(session, 'dialog_stack', []) or [])
    except Exception:
        stack = []

    dialogs = []
    for item in stack:
        try:
            dlg = item[0] if isinstance(item, (list, tuple)) else item
        except Exception:
            dlg = None
        if dlg is not None:
            dialogs.append(dlg)

    names_to_close = set([
        'PluginBrowser', 'PluginBrowserSetup', 'Setup', 'PluginBrowserSetupSummary', 'SetupSummary', 'ChoiceBox', 'ExtensionsList', 'ExtensionsMenu'
    ])

    for dlg in reversed(dialogs):
        try:
            nm = dlg.__class__.__name__
        except Exception:
            nm = ''
        if nm in names_to_close:
            try:
                dlg.close()
            except Exception:
                pass


class AutoDBStatusOSD(Screen):
    skin = """
        <screen name="AutoDBStatusOSD" position="10,10" size="980,40" backgroundColor="#80000000" cornerRadius="16" flags="wfNoBorder" zPosition="999">
            <widget name="text" position="center,0" size="980,40" font="Regular;27" valign="center" halign="center" cornerRadius="16" transparent="1" foregroundColor="#ffffff" borderWidth="1" borderColor="black" />
        </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self['text'] = Label('AutoDB ...')
        try:
            self.onShown.append(lambda: self.instance.setFocus(None))
        except Exception:
            pass

    def setText(self, t):
        try:
            self['text'].setText(t)
        except Exception:
            pass


class AutoDBRunWatcher(object):
    RX_TOTAL = re.compile(r"Total services in apdb:\s*(\d+)")
    RX_ADDED = re.compile(r"\]\s*(\d+)\s+new file\(s\) added\s*\(")
    RX_FIN = re.compile(r"\*\*\* Job finished \*\*\*")
    RX_ACTIVITY = re.compile(r"\*\*\* Triggered run requested \*\*\*|\*\*\* Running \*\*\*|Total services in apdb")

    DOUBLE_EXIT_WINDOW = 1.2
    EXIT_DEBOUNCE = 0.35

    def __init__(self):
        self.timer = eTimer()
        self._osd_finish_timer = None
        try:
            self.timer_conn = self.timer.timeout.connect(self._tick)
        except Exception:
            self.timer.callback.append(self._tick)

        self.running = False
        self.want_poster = False
        self.want_backdrop = False

        self._pos_p = 0
        self._pos_b = 0
        self._start_ts = 0

        self._saw_activity_p = False
        self._saw_activity_b = False

        self.total_p = 0
        self.total_b = 0
        self.done_p = 0
        self.done_b = 0
        self.new_p = 0
        self.new_b = 0

        self.session = None
        self.osd = None
        self.osd_visible = True

        self._hooked = False
        self._last_exit_press_ts = 0.0
        self._last_exit_event_ts = 0.0
        self._stop_requested = False
        self._stop_box_open = False

    def _seek_end(self, path):
        try:
            return os.path.getsize(path)
        except Exception:
            return 0

    def _close_osd(self):
        try:
            if self.osd is not None:
                self.osd.hide()
        except Exception:
            pass
        try:
            if self.osd is not None:
                self.osd.close()
        except Exception:
            pass
        self.osd = None

    def _ensure_osd(self):
        if not self.osd_visible:
            return
        if self.session is None:
            return
        if self.osd is not None:
            return
        try:
            self.osd = self.session.instantiateDialog(AutoDBStatusOSD)
            self.osd.show()
        except Exception:
            self.osd = None

    def _hook_global_exit(self):
        if self._hooked:
            return
        if eActionMap is None:
            return
        for ctx in ('OkCancelActions', 'InfobarShowHideActions'):
            try:
                eActionMap.getInstance().bindAction(ctx, -0x7FFFFFFF, self._on_global_action)
                self._hooked = True
            except Exception:
                pass

    def _is_exit_action(self, args):
        for a in args:
            if isinstance(a, int) and (a == 0xAE or a == 174):
                return True
        for a in args:
            if isinstance(a, str) and a in ('cancel', 'exit', 'hide'):
                return True
        return False

    def _exit_hook_allowed(self):
        """Return True if global EXIT hook should be active in the current GUI context.

        IMPORTANT:
        - EXIT must keep its normal meaning (close plugin / menu / list) everywhere.
        - We only intercept EXIT in plain LiveTV (InfoBar on top).
        """
        try:
            dlg = getattr(self.session, 'current_dialog', None)
        except Exception:
            dlg = None
        if dlg is None:
            return False
        try:
            nm = dlg.__class__.__name__ or ''
        except Exception:
            nm = ''

        # Intercept only in LiveTV / InfoBar.
        # In menus, plugin browser, channel list, movie list etc. EXIT must close the screen as usual.
        return (nm.startswith('InfoBar') or nm == 'InfoBar')


    def _on_global_action(self, *args, **kwargs):
        if not self.running:
            return 0
        if not self._is_exit_action(args):
            return 0
        if self.session is None:
            return 0

        # Intercept EXIT only in allowed contexts.
        if not self._exit_hook_allowed():
            return 0

        now = time.time()
        if self._last_exit_event_ts and (now - self._last_exit_event_ts) < self.EXIT_DEBOUNCE:
            return 0
        self._last_exit_event_ts = now

        # IMPORTANT:
        # Never open a MessageBox directly inside the global action callback.
        # Some images can deadlock input handling if a modal dialog is spawned from here.
        # Solution: schedule the prompt via a short timer (mainloop-safe).
        if self._stop_box_open:
            return 0
        self._stop_box_open = True

        def _cb(ans):
            try:
                self._stop_box_open = False
                if ans:
                    self.stop_requested(user_initiated=True)
            except Exception:
                self._stop_box_open = False

        def _open_prompt():
            try:
                self.session.openWithCallback(
                    _cb,
                    MessageBox,
                    tr('Do you really want to stop AutoDB?', 'Wollen Sie AutoDB wirklich beenden?'),
                    type=MessageBox.TYPE_YESNO,
                    default=False
                )
            except Exception:
                self._stop_box_open = False

        try:
            t = eTimer()
            t.callback.append(_open_prompt)
            t.start(50, True)
            self._stop_prompt_timer = t
        except Exception:
            _open_prompt()
        return 0

    def stop_requested(self, user_initiated=False):
        if not self.running:
            return
        if self._stop_requested:
            return
        self._stop_requested = True

        if self.want_poster:
            _touch(STOP_POSTER)
        if self.want_backdrop:
            _touch(STOP_BACKDROP)

        self.osd_visible = False
        self._close_osd()

        self.running = False
        try:
            self.timer.stop()
        except Exception:
            pass

        if user_initiated:
            _notify('AutoDB STOP angefordert.', timeout=5)
        _write_status('state=stop_requested\nend=%s\n' % time.strftime('%Y-%m-%d %H:%M:%S'))

    def _schedule_close_pluginbrowser(self):
        # Close PluginBrowser/PluginBrowserGrid automatically after starting a scan.
        # Some images leave PluginBrowser active, requiring manual EXIT.
        try:
            if self.session is None:
                return
            self._pb_close_tries = 0
            self._pb_close_timer = eTimer()
            self._pb_close_timer.callback.append(self._try_close_pluginbrowser)
            self._pb_close_timer.start(150, True)
        except Exception:
            pass

    def _try_close_pluginbrowser(self):
        try:
            self._pb_close_tries += 1
            if self.session is None:
                return

            dlg = getattr(self.session, 'current_dialog', None)
            if dlg is not None and dlg.__class__.__name__ in ('PluginBrowser', 'PluginBrowserGrid'):
                try:
                    dlg.close()
                    return
                except Exception:
                    pass

            stack = getattr(self.session, 'dialog_stack', None)
            if stack:
                for d in list(stack):
                    try:
                        if d is not None and d.__class__.__name__ in ('PluginBrowser', 'PluginBrowserGrid'):
                            d.close()
                    except Exception:
                        pass

            if getattr(self, '_pb_close_tries', 0) < 10:
                self._pb_close_timer.start(150, True)
        except Exception:
            pass

    def start(self, session, run_poster, run_backdrop, active_bq, total_srv):
        self.session = session
        self.want_poster = bool(run_poster)
        self.want_backdrop = bool(run_backdrop)

        _remove(STOP_POSTER)
        _remove(STOP_BACKDROP)

        self._pos_p = self._seek_end(POSTER_LOG) if self.want_poster else 0
        self._pos_b = self._seek_end(BACKDROP_LOG) if self.want_backdrop else 0

        self._saw_activity_p = (not self.want_poster)
        self._saw_activity_b = (not self.want_backdrop)

        self.total_p = 0
        self.total_b = 0
        self.done_p = 0
        self.done_b = 0
        self.new_p = 0
        self.new_b = 0

        self._start_ts = time.time()
        self.running = True
        self.osd_visible = True
        self._stop_requested = False
        self._stop_box_open = False

        self._last_exit_press_ts = 0.0
        self._last_exit_event_ts = 0.0

        mode = tr('Poster and Backdrop', 'Poster und Backdrop') if (self.want_poster and self.want_backdrop) else ('Poster' if self.want_poster else 'Backdrop')
        _write_status('state=running\nstart=%s\nmode=%s\nactive_bouquets=%d\nservices_selected=%d\n' % (
            time.strftime('%Y-%m-%d %H:%M:%S'), mode, int(active_bq), int(total_srv)
        ))
        # NOTE: Do not show modal start MessageBox/Notification (can block remote). OSD shows status.
        # _notify('AutoDB gestartet (%s).' % mode, timeout=8)

        self._hook_global_exit()
        self._ensure_osd()
        # Auto-close PluginBrowser so LiveTV is immediately usable
        self._schedule_close_pluginbrowser()

        self.timer.start(1000, False)

    def _read_chunk(self, path, pos):
        try:
            if not os.path.exists(path):
                return '', pos
            with open(path, 'r') as f:
                f.seek(pos)
                data = f.read()
                pos = f.tell()
            return data, pos
        except Exception:
            return '', pos

    def _update_from_log(self, data, kind):
        if not data:
            return

        m = self.RX_TOTAL.search(data)
        if m:
            tot = int(m.group(1) or 0)
            if kind == 'poster':
                self.total_p = tot
            else:
                self.total_b = tot

        for m in self.RX_ADDED.finditer(data):
            n = int(m.group(1) or 0)
            if kind == 'poster':
                self.done_p += 1
                self.new_p += n
            else:
                self.done_b += 1
                self.new_b += n

    def _pct(self, done, total):
        return int((done * 100) / total) if total else 0

    def _fmt(self):
        elapsed = int(time.time() - self._start_ts) if self._start_ts else 0
        mm = elapsed // 60
        ss = elapsed % 60

        parts = []
        if self.want_poster:
            parts.append(tr('Poster %d%% (%d/%d) New:%d', 'Poster %d%% (%d/%d) Neu:%d') % (self._pct(self.done_p, self.total_p), self.done_p, self.total_p, self.new_p))
        if self.want_backdrop:
            parts.append(tr('Backdrop %d%% (%d/%d) New:%d', 'Backdrop %d%% (%d/%d) Neu:%d') % (self._pct(self.done_b, self.total_b), self.done_b, self.total_b, self.new_b))

        return 'AutoDB: ' + ' | '.join(parts) + '  %02d:%02d' % (mm, ss)

    def _tick(self):
        if not self.running:
            try:
                self.timer.stop()
            except Exception:
                pass
            return

        if self.want_poster:
            data, self._pos_p = self._read_chunk(POSTER_LOG, self._pos_p)
            if data:
                if self.RX_ACTIVITY.search(data):
                    self._saw_activity_p = True
                self._update_from_log(data, 'poster')
                if self._saw_activity_p and self.RX_FIN.search(data):
                    self.want_poster = False

        if self.want_backdrop:
            data, self._pos_b = self._read_chunk(BACKDROP_LOG, self._pos_b)
            if data:
                if self.RX_ACTIVITY.search(data):
                    self._saw_activity_b = True
                self._update_from_log(data, 'backdrop')
                if self._saw_activity_b and self.RX_FIN.search(data):
                    self.want_backdrop = False

        self._ensure_osd()
        if self.osd is not None:
            try:
                self.osd.setText(self._fmt())
            except Exception:
                pass

        if (not self.want_poster) and (not self.want_backdrop):
            self.running = False
            try:
                self.timer.stop()
            except Exception:
                pass

            self.osd_visible = False
            if self.osd is not None:
                try:
                    self.osd.setText(self._fmt() + '  (fertig)')
                except Exception:
                    pass
                # Keep timer as attribute; local eTimer can be GC'ed on some images before it fires.
                self._osd_finish_timer = eTimer()

                def _close():
                    try:
                        self._close_osd()
                    except Exception:
                        pass
                    try:
                        if self._osd_finish_timer is not None:
                            self._osd_finish_timer.stop()
                    except Exception:
                        pass
                    self._osd_finish_timer = None

                try:
                    self._osd_finish_timer.timeout.connect(_close)
                except Exception:
                    self._osd_finish_timer.callback.append(_close)
                self._osd_finish_timer.start(2000, True)
            _notify('AutoDB fertig.', timeout=4)
            _write_status('state=finished\nend=%s\n' % time.strftime('%Y-%m-%d %H:%M:%S'))


WATCHER = AutoDBRunWatcher()


class AutoDBInfoScreen(Screen):
    skin = """
    <screen name="AutoDBInfoScreen" position="center,center" size="1100,680" title="Information" flags="wfNoBorder" backgroundColor="transparent">
        <widget source="Title" render="Label" position="20,0" size="1060,60" font="Italic; 42" halign="left" valign="center" transparent="1" foregroundColor="gradient_foreground_selection" backgroundColor="background" textBorderColor="black" textBorderWidth="1" zPosition="1" />
        <eLabel name="menu_bg" position="0,60" size="1100,620" backgroundColor="gradient_BGO,gradient_BGM,gradient_BGU,vertical" zPosition="-8" />
        <eLabel name="title_bg" position="0,0" size="1100,70" backgroundColor="gradient_TBGL,gradient_BGO,gradient_BGU,horizontal" zPosition="-9" cornerRadius="12" />
        <eLabel name="title_line" position="0,60" size="1100,4" backgroundColor="gradient_background,gradient_BGLR,gradient_BGLM,horizontal" zPosition="10" />
        <eLabel name="Line_Menu" position="15,625" size="1070,2" backgroundColor="gradient_BGLR,gradient_BGLM,gradient_BGLR,horizontal" zPosition="10" />
        <eLabel name="Line_Menu" position="15,375" size="1070,2" backgroundColor="gradient_BGLR,gradient_BGLM,gradient_BGLR,horizontal" zPosition="10" />
        <widget name="text" position="20,70" size="1060,540" font="Regular;30" backgroundColor="gradient_background" halign="left" valign="top" transparent="1" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self['title_lbl'] = Label(tr('Information', 'Informationen'))
        self['text'] = Label(build_autodb_info_text())
        self['actions'] = ActionMap(
            ['OkCancelActions', 'ColorActions'],
            {
                'ok': self.close,
                'cancel': self.close,
                'blue': self.close,
            },
            -1
        )


class AutoDBManager(Screen):
    skin = """
    <screen name="AutoDBManager" position="center,center" size="1100,680" title="AutoDB Manager (Poster + Backdrop)" flags="wfNoBorder" backgroundColor="transparent">
        <widget source="Title" render="Label" position="20,0" size="1060,60" font="Italic; 42" halign="left" valign="center" transparent="1" foregroundColor="gradient_foreground_selection" backgroundColor="background" textBorderColor="black" textBorderWidth="1" zPosition="1" />
        <eLabel name="menu_bg" position="0,60" size="1100,620" backgroundColor="gradient_BGO,gradient_BGM,gradient_BGU,vertical" zPosition="-8" />
        <eLabel name="title_bg" position="0,0" size="1100,70" backgroundColor="gradient_TBGL,gradient_BGO,gradient_BGU,horizontal" zPosition="-9" cornerRadius="12" />
        <eLabel name="title_line" position="0,60" size="1100,4" backgroundColor="gradient_background,gradient_BGLR,gradient_BGLM,horizontal" zPosition="10" />
        <eLabel name="Line_Menu" position="15,625" size="1070,2" backgroundColor="gradient_BGLR,gradient_BGLM,gradient_BGLR,horizontal" zPosition="10" />
        <widget name="list" position="20,70" size="1060,540" font="Regular;30" backgroundColor="gradient_background" scrollbarMode="showOnDemand" itemHeight="45" transparent="1" />
        <ePixmap pixmap="buttons/key_red.png" position="20,640" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_green.png" position="320,640" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_yellow.png" position="590,640" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_blue.png" position="860,640" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <widget name="key_red" position="60,635" size="260,40" backgroundColor="gradient_background" font="Regular;24" valign="center" halign="left" transparent="1" />
        <widget name="key_green" position="360,635" size="220,40" backgroundColor="gradient_background" font="Regular;24" valign="center" halign="left" transparent="1" />
        <widget name="key_yellow" position="630,635" size="220,40" backgroundColor="gradient_background" font="Regular;24" valign="center" halign="left" transparent="1" />
        <widget name="key_blue" position="900,635" size="220,40" backgroundColor="gradient_background" font="Regular;24" valign="center" halign="left" transparent="1" />
    </screen>
    """

    ROW_OPTION = 'option'
    ROW_BOUQUET = 'bouquet'
    ROW_SEP = 'sep'

    def __init__(self, session):
        Screen.__init__(self, session)

        self['title'] = Label('Setup-AutoDB-Scan')
        self['key_red'] = Button(tr('Reload bouquets', 'Bouquets neu einlesen'))
        self['key_green'] = Button(tr('Save', 'Speichern'))
        self['key_yellow'] = Button(tr('Start AutoDB', 'Start AutoDB'))
        self['key_blue'] = Button(tr('Info', 'Info'))

        self.run_poster = True
        self.run_backdrop = True

        # Load persisted bouquet selection (poster_autodb_bouquets.txt).
        # If missing/empty, auto-discover bouquets from bouquets.tv and read the real display names
        # from each userbouquet*.tv (#NAME ...).
        self.entries = _parse_bouquet_file(_read_lines(BOUQUET_FILE))
        if not self.entries:
            self.entries = _discover_bouquets_from_bouquets_tv()
            # Persist defaults so the UI is stable across restarts.
            _write_bouquet_file(self.entries)
        else:
            # If the file exists but names are missing/placeholder, enrich them from bouquet files.
            if _enrich_entries_with_names(self.entries):
                _write_bouquet_file(self.entries)

        self['list'] = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
        self['list'].l.setFont(0, gFont('Regular', 30))
        self['list'].l.setItemHeight(45)

        self['actions'] = ActionMap(
            ['OkCancelActions', 'ColorActions', 'DirectionActions'],
            {
                'ok': self.toggle,
                'left': self.keyLeft,
                'right': self.keyRight,
                'cancel': self.close,
                'red': self.reloadBouquets,
                'green': self.save,
                'yellow': self.confirm_start,
                'blue': self.show_info,
            },
            -1
        )

        self.refresh()

    def refresh(self):
        self['list'].setList(self._build_list())

    def reloadBouquets(self):
        """Rebuild bouquet list from bouquets.tv and refresh UI."""
        msg = tr(
            'Rebuild bouquet list from bouquets.tv? Existing selections will be kept when possible.',
            'Bouquet-Liste aus bouquets.tv neu einlesen? Vorhandene Auswahl wird nach Möglichkeit beibehalten.'
        )
        self.session.openWithCallback(self._reloadBouquetsConfirmed, MessageBox, msg, type=MessageBox.TYPE_YESNO, default=True)

    def _reloadBouquetsConfirmed(self, answer):
        if not answer:
            return

        # Preserve current enabled flags (by bouquet_id) where possible.
        old_flags = {}
        for e in self.entries or []:
            bid = e.get('bouquet_id')
            if bid:
                old_flags[bid] = bool(e.get('enabled'))

        self.entries = _discover_bouquets_from_bouquets_tv()

        for e in self.entries or []:
            bid = e.get('bouquet_id')
            if bid in old_flags:
                e['enabled'] = old_flags[bid]

        _write_bouquet_file(self.entries)
        self.refresh()

        self.session.open(
            MessageBox,
            tr('Bouquets reloaded.', 'Bouquets neu eingelesen.'),
            type=MessageBox.TYPE_INFO,
            timeout=3
        )


    def _row_option(self, key, label, enabled):
        png = _load_switch(enabled)
        data = (self.ROW_OPTION, key)
        res = [data]
        if png:
            res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 7), size=(64, 26), png=png))
        else:
            res.append(MultiContentEntryText(pos=(10, 0), size=(80, 42), font=0, text='[x]' if enabled else '[ ]',
                                             flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
        res.append(MultiContentEntryText(pos=(90, 0), size=(980, 42), font=0, text=label,
                                         flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
        return res

    def _row_sep(self, text):
        data = (self.ROW_SEP, None)
        res = [data]
        res.append(MultiContentEntryText(pos=(10, 0), size=(1040, 42), font=0, text=text,
                                         flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
        return res

    def _row_bouquet(self, bouquet_id, name, enabled):
        png = _load_switch(enabled)
        data = (self.ROW_BOUQUET, bouquet_id)
        res = [data]
        if png:
            res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 7), size=(64, 26), png=png))
        else:
            res.append(MultiContentEntryText(pos=(10, 0), size=(80, 42), font=0, text='[x]' if enabled else '[ ]',
                                             flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
        res.append(MultiContentEntryText(pos=(90, 0), size=(980, 42), font=0, text=name or bouquet_id,
                                         flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
        return res

    def _build_list(self):
        L = []
        L.append(self._row_option('poster', 'Poster AutoDB', self.run_poster))
        L.append(self._row_option('backdrop', 'Backdrop AutoDB', self.run_backdrop))
        L.append(self._row_sep(tr('Bouquets (AutoDB uses only services from enabled bouquets):', 'Bouquets (AutoDB verwendet nur Sender aus aktivierten Bouquets):')))
        for e in self.entries:
            L.append(self._row_bouquet(e.get('bouquet_id'), e.get('name'), bool(e.get('enabled'))))
        return L

    def _current_meta(self):
        sel = None
        try:
            sel = self['list'].l.getCurrentSelection()
        except Exception:
            sel = None
        try:
            if isinstance(sel, list) and len(sel) > 0 and isinstance(sel[0], tuple) and len(sel[0]) >= 2:
                return sel[0][0], sel[0][1]
        except Exception:
            pass
        return None, None

    def _set_current_state(self, enabled):
        rowtype, key = self._current_meta()
        if not rowtype or rowtype == self.ROW_SEP:
            return

        changed = False
        if rowtype == self.ROW_OPTION:
            if key == 'poster':
                if self.run_poster != bool(enabled):
                    self.run_poster = bool(enabled)
                    changed = True
            elif key == 'backdrop':
                if self.run_backdrop != bool(enabled):
                    self.run_backdrop = bool(enabled)
                    changed = True
        elif rowtype == self.ROW_BOUQUET:
            for e in self.entries:
                if e.get('bouquet_id') == key:
                    if e.get('enabled') != bool(enabled):
                        e['enabled'] = bool(enabled)
                        changed = True
                    break

        if changed:
            self.refresh()

    def keyLeft(self):
        self._set_current_state(False)

    def keyRight(self):
        self._set_current_state(True)

    def toggle(self):
        rowtype, key = self._current_meta()
        if not rowtype or rowtype == self.ROW_SEP:
            return

        if rowtype == self.ROW_OPTION:
            if key == 'poster':
                self.run_poster = not self.run_poster
            elif key == 'backdrop':
                self.run_backdrop = not self.run_backdrop
            self.refresh()
            return

        if rowtype == self.ROW_BOUQUET:
            for e in self.entries:
                if e.get('bouquet_id') == key:
                    e['enabled'] = not e.get('enabled')
                    break
            self.refresh()

    def show_info(self):
        self.session.open(AutoDBInfoScreen)

    def save(self):
        if _write_bouquet_file(self.entries):
            self.session.open(MessageBox, 'Gespeichert:\n%s' % BOUQUET_FILE, type=MessageBox.TYPE_INFO, timeout=4)
        else:
            self.session.open(MessageBox, 'Fehler beim Speichern!\n%s' % BOUQUET_FILE, type=MessageBox.TYPE_ERROR, timeout=6)

    def confirm_start(self):
        _write_bouquet_file(self.entries)

        if not self.run_poster and not self.run_backdrop:
            self.session.open(MessageBox, tr('Please enable at least Poster or Backdrop!', 'Bitte mindestens Poster oder Backdrop aktivieren!'), type=MessageBox.TYPE_ERROR, timeout=6)
            return

        active_bq, total_srv = _count_services(self.entries)
        mode = tr('Poster and Backdrop', 'Poster und Backdrop') if (self.run_poster and self.run_backdrop) else ('Poster' if self.run_poster else 'Backdrop')

        msg = (
            'Auswahl / Selection:\n'
            '  Mode: %s\n'
            '  Aktive Bouquets / Active bouquets: %d\n'
            '  Sender (ServiceRefs) / Services: %d\n\n'
            % (mode, int(active_bq), int(total_srv))
        )
        msg += (
            'Hinweis / Notice:\n'
            'Bitte darauf achten, dass für die ausgewählten Bouquets das EPG geladen ist.\n'
            'EXIT: In LiveTV/InfoBar fragt AutoDB nach „wirklich beenden?“ (Ja/Nein).\n\n'
            'Start now?'
        )

        self.session.openWithCallback(lambda ok: self._start_cb(ok, active_bq, total_srv), MessageBox, msg, type=MessageBox.TYPE_YESNO)

    def _start_cb(self, ok, active_bq, total_srv):
        if not ok:
            return

        # Ensure AutoDB workers are loaded even if no Infobar widgets are active
        try:
            if self.run_poster:
                from Components.Renderer import GradientPosterX  # noqa: F401
            if self.run_backdrop:
                from Components.Renderer import GradientBackdropX  # noqa: F401
        except Exception:
            pass

        if self.run_poster:
            _touch(TRIG_POSTER)
        if self.run_backdrop:
            _touch(TRIG_BACKDROP)

        WATCHER.start(self.session, self.run_poster, self.run_backdrop, active_bq, total_srv)

        t = eTimer()
        def _do():
            try:
                _return_to_livetv(self.session)
            except Exception:
                pass
        try:
            t.timeout.connect(_do)
        except Exception:
            t.callback.append(_do)
        t.start(250, True)

        self.close()
