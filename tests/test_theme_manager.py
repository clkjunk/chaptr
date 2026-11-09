from hashlib import sha256
from io import BytesIO
import json
from zipfile import ZipFile

import pytest

from chaptr import theme_manager
from chaptr.cli import main


def archive(theme_id: str, css: str) -> bytes:
    destination = BytesIO()
    with ZipFile(destination, "w") as package:
        package.writestr(f"{theme_id}.css", css)
        package.writestr("README.md", f"# {theme_id}\n")
        package.writestr("LICENSE", "MIT License\n")
    return destination.getvalue()


def catalog(archive_bytes: bytes, version: str) -> bytes:
    return json.dumps({
        "schema_version": 1,
        "themes": [{
            "id": "roleplaying",
            "name": "Roleplaying",
            "description": "A theme for fantasy roleplaying documents.",
            "version": version,
            "license": "MIT",
            "min_chaptr_version": "0.1.1",
            "archive_url": "https://github.com/clkjunk/chaptr-themes/releases/download/roleplaying/theme.zip",
            "sha256": sha256(archive_bytes).hexdigest(),
        }],
    }).encode("utf-8")


def mock_fetch(monkeypatch, archive_bytes: bytes, catalog_bytes: bytes) -> None:
    def fetch(url: str, max_bytes: int) -> bytes:
        if url == theme_manager.CATALOG_URL:
            return catalog_bytes
        return archive_bytes

    monkeypatch.setattr(theme_manager, "_fetch", fetch)


def test_add_theme_installs_files_and_records_version(tmp_path, monkeypatch):
    package = archive("roleplaying", "body { color: red; }")
    mock_fetch(monkeypatch, package, catalog(package, "1.0.0"))

    installed = theme_manager.add_theme(tmp_path, "roleplaying")

    theme_directory = tmp_path / "themes" / "roleplaying"
    assert installed.version == "1.0.0"
    assert (theme_directory / "roleplaying.css").read_text(encoding="utf-8") == (
        "body { color: red; }"
    )
    assert (theme_directory / "README.md").is_file()
    metadata = json.loads((theme_directory / ".chaptr-theme.json").read_text(encoding="utf-8"))
    assert metadata["version"] == "1.0.0"


def test_check_and_update_theme_replaces_installed_files(tmp_path, monkeypatch):
    stylesheet = tmp_path / "styles.css"
    stylesheet.write_text("body { color: green; }", encoding="utf-8")
    initial_package = archive("roleplaying", "body { color: red; }")
    mock_fetch(monkeypatch, initial_package, catalog(initial_package, "1.0.0"))
    theme_manager.add_theme(tmp_path, "roleplaying")

    updated_package = archive("roleplaying", "body { color: blue; }")
    mock_fetch(monkeypatch, updated_package, catalog(updated_package, "1.1.0"))
    available = theme_manager.check_updates(tmp_path)

    assert [(item.theme_id, item.installed_version, item.available_version) for item in available] == [
        ("roleplaying", "1.0.0", "1.1.0")
    ]
    updated = theme_manager.update_theme(tmp_path, "roleplaying")

    assert updated.version == "1.1.0"
    assert (tmp_path / "themes" / "roleplaying" / "roleplaying.css").read_text(
        encoding="utf-8"
    ) == "body { color: blue; }"
    assert stylesheet.read_text(encoding="utf-8") == "body { color: green; }"


def test_add_theme_rejects_archive_path_traversal(tmp_path, monkeypatch):
    destination = BytesIO()
    with ZipFile(destination, "w") as package:
        package.writestr("roleplaying.css", "body { color: red; }")
        package.writestr("../outside.css", "body { color: black; }")
    payload = destination.getvalue()
    mock_fetch(monkeypatch, payload, catalog(payload, "1.0.0"))

    with pytest.raises(theme_manager.ThemeError, match="unsafe path"):
        theme_manager.add_theme(tmp_path, "roleplaying")

    assert not (tmp_path / "outside.css").exists()
    assert not (tmp_path / "themes" / "roleplaying").exists()


def test_add_theme_rejects_checksum_mismatch(tmp_path, monkeypatch):
    package = archive("roleplaying", "body { color: red; }")
    different_package = archive("roleplaying", "body { color: black; }")
    mock_fetch(monkeypatch, package, catalog(different_package, "1.0.0"))

    with pytest.raises(theme_manager.ThemeError, match="checksum mismatch"):
        theme_manager.add_theme(tmp_path, "roleplaying")

    assert not (tmp_path / "themes" / "roleplaying").exists()


def test_add_theme_preserves_unmanaged_local_theme(tmp_path, monkeypatch):
    theme_directory = tmp_path / "themes" / "roleplaying"
    theme_directory.mkdir(parents=True)
    stylesheet = theme_directory / "roleplaying.css"
    stylesheet.write_text("/* local theme */", encoding="utf-8")
    package = archive("roleplaying", "body { color: red; }")
    mock_fetch(monkeypatch, package, catalog(package, "1.0.0"))

    with pytest.raises(theme_manager.ThemeError, match="already exists"):
        theme_manager.add_theme(tmp_path, "roleplaying")

    assert stylesheet.read_text(encoding="utf-8") == "/* local theme */"


def test_themes_list_reports_empty_catalog(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["chaptr", "themes", "list"])
    monkeypatch.setattr(theme_manager, "load_catalog", lambda: [])

    assert main() == 0
    assert "No community themes are currently available." in capsys.readouterr().out