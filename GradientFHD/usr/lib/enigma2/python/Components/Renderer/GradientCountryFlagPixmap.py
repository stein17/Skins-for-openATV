# -*- coding: utf-8 -*-
from Components.Renderer.Renderer import Renderer
from enigma import ePixmap
import os, unicodedata, re, glob

class GradientCountryFlagPixmap(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.basePath = '/usr/share/enigma2/skin_default/countries'
        self.missing = 'missing.png'
        self.scaled = True
        self.preferName = True
        self.fuzzy = False
        self._cache = {}
        self._last_value = None
        self._last_path = None

    def applySkin(self, desktop, parent):
        attribs = []
        for (attrib, value) in self.skinAttributes:
            if attrib == 'basePath':
                self.basePath = value.rstrip('/')
            elif attrib == 'missing':
                self.missing = value
            elif attrib in ('scaled', 'scale'):
                self.scaled = value in ('1', 'true', 'True', 'yes')
            elif attrib in ('preferName','useName'):
                self.preferName = value in ('1','true','True','yes')
            elif attrib in ('fuzzy','fuzzyMatch'):
                self.fuzzy = value in ('1','true','True','yes')
            else:
                attribs.append((attrib, value))
        self.skinAttributes = attribs
        if self.instance:
            try:
                self.instance.setScale(1 if self.scaled else 0)
            except Exception:
                pass
        return Renderer.applySkin(self, desktop, parent)

    @staticmethod
    def _ascii(s):
        try:
            s = unicodedata.normalize('NFKD', s)
            s = s.encode('ascii','ignore').decode('ascii')
        except Exception:
            pass
        return s

    @staticmethod
    def _norm_name(s):
        s = s.strip().lower()
        s = GradientCountryFlagPixmap._ascii(s)
        s = s.replace('&',' and ')
        s = re.sub(r"[^a-z0-9]+"," ", s)
        s = re.sub(r"\s+"," ", s).strip()
        repl = {
            'cote d ivoire':'ivory coast',
            'cotedivoire':'ivory coast',
            'czechia':'czech republic',
            'north macedonia':'republic of macedonia',
            'eswatini':'swaziland',
            'u s a':'united states of america',
            'united states':'united states of america',
            'uk':'united kingdom',
            'great britain':'united kingdom',
            'holy see':'vatican city',
            'lao pdr':'laos',
            'burma':'myanmar',
            'korea south':'south korea',
            'korea north':'north korea',
            'republic of korea':'south korea',
            'kyrgyz republic':'kyrgyzstan',
            # german
            'deutschland':'germany',
            'osterreich':'austria',
            'oesterreich':'austria',
            'schweiz':'switzerland',
            'vereinigte staaten':'united states of america',
            'vereinigte staaten von amerika':'united states of america',
            'vereinigtes konigreich':'united kingdom',
            'vereinigtes königreich':'united kingdom',
            'niederlande':'netherlands',
            'frankreich':'france',
            'italien':'italy',
            'spanien':'spain',
            'polen':'poland',
            'griechenland':'greece',
            'turkei':'turkey',
            'tuerkei':'turkey',
            'türkei':'turkey',
            'turkiye':'turkey',
            'timor leste':'east timor',
            'saint lucia':'st lucia',
            'saint vincent and the grenadines':'st vincent and the grenadines',
            'saint barthelemy':'st barts',
        }
        if s in repl:
            s = repl[s]
        key = re.sub(r"\s+","", s)
        return key

    def _code_to_prefname(self, code):
        m = {
            'US':'united states of america', 'GB':'united kingdom', 'UK':'united kingdom',
            'CI':'ivory coast', 'CD':'democratic republic of congo', 'CG':'republic of the congo',
            'KR':'south korea', 'KP':'north korea', 'VA':'vatican city', 'CZ':'czech republic',
            'SZ':'swaziland', 'MK':'republic of macedonia', 'TL':'east timor',
            'HK':'hong kong', 'MO':'macao',
            'DE':'germany', 'AT':'austria', 'CH':'switzerland',
            'FR':'france', 'IT':'italy', 'ES':'spain', 'PT':'portugal',
            'NL':'netherlands', 'BE':'belgium', 'LU':'luxembourg',
            'IE':'ireland', 'DK':'denmark', 'SE':'sweden', 'NO':'norway', 'FI':'finland',
            'PL':'poland', 'GR':'greece', 'HU':'hungary', 'RO':'romania', 'BG':'bulgaria',
            'TR':'turkey',
            'CA':'canada',  # ergänzt
            'ZA':'south africa',
        }
        return m.get(code.upper(), '')

    def _missing_path(self):
        cands = [self.missing,
                 os.path.join(self.basePath, self.missing)]
        for c in cands:
            if c and os.path.exists(c):
                return c
        return ''

    def _find_by_wildcard(self, keyname):
        # Nur für Namen (nicht für Codes) – bewusst KEIN "*<key>.png", um false positives zu vermeiden
        pats = [
            os.path.join(self.basePath, keyname + '.png'),
            os.path.join(self.basePath, '*-' + keyname + '.png'),
            os.path.join(self.basePath, '*_' + keyname + '.png'),
        ]
        for p in pats:
            ms = glob.glob(p)
            if ms:
                return ms[0]
        return ''

    def _find_path(self, txt):
        if not txt:
            return ''
        if txt in self._cache:
            return self._cache[txt]

        q = (txt or '').strip()

        # 1) Codes strikt: zuerst direkt basePath/<code>.png
        m = re.match(r'^([A-Za-z]{2})', q)
        if m:
            code = m.group(1).lower()
            p_code = os.path.join(self.basePath, code + '.png')
            if os.path.exists(p_code):
                self._cache[txt] = p_code
                return p_code
            # optional: via bevorzugter Name weiterprobieren
            pref = self._code_to_prefname(code)
            if pref:
                key = self._norm_name(pref)
                p = self._find_by_wildcard(key)
                if p:
                    self._cache[txt] = p
                    return p
            # KEIN "*ca.png" o. ä., um "south africa.png" nicht zu treffen

        # 2) Name (CountryName / CountryLabel ohne Code)
        # bei "DE – Deutschland" nicht die Kennung nehmen, sondern den Namen
        if ' - ' in q:
            parts = q.split(' - ', 1)
            # falls vorne ein Code war und oben nicht gefunden, nimm den Rest (Name)
            q = parts[-1].strip()

        key = self._norm_name(q)
        p = self._find_by_wildcard(key)
        if p:
            self._cache[txt] = p
            return p

        self._cache[txt] = ''
        return ''

    def changed(self, what):
        if not self.instance:
            return
        try:
            text = str(self.source.text or '').strip()
        except Exception:
            text = ''
        if self._last_value is not None and text == self._last_value:
            return
        path = self._find_path(text)
        if path and os.path.exists(path):
            if self._last_path != path:
                try:
                    self.instance.setScale(1 if self.scaled else 0)
                except Exception:
                    pass
                self.instance.setPixmapFromFile(path)
                self._last_path = path
            self._last_value = text
            self.instance.show()
        else:
            miss = self._missing_path()
            if miss and os.path.exists(miss):
                if self._last_path != miss:
                    self.instance.setPixmapFromFile(miss)
                    self._last_path = miss
                self._last_value = text
                self.instance.show()
            else:
                self._last_value = text
                self.instance.hide()
