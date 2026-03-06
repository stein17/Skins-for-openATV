"""
1. OPTIMIERTE GradientConverlibr.py
===================================

Zentrale Library fuer ALLE Gradient-Renderer

NEUE FEATURES:
- TITLE_MAPPINGS Integration
- apply_title_mapping() Funktion
- Alle Renderer profitieren automatisch!
- Python 2/3 kompatibel
"""
from __future__ import print_function
from re import sub, I, compile, DOTALL
from unicodedata import normalize
import sys

try:
    from six import text_type
except ImportError:
    text_type = type(u"")

PY3 = sys.version_info[0] >= 3
if PY3:
    import html as _html
    from urllib.parse import quote_plus
else:
    from HTMLParser import HTMLParser as _HTMLParser
    _html = _HTMLParser()
    from urllib import quote_plus
TITLE_MAPPINGS = {}

# -----------------------------------------------------------------------------
# Persistent title overrides (user editable)
# File: /media/hdd/xtra/custom/title_overrides.json
# Format:
#   {"prefix": {"planet weltweit -": "Planet Weltweit"}, "exact": {"foo": "bar"}}
# Built-in safe prefixes included for known problematic EPG titles.
# -----------------------------------------------------------------------------
_TITLE_OVERRIDES_LOADED = False
_TITLE_OVERRIDES = {"prefix": {}, "exact": {}}
_BUILTIN_PREFIX_OVERRIDES = {
    "planet weltweit": "Planet Weltweit",
    "container wars": "Container Wars",
    "storage hunters": "Storage Hunters",
    "axel! will's wissen": "Axel! will's wissen",
    "bad buddies": "Bad Buddies",
}

