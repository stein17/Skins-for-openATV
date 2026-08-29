# -*- coding: utf-8 -*-
# 02.26 @stein17, Many new features and improvements
# GradientWQHD – EMC Banner Renderer (Cache-only)
#
# - Reads banners from: <storage>/xtra/EMC/banner/
# - Prefers TMDb-ID naming: tmdb_<id>_banner.jpg (or tmdb_<id>.jpg)
# - Falls back to title/filename slug: <slug>_banner.jpg / <slug>.jpg
#
# Usage in skin.xml (examples):
#   <widget source="Service" render="GradientBannerXEMC" position="30,520" size="685,120" zPosition="3" alphatest="blend" />
#   <widget source="session.CurrentService" render="GradientBannerXEMC" position="100,780" size="800,140" zPosition="4" alphatest="blend" />
#
from __future__ import absolute_import, print_function

import os
import re
import json
import unicodedata

from Components.Renderer.Renderer import Renderer
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.CurrentService import CurrentService
from Components.config import config
try:
	from Components.AVSwitch import AVSwitch
except Exception:
	AVSwitch = None
from enigma import ePixmap, loadJPG, ePicLoad, BT_SCALE, BT_KEEP_ASPECT_RATIO, BT_HALIGN_CENTER, BT_VALIGN_CENTER

DEBUG = False


def _get_emc_cache_base():
	"""Resolve EMC cache base path compatible with GradientMoviescanner."""
	try:
		base = config.plugins.GradientWQHD.posterXPath.value
		if base == "AUTO":
			for candidate in ("/media/hdd", "/media/usb", "/media/mmc"):
				if os.path.isdir(candidate):
					base = candidate
					break
			else:
				base = "/media/hdd"
	except Exception:
		base = "/media/hdd"
	return os.path.join(base, "xtra", "EMC")


EMC_BASE = _get_emc_cache_base()
BANNER_FOLDER = os.path.join(EMC_BASE, "banner")
INFO_FOLDER = os.path.join(EMC_BASE, "infos")

for _d in (EMC_BASE, BANNER_FOLDER, INFO_FOLDER):
	try:
		if not os.path.exists(_d):
			os.makedirs(_d, exist_ok=True)
	except Exception:
		pass

PATHS_LOG = "/tmp/GradientWQHD_paths.log"

def _log_active_paths_once():
	try:
		with open(PATHS_LOG, "a+", encoding="utf-8") as lf:
			lf.write("[%s] GradientBannerXEMC EMC_BASE=%s\n" % (__import__('time').strftime("%Y-%m-%d %H:%M:%S"), EMC_BASE))
	except Exception:
		pass

_log_active_paths_once()

# Keep module-level helper variable names stable (cleanup/no-op for linters)
del _d


def _debug(msg):
	if DEBUG:
		try:
			print("[GradientBannerXEMC]", msg)
		except Exception:
			pass


def clean_filename_for_search(s):
	"""
	Create a stable slug from a title/path segment.
	- ASCII-ish
	- lowercase
	- spaces -> underscores
	- remove punctuation
	"""
	try:
		if s is None:
			return ""
		if not isinstance(s, str):
			s = str(s)
		s = s.strip()
		s = unicodedata.normalize("NFKD", s)
		s = s.encode("ascii", "ignore").decode("ascii")
		s = s.lower()
		# remove common suffixes
		s = re.sub(r"\.(ts|mkv|mp4|avi|mov|mpg|mpeg|m2ts)$", "", s, flags=re.I)
		# keep alnum + spaces
		s = re.sub(r"[^a-z0-9\s_]+", " ", s)
		s = re.sub(r"\s+", " ", s).strip()
		s = s.replace(" ", "_")
		s = re.sub(r"_+", "_", s).strip("_")
		return s
	except Exception:
		return ""




