# -*- coding: utf-8 -*-
from __future__ import absolute_import

from urllib.parse import quote, unquote

from Components.config import (
    config,
    ConfigSubsection,
    ConfigSelection,
    ConfigText,
    configfile,
)

from .constants import COLOR_ITEMS, COLOR_CHOICES


if not hasattr(config.plugins, "BundesligaWQHD"):
    config.plugins.BundesligaWQHD = ConfigSubsection()

_cfg = config.plugins.BundesligaWQHD

# Dauerhafte Auswahl. Es werden absichtlich nur Dateinamen und keine absoluten
# Pfade gespeichert, damit eine Sicherung auch nach einem Neu-Flash gültig ist.
if not hasattr(_cfg, "team"):
    _cfg.team = ConfigText(default="", fixed_size=False)
if not hasattr(_cfg, "skinparts"):
    _cfg.skinparts = ConfigText(default="", fixed_size=False)
if not hasattr(_cfg, "state_version"):
    _cfg.state_version = ConfigText(default="1", fixed_size=False)

for key, _label, _xml_name in COLOR_ITEMS:
    if not hasattr(_cfg, key):
        setattr(
            _cfg,
            key,
            ConfigSelection(default="team", choices=COLOR_CHOICES)
        )


def color_config(key):
    return getattr(_cfg, key)


def overrides_active():
    return any(color_config(key).value != "team" for key, _label, _xml_name in COLOR_ITEMS)


def get_overrides():
    result = {}
    for key, _label, xml_name in COLOR_ITEMS:
        value = color_config(key).value
        if value != "team":
            result[xml_name] = value
    return result


def reset_colors(save=False):
    for key, _label, _xml_name in COLOR_ITEMS:
        cfg = color_config(key)
        cfg.value = "team"
        if save:
            cfg.save()
    if save:
        configfile.save()


def save_colors():
    for key, _label, _xml_name in COLOR_ITEMS:
        color_config(key).save()
    configfile.save()


def cancel_colors():
    for key, _label, _xml_name in COLOR_ITEMS:
        color_config(key).cancel()


def get_saved_team():
    return _cfg.team.value.strip()


def save_team(filename):
    _cfg.team.value = filename or ""
    _cfg.team.save()
    configfile.save()


def _encode_component(value):
    return quote(value or "", safe="")


def _decode_component(value):
    try:
        return unquote(value or "")
    except Exception:
        return value or ""


def get_saved_skinparts():
    """Return {category: filename} from the compact settings value."""
    result = {}
    raw = _cfg.skinparts.value.strip()
    if not raw:
        return result
    for item in raw.split(";"):
        if not item or "=" not in item:
            continue
        category, filename = item.split("=", 1)
        category = _decode_component(category).strip()
        filename = _decode_component(filename).strip()
        if category and filename:
            result[category] = filename
    return result


def save_skinparts(values):
    items = []
    for category in sorted(values):
        filename = values.get(category) or ""
        if filename:
            items.append("%s=%s" % (_encode_component(category), _encode_component(filename)))
    _cfg.skinparts.value = ";".join(items)
    _cfg.skinparts.save()
    configfile.save()


def set_saved_skinpart(category, filename):
    values = get_saved_skinparts()
    if filename:
        values[category] = filename
    else:
        values.pop(category, None)
    save_skinparts(values)
