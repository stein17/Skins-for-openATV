# -*- coding: utf-8 -*-
from __future__ import absolute_import

from Components.config import (
    ConfigSelection,
    ConfigSubsection,
    ConfigYesNo,
    config,
    configfile,
)

from .constants import STATIC_ICONSET_ID, STORAGE_CHOICES
from .iconsets import IconsetManager


if not hasattr(config.plugins, "AnimatedWeather"):
    config.plugins.AnimatedWeather = ConfigSubsection()

_cfg = config.plugins.AnimatedWeather
_managers = {}

if not hasattr(_cfg, "enabled"):
    _cfg.enabled = ConfigYesNo(default=True)
if not hasattr(_cfg, "interval"):
    _cfg.interval = ConfigSelection(
        default="200",
        choices=[(str(value), "%d ms" % value) for value in range(100, 501, 20)],
    )
if not hasattr(_cfg, "storage"):
    # OpenATV 8.0 / Python 3.14 akzeptiert hier ausdrücklich nur list oder
    # dict. STORAGE_CHOICES ist absichtlich ein unveränderliches tuple und
    # wird deshalb für ConfigSelection in eine Liste umgewandelt.
    _cfg.storage = ConfigSelection(default="flash", choices=list(STORAGE_CHOICES))
if not hasattr(_cfg, "iconset"):
    # ConfigSelection muss die gespeicherte Auswahl bereits beim Erzeugen
    # kennen. Wird es zunaechst nur mit "static" angelegt, ersetzt Enigma2
    # einen gespeicherten Wert wie "meteocons-2-fill" sofort durch den ersten
    # Eintrag der Liste. Ein spaeteres setChoices() kann ihn dann nicht mehr
    # wiederherstellen.
    initial_iconset_choices = IconsetManager(storage_key=_cfg.storage.value).choices()
    _cfg.iconset = ConfigSelection(
        default=STATIC_ICONSET_ID,
        choices=initial_iconset_choices,
    )


def animation_config():
    return _cfg.enabled


def interval_config():
    return _cfg.interval


def storage_config():
    return _cfg.storage


def iconset_config():
    return _cfg.iconset


def manager_for_current_storage():
    storage_key = _cfg.storage.value
    if storage_key not in _managers:
        _managers[storage_key] = IconsetManager(storage_key=storage_key)
    return _managers[storage_key]


def refresh_iconset_choices(preferred=None):
    if preferred is not None:
        current = preferred
    else:
        # ConfigSelection kann einen gespeicherten Wert bereits auf den ersten
        # Listeneintrag zurueckgesetzt haben, bevor alle Auswahlmoeglichkeiten
        # bekannt sind. saved_value enthaelt dann weiterhin den korrekten Wert
        # aus /etc/enigma2/settings und hat Vorrang.
        saved = getattr(_cfg.iconset, "saved_value", None)
        current = saved if saved else _cfg.iconset.value
    choices = manager_for_current_storage().choices()
    values = [value for value, label in choices]
    if current not in values:
        # Externe Datentraeger koennen beim GUI-Start erst einige Augenblicke
        # spaeter bereit sein. Eine bereits gespeicherte lokale Auswahl darf
        # deshalb nicht nur wegen einer voruebergehend leeren Set-Liste auf
        # "statisch" zurueckfallen.
        if current and current != STATIC_ICONSET_ID:
            choices.append((current, "%s (momentan nicht verfügbar)" % current))
        else:
            current = STATIC_ICONSET_ID
    try:
        # Der Default muss dauerhaft "static" bleiben. Wird hier die aktuelle
        # Auswahl als Default gesetzt, entfernt Enigma2 sie beim Speichern aus
        # /etc/enigma2/settings.
        _cfg.iconset.setChoices(choices, default=STATIC_ICONSET_ID)
    except TypeError:
        _cfg.iconset.setChoices(choices)
    _cfg.iconset.value = current
    return choices


def save_settings():
    _cfg.enabled.save()
    _cfg.interval.save()
    _cfg.storage.save()
    _cfg.iconset.save()
    configfile.save()


def cancel_settings():
    _cfg.enabled.cancel()
    _cfg.interval.cancel()
    _cfg.storage.cancel()
    _cfg.iconset.cancel()


refresh_iconset_choices()