def _normalize_emc_title(title, filename_stem=None):
	"""
	Normalize recording titles so a series uses ONE artwork set.
	Handles patterns like:
	  "Babylon Berlin - S02E06 - Episode 6" -> "Babylon Berlin"
	"""
	if not title:
		title = ""
	t = str(title).strip()
	t = re.sub(r'\s+', ' ', t)
	t = t.replace("_", " - ")
	t = re.sub(r'^\d{8}\s+\d{3,4}\s*-\s*[^-]+?\s*-\s*', '', t)

	t = re.sub(r'(?i)\bS\s*\d{1,2}\s*E\s*\d{1,3}\b', '', t)
	t = re.sub(r'(?i)\b\d{1,2}\s*x\s*\d{1,3}\b', '', t)
	t = re.sub(r'(?i)\bStaffel\s*\d{1,2}\b', '', t)
	t = re.sub(r'(?i)\bFolge\s*\d{1,3}\b', '', t)
	t = re.sub(r'(?i)\bEpisode\s*\d{1,3}\b', '', t)
	# Handle filenames like "<series>_6_<subtitle>" or titles like "<series> 6 <subtitle>"
	fs = (filename_stem or "")
	mfs = re.match(r'^(?P<series>.+?)_\d{1,3}_.+$', fs)
	if mfs:
		t = mfs.group('series').replace('_',' ').strip() or t
	mnum = re.match(r'^(?P<series>.+?)\s+(?P<num>\d{1,3})\s+(?P<rest>[^\d].+)$', t)
	if mnum:
		series = (mnum.group('series') or '').strip()
		num = int(mnum.group('num') or '0')
		if series and len(series) >= 6 and num >= 1 and num <= 300 and not re.search(r'\d$', series):
			if len(series.split()) >= 2:
				t = series


	parts = [p.strip() for p in t.split(" - ") if p.strip()]
	if len(parts) >= 2:
		def score(p):
			s = 0
			if any(ord(ch) > 127 for ch in p):
				s += 3
			if len(p) >= 6:
				s += 1
			if re.search(r'(?i)\b(episode|folge)\b', p):
				s -= 3
			return s
		best = max(parts, key=score)
		if score(best) > score(parts[0]):
			t = best
		else:
			t = parts[0]

	t = re.sub(r'\(\s*\)', '', t).strip()
	t = re.sub(r'[-:|]\s*$', '', t).strip()
	t = re.sub(r'\s{2,}', ' ', t).strip()

	if re.fullmatch(r'(?i)(episode|folge)\s*\d{1,3}', t) or len(t) < 3:
		if filename_stem:
			f = str(filename_stem)
			f = f.replace("_", " - ")
			f = re.sub(r'^\d{8}\s+\d{3,4}\s*-\s*[^-]+?\s*-\s*', '', f)
			f = re.sub(r'(?i)\bS\s*\d{1,2}\s*E\s*\d{1,3}\b', '', f)
			f = re.sub(r'(?i)\b\d{1,2}\s*x\s*\d{1,3}\b', '', f)
			f = re.sub(r'(?i)\bStaffel\s*\d{1,2}\b', '', f)
			f = re.sub(r'(?i)\bFolge\s*\d{1,3}\b', '', f)
			f = re.sub(r'(?i)\bEpisode\s*\d{1,3}\b', '', f)
			fparts = [p.strip() for p in f.split(" - ") if p.strip()]
			if fparts:
				t = fparts[0]
	return t


def _safe_name_keep_spaces(s):
	"""Remove only invalid filename chars, keep spaces/umlauts (must match MovieScanner)."""
	try:
		return re.sub(r'[\\/:"*?<>|]+', '', s or "").strip()
	except Exception:
		return ""


def _preferred_slug(safe_slug, tmdb_id):
	try:
		if tmdb_id and int(tmdb_id) > 0:
			return "tmdb_%d" % int(tmdb_id)
	except Exception:
		pass
	return safe_slug


def _read_tmdb_id(json_path):
	try:
		if json_path and os.path.exists(json_path):
			with open(json_path, "r", encoding="utf-8", errors="ignore") as f:
				data = json.load(f)
			# tolerate different keys
			for k in ("tmdb_id", "id", "tmdbId", "tmdb"):
				if k in data and data.get(k):
					return data.get(k)
	except Exception:
		pass
	return None


