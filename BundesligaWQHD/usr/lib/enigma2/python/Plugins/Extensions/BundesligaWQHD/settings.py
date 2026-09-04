# -*- coding: utf-8 -*-
from __future__ import absolute_import

from urllib.parse import quote, unquote

from Components.config import (
    config,
    ConfigSubsection,
    ConfigSelection,
    ConfigText,
    ConfigYesNo,
    configfile,
)

from .constants import COLOR_ITEMS, COLOR_CHOICES
from .weathericons import DEFAULT_ICONSET_ID, iconset_choices

try:
    from Plugins.Extensions.AnimatedWeather.settings import (
        animation_config as _central_animation_config,
        cancel_settings as _central_cancel_settings,
        iconset_config as _central_iconset_config,
        interval_config as _central_interval_config,
        save_settings as _central_save_settings,
    )
except (ImportError, AttributeError):
    _central_animation_config = None
    _central_cancel_settings = None
    _central_iconset_config = None
    _central_interval_config = None
    _central_save_settings = None


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
if not hasattr(_cfg, "weather_animation"):
    _cfg.weather_animation = ConfigYesNo(default=True)
if not hasattr(_cfg, "weather_animation_interval"):
    _cfg.weather_animation_interval = ConfigSelection(
        default="200",
        choices=[(str(value), "%d ms" % value) for value in range(100, 501, 20)]
    )
if not hasattr(_cfg, "weather_iconset"):
    _cfg.weather_iconset = ConfigSelection(
        default=DEFAULT_ICONSET_ID,
        choices=iconset_choices()
    )

for key, _label, _xml_name in COLOR_ITEMS:
    if not hasattr(_cfg, key):
        setattr(
            _cfg,
            key,
            ConfigSelection(default="team", choices=COLOR_CHOICES)
        )


def color_config(key):
    return getattr(_cfg, key)


def weather_animation_config():
    if _central_animation_config is not None:
        return _central_animation_config()
    return _cfg.weather_animation


def weather_animation_interval_config():
    if _central_interval_config is not None:
        return _central_interval_config()
    return _cfg.weather_animation_interval


def weather_iconset_config():
    if _central_iconset_config is not None:
        return _central_iconset_config()
    return _cfg.weather_iconset


def save_weather_settings():
    if _central_save_settings is not None:
        _central_save_settings()
        return
    _cfg.weather_animation.save()
    _cfg.weather_animation_interval.save()
    _cfg.weather_iconset.save()
    configfile.save()


def cancel_weather_settings():
    if _central_cancel_settings is not None:
        _central_cancel_settings()
        return
    _cfg.weather_animation.cancel()
    _cfg.weather_animation_interval.cancel()
    _cfg.weather_iconset.cancel()


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
