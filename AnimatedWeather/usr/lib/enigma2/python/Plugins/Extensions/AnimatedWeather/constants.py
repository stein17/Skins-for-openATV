# -*- coding: utf-8 -*-

from os.path import join


PLUGIN_NAME = "Animated Weather"
PLUGIN_VERSION = "0.3-r4"
PLUGIN_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/AnimatedWeather"
DATA_PATH = "/usr/share/enigma2/AnimatedWeather"
CATALOG_PATH = join(DATA_PATH, "catalog.json")
PREVIEW_PATH = join(DATA_PATH, "previews")

STATIC_ICONSET_ID = "static"
EXPECTED_CODES = tuple([str(value) for value in range(48)] + ["NA"])

STORAGE_PATHS = {
    "flash": join(DATA_PATH, "sets"),
    "hdd": "/media/hdd/AnimatedWeather/sets",
    "usb": "/media/usb/AnimatedWeather/sets",
    "mmc": "/media/mmc/AnimatedWeather/sets",
}

STORAGE_CHOICES = (
    ("flash", "Flash-Speicher"),
    ("hdd", "Festplatte (/media/hdd)"),
    ("usb", "USB (/media/usb)"),
    ("mmc", "MMC (/media/mmc)"),
)

OFFICIAL_RELEASE_PREFIX = (
    "https://github.com/stein17/Skins-for-openATV/releases/download/"
)
RELEASE_BASE_URL = OFFICIAL_RELEASE_PREFIX + "animated-weather-icons-v1.4.0/"

MAX_ARCHIVE_SIZE = 30 * 1024 * 1024
MAX_UNPACKED_SIZE = 100 * 1024 * 1024
MAX_ARCHIVE_FILES = 5000
MAX_FRAMES = 60
MIN_FRAMES = 1
DOWNLOAD_CHUNK_SIZE = 128 * 1024


def storage_path(storage_key):
    return STORAGE_PATHS.get(storage_key, STORAGE_PATHS["flash"])
