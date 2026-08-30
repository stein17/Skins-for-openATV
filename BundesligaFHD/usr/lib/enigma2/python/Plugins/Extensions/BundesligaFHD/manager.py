# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import re
import shutil
import xml.etree.ElementTree as ET

from .constants import (
    CATEGORY_TITLES,
    DEFAULT_TEAM_TITLE,
    SKIN_BASE,
    STATE_ACTIVE_DIR,
    STATE_BASE,
)
from .teamassets import TeamAssetManager, TeamAssetError

TEAM_DIRNAME = "team_colors"
TEAM_LINK = "skin_10_team_profile.xml"
TEAM_SELECTION_PIXMAP = "select_54.png"
COLOR_OVERRIDE_FILE = "skin_20_user_colors.xml"
LEGACY_TEAM_LINKS = ("skin_user_team_colors.xml",)
SKINPART_FILENAME_ALIASES = {
    ("weather", "weather_5_Day _Details_Compact.xml"): "weather_5_Day_Details_Compact.xml",
}


def decode_skin_name(value):
    def repl(match):
        try:
            return chr(int(match.group(1), 16))
        except Exception:
            return match.group(0)

    return re.sub(r"#U([0-9a-fA-F]{4})", repl, value)


def safe_name(value):
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", value)
    return value.strip("_") or "skinpart"


def friendly_file_name(filename, category=None):
    name = os.path.splitext(os.path.basename(filename))[0]
    prefixes = ["skin_", "team_colors_"]
    if category:
        prefixes.extend((category + "_", "skin_" + category + "_"))
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if name.lower().startswith(prefix.lower()):
                name = name[len(prefix):]
                changed = True
    return decode_skin_name(name.replace("_", " ")).strip()


