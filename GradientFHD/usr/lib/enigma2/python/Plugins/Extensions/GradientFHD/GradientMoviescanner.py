# -*- coding: utf-8 -*-
#
# =============================================================================
#  DEUTSCH / GERMAN
# =============================================================================
#  MovieScanner for Enigma2 Skins
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
#  MovieScanner for Enigma2 Skins
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

import os
import re
import json
import time
import traceback
import threading
import types
import xml.etree.ElementTree as _ET
from datetime import datetime
from urllib.parse import quote, urlencode
import urllib.request
import urllib.error

# --- requests compatibility ---------------------------------------------------
# Some images ship without python3-requests. The original code uses `requests.*` in
# multiple places (also outside functions). Ensure `requests` always exists.
try:
    import requests as _requests  # type: ignore
except Exception:
    _requests = None

if _requests is None:
    class _CompatHTTPError(Exception):
        pass

    class _CompatResponse:
        def __init__(self, url, status_code, headers, content):
            self.url = url
            self.status_code = int(status_code)
            self.headers = headers or {}
            self.content = content or b""
            try:
                self.text = self.content.decode("utf-8", "ignore")
            except Exception:
                self.text = ""

        def json(self):
            return json.loads(self.text or "{}")

        def raise_for_status(self):
            if self.status_code >= 400:
                raise _CompatHTTPError("HTTP %s for %s" % (self.status_code, self.url))

    def _build_url(url, params):
        if not params:
            return url
        try:
            qs = urlencode(params, doseq=True)
        except Exception:
            qs = urlencode({k: str(v) for k, v in params.items()})
        sep = "&" if "?" in url else "?"
        return url + sep + qs

    def _urlopen(url, method="GET", headers=None, data=None, timeout=10):
        req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return _CompatResponse(url, getattr(resp, "status", 200), dict(getattr(resp, "headers", {}) or {}), resp.read())
        except urllib.error.HTTPError as e:
            try:
                body = e.read() or b""
            except Exception:
                body = b""
            return _CompatResponse(url, getattr(e, "code", 500), dict(getattr(e, "headers", {}) or {}), body)
        except Exception as e:
            # Mimic requests raising on connection problems
            raise e

    class _CompatRequests:
        class exceptions:
            RequestException = Exception
            HTTPError = _CompatHTTPError

        class utils:
            quote = staticmethod(quote)

        def get(self, url, headers=None, params=None, timeout=10, **kwargs):
            u = _build_url(url, params)
            return _urlopen(u, method="GET", headers=headers, timeout=timeout)

        def post(self, url, headers=None, json=None, data=None, timeout=10, **kwargs):
            hdrs = dict(headers or {})
            payload = None
            if json is not None:
                hdrs.setdefault("Content-Type", "application/json")
            # Avoid shadowing module name:
            if json is not None:
                payload = __import__("json").dumps(json).encode("utf-8")
            elif data is not None:
                if isinstance(data, (bytes, bytearray)):
                    payload = bytes(data)
                else:
                    payload = str(data).encode("utf-8")
            return _urlopen(url, method="POST", headers=hdrs, data=payload, timeout=timeout)

    requests = _CompatRequests()
else:
    requests = _requests

#New idea and features from @stein17 with the help of Python Code Generator

# --- OMDb enrichment helpers (added) ---


def _get_omdb_keys():
	"""Return list of OMDb keys (priority: plugin config -> scanner config -> skin files -> env)."""
	import os
	keys = []

	def _split(v):
		try:
			return [x.strip() for x in (v or '').split(',') if x.strip()]
		except Exception:
			return []

	# 1) Plugin API screen (api_keys_config.py)
	try:
		k = getattr(getattr(getattr(config, 'plugins', None), 'GradientFHD', None), 'omdb_api', None)
		if k and getattr(k, 'value', None):
			keys = _split(k.value)
	except Exception:
		pass

	# 2) Older / scanner field (compat)
	if not keys:
		try:
			k = getattr(getattr(getattr(getattr(config, 'plugins', None), 'GradientFHD', None), 'scanner', None), 'omdb_keys', None)
			if k and getattr(k, 'value', None):
				keys = _split(k.value)
		except Exception:
			pass

	# 3) Skin file written by API screen / renderers
	if not keys:
		try:
			skin = config.skin.primary_skin.value.replace('/skin.xml', '')
			key_file = '/usr/share/enigma2/%s/omdbkey' % skin
			if os.path.isfile(key_file):
				with open(key_file, 'r') as f:
					keys = _split((f.read() or '').strip())
		except Exception:
			pass

	# 4) Environment variable fallback
	if not keys:
		env = os.environ.get('OMDB_API', '') or os.environ.get('OMDBKEY', '')
		keys = _split(env)

	# 5) Legacy settings line (very old builds)
	if not keys:
		try:
			with open('/etc/enigma2/settings', 'r', encoding='utf-8', errors='ignore') as _sf:
				for line in _sf:
					if line.startswith('config.plugins.GradientFHD.scanner.omdb=') or line.startswith('config.plugins.GradientFHD.omdb_api='):
						val = line.split('=', 1)[1].strip()
						keys = _split(val)
						break
		except Exception:
			pass

	return keys

def _fill_if_empty(dst, key, val):
	if dst.get(key) in (None, "", "N/A") and val not in (None, "", "N/A"):
		dst[key] = val


def enrich_with_omdb_data(data, title_guess=None, year=None, typ=None):
	keys = _get_omdb_keys()
	if not keys:
		return data
	imdb = data.get('imdbID') or None
	last_err = None
	for k in keys:
		try:
			if imdb:
				url = f"http://www.omdbapi.com/?apikey={k}&i={imdb}&plot=short&r=json"
			else:
				if not title_guess:
					continue
				u = f"http://www.omdbapi.com/?apikey={k}&t={requests.utils.quote(title_guess)}&plot=short&r=json"
				if year:
					u += f"&y={year}"
				url = u
			r = requests.get(url, timeout=8)
			r.raise_for_status()
			js = r.json()
			if js.get('Response') != 'True':
				last_err = js.get('Error')
				continue
			_fill_if_empty(data, 'imdbRating', js.get('imdbRating'))
			_fill_if_empty(data, 'Genre', js.get('Genre'))
			_fill_if_empty(data, 'Duration', (js.get('Runtime') or '').replace(' min', ' min'))
			_fill_if_empty(data, 'Country', js.get('Country'))
			_fill_if_empty(data, 'Released', js.get('Released'))
			_fill_if_empty(data, 'Director', js.get('Director'))
			_fill_if_empty(data, 'Writer', js.get('Writer'))
			_fill_if_empty(data, 'Actors', js.get('Actors'))
			_fill_if_empty(data, 'Awards', js.get('Awards'))
			_fill_if_empty(data, 'Type', js.get('Type'))
			if not data.get('imdbID') and js.get('imdbID'):
				data['imdbID'] = js.get('imdbID')
			if not data.get('Plot') and js.get('Plot'):
				data['Plot'] = js.get('Plot')
			return data
		except Exception as e:
			last_err = str(e)
			continue
	return data


def enrich_with_omdb_path(jpath, title_guess=None, year=None, typ=None, lang=None, log_path=None):
	try:
		with open(jpath, 'r', encoding='utf-8') as _f:
			d = json.load(_f)
	except Exception:
		return
	d2 = enrich_with_omdb_data(d, title_guess, year, typ)
	if d2 != d:
		try:
			with open(jpath, 'w', encoding='utf-8') as _f:
				json.dump(d2, _f, ensure_ascii=False)
		except Exception as e:
			if log_path:
				try:
					with open(log_path, 'a+') as _lf:
						_lf.write(f"omdb enrich write error: {title_guess}, {e}\n")
				except Exception:
					pass
# --- end helpers ---


# Enigma2 UI
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import config, configfile, ConfigSubsection, getConfigListEntry, NoSave, ConfigNothing, ConfigInteger, ConfigYesNo, ConfigSelection, ConfigClock, ConfigText
from enigma import eTimer, eActionMap
try:
	from Tools import Notifications
except Exception:
	Notifications = None

# Utils
import os
import re

def _normalize_emc_title(title, filename_stem=None):
#	"""
#	Normalize EMC recording titles for cache-keying (series = 1 artwork).
#	Examples:
#	  "Babylon Berlin S01E04" -> "Babylon Berlin"
#	  "Babylon Berlin - S02E06 - Episode 6" -> "Babylon Berlin"
#	  "Wir waren wie Brüder_Bastogne" -> "Wir waren wie Brüder"
#	If normalization collapses to something useless like "Episode 6", we fallback to filename_stem.
#	"""
	if not title:
		title = ""
	t = title.strip()
	# unify whitespace
	t = re.sub(r'\s+', ' ', t)

	# Convert underscores to separators (common for episode subtitles)
	t = t.replace("_", " - ")

	# Remove leading recording prefixes like "20251217 1010 - Sky Replay HD - "
	t = re.sub(r'^\d{8}\s+\d{3,4}\s*-\s*[^-]+?\s*-\s*', '', t)

	# Remove season/episode patterns (S01E03, s1e3, 1x03)
	t = re.sub(r'(?i)\bS\s*\d{1,2}\s*E\s*\d{1,3}\b', '', t)
	t = re.sub(r'(?i)\b\d{1,2}\s*x\s*\d{1,3}\b', '', t)

	# Remove verbose labels
	t = re.sub(r'(?i)\bStaffel\s*\d{1,2}\b', '', t)
	t = re.sub(r'(?i)\bFolge\s*\d{1,3}\b', '', t)
	t = re.sub(r'(?i)\bEpisode\s*\d{1,3}\b', '', t)

	# Remove dangling separators like " -  - "
	t = re.sub(r'\s*-\s*-\s*', ' - ', t)

	# If title has multiple parts separated by " - ", prefer the most "series-like" part:
	# For bilingual titles like "Band Of Brothers - Wir waren wie Brüder" we prefer the German part.
	parts = [p.strip() for p in t.split(" - ") if p.strip()]
	if len(parts) >= 2:
		# Prefer part that contains non-ascii (umlauts) or looks like a real title (not just a number/short token)
		def score(p):
			s = 0
			if any(ord(ch) > 127 for ch in p):
				s += 3
			if len(p) >= 6:
				s += 1
			if re.search(r'(?i)\b(episode|folge)\b', p):
				s -= 3
			if re.fullmatch(r'\d+', p):
				s -= 3
			return s
		best = max(parts, key=score)
		# But if the best is still generic, keep first
		if score(best) > score(parts[0]):
			t = best
		else:
			t = parts[0]

	# Clean brackets that became empty
	t = re.sub(r'\(\s*\)', '', t).strip()

	# Final cleanup of separators/whitespace
	t = re.sub(r'[-:|]\s*$', '', t).strip()
	t = re.sub(r'\s{2,}', ' ', t).strip()

	# If we collapsed to something useless like "Episode 6", use filename stem to recover series name
	if re.fullmatch(r'(?i)(episode|folge)\s*\d{1,3}', t) or len(t) < 3:
		if filename_stem:
			f = filename_stem
			f = re.sub(r'\.[a-z0-9]{2,4}$', '', f, flags=re.I)
			f = f.replace("_", " - ")
			f = re.sub(r'^\d{8}\s+\d{3,4}\s*-\s*[^-]+?\s*-\s*', '', f)
			f = re.sub(r'(?i)\bS\s*\d{1,2}\s*E\s*\d{1,3}\b', '', f)
			f = re.sub(r'(?i)\b\d{1,2}\s*x\s*\d{1,3}\b', '', f)
			f = re.sub(r'(?i)\bStaffel\s*\d{1,2}\b', '', f)
			f = re.sub(r'(?i)\bFolge\s*\d{1,3}\b', '', f)
			f = re.sub(r'(?i)\bEpisode\s*\d{1,3}\b', '', f)
			f = re.sub(r'\s*-\s*-\s*', ' - ', f)
			fparts = [p.strip() for p in f.split(" - ") if p.strip()]
			if fparts:
				# Take first meaningful chunk
				t = fparts[0]
			f = re.sub(r'\(\s*\)', '', f).strip()
			t = re.sub(r'\s{2,}', ' ', t).strip()

	return t

def _t(de_text, en_text):
	"""Return German text if GUI language is German, otherwise English.

	We check multiple signals because some images report language differently:
	- config.osd.language.value
	- Components.Language.language.getLanguage()
	- environment (LANG/LC_ALL)
	"""
	cands = []
	try:
		cands.append(getattr(getattr(getattr(config, 'osd', None), 'language', None), 'value', None))
	except Exception:
		pass
	try:
		cands.append(language.getLanguage())
	except Exception:
		pass
	try:
		cands.append(os.environ.get('LANG'))
		cands.append(os.environ.get('LC_ALL'))
	except Exception:
		pass

	def _is_de(v):
		if not v:
			return False
		v = str(v).strip().lower()
		return v.startswith('de') or 'deutsch' in v or 'german' in v

	for v in cands:
		if _is_de(v):
			return de_text
	return en_text

# ===== API KEY FUNCTIONS (INLINE) =====
def _skin_dir():
	try:
		skin = config.skin.primary_skin.value.replace("/skin.xml", "")
		return "/usr/share/enigma2/%s" % skin
	except Exception:
		return "/usr/share/enigma2/GradientFHD"


def _read_key_file(*names):
	"""Read first non-empty key from /usr/share/enigma2/<skin>/<name>."""
	sdir = _skin_dir()
	for n in (names or []):
		try:
			fp = os.path.join(sdir, n)
			if os.path.isfile(fp):
				with open(fp, "r") as f:
					v = (f.read() or "").strip()
				if v:
					return v
		except Exception:
			pass
	return ""


def _cfg_value(*path):
	"""Safe getter for config.* chain (returns stripped string)."""
	try:
		obj = config
		for part in path:
			obj = getattr(obj, part)
		v = getattr(obj, "value", None)
		if v is None:
			v = str(obj)
		v = (v or "").strip()
		return v
	except Exception:
		return ""


def get_tmdb_key():
	"""TMDb v3 key. Priority: plugin API screen -> (old) scanner field -> skin files -> renderer default."""
	k = _cfg_value("plugins", "GradientFHD", "tmdb_api") or _cfg_value("plugins", "GradientFHD", "scanner", "tmdb_key")
	if k:
		return k
	k = _read_key_file("tmdbkey", "apikey")
	if k:
		return k
	# Legacy/fallback key bundled in the renderers
	try:
		from Components.Renderer.GradientPosterXDownloadThread import get_tmdb_api_key as _get
		k = (_get() or '').strip()
		if k:
			return k
	except Exception:
		pass
	try:
		from Components.Renderer import GradientPosterXDownloadThread as _r
		k = (getattr(_r, 'tmdb_api', '') or '').strip()
		if k:
			return k
	except Exception:
		pass
	return ""


def get_tvdb_key():
	"""TheTVDB key (v4 UUID or legacy XML).

	Priority: plugin config -> scanner config -> skin file -> renderer default.
	"""
	k = _cfg_value("plugins", "GradientFHD", "thetvdb_v4_api") or _cfg_value("plugins", "GradientFHD", "scanner", "tvdb_key")
	if k:
		return k
	k = _read_key_file("thetvdbkey")
	if k:
		return k
	# Renderer defaults (legacy key bundled in GradientPosterXDownloadThread)
	try:
		from Components.Renderer import GradientPosterXDownloadThread as _r
		k = (getattr(_r, 'thetvdbkey', '') or getattr(_r, 'TVDB_LEGACY_DEFAULT_KEY', '') or '').strip()
		if k:
			return k
	except Exception:
		pass
	return ""


def get_tvdb_pin():
	"""Optional TVDB v4 PIN (if enabled in TVDB account)."""
	p = _cfg_value("plugins", "GradientFHD", "thetvdb_pin")
	return p or _read_key_file("thetvdbpin")


def get_tvdb_legacy_key():
	"""Legacy TVDB key (XML API)."""
	k = _cfg_value("plugins", "GradientFHD", "thetvdb_legacy_api")
	if k:
		return k
	k = _read_key_file("thetvdbkey_legacy", "thetvdbkey")
	if k:
		return k
	try:
		from Components.Renderer import GradientPosterXDownloadThread as _r
		k = (getattr(_r, 'TVDB_LEGACY_DEFAULT_KEY', '') or getattr(_r, 'thetvdbkey', '') or '').strip()
		if k:
			return k
	except Exception:
		pass
	return ""


_TVDB_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_TVDB_HEX32_RE = re.compile(r"^[0-9a-fA-F]{32}$")


def _is_tvdb_uuid_key(api_key):
	try:
		return True if _TVDB_UUID_RE.match((api_key or '').strip()) else False
	except Exception:
		return False


def _is_tvdb_hex32_key(api_key):
	try:
		return True if _TVDB_HEX32_RE.match((api_key or '').strip()) else False
	except Exception:
		return False


def _tvdb_legacy_get_series_id(query, lang='de'):
	if not requests:
		return None
	q = (query or '').strip()
	if not q:
		return None
	try:
		try:
			qenc = requests.utils.quote(q.encode('utf-8'))
		except Exception:
			qenc = quote(q)
		url = "https://thetvdb.com/api/GetSeries.php?seriesname=%s" % qenc
		if lang:
			url += "&language=%s" % lang
		r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
		if r.status_code != 200 or not (r.text or '').strip():
			return None
		root = _ET.fromstring(r.text.encode('utf-8') if isinstance(r.text, str) else r.text)
		for series in root.findall('.//Series'):
			sid = None
			for tag in ('seriesid', 'id'):
				el = series.find(tag)
				if el is not None and (el.text or '').strip():
					sid = (el.text or '').strip()
					break
			if sid:
				return sid
	except Exception:
		return None
	return None


def _tvdb_legacy_get_banners_xml(api_key, series_id):
	if not requests or not api_key or not series_id:
		return None
	try:
		url = "https://thetvdb.com/api/%s/series/%s/banners.xml" % (api_key.strip(), str(series_id).strip())
		r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
		if r.status_code != 200 or not (r.text or '').strip():
			return None
		return r.text
	except Exception:
		return None


def _tvdb_legacy_pick_banner(banners_xml, want='poster', prefer_langs=('de','en','')):
	if not banners_xml:
		return None
	try:
		root = _ET.fromstring(banners_xml.encode('utf-8') if isinstance(banners_xml, str) else banners_xml)
		candidates = []
		for b in root.findall('.//Banner'):
			btype = ((b.findtext('BannerType') or '')).strip().lower()
			btype2 = ((b.findtext('BannerType2') or '')).strip().lower()
			lang = ((b.findtext('Language') or '')).strip().lower()
			path = (b.findtext('BannerPath') or '').strip()
			if not path:
				continue
			if want == 'poster':
				if btype != 'poster' and btype2 != 'poster':
					continue
			elif want in ('fanart', 'backdrop'):
				if btype not in ('fanart', 'background', 'backdrop') and btype2 not in ('fanart', 'background', 'backdrop'):
					continue
			else:  # banner
				if btype not in ('series', 'banner') and btype2 not in ('series', 'banner', 'graphical', 'wide', 'serieswide'):
					continue
			candidates.append((lang, path))
		if not candidates:
			return None
		for pl in prefer_langs:
			pl = (pl or '').lower()
			for lang, path in candidates:
				if (lang or '') == pl:
					return path
		return candidates[0][1]
	except Exception:
		return None


def _tvdb_legacy_banner_url(banner_path):
        """
        TVDb legacy can return v4-style paths like:
          /banners/v4/series/<id>/banners/<file>.jpg
        Those must be fetched from https://thetvdb.com (no extra /banners/ prefix).
        """
        if not banner_path:
                return None
        bp = (banner_path or '').strip()
        if not bp:
                return None
        if bp.startswith("http://") or bp.startswith("https://"):
                return bp
        if bp.startswith("/banners/"):
                return "https://thetvdb.com%s" % bp
        p = bp.lstrip("/")
        return "https://artworks.thetvdb.com/banners/%s" % p

def _tvdb_legacy_fetch_url(url, timeout=12):
        """
        Simple fetch helper for TVDb legacy endpoints (GetSeries.php, banners.xml).
        Uses requests if available. Returns bytes or None.
        """
        try:
                import requests as _rq
        except Exception:
                _rq = None
        if not url:
                return None
        try:
                if _rq:
                        r = _rq.get(url, timeout=timeout, headers={"User-Agent": "GradientFHD/1.0"})
                        if r.status_code != 200:
                                return None
                        return r.content
        except Exception:
                return None
        return None


def _tvdb_legacy_get_series_xml(seriesname, language=None, api_key=None):
        # Fetch GetSeries.php XML (used for <banner> fallback).
        # IMPORTANT: use urllib.parse.quote locally (do not depend on module-level quote defined later).
        try:
                from urllib.parse import quote as _q
        except Exception:
                def _q(x): return x

        q = (seriesname or '').strip()
        if not q:
                return None
        lang = (language or '').strip() if language else ''

        url = "https://thetvdb.com/api/GetSeries.php?seriesname=%s" % _q(q)
        if lang:
                url += "&language=%s" % _q(lang)
        if api_key:
                url += "&apikey=%s" % _q(api_key)

        return _tvdb_legacy_fetch_url(url)

def _tvdb_legacy_fetch_xml(query, api_key, prefer_langs=('de','en','')):
        if not api_key or not _is_tvdb_hex32_key(api_key):
                return (None, None, None)
        langs = []
        for l in (prefer_langs or []):
                if l is None:
                        continue
                l = (l or '').strip()
                if l not in langs:
                        langs.append(l)
        if '' not in langs:
                langs.append('')

        sid = None
        getseries_xml = None
        for lng in langs:
                try:
                        getseries_xml = _tvdb_legacy_get_series_xml(query, lng or None, api_key=api_key)
                except Exception:
                        getseries_xml = None
                sid = _tvdb_legacy_get_series_id(query, lng or None)
                if sid:
                        break
        if not sid:
                return (None, None, getseries_xml)
        xml = _tvdb_legacy_get_banners_xml(api_key, sid)
        if not xml:
                return (sid, None, getseries_xml)
        return (sid, xml, getseries_xml)


def get_omdb_key():
	"""Return first OMDb key (may be comma separated in config). Includes renderer default fallback."""
	keys = _get_omdb_keys()
	k = (keys[0] if keys else "").strip()
	if k:
		return k
	try:
		from Components.Renderer import GradientPosterXDownloadThread as _r
		k = (getattr(_r, 'omdb_api', '') or '').strip()
		if k:
			return k
	except Exception:
		pass
	return ""


def get_fanart_key():
	"""Fanart.tv key. Priority: plugin config -> (old) scanner field -> skin file -> renderer default."""
	k = _cfg_value("plugins", "GradientFHD", "fanart_api") or _cfg_value("plugins", "GradientFHD", "scanner", "fanart_key")
	if k:
		return k
	k = _read_key_file("fanartkey")
	if k:
		return k
	try:
		from Components.Renderer import GradientPosterXDownloadThread as _r
		k = (getattr(_r, 'fanart_api', '') or '').strip()
		if k:
			return k
	except Exception:
		pass
	return ""


# Ensure quote() exists even if requests import failed
try:
	quote
except Exception:
	def quote(s):
		return s
try:
	from PIL import Image
except Exception:
	class _ImgDummy(object):
		def verify(self): pass

	class Image:
		@staticmethod
		def open(path): return _ImgDummy()

# List-Widget aus xtra
from .GradientSelectionList import GradientSelectionList as xtraSelectionList, GradientSelectionEntryComponent as xtraSelectionEntryComponent

# Safe wrapper: avoids OpenATV crash on GUI-delete when the same MenuList is bound
# under multiple widget names (e.g. 'paths' + 'config') or when a widget is not
# instantiated due to a temporary skin mismatch.
class SafeSelectionList(xtraSelectionList):
	def preWidgetRemove(self, instance):
		# OpenATV MenuList.preWidgetRemove() can crash if self.l is None.
		try:
			l = getattr(self, 'l', None)
			if l is not None:
				try:
					l.setContent(None)
				except Exception:
					pass
		except Exception:
			pass


