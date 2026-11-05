from pathlib import Path

import pytest
import yaml

from mdoc.cli import BuildError, build, init_project, main, substitute


@pytest.mark.parametrize("arguments, expected", [
    (["--help"], ["mdoc help", "build", "init", "Examples:"]),
    (["init", "--help"], ["DIRECTORY", "current directory", "never overwritten"]),
    (["build", "--help"], ["--config PATH", "default: html", "--theme NAME", "native libraries"]),
    (["help"], ["SYNOPSIS", "CONFIGURATION", "EXIT STATUS", "LIMITATIONS"]),
])
def test_cli_help_without_a_project(arguments, expected, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["mdoc", *arguments])
    if arguments == ["help"]:
        assert main() == 0
    else:
        with pytest.raises(SystemExit) as error:
            main()
        assert error.value.code == 0
    captured = capsys.readouterr()
    assert not captured.err
    for text in expected:
        assert text in captured.out


@pytest.mark.parametrize("directory", [None, "nested/My Document"])
def test_init_cli_creates_buildable_project(directory, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    arguments = ["mdoc", "init"] + ([directory] if directory else [])
    monkeypatch.setattr("sys.argv", arguments)
    assert main() == 0
    root = tmp_path / directory if directory else tmp_path
    config = root / "document.yaml"
    assert "Initialized project" in capsys.readouterr().out
    assert (root / "styles.css").is_file()
    assert (root / ".gitignore").read_text(encoding="utf-8") == "build/\n"
    assert not (root / "build").exists()
    documentation = Path(__file__).resolve().parents[1] / "docs"
    for source in documentation.iterdir():
        if source.is_file() and source.suffix in {".md", ".yaml", ".css"}:
            assert (root / source.name).read_bytes() == source.read_bytes()
    rendered = build(config).read_text(encoding="utf-8")
    assert "<title>mdoc Documentation</title>" in rendered
    assert "<h1>User Workflow</h1>" in rendered
    assert "<h1>Configuration and Variables</h1>" in rendered
    assert "<h1>Roadmap</h1>" in rendered
    assert "# User Workflow" in build(config, "markdown").read_text(encoding="utf-8")


@pytest.mark.parametrize("filename", [
    "document.yaml", "README.md", "01-requirements.md", "02-workflow.md",
    "03-configuration.md", "04-themes.md", "05-pdf.md", "06-limitations.md",
    "07-roadmap.md", "styles.css", ".gitignore",
])
def test_init_refuses_collisions_before_writing(filename, tmp_path):
    existing = tmp_path / filename
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("Keep my content", encoding="utf-8")
    with pytest.raises(BuildError, match="Refusing to overwrite"):
        init_project(tmp_path)
    assert existing.read_text(encoding="utf-8") == "Keep my content"
    assert [path for path in tmp_path.rglob("*") if path.is_file()] == [existing]


def test_init_keeps_unrelated_files_and_reports_repeat_init(tmp_path, monkeypatch, capsys):
    existing = tmp_path / "notes.md"
    existing.write_text("Personal notes", encoding="utf-8")
    init_project(tmp_path)
    assert existing.read_text(encoding="utf-8") == "Personal notes"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["mdoc", "init"])
    assert main() == 1
    captured = capsys.readouterr()
    assert "Refusing to overwrite" in captured.err
    assert not captured.out


@pytest.mark.parametrize("blocked_path", ["project", "project/document.yaml"])
def test_init_rejects_file_as_directory(blocked_path, tmp_path):
    existing = tmp_path / blocked_path
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("Keep my content", encoding="utf-8")
    with pytest.raises(BuildError):
        init_project(tmp_path / "project")
    assert existing.read_text(encoding="utf-8") == "Keep my content"
    assert [path for path in tmp_path.rglob("*") if path.is_file()] == [existing]


def project(root: Path, product: str) -> Path:
    root.mkdir()
    (root / "chapter.md").write_text("# $product\n\n`$product` costs $$20.\n", encoding="utf-8")
    config = root / "document.yaml"
    config.write_text(yaml.safe_dump({
        "files": ["chapter.md"], "variables": {"product": product}, "theme": "modern"
    }), encoding="utf-8")
    return config


def test_independent_projects_from_other_directory(tmp_path, monkeypatch):
    first = project(tmp_path / "first", "Alpha")
    second = project(tmp_path / "second", "Beta")
    monkeypatch.chdir(tmp_path)
    assert build(first, "markdown").read_text(encoding="utf-8") == "# Alpha\n\n`$product` costs $20.\n"
    assert "<h1>Beta</h1>" in build(second).read_text(encoding="utf-8")
    assert build(first).parent == first.parent / "build"


def test_local_theme_and_extra_stylesheet(tmp_path):
    config = project(tmp_path / "project", "Alpha")
    themes = config.parent / "themes"
    themes.mkdir()
    (themes / "modern.css").write_text("h1 { color: red; }", encoding="utf-8")
    (config.parent / "styles.css").write_text("body { line-height: 1.9; }", encoding="utf-8")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings["stylesheet"] = "styles.css"
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    rendered = build(config).read_text(encoding="utf-8")
    assert "color: red" in rendered
    assert "#146454" not in rendered
    assert rendered.index("line-height: 1.9") > rendered.index("color: red")
    assert "#632c35" in build(config, theme="vintage").read_text(encoding="utf-8")


def test_chapter_relative_images(tmp_path):
    config = project(tmp_path / "project", "Alpha")
    chapters = config.parent / "chapters"
    chapters.mkdir()
    (chapters / "notes.md").write_text("# Notes\n\n![Record](record.png)\n", encoding="utf-8")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings["files"] = ["chapters/notes.md"]
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    assert (chapters / "record.png").as_uri() in build(config).read_text(encoding="utf-8")


def test_variables_preserve_code_and_report_location():
    source = "# $name\n\n```text\n$missing\n```\n\n    $missing\n\n`$missing`\n"
    assert "$missing" in substitute(source, {"name": "Example"}, Path("chapter.md"))
    with pytest.raises(BuildError, match=r"chapter.md:2: undefined variable \$missing"):
        substitute("# Title\n$missing", {}, Path("chapter.md"))


def test_invalid_configuration_and_unknown_theme(tmp_path):
    config = project(tmp_path / "project", "Alpha")
    with pytest.raises(BuildError, match="Unknown theme"):
        build(config, theme="missing")
    config.write_text("files: chapter.md\n", encoding="utf-8")
    with pytest.raises(BuildError, match="nonempty list"):
        build(config)