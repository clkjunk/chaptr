from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile


CATALOG_URL = "https://raw.githubusercontent.com/clkjunk/chaptr-themes/main/catalog.json"
MAX_CATALOG_SIZE = 1024 * 1024
MAX_ARCHIVE_SIZE = 25 * 1024 * 1024
MAX_UNPACKED_SIZE = 50 * 1024 * 1024
MAX_ARCHIVE_FILES = 300
THEME_ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
VERSION_PATTERN = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


class ThemeError(ValueError):
    pass


@dataclass(frozen=True)
class ThemeInfo:
    theme_id: str
    name: str
    description: str
    version: str
    license: str
    min_chaptr_version: str
    archive_url: str
    sha256: str


@dataclass(frozen=True)
class ThemeUpdate:
    theme_id: str
    installed_version: str
    available_version: str | None
    status: str


def _version_tuple(value: str, field: str) -> tuple[int, int, int]:
    match = VERSION_PATTERN.fullmatch(value)
    if not match:
        raise ThemeError(f"Invalid {field} '{value}'; expected a numeric x.y.z version.")
    return tuple(int(part) for part in match.groups())


def _chaptr_version() -> tuple[int, int, int]:
    try:
        installed = version("chaptr")
    except PackageNotFoundError as error:
        raise ThemeError("Cannot determine the installed Chaptr version.") from error
    return _version_tuple(installed, "installed Chaptr version")


def _fetch(url: str, max_bytes: int) -> bytes:
    if urlsplit(url).scheme != "https":
        raise ThemeError("Theme catalog and archive URLs must use HTTPS.")
    request = Request(url, headers={"User-Agent": "chaptr-theme-manager"})
    try:
        with urlopen(request, timeout=20) as response:
            if urlsplit(response.geturl()).scheme != "https":
                raise ThemeError("Theme downloads must remain on HTTPS.")
            content = response.read(max_bytes + 1)
    except (OSError, URLError) as error:
        raise ThemeError(f"Unable to download {url}: {error}") from error
    if len(content) > max_bytes:
        raise ThemeError(f"Download exceeds the {max_bytes}-byte size limit.")
    return content


def load_catalog() -> list[ThemeInfo]:
    try:
        catalog = json.loads(_fetch(CATALOG_URL, MAX_CATALOG_SIZE))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ThemeError("The Chaptr themes catalog is not valid UTF-8 JSON.") from error
    if not isinstance(catalog, dict) or type(catalog.get("schema_version")) is not int:
        raise ThemeError("The Chaptr themes catalog has an invalid schema version.")
    if catalog["schema_version"] != 1:
        raise ThemeError(f"Unsupported themes catalog version: {catalog['schema_version']}.")
    entries = catalog.get("themes")
    if not isinstance(entries, list):
        raise ThemeError("The themes catalog must contain a themes list.")

    result = []
    seen = set()
    chaptr_version = _chaptr_version()
    required = (
        "id", "name", "description", "version", "license",
        "min_chaptr_version", "archive_url", "sha256",
    )
    for entry in entries:
        if not isinstance(entry, dict) or any(
            not isinstance(entry.get(field), str) or not entry[field].strip()
            for field in required
        ):
            raise ThemeError("Each catalog entry must provide all required text fields.")
        theme_id = entry["id"]
        if not THEME_ID_PATTERN.fullmatch(theme_id):
            raise ThemeError(f"Invalid theme ID '{theme_id}'.")
        if theme_id in seen:
            raise ThemeError(f"Duplicate theme ID '{theme_id}' in catalog.")
        seen.add(theme_id)
        _version_tuple(entry["version"], f"version for theme '{theme_id}'")
        minimum = _version_tuple(entry["min_chaptr_version"], "minimum Chaptr version")
        if minimum > chaptr_version:
            raise ThemeError(
                f"Theme '{theme_id}' requires Chaptr {entry['min_chaptr_version']} or newer."
            )
        url = urlsplit(entry["archive_url"])
        if url.scheme != "https" or url.hostname != "github.com" or url.username or url.password:
            raise ThemeError(f"Theme '{theme_id}' must use an HTTPS GitHub release URL.")
        checksum = entry["sha256"]
        if not SHA256_PATTERN.fullmatch(checksum):
            raise ThemeError(f"Theme '{theme_id}' has an invalid SHA-256 checksum.")
        result.append(ThemeInfo(
            theme_id=theme_id,
            name=entry["name"],
            description=entry["description"],
            version=entry["version"],
            license=entry["license"],
            min_chaptr_version=entry["min_chaptr_version"],
            archive_url=entry["archive_url"],
            sha256=checksum,
        ))
    return sorted(result, key=lambda theme: theme.theme_id)


