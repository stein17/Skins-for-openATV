#!/usr/bin/python
# -*- coding: utf-8 -*-

from re import sub, S, I, search, compile, DOTALL, escape
from six import text_type
from unicodedata import normalize
import sys

unicode = str

PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True
    import html
    html_parser = html
    from urllib.parse import quote_plus
else:
    from urllib import quote_plus
    from HTMLParser import HTMLParser
    html_parser = HTMLParser()

def quoteEventName(eventName):
    try:
        text = eventName.decode('utf8').replace(u'\x86', u'').replace(u'\x87', u'').encode('utf8')
    except:
        text = eventName
    return quote_plus(text, safe="+")

# Consolidated REGEX pattern for cleaning event names
# Updated REGEX pattern
REGEX = compile(
    r'[\(\[].*?[\)\]]|'  # Remove text inside parentheses or brackets
    r'[:\s]*\(?(?:odc\.?\s*\d+|ep\.?\s*\d+|episode\.?\s*\d+)\)?$|'  # Remove "odc.", "ep.", "episode" with numbers
    r'[:\s]*\(?(?:odc\.?\s*\d+|ep\.?\s*\d+|episode\.?\s*\d+)\)?$|'  # Consolidated rule for "odc", "ep", "episode"
    r'[:!]|'  # Remove colons or exclamation marks
    r'\s-\s.*|'  # Remove text after a dash
    r',|'  # Remove commas
    r'/.*|'  # Remove text after a slash
    r'\|\s?\d+\+|'  # Remove "|" followed by a number and "+"
    r'\d+\+|'  # Remove number followed by "+"
    r'\s\*\d{4}\Z|'  # Remove "*" followed by a 4-digit year
    r'[\(\[\|].*?[\)\]\|]|'  # Remove text inside parentheses, brackets, or pipes
    r'(?:\"[\.|\,]?\s.*|\"|'  # Remove text inside quotes
    r'\.\s.+)|'  # Remove text after a period
    r'Премьера\.\s|'  # Remove "Премьера.", specific for Russian
    r'[хмтдХМТД]/[фс]\s|'  # Remove patterns for Russian with "/ф" or "/с"
    r'\s[сС](?:езон|ерия|-н|-я)\s.*|'  # Remove "season" or "episode" in Russian
    r'\s\d{1,3}\с[чсЧС]\.?\с.*|'  # Remove part/episode number in Russian
    r'\.\с\d{1,3}\с[чсЧС]\.?\с.*|'  # Remove part/episode number in Russian with a period
    r'\с[чсЧС]\.?\с\d{1,3}.*|'  # Remove part/episode in Russian
    r'\d{1,3}-(?:я|й)\с?с-н.*',  # Remove ending with number and Russian suffix
    DOTALL
)

def remove_accents(string):
    if not isinstance(string, text_type):
        string = text_type(string, 'utf-8')
    string = sub(u"[àáâãäå]", 'a', string)  # Replace accented 'a' characters
    string = sub(u"[èéêë]", 'e', string)    # Replace accented 'e' characters
    string = sub(u"[ìíîï]", 'i', string)    # Replace accented 'i' characters
    string = sub(u"[òóôõö]", 'o', string)   # Replace accented 'o' characters
    string = sub(u"[ùúûü]", 'u', string)    # Replace accented 'u' characters
    string = sub(u"[ýÿ]", 'y', string)      # Replace accented 'y' characters
    return string

def unicodify(s, encoding='utf-8', norm=None):
    if not isinstance(s, text_type):
        s = text_type(s, encoding)
    if norm:
        s = normalize(norm, s)
    return s

def str_encode(text, encoding="utf8"):
    if not PY3:
        if isinstance(text, text_type):
            return text.encode(encoding)
    return text