# API Keys
# API keys inline - see below


# Sichere Übersetzung: Stelle sicher, dass '_' aufrufbar ist
try:
	__t = _
	if not callable(__t):
		raise Exception("underscore-not-callable")
except Exception:
	def _(s): return s


# Pfade/Konstanten
VIDEO_EXTS = (".ts", ".mkv", ".avi", ".mp4", ".m4v", ".mpg", ".mpeg", ".mov", ".wmv", ".flv", ".stream", ".iso")
DEFAULT_HDD_MOVIE = "/media/hdd/movie"

# EMC-Cache (für Aufnahmen)


def get_emc_cache_base():
	"""Get EMC cache base path from GradientFHD storage setting."""
	try:
		base = config.plugins.GradientFHD.posterXPath.value
		if base and base != "AUTO":
			if os.path.isdir(base):
				return os.path.join(base, "xtra", "EMC")
	except Exception:
		pass

	for candidate in ["/media/hdd", "/media/usb", "/media/mmc", "/media/net", "/media/autofs"]:
		try:
			if os.path.isdir(candidate) and os.access(candidate, os.W_OK):
				return os.path.join(candidate, "xtra", "EMC")
		except Exception:
			pass

	return os.path.join("/media/hdd", "xtra", "EMC")


EMC_BASE = get_emc_cache_base()
EMC_POSTER = os.path.join(EMC_BASE, "poster")
EMC_BACKDROP = os.path.join(EMC_BASE, "backdrop")
EMC_BANNER = os.path.join(EMC_BASE, "banner")
EMC_INFOS = os.path.join(EMC_BASE, "infos")

# Create directories if they don't exist
for _dir in [EMC_BASE, EMC_POSTER, EMC_BACKDROP, EMC_BANNER, EMC_INFOS]:
	if not os.path.isdir(_dir):
		try:
			os.makedirs(_dir, 0o755)
		except:
			pass

PATHS_LOG = "/tmp/GradientFHD_paths.log"