class GradientBannerXEMC(Renderer):
	GUI_WIDGET = ePixmap

	def __init__(self):
		Renderer.__init__(self)
		self._last_path = None
		self.picload = None
		self.picload_conn = None
		self._decode_path = None

	def postWidgetCreate(self, instance):
		Renderer.postWidgetCreate(self, instance)
		try:
			self.picload = ePicLoad()
			try:
				self.picload_conn = self.picload.PictureData.connect(self._onPicDecoded)
			except Exception:
				self.picload.PictureData.get().append(self._onPicDecoded)
		except Exception:
			self.picload = None

	def preWidgetRemove(self, instance):
		self._clear()
		try:
			Renderer.preWidgetRemove(self, instance)
		except Exception:
			pass

	def _getDecodeSize(self):
		w = h = 0
		try:
			sz = self.instance.size()
			w = sz.width()
			h = sz.height()
		except Exception:
			pass
		if w <= 0:
			w = 455
		if h <= 0:
			h = 84
		return int(w), int(h)

	def _startDecodeBanner(self, path):
		if not self.instance or not path or not os.path.exists(path):
			return False
		try:
			self._clear()
			self._decode_path = path
			if self.picload is None:
				self.picload = ePicLoad()
				try:
					self.picload_conn = self.picload.PictureData.connect(self._onPicDecoded)
				except Exception:
					self.picload.PictureData.get().append(self._onPicDecoded)
			width, height = self._getDecodeSize()
			sc = (1, 1)
			try:
				if AVSwitch is not None:
					sc = AVSwitch().getFramebufferScale()
			except Exception:
				pass
			try:
				self.picload.setPara((width, height, sc[0], sc[1], False, 1, '#00000000'))
			except Exception:
				self.picload.setPara([width, height, sc[0], sc[1], False, 1, '#00000000'])
			res = self.picload.startDecode(path)
			if res != 0:
				self._decode_path = None
				return False
			return True
		except Exception:
			self._decode_path = None
			return False

	def _onPicDecoded(self, picInfo=None):
		try:
			if not self.instance or not self.picload or not self._decode_path:
				return
			ptr = self.picload.getData()
			if ptr is None:
				return
			self.instance.setPixmap(ptr)
			try:
				self.instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
			except Exception:
				try:
					self.instance.setScale(1)
				except Exception:
					pass
			self.instance.show()
			self._last_path = self._decode_path
		except Exception:
			self._clear()
		finally:
			self._decode_path = None

	
	def changed(self, what):
		try:
			if self.instance is None:
				return

			# Handle clear
			try:
				if what and what[0] == self.CHANGED_CLEAR:
					self._clear()
					return
			except Exception:
				pass

			src = self.source
			if src is None:
				self._clear()
				return

			event = None
			ref = None
			path = None
			title = ""

			# Source can be ServiceEvent (list contexts) or CurrentService (player)
			if isinstance(src, ServiceEvent):
				event = getattr(src, 'event', None)
				ref = getattr(src, 'service', None)
				if event:
					try:
						title = event.getEventName() or ""
					except Exception:
						title = ""
			elif isinstance(src, CurrentService):
				ref = src.getCurrentServiceReference()
				if ref:
					try:
						title = ref.getName() or ""
					except Exception:
						title = ""
			else:
				self._clear()
				return

			if ref:
				try:
					path = ref.getPath()
				except Exception:
					path = None

			if not path:
				self._clear()
				return

			base = os.path.basename(path)
			stem = ""
			try:
				stem = os.path.splitext(base)[0]
			except Exception:
				stem = base

			# Prefer normalized recording title for cache match
			series_title = _normalize_emc_title(title or base, stem)
			series_safe_name = _safe_name_keep_spaces(series_title)
			series_safe_slug = clean_filename_for_search(series_title)
			safe_slug = clean_filename_for_search(base or title)

			# Read TMDb ID if available (helps if you also store tmdb_<id> files)
			tmdb_id = None
			for jp in (
				os.path.join(INFO_FOLDER, series_safe_name + '.json') if series_safe_name else '',
				os.path.join(INFO_FOLDER, series_safe_slug + '.json') if series_safe_slug else '',
				os.path.join(INFO_FOLDER, safe_slug + '.json') if safe_slug else '',
			):
				if jp:
					tmdb_id = _read_tmdb_id(jp)
					if tmdb_id:
						break

			pref = _preferred_slug(series_safe_slug or safe_slug, tmdb_id)

			# Direct candidate names (legacy + your EMC human filenames)
			candidates = []
			# tmdb-id naming (optional)
			candidates += [
				os.path.join(BANNER_FOLDER, pref + '_banner.jpg'),
				os.path.join(BANNER_FOLDER, pref + '.jpg'),
			]
			# MovieScanner safe_name
			if series_safe_name:
				candidates += [
					os.path.join(BANNER_FOLDER, series_safe_name + '_banner.jpg'),
					os.path.join(BANNER_FOLDER, series_safe_name + '.jpg'),
				]
			# slug
			if series_safe_slug:
				candidates += [
					os.path.join(BANNER_FOLDER, series_safe_slug + '_banner.jpg'),
					os.path.join(BANNER_FOLDER, series_safe_slug + '.jpg'),
				]
			if safe_slug and safe_slug != series_safe_slug:
				candidates += [
					os.path.join(BANNER_FOLDER, safe_slug + '_banner.jpg'),
					os.path.join(BANNER_FOLDER, safe_slug + '.jpg'),
				]

			found = None
			for cp in candidates:
				if cp and os.path.exists(cp):
					found = cp
					break

			# Robust cache-only match inside EMC banner folder
			if not found:
				titles = []
				for _t in (series_title, title, base, stem):
					if _t and _t not in titles:
						titles.append(_t)

				expanded = []
				for _t in titles:
					for v in _emc_expand_title_variants(_t):
						if v and v not in expanded:
							expanded.append(v)

				try:
					mapped = []
					for _t in list(expanded):
						mt = apply_title_mapping(_t)
						if mt and mt not in expanded and mt not in mapped:
							mapped.append(mt)
				except Exception:
					mapped = []
				expanded += mapped

				found = _emc_find_artwork(EMC_BANNER_FOLDER, expanded)

			if not found:
				self._clear()
				return

			if found == self._last_path:
				return

			if not self._startDecodeBanner(found):
				self._clear()
				return

		except Exception as e:
			_debug('changed() error: %s' % e)
			self._clear()

	def _clear(self):
		try:
			if self.instance:
				try:
					self.instance.setPixmap(None)
				except Exception:
					pass
				self.instance.hide()
		except Exception:
			pass
		self._last_path = None