def _load_title_overrides():
    global _TITLE_OVERRIDES_LOADED, _TITLE_OVERRIDES
    if _TITLE_OVERRIDES_LOADED:
        return
    _TITLE_OVERRIDES_LOADED = True
    try:
        import os, json
        path = os.path.join(getPosterXBasePath(), "xtra", "custom", "title_overrides.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                p = data.get("prefix") or {}
                e = data.get("exact") or {}
                if isinstance(p, dict):
                    for k,v in p.items():
                        if k and v:
                            _TITLE_OVERRIDES["prefix"][str(k).lower().strip()] = str(v).strip()
                if isinstance(e, dict):
                    for k,v in e.items():
                        if k and v:
                            _TITLE_OVERRIDES["exact"][str(k).lower().strip()] = str(v).strip()
    except Exception:
        pass

def _apply_title_overrides(title):
    try:
        _load_title_overrides()
        t = (title or "").strip()
        if not t:
            return title
        key = t.lower().strip()
        m = _TITLE_OVERRIDES["exact"].get(key)
        if m:
            return m
        for pref,val in _TITLE_OVERRIDES["prefix"].items():
            if key.startswith(pref):
                return val
        for pref,val in _BUILTIN_PREFIX_OVERRIDES.items():
            if key.startswith(pref):
                return val
        return title
    except Exception:
        return title

def quoteEventName(eventName):
    try:
        text = eventName.decode('utf8').replace(u'\x86', u'').replace(u'\x87', u'').encode('utf8')
    except Exception:
        text = eventName
    return quote_plus(text, safe='+')
REGEX = compile('\\s\\*\\d{4}\\Z|[\\( \\[ ].*?[ \\) \\]]|[:!]|\\s-\\s.*', DOTALL)

def cutName(eventName=u''):
    if not eventName:
        return u''
    ev = _unicodify(eventName, norm='NFC')
    if ev.isdigit():
        return ev
    ev = ev.replace(u'&', u'e')
    if not ev[:2].isdigit() and not ev[:3].isdigit():
        ev = sub('^\\d{10}-', u'', ev)
    ev = sub('[:\\s]*\\( ?(:?odc\\.?\\s*\\d+|ep\\.?\\s*\\d+|episode\\.?\\s*\\d+) \\)?$', u'', ev, flags=I)
    ev = sub('(\\d+)[\\s-]*(\\d+)$', '\\1', ev)
    ev = sub('\\s*(\\d+|I{1,3}|IV|V|VI|VII|VIII|IX|X)$', u'', ev)
    terms_to_remove = [u'AXN', u'AXN Black', u'AXN White', u'Regina -', u'Live:', u'LIVE: ', u'Prima', u'programu', u'filter cine34', u'cine34', u'Episode', u'Ep', u'Top 10 - ']
    for term in terms_to_remove:
        ev = ev.replace(term, u'')
    for age in (u'18+', u'(18+)', u'16+', u'(16+)', u'12+', u'(12+)', u'7+', u'(7+)', u'6+', u'(6+)', u'0+', u'(0+)'):
        ev = ev.replace(age, u'')
    ev = ev.replace(u'+', u'')
    ev = sub('[:\\-]', u' ', ev)
    ev = sub('[^\\w\\s]', u' ', ev)
    ev = sub('\\s+', u' ', ev).strip()
    return ev



def _unicodify(s, encoding='utf-8', norm=None):
    if not isinstance(s, text_type):
        s = text_type(s, encoding, errors='ignore')
    if norm:
        s = normalize(norm, s)
    return s

def remove_accents(string):
    s = _unicodify(string, norm='NFD')
    return u''.join((ch for ch in s if not u'̀' <= ch <= u'ͯ'))

def apply_title_mapping(title):
    """Lightweight, non-destructive normalization.

    v17: No hardcoded title lists in the renderer.
    Only applies safe whitespace/encoding normalization.
    Real exceptions belong into /media/hdd/xtra/custom/title_overrides.json.
    """
    try:
        if title is None:
            return ""
        if not isinstance(title, text_type):
            try:
                title = text_type(title)
            except Exception:
                title = str(title)
        t = title.strip()
        # normalize unicode (NFKC) and collapse whitespace
        try:
            t = normalize("NFKC", t)
        except Exception:
            pass
        t = sub(r"\s+", " ", t).strip()
        # keep TITLE_MAPPINGS optional (user may fill it)
        key = t.lower()
        t = _apply_title_overrides(t)
        key = t.lower()
        mapped = TITLE_MAPPINGS.get(key)
        return mapped if mapped else t
    except Exception:
        return title or ""


def getCleanTitle(eventitle=u''):
    if not eventitle:
        return u''
    ev = _unicodify(eventitle)
    return ev.replace(u' ^`^s', u'').replace(u' ^`^y', u'')

def sanitize_filename(filename):
    if not filename:
        return u''
    fn = _unicodify(filename)
    fn = sub('[^\\w\\s-]', u'', fn)
    return fn.strip()

def convtext(text=u''):
    if not text:
        return u''
    t = _unicodify(text, norm='NFC')
    t = t.replace(u'\x86', u'').replace(u'\x87', u'')
    t = t.strip().lower()
    junk = [u'1080p', u'1080i', u'720p', u'hdtv', u'web-dl', u'webrip', u'webhdrip', u'webhdtv', u'bdrip', u'dvdrip', u'dvdscr', u'bluray', u'brrip', u'xvid', u'x264', u'h264', u'avc', u'dts', u'ac3', u'ac3d', u'ac3md', u'dd51', u'retail', u'unrated', u'uncut', u'complete', u'internal', u'repack', u'sync', u'line.dubbed', u'dubbed']
    for j in junk:
        t = t.replace(j, u'')
    # v2.2: Deutsche Umlaute VORHER ersetzen (ö→oe, nicht ö→o)
    t = t.replace('ö', 'oe').replace('Ö', 'Oe')
    t = t.replace('ä', 'ae').replace('Ä', 'Ae')
    t = t.replace('ü', 'ue').replace('Ü', 'Ue')
    t = t.replace('ß', 'ss')
    
    t = cutName(t)
    t = getCleanTitle(t)
    if t.endswith(u' the'):
        t = u'the ' + t[:-4]
    t = remove_accents(t)
    t = sub('[^\\w\\s]', u' ', t)
    t = sub('\\s+', u' ', t).strip()
    return t
if __name__ == '__main__':
    print('=' * 70)
    print('GradientConverlibr - OPTIMIERTE VERSION')
    print('=' * 70)
    print()
    print('NEUE FEATURES:')
    print('  - TITLE_MAPPINGS integriert (%d Eintraege)' % len(TITLE_MAPPINGS))
    print('  - SPORT_KEYWORDS integriert (%d Eintraege)' % len(SPORT_KEYWORDS))
    print('  - apply_title_mapping() Funktion')
    print('  - Profitiert ALLEN Gradient-Renderern!')
    print()
    print('TEST: apply_title_mapping()')
    print('-' * 70)
    test_titles = [u'gzsz', u'Tagesschau', u'heute-show', u'Champions League', u'Bundesliga', u'Tatort', u'Der Bergdoktor']
    for title in test_titles:
        mapped = apply_title_mapping(title)
        if title.lower() != mapped.lower():
            print("  '%s' -> '%s' [MAPPING!]" % (title, mapped))
        else:
            print("  '%s' (unveraendert)" % title)
    print()
    print('TEST: convtext()')
    print('-' * 70)
    test_convtext = [u'Tatort 2024-01-15', u'GZSZ Folge 1234', u'Der Bergdoktor S05E10', u'Sportschau Bundesliga']
    for t in test_convtext:
        result = convtext(t)
        print("  '%s' -> '%s'" % (t, result))
    print()
    print('=' * 70)

# ============================================================================
# v3.0 OPTIMIERUNGEN - Duplikat-Vermeidung
# ============================================================================
from re import sub, I

def normalize_title_for_filename(title):
    """Normalisiert Titel zu eindeutigem Dateinamen (keine Duplikate!)."""
    if not title:
        return ''
    
    title = str(title).lower().strip()
    # normalize ellipsis / trailing dots to prevent duplicate slugs
    title = title.replace('…', '...')
    title = sub(r'\.{3,}$', '', title).strip()
    
    # Umlaute RICHTIG ersetzen (ü->ue nicht ü->u!)
    replacements = [
        ('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'),
        ('Ä', 'Ae'), ('Ö', 'Oe'), ('Ü', 'Ue'),
        ('ß', 'ss'), ('é', 'e'), ('è', 'e'), ('á', 'a'),
        ('&', 'und'), ('@', 'at')
    ]
    for old, new in replacements:
        title = title.replace(old, new)
    
    # Sonderzeichen entfernen
    title = sub(r'[:\-–—_\.\,\!\?\'\"\(\)\[\]]', ' ', title)
    title = sub(r'\s+', ' ', title).strip().replace(' ', '_')
    title = sub(r'[^\w]', '', title)
    
    return title

def get_canonical_slug(title):
    """Gibt kanonischen Slug zurück - ERSETZT convtext() für Dateinamen!"""
    return normalize_title_for_filename(title)

def is_daily_series(title):
    """Erkennt Daily-Serien/Telenovelas."""
    daily = ['gzsz', 'unter uns', 'awz', 'sturm der liebe', 'rote rosen',
             'berlin tag nacht', 'barbara salesch', 'auf streife']
    norm = normalize_title_for_filename(title).replace('_', ' ')
    return any(d in norm for d in daily)

def get_search_variants(title):
    """Generiert mehrere Suchvarianten für bessere Treffer."""
    variants = [title] if title else []
    
    # Ohne Episode/Folge
    cleaned = sub(r'\s*-\s*Folge\s+\d+.*$', '', title, flags=I)
    cleaned = sub(r'\s*\(\d+\)\s*$', '', cleaned)
    if cleaned != title and cleaned:
        variants.append(cleaned.strip())
    
    # Haupttitel (vor " - " oder ": ")
    for sep in [' - ', ': ', ' – ']:
        if sep in title:
            base = title.split(sep)[0].strip()
            if base and base not in variants:
                variants.append(base)
            break
    
    return variants

def get_min_score_for_title(title):
    """Niedrigerer Score für Daily-Serien."""
    return 40 if is_daily_series(title) else 60

def check_for_existing_file(title, folder, ext='.jpg'):
    """Prüft ob Datei mit normalisiertem Namen bereits existiert."""
    import os
    slug = get_canonical_slug(title)
    if not slug:
        return False, None
    path = folder + '/' + slug + ext
    exists = os.path.exists(path)
    return exists, path

# Ende v3.0 Optimierungen