def get_theme(theme_id: str) -> ThemeInfo:
    if not THEME_ID_PATTERN.fullmatch(theme_id):
        raise ThemeError(f"Invalid theme ID '{theme_id}'.")
    for theme in load_catalog():
        if theme.theme_id == theme_id:
            return theme
    raise ThemeError(f"Theme '{theme_id}' is not in the Chaptr themes catalog.")


def _read_install_record(theme_directory: Path, theme_id: str) -> dict:
    record_path = theme_directory / ".chaptr-theme.json"
    if not record_path.is_file():
        raise ThemeError(f"Theme '{theme_id}' is not managed by Chaptr.")
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ThemeError(f"Installed metadata for theme '{theme_id}' is invalid.") from error
    if (
        not isinstance(record, dict)
        or record.get("schema_version") != 1
        or record.get("id") != theme_id
        or not isinstance(record.get("version"), str)
    ):
        raise ThemeError(f"Installed metadata for theme '{theme_id}' is invalid.")
    _version_tuple(record["version"], f"installed version for theme '{theme_id}'")
    return record


def installed_theme_version(project_root: Path, theme_id: str) -> str:
    if not THEME_ID_PATTERN.fullmatch(theme_id):
        raise ThemeError(f"Invalid theme ID '{theme_id}'.")
    record = _read_install_record(project_root / "themes" / theme_id, theme_id)
    return record["version"]


def check_updates(project_root: Path) -> list[ThemeUpdate]:
    catalog = {theme.theme_id: theme for theme in load_catalog()}
    themes_directory = project_root / "themes"
    if not themes_directory.is_dir():
        return []
    updates = []
    for theme_directory in sorted(themes_directory.iterdir()):
        if theme_directory.is_symlink() or not theme_directory.is_dir():
            continue
        record_path = theme_directory / ".chaptr-theme.json"
        if not record_path.is_file():
            continue
        record = _read_install_record(theme_directory, theme_directory.name)
        installed = record["version"]
        available = catalog.get(theme_directory.name)
        if available is None:
            status, available_version = "unlisted", None
        elif _version_tuple(available.version, "catalog version") > _version_tuple(
            installed, "installed version"
        ):
            status, available_version = "update", available.version
        elif _version_tuple(available.version, "catalog version") < _version_tuple(
            installed, "installed version"
        ):
            status, available_version = "local-newer", available.version
        else:
            status, available_version = "current", available.version
        updates.append(ThemeUpdate(
            theme_id=theme_directory.name,
            installed_version=installed,
            available_version=available_version,
            status=status,
        ))
    return updates