def cutName(eventName=""):
    if eventName:
        # Ensure numeric event names are not removed
        if eventName.isdigit():
            return eventName

        # Replace '&' with 'e' for better readability
        eventName = eventName.replace('&', 'e')

        # Remove numeric identifiers at the beginning of the event name (only if they are not part of the name)
        # Example: Do not remove "19+" or "90 Days to Wed"
        if not eventName[:2].isdigit() and not eventName[:3].isdigit():
            eventName = sub(r'^\d{10}-', '', eventName)

        # Remove episode numbers in various formats (odc., ep., episode)
        eventName = sub(r'[:\s]*\(?(?:odc\.?\s*\d+|ep\.?\s*\d+|episode\.?\s*\d+)\)?$', '', eventName, flags=I)

        # Remove episode numbers after a dash or space (e.g., "2-8" → "2")
        eventName = sub(r'(\d+)[\s-]*(\d+)$', r'\1', eventName)  # Keep only the season number

        # Remove season numbers like "2", "11", "I", "II" at the end (if not part of the title)
        eventName = sub(r'\s*(\d+|I{1,3}|IV|V|VI|VII|VIII|IX|X)$', '', eventName)

        # Remove special characters and extra spaces
        eventName = sub(r'[^\w\s]', '', eventName)  # Clean up special characters
        eventName = sub(r'[:\-]', ' ', eventName)  # Remove colons and dashes

        # Normalize spaces
        eventName = sub(r'\s+', ' ', eventName).strip()

        # Remove specified terms (e.g., "AXN", "Live:", "Episode")
        terms_to_remove = [
            "AXN", "AXN Black", "AXN White", "Regina -", "Live:", "LIVE: ", "Prima", "programu", 
            "filter cine34", "cine34", "Episode", "Ep", "Top 10 - "
        ]
        for term in terms_to_remove:
            eventName = eventName.replace(term, "")

        # Remove age ratings and other unwanted suffixes
        eventName = eventName.replace('(18+)', '').replace('18+', '').replace('(16+)', '').replace('16+', '')
        eventName = eventName.replace('(12+)', '').replace('12+', '').replace('(7+)', '').replace('7+', '')
        eventName = eventName.replace('(6+)', '').replace('6+', '').replace('(0+)', '').replace('0+', '').replace('+', '')

        # Handle specific event names (e.g., "1, 2, 3...Kabaret! Wyzej, dalej, mocniej")
        eventName = eventName.replace('1, 2, 3...Kabaret! Wyzej, dalej, mocniej', 'Kabaret Wyzej dalej mocniej')

        # Remove episode numbers like " - Ep.5"
        eventName = sub(r'\s*-\s*Ep\.\d+$', '', eventName)

        # Remove patterns like "2 3" or "2 - 3"
        eventName = sub(r'\s*\d+\s+\d+$', '', eventName)
        eventName = sub(r'\s*\d+\s*-\s*\d+$', '', eventName)

        # Remove patterns like " - 9388" or "5-2"
        eventName = sub(r'\s*-\s*\d+$', '', eventName)
        eventName = sub(r'\s*\d+-\d+$', '', eventName)

        # Remove trailing exclamation marks and dots
        eventName = sub(r'\s*!\s*$', '', eventName)
        eventName = sub(r'\s*\.\s*', ' ', eventName)

        # Remove colons and replace with space
        eventName = sub(r'\s*:\s*', ' ', eventName)

        return eventName.strip()
    return ""

def getCleanTitle(eventitle=""):
    save_name = eventitle.replace(' ^`^s', '').replace(' ^`^y', '')
    return save_name

def sanitize_filename(filename):
    sanitized = sub(r'[^\w\s-]', '', filename)
    return sanitized.strip()