class SkinManager(object):
    """Manage active skin files in /etc/enigma2.

    The active mySkin directory lives below /etc/enigma2 so a normal OpenATV
    settings backup contains the selected team, generated color XML and all
    active skinpart links. The two historical skin directories are only links
    to this persistent location.
    """

    def __init__(self, skin_base=SKIN_BASE):
        self.skin_base = skin_base
        self.all_screens_dir = os.path.join(skin_base, "allScreens")
        self.team_dir = os.path.join(self.all_screens_dir, TEAM_DIRNAME)
        self.preview_dir = os.path.join(skin_base, "preview")
        self.legacy_my_skin_off = os.path.join(skin_base, "mySkin_off")
        self.legacy_my_skin = os.path.join(skin_base, "mySkin")
        self.state_base = STATE_BASE
        self.active_dir = STATE_ACTIVE_DIR
        catalog_path = os.path.join(skin_base, "team_assets", "catalog.json")
        self.assets = TeamAssetManager(skin_base=skin_base, catalog_path=catalog_path)
        self._prepare_directories()

    def _prepare_directories(self):
        if not os.path.isdir(self.state_base):
            os.makedirs(self.state_base)
        if not os.path.isdir(self.active_dir):
            os.makedirs(self.active_dir)

        # Migrate an existing installation before replacing the old paths.
        candidates = []
        for legacy in (self.legacy_my_skin_off, self.legacy_my_skin):
            if os.path.isdir(legacy) and not os.path.islink(legacy):
                candidates.append(legacy)
            elif os.path.islink(legacy):
                target = os.path.realpath(legacy)
                if os.path.isdir(target) and target != os.path.realpath(self.active_dir):
                    candidates.append(target)

        seen = set()
        for source in candidates:
            real = os.path.realpath(source)
            if real in seen or real == os.path.realpath(self.active_dir):
                continue
            seen.add(real)
            self._migrate_directory(real)

        for legacy in (self.legacy_my_skin_off, self.legacy_my_skin):
            self._replace_directory_with_link(legacy, self.active_dir)

    def _migrate_directory(self, source):
        try:
            names = os.listdir(source)
        except OSError:
            return
        for name in names:
            src = os.path.join(source, name)
            dst = os.path.join(self.active_dir, name)
            if os.path.lexists(dst):
                continue
            try:
                if os.path.islink(src):
                    os.symlink(os.readlink(src), dst)
                elif os.path.isfile(src):
                    shutil.copy2(src, dst)
            except OSError as error:
                print("[BundesligaFHDConfig] Migration failed for %s: %s" % (src, error))

    @staticmethod
    def _replace_directory_with_link(path_value, target):
        if os.path.islink(path_value):
            try:
                if os.path.realpath(path_value) == os.path.realpath(target):
                    return
                os.remove(path_value)
            except OSError:
                return
        elif os.path.isdir(path_value):
            try:
                # All relevant files have already been copied to the state dir.
                shutil.rmtree(path_value)
            except OSError as error:
                print("[BundesligaFHDConfig] Could not remove legacy directory %s: %s" % (path_value, error))
                return
        elif os.path.lexists(path_value):
            try:
                os.remove(path_value)
            except OSError:
                return

        try:
            os.symlink(target, path_value)
        except OSError as error:
            print("[BundesligaFHDConfig] Could not create link %s: %s" % (path_value, error))

    def list_teams(self):
        result = []
        if not os.path.isdir(self.team_dir):
            return result
        for filename in os.listdir(self.team_dir):
            if filename.startswith("team_colors_") and filename.endswith(".xml"):
                fullpath = os.path.join(self.team_dir, filename)
                result.append((fullpath, friendly_file_name(filename)))
        result.sort(key=lambda item: item[1].lower())
        return result

    def source_for_team_filename(self, filename):
        if not filename:
            return ""
        filename = os.path.basename(filename)
        direct = os.path.join(self.team_dir, filename)
        if os.path.isfile(direct):
            return direct

        wanted = decode_skin_name(filename).lower()
        for fullpath, _title in self.list_teams():
            if decode_skin_name(os.path.basename(fullpath)).lower() == wanted:
                return fullpath
        return ""

    def current_team(self):
        candidates = [os.path.join(self.active_dir, TEAM_LINK)]
        candidates.extend(os.path.join(self.active_dir, item) for item in LEGACY_TEAM_LINKS)
        for linkpath in candidates:
            if os.path.lexists(linkpath):
                target = os.path.realpath(linkpath)
                if target.endswith(".xml") and os.path.exists(target):
                    return target
        return ""

    def current_team_filename(self):
        current = self.current_team()
        return os.path.basename(current) if current else ""

    def team_uses_special_config_style(self, source=None):
        source = source or self.current_team()
        if not source or not os.path.isfile(source):
            return False

        try:
            root = ET.parse(source).getroot()
            for screen in root.iter("screen"):
                if screen.get("name") == "setup_config":
                    return True
            return False
        except (ET.ParseError, IOError, OSError) as error:
            print("[BundesligaFHDConfig] Team profile XML check failed: %s" % error)

        try:
            with open(source, "r", encoding="utf-8", errors="ignore") as handle:
                xml_data = handle.read()
            xml_data = re.sub(r"<!--.*?-->", "", xml_data, flags=re.S)
            pattern = r"<screen\b[^>]*\bname\s*=\s*[\"\']setup_config[\"\']"
            return re.search(pattern, xml_data, flags=re.I) is not None
        except (IOError, OSError, UnicodeError) as error:
            print("[BundesligaFHDConfig] Team profile fallback check failed: %s" % error)
            return False

    def default_team(self, teams=None):
        teams = teams if teams is not None else self.list_teams()
        wanted = DEFAULT_TEAM_TITLE.lower()
        for path_value, title in teams:
            if decode_skin_name(title).lower() == wanted:
                return path_value
        return teams[0][0] if teams else ""

    def selection_pixmap_path(self):
        """Return the stable path used by all setup_config screens."""
        return os.path.join(self.assets.verein_dir, TEAM_SELECTION_PIXMAP)

    def selection_pixmap_for_entry(self, entry):
        if not entry:
            return ""
        return os.path.join(self.assets.team_path(entry), TEAM_SELECTION_PIXMAP)

    def selection_pixmap_is_current(self, entry):
        source = self.selection_pixmap_for_entry(entry)
        destination = self.selection_pixmap_path()
        return bool(
            source
            and os.path.isfile(source)
            and os.path.islink(destination)
            and os.path.realpath(destination) == os.path.realpath(source)
        )

    def apply_team(self, source):
        if not source or not os.path.isfile(source):
            raise IOError("Teamprofil nicht gefunden: %s" % source)
        entry = self.assets.team_for_profile(source)
        if not entry:
            raise TeamAssetError("Der Verein wurde im Vereinskatalog nicht gefunden.")
        if not self.assets.is_installed(entry):
            raise TeamAssetError("Die Bilder für %s sind noch nicht installiert." % entry["title"])
        selection_source = self.selection_pixmap_for_entry(entry)
        if not os.path.isfile(selection_source):
            raise TeamAssetError("Das Auswahlbild für %s fehlt." % entry["title"])

        # The skin always uses Verein/select_54.png.  Only this link changes,
        # so every club can keep its own image inside its asset directory.
        self._replace_symlink(selection_source, self.selection_pixmap_path())
        self._replace_symlink(source, os.path.join(self.active_dir, TEAM_LINK))
        for legacy in LEGACY_TEAM_LINKS:
            legacy_path = os.path.join(self.active_dir, legacy)
            if os.path.islink(legacy_path):
                try:
                    os.remove(legacy_path)
                except OSError:
                    pass

    def color_override_path(self):
        return os.path.join(self.active_dir, COLOR_OVERRIDE_FILE)

    def color_override_exists(self):
        output = self.color_override_path()
        return os.path.exists(output) or os.path.islink(output)

    def write_color_overrides(self, overrides):
        output = self.color_override_path()
        if not overrides:
            self._remove(output)
            return

        lines = ["<skin>", "  <colors>"]
        for xml_name in sorted(overrides):
            value = overrides[xml_name]
            lines.append('    <color name="%s" value="%s" />' % (xml_name, value))
        lines.extend(("  </colors>", "</skin>", ""))
        temp = output + ".tmp"
        with open(temp, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines))
        os.replace(temp, output)

    def preview_for_source(self, source, category=None):
        if not source or source == "default":
            return ""
        base = os.path.splitext(os.path.basename(source))[0]
        candidates = [
            os.path.join(self.preview_dir, "preview_%s.png" % base),
            os.path.join(self.preview_dir, "%s.png" % base),
        ]
        if category:
            candidates.extend((
                os.path.join(self.preview_dir, category, "preview_%s.png" % base),
                os.path.join(self.preview_dir, category, "%s.png" % base),
            ))
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate
        return ""

    def discover_categories(self):
        result = []
        if not os.path.isdir(self.all_screens_dir):
            return result
        for dirname in os.listdir(self.all_screens_dir):
            if dirname == TEAM_DIRNAME:
                continue
            fullpath = os.path.join(self.all_screens_dir, dirname)
            if not os.path.isdir(fullpath):
                continue
            xml_files = [item for item in os.listdir(fullpath) if item.endswith(".xml")]
            if not xml_files:
                continue
            title = CATEGORY_TITLES.get(dirname.lower(), decode_skin_name(dirname.replace("_", " ")).title())
            result.append((dirname, title))
        result.sort(key=lambda item: item[1].lower())
        return result

    def category_choices(self, category):
        directory = os.path.join(self.all_screens_dir, category)
        choices = [("default", "Vereins-/Skinstandard")]
        if os.path.isdir(directory):
            files = sorted(
                (item for item in os.listdir(directory) if item.endswith(".xml")),
                key=lambda item: friendly_file_name(item, category).lower()
            )
            for filename in files:
                fullpath = os.path.join(directory, filename)
                choices.append((fullpath, friendly_file_name(filename, category)))
        return choices

    def source_for_category_filename(self, category, filename):
        if not category or not filename:
            return ""
        filename = os.path.basename(filename)
        filename = SKINPART_FILENAME_ALIASES.get((category, filename), filename)
        direct = os.path.join(self.all_screens_dir, category, filename)
        return direct if os.path.isfile(direct) else ""

    def category_link(self, category):
        return os.path.join(self.active_dir, "skin_50_%s.xml" % safe_name(category))

    def active_category_value(self, category):
        linkpath = self.category_link(category)
        if os.path.lexists(linkpath):
            target = os.path.realpath(linkpath)
            if os.path.isfile(target):
                return target
        return "default"

    def active_categories(self):
        result = {}
        for category, _title in self.discover_categories():
            target = self.active_category_value(category)
            if target != "default":
                result[category] = os.path.basename(target)
        return result

    def apply_category(self, category, source):
        linkpath = self.category_link(category)
        if source == "default" or not source:
            self._remove(linkpath)
            return
        if not os.path.isfile(source):
            raise IOError("Skinpart nicht gefunden: %s" % source)
        self._replace_symlink(source, linkpath)

    def restore_from_values(self, team_filename, overrides, skinparts):
        """Recreate runtime files and return a missing saved team entry.

        A clean flash restores the saved profile name before its image pack is
        available. In that case Bayern is activated as a temporary fallback;
        the saved profile itself is deliberately not overwritten.
        """
        changed = False
        missing_team = None

        team_source = self.source_for_team_filename(team_filename)
        requested_entry = self.assets.team_for_profile(team_source or team_filename)
        if requested_entry and not self.assets.is_installed(requested_entry):
            missing_team = requested_entry
            team_source = self.default_team()
        elif not team_source and not self.current_team():
            team_source = self.default_team()
        if team_source:
            expected = os.path.realpath(team_source)
            current = os.path.realpath(self.current_team()) if self.current_team() else ""
            entry = self.assets.team_for_profile(team_source)
            if current != expected or not self.selection_pixmap_is_current(entry):
                self.apply_team(team_source)
                changed = True

        before_override = ""
        output = self.color_override_path()
        if os.path.isfile(output):
            try:
                with open(output, "r", encoding="utf-8", errors="ignore") as handle:
                    before_override = handle.read()
            except OSError:
                pass
        self.write_color_overrides({} if missing_team else overrides)
        after_override = ""
        if os.path.isfile(output):
            try:
                with open(output, "r", encoding="utf-8", errors="ignore") as handle:
                    after_override = handle.read()
            except OSError:
                pass
        if before_override != after_override:
            changed = True

        for category, filename in skinparts.items():
            source = self.source_for_category_filename(category, filename)
            if not source:
                continue
            current = self.active_category_value(category)
            if current == "default" or os.path.realpath(current) != os.path.realpath(source):
                self.apply_category(category, source)
                changed = True

        return missing_team

    @staticmethod
    def _remove(filename):
        if os.path.lexists(filename):
            if os.path.isdir(filename) and not os.path.islink(filename):
                raise IOError("Verzeichnis wird nicht entfernt: %s" % filename)
            os.remove(filename)

    def _replace_symlink(self, source, destination):
        temp = "%s.tmp-%d" % (destination, os.getpid())
        self._remove(temp)
        try:
            os.symlink(source, temp)
            os.replace(temp, destination)
        except Exception:
            self._remove(temp)
            raise