def _extract_archive(theme: ThemeInfo, archive: bytes, destination: Path) -> None:
    try:
        with ZipFile(BytesIO(archive)) as package:
            members = package.infolist()
            if len(members) > MAX_ARCHIVE_FILES:
                raise ThemeError("Theme archive contains too many files.")
            unpacked_size = sum(member.file_size for member in members)
            if unpacked_size > MAX_UNPACKED_SIZE:
                raise ThemeError("Theme archive exceeds the unpacked size limit.")
            seen = set()
            for member in members:
                name = member.filename
                if "\\" in name or "\x00" in name:
                    raise ThemeError("Theme archive contains an unsafe path.")
                path = PurePosixPath(name.rstrip("/"))
                parts = path.parts
                if path.is_absolute() or any(part in {".", ".."} or ":" in part for part in parts):
                    raise ThemeError("Theme archive contains an unsafe path.")
                if parts[:2] == ("themes", theme.theme_id):
                    parts = parts[2:]
                elif parts[:1] == (theme.theme_id,):
                    parts = parts[1:]
                if not parts:
                    continue
                if parts == (".chaptr-theme.json",):
                    raise ThemeError("Theme archive uses a reserved Chaptr metadata filename.")
                relative_path = Path(*parts)
                target = destination / relative_path
                if not target.resolve().is_relative_to(destination.resolve()):
                    raise ThemeError("Theme archive contains an unsafe path.")
                mode = member.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise ThemeError("Theme archive contains a symbolic link.")
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if parts in seen:
                    raise ThemeError("Theme archive contains duplicate file paths.")
                seen.add(parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with package.open(member) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)
    except (BadZipFile, RuntimeError) as error:
        raise ThemeError("Theme download is not a valid ZIP archive.") from error
    if not (destination / f"{theme.theme_id}.css").is_file():
        raise ThemeError(f"Theme archive is missing {theme.theme_id}.css.")
    if not (destination / "README.md").is_file() or not (destination / "LICENSE").is_file():
        raise ThemeError("Theme archive must include README.md and LICENSE.")


def _install(theme: ThemeInfo, project_root: Path, replace: bool) -> ThemeInfo:
    themes_directory = project_root / "themes"
    target = themes_directory / theme.theme_id
    if target.is_symlink():
        raise ThemeError(f"Refusing to replace symbolic-link theme path: {target}.")
    if target.exists():
        if not replace:
            raise ThemeError(
                f"Theme directory already exists: {target}. Use 'chaptr themes update' "
                "for an installed theme or choose another project directory."
            )
        _read_install_record(target, theme.theme_id)

    archive = _fetch(theme.archive_url, MAX_ARCHIVE_SIZE)
    archive_hash = sha256(archive).hexdigest()
    if archive_hash != theme.sha256:
        raise ThemeError(f"SHA-256 checksum mismatch for theme '{theme.theme_id}'.")

    themes_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{theme.theme_id}-", dir=themes_directory) as temporary:
        staging = Path(temporary) / theme.theme_id
        staging.mkdir()
        _extract_archive(theme, archive, staging)
        record = {
            "schema_version": 1,
            "id": theme.theme_id,
            "version": theme.version,
            "archive_sha256": archive_hash,
        }
        (staging / ".chaptr-theme.json").write_text(
            json.dumps(record, indent=2) + "\n", encoding="utf-8"
        )
        if target.exists():
            backup = Path(temporary) / "previous"
            target.rename(backup)
            try:
                staging.rename(target)
            except OSError:
                backup.rename(target)
                raise
            shutil.rmtree(backup)
        else:
            staging.rename(target)
    return theme


def add_theme(project_root: Path, theme_id: str) -> ThemeInfo:
    theme = get_theme(theme_id)
    return _install(theme, project_root, replace=False)


def update_theme(project_root: Path, theme_id: str) -> ThemeInfo:
    if not THEME_ID_PATTERN.fullmatch(theme_id):
        raise ThemeError(f"Invalid theme ID '{theme_id}'.")
    theme_directory = project_root / "themes" / theme_id
    record = _read_install_record(theme_directory, theme_id)
    theme = get_theme(theme_id)
    current = _version_tuple(record["version"], "installed version")
    latest = _version_tuple(theme.version, "catalog version")
    if latest < current:
        raise ThemeError(
            f"Installed theme '{theme_id}' is newer than the catalog; refusing to downgrade."
        )
    if latest == current:
        return theme
    return _install(theme, project_root, replace=True)