def convtext(text=''):
    try:
        if text is None:
            print('return None original text:', type(text))
            return
        if text == '':
            print('text is an empty string')
        else:
            text = str(text)
            text = text.lower().rstrip()

            # Optimized sostituzioni list
            sostituzioni = [
                # Replacements for common patterns
                ('1/2', 'mezzo', 'replace'),  # Example: "1/2" to "mezzo"
                ('c.s.i.', 'csi', 'replace'),  # Example: "c.s.i." to "csi"
                ('c.s.i:', 'csi', 'replace'),  # Example: "c.s.i:" to "csi"
                ('n.c.i.s.:', 'ncis', 'replace'),  # Example: "n.c.i.s.:" to "ncis"
                ('ncis:', 'ncis', 'replace'),  # Example: "ncis:" to "ncis"
                ('Navy cis:', 'ncis', 'replace'),  # Example: "ncis:" to "ncis"
                ('ritorno al futuro:', 'ritorno al futuro', 'replace'),  # Example: "ritorno al futuro:" to "ritorno al futuro"

                # Set replacements for specific titles
                ('superman e lois', 'superman & lois', 'set'),  # Example: "superman & lois" to "superman e lois"
                ('lois i clark', 'superman & lois', 'set'),  # Example: "lois & clark" to "superman e lois"
                ('JAG - Wojskowe Biuro Sledcze', 'J.A.G', 'set'),  # Example: "JAG - Wojskowe Biuro Sledcze" to "JAG"
                ("una 44 magnum per", 'magnumxx', 'set'),  # Example: "una 44 magnum per" to "magnumxx"
                ('john q', 'johnq', 'set'),  # Example: "john q" to "johnq"
                ('il ritorno di colombo', 'colombo', 'set'),  # Example: "il ritorno di colombo" to "colombo"
                ('lingo: parole', 'lingo', 'set'),  # Example: "lingo: parole" to "lingo"
                ('io & marilyn', 'io e marilyn', 'set'),  # Example: "io & marilyn" to "io e marilyn"
                ('giochi olimpici parigi', 'olimpiadi di parigi', 'set'),  # Example: "giochi olimpici parigi" to "olimpiadi di parigi"
                ('bruno barbieri', 'brunobarbierix', 'set'),  # Example: "bruno barbieri" to "brunobarbierix"
                ("anni '60", 'anni 60', 'set'),  # Example: "anni '60" to "anni 60"
                ('cortesie per gli ospiti', 'cortesieospiti', 'set'),  # Example: "cortesie per gli ospiti" to "cortesieospiti"
                ('tg regione', 'tg3', 'set'),  # Example: "tg regione" to "tg3"
                ('tg1', 'tguno', 'set'),  # Example: "tg1" to "tguno"
                ('josephine angelo', 'josephine ange gardien', 'set'),  # Example: "josephine angelo" to "josephine ange gardien"
                ('alessandro borghese - 4 ristoranti', 'alessandroborgheseristoranti', 'set'),  # Example: "alessandro borghese - 4 ristoranti" to "alessandroborgheseristoranti"
                ('alessandro borghese: 4 ristoranti', 'alessandroborgheseristoranti', 'set'),  # Example: "alessandro borghese: 4 ristoranti" to "alessandroborgheseristoranti"
                ('amici di maria', 'amicimaria', 'set'),  # Example: "amici di maria" to "amicimaria"
                ('ritorno al futuro - parte iii', 'ritornoalfuturoparteiii', 'set'),  # Example: "ritorno al futuro - parte iii" to "ritornoalfuturoparteiii"
                ('ritorno al futuro - parte ii', 'ritornoalfuturoparteii', 'set'),  # Example: "ritorno al futuro - parte ii" to "ritornoalfuturoparteii"
                ('walker, texas ranger', 'walker texas ranger', 'set'),  # Example: "walker, texas ranger" to "walker texas ranger"
                ('e.r.', 'ermediciinprimalinea', 'set'),  # Example: "e.r." to "ermediciinprimalinea"
                ('alexa: vita da detective', 'alexa vita da detective', 'set'),  # Example: "alexa: vita da detective" to "alexa vita da detective"
                ('shaun: vita da pecora', 'shaun', 'set'),  # Example: "shaun: vita da pecora" to "shaun"
                ('gf daily', 'grande fratello', 'set'),  # Example: "gf daily" to "grande fratello"
            ]

            # Apply sostituzioni
            for parola, sostituto, metodo in sostituzioni:
                if parola in text:
                    if metodo == 'set':
                        text = sostituto
                        break
                    elif metodo == 'replace':
                        text = text.replace(parola, sostituto)

            # Clean up the text further
            text = cutName(text)
            text = getCleanTitle(text)

            if text.endswith("the"):
                text = "the " + text[:-4]

            # Remove unwanted characters and patterns
            text = text.replace("\xe2\x80\x93", "").replace('\xc2\x86', '').replace('\xc2\x87', '').replace('webhdtv', '')
            text = text.replace('1080i', '').replace('dvdr5', '').replace('((', '(').replace('))', ')').replace('hdtvrip', '')
            text = text.replace('german', '').replace('english', '').replace('ws', '').replace('ituneshd', '').replace('hdtv', '')
            text = text.replace('dvdrip', '').replace('unrated', '').replace('retail', '').replace('web-dl', '').replace('divx', '')
            text = text.replace('bdrip', '').replace('uncut', '').replace('avc', '').replace('ac3d', '').replace('ts', '')
            text = text.replace('ac3md', '').replace('ac3', '').replace('webhdtvrip', '').replace('xvid', '').replace('bluray', '')
            text = text.replace('complete', '').replace('internal', '').replace('dtsd', '').replace('h264', '').replace('dvdscr', '')
            text = text.replace('dubbed', '').replace('line.dubbed', '').replace('dd51', '').replace('dvdr9', '').replace('sync', '')
            text = text.replace('webhdrip', '').replace('webrip', '').replace('repack', '').replace('dts', '').replace('webhd', '')
            text = text.strip(' -')

            # Remove accents and final cleanup
            text = remove_accents(text)
            text = sub(r'[^\w\s]+$', '', text)  # Remove trailing special characters
            text = text.strip()

            return text
    except Exception as e:
        print("Error in convtext:", e)
        return text