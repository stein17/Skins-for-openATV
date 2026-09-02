# -*- coding: utf-8 -*-
from __future__ import absolute_import

import hashlib
import json
import os
import re
import shutil
import struct
import tempfile
import unicodedata
import zipfile
from glob import glob
from urllib.request import Request, urlopen

from .constants import (
    CATALOG_PATH,
    DOWNLOAD_CHUNK_SIZE,
    EXPECTED_CODES,
    MAX_ARCHIVE_FILES,
    MAX_ARCHIVE_SIZE,
    MAX_FRAMES,
    MAX_UNPACKED_SIZE,
    MIN_FRAMES,
    RELEASE_BASE_URL,
    STATIC_ICONSET_ID,
    storage_path,
)


class IconsetError(Exception):
    pass


def format_bytes(value):
    value = int(value or 0)
    if value >= 1024 * 1024:
        return "%.1f MiB" % (float(value) / (1024 * 1024))
    if value >= 1024:
        return "%.0f KiB" % (float(value) / 1024)
    return "%d B" % value


def safe_id(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return (value or "lokales-iconset")[:60]


def _json_load(filename, default=None):
    try:
        with open(filename, "r", encoding="utf-8") as source:
            return json.load(source)
    except (OSError, ValueError, TypeError):
        return default


def _png_dimensions(filename):
    with open(filename, "rb") as source:
        return _png_dimensions_from_header(source.read(24))


def _png_dimensions_from_header(header):
    if (
        len(header) != 24
        or header[:8] != b"\x89PNG\r\n\x1a\n"
        or header[12:16] != b"IHDR"
    ):
        raise IconsetError("Ungültige PNG-Datei im Wetter-Iconset.")
    return struct.unpack(">II", header[16:24])


def _frame_indices(directory):
    try:
        names = os.listdir(directory)
    except OSError:
        raise IconsetError("Motivordner fehlt: %s" % os.path.basename(directory))
    indices = []
    for name in names:
        match = re.match(r"^a([0-9]+)\.png$", name, re.IGNORECASE)
        if match:
            indices.append(int(match.group(1)))
    indices.sort()
    if len(indices) < MIN_FRAMES:
        raise IconsetError("Zu wenige Wetterbilder in %s." % os.path.basename(directory))
    if len(indices) > MAX_FRAMES:
        raise IconsetError("Zu viele Wetterbilder in %s." % os.path.basename(directory))
    if indices != list(range(len(indices))):
        raise IconsetError("Die Wetterbilder in %s sind nicht lückenlos nummeriert." % os.path.basename(directory))
    return indices


def _static_name(code):
    return "na.png" if code == "NA" else "%s.png" % code


def _safe_target(value):
    return bool(
        value
        and os.path.basename(value) == value
        and value not in (".", "..")
        and re.match(r"^[^/\\\x00]+$", value)
    )


class IconsetManager(object):
    # Das Einstellungsmenü wird bei jeder Cursorbewegung aktualisiert. Eine
    # vollständige Prüfung aller PNG-Dateien ist dort unnötig teuer und kann
    # auf Enigma2 den Spinner auslösen. Der Cache enthält deshalb nur eine
    # schnelle Strukturprüfung. Die gründliche Prüfung bleibt unverändert in
    # install_public() und import_local().
    _installed_entries_cache = {}

    def __init__(self, storage_key="flash", sets_base=None, catalog_path=None, resolution=None):
        self.storage_key = storage_key or "flash"
        self.sets_base = sets_base or storage_path(self.storage_key)
        self.catalog_path = catalog_path or CATALOG_PATH
        self.catalog = _json_load(self.catalog_path, {}) or {}
        self.resolution = resolution or self._resolution_key()

    def _resolution_key(self):
        try:
            from enigma import getDesktop
            return "wqhd" if getDesktop(0).size().width() >= 2560 else "fhd"
        except Exception:
            return "fhd"

    def public_entries(self):
        result = []
        for entry in self.catalog.get("sets", []):
            if not isinstance(entry, dict):
                continue
            iconset_id = str(entry.get("id", ""))
            if not re.match(r"^[a-z0-9][a-z0-9.-]+$", iconset_id):
                continue
            if self.package(entry):
                result.append(entry)
        return result

    def public_entry(self, iconset_id):
        for entry in self.public_entries():
            if entry.get("id") == iconset_id:
                return entry
        return None

    def package(self, entry):
        packages = (entry or {}).get("packages", {})
        # Ein Universalpaket genügt. ePixmap skaliert das Bild
        # mit beibehaltenem Seitenverhältnis auf die tatsächliche Widgetgröße.
        return (
            packages.get("universal")
            or packages.get("wqhd")
            or packages.get(self.resolution)
            or packages.get("fhd")
            or {}
        )

    def package_size_text(self, entry):
        return format_bytes(self.package(entry).get("bytes", 0))

    def iconset_path(self, iconset_id):
        if not _safe_target(iconset_id or ""):
            return ""
        return os.path.join(self.sets_base, iconset_id)

    def ensure_storage(self):
        """Verhindert, dass ein fehlender Datenträger unbemerkt Flash belegt."""
        configured_base = storage_path(self.storage_key)
        if os.path.normpath(self.sets_base) == os.path.normpath(configured_base) and self.storage_key != "flash":
            mount_root = os.path.dirname(os.path.dirname(configured_base))
            real_root = os.path.realpath(mount_root)
            if not os.path.isdir(mount_root) or not (
                os.path.ismount(mount_root) or os.path.ismount(real_root)
            ):
                raise IconsetError("Der gewählte Datenträger %s ist nicht eingehängt." % mount_root)
        if not os.path.isdir(self.sets_base):
            os.makedirs(self.sets_base)

    def _legacy_codes(self, names):
        result = [str(value) for value in range(48)]
        if "NA" in names:
            result.append("NA")
        return result

    def _flat_codes(self, directory):
        result = [str(value) for value in range(48)]
        if os.path.isfile(os.path.join(directory, "na.png")):
            result.append("NA")
        return result

    def _quick_layout(self, path):
        if not os.path.isdir(path) or os.path.islink(path):
            return ""
        if os.path.isfile(os.path.join(path, "mapping.json")):
            return "mapped"
        if all(os.path.isfile(os.path.join(path, str(value), "a0.png")) for value in range(48)):
            return "legacy"
        if all(os.path.isfile(os.path.join(path, "%d.png" % value)) for value in range(48)):
            return "flat"
        return ""

    def is_installed(self, iconset_id):
        return bool(self.selected_path(iconset_id))

    def _cache_key(self):
        return os.path.realpath(self.sets_base)

    def invalidate_installed_cache(self):
        self._installed_entries_cache.pop(self._cache_key(), None)

    def _quick_details(self, path):
        """Prüft nur die Struktur eines bereits installierten Iconsets.

        PNG-Inhalte und sämtliche Frames werden ausschließlich bei der
        Installation geprüft. Hier reicht es, Mapping, Zielpfade und a0.png
        zu kontrollieren. Das hält die Bedienoberfläche reaktionsschnell.
        """
        layout = self._quick_layout(path)
        if not layout:
            return None

        manifest = _json_load(os.path.join(path, "manifest.json"), {}) or {}
        min_frame_hint = manifest.get("min_frames", manifest.get("frames", 0))
        max_frame_hint = manifest.get("max_frames", manifest.get("frames", 0))
        try:
            min_frame_hint = int(min_frame_hint)
        except (TypeError, ValueError):
            min_frame_hint = 0
        try:
            max_frame_hint = int(max_frame_hint)
        except (TypeError, ValueError):
            max_frame_hint = 0

        if layout == "mapped":
            mapping_path = os.path.join(path, "mapping.json")
            if os.path.islink(mapping_path):
                return None
            mapping = _json_load(mapping_path)
            try:
                targets = self._mapping_targets(mapping)
            except IconsetError:
                return None
            for target in targets:
                target_path = os.path.join(path, target)
                if target.lower().endswith(".png"):
                    if not os.path.isfile(target_path) or os.path.islink(target_path):
                        return None
                elif (
                    not os.path.isdir(target_path)
                    or os.path.islink(target_path)
                    or not os.path.isfile(os.path.join(target_path, "a0.png"))
                    or os.path.islink(os.path.join(target_path, "a0.png"))
                ):
                    return None
        elif layout == "legacy":
            for code in self._legacy_codes(set(os.listdir(path))):
                target_path = os.path.join(path, code)
                first_frame = os.path.join(target_path, "a0.png")
                if (
                    not os.path.isdir(target_path)
                    or os.path.islink(target_path)
                    or not os.path.isfile(first_frame)
                    or os.path.islink(first_frame)
                ):
                    return None
        else:
            for code in self._flat_codes(path):
                target_path = os.path.join(path, _static_name(code))
                if not os.path.isfile(target_path) or os.path.islink(target_path):
                    return None
        return {
            "layout": layout,
            "min_frames": min_frame_hint,
            "max_frames": max_frame_hint,
        }

    def installed_entries(self, refresh=False):
        cache_key = self._cache_key()
        if not refresh and cache_key in self._installed_entries_cache:
            return [dict(entry) for entry in self._installed_entries_cache[cache_key]]

        entries = []
        if not os.path.isdir(self.sets_base):
            return entries
        for name in sorted(os.listdir(self.sets_base), key=lambda value: value.casefold()):
            path = self.iconset_path(name)
            if not path or not os.path.isdir(path) or os.path.islink(path):
                continue
            details = self._quick_details(path)
            if not details:
                continue
            manifest = _json_load(os.path.join(path, "manifest.json"), {}) or {}
            public = self.public_entry(name) or {}
            entries.append({
                "id": name,
                "label": manifest.get("label") or public.get("label") or name,
                "license": manifest.get("license") or public.get("license") or "Nur lokal / unbekannt",
                "local_only": bool(manifest.get("local_only", not bool(public))),
                "layout": details["layout"],
                "min_frames": details["min_frames"],
                "max_frames": details["max_frames"],
                "path": path,
            })
        self._installed_entries_cache[cache_key] = [dict(entry) for entry in entries]
        return entries

    def installed_entry(self, iconset_id):
        for entry in self.installed_entries():
            if entry["id"] == iconset_id:
                return entry
        return None

    def update_available(self, iconset_id):
        """Erkennt gezielt katalogisierte Set-Aktualisierungen.

        Nur Katalogeinträge mit einer expliziten Revision werden verglichen.
        Dadurch erscheinen ältere, unveränderte Sets ohne Revisionsangabe
        nicht fälschlich als aktualisierbar.
        """
        entry = self.public_entry(iconset_id)
        revision = (entry or {}).get("revision")
        path = self.selected_path(iconset_id)
        if revision is None or not path:
            return False
        manifest = _json_load(os.path.join(path, "manifest.json"), {}) or {}
        return str(manifest.get("catalog_revision", "")) != str(revision)

    def choices(self):
        choices = [(STATIC_ICONSET_ID, "OAWeather Original (statisch)")]
        known = set([STATIC_ICONSET_ID])
        for entry in self.public_entries():
            iconset_id = entry["id"]
            label = entry.get("label", iconset_id)
            if self.update_available(iconset_id):
                label += " (Update)"
            elif not self.is_installed(iconset_id):
                label += " (Download)"
            choices.append((iconset_id, label))
            known.add(iconset_id)
        for entry in self.installed_entries():
            if entry["id"] not in known:
                choices.append((entry["id"], "%s (lokal)" % entry["label"]))
        return choices

    def selected_path(self, iconset_id):
        if iconset_id == STATIC_ICONSET_ID:
            return ""
        path = self.iconset_path(iconset_id)
        return path if path and self._quick_layout(path) else ""

    def preview_frame(self, iconset_id):
        """Liefert ohne vollständige Set-Prüfung ein geeignetes Vorschaubild.

        Die häufigsten, gut unterscheidbaren Tagesmotive werden zuerst
        versucht. Dadurch funktioniert die Vorschau auch für eigene gemappte,
        klassische und vollständig statische Wettersets.
        """
        path = self.selected_path(iconset_id)
        if not path:
            return ""
        dedicated = os.path.join(path, "preview.png")
        if os.path.isfile(dedicated) and not os.path.islink(dedicated):
            try:
                width, height = _png_dimensions(dedicated)
                if 16 <= width <= 1024 and 16 <= height <= 1024:
                    return dedicated
            except (OSError, ValueError, TypeError, IconsetError):
                pass
        layout = self._quick_layout(path)
        codes = ("32", "34", "30", "12", "16", "4", "20", "NA", "0")
        if layout == "mapped":
            mapping = _json_load(os.path.join(path, "mapping.json"), {}) or {}
            for code in codes:
                value = mapping.get(code, {})
                target = value.get("icon", "") if isinstance(value, dict) else str(value)
                if not _safe_target(target):
                    continue
                target_path = os.path.join(path, target)
                filename = target_path if target.lower().endswith(".png") else os.path.join(target_path, "a0.png")
                if os.path.isfile(filename) and not os.path.islink(filename):
                    return filename
        elif layout == "legacy":
            for code in codes:
                filename = os.path.join(path, code, "a0.png")
                if os.path.isfile(filename) and not os.path.islink(filename):
                    return filename
        elif layout == "flat":
            for code in codes:
                filename = os.path.join(path, _static_name(code))
                if os.path.isfile(filename) and not os.path.islink(filename):
                    return filename
        return ""

    def _mapping_targets(self, mapping):
        if not isinstance(mapping, dict) or set(mapping.keys()) != set(EXPECTED_CODES):
            raise IconsetError("mapping.json muss die Wettercodes 0 bis 47 und NA enthalten.")
        targets = set()
        for code in EXPECTED_CODES:
            value = mapping.get(code, {})
            target = value.get("icon", "") if isinstance(value, dict) else str(value)
            if not _safe_target(target):
                raise IconsetError("Ungültiges Wetterbild für Wettercode %s." % code)
            targets.add(target)
        return sorted(targets)

    def _validate_png(self, filename, description):
        if not os.path.isfile(filename) or os.path.islink(filename):
            raise IconsetError("Wetterbild fehlt oder ist unsicher: %s" % description)
        size = _png_dimensions(filename)
        if min(size) < 16 or max(size) > 1024:
            raise IconsetError("Unzulässige Bildgröße in %s." % description)
        return size

    def validate_directory(self, directory, quiet=False):
        try:
            if not os.path.isdir(directory) or os.path.islink(directory):
                raise IconsetError("Der Iconset-Ordner ist nicht vorhanden oder unsicher.")
            mapping_path = os.path.join(directory, "mapping.json")
            targets = []
            if os.path.isfile(mapping_path):
                layout = "mapped"
                for target in self._mapping_targets(_json_load(mapping_path)):
                    targets.append((target, target.lower().endswith(".png")))
            elif all(os.path.isdir(os.path.join(directory, str(value))) for value in range(48)):
                layout = "legacy"
                names = set(os.listdir(directory))
                targets = [(code, False) for code in self._legacy_codes(names)]
            elif all(os.path.isfile(os.path.join(directory, "%d.png" % value)) for value in range(48)):
                layout = "flat"
                targets = [(_static_name(code), True) for code in self._flat_codes(directory)]
            else:
                raise IconsetError("Kein vollständiges Wetter-Iconset gefunden.")

            frame_counts = []
            dimensions = set()
            for target, is_static in targets:
                if is_static:
                    dimensions.add(self._validate_png(os.path.join(directory, target), target))
                    frame_counts.append(1)
                    continue
                icon_directory = os.path.join(directory, target)
                if not os.path.isdir(icon_directory) or os.path.islink(icon_directory):
                    raise IconsetError("Motivordner fehlt oder ist unsicher: %s" % target)
                indices = _frame_indices(icon_directory)
                frame_counts.append(len(indices))
                first_size = None
                for index in indices:
                    relative = "%s/a%d.png" % (target, index)
                    size = self._validate_png(os.path.join(directory, relative), relative)
                    if first_size is None:
                        first_size = size
                    elif size != first_size:
                        raise IconsetError("Unterschiedliche Bildgrößen im Motivordner %s." % target)
                dimensions.add(first_size)
            if not frame_counts:
                raise IconsetError("Das Wetter-Iconset enthält keine Wetterbilder.")
            return {
                "layout": layout,
                "folders": len(targets),
                "min_frames": min(frame_counts),
                "max_frames": max(frame_counts),
                "dimensions": sorted(dimensions),
            }
        except Exception:
            if quiet:
                return None
            raise

    def _archive_members(self, archive):
        members = archive.infolist()
        if not members or len(members) > MAX_ARCHIVE_FILES:
            raise IconsetError("Ungültige Anzahl Dateien im ZIP-Archiv.")
        total = 0
        normalized = []
        for member in members:
            name = member.filename.replace("\\", "/")
            clean = os.path.normpath(name).replace("\\", "/")
            if clean in ("", "."):
                continue
            if clean.startswith("../") or clean.startswith("/") or "/../" in clean:
                raise IconsetError("Unsicherer Dateipfad im ZIP-Archiv.")
            mode = (member.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise IconsetError("Verknüpfungen sind im ZIP-Archiv nicht erlaubt.")
            total += int(member.file_size or 0)
            if total > MAX_UNPACKED_SIZE:
                raise IconsetError("Das entpackte Iconset ist unerwartet groß.")
            normalized.append((member, clean))
        return normalized

    def _archive_mapping_targets(self, archive, prefix):
        try:
            with archive.open(prefix + "mapping.json", "r") as source:
                mapping = json.loads(source.read().decode("utf-8"))
        except Exception as error:
            raise IconsetError("mapping.json im ZIP-Archiv ist ungültig: %s" % error)
        return self._mapping_targets(mapping)

    def _archive_candidate(self, archive, files, root, layout):
        prefix = root.rstrip("/") + "/" if root else ""
        if layout == "mapped":
            targets = self._archive_mapping_targets(archive, prefix)
        elif layout == "legacy":
            targets = [str(value) for value in range(48)]
            if prefix + "NA/a0.png" in files:
                targets.append("NA")
        else:
            targets = [_static_name(str(value)) for value in range(48)]
            if prefix + "na.png" in files:
                targets.append("na.png")

        counts = []
        dimensions = set()
        for target in targets:
            if layout == "flat" or target.lower().endswith(".png"):
                name = prefix + target
                if name not in files:
                    return None
                with archive.open(archive.getinfo(name), "r") as source:
                    dimensions.add(_png_dimensions_from_header(source.read(24)))
                counts.append(1)
                continue
            pattern = re.compile(r"^%s%s/a([0-9]+)\.png$" % (re.escape(prefix), re.escape(target)), re.IGNORECASE)
            indices = sorted(int(match.group(1)) for name in files for match in [pattern.match(name)] if match)
            if len(indices) < MIN_FRAMES or len(indices) > MAX_FRAMES or indices != list(range(len(indices))):
                return None
            counts.append(len(indices))
            with archive.open(archive.getinfo(prefix + target + "/a0.png"), "r") as source:
                dimensions.add(_png_dimensions_from_header(source.read(24)))
        if not counts:
            return None
        manifest_label = ""
        manifest_name = prefix + "manifest.json"
        if manifest_name in files:
            try:
                with archive.open(archive.getinfo(manifest_name), "r") as source:
                    manifest = json.loads(source.read().decode("utf-8"))
                label = manifest.get("label", "") if isinstance(manifest, dict) else ""
                if isinstance(label, str):
                    manifest_label = re.sub(r"[\x00-\x1f\x7f]+", " ", label).strip()[:80]
            except (KeyError, OSError, RuntimeError, TypeError, ValueError, UnicodeError):
                manifest_label = ""
        return {
            "root": root,
            "layout": layout,
            "label": manifest_label or (os.path.basename(root) if root else "Wetter-Iconset"),
            "manifest_label": manifest_label,
            "folders": len(targets),
            "min_frames": min(counts),
            "max_frames": max(counts),
            "dimensions": sorted(dimensions)[0],
        }

    def inspect_archive(self, archive_filename):
        if not os.path.isfile(archive_filename):
            raise IconsetError("ZIP-Datei wurde nicht gefunden.")
        if os.path.getsize(archive_filename) > MAX_ARCHIVE_SIZE:
            raise IconsetError("Die ZIP-Datei ist größer als 30 MiB.")
        candidates = []
        try:
            with zipfile.ZipFile(archive_filename, "r") as archive:
                members = self._archive_members(archive)
                files = set(name for member, name in members if not member.is_dir())
                roots = set()
                for name in files:
                    if name == "mapping.json":
                        roots.add(("", "mapped"))
                    elif name.endswith("/mapping.json"):
                        roots.add((name[:-len("/mapping.json")], "mapped"))
                    if name == "0/a0.png":
                        roots.add(("", "legacy"))
                    elif name.endswith("/0/a0.png"):
                        roots.add((name[:-len("/0/a0.png")], "legacy"))
                    if name == "0.png":
                        roots.add(("", "flat"))
                    elif name.endswith("/0.png"):
                        roots.add((name[:-len("/0.png")], "flat"))

                for root, layout in sorted(roots, key=lambda item: (item[0].count("/"), item[0], item[1])):
                    prefix = root.rstrip("/") + "/" if root else ""
                    if layout == "legacy" and not all(prefix + "%d/a0.png" % value in files for value in range(48)):
                        continue
                    if layout == "flat" and not all(prefix + "%d.png" % value in files for value in range(48)):
                        continue
                    candidate = self._archive_candidate(archive, files, root, layout)
                    if candidate:
                        if not root and not candidate.get("manifest_label"):
                            candidate["label"] = os.path.splitext(os.path.basename(archive_filename))[0]
                        candidates.append(candidate)
        except IconsetError:
            raise
        except (OSError, ValueError, zipfile.BadZipFile) as error:
            raise IconsetError("ZIP-Datei konnte nicht gelesen werden: %s" % error)
        if not candidates:
            raise IconsetError("Kein vollständiges Wetter-Iconset im ZIP-Archiv gefunden.")
        return candidates

    def scan_local_archives(self):
        paths = list(glob(os.path.join(self.sets_base, "*.zip")))
        for root in ("/tmp", "/media/hdd", "/media/usb", "/media/mmc"):
            paths.extend(glob(os.path.join(root, "*.zip")))
            paths.extend(glob(os.path.join(root, "AnimatedWeather", "*.zip")))
            paths.extend(glob(os.path.join(root, "AnimatedWeather", "packages", "*.zip")))
            # Ein ZIP gehört eigentlich neben den sets-Ordner. Wird es dort
            # versehentlich abgelegt, soll der Import es trotzdem finden.
            paths.extend(glob(os.path.join(root, "AnimatedWeather", "sets", "*.zip")))
        unique = []
        seen = set()
        for filename in sorted(paths):
            real = os.path.realpath(filename)
            if real not in seen and os.path.isfile(real):
                seen.add(real)
                unique.append(real)
        return unique

    def _extract_candidate(self, archive_filename, root, destination):
        prefix = root.rstrip("/") + "/" if root else ""
        with zipfile.ZipFile(archive_filename, "r") as archive:
            members = self._archive_members(archive)
            selected = 0
            for member, name in members:
                if member.is_dir() or (prefix and not name.startswith(prefix)):
                    continue
                relative = name[len(prefix):] if prefix else name
                if not relative or relative.startswith("../") or "/../" in relative:
                    continue
                allowed = relative in (
                    "mapping.json", "manifest.json", "LICENSE", "LICENSE.txt",
                    "LICENSE-NOTICE.txt", "README.md", "README_DE.txt", "VERSION.txt"
                )
                allowed = allowed or bool(re.match(r"^[^/\\\x00]+/a[0-9]+\.png$", relative, re.IGNORECASE))
                allowed = allowed or bool(re.match(r"^(?:[0-9]+|na)\.png$", relative, re.IGNORECASE))
                allowed = allowed or bool(re.match(r"^[^/\\\x00]+\.png$", relative, re.IGNORECASE))
                if not allowed:
                    continue
                target = os.path.join(destination, relative)
                parent = os.path.dirname(target)
                if not os.path.isdir(parent):
                    os.makedirs(parent)
                with archive.open(member, "r") as source, open(target, "wb") as output:
                    shutil.copyfileobj(source, output, DOWNLOAD_CHUNK_SIZE)
                selected += 1
            if not selected:
                raise IconsetError("Im ausgewählten ZIP-Ordner wurden keine Wetterbilder gefunden.")

    def _write_manifest(
        self,
        directory,
        iconset_id,
        label,
        license_text,
        local_only,
        layout,
        catalog_revision=None,
        package_sha256="",
        min_frames=None,
        max_frames=None,
    ):
        manifest = {
            "schema": 1,
            "id": iconset_id,
            "label": label,
            "license": license_text,
            "local_only": bool(local_only),
            "layout": layout,
        }
        if catalog_revision is not None:
            manifest["catalog_revision"] = catalog_revision
        if package_sha256:
            manifest["package_sha256"] = package_sha256
        if min_frames is not None:
            manifest["min_frames"] = int(min_frames)
        if max_frames is not None:
            manifest["max_frames"] = int(max_frames)
        with open(os.path.join(directory, "manifest.json"), "w", encoding="utf-8") as output:
            json.dump(manifest, output, ensure_ascii=False, indent=2, sort_keys=True)
            output.write("\n")

    def _replace_target(self, source, target):
        if not os.path.isdir(self.sets_base):
            os.makedirs(self.sets_base)
        backup = ""
        try:
            if os.path.lexists(target):
                if os.path.islink(target) or not os.path.isdir(target):
                    raise IconsetError("Der vorhandene Zielpfad ist unsicher.")
                backup = target + ".old-%d" % os.getpid()
                if os.path.lexists(backup):
                    raise IconsetError("Temporärer Sicherungsordner ist bereits vorhanden.")
                os.rename(target, backup)
            os.rename(source, target)
            if backup:
                shutil.rmtree(backup)
            self.invalidate_installed_cache()
        except Exception:
            if backup and os.path.isdir(backup) and not os.path.lexists(target):
                os.rename(backup, target)
            raise

    def import_local(self, archive_filename, candidate, label, overwrite=False, progress=None):
        progress = progress or (lambda text: None)
        label = (label or candidate.get("label") or "Lokales Iconset").strip()
        iconset_id = "local-%s" % safe_id(label)
        target = self.iconset_path(iconset_id)
        if os.path.exists(target) and not overwrite:
            raise IconsetError("Ein lokales Iconset mit diesem Namen ist bereits installiert.")
        self.ensure_storage()
        work = tempfile.mkdtemp(prefix=".local-import-", dir=self.sets_base)
        staging = os.path.join(work, iconset_id)
        os.makedirs(staging)
        try:
            progress("Lokales ZIP-Archiv wird sicher entpackt …")
            self._extract_candidate(archive_filename, candidate.get("root", ""), staging)
            progress("Wettercodes und Wetterbilder werden geprüft …")
            details = self.validate_directory(staging)
            self._write_manifest(
                staging,
                iconset_id,
                label,
                "Nur lokal / Lizenz nicht durch das Plugin geprüft",
                True,
                details["layout"],
                min_frames=details["min_frames"],
                max_frames=details["max_frames"],
            )
            progress("Lokales Iconset wird installiert …")
            self._replace_target(staging, target)
            return iconset_id
        finally:
            if os.path.isdir(work):
                shutil.rmtree(work)

    def _download(self, url, destination, expected_size, progress):
        if not url.startswith(RELEASE_BASE_URL):
            raise IconsetError("Unsichere Downloadadresse im Wetterkatalog.")
        request = Request(url, headers={"User-Agent": "AnimatedWeather/0.3"})
        total = 0
        try:
            response = urlopen(request, timeout=35)
            try:
                length = response.headers.get("Content-Length")
                if length and int(length) > MAX_ARCHIVE_SIZE:
                    raise IconsetError("Das Wetterpaket ist unerwartet groß.")
                with open(destination, "wb") as output:
                    while True:
                        chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_ARCHIVE_SIZE:
                            raise IconsetError("Das Wetterpaket überschreitet 30 MiB.")
                        output.write(chunk)
            finally:
                response.close()
        except IconsetError:
            raise
        except Exception as error:
            raise IconsetError("Download fehlgeschlagen: %s" % error)
        if total <= 0:
            raise IconsetError("GitHub lieferte eine leere Datei.")
        self._verify_size(destination, expected_size)
        progress("Download abgeschlossen: %s" % format_bytes(total))

    def _verify_size(self, filename, expected):
        if expected and os.path.getsize(filename) != int(expected):
            raise IconsetError("Die Dateigröße stimmt nicht mit dem Katalog überein.")

    def _verify_sha256(self, filename, expected):
        digest = hashlib.sha256()
        with open(filename, "rb") as source:
            while True:
                chunk = source.read(DOWNLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                digest.update(chunk)
        if digest.hexdigest().lower() != (expected or "").lower():
            raise IconsetError("SHA-256-Prüfung des Wetterpakets fehlgeschlagen.")

    def install_public(self, iconset_id, progress=None):
        progress = progress or (lambda text: None)
        entry = self.public_entry(iconset_id)
        package = self.package(entry)
        if not entry or not package:
            raise IconsetError("Für dieses Iconset fehlt ein freigegebenes Paket.")
        self.ensure_storage()
        work = tempfile.mkdtemp(prefix=".set-install-", dir=self.sets_base)
        staging = os.path.join(work, iconset_id)
        os.makedirs(staging)
        archive_filename = ""
        try:
            package_filename = package.get("file", "")
            if not package_filename or os.path.basename(package_filename) != package_filename:
                raise IconsetError("Ungültiger Dateiname im Wetterkatalog.")
            archive_handle, archive_filename = tempfile.mkstemp(
                prefix="animatedweather-", suffix=".zip", dir="/tmp"
            )
            os.close(archive_handle)
            progress("Wetterset wird von GitHub geladen …")
            self._download(
                RELEASE_BASE_URL + package_filename,
                archive_filename,
                package.get("bytes"),
                progress,
            )
            progress("SHA-256-Prüfsumme wird kontrolliert …")
            self._verify_sha256(archive_filename, package.get("sha256"))
            progress("Archiv wird sicher entpackt …")
            self._extract_candidate(archive_filename, package.get("archive_root", ""), staging)
            progress("Wettercodes und Wetterbilder werden geprüft …")
            details = self.validate_directory(staging)
            self._write_manifest(
                staging,
                iconset_id,
                entry.get("label", iconset_id),
                entry.get("license", "Unbekannt"),
                False,
                details["layout"],
                catalog_revision=entry.get("revision"),
                package_sha256=package.get("sha256", ""),
                min_frames=details["min_frames"],
                max_frames=details["max_frames"],
            )
            progress("Iconset wird installiert …")
            self._replace_target(staging, self.iconset_path(iconset_id))
            return iconset_id
        finally:
            if archive_filename and os.path.isfile(archive_filename):
                try:
                    os.remove(archive_filename)
                except OSError:
                    pass
            if os.path.isdir(work):
                shutil.rmtree(work)

    def remove(self, iconset_id):
        path = self.iconset_path(iconset_id)
        if not path or not os.path.isdir(path) or os.path.islink(path):
            raise IconsetError("Iconset wurde nicht gefunden oder ist unsicher.")
        shutil.rmtree(path)
        self.invalidate_installed_cache()