# -----------------------------------------------------------------------------
# EMC Cache-only Artwork (Poster/Backdrop/Banner)
#   - show artwork ONLY from <storage>/xtra/EMC/{poster,backdrop,banner}
#   - NEVER download and NEVER write next to recordings
# -----------------------------------------------------------------------------

EMC_POSTER_FOLDER = os.path.join(EMC_BASE, "poster")
EMC_BACKDROP_FOLDER = os.path.join(EMC_BASE, "backdrop")
EMC_BANNER_FOLDER = os.path.join(EMC_BASE, "banner")

# folder index cache: {folder: {norm_key: fullpath}}
_EMC_INDEX = {}
_EMC_INDEX_MTIME = {}

def _emc_read_meta_title(media_path):
    """
    Enigma2 recording meta: <file>.ts.meta (or generally <file>.<ext>.meta)
    Title is usually on 2nd line.
    """
    try:
        meta_path = media_path + ".meta"
        if not os.path.exists(meta_path):
            return ""
        with open(meta_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.read().splitlines()
        if len(lines) >= 2:
            return (lines[1] or "").strip()
    except Exception:
        pass
    return ""

def _emc_extract_title_from_filename(path):
    try:
        base = os.path.basename(path)
        stem = os.path.splitext(base)[0]
        # common recording naming: "YYYYMMDD HHMM - CHANNEL - Title"
        if " - " in stem:
            stem = stem.split(" - ")[-1]
        stem = (stem or "").strip()
        # underscores are common in refs/titles -> treat like spaces
        stem = stem.replace("_", " ")
        stem = re.sub(r"\s+", " ", stem).strip()
        return stem
    except Exception:
        return ""


def _emc_expand_title_variants(title):
    """Generate robust title variants for cache matching (no manual per-title mapping)."""
    if not title:
        return []
    try:
        t = str(title).strip()
    except Exception:
        return []
    if not t:
        return []

    variants = []
    def add(x):
        if not x:
            return
        x = str(x).strip()
        if not x:
            return
        if x not in variants:
            variants.append(x)

    add(t)
    add(t.replace('_', ' '))
    add(re.sub(r"\s+", " ", t.replace('_', ' ')).strip())

    # Remove bracketed qualifiers: [Extended Cut], (Director's Cut), etc.
    t_nobr = re.sub(r"\[[^\]]+\]", " ", t)
    t_nobr = re.sub(r"\([^\)]*\)", " ", t_nobr)
    t_nobr = re.sub(r"\s+", " ", t_nobr).strip()
    add(t_nobr)

    # Split on common subtitle separators and add shorter base titles
    for sep in [" - ", " – ", " — ", ":", "|"]:
        if sep in t:
            base = t.split(sep, 1)[0].strip()
            add(base)
        if sep in t_nobr:
            base = t_nobr.split(sep, 1)[0].strip()
            add(base)

    # Remove common edition/quality tags
    tags_pat = r"\b(extended\s+cut|director.?s\s+cut|uncut|special\s+edition|remastered|ultimate\s+edition|\d{k}|uhd|hd)\b"
    t_notags = re.sub(tags_pat, " ", t_nobr, flags=re.IGNORECASE)
    t_notags = re.sub(r"\s+", " ", t_notags).strip()
    add(t_notags)

    return [v for v in variants if v]
def _emc_norm_key(s):
    """
    Normalize for matching:
      - case-insensitive
      - '_' treated as space
      - German umlauts normalized to ae/oe/ue and ß->ss
      - strip diacritics
      - keep a-z0-9 and spaces
    """
    if not s:
        return ""
    try:
        s = str(s).strip()
    except Exception:
        return ""
    if not s:
        return ""
    s = s.replace("\xc2\x86", "").replace("\xc2\x87", "")
    s = s.replace("Â\x86", "").replace("Â\x87", "")
    s = s.replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = s.casefold()
    # German transliterations (pre-diacritic stripping)
    s = s.replace("ß", "ss")
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    # strip remaining diacritics
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _emc_build_index(folder):
    try:
        mtime = os.path.getmtime(folder)
    except Exception:
        return {}
    if _EMC_INDEX_MTIME.get(folder) == mtime and folder in _EMC_INDEX:
        return _EMC_INDEX[folder]
    idx = {}
    try:
        for fn in os.listdir(folder):
            if not fn.lower().endswith(".jpg"):
                continue
            stem = os.path.splitext(fn)[0]
            key = _emc_norm_key(stem)
            if key and key not in idx:
                idx[key] = os.path.join(folder, fn)
    except Exception:
        idx = {}
    _EMC_INDEX[folder] = idx
    _EMC_INDEX_MTIME[folder] = mtime
    return idx

def _emc_find_artwork(folder, titles):
    """Return best matching jpg path from folder for any of titles (cache-only)."""
    idx = _emc_build_index(folder)
    if not idx:
        return None

    best = None
    best_score = 10**9

    def consider(p, score):
        nonlocal best, best_score
        try:
            if not p or not os.path.exists(p) or os.path.getsize(p) <= 0:
                return
        except Exception:
            return
        if score < best_score:
            best = p
            best_score = score

    # 0) exact key match
    for t in titles or []:
        k = _emc_norm_key(t)
        if not k:
            continue
        p = idx.get(k)
        if p:
            consider(p, 0)

    if best:
        return best

    # 1) prefix both ways (handles "Titel 001" and "Titel Extended Cut")
    for t in titles or []:
        k = _emc_norm_key(t)
        if not k:
            continue
        for kk, p in idx.items():
            if kk.startswith(k) or k.startswith(kk):
                # score by length delta to prefer closest
                consider(p, 100 + abs(len(kk) - len(k)))

    if best:
        return best

    # 2) contains both ways (last resort but still limited to same folder)
    for t in titles or []:
        k = _emc_norm_key(t)
        if not k:
            continue
        for kk, p in idx.items():
            if (k in kk) or (kk in k):
                consider(p, 200 + abs(len(kk) - len(k)))

    return best
    # exact match pass
    for t in titles or []:
        k = _emc_norm_key(t)
        if not k:
            continue
        p = idx.get(k)
        if p and os.path.exists(p) and os.path.getsize(p) > 0:
            return p

    # prefix fallback (e.g. "Titel 001")
    for t in titles or []:
        k = _emc_norm_key(t)
        if not k:
            continue
        for kk, p in idx.items():
            if kk.startswith(k) and os.path.exists(p) and os.path.getsize(p) > 0:
                return p

    return None