def _append_paths_log(source, rows=None):
	"""Write active scan/cache paths for easier support diagnostics."""
	try:
		lines = ["[%s] %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), source)]
		for r in (rows or []):
			lines.append("  - %s" % r)
		with open(PATHS_LOG, "a+", encoding="utf-8") as lf:
			lf.write("\n".join(lines) + "\n")
	except Exception:
		pass


def _normalize_legacy_info_json_names():
	"""Rename legacy '*.ts.json' / '*.cut.json' style info files to clean '<title>.json'."""
	renamed = 0
	removed_dupes = 0
	try:
		if not os.path.isdir(EMC_INFOS):
			return renamed, removed_dupes
		for fn in os.listdir(EMC_INFOS):
			if not fn.lower().endswith('.json'):
				continue
			stem = os.path.splitext(fn)[0]
			clean = make_safe_cache_name(stem)
			if not clean or clean == stem:
				continue
			src = os.path.join(EMC_INFOS, fn)
			dst = os.path.join(EMC_INFOS, clean + '.json')
			try:
				if os.path.abspath(src) == os.path.abspath(dst):
					continue
			except Exception:
				pass
			try:
				if os.path.exists(dst):
					# Ziel existiert bereits -> Altdatei entfernen
					os.remove(src)
					removed_dupes += 1
				else:
					os.rename(src, dst)
					renamed += 1
			except Exception:
				pass
	except Exception:
		pass
	return renamed, removed_dupes


_renamed_infos, _removed_info_dupes = (0, 0)

_append_paths_log("MovieScanner init", [
	"EMC_BASE=%s" % EMC_BASE,
	"EMC_POSTER=%s" % EMC_POSTER,
	"EMC_BACKDROP=%s" % EMC_BACKDROP,
	"EMC_BANNER=%s" % EMC_BANNER,
	"EMC_INFOS=%s" % EMC_INFOS,
	"renamed_info_json=%d" % _renamed_infos,
	"removed_info_json_dupes=%d" % _removed_info_dupes,
])

# TV-Cache (für EPG)


def get_tv_cache_base():
	try:
		loc = config.plugins.GradientFHD.scanner.loc.value or "/media/hdd/"
	except Exception:
		loc = "/media/hdd/"
	return os.path.join(loc, "GradientFHD")


CLEANUP_REPORT = "/tmp/GradientFHD_cleanup_report.txt"
SCHED_LOG = "/tmp/GradientFHD_cleanup_schedule.log"
MOVIESCAN_SCHED_LOG = "/tmp/GradientFHD_moviescanner_schedule.log"
# REPORT_PATH wird dynamisch in EMC_BASE erstellt
def get_report_path():
	return os.path.join(get_emc_cache_base(), "scanner_report_%s.txt" % datetime.now().strftime("%Y%m%d_%H%M%S"))
REPORT_PATH = get_report_path()

EXCLUDE_DIR_NAMES = {"trash", ".trash", "scan", ".scan", "trashcan", ".trashcan"}

# Scanner-Optionen
OPT_ONLY_MISSING = True
OPT_NEED_POSTER = True
OPT_NEED_BACKDROP = True
OPT_NEED_BANNER = True


# Hilfsfunktionen
def ensure_dirs():
	for p in (EMC_POSTER, EMC_BACKDROP, EMC_BANNER, EMC_INFOS):
		try:
			if not os.path.isdir(p):
				os.makedirs(p)
		except Exception:
			pass
	tv_base = get_tv_cache_base()
	for sub in ("poster", "backdrop", "banner", "infos"):
		try:
			p = os.path.join(tv_base, sub)
			if not os.path.isdir(p):
				os.makedirs(p)
		except Exception:
			pass


def listdir_filtered(path):
	try:
		return sorted(os.listdir(path))
	except Exception:
		return []


def is_excluded_dir(path):
	name = os.path.basename(os.path.normpath(path)).lower()
	return name in EXCLUDE_DIR_NAMES


def count_videos_recursive(path):
	total = 0
	for root, dirs, files in os.walk(path):
		dirs[:] = [d for d in dirs if not is_excluded_dir(os.path.join(root, d))]
		for f in files:
			if f.lower().endswith(VIDEO_EXTS):
				total += 1
	return total


def count_videos_root_only(path):
	total = 0
	try:
		for f in os.listdir(path):
			fp = os.path.join(path, f)
			if os.path.isfile(fp) and f.lower().endswith(VIDEO_EXTS):
				total += 1
	except Exception:
		pass
	return total


NETWORK_SCAN_ROOTS = ("/media/autofs", "/media/net")
LOCAL_MOVIE_ROOTS = (DEFAULT_HDD_MOVIE, "/media/usb/movie", "/media/mmc/movie")


def _norm_real_path(path):
	try:
		return os.path.abspath(os.path.realpath(path))
	except Exception:
		try:
			return os.path.abspath(path)
		except Exception:
			return path


def _append_unique_dir(paths, seen, candidate):
	try:
		if (not candidate) or (not os.path.isdir(candidate)) or is_excluded_dir(candidate):
			return
		np = _norm_real_path(candidate)
		if np in seen:
			return
		seen.add(np)
		paths.append(candidate)
	except Exception:
		pass


def _is_flat_movie_root(path):
	np = _norm_real_path(path)
	for r in LOCAL_MOVIE_ROOTS:
		if np == _norm_real_path(r):
			return True
	return False


def _configured_video_dirs():
	"""Try Enigma2 recording/movie config paths as additional scan start points."""
	out = []
	candidates = []
	try:
		vd = getattr(getattr(config, 'movielist', None), 'videodirs', None)
		if vd is not None:
			val = getattr(vd, 'value', None)
			if isinstance(val, (list, tuple)):
				candidates.extend([x for x in val if isinstance(x, str)])
	except Exception:
		pass
	try:
		last_videodir = getattr(getattr(config, 'movielist', None), 'last_videodir', None)
		if last_videodir is not None:
			val = getattr(last_videodir, 'value', None)
			if isinstance(val, str) and val:
				candidates.append(val)
	except Exception:
		pass
	for p in candidates:
		try:
			if isinstance(p, str) and p and os.path.isdir(p):
				out.append(p)
		except Exception:
			pass
	return out


def _add_children(paths, seen, base):
	"""Add first-level child folders of base (no recursion here)."""
	for name in listdir_filtered(base):
		p = os.path.join(base, name)
		if os.path.isdir(p) and (not is_excluded_dir(p)):
			_append_unique_dir(paths, seen, p)


def scan_start_points():
	"""
	Build selectable scan roots.

	Legacy behavior is kept (/media/hdd/movie + subdirs), but we additionally
	support NAS/autofs structures like:
	  /media/autofs/DISKSTATION/Filme
	and configured movielist video dirs.
	"""
	roots = []
	seen = set()

	# 1) Known local movie roots (legacy + common alternatives)
	for base in LOCAL_MOVIE_ROOTS:
		if os.path.isdir(base):
			_append_unique_dir(roots, seen, base)
			_add_children(roots, seen, base)

	# 2) Explicitly configured movie/recording dirs from Enigma2 config
	for p in _configured_video_dirs():
		_append_unique_dir(roots, seen, p)
		# If this is a movie root, expose its direct subfolders as selectable items
		if _is_flat_movie_root(p):
			_add_children(roots, seen, p)

	# 3) Network automount roots (/media/autofs, /media/net)
	#    Add host/share level and one level below, so users can select either
	#    the complete share or a dedicated movie folder (e.g. .../Filme).
	for net_root in NETWORK_SCAN_ROOTS:
		if not os.path.isdir(net_root):
			continue
		for host_or_share in listdir_filtered(net_root):
			host_path = os.path.join(net_root, host_or_share)
			if not os.path.isdir(host_path) or is_excluded_dir(host_path):
				continue
			_append_unique_dir(roots, seen, host_path)
			_add_children(roots, seen, host_path)

	return roots


def nice_folder_label(path):
	is_root_movie = _is_flat_movie_root(path)
	base = os.path.basename(os.path.normpath(path)) or path
	if is_root_movie:
		cnt = count_videos_root_only(path)
		label = "%s (Aufnahmen) (%d)" % (base, cnt)
	else:
		cnt = count_videos_recursive(path)
		label = "%s (%d)" % (base, cnt)
	return (label, cnt)


def read_e2_meta_title(fp):
	base, ext = os.path.splitext(fp)
	candidates = [base + ".meta"]
	if ext.lower() == ".ts":
		candidates.append(fp + ".meta")
	for mp in candidates:
		try:
			if os.path.exists(mp):
				with open(mp, 'r') as f:
					lines = [l.strip() for l in f.readlines()]
				if not lines:
					continue
				if ':' in lines[0] and lines[0].count(':') >= 2:
					if len(lines) > 1 and lines[1]:
						return lines[1]
				if lines[0]:
					return lines[0]
		except Exception:
			pass
	return None


def normalize_umlauts(s):
	repl = {"ä": "ae", "Ä": "Ae", "ö": "oe", "Ö": "Oe", "ü": "ue", "Ü": "Ue", "ß": "ss"}
	for k, v in repl.items():
		s = s.replace(k, v)
	return s


def split_camel_case(s):
	return re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', s)


# Suffixe/Sidecars, die manchmal fälschlich im Titel landen (z.B. nach Schnitt)
KNOWN_TITLE_SUFFIXES = (
	".ts", ".mkv", ".avi", ".mp4", ".m4v", ".mpg", ".mpeg", ".mov", ".wmv", ".flv", ".stream", ".iso",
	".cut", ".cuts", ".meta", ".eit", ".ap", ".sc", ".del", ".tmp"
)


def _fix_mojibake_text(s):
	"""Heuristisch typische UTF-8/Latin1-Mojibake reparieren (z.B. "zurÃ¼ck" -> "zurück")."""
	if not s:
		return s
	try:
		t = str(s)
	except Exception:
		return s
	try:
		bad_before = t.count("Ã") + t.count("Â")
		if bad_before <= 0:
			return t
		for enc in ("latin-1", "cp1252"):
			try:
				cand = t.encode(enc, "ignore").decode("utf-8", "ignore")
			except Exception:
				continue
			if not cand:
				continue
			bad_after = cand.count("Ã") + cand.count("Â")
			if bad_after < bad_before:
				t = cand
				break
	except Exception:
		pass
	return t


def _strip_known_title_suffixes(s):
	"""Entfernt am Ende angehängte Dateisuffixe mehrfach (z.B. '.ts', '.cut', '.meta')."""
	if not s:
		return s
	try:
		t = str(s).strip()
	except Exception:
		return s
	# mehrfach entfernen, falls z.B. '.ts.meta' im Titel landet
	for _ in range(4):
		low = t.lower().rstrip()
		changed = False
		for ext in KNOWN_TITLE_SUFFIXES:
			if low.endswith(ext):
				t = t[:len(t) - len(ext)].rstrip(" ._-")
				changed = True
				break
		if not changed:
			break
	return t


def _extract_trailing_year(s):
	"""Extrahiert ein Jahr, wenn es am Ende steht, und liefert (title_without_year, year_or_None)."""
	if not s:
		return s, None
	try:
		t = str(s).strip()
	except Exception:
		return s, None

	# ... (2024) / ... [2024]
	m = re.match(r'^(.*?)\s*[\(\[]((?:19|20)\d{2})[\)\]]\s*$', t)
	if m:
		return (m.group(1).strip() or t), m.group(2)

	# ... 2024 / ...-2024
	m = re.match(r'^(.*?)\s*[-_. ]\s*((?:19|20)\d{2})\s*$', t)
	if m:
		try:
			y = int(m.group(2))
			if 1900 <= y <= datetime.now().year + 1:
				return (m.group(1).strip() or t), m.group(2)
		except Exception:
			pass
	return t, None


def make_safe_cache_name(title, fallback_stem=None):
	"""Einheitlicher Safe-Name für Cache-Dateien (ohne versehentliches '.ts')."""
	t = title or ""
	if t:
		t = _fix_mojibake_text(t)
		t = t.replace("\xc2\x86", "").replace("\xc2\x87", "")
		t = t.replace("Â\x86", "").replace("Â\x87", "")
		t = re.sub(r'\s+', ' ', t.replace('_', ' ')).strip()
		t = _strip_known_title_suffixes(t)
		t = re.sub(r'[\\/:"*?<>|]+', '', t).strip()
		t = _strip_known_title_suffixes(t)
		t = re.sub(r'\s+', ' ', t).strip(' .')
	if (not t) and fallback_stem:
		f = os.path.splitext(os.path.basename(fallback_stem))[0]
		f = _strip_known_title_suffixes(_fix_mojibake_text(f or ""))
		f = re.sub(r'[\\/:"*?<>|]+', '', f).strip()
		t = f or ""
	return t


# Late init: now helper functions are available
try:
	_renamed_infos, _removed_info_dupes = _normalize_legacy_info_json_names()
	if _renamed_infos or _removed_info_dupes:
		_append_paths_log("MovieScanner legacy-info-normalize", [
			"renamed_info_json=%d" % _renamed_infos,
			"removed_info_json_dupes=%d" % _removed_info_dupes,
		])
except Exception:
	pass


PREFIX_RX = re.compile(
	r'^\s*(\d{4,8}\s+\d{3,4}\s*[-–]\s*)?'
	r'([A-Za-z0-9_+ÄÖÜäöüß\. ]{2,}?\s+(HD|FHD|SD)\s*(DE)?(\s*\[ \+ \])?\s*[-–]\s*)?',
	re.I
)


def clean_title_from_filename(name, fullpath=None):
	"""
	Liefert (title, year) aus Dateiname/Meta.
	Entfernt Kanal-/Zeit-Vorspänne und gängige Tags.
	"""
	year = None

	# 1) E2 .meta bevorzugen
	if fullpath:
		try:
			mt = read_e2_meta_title(fullpath)
		except Exception:
			mt = None
		if mt:
			t = _fix_mojibake_text(mt)
			t = re.sub(r"\s+", " ", str(t).replace("_", " ")).strip()
			t = re.sub(r'\[[^\]]*\]', ' ', t)
			t = _strip_known_title_suffixes(t)
			t = re.sub(r'\s+', ' ', t).strip()
			t, y2 = _extract_trailing_year(t)
			if y2:
				year = y2
			if t:
				return t, year

	base = os.path.splitext(name)[0]
	base = _fix_mojibake_text(base)
	base = _strip_known_title_suffixes(base)
	base = base.replace("_", " ").replace(".", " ")
	base = re.sub(r'^\s*(\d{3,4}(?:\s+\d{3,4}){0,2}\s*)', ' ', base)  # "0306 0217"
	base = re.sub(r'^\s*(?:(?:sky|spiegel|history|nat\s*geo|disney|kinowelt|cinema|premiere|premieren|sat\s*1|rtl|zdf|orf|ard|vox|pro\s*7|sci|syfy|hd|fhd|uhd|de|vip)(?:[^\w]+|\b))+', ' ', base, flags=re.I)
	base = re.sub(r'\[[^\]]*\]', ' ', base)
	try:
		base = normalize_umlauts(base)
	except Exception:
		pass
	base = re.sub(r'\s+', ' ', base).strip()

	# Jahr am Ende erkennen: "Titel (2024)" oder "Titel 2024"
	base, y2 = _extract_trailing_year(base)
	if y2:
		year = y2

	if not year:
		m_last_year = re.search(r'(.+?)\s*\(((?:19|20)\d{2})\)\s*$', base)
		if m_last_year:
			base = m_last_year.group(1).strip()
			year = m_last_year.group(2)

	STOP = ('sky', 'cinema', 'premiere', 'premieren', 'fhd', 'hd', 'de', 'vip', 'kinowelt', 'tv', 'spiegel', 'history', 'nat', 'geo', 'disney', 'rtl', 'sat', 'pro', 'vox', 'arte', 'zdf', 'orf', 'srf', 'one', 'syfy')
	low = base.lower()
	if any(w in low for w in STOP):
		for sep in (':', ' - '):
			if sep in base:
				tail = base.split(sep)[-1].strip()
				if len(tail.split()) >= 2:
					base = tail
					break

	base = _strip_known_title_suffixes(base)
	base = re.sub(r'\s+', ' ', base).strip()

	if year:
		try:
			y = int(year)
			if y < 1900 or y > datetime.now().year + 1:
				year = None
		except Exception:
			year = None

	if not base:
		base = os.path.splitext(name)[0]
	base = _strip_known_title_suffixes(_fix_mojibake_text(base))
	base = re.sub(r'\s+', ' ', base).strip()
	return base, year


def _extract_recording_channel(path_or_name):
	"""Best-effort channel extraction from recording filenames like
	'20251226 1322 - Sky Cinema Action HD - Rambo.ts'.
	Returns the channel part or ''.
	"""
	try:
		base = os.path.splitext(os.path.basename(path_or_name or ''))[0]
		base = _fix_mojibake_text(base)
		parts = [p.strip() for p in re.split(r'\s*[-–]\s*', base) if p and p.strip()]
		if len(parts) >= 3:
			if re.match(r'^\d{6,8}\s+\d{3,4}$', parts[0]) or re.match(r'^\d{6,8}$', parts[0]):
				return parts[1]
	except Exception:
		pass
	return ''


def _is_movie_channel_hint(channel_name):
	"""Channels with a strong movie bias should not force recordings into TV mode."""
	try:
		ch = re.sub(r'\s+', ' ', (channel_name or '').strip().lower())
	except Exception:
		ch = ''
	if not ch:
		return False
	for hint in (
		'sky cinema', 'cinema', 'kinowelt', 'warner tv film', 'tnt film',
		'mgm', 'silverline', 'axn movies', 'movie channel'
	):
		if hint in ch:
			return True
	return False


def detect_media_type(path_or_name, title_hint=None, fullpath=None):
	"""Classify recording as movie or tv.

	Important fix:
	Recordings from clear movie channels like 'Sky Cinema ...' must stay movie,
	even if the raw filename uses a typical recording schema with many ' - '.
	"""
	try:
		raw = ' '.join([x for x in (path_or_name, fullpath, title_hint) if x]).lower()
	except Exception:
		raw = (path_or_name or '').lower()
	title_s = ((title_hint or '') if isinstance(title_hint, str) else str(title_hint or '')).lower()
	import re as _re

	if any(k in raw for k in ('doku', 'dokumentation', 'dokumentar', 'documentary')):
		return "tv"
	if any(k in raw for k in ('staffel', 'season', 'serie', 'episode', 'folge')):
		return "tv"
	if _re.search(r'\bS\d{1,2}E\d{1,3}\b', raw) or _re.search(r'\bE\d{1,3}\b', raw):
		return "tv"
	# Episoden-/Teil-Nummern in Aufnahmenamen ("1. ...", "Teil 2")
	if _re.search(r'\b(teil|part)\s*\d+\b', raw) or _re.search(r'\b\d+\.\s+[^\d/]', raw):
		return "tv"

	# Strong movie-channel override for recordings like:
	# 20251226 1322 - Sky Cinema Action HD - Rambo.ts
	channel_hint = _extract_recording_channel(fullpath or path_or_name)
	if _is_movie_channel_hint(channel_hint):
		return "movie"

	# Aufnahme-Schema: Datum - Sender - Serie - Episode
	if raw.count(' - ') >= 3 or raw.replace('_', ' - ').count(' - ') >= 3:
		return "tv"

	# If title itself clearly looks episodic, keep TV.
	if title_s and (' - ' in title_s or ' – ' in title_s):
		if any(k in title_s for k in ('staffel', 'season', 'serie', 'episode', 'folge')):
			return "tv"

	return "movie"


def bytes_to_mb(b):
	try:
		return b / 1048576.0
	except Exception:
		return 0.0


# Sprache/Einstellungen
def lang_param():
	try:
		if config.plugins.GradientFHD.scanner.searchLang.value:
			from Components.Language import language
			lang = language.getLanguage()[:2]
			return lang or "de"
	except Exception:
		pass
	return "de"


def cfg_search_type():
	try:
		return config.plugins.GradientFHD.scanner.searchType.value or "multi"
	except Exception:
		return "multi"


# Persistente Cleanup-Konfiguration
if not hasattr(config.plugins, 'GradientFHD'):
	config.plugins.GradientFHD = ConfigSubsection()
if not hasattr(config.plugins.GradientFHD, 'scanner'):
	config.plugins.GradientFHD.scanner = ConfigSubsection()
if not hasattr(config.plugins.GradientFHD.scanner, 'cleanup'):
	config.plugins.GradientFHD.scanner.cleanup = ConfigSubsection()
C = config.plugins.GradientFHD.scanner.cleanup
AS = config.plugins.GradientFHD.scanner

# Migrate legacy MovieScanner auto-scan settings from cleanup.* to scanner.*
_legacy_auto_scan_enabled = None
_legacy_auto_scan_time = None
try:
	if hasattr(C, 'auto_scan_enabled'):
		_legacy_auto_scan_enabled = bool(AS.auto_scan_enabled.value)
except Exception:
	_legacy_auto_scan_enabled = None
try:
	if hasattr(C, 'auto_scan_time'):
		_legacy_auto_scan_time = C.auto_scan_time.value
except Exception:
	_legacy_auto_scan_time = None

# Persist selected scan paths (EMC/movie)
if not hasattr(config.plugins.GradientFHD.scanner, 'movie_paths'):
	config.plugins.GradientFHD.scanner.movie_paths = ConfigText(default="", fixed_size=False)

# Storage mode for EMC artwork (MovieScanner)
# NOTE: Recording-folder storage has been removed on purpose to avoid unnecessary I/O/traffic.
# The EMC cache (/media/.../xtra/EMC/) is the only supported target.
if not hasattr(config.plugins.GradientFHD.scanner, 'emc_storage_mode'):
	config.plugins.GradientFHD.scanner.emc_storage_mode = ConfigSelection(default="emc", choices=[
		("emc", _t("EMC Cache (/xtra/EMC)", "EMC cache (/xtra/EMC)")),
	])
# Safety: if an old config still contains "recording", force back to "emc"
try:
	if config.plugins.GradientFHD.scanner.emc_storage_mode.value != "emc":
		config.plugins.GradientFHD.scanner.emc_storage_mode.value = "emc"
		config.plugins.GradientFHD.scanner.emc_storage_mode.save()
		configfile.save()
except Exception:
	pass

# Legacy: if you keep cache mode, optionally copy poster next to the recording as cover.jpg
if not hasattr(config.plugins.GradientFHD.scanner, 'copyPosterToRecording'):
	config.plugins.GradientFHD.scanner.copyPosterToRecording = ConfigYesNo(default=False)



def _ensure_sel(attr, default='never'):
	if not hasattr(C, attr):
		setattr(C, attr, ConfigSelection(default=default, choices=[
			('never', _('Niemals löschen')),
			('7', '7'), ('14', '14'), ('30', '30'), ('90', '90'), ('365', '365')
		]))
	return getattr(C, attr)


def _ensure_yesno(attr, default=False):
	if not hasattr(C, attr):
		setattr(C, attr, ConfigYesNo(default=default))
	return getattr(C, attr)


def _ensure_int(attr, default, limits=(0, 999999)):
	if not hasattr(C, attr):
		setattr(C, attr, ConfigInteger(default=default, limits=limits))
	return getattr(C, attr)


def _ensure_clock(attr, default_sec):
	if not hasattr(C, attr):
		setattr(C, attr, ConfigClock(default=default_sec))
	return getattr(C, attr)


# Bereiche aktivieren (TV/EMC x Poster/Backdrop/Banner/Infos)
C.include_tv_poster = _ensure_yesno('include_tv_poster', True)
C.include_tv_backdrop = _ensure_yesno('include_tv_backdrop', True)
C.include_tv_banner = _ensure_yesno('include_tv_banner', True)
C.include_tv_infos = _ensure_yesno('include_tv_infos', False)

C.include_emc_poster = _ensure_yesno('include_emc_poster', True)
C.include_emc_backdrop = _ensure_yesno('include_emc_backdrop', True)
C.include_emc_banner = _ensure_yesno('include_emc_banner', True)
C.include_emc_infos = _ensure_yesno('include_emc_infos', True)

# Retention je Bereich (Tage)
for seg in ('tv', 'emc'):
	for area in ('poster', 'backdrop', 'banner', 'infos'):
		_ensure_sel('ret_%s_%s' % (seg, area), 'never')

# Mindestalter (Stunden)
C.min_age_hours = _ensure_int('min_age_hours', 24, limits=(0, 2400))

# Keep-N pro Bereich (nur Poster/Backdrop/Banner)
C.keep_min_enable = _ensure_yesno('keep_min_enable', True)
C.keep_min_poster = _ensure_int('keep_min_poster', 50, limits=(0, 10000))
C.keep_min_backdrop = _ensure_int('keep_min_backdrop', 50, limits=(0, 10000))
C.keep_min_banner = _ensure_int('keep_min_banner', 50, limits=(0, 10000))

# Größenlimit pro Segment (nur Preset in GB)
C.size_tv_gb_preset = ConfigSelection(default='10', choices=[
	('0', _('Aus (kein Limit)')),
	('1', '1 GB'), ('2', '2 GB'), ('3', '3 GB'),
	('5', '5 GB'), ('10', '10 GB'), ('20', '20 GB'), ('50', '50 GB')
])
C.size_emc_gb_preset = ConfigSelection(default='0', choices=[
	('0', _('Aus (kein Limit)')),
	('1', '1 GB'), ('2', '2 GB'), ('3', '3 GB'),
	('5', '5 GB'), ('10', '10 GB'), ('20', '20 GB'), ('50', '50 GB')
])

# Auto-Bereinigung
C.auto_enabled = _ensure_yesno('auto_enabled', False)
C.auto_time = _ensure_clock('auto_time', 3 * 3600 + 30 * 60)  # 03:30

# MovieScanner Auto-Scan (sauber getrennt unter scanner.*)
if not hasattr(AS, 'auto_scan_enabled'):
	AS.auto_scan_enabled = ConfigYesNo(default=bool(_legacy_auto_scan_enabled) if _legacy_auto_scan_enabled is not None else False)
if not hasattr(AS, 'auto_scan_time'):
	AS.auto_scan_time = ConfigClock(default=_legacy_auto_scan_time if _legacy_auto_scan_time is not None else (4 * 3600 + 30 * 60))


def _limit_bytes(gb_preset):
	try:
		pres_gb = int(str(getattr(gb_preset, 'value', gb_preset)))
	except Exception:
		pres_gb = 0
	return pres_gb * 1024 * 1024 * 1024


def build_title_candidates(title, mtype=None):
	import re as _re
	t = (title or '').strip()
	t = _strip_known_title_suffixes(_fix_mojibake_text(t))
	cands = []
	if not t:
		return cands
	cands.append(t)
	t2 = _re.sub(r'(Episode|Folge)\s*\d+', ' ', t, flags=_re.I)
	t2 = _re.sub(r'S\d{1,2}E\d{1,3}', ' ', t2, flags=_re.I)
	t2 = _re.sub(r'E\d{1,3}', ' ', t2, flags=_re.I)
	t2 = _re.sub(r'\([^\)]*\)$', ' ', t2).strip(' -:– ')
	if t2 and t2 not in cands:
		cands.append(t2)
	# Variante ohne angehängtes Jahr ("Titel 2024" -> "Titel")
	t3, _y3 = _extract_trailing_year(t2)
	if t3 and t3 not in cands:
		cands.append(t3)
	parts = _re.split(r'\s*[\-:–]\s*', t2)
	if len(parts) >= 2:
		first = parts[0].strip(); last = parts[-1].strip(); mid = ' '.join(parts[:-1]).strip()
		if mtype == 'tv':
			order = (first, mid, last)
		else:
			order = (last, mid, first)
		for v in order:
			if v and v not in cands:
				cands.append(v)
	# Episoden-Nummern/Teile entfernen (z.B. "Sitting Bull 1. ...")
	m = _re.match(r'^(.*?)[\s\-:]*\d+\.(?:\s|$)', t2)
	if m:
		base_num = (m.group(1) or '').strip()
		if base_num and base_num not in cands:
			cands.append(base_num)
	m = _re.match(r'^(.*?)[\s\-:]*(teil|part|folge|episode)\s*\d+', t2, flags=_re.I)
	if m:
		base_num = (m.group(1) or '').strip()
		if base_num and base_num not in cands:
			cands.append(base_num)
	tokens = t2.split()
	if mtype == 'tv' and len(tokens) >= 3:
		for k in (1, 2, 3, 4):
			if len(tokens) >= k:
				cand = ' '.join(tokens[:k]).strip()
				if cand and cand not in cands:
					cands.append(cand)

	def de_diacritics_variants(s):
		maps = [('ae', 'ä'), ('oe', 'ö'), ('ue', 'ü'), ('Ae', 'Ä'), ('Oe', 'Ö'), ('Ue', 'Ü')]
		outs = set()
		for (a, b) in maps:
			if a in s:
				outs.add(s.replace(a, b))
		return list(outs)
	for v in list(cands):
		for vv in de_diacritics_variants(v):
			if vv not in cands:
				cands.append(vv)
	cands = [_re.sub(r'\s+', ' ', x).strip() for x in cands]
	cands = [x for x in cands if len(x) >= 2]
	seen = set(); out = []
	for x in sorted(cands, key=lambda s: -len(s)):
		if x not in seen:
			seen.add(x); out.append(x)
	return out

# ===== MovieScannerMain (GRÜN = Suchlauf) =====



def _ms_notify(text, timeout=6, mtype=None):
	try:
		if Notifications is None:
			return
		if mtype is None:
			mtype = MessageBox.TYPE_INFO
		if hasattr(Notifications, 'AddPopup'):
			Notifications.AddPopup(text, mtype, int(timeout))
		else:
			Notifications.AddNotification(MessageBox, text, type=mtype, timeout=int(timeout))
	except Exception:
		pass


class MovieScannerStatusOSD(Screen):
	skin = """
        <screen name="MovieScannerStatusOSD" position="10,10" size="1160,90" backgroundColor="#80000000" cornerRadius="20" flags="wfNoBorder" zPosition="999">
			<widget name="current" position="20,4" size="1120,32" font="Gradient_Font; 27" foregroundColor="green" backgroundColor="background" transparent="1" valign="center" borderWidth="1" borderColor="black" />
			<widget name="progress" position="20,40" size="1120,10" foregroundColor="yellow" borderColor="yellow" borderWidth="2" backgroundColor="black" />
			<widget name="status" position="20,54" size="1120,32" font="Gradient_Font; 27" foregroundColor="white" backgroundColor="background" transparent="1" borderWidth="1" borderColor="black" />
		</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["progress"] = ProgressBar()
		self["progress"].setRange((0, 100))
		self["progress"].setValue(0)
		self["status"] = Label("")
		self["current"] = Label("")

	def updateState(self, current_text, status_text, percent):
		try:
			self["current"].setText(current_text or "")
		except Exception:
			pass
		try:
			self["status"].setText(status_text or "")
		except Exception:
			pass
		try:
			p = int(percent or 0)
			if p < 0:
				p = 0
			elif p > 100:
				p = 100
			self["progress"].setValue(p)
		except Exception:
			pass


class MovieScannerEngine(object):
	def __init__(self, owner_screen):
		self.owner_screen = owner_screen
		self.session = owner_screen.session
		self.stop_flag = False
		self.stats = {"total": 0, "done": 0, "ok": 0, "skipped": 0, "err": 0, "poster": 0, "backdrop": 0, "banner": 0}
		self._hint_base = getattr(owner_screen, "_hint_base", "") or ""
		self._has_current_widget = bool(getattr(owner_screen, "_has_current_widget", False))
		self.current_line = ""
		for _name in (
			"_worker", "_download_image", "_try_tmdb", "_try_tvdb", "_try_tvdb_legacy",
			"_try_omdb_poster", "_try_fanart_banner", "_copyPosterToRecording",
			"_try_tvdb_banner", "_try_tvdb_legacy_banner"
		):
			setattr(self, _name, types.MethodType(getattr(MovieScannerMain, _name), self))

	def status_line(self):
		return "Gesamt: %(total)d  Fertig: %(done)d  Poster: %(poster)d  Backdrop: %(backdrop)d  Banner: %(banner)d  Skip: %(skipped)d  Err: %(err)d" % self.stats

	def percent(self):
		total = int(self.stats.get("total", 0) or 0)
		if total <= 0:
			return 0
		done = int(self.stats.get("done", 0) or 0)
		return int(done * 100.0 / max(total, 1))

	def _visible_screen(self):
		return getattr(MOVIESCAN_WATCHER, "screen", None)

	def _apply_to_visible_screen(self):
		scr = self._visible_screen()
		if scr is None:
			return
		try:
			scr["progress"].setValue(self.percent())
		except Exception:
			pass
		try:
			scr["status"].setText(self.status_line())
		except Exception:
			pass
		try:
			scr["current"].setText(self.current_line or "")
		except Exception:
			pass
		try:
			if not getattr(scr, "_has_current_widget", False):
				if self.current_line and self._hint_base:
					scr["hint"].setText(self.current_line + ("\n\n" + self._hint_base))
				elif self.current_line:
					scr["hint"].setText(self.current_line)
				else:
					scr["hint"].setText(self._hint_base)
		except Exception:
			pass

	def _ui_set_current(self, text, idx):
		total = max(int(self.stats.get("total", 0) or 0), 0)
		prefix = _t("Aktuell", "Current")
		counter = (" (%d/%d)" % (idx, total)) if total else (" (%d)" % idx)
		self.current_line = "%s: %s%s" % (prefix, text, counter)
		MOVIESCAN_WATCHER.update_views()

	def _ui_progress(self):
		MOVIESCAN_WATCHER.update_views()

	def _apply_finish_to_visible_screen(self):
		scr = self._visible_screen()
		if scr is None:
			return
		if self.stop_flag:
			msg = _t("Abgebrochen.", "Aborted.")
		else:
			msg = _t("Fertig. Report: %s", "Done. Report: %s") % REPORT_PATH
		try:
			scr["info"].setText(msg)
		except Exception:
			pass
		try:
			scr["status"].setText(self.status_line())
		except Exception:
			pass
		try:
			scr["hint"].setText(msg + ("\n\n" + self._hint_base if self._hint_base else ""))
		except Exception:
			pass
		try:
			scr["current"].setText("")
		except Exception:
			pass
		try:
			scr["progress"].setValue(self.percent())
		except Exception:
			pass

	def _ui_finish(self):
		MOVIESCAN_WATCHER.finish(stopped=bool(self.stop_flag))


class MovieScannerRunController(object):
	EXIT_DEBOUNCE = 0.35
	RED_DEBOUNCE = 0.25

	def __init__(self):
		self.running = False
		self.session = None
		self.screen = None
		self.engine = None
		self.scan_thread = None
		self.osd = None
		self.osd_visible = False
		self._hooked = False
		self._last_exit_ts = 0.0
		self._last_red_ts = 0.0
		self._stop_box_open = False
		self.scheduled_run = False

	def _action_allowed(self):
		try:
			dlg = getattr(self.session, "current_dialog", None)
		except Exception:
			dlg = None
		if dlg is None:
			return False
		try:
			nm = dlg.__class__.__name__ or ""
		except Exception:
			nm = ""
		return nm.startswith("InfoBar") or nm == "InfoBar"

	def _is_exit_action(self, args):
		for a in args:
			if isinstance(a, str) and a in ("cancel", "exit", "hide"):
				return True
		for a in args:
			if isinstance(a, int) and a in (0xAE, 174):
				return True
		return False

	def _is_red_action(self, args):
		for a in args:
			if isinstance(a, str) and a == "red":
				return True
		return False

	def _on_global_action(self, *args, **kwargs):
		if not self.running or self.session is None:
			return 0
		if not self._action_allowed():
			return 0
		now = time.time()
		if self._is_red_action(args):
			if self._last_red_ts and (now - self._last_red_ts) < self.RED_DEBOUNCE:
				return 0
			self._last_red_ts = now
			if self.osd_visible and self.screen is None:
					# In hidden LiveTV mode, RED should do nothing.
					return 0
			return 0
		if self._is_exit_action(args):
			if self._last_exit_ts and (now - self._last_exit_ts) < self.EXIT_DEBOUNCE:
				return 0
			self._last_exit_ts = now
			if self.screen is None and self.osd_visible:
					# In LiveTV with OSD visible, EXIT should stop the scan and close everything.
					self.stop_and_close_all()
			return 0
		return 0

	def _hook_global_actions(self):
		if self._hooked:
			return
		for ctx in ("OkCancelActions", "InfobarShowHideActions", "ColorActions"):
			try:
				eActionMap.getInstance().bindAction(ctx, -0x7FFFFFFF, self._on_global_action)
				self._hooked = True
			except Exception:
				pass

	def attach_screen(self, screen):
		try:
			self.session = screen.session
		except Exception:
			pass
		self.screen = screen
		if self.running and self.engine is not None:
			try:
				screen.scan_thread = self.scan_thread
			except Exception:
				pass
			self._close_osd()
			self.engine._apply_to_visible_screen()

	def start(self, screen, files):
		self.session = screen.session
		self.screen = screen
		self.engine = MovieScannerEngine(screen)
		self.engine.stats["total"] = len(files)
		self.running = True
		self.scheduled_run = False
		self._hook_global_actions()
		self._close_osd()
		self.scan_thread = threading.Thread(target=self.engine._worker, args=(files,))
		self.scan_thread.daemon = True
		self.scan_thread.start()
		try:
			screen.scan_thread = self.scan_thread
		except Exception:
			pass

	def start_background(self, session, files, show_osd=True, scheduled=False):
		if self.running:
			return False
		class _BgOwner(object):
			pass
		owner = _BgOwner()
		owner.session = session
		owner._hint_base = ""
		owner._has_current_widget = False
		self.session = session
		self.screen = None
		self.engine = MovieScannerEngine(owner)
		self.engine.stats["total"] = len(files)
		self.running = True
		self.scheduled_run = bool(scheduled)
		self._hook_global_actions()
		self._close_osd()
		if show_osd:
			self._ensure_osd()
		self.scan_thread = threading.Thread(target=self.engine._worker, args=(files,))
		self.scan_thread.daemon = True
		self.scan_thread.start()
		return True

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
		self.osd_visible = False

	def _ensure_osd(self):
		if not self.running or self.session is None or self.engine is None:
			return
		if self.osd is None:
			try:
				self.osd = self.session.instantiateDialog(MovieScannerStatusOSD)
			except Exception:
				self.osd = None
		if self.osd is not None:
			try:
				self.osd.show()
			except Exception:
				pass
			self.osd_visible = True
			self._refresh_osd()

	def _refresh_osd(self):
		if self.osd is None or self.engine is None:
			return
		try:
			self.osd.updateState(self.engine.current_line, self.engine.status_line(), self.engine.percent())
		except Exception:
			pass

	def show_osd_parallel(self):
		if not self.running or self.engine is None:
			return
		self._ensure_osd()

	def close_osd_only(self):
		self._close_osd()

	def stop_and_close_all(self):
		if not self.running:
			return
		self.request_stop()
		self._close_osd()
		self.screen = None
		self._close_to_livetv()

	def _close_to_livetv(self):
		"""Close dialogs until we are back on InfoBar/LiveTV (robust async).

		Certain dialog chains (ExtensionsMenu -> Plugin) don't pop synchronously in a tight loop.
		We therefore close ONE dialog per timer tick until InfoBar becomes current_dialog.
		"""
		if self.session is None:
			return
		try:
			from enigma import eTimer
		except Exception:
			eTimer = None

		# Fallback: best-effort sync loop
		if eTimer is None:
			for _i in range(96):
				try:
					dlg = getattr(self.session, "current_dialog", None)
				except Exception:
					dlg = None
				if dlg is None:
					break
				try:
					nm = dlg.__class__.__name__ or ""
				except Exception:
					nm = ""
				if ("InfoBar" in nm) or nm == "InfoBar":
					break
				try:
					dlg.close()
				except Exception:
					try:
						self.session.close(dlg)
					except Exception:
						break
			return

		# Async: close step-by-step
		try:
			if getattr(self, "_livetv_close_timer", None) is None:
				self._livetv_close_timer = eTimer()
				try:
					self._livetv_close_timer.callback.append(self._close_to_livetv_step)
				except Exception:
					self._livetv_close_timer_conn = self._livetv_close_timer.timeout.connect(self._close_to_livetv_step)
		except Exception:
			return

		self._livetv_close_steps_left = 96
		try:
			self._livetv_close_timer.start(10, True)
		except Exception:
			pass

	def _close_to_livetv_step(self):
		try:
			steps = int(getattr(self, "_livetv_close_steps_left", 0))
		except Exception:
			steps = 0
		if steps <= 0:
			return
		self._livetv_close_steps_left = steps - 1

		try:
			dlg = getattr(self.session, "current_dialog", None)
		except Exception:
			dlg = None
		if dlg is None:
			return
		try:
			nm = dlg.__class__.__name__ or ""
		except Exception:
			nm = ""
		if ("InfoBar" in nm) or nm == "InfoBar":
			return

		try:
			dlg.close()
		except Exception:
			try:
				self.session.close(dlg)
			except Exception:
				return

		try:
			self._livetv_close_timer.start(10, True)
		except Exception:
			pass

	def hide_to_livetv(self):
		if not self.running or self.engine is None:
			return
		# Close the MovieScanner dialog itself first, then unwind dialog stack to InfoBar.
		try:
			if self.screen is not None:
				self.screen.close()
		except Exception:
			pass
		self.screen = None
		self._ensure_osd()
		self._close_to_livetv()

	def hide_to_osd(self):
		if not self.running or self.engine is None:
			return
		self.screen = None
		self._ensure_osd()

	def reopen_main(self):
		if not self.running or self.session is None:
			return
		if self.screen is not None:
			return
		self._close_osd()
		try:
			self.session.open(MovieScannerMain)
		except Exception:
			pass

	def update_views(self):
		if not self.running or self.engine is None:
			return
		# Update BOTH: Main window (if open) and OSD (if visible)
		if self.screen is not None:
			try:
				self.engine._apply_to_visible_screen()
			except Exception:
				pass
		if self.osd_visible:
			self._refresh_osd()

	def request_stop(self):
		if self.engine is not None:
			self.engine.stop_flag = True
		self.update_views()

	def ask_stop(self):
		if self._stop_box_open or self.session is None:
			return
		self._stop_box_open = True

		def _cb(ans):
			self._stop_box_open = False
			if ans:
				self.request_stop()

		def _open():
			try:
				self.session.openWithCallback(
					_cb,
					MessageBox,
					_t("MovieScanner wirklich stoppen?", "Really stop MovieScanner?"),
					type=MessageBox.TYPE_YESNO,
					default=False
				)
			except Exception:
				self._stop_box_open = False

		try:
			t = eTimer()
			t.callback.append(_open)
			t.start(50, True)
			self._stop_prompt_timer = t
		except Exception:
			_open()

	def _write_schedule_result(self, stopped=False):
		if not getattr(self, "scheduled_run", False):
			return
		try:
			ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			state = 'aborted' if stopped else 'finished'
			result = ''
			if self.engine is not None:
				result = self.engine.status_line()
			with open(MOVIESCAN_SCHED_LOG, 'a') as f:
				f.write('[%s] scheduled moviescan %s: %s\n' % (ts, state, result))
		except Exception:
			pass

	def finish(self, stopped=False):
		if not self.running:
			return
		self.running = False
		self._close_osd()
		try:
			if self.engine is not None:
				self.engine._apply_finish_to_visible_screen()
		except Exception:
			pass
		self._write_schedule_result(stopped=bool(stopped))
		txt = ("Suchlauf abgebrochen  |  " if stopped else "Suchlauf beendet  |  ")
		if self.engine is not None:
			txt += self.engine.status_line()
		_ms_notify(txt, timeout=6)
		try:
			if self.screen is not None:
				self.screen["key_red"].setText(_t("Schließen", "Close"))
		except Exception:
			pass
		self.screen = None
		self.scan_thread = None
		self.engine = None
		self.scheduled_run = False

MOVIESCAN_WATCHER = MovieScannerRunController()


class MovieScannerMain(Screen):
	skin = """
    <screen name="GradientFHD_MovieScannerMain" position="center,center" size="1160,860" title="GradientDB - Movie Scanner" backgroundColor="transparent" flags="wfNoBorder">
        <widget source="Title" render="Label" position="20,0" size="1060,60" font="Italic; 42" halign="left" valign="center" transparent="1" foregroundColor="gradient_foreground_selection" backgroundColor="background" textBorderColor="black" textBorderWidth="1" zPosition="1" />
        <widget name="config" position="30,80" size="1100,360" itemHeight="45" font="Gradient_Font;30" foregroundColor="white" backgroundColor="background" scrollbarMode="showOnDemand" zPosition="3" transparent="1" />
        <widget name="hint" position="30,480" size="1100,140" font="Gradient_Font;30" foregroundColor="gradient_foreground_selection" backgroundColor="background" transparent="1" />
        <widget name="progress" position="30,715" size="1100,20" foregroundColor="yellow" borderColor="yellow" borderWidth="2" backgroundColor="black" />
        <widget name="status" position="30,750" size="1100,40" font="Gradient_Font; 30" foregroundColor="ButtonYellow" backgroundColor="gradient_background" transparent="1" />
        <widget name="current" position="30,630" size="1100,70" font="Gradient_Font;30" foregroundColor="green" backgroundColor="gradient_background" transparent="1" valign="bottom" />
        <eLabel name="menu_bg" position="0,60" size="1160,800" backgroundColor="gradient_BGO,gradient_BGM,gradient_BGU,vertical" zPosition="-8" />
        <eLabel name="title_bg" position="0,0" size="1160,70" backgroundColor="gradient_TBGL,gradient_BGO,gradient_BGU,horizontal" zPosition="-9" cornerRadius="12" />
        <eLabel name="title_line" position="0,60" size="1160,4" backgroundColor="gradient_background,gradient_BGLR,gradient_BGLM,horizontal" zPosition="10" />
        <eLabel name="Line_Menu" position="15,795" size="1130,2" backgroundColor="gradient_BGLR,gradient_BGLM,gradient_BGLR,horizontal" zPosition="10" />
        <eLabel name="Line_config" position="30,460" size="1100,2" backgroundColor="gradient_BGLR,gradient_BGLM,gradient_BGLR,horizontal" zPosition="10" />
        <ePixmap pixmap="buttons/key_red.png" position="20,815" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_green.png" position="300,815" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_yellow.png" position="580,815" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_blue.png" position="860,815" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <widget name="key_red" position="60,810" size="220,40" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" valign="center" halign="left" transparent="1" />
        <widget name="key_green" position="340,810" size="220,40" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" valign="center" halign="left" transparent="1" />
        <widget name="key_yellow" position="620,810" size="220,40" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" valign="center" halign="left" transparent="1" />
        <widget name="key_blue" position="900,810" size="220,40" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" valign="center" halign="left" transparent="1" />
    </screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.setTitle("GradientDB - Movie Scanner")

		self["paths"] = SafeSelectionList([])

		# Skin-Kompatibilität: manche Skins nutzen widget name="config" statt "paths".
		# Wir binden beide Namen auf die gleiche SelectionList, damit die Ordnerauswahl immer sichtbar ist.
		try:
			self["config"]
		except Exception:
			self["config"] = self["paths"]
		self["status"] = Label("")
		self["info"] = Label("")
		self["hint"] = Label("")
		# Shows the currently processed title during scan (skin can place this widget freely)
		self["current"] = Label("")
		self._has_current_widget = False
		self["key_red"] = Label(_("Schließen"))
		self["key_green"] = Label(_("Suchlauf"))
		self["key_yellow"] = Label(_("Info"))
		self["key_blue"] = Label(_t("Einstellungen", "Settings"))
		self["progress"] = ProgressBar()
		self["progress"].setRange((0, 100))
		self["progress"].setValue(0)

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "InfobarActions"], {
			"cancel": self.keyExitScreen,
			"red": self.keyRedOsd,
			"green": self.startScan,
			"yellow": self.showInfoMain,
			"blue": self.openAdvancedCleanup,
			"ok": self["paths"].toggleSelection,
			"left": self._noop, "right": self._noop, "up": self.moveUp, "down": self.moveDown,
			"info": self.showInfoMain
		}, -1)

		try:
			self["paths"].l.setItemHeight(70)
		except Exception:
			pass

		self.scan_thread = None
		self.stop_flag = False
		self.stats = {"total": 0, "done": 0, "ok": 0, "skipped": 0, "err": 0, "poster": 0, "backdrop": 0, "banner": 0}
		# Run-Counter (nur dieser Suchlauf)
		self.stats["poster"] = 0
		self.stats["backdrop"] = 0
		self.stats["banner"] = 0

		self._path_by_row_index = {}

		self._hint_base = ""
		ensure_dirs()
		self.onLayoutFinish.append(self.populatePaths)
		self.onLayoutFinish.append(self._detect_current_widget)
		try:
			MOVIESCAN_WATCHER.attach_screen(self)
		except Exception:
			pass

	def _noop(self): pass

	def moveUp(self):
		try: self["paths"].instance.moveSelection(self["paths"].instance.moveUp)
		except Exception: pass

	def moveDown(self):
		try: self["paths"].instance.moveSelection(self["paths"].instance.moveDown)
		except Exception: pass

	def populatePaths(self):
		items = []
		self._path_by_row_index = {}
		idx = 0
		saved = []
		try:
			raw = (config.plugins.GradientFHD.scanner.movie_paths.value or '').strip()
			if raw:
				if raw.startswith('['):
					saved = json.loads(raw)
				else:
					saved = [x.strip() for x in raw.split(',') if x.strip()]
		except Exception:
			saved = []
		saved_norm = set([_norm_real_path(p) for p in saved if isinstance(p, str) and p])
		discovered = scan_start_points()
		seen_disp = set([_norm_real_path(p) for p in discovered])
		# Keep previously saved valid paths visible, even if they are currently
		# not returned by auto-discovery.
		for sp in saved:
			try:
				if isinstance(sp, str) and sp and os.path.isdir(sp):
					nsp = _norm_real_path(sp)
					if nsp not in seen_disp:
						discovered.append(sp)
						seen_disp.add(nsp)
			except Exception:
				pass
		for p in discovered:
			label, _cnt = nice_folder_label(p)
			prechecked = 1 if os.path.isdir(p) else 0
			if saved_norm:
				prechecked = 1 if _norm_real_path(p) in saved_norm else 0
			items.append(xtraSelectionEntryComponent("%s" % label, 1, 0, prechecked))
			self._path_by_row_index[idx] = p
			idx += 1
		self["paths"].setList(items)
		# Base hint shown below (and reused during scan updates)
		self._hint_base = _t(
			"Ordner wählen (OK = an/aus).  Grün startet den Suchlauf.\n"
			"ROT blendet aus. Danach ist Live TV sichtbar, OSD läuft weiter.",
			"Select folders (OK = toggle).  Green starts scanning.\n"
			"RED hides the window. Live TV becomes visible and the OSD keeps running."
		)
		try:
			self["hint"].setText(self._hint_base)
		except Exception:
			pass
		try:
			self["current"].setText("")
		except Exception:
			pass
		self["status"].setText(_t("Blau: MovieScan-Verwaltung öffnen  •  Grün: Suchlauf starten", "Blue: Open MovieScan-management  •  Green: Start scan"))


	def _detect_current_widget(self):
		"""Detect whether the current-title widget exists in the active skin.
		If not, we will fall back to updating the hint text, so older skins still work."""
		try:
			# After skin application, widgets that exist will have an 'instance'
			self._has_current_widget = bool(getattr(self["current"], "instance", None))
		except Exception:
			self._has_current_widget = False

	def _gather_selected_paths(self):
		sel_paths = []
		seen = set()
		try:
			for idx, item in enumerate(self["paths"].list):
				row = self["paths"].list[idx][0]
				checked = row[3]
				real_path = self._path_by_row_index.get(idx)
				if checked and real_path and os.path.isdir(real_path):
					np = _norm_real_path(real_path)
					if np in seen:
						continue
					seen.add(np)
					sel_paths.append(real_path)
		except Exception:
			pass
		return sel_paths

	def openAdvancedCleanup(self):
		self.session.open(MovieScannerCleanupAdvanced)

	def showInfoMain(self):
		sel = []
		try:
			sel = self._gather_selected_paths()
		except Exception:
			sel = []
		text = build_info_text_emc()
		self.session.open(MessageBox, text, MessageBox.TYPE_INFO)

	def keyRedOsd(self):
		try:
			if MOVIESCAN_WATCHER.running:
				MOVIESCAN_WATCHER.hide_to_livetv()
				return
		except Exception:
			pass
		self.close()

	def keyExitScreen(self):
		try:
			if MOVIESCAN_WATCHER.running:
				MOVIESCAN_WATCHER.stop_and_close_all()
				return
		except Exception:
			pass
		self.close()

	# ===== Suchlauf =====
	def startScan(self):
		if MOVIESCAN_WATCHER.running:
			MOVIESCAN_WATCHER.request_stop()
			self["status"].setText(_("Abbruch angefordert..."))
			return
		if self.scan_thread and self.scan_thread.is_alive():
			self.stop_flag = True
			self["status"].setText(_("Abbruch angefordert..."))
			return

		sel_paths = self._gather_selected_paths
		sel = []
		try:
			sel = self._gather_selected_paths()
		except Exception:
			sel = []
		if not sel:
			self.session.open(MessageBox, _("Bitte mindestens einen Ordner auswählen."), MessageBox.TYPE_INFO, timeout=5)
			return

		# Save selection for next run + write helper file
		try:
			config.plugins.GradientFHD.scanner.movie_paths.value = json.dumps(sel, ensure_ascii=False)
			configfile.save()
		except Exception:
			pass
		try:
			os.makedirs(EMC_BASE, exist_ok=True)
			pfile = os.path.join(EMC_BASE, 'scanner_paths.txt')
			with open(pfile, 'w', encoding='utf-8') as pf:
				pf.write('GradientFHD MovieScanner Paths\n')
				pf.write('Saved on: %s\n\n' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
				pf.write('Selected paths:\n')
				for sp in sel:
					pf.write('  - %s\n' % sp)
				pf.write('\nAvailable paths:\n')
				for ap in scan_start_points():
					pf.write('  - %s\n' % ap)
		except Exception:
			pass
		try:
			_append_paths_log("MovieScanner startScan", [
				"selected=%s" % ", ".join(sel),
				"available=%s" % ", ".join(scan_start_points()),
			])
		except Exception:
			pass

		self.stop_flag = False
		self.stats = {"total": 0, "done": 0, "ok": 0, "skipped": 0, "err": 0, "poster": 0, "backdrop": 0, "banner": 0}
		self["progress"].setValue(0)
		self["info"].setText("")
		self["status"].setText("Gesamt: %(total)d  Fertig: %(done)d  Poster: %(poster)d  Backdrop: %(backdrop)d  Banner: %(banner)d  Skip: %(skipped)d  Err: %(err)d" % self.stats)
		try:
			run_hint = _t(
				"Suche läuft...\n\nROT blendet aus. Danach ist Live TV sichtbar, OSD läuft weiter.",
				"Scan running...\n\nRED hides the window. Live TV becomes visible and the OSD keeps running."
			)
			self["hint"].setText(run_hint)
		except Exception:
			pass

		files = []
		for base in sel:
			if _is_flat_movie_root(base):
				try:
					for f in os.listdir(base):
						fp = os.path.join(base, f)
						if os.path.isfile(fp) and f.lower().endswith(VIDEO_EXTS):
							files.append(fp)
				except Exception:
					pass
			else:
				for root, dirs, fls in os.walk(base):
					dirs[:] = [d for d in dirs if not is_excluded_dir(os.path.join(root, d))]
					for f in fls:
						if f.lower().endswith(VIDEO_EXTS):
							files.append(os.path.join(root, f))

		self.stats["total"] = len(files)
		if not files:
				self.session.open(MessageBox, _("Keine passenden Dateien gefunden."), MessageBox.TYPE_INFO, timeout=5)
				return

		MOVIESCAN_WATCHER.start(self, files)
		# MOVIESCAN_WATCHER.show_osd_parallel()  # OSD now starts on RED (hide)
		try:
			self["key_red"].setText(_t("Ausblenden", "Hide"))
		except Exception:
			pass
		self["status"].setText(_t("Suchlauf läuft  •  ROT blendet aus  •  EXIT beendet alles", "Scan running  •  RED hides  •  EXIT stops everything"))

	def _worker(self, files):
		tmdb_key = get_tmdb_key()
		# tvdb_key: prefer v4 UUID if available, fall back to legacy 32-hex.
		# Both keys are passed into _try_tvdb_banner / _try_tvdb_legacy_banner
		# which handle the delegation automatically.
		tvdb_key = get_tvdb_key() or get_tvdb_legacy_key()
		fanart_key = get_fanart_key()
		lang = lang_param()
		rep_lines = []
		ok_details = []
		skip_details = []
		# provider counters
		poster_by, backdrop_by, banner_by = {}, {}, {}
		prov_lines = []
		import time as _time

		for idx, fp in enumerate(files, start=1):
			if self.stop_flag:
				break
			try:
				title_guess, year = clean_title_from_filename(os.path.basename(fp), fullpath=fp)
				mtype = detect_media_type(fp + " " + os.path.dirname(fp), title_hint=title_guess, fullpath=fp)
				title_key = title_guess
				title_search = title_guess
				if mtype == 'tv':
					_norm = _normalize_emc_title(title_guess, os.path.splitext(os.path.basename(fp))[0])
					if _norm:
						title_key = _norm
						title_search = _norm
				safe_name = make_safe_cache_name(title_key, fallback_stem=os.path.splitext(os.path.basename(fp))[0])
				if not safe_name:
					safe_name = "item_%d" % idx

				# UI Fortschritt
				self._ui_set_current(_("Verarbeite: %s") % title_guess, idx)

				# Artwork target paths (EMC cache only)
				# (Recording-folder storage removed to avoid unnecessary I/O/traffic)
				storage_mode = "emc"
				poster_path = os.path.join(EMC_POSTER, "%s.jpg" % safe_name)
				backdr_path = os.path.join(EMC_BACKDROP, "%s.jpg" % safe_name)
				banner_path = os.path.join(EMC_BANNER, "%s.jpg" % safe_name)
				need_poster = (not os.path.exists(poster_path)) if OPT_ONLY_MISSING else OPT_NEED_POSTER
				need_backdr = (not os.path.exists(backdr_path)) if OPT_ONLY_MISSING else OPT_NEED_BACKDROP
				need_banner = (not os.path.exists(banner_path)) if OPT_ONLY_MISSING else OPT_NEED_BANNER
				# provider track
				poster_provider = None
				backdrop_provider = None
				banner_provider = None
				pre_p = os.path.exists(poster_path) and os.path.getsize(poster_path) > 0
				pre_b = os.path.exists(backdr_path) and os.path.getsize(backdr_path) > 0
				pre_bn = os.path.exists(banner_path) and os.path.getsize(banner_path) > 0
				# --- NEU (früh): Falls Poster bereits im EMC-Cache vorhanden ist, gleich als Cover neben die Aufnahme kopieren ---
				if storage_mode != "recording":
					try:
						if getattr(config.plugins.GradientFHD.scanner, 'copyPosterToRecording', None) and \
								config.plugins.GradientFHD.scanner.copyPosterToRecording.value:
							if os.path.exists(poster_path) and os.path.getsize(poster_path) > 0:
								base, _ext = os.path.splitext(fp)
								dst = base + ".jpg"
								do_copy = True
								if os.path.exists(dst):
									try:
										from PIL import Image
										Image.open(dst).verify()
										do_copy = False
									except Exception:
										do_copy = True
								if do_copy:
									import shutil
									shutil.copyfile(poster_path, dst)
					except Exception:
						pass
				# --- NEU (früh) Ende ---
				ok_any = False
				candidates = build_title_candidates(title_search, mtype)
				poster_provider = None; backdrop_provider=None; banner_provider=None
				pre_p = os.path.exists(poster_path) and os.path.getsize(poster_path) > 0
				pre_b = os.path.exists(backdr_path) and os.path.getsize(backdr_path) > 0
				pre_bn = os.path.exists(banner_path) and os.path.getsize(banner_path) > 0
				for cand in (candidates or [title_search]):
					if requests and tmdb_key and (need_poster or need_backdr) and getattr(config.plugins.GradientFHD.scanner, 'tmdb', ConfigYesNo(default=True)).value:
						ok_any |= self._try_tmdb(cand, mtype, lang, year, tmdb_key, need_poster, poster_path, need_backdr, backdr_path)
						if not poster_provider and (not pre_p) and (os.path.exists(poster_path) and os.path.getsize(poster_path)>0): poster_provider='TMDB'
						if not backdrop_provider and (not pre_b) and (os.path.exists(backdr_path) and os.path.getsize(backdr_path)>0): backdrop_provider='TMDB'
					if requests and (need_poster or need_backdr) and tvdb_key and getattr(config.plugins.GradientFHD.scanner, 'tvdb', ConfigYesNo(default=False)).value:
						if not (os.path.exists(poster_path) and os.path.getsize(poster_path)>0) or not (os.path.exists(backdr_path) and os.path.getsize(backdr_path)>0):
							ok_any |= self._try_tvdb(cand, mtype, lang, tvdb_key, need_poster, poster_path, need_backdr, backdr_path)
							if not poster_provider and (not pre_p) and (os.path.exists(poster_path) and os.path.getsize(poster_path)>0): poster_provider='TVDB'
							if not backdrop_provider and (not pre_b) and (os.path.exists(backdr_path) and os.path.getsize(backdr_path)>0): backdrop_provider='TVDB'
					need_poster = not (os.path.exists(poster_path) and os.path.getsize(poster_path)>0) if OPT_ONLY_MISSING else False
					need_backdr = not (os.path.exists(backdr_path) and os.path.getsize(backdr_path)>0) if OPT_ONLY_MISSING else False
					if not need_poster and not need_backdr:
						break
				# OMDb Poster fallback
				try:
					from Components.config import config as _cfg
					use_omdb_fb = getattr(getattr(getattr(_cfg,'plugins',None),'GradientFHD',None),'omdbPoster', None)
					use_omdb_fb = bool(use_omdb_fb and getattr(use_omdb_fb,'value',False))
				except Exception:
					use_omdb_fb = False
				if use_omdb_fb and not (os.path.exists(poster_path) and os.path.getsize(poster_path)>0):
					ok_any |= self._try_omdb_poster(title_guess, year, poster_path)
					if not poster_provider and (os.path.exists(poster_path) and os.path.getsize(poster_path)>0):
						poster_provider='OMDB'
				# Banner over candidates:
				#   - TV: TVDB -> FANART
				#   - MOVIE: FANART -> (optional) TVDB(v4 only)
				if need_banner and requests:
					for bcand in (candidates or [title_guess]):
						if mtype == 'movie':
							# Fanart is usually best for movies (uses TMDb ID)
							if fanart_key and not (os.path.exists(banner_path) and os.path.getsize(banner_path)>0):
								pre = os.path.exists(banner_path)
								ok_any |= self._try_fanart_banner(bcand, mtype, fanart_key, banner_path)
								if (not pre) and (os.path.exists(banner_path) and os.path.getsize(banner_path)>0) and not banner_provider:
									banner_provider='FANART'
							# Optional: TVDb v4 banners for movies only if UUID key is used (avoid legacy series banners)
							if tvdb_key and _is_tvdb_uuid_key(tvdb_key) and not (os.path.exists(banner_path) and os.path.getsize(banner_path)>0):
								pre = os.path.exists(banner_path)
								ok_any |= self._try_tvdb_banner(bcand, mtype, lang, tvdb_key, banner_path)
								if (not pre) and (os.path.exists(banner_path) and os.path.getsize(banner_path)>0) and not banner_provider:
									banner_provider='TVDB'
						else:
							# TV/Series: TVDb first, then Fanart fallback
							if tvdb_key and not (os.path.exists(banner_path) and os.path.getsize(banner_path)>0):
								pre = os.path.exists(banner_path)
								ok_any |= self._try_tvdb_banner(bcand, mtype, lang, tvdb_key, banner_path)
								if (not pre) and (os.path.exists(banner_path) and os.path.getsize(banner_path)>0) and not banner_provider:
									banner_provider='TVDB'
							if fanart_key and not (os.path.exists(banner_path) and os.path.getsize(banner_path)>0):
								pre = os.path.exists(banner_path)
								ok_any |= self._try_fanart_banner(bcand, mtype, fanart_key, banner_path)
								if (not pre) and (os.path.exists(banner_path) and os.path.getsize(banner_path)>0) and not banner_provider:
									banner_provider='FANART'
						if os.path.exists(banner_path) and os.path.getsize(banner_path)>0:
							break
				
				# ============================================================
				# STAFFEL-POSTER + EPISODE-STILL (für Serien mit S##E## im Namen)
				# ============================================================
				if mtype == 'tv' and requests:
					try:
						# --------------------------------------------------------
						# Episode-Info aus Dateinamen (alle Formate unterstützt)
						# --------------------------------------------------------
						_fn_base  = os.path.basename(fp)
						_ep_info  = parse_episode_info(_fn_base)
						_ep_series_title = _ep_info.get('series_title') or title_search
						_ep_title_hint   = _ep_info.get('ep_title')

						# Bereinigter safe_name ohne S##E## / Episode-Suffixe
						import re as _re_ep
						_ep_safe = make_safe_cache_name(_ep_series_title, fallback_stem=os.path.splitext(_fn_base)[0])
						_ep_format       = _ep_info.get('format', 'unknown')

						# Für "Serie-EpTitel" Format: Geschwister-Dateien analysieren
						# und kollisions-freie Episode-Nummern zuweisen
						_ep_index_override = None
						if _ep_format == 'Series-EpTitle' and _ep_title_hint:
							try:
								_folder = os.path.dirname(fp)
								_tmdb_sid = tmdb_get_series_id(
									_ep_safe, lang, year, tmdb_key, requests) if tmdb_key else None
								_folder_map = resolve_episode_assignments_for_folder(
									folder=_folder,
									series_title=_ep_safe,
									series_id=_tmdb_sid,
									lang=lang,
									api_key=tmdb_key,
									requests_mod=requests,
								)
								_ep_index_override = _folder_map.get(_fn_base)
							except Exception:
								pass

						_ep_result = download_season_episode_artwork(
							safe_name=_ep_safe,
							filename=_fn_base,
							episode_title=_ep_title_hint,
							mtype=mtype,
							lang=lang,
							year=year,
							emc_poster=EMC_POSTER,
							emc_backdrop=EMC_BACKDROP,
							tmdb_key=tmdb_key,
							tvdb_key=tvdb_key,
							tvdb_legacy_key=get_tvdb_legacy_key(),
							requests_mod=requests,
							download_fn=self._download_image,
							tvdb4_get_fn=tvdb4_get,
							tvdb4_ensure_token_fn=tvdb4_ensure_token,
							get_tvdb_pin_fn=get_tvdb_pin,
							is_tvdb_uuid_fn=_is_tvdb_uuid_key,
							is_tvdb_hex32_fn=_is_tvdb_hex32_key,
							tvdb_legacy_get_series_id_fn=_tvdb_legacy_get_series_id,
							only_missing=True,
							ep_index_override=_ep_index_override,
						)
						_ep_sp = _ep_result.get('season_poster')
						_ep_es = _ep_result.get('episode_still')
						if _ep_sp or _ep_es:
							ok_any = True
						# Zähler für Season/Episode-Artwork mitführen
						if _ep_sp:
							self.stats["poster"] += 1
						if _ep_es:
							self.stats["backdrop"] += 1
					except Exception:
						pass

				# Live-Counter: maximal 1x pro Item, nur wenn neu geladen wurde
				
				if poster_provider:
				
				        self.stats["poster"] += 1
				
				if backdrop_provider:
				
				        self.stats["backdrop"] += 1
				
				if banner_provider:
				
				        self.stats["banner"] += 1

				
				# final cover
				# final cover
				if storage_mode != "recording":
					self._copyPosterToRecording(fp, poster_path)
				# -- EMC Infos (JSON) --
# -- EMC Infos (JSON) --
				try:
					if getattr(C, 'include_emc_infos', None) and getattr(C, 'include_emc_infos').value:
						try:
							os.makedirs(EMC_INFOS, exist_ok=True)
						except Exception:
							pass
						jpath = os.path.join(EMC_INFOS, "%s.json" % safe_name)
						if not os.path.exists(jpath):
							tmdb_key2 = get_tmdb_key()
							data = {"Title": title_guess, "Year": None, "imdbRating": None, "Rated": "", "Released": None, "Genre": None, "Duration": None, "Country": None, "Director": None, "Writer": None, "Actors": None, "Awards": None, "Type": "movie" if mtype=="movie" else "tv", "Plot": "", "imdbID": None}
							if requests and tmdb_key2:
								# Suche auf TMDb
								srch_type = 'tv' if mtype=='tv' else ('movie' if mtype=='movie' else cfg_search_type())
								base = "https://api.themoviedb.org/3/search/%s?api_key=%s&query=%s" % (srch_type, tmdb_key2, quote(title_guess))
								urls = [base]
								if lang: urls.insert(0, base + "&language=%s" % lang)
								if year and srch_type=='movie' and lang: urls.insert(0, base + "&language=%s&year=%s" % (lang, year))
								res=None
								for u in urls:
									try:
										rjs = requests.get(u, timeout=10).json()
										arr = rjs.get("results") or []
										if arr: res = arr[0]; break
									except Exception:
										pass
								if not res and srch_type!='multi':
									base2 = "https://api.themoviedb.org/3/search/multi?api_key=%s&query=%s" % (tmdb_key2, quote(title_guess))
									urls = [base2]
									if lang: urls.insert(0, base2 + "&language=%s" % lang)
									for u in urls:
										try:
											rjs = requests.get(u, timeout=10).json()
											arr = rjs.get("results") or []
											if arr: res = arr[0]; break
										except Exception:
											pass
								if res:
									media = res.get("media_type") or srch_type
									mid = res.get("id")
									try:
										det = requests.get("https://api.themoviedb.org/3/%s/%s?api_key=%s&language=%s" % ("tv" if media=="tv" else "movie", mid, tmdb_key2, lang or "de"), timeout=10).json()
									except Exception:
										det = {}
									if det:
										data["Title"] = det.get("name") if media=="tv" else (det.get("title") or data["Title"])
										d = det.get("first_air_date") if media=="tv" else det.get("release_date")
										if d: data["Year"] = d[:4]
										g = det.get("genres") or []
										if g: data["Genre"] = ", ".join([x.get("name") for x in g if x.get("name")])
										if media=="tv":
											rt = det.get("episode_run_time") or []
											if rt: data["Duration"] = "%s min" % rt[0]
											oc = det.get("origin_country") or []
											if oc: data["Country"] = ", ".join(oc)
											data["Type"] = "tv"
										else:
											rt = det.get("runtime")
											if rt: data["Duration"] = "%s min" % rt
											pc = det.get("production_countries") or []
											if pc: data["Country"] = ", ".join([c.get("name") for c in pc if c.get("name")])
											data["Type"] = "movie"
										if not data["Plot"]:
											data["Plot"] = det.get("overview") or ""
									# imdb id
									try:
										ext = requests.get("https://api.themoviedb.org/3/%s/%s/external_ids?api_key=%s" % ("tv" if (res.get("media_type")=="tv") else "movie", mid, tmdb_key2), timeout=10).json()
										data["imdbID"] = ext.get("imdb_id")
									except Exception:
										pass
							# Schreiben
							with open(jpath, "w", encoding="utf-8") as jf:
								import json
								jf.write(json.dumps(data, ensure_ascii=False))
				except Exception as e:
					try:
						with open("/tmp/GradientFHD_scanner.log","a+") as _f:
							_f.write("emc infos error, %s, %s\n" % (title_guess, e))
					except Exception:
						pass
				# final copy to recording
				if storage_mode != "recording":
					self._copyPosterToRecording(fp, poster_path)
				# providers summary
				# Für Report: Bereinigten Serientitel ohne S##E## verwenden
				_report_title = title_guess
				if mtype == 'tv':
					_ep_info_r = parse_episode_info(os.path.basename(fp))
					_clean_r = (_ep_info_r.get('series_title') or title_guess)
					if _clean_r and _clean_r != title_guess:
						_report_title = _clean_r
					if _ep_info_r.get('season'):
						_report_title += ' [S%02d' % _ep_info_r['season']
						if _ep_info_r.get('episode'):
							_report_title += 'E%02d' % _ep_info_r['episode']
						_report_title += ']'
				prov_lines.append('%s | type=%s | title=%s | poster=%s | backdrop=%s | banner=%s' % (os.path.basename(fp), ('tv' if mtype=='tv' else 'movie'), _report_title, (poster_provider or '-'), (backdrop_provider or '-'), (banner_provider or '-')))
				if poster_provider: poster_by[poster_provider] = poster_by.get(poster_provider,0)+1
				if backdrop_provider: backdrop_by[backdrop_provider] = backdrop_by.get(backdrop_provider,0)+1
				if banner_provider: banner_by[banner_provider] = banner_by.get(banner_provider,0)+1
				self.stats["ok"] += 1 if ok_any else 0
				self.stats["skipped"] += 1 if not ok_any else 0
				
				if ok_any:
					ok_details.append('%s | type=%s | title=%s | poster=%s | backdrop=%s | banner=%s' % (os.path.basename(fp), ('tv' if mtype=='tv' else 'movie'), title_guess, (poster_provider or '-'), (backdrop_provider or '-'), (banner_provider or '-')))
				else:
					skip_details.append('%s | title=%s' % (os.path.basename(fp), title_guess))
				
			except Exception as e:
				self.stats["err"] += 1
				rep_lines.append("ERR %s: %s" % (os.path.basename(fp), str(e)[:120]))
			finally:
				self.stats["done"] += 1
				self._ui_progress()

		# write provider report
		try:
			ts = _time.strftime('%Y%m%d_%H%M%S')
			pr_path = os.path.join(EMC_BASE, 'scanner_providers_%s.txt' % ts)
			os.makedirs(EMC_BASE, exist_ok=True)
			with open(pr_path, 'w') as pf:
				pf.write('GradientFHD Provider Report\n')
				pf.write('Total: %(total)d Done: %(done)d OK: %(ok)d Skip: %(skipped)d Err: %(err)d\n\n' % self.stats)
				if poster_by:
					pf.write('Poster:\n')
					for k,v in poster_by.items(): pf.write('  %s: %d\n' % (k, v))
					pf.write('\n')
				else:
					pf.write('Poster:\n  (none)\n\n')
				if backdrop_by:
					pf.write('Backdrop:\n')
					for k,v in backdrop_by.items(): pf.write('  %s: %d\n' % (k, v))
					pf.write('\n')
				else:
					pf.write('Backdrop:\n  (none)\n\n')
				if banner_by:
					pf.write('Banner:\n')
					for k,v in banner_by.items(): pf.write('  %s: %d\n' % (k, v))
					pf.write('\n')
				else:
					pf.write('Banner:\n  (none)\n\n')
				for ln in prov_lines: pf.write(ln+'\n')
		except Exception:
			pass
		try:
			with open(REPORT_PATH, "w") as f:
				f.write("GradientFHD Scanner Report\n")
				f.write("Total: %(total)d Done: %(done)d OK: %(ok)d Skip: %(skipped)d Err: %(err)d\n\n" % self.stats)
				f.write("Providers Summary\n")
				if poster_by:
					f.write("Poster: " + ", ".join("%s %d" % (k, poster_by[k]) for k in sorted(poster_by.keys())) + "\n")
				else:
					f.write("Poster: (none)\n")
				if backdrop_by:
					f.write("Backdrop: " + ", ".join("%s %d" % (k, backdrop_by[k]) for k in sorted(backdrop_by.keys())) + "\n")
				else:
					f.write("Backdrop: (none)\n")
				if banner_by:
					f.write("Banner: " + ", ".join("%s %d" % (k, banner_by[k]) for k in sorted(banner_by.keys())) + "\n")
				else:
					f.write("Banner: (none)\n")
				f.write("\nOK items (%d):\n" % len(ok_details))
				for ln in ok_details:
					f.write("- " + ln + "\n")
				f.write("\nSkipped items (%d):\n" % len(skip_details))
				for ln in skip_details:
					f.write("- " + ln + "\n")
		except Exception:
			pass

		self._ui_finish()

	# UI-Updates (thread-safe)
	def _ui_set_current(self, text, idx):
		from twisted.internet.reactor import callFromThread
		def apply():
			# Current item
			total = max(int(self.stats.get("total", 0) or 0), 0)
			prefix = _t("Aktuell", "Current")
			counter = (" (%d/%d)" % (idx, total)) if total else (" (%d)" % idx)
			line = "%s: %s%s" % (prefix, text, counter)
			# Preferred: dedicated widget so the skin can position/color it freely
			try:
				self["current"].setText(line)
			except Exception:
				pass
			# Backward compatible: if the skin has no "current" widget, show it in the hint area
			if not getattr(self, "_has_current_widget", False):
				try:
					self["hint"].setText(line + ("\n\n" + self._hint_base if self._hint_base else ""))
				except Exception:
					pass
			if self.stats["total"]:
				val = int(idx * 100.0 / max(self.stats["total"], 1))
				self["progress"].setValue(val)
			self["status"].setText("Gesamt: %(total)d  Fertig: %(done)d  Poster: %(poster)d  Backdrop: %(backdrop)d  Banner: %(banner)d  Skip: %(skipped)d  Err: %(err)d" % self.stats)
		callFromThread(apply)

	def _ui_progress(self):
		from twisted.internet.reactor import callFromThread
		def apply():
			done = self.stats["done"]
			total = max(self.stats["total"], 1)
			self["progress"].setValue(int(done * 100.0 / total))
			self["status"].setText("Gesamt: %(total)d  Fertig: %(done)d  Poster: %(poster)d  Backdrop: %(backdrop)d  Banner: %(banner)d  Skip: %(skipped)d  Err: %(err)d" % self.stats)
		callFromThread(apply)

	def _ui_finish(self):
		from twisted.internet.reactor import callFromThread
		def apply():
			if self.stop_flag:
				msg = _t("Abgebrochen.", "Aborted.")
			else:
				msg = _t("Fertig. Report: %s", "Done. Report: %s") % REPORT_PATH
			try:
				self["info"].setText(msg)
			except Exception:
				pass
			self["status"].setText("Gesamt: %(total)d  Fertig: %(done)d  Poster: %(poster)d  Backdrop: %(backdrop)d  Banner: %(banner)d  Skip: %(skipped)d  Err: %(err)d" % self.stats)
			try:
				self["hint"].setText(msg + ("\n\n" + self._hint_base if self._hint_base else ""))
			except Exception:
				pass
		callFromThread(apply)

	# Downloader/Provider
	def _download_image(self, url, dest):
		if not requests:
			return False
		try:
			r = requests.get(url, stream=True, timeout=12, allow_redirects=True)
			if r.status_code == 200:
				with open(dest, "wb") as f:
					for chunk in r.iter_content(1024 * 32):
						if not chunk:
							break
						f.write(chunk)
				Image.open(dest).verify()
				return True
		except Exception:
			pass
		try:
			if os.path.exists(dest):
				os.remove(dest)
		except Exception:
			pass
		return False

	def _try_tmdb(self, title, mtype, lang, year, api_key, need_poster, poster_path, need_backdr, backdr_path):
		if not requests:
			return False
		try:
			def first_result(url):
				try:
					js = requests.get(url, timeout=10).json()
					res = js.get("results") or []
					if res:
						return res[0]
				except Exception:
					pass
				return None

			def tmdb_urls(srch_type):
				base = "https://api.themoviedb.org/3/search/%s?api_key=%s&query=%s" % (srch_type, api_key, quote(title))
				urls = []
				if lang:
					if year and srch_type == "movie":
						urls.append(base + "&language=%s&year=%s" % (lang, year))
					elif year and srch_type == "tv":
						urls.append(base + "&language=%s&first_air_date_year=%s" % (lang, year))
					urls.append(base + "&language=%s" % lang)
				urls.append(base)
				return urls

			srch_type = "tv" if mtype == "tv" else ("movie" if mtype == "movie" else cfg_search_type())
			result = None
			for url in tmdb_urls(srch_type):
				result = first_result(url)
				if result:
					break
			if not result and srch_type != "multi":
				for url in tmdb_urls("multi"):
					result = first_result(url)
					if result:
						break
			if not result:
				return False

			p_size = getattr(config.plugins.GradientFHD.scanner, "TMDBpostersize", None)
			p_size = p_size.value if p_size else "w342"
			b_size = getattr(config.plugins.GradientFHD.scanner, "TMDBbackdropsize", None)
			b_size = b_size.value if b_size else "w780"

			ok_any = False
			if need_poster and result.get("poster_path"):
				urlp = "https://image.tmdb.org/t/p/%s%s" % (p_size, result["poster_path"]) 
				ok_any |= self._download_image(urlp, poster_path)
			if need_backdr and result.get("backdrop_path"):
				urlb = "https://image.tmdb.org/t/p/%s%s" % (b_size, result["backdrop_path"]) 
				ok_any |= self._download_image(urlb, backdr_path)
			return ok_any
		except Exception:
			return False

		def first_result(url):
			try:
				js = requests.get(url, timeout=10).json()
				res = js.get("results") or []
				if res:
					return res[0]
			except Exception:
				pass
			return None

		def tmdb_urls(srch_type):
			base = "https://api.themoviedb.org/3/search/%s?api_key=%s&query=%s" % (srch_type, api_key, quote(title))
			urls = []
			if lang:
				if year and srch_type == "movie":
					urls.append(base + "&language=%s&year=%s" % (lang, year))
				elif year and srch_type == "tv":
					urls.append(base + "&language=%s&first_air_date_year=%s" % (lang, year))
				urls.append(base + "&language=%s" % lang)
			urls.append(base)
			return urls

		srch_type = "tv" if mtype == "tv" else ("movie" if mtype == "movie" else cfg_search_type())
		result = None
		for url in tmdb_urls(srch_type):
			result = first_result(url)
			if result:
				break
		if not result and srch_type != "multi":
			for url in tmdb_urls("multi"):
				result = first_result(url)
				if result:
					break
		if not result:
			return False

		p_size = getattr(config.plugins.GradientFHD.scanner, "TMDBpostersize", None)
		p_size = p_size.value if p_size else "w342"
		b_size = getattr(config.plugins.GradientFHD.scanner, "TMDBbackdropsize", None)
		b_size = b_size.value if b_size else "w780"

		ok_any = False
		if need_poster and result.get("poster_path"):
			urlp = "https://image.tmdb.org/t/p/%s%s" % (p_size, result["poster_path"])
			ok_any |= self._download_image(urlp, poster_path)
		if need_backdr and result.get("backdrop_path"):
			urlb = "https://image.tmdb.org/t/p/%s%s" % (b_size, result["backdrop_path"])
			ok_any |= self._download_image(urlb, backdr_path)
				# removed NEU copy block
		try:
			if getattr(config.plugins.GradientFHD.scanner, 'copyPosterToRecording', None) \
					and config.plugins.GradientFHD.scanner.copyPosterToRecording.value:
				src = poster_path
				if os.path.exists(src) and os.path.getsize(src) > 0:
					base, _ext = os.path.splitext(fp)
					dst = base + ".jpg"
					do_copy = True
					if os.path.exists(dst):
						try:
							from PIL import Image
							Image.open(dst).verify()
							do_copy = False
						except Exception:
							do_copy = True
					if do_copy:
						import shutil
						shutil.copyfile(src, dst)
		except Exception:
			pass
		# --- NEU Ende ---


		return ok_any

	def _try_tvdb_legacy(self, title, lang, api_key, need_poster, poster_path, need_backdr, backdr_path):
		if not requests or not api_key:
			return False
		if not _is_tvdb_hex32_key(api_key):
			return False
		prefer_langs = (lang or 'de', 'en', '')
		_sid, xml, _gsxml = _tvdb_legacy_fetch_xml(title, api_key, prefer_langs=prefer_langs)
		if not xml:
			return False
		ok_any = False
		if need_poster:
			path = _tvdb_legacy_pick_banner(xml, want='poster', prefer_langs=prefer_langs)
			urlp = _tvdb_legacy_banner_url(path) if path else None
			if urlp:
				ok_any |= self._download_image(urlp, poster_path)
		if need_backdr:
			path = _tvdb_legacy_pick_banner(xml, want='fanart', prefer_langs=prefer_langs)
			urlb = _tvdb_legacy_banner_url(path) if path else None
			if urlb:
				ok_any |= self._download_image(urlb, backdr_path)
		return ok_any

	def _try_tvdb(self, title, mtype, lang, api_key, need_poster, poster_path, need_backdr, backdr_path):
		if not requests:
			return False
		key = (api_key or '').strip()
		if not key:
			return False
		if not _is_tvdb_uuid_key(key):
			return self._try_tvdb_legacy(title, lang, key, need_poster, poster_path, need_backdr, backdr_path)
		token = tvdb4_ensure_token(key, pin=get_tvdb_pin())
		if not token:
			# v4 login failed -> fall back to legacy key for poster/backdrop
			return self._try_tvdb_legacy(title, lang, get_tvdb_legacy_key(), need_poster, poster_path, need_backdr, backdr_path)
		try:
			if mtype == 'movie':
				kinds = ['movie', 'series']
			else:
				kinds = ['series', 'movie']
			cand = None
			for k in kinds:
				k = "series" if k == "tv" else ("movie" if k == "movie" else k)
				js = tvdb4_get('/search', params={"query": title, "type": k})
				data = (js or {}).get('data') or []
				if data:
					cand = data[0]
					break
			if not cand:
				js = tvdb4_get('/search', params={"query": title})
				data = (js or {}).get('data') or []
				if data:
					cand = data[0]
			if not cand:
				# v4 found nothing -> try legacy poster/backdrop
				return self._try_tvdb_legacy(title, lang, get_tvdb_legacy_key(), need_poster, poster_path, need_backdr, backdr_path)
			cid = cand.get('id')
			ctype = cand.get('type')
			posters = []
			backs = []
			if ctype == 'series':
				a = tvdb4_get('/series/%s/artworks' % cid)
				arts = (a or {}).get('data') or []
				for it in arts:
					t = ((it.get('type') or {}).get('name') or '').lower()
					img = it.get('image') or ''
					lg = (it.get('language') or '')
					if not img:
						continue
					if 'poster' in t:
						posters.append((lg,img))
					elif 'background' in t or 'fanart' in t or 'backdrop' in t:
						backs.append((lg,img))
			else:
				a = tvdb4_get('/movies/%s/extended' % cid)
				arts = ((a or {}).get('data') or {}).get('artworks') or []
				for it in arts:
					t = ((it.get('type') or {}).get('name') or '').lower()
					img = it.get('image') or ''
					lg = (it.get('language') or '')
					if not img:
						continue
					if 'poster' in t:
						posters.append((lg,img))
					elif 'background' in t or 'fanart' in t or 'backdrop' in t:
						backs.append((lg,img))
			def pick_by_language(items, lang_code):
				if not items:
					return None
				pref = (lang_code or '').lower()
				map3 = {'de':'deu','en':'eng','fr':'fra','it':'ita','es':'spa','pt':'por','nl':'nld','pl':'pol'}
				prefs = [pref, map3.get(pref, None)]
				for pr in prefs:
					if not pr: continue
					for (lg,u) in items:
						if (lg or '').lower().startswith(pr):
							return u
				for (lg,u) in items:
					if not lg:
						return u
				return items[0][1]
			ok_any = False
			if need_poster and posters:
				urlp = pick_by_language(posters, lang)
				if urlp:
					ok_any |= self._download_image(urlp, poster_path)
			if need_backdr and backs:
				urlb = pick_by_language(backs, lang)
				if urlb:
					ok_any |= self._download_image(urlb, backdr_path)
			return ok_any
		except Exception:
			return False

			def pick_by_language(items, lang_code):
				if not items:
					return None
				pref = (lang_code or '').lower()
				map3 = {'de':'deu','en':'eng','fr':'fra','it':'ita','es':'spa'}
				prefs = [pref, map3.get(pref, None)]
				for pr in prefs:
					if not pr: continue
					for (lg,u) in items:
						if (lg or '').lower().startswith(pr):
							return u
				for (lg,u) in items:
					if not lg:
						return u
				return items[0][1]
			if need_poster and posters:
				urlp = pick_by_language(posters, lang)
				if urlp:
					ok_any |= self._download_image(urlp, poster_path)
			if need_backdr and backs:
				urlb = pick_by_language(backs, lang)
				if urlb:
					ok_any |= self._download_image(urlb, backdr_path)
			return ok_any
		except Exception:
			return False

	def _try_fanart_banner(self, title, mtype, api_key, banner_path):
		if not requests:
			return False
		try:
			tmdb_key = get_tmdb_key()
			if not tmdb_key:
				return False

			def first_result(url):
				try:
					js = requests.get(url, timeout=10).json()
					res = js.get('results') or []
					if res:
						return res[0]
				except Exception:
					return None
				return None

			srch_type = 'tv' if mtype == 'tv' else ('movie' if mtype == 'movie' else cfg_search_type())
			base = 'https://api.themoviedb.org/3/search/%s?api_key=%s&query=%s' % (srch_type, tmdb_key, quote(title))
			urls = [base]
			lng = lang_param()
			if lng:
				urls.insert(0, base + '&language=%s' % lng)
			if srch_type == 'movie':
				m = re.search(r'(19|20)\d{2}', title)
				if m:
					urls.insert(0, base + '&language=%s&year=%s' % (lng, m.group(0)))
			res = None
			for u in urls:
				res = first_result(u)
				if res:
					break
			if not res and srch_type != 'multi':
				base = 'https://api.themoviedb.org/3/search/multi?api_key=%s&query=%s' % (tmdb_key, quote(title))
				urls = [base]
				if lng:
					urls.insert(0, base + '&language=%s' % lng)
				for u in urls:
					res = first_result(u)
					if res:
						break
			if not res:
				# Fallback reine Titelsuche bei Fanart
				try:
					if mtype == 'movie':
						url = 'https://webservice.fanart.tv/v3/movies?api_key=%s&title=%s' % (api_key, quote(title))
						js = requests.get(url, timeout=10).json()
						banners = js.get('movie', [{}])[0].get('moviebanner') or []
					else:
						url = 'https://webservice.fanart.tv/v3/tv?api_key=%s&title=%s' % (api_key, quote(title))
						js = requests.get(url, timeout=10).json()
						banners = js.get('tv', [{}])[0].get('tvbanner') or []
					if not banners:
						return False
					urlb = banners[0].get('url')
					if not urlb:
						return False
					return self._download_image(urlb, banner_path)
				except Exception:
					return False

			media_type = res.get('media_type') or srch_type
			tmdb_id = res.get('id')
			if media_type == 'movie':
				f = requests.get('https://webservice.fanart.tv/v3/movies/%s?api_key=%s' % (tmdb_id, api_key), timeout=10)
				if f.status_code != 200:
					return False
				js = f.json()
				banners = js.get('moviebanner') or []
				if not banners:
					return False
				urlb = banners[0].get('url')
				if not urlb:
					return False
				return self._download_image(urlb, banner_path)
			else:
				ext = requests.get('https://api.themoviedb.org/3/tv/%s/external_ids?api_key=%s' % (tmdb_id, tmdb_key), timeout=10)
				tvdb_id = None
				if ext.status_code == 200:
					try:
						tvdb_id = ext.json().get('tvdb_id')
					except Exception:
						tvdb_id = None
				if not tvdb_id:
					return False
				f = requests.get('https://webservice.fanart.tv/v3/tv/%s?api_key=%s' % (tvdb_id, api_key), timeout=10)
				if f.status_code != 200:
					return False
				js = f.json()
				banners = js.get('tvbanner') or []
				if not banners:
					return False
				urlb = banners[0].get('url')
				if not urlb:
					return False
				return self._download_image(urlb, banner_path)
		except Exception:
			return False


	def _copyPosterToRecording(self, fp, poster_path):
		try:
			from Components.config import config
			if getattr(config.plugins.GradientFHD.scanner, 'copyPosterToRecording', None) and                     config.plugins.GradientFHD.scanner.copyPosterToRecording.value:
				if os.path.exists(poster_path) and os.path.getsize(poster_path) > 0:
					base, _ext = os.path.splitext(fp)
					dst = base + '.jpg'
					do_copy = True
					if os.path.exists(dst):
						try:
							from PIL import Image
							Image.open(dst).verify()
							do_copy = False
						except Exception:
							do_copy = True
					if do_copy:
						import shutil
						shutil.copyfile(poster_path, dst)
		except Exception:
			pass

	def _try_omdb_poster(self, title, year, poster_path):
		try:
			import requests
			key = get_omdb_key()
			if not key:
				return False
			url = 'http://www.omdbapi.com/?apikey=%s&t=%s&r=json' % (key, requests.utils.quote(title))
			if year:
				url += '&y=%s' % year
			js = requests.get(url, timeout=8).json()
			if js.get('Response') != 'True':
				return False
			purl = js.get('Poster') or ''
			if not purl or purl in ('N/A',):
				return False
			return self._download_image(purl, poster_path)
		except Exception:
			return False
	def _try_tvdb_legacy_banner(self, title, lang, api_key, banner_path):
		"""Download a banner via the TVDb Legacy XML API.

		api_key must be a 32-hex legacy key. If a UUID v4 key is passed,
		we try to resolve the legacy key from thetvdbkey_legacy file or the
		built-in TVDB_LEGACY_DEFAULT_KEY so banners still work alongside v4.
		"""
		if not requests or not api_key:
			return False

		legacy_key = (api_key or '').strip()

		# If caller passed a UUID key, we cannot use it for legacy XML.
		# Try to find a usable legacy key instead.
		if not _is_tvdb_hex32_key(legacy_key):
			resolved = ''
			# 1) thetvdbkey_legacy file in skin dir
			try:
				lp = os.path.join(_skin_dir(), 'thetvdbkey_legacy')
				if os.path.isfile(lp):
					with open(lp, 'r') as _f:
						_v = (_f.read() or '').strip()
					if _v and _is_tvdb_hex32_key(_v):
						resolved = _v
			except Exception:
				pass
			# 2) Built-in renderer default
			if not resolved:
				try:
					from Components.Renderer import GradientPosterXDownloadThread as _rdt
					_bk = (getattr(_rdt, 'TVDB_LEGACY_DEFAULT_KEY', '') or '').strip()
					if _bk and _is_tvdb_hex32_key(_bk):
						resolved = _bk
				except Exception:
					pass
			if not resolved:
				return False
			legacy_key = resolved

		prefer_langs = (lang or 'de', 'en', '')
		_sid, banners_xml, getseries_xml = _tvdb_legacy_fetch_xml(title, legacy_key, prefer_langs=prefer_langs)

		# 1) Try banners.xml
		path = _tvdb_legacy_pick_banner(banners_xml, want='banner', prefer_langs=prefer_langs) if banners_xml else None

		# 2) Fallback: GetSeries.php <banner>
		if not path and getseries_xml:
			try:
				root = _ET.fromstring(getseries_xml.encode('utf-8') if isinstance(getseries_xml, str) else getseries_xml)
				b = root.findtext('.//Series/banner') or root.findtext('.//banner')
				if b:
					path = b.strip()
			except Exception:
				pass

		urlb = _tvdb_legacy_banner_url(path) if path else None
		if not urlb:
			return False
		return self._download_image(urlb, banner_path)

	def _try_tvdb_banner(self, title, mtype, lang, api_key, banner_path):
		if not requests:
			return False
		key = (api_key or '').strip()
		if not key:
			return False
		# Legacy 32-hex key: use the legacy XML path directly
		if not _is_tvdb_uuid_key(key):
			return self._try_tvdb_legacy_banner(title, lang, key, banner_path)
		# UUID v4 key path follows below.
		# After v4 attempt we also try the legacy path as a fallback so that
		# having a v4 key does NOT break banner loading.
		token = tvdb4_ensure_token(key, pin=get_tvdb_pin())
		if not token:
			# v4 login failed -> immediately try legacy banner
			return self._try_tvdb_legacy_banner(title, lang, get_tvdb_legacy_key(), banner_path)
		try:
			if mtype == 'movie':
				kinds = ['movie', 'series']
			else:
				kinds = ['series', 'movie']
			cand = None
			for k in kinds:
				k = 'series' if k == 'tv' else ('movie' if k == 'movie' else k)
				js = tvdb4_get('/search', params={'query': title, 'type': k})
				data = (js or {}).get('data') or []
				if data:
					cand = data[0]
					break
			if not cand:
				js = tvdb4_get('/search', params={'query': title})
				data = (js or {}).get('data') or []
				if data:
					cand = data[0]
			# v4 found nothing -> try legacy
			if not cand:
				return self._try_tvdb_legacy_banner(title, lang, get_tvdb_legacy_key(), banner_path)
			cid = cand.get('id')
			ctype = cand.get('type')
			arts = []
			if ctype == 'series':
				a = tvdb4_get('/series/%s/artworks' % cid)
				arts = (a or {}).get('data') or []
				# Also try extended endpoint for series
				if not arts:
					a2 = tvdb4_get('/series/%s/extended' % cid)
					arts = ((a2 or {}).get('data') or {}).get('artworks') or []
			else:
				a = tvdb4_get('/movies/%s/extended' % cid)
				arts = ((a or {}).get('data') or {}).get('artworks') or []
			if not arts:
				# v4 has no artworks -> try legacy banner
				return self._try_tvdb_legacy_banner(title, lang, get_tvdb_legacy_key(), banner_path)
			# Build candidate list with scoring
			pref2 = (lang or '').lower()
			pref3 = {'de':'deu','en':'eng','fr':'fra','it':'ita','es':'spa','pt':'por','nl':'nld','pl':'pol'}.get(pref2, pref2)
			items = []  # (score, url)
			for it in arts:
				t = ((it.get('type') or {}).get('name') or '').lower()
				if not any(x in t for x in ('banner','serieswide','wide')):
					continue
				url = it.get('image') or ''
				if not url:
					continue
				lg = (it.get('language') or '').lower()
				st = it.get('status')
				if isinstance(st, dict):
					st = (st.get('name') or st.get('value') or '').lower()
				else:
					st = (st or '').lower()
				w = it.get('width') or 0
				try:
					w = int(w)
				except Exception:
					w = 0
				score = 0
				if lg in (pref2, pref3):
					score += 50
				if st == 'approved':
					score += 20
				if 'serieswide' in t:
					score += 5
				if 'banner' in t:
					score += 3
				if w and w >= 1000:
					score += 10
				items.append((score, url))
			if not items:
				# v4 found no banner artwork -> try legacy
				return self._try_tvdb_legacy_banner(title, lang, get_tvdb_legacy_key(), banner_path)
			items.sort(key=lambda x: x[0], reverse=True)
			best_url = items[0][1]
			if self._download_image(best_url, banner_path):
				return True
			# v4 download failed -> try legacy as fallback
			return self._try_tvdb_legacy_banner(title, lang, get_tvdb_legacy_key(), banner_path)
		except Exception:
			# v4 raised -> legacy as last resort
			try:
				return self._try_tvdb_legacy_banner(title, lang, get_tvdb_legacy_key(), banner_path)
			except Exception:
				return False

			def pick_by_language(items, lang_code):
				if not items:
					return None
				pref = (lang_code or '').lower()
				map3 = {'de':'deu','en':'eng','fr':'fra','it':'ita','es':'spa'}
				prefs = [pref, map3.get(pref, None)]
				for pr in prefs:
					if not pr:
						continue
					for (lg,u) in items:
						if (lg or '').lower().startswith(pr):
							return u
				for (lg,u) in items:
					if not lg:
						return u
				return items[0][1]
			urlb = pick_by_language(banners, lang)
			if not urlb:
				return False
			return self._download_image(urlb, banner_path)
		except Exception:
			return False


# ===== TVDB v4 Helper (modulweit) =====
TVDB4_BASE = 'https://api4.thetvdb.com/v4'

# ============================================================================
# SEASON / EPISODE ARTWORK MODULE (eingebettet)
# ============================================================================
# -*- coding: utf-8 -*-
# ============================================================================
#  GradientFHD – Season Poster + Episode Still/Backdrop
#  Modul-Patch für GradientMoviescanner.py
#
#  Neue Dateinamen-Konvention im EMC-Cache:
#    Serien-Poster   (fallback):   <safe_name>.jpg
#    Staffel-Poster:               <safe_name>_S01.jpg
#    Episode-Backdrop (Still):     <safe_name>_S01E01.jpg
#    Serien-Banner   (fallback):   <safe_name>.jpg (unverändert)
#
#  Funktioniert mit:
#    - TMDb  (Staffel-Poster + Episode-Still)
#    - TVDb v4 (Staffel-Poster + Episode-Still)
#    - TVDb Legacy XML (Staffel-Poster über banners.xml)
#
#  Benötigt:   requests, PIL, enigma2/OpenATV
#  Einbindung: wird in GradientMoviescanner._worker() aufgerufen
# ============================================================================

import os
import re


# ============================================================================
# HELPER: Episode-Info aus Dateinamen extrahieren
# ============================================================================

def parse_season_episode(filename):
    """Wrapper: gibt (season, episode) zurück – Kompatibilität mit altem Code."""
    info = parse_episode_info(filename)
    return info.get('season'), info.get('episode')


def parse_episode_info(filename):
    """
    Vollständige Episode-Erkennung für alle Dateiname-Formate:

      FORMAT 1 – S##E##:
        'Babylon Berlin S01E01.mkv'
        → series='Babylon Berlin', S=1, E=1

      FORMAT 2 – NxNN:
        'Band.of.Brothers.1x06.mkv'
        → series='Band of Brothers', S=1, E=6

      FORMAT 3 – N. Titel (Dokumentationen):
        'Kevin Costner\'s The West 1. Das Ende der Konföderation.stream'
        → series='Kevin Costner\'s The West', S=1, E=1, ep_title='Das Ende...'

      FORMAT 4 – Serie-Episodentitel:
        'Wir waren wie Brüder-Bastogne.mp4'
        → series='Wir waren wie Brüder', ep_title='Bastogne'

    Returns:
        dict {
          'series_title': str,    – Bereinigter Serientitel ohne Episoden-Info
          'season':       int|None,
          'episode':      int|None,
          'ep_title':     str|None,  – Episodentitel für API-Matching
          'format':       str         – Erkanntes Format
        }
    """
    base = os.path.basename(filename or '')
    stem = os.path.splitext(base)[0]
    stem = stem.strip()
    result = {'series_title': stem, 'season': None, 'episode': None,
              'ep_title': None, 'format': 'unknown'}

    # FORMAT 1: S01E05 / S01E5 / S1E05
    m = re.search(r'(.*?)\s*[Ss](\d{1,2})[Ee](\d{1,3})(.*)', stem)
    if m:
        series = m.group(1).strip().rstrip('-').strip()
        result['series_title'] = series if series else stem
        result['season']  = int(m.group(2))
        result['episode'] = int(m.group(3))
        result['format']  = 'SxxExx'
        rest = m.group(4).strip().lstrip('-').strip()
        if rest and len(rest) > 3:
            result['ep_title'] = rest
        return result

    # FORMAT 2: 1x06 / 01x06
    m = re.search(r'(.*?)\s*\b(\d{1,2})[xX](\d{1,3})\b(.*)', stem)
    if m:
        series = m.group(1).strip().rstrip('-').strip()
        # Punkte als Leerzeichen (Band.of.Brothers.)
        series = re.sub(r'\.+', ' ', series).strip().rstrip('.').strip()
        result['series_title'] = series if series else stem
        result['season']  = int(m.group(2))
        result['episode'] = int(m.group(3))
        result['format']  = 'NxNN'
        rest = m.group(4).strip().lstrip('-').strip()
        if rest and len(rest) > 3:
            result['ep_title'] = rest
        return result

    # FORMAT 3: 'Kevin Costner\'s The West 1. Das Ende...'
    # Muster: <Serientitel> <Zahl>. <Episodentitel>
    m = re.search(r'^(.+?)\s+(\d{1,3})\.\s+(.+)$', stem)
    if m:
        series   = m.group(1).strip()
        ep_num   = int(m.group(2))
        ep_title = m.group(3).strip()
        if 1 <= ep_num <= 99 and len(series) >= 3:
            result['series_title'] = series
            result['season']  = 1       # Dokumentationen: immer Staffel 1
            result['episode'] = ep_num
            result['ep_title'] = ep_title
            result['format']  = 'N.Title'
            return result

    # FORMAT 4: 'Wir waren wie Brüder-Bastogne' (Serie-Episodentitel)
    m = re.search(r'^(.+?)\s*[-–]\s*(.+)$', stem)
    if m:
        part1 = m.group(1).strip()
        part2 = m.group(2).strip()
        if len(part1) >= 4 and len(part2) >= 2:
            result['series_title'] = part1
            result['ep_title']     = part2
            result['format']       = 'Series-EpTitle'
            return result

    return result


def make_season_safe_name(safe_series_name, season):
    """
    Staffel-Poster Dateiname:  <safe_series>_S01.jpg
    """
    return '%s_S%02d' % (safe_series_name, season)


def make_episode_safe_name(safe_series_name, season, episode):
    """
    Episode-Backdrop Dateiname:  <safe_series>_S01E05.jpg
    """
    return '%s_S%02dE%02d' % (safe_series_name, season, episode)


# ============================================================================
# TMDb: Staffel-Poster & Episode-Still
# ============================================================================

def tmdb_get_series_id(title, lang, year, api_key, requests_mod):
    """Sucht TMDb-ID einer TV-Serie."""
    from urllib.parse import quote
    base = 'https://api.themoviedb.org/3/search/tv?api_key=%s&query=%s' % (
        api_key, quote(title))
    urls = []
    if lang:
        if year:
            urls.append(base + '&language=%s&first_air_date_year=%s' % (lang, year))
        urls.append(base + '&language=%s' % lang)
    urls.append(base)

    for url in urls:
        try:
            js = requests_mod.get(url, timeout=10).json()
            res = (js.get('results') or [])
            if res:
                return res[0].get('id')
        except Exception:
            pass
    return None


def tmdb_get_season_poster(series_id, season, lang, api_key, requests_mod):
    """
    TMDb Staffel-Poster.
    GET /tv/{series_id}/season/{season}?api_key=...&language=de-DE
    → data['poster_path']
    """
    if not series_id or season is None:
        return None
    url = 'https://api.themoviedb.org/3/tv/%s/season/%d?api_key=%s' % (
        series_id, season, api_key)
    if lang:
        url += '&language=%s' % lang

    try:
        js = requests_mod.get(url, timeout=10).json()
        p = js.get('poster_path')
        if p:
            return 'https://image.tmdb.org/t/p/w342%s' % p
    except Exception:
        pass
    return None


def tmdb_get_episode_still(series_id, season, episode, lang, api_key, requests_mod):
    """
    TMDb Episode-Still (Thumbnail/Screenshot der Episode).
    GET /tv/{series_id}/season/{season}/episode/{ep}?api_key=...
    → data['still_path']
    """
    if not series_id or season is None or episode is None:
        return None
    url = 'https://api.themoviedb.org/3/tv/%s/season/%d/episode/%d?api_key=%s' % (
        series_id, season, episode, api_key)
    if lang:
        url += '&language=%s' % lang

    try:
        js = requests_mod.get(url, timeout=10).json()
        s = js.get('still_path')
        if s:
            return 'https://image.tmdb.org/t/p/w780%s' % s
    except Exception:
        pass
    return None


# ============================================================================
# TMDb: Episode-Titel-Matching (für "Band of Brothers – Bastogne" Stil)
# ============================================================================

def tmdb_find_episode_by_title(series_id, episode_title, lang, api_key, requests_mod,
                               ep_index=None, total_eps=None):
    """
    Sucht Episode über Titel (DE+EN) mit Fuzzy-Matching.
    
    Fallback: Wenn kein Titel-Match → Positions-basiertes Matching
      ep_index=2 bei 10 Dateien → Episode 2 in Staffel 1

    Returns: (season: int, episode: int) oder (None, None)
    """
    if not series_id:
        return None, None

    def _norm_ep(s):
        s = (s or '').lower().strip()
        s = s.replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss')
        import unicodedata
        s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
        return re.sub(r'[^a-z0-9]', '', s)

    ep_norm = _norm_ep(episode_title or '')
    
    for season_n in range(1, 9):
        # Lade Staffel in BEIDEN Sprachen auf einmal
        ep_pool = {}   # ep_num → [norm_name1, norm_name2, ...]
        ep_count = 0
        
        for lang_try in ([lang, 'en-US'] if lang and not lang.startswith('en') else ['en-US']):
            url = 'https://api.themoviedb.org/3/tv/%s/season/%d?api_key=%s&language=%s' % (
                series_id, season_n, api_key, lang_try)
            try:
                js = requests_mod.get(url, timeout=10).json()
                if js.get('status_code') == 34 or js.get('status_message','').find('404') != -1:
                    break
                eps = js.get('episodes') or []
                if not eps:
                    break
                ep_count = max(ep_count, len(eps))
                for ep in eps:
                    num = ep.get('episode_number')
                    name_n = _norm_ep(ep.get('name') or '')
                    if num not in ep_pool:
                        ep_pool[num] = []
                    if name_n and name_n not in ep_pool[num]:
                        ep_pool[num].append(name_n)
            except Exception:
                continue

        if not ep_pool:
            break   # Diese Staffel existiert nicht → fertig
        
        # Titel-Matching wenn Suchbegriff vorhanden
        if ep_norm:
            for ep_num, names in sorted(ep_pool.items()):
                for name_n in names:
                    if not name_n:
                        continue
                    # Exakter Match
                    if ep_norm == name_n:
                        return season_n, ep_num
                    # Substring-Match (min 5 Zeichen)
                    if len(ep_norm) >= 5 and len(name_n) >= 5:
                        if ep_norm in name_n or name_n in ep_norm:
                            return season_n, ep_num
                        # Wort-basierter Fuzzy: ≥50% der Wörter übereinstimmend
                        words_search = set(ep_norm[i:i+4] for i in range(0, len(ep_norm)-3, 2))
                        words_ep    = set(name_n[i:i+4] for i in range(0, len(name_n)-3, 2))
                        if words_search and words_ep:
                            overlap = len(words_search & words_ep)
                            similarity = overlap / max(len(words_search), len(words_ep))
                            if similarity >= 0.6:  # 60% Ähnlichkeit
                                return season_n, ep_num

        # Positions-basiertes Fallback: 
        # Wenn ep_index bekannt (z.B. 3. Datei alphabetisch = Episode 3)
        if ep_index is not None and 1 <= ep_index <= ep_count:
            sorted_eps = sorted(ep_pool.keys())
            if ep_index <= len(sorted_eps):
                return season_n, sorted_eps[ep_index - 1]
    
    return None, None


# ============================================================================
# TVDb v4: Staffel-Poster & Episode-Still
# ============================================================================

def tvdb4_get_series_id(title, api_key, tvdb4_get_fn, tvdb4_ensure_token_fn, get_tvdb_pin_fn):
    """TVDb v4: Serien-ID für Titel suchen."""
    try:
        pin = get_tvdb_pin_fn() if get_tvdb_pin_fn else None
        token = tvdb4_ensure_token_fn(api_key, pin=pin)
        if not token:
            return None
        for params in (
            {'query': title, 'type': 'series', 'language': 'deu', 'limit': 5},
            {'query': title, 'type': 'series', 'limit': 5},
        ):
            js = tvdb4_get_fn('/search', params=params)
            data = (js or {}).get('data') or []
            if data:
                item = data[0]
                sid = item.get('tvdb_id') or item.get('id')
                try:
                    return int(sid)
                except Exception:
                    pass
    except Exception:
        pass
    return None


def tvdb4_get_season_poster(series_id, season, api_key, tvdb4_get_fn):
    """
    TVDb v4: Staffel-Poster.
    GET /seasons?seriesId=...&type=official → findet season_id für Staffel n
    GET /seasons/{season_id}/artworks → Poster
    """
    if not series_id or season is None:
        return None
    try:
        # Alle Staffeln der Serie holen
        js = tvdb4_get_fn('/series/%d/seasons' % series_id)
        seasons_data = ((js or {}).get('data') or [])
        season_id = None

        for s in seasons_data:
            stype = ((s.get('type') or {}).get('type') or '').lower()
            if stype == 'official' and s.get('number') == season:
                season_id = s.get('id')
                break

        if not season_id:
            return None

        # Artworks der Staffel holen
        js2 = tvdb4_get_fn('/seasons/%d/extended' % season_id)
        artworks = ((js2 or {}).get('data') or {}).get('artwork') or []

        # Poster-Typ suchen (type.id == 7 = season poster in TVDb v4)
        best = None
        for a in artworks:
            atype_id = (a.get('type') or 0)
            try:
                atype_id = int(atype_id)
            except Exception:
                atype_id = 0
            # type 7 = season poster, type 8 = season banner
            if atype_id in (7, 8):
                img = a.get('image') or ''
                if img:
                    best = img
                    break  # Erstes nehmen

        if best:
            if not best.startswith('http'):
                best = 'https://artworks.thetvdb.com' + best
            return best

    except Exception:
        pass
    return None


def tvdb4_get_episode_still(series_id, season, episode, api_key, tvdb4_get_fn):
    """
    TVDb v4: Episode-Thumbnail/Still.
    GET /series/{id}/episodes/official?season={n}&episodeNumber={e}
    → episodes[0].image
    """
    if not series_id or season is None or episode is None:
        return None
    try:
        js = tvdb4_get_fn('/series/%d/episodes/official' % series_id,
                           params={'season': season, 'episodeNumber': episode, 'limit': 1})
        episodes = ((js or {}).get('data') or {}).get('episodes') or []
        if not episodes:
            return None
        img = episodes[0].get('image') or ''
        if img:
            if not img.startswith('http'):
                img = 'https://artworks.thetvdb.com' + img
            return img
    except Exception:
        pass
    return None


def tvdb4_find_episode_by_title(series_id, episode_title, api_key, tvdb4_get_fn):
    """
    TVDb v4: Episode per Titel suchen (für Dateinamen ohne S##E##).
    """
    if not series_id or not episode_title:
        return None, None
    def _norm_tvdb(s):
        s = (s or '').lower().strip()
        s = s.replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss')
        import unicodedata
        s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
        return re.sub(r'[^a-z0-9]', '', s)

    ep_norm = _norm_tvdb(episode_title)
    if not ep_norm:
        return None, None
    try:
        for page in range(0, 5):
            js = tvdb4_get_fn('/series/%d/episodes/official' % series_id,
                               params={'limit': 100, 'page': page})
            episodes = ((js or {}).get('data') or {}).get('episodes') or []
            if not episodes:
                break
            for ep in episodes:
                ep_name = _norm_tvdb(ep.get('name') or '')
                if ep_norm and ep_name:
                    if ep_norm == ep_name:
                        return ep.get('seasonNumber'), ep.get('number')
                    if len(ep_norm) >= 5 and (ep_norm in ep_name or ep_name in ep_norm):
                        return ep.get('seasonNumber'), ep.get('number')
    except Exception:
        pass
    return None, None


# ============================================================================
# TVDb Legacy XML: Staffel-Poster
# ============================================================================

def tvdb_legacy_get_season_poster(series_id, season, api_key, requests_mod):
    """
    TVDb Legacy: Staffel-Poster aus banners.xml.
    BannerType=season, BannerType2=season (nicht 'seasonwide')
    Season wird in der <Season>-Tag überprüft.
    """
    if not series_id or season is None or not api_key:
        return None
    try:
        import xml.etree.ElementTree as ET
        url = 'https://thetvdb.com/api/%s/series/%s/banners.xml' % (
            api_key.strip(), str(series_id).strip())
        r = requests_mod.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.status_code != 200:
            return None
        root = ET.fromstring(r.text.encode('utf-8') if isinstance(r.text, str) else r.text)
        candidates = []
        for b in root.findall('.//Banner'):
            btype  = (b.findtext('BannerType')  or '').strip().lower()
            btype2 = (b.findtext('BannerType2') or '').strip().lower()
            bseas  = b.findtext('Season')
            try:
                bseas = int(bseas or -1)
            except Exception:
                bseas = -1
            path   = (b.findtext('BannerPath') or '').strip()
            if not path:
                continue
            # Staffel-Poster: BannerType=season, BannerType2=season (Hochformat)
            if btype == 'season' and btype2 == 'season' and bseas == season:
                lang = (b.findtext('Language') or '').strip().lower()
                candidates.append((lang, path))

        if not candidates:
            return None

        for pl in ('de', 'en', ''):
            for lang, path in candidates:
                if (lang or '') == pl:
                    p = path.lstrip('/')
                    return 'https://artworks.thetvdb.com/banners/%s' % p
        p = candidates[0][1].lstrip('/')
        return 'https://artworks.thetvdb.com/banners/%s' % p
    except Exception:
        pass
    return None


# ============================================================================
# Haupt-Funktion: Staffel+Episode Artwork herunterladen
# ============================================================================


def resolve_episode_assignments_for_folder(folder, series_title, series_id,
                                            lang, api_key, requests_mod,
                                            tvdb4_get_fn=None):
    """
    Liest ALLE Dateien im Ordner mit dem gleichen Serientitel-Präfix.
    Weist jeder Datei eine Episode-Nummer zu:
      1. DE-Titel Match (TMDb de-DE)
      2. EN-Titel Match (TMDb en-US)
      3. Kollisions-freier Positions-Fallback (nächste freie Nummer)

    Returns:
        dict { basename → episode_number }
    """
    import glob as _glob

    def _norm(s):
        s = (s or '').lower().strip()
        s = s.replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss')
        import unicodedata
        s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
        return re.sub(r'[^a-z0-9]', '', s)

    series_norm = _norm(series_title)

    # Alle Mediendateien im Ordner finden die zum Serientitel passen
    MEDIA_EXT = {'.mp4','.mkv','.avi','.ts','.m4v','.mov','.stream'}
    candidates = []
    try:
        for fn in sorted(os.listdir(folder)):
            ext = os.path.splitext(fn)[1].lower()
            if ext not in MEDIA_EXT:
                continue
            info = parse_episode_info(fn)
            fn_series = _norm(info.get('series_title') or '')
            # Muss zum gleichen Serientitel gehören
            if fn_series == series_norm or series_norm in fn_series or fn_series in series_norm:
                ep_title = (info.get('ep_title') or '').strip()
                candidates.append((fn, ep_title, info))
    except Exception:
        return {}

    if not candidates:
        return {}

    # Episode-Titel aus TMDb laden (DE + EN)
    tmdb_ep_de = {}   # ep_num → norm_title
    tmdb_ep_en = {}
    if series_id and api_key and requests_mod:
        for lang_try, target in [(lang or 'de-DE', tmdb_ep_de), ('en-US', tmdb_ep_en)]:
            for season_n in range(1, 3):  # Staffel 1 + 2 (meist Staffel 1)
                url = 'https://api.themoviedb.org/3/tv/%s/season/%d?api_key=%s&language=%s' % (
                    series_id, season_n, api_key, lang_try)
                try:
                    js = requests_mod.get(url, timeout=10).json()
                    if js.get('status_code') == 34:
                        break
                    for ep in (js.get('episodes') or []):
                        num  = ep.get('episode_number')
                        name = _norm(ep.get('name') or '')
                        if num and name:
                            target[num] = name
                except Exception:
                    continue

    # Zuweisung in 2 Pässen
    assignments = {}   # filename → ep_num
    used_eps    = set()

    # PASS 1: Exakter Titel-Match (DE zuerst, dann EN)
    for fn, ep_title, info in candidates:
        if not ep_title:
            continue
        ep_n = _norm(ep_title)
        matched = None
        for ep_map in [tmdb_ep_de, tmdb_ep_en]:
            for num, title_n in ep_map.items():
                if not title_n:
                    continue
                if ep_n == title_n:
                    matched = num
                    break
                if len(ep_n) >= 5 and len(title_n) >= 5:
                    if ep_n in title_n or title_n in ep_n:
                        matched = num
                        break
            if matched:
                break
        if matched and matched not in used_eps:
            assignments[fn] = matched
            used_eps.add(matched)

    # PASS 2: Positions-Fallback für ungematchte (nächste freie Nummer)
    total = len(candidates)
    available = [i for i in range(1, total + 5) if i not in used_eps]
    avail_idx = 0
    for fn, ep_title, info in candidates:
        if fn not in assignments:
            if avail_idx < len(available):
                ep_num = available[avail_idx]
                avail_idx += 1
                assignments[fn] = ep_num
                used_eps.add(ep_num)

    return assignments


def download_season_episode_artwork(
        safe_name,         # Sicherer Serienname (bereits bereinigt)
        filename,          # Originaler Dateiname (für S##E## Extraktion)
        episode_title,     # Episodentitel (aus Dateiname, für Title-Matching)
        mtype,             # 'tv' oder 'movie'
        lang,              # Sprache z.B. 'de-DE'
        year,              # Erscheinungsjahr der Serie (kann None sein)
        emc_poster,        # Pfad zum poster-Ordner
        emc_backdrop,      # Pfad zum backdrop-Ordner
        tmdb_key,          # TMDb API Key
        tvdb_key,          # TVDb Key (UUID v4 oder Legacy)
        tvdb_legacy_key,   # TVDb Legacy 32-hex Key
        requests_mod,      # requests Modul
        download_fn,       # self._download_image(url, path) Funktion
        tvdb4_get_fn=None,           # tvdb4_get Funktion (optional)
        tvdb4_ensure_token_fn=None,  # tvdb4_ensure_token (optional)
        get_tvdb_pin_fn=None,        # get_tvdb_pin (optional)
        is_tvdb_uuid_fn=None,        # _is_tvdb_uuid_key (optional)
        is_tvdb_hex32_fn=None,       # _is_tvdb_hex32_key (optional)
        tvdb_legacy_get_series_id_fn=None,  # _tvdb_legacy_get_series_id (optional)
        only_missing=True,
        ep_index_override=None,      # Überschreibt Episode-Nr. (Folder-Resolver)
):
    """
    Lädt Staffel-Poster und Episode-Stills für eine Serieinepisode.

    Gibt zurück:
        dict mit:
          'season_poster': True/False
          'episode_still': True/False
          'season': int|None
          'episode': int|None
    """
    result = {'season_poster': False, 'episode_still': False,
              'season': None, 'episode': None}

    if mtype != 'tv':
        return result
    if not requests_mod:
        return result

    # ---- Staffel/Episode aus Dateiname extrahieren ----
    season, episode = parse_season_episode(filename)
    result['season']  = season
    result['episode'] = episode

    # ---- Ziel-Pfade ----
    season_poster_path  = None
    episode_still_path  = None

    if season is not None:
        sp_name = make_season_safe_name(safe_name, season)
        season_poster_path = os.path.join(emc_poster, '%s.jpg' % sp_name)

    # ep_index_override: überschreibt Episode-Nummer aus Dateinamen
    # (wird vom Folder-Resolver für "Serie-EpTitle" Format gesetzt)
    if ep_index_override is not None and season is None:
        # Format "Serie-EpTitle": Staffel 1, Episode aus Folder-Resolver
        season  = 1
        episode = ep_index_override
        result['season']  = season
        result['episode'] = episode

    if season is not None and episode is not None:
        ep_name = make_episode_safe_name(safe_name, season, episode)
        episode_still_path = os.path.join(emc_backdrop, '%s.jpg' % ep_name)

    need_season_poster = (season_poster_path is not None and
                          (not only_missing or
                           not os.path.exists(season_poster_path) or
                           os.path.getsize(season_poster_path) == 0))

    need_episode_still = (episode_still_path is not None and
                          (not only_missing or
                           not os.path.exists(episode_still_path) or
                           os.path.getsize(episode_still_path) == 0))

    if not need_season_poster and not need_episode_still:
        # Bereits im Cache
        result['season_poster'] = (season_poster_path is not None and
                                   os.path.exists(season_poster_path))
        result['episode_still'] = (episode_still_path is not None and
                                   os.path.exists(episode_still_path))
        return result

    # ---- Episode-Titel für Title-Matching (kein S##E## im Dateinamen) ----
    ep_title_for_match = None
    if season is None and episode_title:
        ep_title_for_match = episode_title

    # ==================================================================
    # TMDb Pfad
    # ==================================================================
    if tmdb_key and (need_season_poster or need_episode_still):
        try:
            series_id = tmdb_get_series_id(safe_name, lang, year, tmdb_key, requests_mod)
            if series_id:
                # Episode per Titel suchen wenn kein S##E##
                ep_season, ep_num = season, episode
                if ep_title_for_match and ep_season is None:
                    ep_season, ep_num = tmdb_find_episode_by_title(
                        series_id, ep_title_for_match, lang, tmdb_key, requests_mod)
                    if ep_season is not None:
                        ep_name = make_episode_safe_name(safe_name, ep_season, ep_num)
                        episode_still_path = os.path.join(emc_backdrop, '%s.jpg' % ep_name)
                        sp_name = make_season_safe_name(safe_name, ep_season)
                        season_poster_path = os.path.join(emc_poster, '%s.jpg' % sp_name)
                        need_season_poster = not os.path.exists(season_poster_path)
                        need_episode_still = not os.path.exists(episode_still_path)
                        result['season']  = ep_season
                        result['episode'] = ep_num

                # Staffel-Poster
                if need_season_poster and ep_season is not None:
                    url = tmdb_get_season_poster(series_id, ep_season, lang, tmdb_key, requests_mod)
                    if url:
                        ok = download_fn(url, season_poster_path)
                        if ok:
                            result['season_poster'] = True
                            need_season_poster = False

                # Episode-Still
                if need_episode_still and ep_season is not None and ep_num is not None:
                    url = tmdb_get_episode_still(series_id, ep_season, ep_num, lang, tmdb_key, requests_mod)
                    if url:
                        ok = download_fn(url, episode_still_path)
                        if ok:
                            result['episode_still'] = True
                            need_episode_still = False
        except Exception:
            pass

    # ==================================================================
    # TVDb v4 Pfad (wenn UUID Key vorhanden und TMDb nicht erfolgreich)
    # ==================================================================
    if (need_season_poster or need_episode_still) and tvdb4_get_fn and is_tvdb_uuid_fn:
        try:
            if is_tvdb_uuid_fn(tvdb_key):
                series_id_v4 = tvdb4_get_series_id(
                    safe_name, tvdb_key, tvdb4_get_fn,
                    tvdb4_ensure_token_fn, get_tvdb_pin_fn)
                if series_id_v4:
                    ep_season2, ep_num2 = season, episode
                    if ep_title_for_match and ep_season2 is None:
                        ep_season2, ep_num2 = tvdb4_find_episode_by_title(
                            series_id_v4, ep_title_for_match, tvdb_key, tvdb4_get_fn)
                        if ep_season2 is not None:
                            sp_name = make_season_safe_name(safe_name, ep_season2)
                            ep_name = make_episode_safe_name(safe_name, ep_season2, ep_num2)
                            season_poster_path = os.path.join(emc_poster, '%s.jpg' % sp_name)
                            episode_still_path = os.path.join(emc_backdrop, '%s.jpg' % ep_name)
                            need_season_poster = not os.path.exists(season_poster_path)
                            need_episode_still = not os.path.exists(episode_still_path)

                    if need_season_poster and ep_season2 is not None:
                        url = tvdb4_get_season_poster(series_id_v4, ep_season2, tvdb_key, tvdb4_get_fn)
                        if url:
                            ok = download_fn(url, season_poster_path)
                            if ok:
                                result['season_poster'] = True
                                need_season_poster = False

                    if need_episode_still and ep_season2 is not None and ep_num2 is not None:
                        url = tvdb4_get_episode_still(series_id_v4, ep_season2, ep_num2, tvdb_key, tvdb4_get_fn)
                        if url:
                            ok = download_fn(url, episode_still_path)
                            if ok:
                                result['episode_still'] = True
                                need_episode_still = False
        except Exception:
            pass

    # ==================================================================
    # TVDb Legacy Pfad (Staffel-Poster via banners.xml)
    # ==================================================================
    if need_season_poster and tvdb_legacy_key and is_tvdb_hex32_fn and tvdb_legacy_get_series_id_fn:
        try:
            if is_tvdb_hex32_fn(tvdb_legacy_key):
                ep_season3 = season if season is not None else result.get('season')
                if ep_season3 is not None:
                    sid_legacy = (tvdb_legacy_get_series_id_fn(safe_name, 'de') or
                                  tvdb_legacy_get_series_id_fn(safe_name, 'en'))
                    if sid_legacy:
                        url = tvdb_legacy_get_season_poster(
                            sid_legacy, ep_season3, tvdb_legacy_key, requests_mod)
                        if url:
                            ok = download_fn(url, season_poster_path)
                            if ok:
                                result['season_poster'] = True
        except Exception:
            pass

    return result


_tvdb4_token = None
_tvdb4_token_ts = 0

def tvdb4_ensure_token(apikey, pin=None):
	global _tvdb4_token, _tvdb4_token_ts
	if not apikey:
		return None
	if _tvdb4_token and (time.time() - _tvdb4_token_ts) < (25 * 24 * 3600):
		return _tvdb4_token
	try:
		r = requests.post(TVDB4_BASE + '/login', json={'apikey': apikey} if not pin else {'apikey': apikey, 'pin': pin}, timeout=10)
		if r.status_code == 200:
			data = r.json().get('data') or {}
			tok = data.get('token')
			if tok:
				_tvdb4_token = tok
				_tvdb4_token_ts = time.time()
				return _tvdb4_token
	except Exception:
		return None
	return None

def tvdb4_get(path, params=None):
	headers = {}
	if _tvdb4_token:
		headers['Authorization'] = 'Bearer ' + _tvdb4_token
	try:
		r = requests.get(TVDB4_BASE + path, params=params or {}, headers=headers, timeout=12)
		if r.status_code == 200:
			return r.json()
	except Exception:
		return None
	return None


# ===== Advanced Cleanup =====
class MovieScannerCleanupAdvanced(Screen, ConfigListScreen):
	"""
	Vereinfachte Cache-Verwaltung (BLAU) für MovieScanner:
	- EMC Limit (GB Preset)
	- Automatische Bereinigung aktivieren
	- Bereinigung: Cache nur für vorhandene Aufnahmen behalten (Poster/Backdrop/Banner/Infos)
	"""

	skin = """
    <screen name="MovieScannerCleanupAdvanced" position="center,center" size="1160,860" title="GradientFHD – MovieScan-Verwaltung" backgroundColor="transparent" flags="wfNoBorder">
        <widget source="Title" render="Label" position="20,0" size="1060,60" font="Italic; 42" halign="left" valign="center" transparent="1" foregroundColor="gradient_foreground_selection" backgroundColor="gradient_background" textBorderColor="black" textBorderWidth="1" zPosition="1" />
        <widget name="config" position="30,90" size="1100,450" itemHeight="45" font="Gradient_Font;30" backgroundColor="gradient_background" scrollbarMode="showOnDemand" transparent="1" />
        <widget name="hint" position="30,570" size="1100,130" font="Gradient_Font;30" foregroundColor="gradient_foreground_selection" backgroundColor="gradient_background" transparent="1" />
        <widget name="status" position="30,720" size="1100,70" font="Gradient_Font; 30" foregroundColor="ButtonYellow" backgroundColor="gradient_background" transparent="1" />
        <eLabel name="menu_bg" position="0,60" size="1160,800" backgroundColor="gradient_BGO,gradient_BGM,gradient_BGU,vertical" zPosition="-8" />
        <eLabel name="title_bg" position="0,0" size="1160,70" backgroundColor="gradient_TBGL,gradient_BGO,gradient_BGU,horizontal" zPosition="-9" cornerRadius="12" />
        <eLabel name="title_line" position="0,60" size="1160,4" backgroundColor="gradient_background,gradient_BGLR,gradient_BGLM,horizontal" zPosition="10" />
        <eLabel name="Line_Menu" position="15,795" size="1130,2" backgroundColor="gradient_BGLR,gradient_BGLM,gradient_BGLR,horizontal" zPosition="10" />
        <eLabel name="Line_config" position="30,550" size="1100,2" backgroundColor="gradient_BGLR,gradient_BGLM,gradient_BGLR,horizontal" zPosition="10" />
        <ePixmap pixmap="buttons/key_red.png" position="20,815" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_green.png" position="300,815" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_yellow.png" position="580,815" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <ePixmap pixmap="buttons/key_blue.png" position="860,815" size="30,30" alphatest="blend" zPosition="10" transparent="1" />
        <widget name="key_red" position="60,810" size="220,40" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" valign="center" halign="left" transparent="1" />
        <widget name="key_green" position="340,810" size="220,40" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" valign="center" halign="left" transparent="1" />
        <widget name="key_yellow" position="620,810" size="220,40" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" valign="center" halign="left" transparent="1" />
        <widget name="key_blue" position="900,810" size="220,40" backgroundColor="ButtonBack" font="Gradient_Font;27" foregroundColor="ButtonText" valign="center" halign="left" transparent="1" />
</screen>
	"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.setTitle(_t("GradientFHD – MovieScan-Verwaltung", "GradientFHD – MovieScan-Management"))
		self['status'] = Label('')
		self['hint'] = Label('')
		self._setlbl('key_red', _t('Speichern', 'Save'))
		self._setlbl('key_green', _t('Bereinigen', 'Clean up'))
		self._setlbl('key_yellow', _t('Vorschau', 'Preview'))
		self._setlbl('key_blue', _t('Info', 'Info'))
		self._lst = []
		self["config"] = ConfigList(self._lst)
		ConfigListScreen.__init__(self, self._lst, session=session)

		self._worker = None
		self._last_preview = None

		self['actions'] = ActionMap(['GradientFHDAction', 'OkCancelActions', 'SetupActions', 'NavigationActions', 'ColorActions'], {
			'cancel': self._close_and_save,
			'red': self._close_and_save,
			'green': self.apply_cleanup,
			'yellow': self.preview_cleanup,
			'blue': self.show_info,
			'ok': lambda: None
		}, -1)

		self._hint_map = []
		self._rebuild()
		try:
			self['config'].onSelectionChanged.append(self._update_hint)
		except Exception:
			pass
		self._update_hint()

	def _setlbl(self, name, text):
		try:
			self[name] = Label(text)
		except Exception:
			pass

	def _close_and_save(self):
		try:
			for x in (self['config'].list or []):
				try:
					cfg = x[1] if len(x) > 1 else None
					if hasattr(cfg, 'save'):
						cfg.save()
				except Exception:
					pass
		except Exception:
			pass
		try:
			AS.auto_scan_enabled.save()
		except Exception:
			pass
		try:
			AS.auto_scan_time.save()
		except Exception:
			pass
		try:
			configfile.save()
		except Exception:
			pass
		try:
			schedule_cleanup_timer(self.session)
		except Exception:
			pass
		try:
			schedule_moviescanner_timer(self.session)
		except Exception:
			pass
		self.close()

	def _update_hint(self):
		idx = 0
		try:
			idx = self['config'].getCurrentIndex()
		except Exception:
			idx = 0
		try:
			text = self._hint_map[idx]
		except Exception:
			text = _t(
				"Cache-Verwaltung: Einstellungen für EMC-Cache, Bereinigung und MovieScanner-Automatik.",
				"Cache management: settings for EMC cache, cleanup and MovieScanner automation."
			)
		try:
			self['hint'].setText(text)
		except Exception:
			pass

	def _rebuild(self):
		lst = []
		hints = []

		lst.append(getConfigListEntry(_t('--- EMC Limit ---', '--- EMC Limit ---'), NoSave(ConfigNothing())))
		hints.append(_t(
			"EMC-Limit: Begrenzt die maximale Größe des EMC-Caches per GB-Vorgabe.",
			"EMC limit: Restricts the maximum EMC cache size using a GB preset."
		))
		lst.append(getConfigListEntry(_t('Max. EMC Cache (GB, Preset)', 'Max. EMC cache (GB preset)'), C.size_emc_gb_preset))
		hints.append(_t(
			"Legt fest, wie groß der EMC-Cache maximal werden darf.",
			"Defines how large the EMC cache is allowed to grow."
		))

		lst.append(getConfigListEntry(_t('--- Cover-Kopie ---', '--- Cover Copy ---'), NoSave(ConfigNothing())))
		hints.append(_t(
			"Cover-Kopie: Zusätzliche Ablage direkt neben der Aufnahme.",
			"Cover copy: Additional storage directly next to the recording."
		))
		lst.append(getConfigListEntry(_t('Poster zusätzlich als Cover neben Aufnahme (nur EMC Cache)', 'Also copy poster as cover next to recording (EMC cache only)'), config.plugins.GradientFHD.scanner.copyPosterToRecording))
		hints.append(_t(
			"Speichert das Poster zusätzlich als Coverdatei neben der Aufnahme im EMC-Bereich.",
			"Also stores the poster as a cover file next to the recording in the EMC area."
		))

		lst.append(getConfigListEntry(_t('--- Cache Bereinigung ---', '--- Cache Cleanup ---'), NoSave(ConfigNothing())))
		hints.append(_t(
			"Automatische Bereinigung des EMC-Caches nach Zeitplan.",
			"Automatic cleanup of the EMC cache on a schedule."
		))
		lst.append(getConfigListEntry(_t('Automatische Bereinigung aktivieren', 'Enable automatic cleanup'), C.auto_enabled))
		hints.append(_t(
			"Aktiviert oder deaktiviert die automatische Cache-Bereinigung.",
			"Enables or disables automatic cache cleanup."
		))
		lst.append(getConfigListEntry(_t('Uhrzeit (HH:MM) für zukünftige Terminplanung', 'Time (HH:MM) for scheduled cleanup'), C.auto_time))
		hints.append(_t(
			"Uhrzeit für die automatische Cache-Bereinigung.",
			"Time used for automatic cache cleanup."
		))

		lst.append(getConfigListEntry(_t('--- MovieScanner Automatik ---', '--- MovieScanner Automation ---'), NoSave(ConfigNothing())))
		hints.append(_t(
			"Automatischer MovieScanner-Suchlauf im Hintergrund.",
			"Automatic MovieScanner background scan."
		))
		lst.append(getConfigListEntry(_t('Automatischen MovieScanner aktivieren', 'Enable automatic MovieScanner'), AS.auto_scan_enabled))
		hints.append(_t(
			"Aktiviert oder deaktiviert den automatischen Suchlauf für Aufnahmen.",
			"Enables or disables the automatic scan for recordings."
		))
		lst.append(getConfigListEntry(_t('Uhrzeit (HH:MM) für automatischen Suchlauf', 'Time (HH:MM) for automatic scan'), AS.auto_scan_time))
		hints.append(_t(
			"Uhrzeit für den automatischen MovieScanner-Suchlauf.",
			"Time used for the automatic MovieScanner scan."
		))

		self._lst = lst
		self._hint_map = hints
		self["config"].list = lst
		try:
			self["config"].l.setList(lst)
		except Exception:
			pass
		self._update_hint()

	def show_info(self):
		txt = _t(
			"MovieScan-Verwaltung\n\n"
			"GREEN: Löscht Cache-Dateien (Poster/Backdrop/Banner/Infos), "
			"für die keine passende Aufnahme im gesamten Movie-Ordner gefunden wird.\n"
			"YELLOW: Vorschau (ohne Löschen) zeigt die Anzahl, die betroffen wäre.\n\n"
			"Hinweis: Zuordnung erfolgt wie im Scan über den bereinigten Titel (safe_name).",
			"This cache management is intentionally reduced.\n\n"
			"GREEN: Removes cache files (poster/backdrop/banner/infos) that have no matching recording "
			"in the full Movie folder.\n"
			"YELLOW: Preview (no deletion) shows how many files would be affected.\n\n"
			"Note: Matching works like the scan via the normalized title (safe_name)."
		)
		self.session.open(MessageBox, txt, MessageBox.TYPE_INFO, timeout=12)

	def _load_selected_movie_paths(self):
		# Persisted selection from main MovieScanner screen (JSON list or csv)
		sel = []
		try:
			raw = (config.plugins.GradientFHD.scanner.movie_paths.value or '').strip()
			if raw:
				if raw.startswith('['):
					sel = json.loads(raw)
				else:
					sel = [x.strip() for x in raw.split(',') if x.strip()]
		except Exception:
			sel = []
		# Sanitize
		out = []
		for p in sel:
			try:
				if p and os.path.isdir(p):
					out.append(p)
			except Exception:
				pass
		# Fallback: if nothing selected, use defaults from scan_start_points()
		if not out:
			try:
				for p in scan_start_points():
					if os.path.isdir(p):
						out.append(p)
			except Exception:
				pass
		return out

	def _collect_recording_safe_names(self, paths):
		keep = set()
		VIDEO_EXTS = ('.ts', '.mkv', '.mp4', '.avi', '.mov', '.m2ts', '.mpg', '.mpeg', '.wmv', '.iso')
		for base in paths:
			for root, _dirs, files in os.walk(base):
				# skip hidden
				try:
					_dirs[:] = [d for d in _dirs if not d.startswith('.')]
				except Exception:
					pass
				for fn in files:
					lfn = fn.lower()
					if not lfn.endswith(VIDEO_EXTS):
						continue
					fp = os.path.join(root, fn)
					try:
						title_guess, _year = clean_title_from_filename(fn, fullpath=fp)
						mtype = detect_media_type(fp + ' ' + os.path.dirname(fp), title_hint=title_guess, fullpath=fp)
						title_key = title_guess
						if mtype == 'tv':
							_norm = _normalize_emc_title(title_guess, os.path.splitext(os.path.basename(fp))[0])
							if _norm:
								title_key = _norm
						safe_name = make_safe_cache_name(title_key, fallback_stem=os.path.splitext(fn)[0])
						if not safe_name:
							safe_name = os.path.splitext(fn)[0].strip()
						if safe_name:
							keep.add(safe_name)
					except Exception:
						pass
		return keep

	def _collect_cache_items(self):
		# returns list of tuples (path, stem, kind)
		items = []
		for kind, folder, ext in (
			('poster', EMC_POSTER, '.jpg'),
			('backdrop', EMC_BACKDROP, '.jpg'),
			('banner', EMC_BANNER, '.jpg'),
			('infos', EMC_INFOS, '.json'),
		):
			try:
				if not os.path.isdir(folder):
					continue
				for fn in os.listdir(folder):
					if not fn.lower().endswith(ext):
						continue
					stem = os.path.splitext(fn)[0]
					items.append((os.path.join(folder, fn), stem, kind))
			except Exception:
				pass
		return items

	def _cleanup_orphan_cache(self, do_delete=False):
		# Use selected/discovered scan paths for matching so NAS/autofs recordings
		# are considered as well.
		paths = self._load_selected_movie_paths()
		if not paths:
			# legacy fallback
			try:
				if os.path.isdir(DEFAULT_HDD_MOVIE):
					paths = [DEFAULT_HDD_MOVIE]
			except Exception:
				paths = []
		# dedupe
		_u = []
		_s = set()
		for p in (paths or []):
			try:
				np = _norm_real_path(p)
				if np in _s:
					continue
				_s.add(np)
				_u.append(p)
			except Exception:
				pass
		paths = _u

		keep = self._collect_recording_safe_names(paths)
		cache_items = self._collect_cache_items()

		to_act = []
		for fpath, stem, kind in cache_items:
			# keep only if there is at least one recording with same safe_name
			if keep and stem in keep:
				continue
			# if there are NO recordings at all => everything becomes orphan (user request)
			if not keep:
				to_act.append((fpath, stem, kind))
			else:
				to_act.append((fpath, stem, kind))

		stats = {'keep_names': len(keep), 'cache_total': len(cache_items), 'orphan': len(to_act),
				 'del_poster': 0, 'del_backdrop': 0, 'del_banner': 0, 'del_infos': 0, 'errors': 0}
		if do_delete:
			for fpath, _stem, kind in to_act:
				try:
					os.remove(fpath)
					stats['del_%s' % kind] = stats.get('del_%s' % kind, 0) + 1
				except Exception:
					stats['errors'] += 1
		return stats

	def _run_worker(self, do_delete):
		from twisted.internet.reactor import callFromThread
		def ui(txt):
			try: self['status'].setText(txt)
			except Exception: pass

		try:
			callFromThread(ui, _t("Scanne Movie-Ordner nach Aufnahmen…", "Scanning Movie folder for recordings…"))
			stats = self._cleanup_orphan_cache(do_delete=do_delete)
			self._last_preview = stats

			if do_delete:
				callFromThread(ui, _t("Fertig   Entfernt: Poster %(p)d / Backdrop %(b)d / Banner %(ba)d / Info-JSON %(i)d  Fehler: %(e)d", "Done   Removed: Posters %(p)d / Backdrops %(b)d / Banners %(ba)d / Info JSON %(i)d  Errors: %(e)d") % {
					'p': stats.get('del_poster', 0),
					'b': stats.get('del_backdrop', 0),
					'ba': stats.get('del_banner', 0),
					'i': stats.get('del_infos', 0),
					'e': stats.get('errors', 0),
				})
			else:
				callFromThread(ui, _t("Vorschau: %(o)d Cache-Dateien wären betroffen (Aufnahmen gefunden: %(k)d)", "Preview: %(o)d cache files would be affected (recordings found: %(k)d)") % {
					'o': stats.get('orphan', 0), 'k': stats.get('keep_names', 0)
				})
		except Exception:
			callFromThread(ui, _t("Fehler bei der Bereinigung.", "Cleanup failed."))
		finally:
			self._worker = None

	def preview_cleanup(self):
		if self._worker:
			return
		self['status'].setText(_t("Vorschau läuft…", "Preview running…"))
		self._worker = threading.Thread(target=self._run_worker, args=(False,), daemon=True)
		self._worker.start()

	def apply_cleanup(self):
		if self._worker:
			return

		def _go(ans):
			if not ans:
				return
			self['status'].setText(_t("Bereinigung läuft…", "Cleanup running…"))
			self._worker = threading.Thread(target=self._run_worker, args=(True,), daemon=True)
			self._worker.start()

		# Confirmation (dangerous operation)
		self.session.openWithCallback(
			_go,
			MessageBox,
			_t("Bereinigung starten?\n\nEs werden Cache-Dateien im EMC-Ordner gelöscht, die keiner vorhandenen Aufnahme im gesamten Movie-Ordner zugeordnet werden können.", "Start cleanup?\n\nCache files in the EMC folder will be deleted if they cannot be matched to an existing recording in the full Movie folder."),
			MessageBox.TYPE_YESNO
		)

class MovieScannerCleanupTimer(Screen, ConfigListScreen):
#	skin = """
# genau hier muß der richtige Skin rein
#	"""
	skinName = "MovieScannerCleanupTimer"

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.setTitle(_t("GradientFHD – MovieScanner Automatik", "GradientFHD – MovieScanner Automation"))

		self['status'] = Label('')
		self._setlbl('key_red', _t('Schließen', 'Close'))
		self._setlbl('key_green', _t('Speichern', 'Save'))

		self._lst = []
		self["config"] = ConfigList(self._lst)
		ConfigListScreen.__init__(self, self._lst, session=session)

		self['actions'] = ActionMap(['GradientFHDAction', 'OkCancelActions', 'SetupActions', 'NavigationActions'], {
			'cancel': self._close_and_save,
			'red': self._close_and_save,
			'green': self._close_and_save,
			'ok': self._close_and_save
		}, -1)

		self._rebuild()

	def _setlbl(self, name, text):
		try:
			self[name] = Label(text)
		except Exception:
			pass

	def _close_and_save(self):
		try: configfile.save()
		except Exception: pass
		try:
			self['status'].setText(_('Gespeichert. (Ausführung bei Session-Start via Autostart)'))
		except Exception:
			pass
		self.close()

	def _rebuild(self):
		lst = []
		lst.append(getConfigListEntry(_t('Automatischen MovieScanner aktivieren', 'Enable automatic MovieScanner'), AS.auto_scan_enabled))
		lst.append(getConfigListEntry(_t('Uhrzeit (HH:MM) für automatischen Suchlauf', 'Time (HH:MM) for automatic scan'), AS.auto_scan_time))
		lst.append(getConfigListEntry(_t('Hinweis: Einstellungen werden sofort gespeichert und zusätzlich beim GUI-Start neu eingeplant.', 'Note: settings are saved immediately and also re-scheduled on GUI start.'), NoSave(ConfigNothing())))
		lst.append(getConfigListEntry(_t('Nur mit gespeicherten Ordnern aus dem MovieScanner.', 'Only uses saved folders from MovieScanner.'), NoSave(ConfigNothing())))
		lst.append(getConfigListEntry(_t('ROT speichert die Einstellungen.', 'RED saves the settings.'), NoSave(ConfigNothing())))
		try:
			self['config'].list = lst
			self['config'].l.setList(lst)
		except Exception:
			pass


# Interne Helfer für Cleanup
def _area_paths():
	tv_base = get_tv_cache_base()
	tv = {
		'poster': os.path.join(tv_base, 'poster'),
		'backdrop': os.path.join(tv_base, 'backdrop'),
		'banner': os.path.join(tv_base, 'banner'),
		'infos': os.path.join(tv_base, 'infos'),
	}
	emc = {
		'poster': EMC_POSTER,
		'backdrop': EMC_BACKDROP,
		'banner': EMC_BANNER,
		'infos': EMC_INFOS,
	}
	return tv, emc

def _iter_files(base):
	if not os.path.isdir(base):
		return
	for root, dirs, files in os.walk(base):
		for f in files:
			yield os.path.join(root, f)

def _collect_cache_info():
	info = {'tv': {}, 'emc': {}}
	tv, emc = _area_paths()
	for seg_name, seg in (('tv', tv), ('emc', emc)):
		for area, path in seg.items():
			cnt = 0
			sz = 0
			try:
				for fp in _iter_files(path):
					cnt += 1
					try:
						sz += os.path.getsize(fp)
					except Exception:
						pass
			except Exception:
				pass
			info[seg_name][area] = (cnt, sz)
	return info

def build_info_text_emc():
	"""Info popup for MovieScanner (EMC only)."""
	info = _collect_cache_info()
	def line(a):
		(cnt, sz) = info['emc'][a]
		return 'EMC %s: %d (~%.1f MB)' % (a, cnt, bytes_to_mb(sz))
	emc_total = bytes_to_mb(sum(sz for (_, sz) in info['emc'].values()))
	lines = [
		'EMC gesamt: ~{:.1f} MB'.format(emc_total),
		line('poster'), line('backdrop'), line('banner'), line('infos'),
	]
	return '\n'.join(lines)

def build_debug_paths_text(selected_paths=None):
	"""Debug popup: zeigt ausgewählte Pfade + Scan-Startpunkte."""
	try:
		selected_paths = selected_paths or []
	except Exception:
		selected_paths = []

	out = []
	out.append("Pfade (Debug):")

	if selected_paths:
		out.append("Ausgewählt:")
		for sp in selected_paths:
			out.append("  - %s" % sp)
	else:
		out.append("Ausgewählt: (keine)")

	try:
		avail = scan_start_points()
		if avail:
			out.append("")
			out.append("Scan-Startpunkte:")
			for ap in avail:
				out.append("  - %s" % ap)
	except Exception as e:
		out.append("")
		out.append("Scan-Startpunkte: (Fehler: %s)" % e)

	return "\n".join(out)
def build_info_text():
	info = _collect_cache_info()
	def line(seg, a):
		(cnt, sz) = info[seg][a]
		return '%s %s: %d (~%.1f MB)' % (seg.upper(), a, cnt, bytes_to_mb(sz))
	tv_total = bytes_to_mb(sum(sz for (_, sz) in info['tv'].values()))
	emc_total = bytes_to_mb(sum(sz for (_, sz) in info['emc'].values()))
	lines = [
		'TV gesamt: ~{:.1f} MB'.format(tv_total),
		line('tv', 'poster'), line('tv', 'backdrop'), line('tv', 'banner'), line('tv', 'infos'),
		'',
		'EMC gesamt: ~{:.1f} MB'.format(emc_total),
		line('emc', 'poster'), line('emc', 'backdrop'), line('emc', 'banner'), line('emc', 'infos'),
	]
	return '\n'.join(lines)


def _load_saved_paths_from_config():
	"""Read persisted scanner.movie_paths config (json-list or csv)."""
	out = []
	try:
		raw = (config.plugins.GradientFHD.scanner.movie_paths.value or '').strip()
		if raw:
			if raw.startswith('['):
				vals = json.loads(raw)
			else:
				vals = [x.strip() for x in raw.split(',') if x.strip()]
			for p in (vals or []):
				try:
					if p and os.path.isdir(p):
						out.append(p)
				except Exception:
					pass
	except Exception:
		pass
	return out

def _retention_days_value(sel):
	v = sel.value
	if v == 'never':
		return None
	try:
		return int(v)
	except Exception:
		return None

def _build_candidates_for_segment(seg_name):
	tv, emc = _area_paths()
	seg = tv if seg_name == 'tv' else emc
	include = {
		'poster': getattr(C, 'include_%s_poster' % seg_name).value,
		'backdrop': getattr(C, 'include_%s_backdrop' % seg_name).value,
		'banner': getattr(C, 'include_%s_banner' % seg_name).value,
		'infos': getattr(C, 'include_%s_infos' % seg_name).value,
	}
	days_sel = {
		'poster': getattr(C, 'ret_%s_poster' % seg_name),
		'backdrop': getattr(C, 'ret_%s_backdrop' % seg_name),
		'banner': getattr(C, 'ret_%s_banner' % seg_name),
		'infos': getattr(C, 'ret_%s_infos' % seg_name),
	}
	min_age_hours = int(C.min_age_hours.value or 0)
	min_age_cutoff = time.time() - min_age_hours * 3600

	candidates = { 'poster': [], 'backdrop': [], 'banner': [], 'infos': [] }
	for area in ('poster', 'backdrop', 'banner', 'infos'):
		if not include.get(area, False):
			continue
		path = seg[area]
		days = _retention_days_value(days_sel[area])
		if days is None:
			continue
		cutoff = time.time() - days * 86400
		for fp in _iter_files(path):
			try:
				mtime = os.path.getmtime(fp)
				if mtime < cutoff and mtime < min_age_cutoff:
					candidates[area].append((mtime, fp))
			except Exception:
				pass
	return candidates

def _apply_keep_min(candidates):
	if not C.keep_min_enable.value:
		return candidates
	out = {k: list(v) for (k, v) in candidates.items()}
	for area, n_cfg in (('poster', C.keep_min_poster), ('backdrop', C.keep_min_backdrop), ('banner', C.keep_min_banner)):
		n = int(n_cfg.value or 0)
		if n <= 0:
			continue
		files = out.get(area, [])
		files.sort(key=lambda t: t[0], reverse=True)  # neueste zuerst behalten
		keep = set(fp for (_, fp) in files[:n])
		out[area] = [(mt, fp) for (mt, fp) in files if fp not in keep]
	return out

def _delete_files(file_list):
	removed = 0
	freed = 0
	for fp in file_list:
		try:
			sz = os.path.getsize(fp)
		except Exception:
			sz = 0
		try:
			os.remove(fp)
			removed += 1
			freed += sz
		except Exception:
			pass
	return (removed, freed)

def _segment_total_size(seg_name, active_areas=None):
	tv, emc = _area_paths()
	seg = tv if seg_name == 'tv' else emc
	total = 0
	files = []
	for area, path in seg.items():
		if active_areas and (area not in active_areas):
			continue
		for fp in _iter_files(path):
			files.append(fp)
			try:
				total += os.path.getsize(fp)
			except Exception:
				pass
	return (files, total)

def _enforce_size_limit(seg_name, limit_bytes):
	if limit_bytes <= 0:
		return (0, 0)
	active = []
	include = {
		'poster': getattr(C, 'include_%s_poster' % seg_name).value,
		'backdrop': getattr(C, 'include_%s_backdrop' % seg_name).value,
		'banner': getattr(C, 'include_%s_banner' % seg_name).value,
		'infos': getattr(C, 'include_%s_infos' % seg_name).value,
	}
	for area in ('poster', 'backdrop', 'banner', 'infos'):
		if include.get(area, False):
			active.append(area)
	(files, total) = _segment_total_size(seg_name, active_areas=active)
	if total <= limit_bytes:
		return (0, 0)

	min_age_hours = int(C.min_age_hours.value or 0)
	min_age_cutoff = time.time() - min_age_hours * 3600

	keep_set = set()
	if C.keep_min_enable.value:
		tv, emc = _area_paths()
		seg_paths = tv if seg_name == 'tv' else emc
		for area, n_cfg in (('poster', C.keep_min_poster), ('backdrop', C.keep_min_backdrop), ('banner', C.keep_min_banner)):
			n = int(n_cfg.value or 0)
			if n <= 0:
				continue
			area_files = []
			base = seg_paths[area]
			for fp in _iter_files(base):
				try:
					mt = os.path.getmtime(fp)
				except Exception:
					mt = 0
				area_files.append((mt, fp))
			area_files.sort(key=lambda t: t[0], reverse=True)
			keep_set.update(fp for (_, fp) in area_files[:n])

	cands = []
	for fp in files:
		try:
			mt = os.path.getmtime(fp)
		except Exception:
			mt = 0
		if fp in keep_set:
			continue
		if mt >= min_age_cutoff:
			continue
		cands.append((mt, fp))
	if not cands:
		return (0, 0)
	cands.sort(key=lambda t: t[0])  # älteste zuerst
	removed = 0
	freed = 0
	for (mt, fp) in cands:
		if total <= limit_bytes:
			break
		try:
			sz = os.path.getsize(fp)
		except Exception:
			sz = 0
		try:
			os.remove(fp)
			total -= sz
			removed += 1
			freed += sz
		except Exception:
			pass
	return (removed, freed)

def _run_cleanup_headless(write_report=False):
	ensure_dirs()
	report_lines = []
	sum_removed = 0
	sum_freed = 0

	for seg_name in ('tv', 'emc'):
		candidates = _build_candidates_for_segment(seg_name)
		candidates = _apply_keep_min(candidates)
		to_delete = []
		for area, lst in candidates.items():
			for (_, fp) in lst:
				to_delete.append(fp)
		(r1, f1) = _delete_files(to_delete)
		sum_removed += r1
		sum_freed += f1
		if write_report:
			report_lines.append('%s: by age -> removed %d (~%.1f MB)' % (seg_name.upper(), r1, bytes_to_mb(f1)))

		limit = _limit_bytes(C.size_tv_gb_preset if seg_name == 'tv' else C.size_emc_gb_preset)
		(r2, f2) = _enforce_size_limit(seg_name, limit)
		sum_removed += r2
		sum_freed += f2
		if write_report:
			report_lines.append('%s: by size -> removed %d (~%.1f MB)' % (seg_name.upper(), r2, bytes_to_mb(f2)))

	if write_report:
		try:
			with open(CLEANUP_REPORT, 'w') as f:
				f.write('GradientFHD Advanced Cleanup Report\n')
				f.write('\n'.join(report_lines))
		except Exception:
			pass
	return (sum_removed, sum_freed)


# Exponiert für Timer/Autostart
def run_scheduled_cleanup_headless():
	ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	(removed, freed) = _run_cleanup_headless(write_report=True)
	try:
		with open(SCHED_LOG, 'w') as f:
			f.write('[%s] scheduled cleanup: removed=%d freed=%.1f MB\n' % (ts, removed, bytes_to_mb(freed)))
	except Exception:
		pass
	return (removed, freed)

# Scheduler (wird von plugin.py aufgerufen)
_cleanup_timer = None
def schedule_cleanup_timer(session):
	global _cleanup_timer
	try:
		if _cleanup_timer is not None:
			try: _cleanup_timer.stop()
			except Exception: pass
			_cleanup_timer = None
		if not C.auto_enabled.value:
			return
		(hh, mm) = C.auto_time.value
		now = datetime.now()
		run_at = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
		if run_at <= now:
			run_at = run_at + timedelta(days=1)
		delta = max(1, int((run_at - now).total_seconds()) * 1000)  # ms
		_cleanup_timer = eTimer()
		def _cb():
			try:
				run_scheduled_cleanup_headless()
			except Exception:
				pass
			try:
				schedule_cleanup_timer(session)  # täglich neu
			except Exception:
				pass
		_cleanup_timer.callback.append(_cb)
		_cleanup_timer.start(delta, True)
		try:
			with open(SCHED_LOG, 'w') as f:
				pass
		except Exception:
			pass
	except Exception:
		pass

def _load_saved_movie_paths():
	res = []
	try:
		raw = (config.plugins.GradientFHD.scanner.movie_paths.value or '').strip()
	except Exception:
		raw = ''
	if not raw:
		return res
	try:
		if raw.startswith('['):
			vals = json.loads(raw)
		else:
			vals = [x.strip() for x in raw.split(',') if x.strip()]
	except Exception:
		vals = []
	seen = set()
	for p in vals:
		try:
			if isinstance(p, str) and p and os.path.isdir(p):
				np = _norm_real_path(p)
				if np in seen:
					continue
				seen.add(np)
				res.append(p)
		except Exception:
			pass
	return res

def _collect_movie_files_from_paths(sel):
	files = []
	for base in (sel or []):
		try:
			if _is_flat_movie_root(base):
				try:
					for f in os.listdir(base):
						fp = os.path.join(base, f)
						if os.path.isfile(fp) and f.lower().endswith(VIDEO_EXTS):
							files.append(fp)
				except Exception:
					pass
			else:
				for root, dirs, fls in os.walk(base):
					dirs[:] = [d for d in dirs if not is_excluded_dir(os.path.join(root, d))]
					for f in fls:
						if f.lower().endswith(VIDEO_EXTS):
							files.append(os.path.join(root, f))
		except Exception:
			pass
	return files

def run_scheduled_moviescan_headless(session):
	if session is None:
		return False
	if MOVIESCAN_WATCHER.running:
		return False
	sel = _load_saved_movie_paths()
	if not sel:
		try:
			with open(MOVIESCAN_SCHED_LOG, 'w') as f:
				f.write('[%s] scheduled moviescan skipped: no saved paths\n' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		except Exception:
			pass
		return False
	files = _collect_movie_files_from_paths(sel)
	if not files:
		try:
			with open(MOVIESCAN_SCHED_LOG, 'w') as f:
				f.write('[%s] scheduled moviescan skipped: no matching files\n' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		except Exception:
			pass
		return False
	ok = False
	try:
		ok = bool(MOVIESCAN_WATCHER.start_background(session, files, show_osd=True, scheduled=True))
	except Exception:
		ok = False
	try:
		with open(MOVIESCAN_SCHED_LOG, 'w') as f:
			f.write('[%s] scheduled moviescan: started=%s files=%d\n' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), str(bool(ok)), len(files)))
	except Exception:
		pass
	return ok

_moviescan_timer = None
def schedule_moviescanner_timer(session):
	global _moviescan_timer
	try:
		if _moviescan_timer is not None:
			try: _moviescan_timer.stop()
			except Exception: pass
			_moviescan_timer = None
		if not AS.auto_scan_enabled.value:
			return
		(hh, mm) = AS.auto_scan_time.value
		now = datetime.now()
		run_at = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
		if run_at <= now:
			run_at = run_at + timedelta(days=1)
		delta = max(1, int((run_at - now).total_seconds()) * 1000)  # ms
		_moviescan_timer = eTimer()
		def _cb():
			try:
				run_scheduled_moviescan_headless(session)
			except Exception:
				pass
			try:
				schedule_moviescanner_timer(session)  # täglich neu
			except Exception:
				pass
		_moviescan_timer.callback.append(_cb)
		_moviescan_timer.start(delta, True)

	except Exception:
		pass
