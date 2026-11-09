def test_markdown_footnotes(tmp_path):
    config = project(tmp_path / "project", "Alpha")
    (config.parent / "chapter.md").write_text(
        "# Notes\n\nA reference.[^source]\n\n[^source]: Supporting **detail**.\n",
        encoding="utf-8",
    )
    rendered = build(config).read_text(encoding="utf-8")
    assert 'class="footnote-ref"' in rendered
    assert 'id="fn1"' in rendered
    assert "Supporting <strong>detail</strong>." in rendered
    assert "[^source]" in build(config, "markdown").read_text(encoding="utf-8")
from pathlib import Path

import pytest
import yaml

from chaptr.cli import BuildError, build, init_project, main, substitute


@pytest.mark.parametrize("arguments, expected", [
    (["--help"], ["chaptr help", "build", "init", "Examples:"]),
    (["init", "--help"], ["DIRECTORY", "current directory", "never overwritten"]),
    (["build", "--help"], ["--config PATH", "default: html", "--theme NAME", "native libraries"]),
    (["help"], ["SYNOPSIS", "CONFIGURATION", "EXIT STATUS", "LIMITATIONS"]),
])
def test_cli_help_without_a_project(arguments, expected, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["chaptr", *arguments])
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
    arguments = ["chaptr", "init"] + ([directory] if directory else [])
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
    assert "<title>chaptr Documentation</title>" in rendered
    assert '<h1 id="user-workflow">User Workflow</h1>' in rendered
    assert '<h1 id="configuration-and-variables">Configuration and Variables</h1>' in rendered
    assert '<h1 id="roadmap">Roadmap</h1>' in rendered
    assert "# User Workflow" in build(config, "markdown").read_text(encoding="utf-8")


@pytest.mark.parametrize("filename", [
    "document.yaml", "README.md", "01-requirements.md", "02-workflow.md",
    "03-configuration.md", "04-themes.md", "05-pdf.md", "06-limitations.md",
    "07-roadmap.md", "styles.css", ".gitignore",
    "00-front-cover.md", "00-authors.md", "99-back-cover.md",
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
    monkeypatch.setattr("sys.argv", ["chaptr", "init"])
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


@pytest.mark.parametrize("section", ["Actions", "Spells", "Reactions", "Custom Abilities"])
def test_monster_container(tmp_path, section):
    config = project(tmp_path / "project", "Alpha")
    source = (
        "# Encounter\n\n::: monster\n## Example Creature\n\n*Medium humanoid*\n\n"
        "**AC:** 12  \n**HP:** 40\n\n| STR | DEX |\n| --- | --- |\n| 9 | 14 |\n\n"
        f"### {section}\n\n**Strike.** Deal damage.\n\n![Reference](reference.png)\n\n"
        "<script>unsafe()</script>\n:::\n\n## After the block\n"
    )
    (config.parent / "chapter.md").write_text(source, encoding="utf-8")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings["table_of_contents"] = True
    settings["toc_depth"] = 3
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    rendered = build(config).read_text(encoding="utf-8")
    assert '<article class="monster-card">' in rendered
    assert '<h2 id="example-creature">Example Creature</h2>' in rendered
    assert f'>{section}</h3>' in rendered
    assert '<strong>Strike.</strong> Deal damage.' in rendered
    assert '<table>' in rendered
    assert (config.parent / "reference.png").as_uri() in rendered
    assert '<script>' not in rendered
    assert '&lt;script&gt;unsafe()&lt;/script&gt;' in rendered
    assert 'href="#example-creature"' not in rendered
    assert 'href="#after-the-block"' in rendered
    assert '</article>\n<h2 id="after-the-block">' in rendered
    assert '::: monster' not in rendered
    assert source == build(config, "markdown").read_text(encoding="utf-8")


def test_independent_projects_from_other_directory(tmp_path, monkeypatch):
    first = project(tmp_path / "first", "Alpha")
    second = project(tmp_path / "second", "Beta")
    monkeypatch.chdir(tmp_path)
    assert build(first, "markdown").read_text(encoding="utf-8") == "# Alpha\n\n`$product` costs $20.\n"
    assert '<h1 id="beta">Beta</h1>' in build(second).read_text(encoding="utf-8")
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


def test_document_numbering_and_cross_chapter_footnotes(tmp_path):
    config = project(tmp_path / "project", "Alpha")
    root = config.parent
    (root / "chapter.md").write_text(
        "# Repeat\n\nA note.[^detail]\n\nTable: First **caption**\n\n| A |\n| --- |\n| 1 |\n",
        encoding="utf-8",
    )
    (root / "second.md").write_text(
        "# Repeat\n\n| B |\n| --- |\n| 2 |\n\nTable: Second caption\n\n[^detail]: Shared note.\n",
        encoding="utf-8",
    )
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings.update({"files": ["chapter.md", "second.md"], "table_of_contents": True})
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    rendered = build(config).read_text(encoding="utf-8")
    assert 'href="#repeat"' in rendered
    assert 'href="#repeat-2"' in rendered
    assert 'id="repeat-2"' in rendered
    assert '<caption style="caption-side: top">Table 1. First <strong>caption</strong></caption>' in rendered
    assert '<caption style="caption-side: bottom">Table 2. Second caption</caption>' in rendered
    assert "Shared note." in rendered
    assert rendered.count('id="fn1"') == 1
    settings["files"].reverse()
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    reordered = build(config).read_text(encoding="utf-8")
    assert 'Table 1. Second caption' in reordered
    assert 'Table 2. First <strong>caption</strong>' in reordered


def test_optional_document_pages(tmp_path):
    config = project(tmp_path / "project", "Alpha")
    root = config.parent
    (root / "chapter.md").write_text(
        "# $product\n\nA note.[^source]\n\n[^source]: Supporting detail.\n", encoding="utf-8"
    )
    for name in ("front", "authors", "back"):
        (root / f"{name}.md").write_text(f"# {name}\n\nPage content.\n", encoding="utf-8")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings.update({
        "title": "A & B", "subtitle": "A guide", "author": "An Author", "title_page": True,
        "table_of_contents": True, "front_cover": "front.md", "back_cover": "back.md",
        "author_section": "authors.md",
    })
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    rendered = build(config).read_text(encoding="utf-8")
    roles = ['class="front-cover document-page"', 'class="title-page document-page"',
             'class="author-section document-page"', 'class="contents document-page"',
             'class="chapter"', 'class="document-notes"', 'class="back-cover document-page"']
    positions = [rendered.index(role) for role in roles]
    assert positions == sorted(positions)
    assert "A &amp; B" in rendered
    assert "An Author" in rendered
    assert 'href="#authors"' not in rendered
    merged = build(config, "markdown").read_text(encoding="utf-8")
    assert merged.index("# front") < merged.index("# Alpha") < merged.index("# back")


@pytest.mark.parametrize("field,value", [("title_page", "yes"), ("table_of_contents", 1),
                                         ("toc_depth", 0), ("toc_depth", True), ("front_cover", 42)])
def test_invalid_document_options(field, value, tmp_path):
    config = project(tmp_path / "project", "Alpha")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings[field] = value
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    with pytest.raises(BuildError, match=field):
        build(config)


def test_heading_ids_do_not_collide_with_tables_or_notes(tmp_path):
    config = project(tmp_path / "project", "Alpha")
    (config.parent / "chapter.md").write_text(
        "# fn1\n\n# Table 1\n\nTable: Values\n\n| A |\n| --- |\n| 1 |\n\n"
        "A note.[^detail]\n\n[^detail]: Supporting text.\n", encoding="utf-8",
    )
    rendered = build(config).read_text(encoding="utf-8")
    assert '<h1 id="fn1-2">fn1</h1>' in rendered
    assert '<h1 id="table-1-2">Table 1</h1>' in rendered
    assert rendered.count('id="fn1"') == 1
    assert rendered.count('id="table-1"') == 1
    assert 'class="contents document-page"' not in rendered
    assert 'class="title-page document-page"' not in rendered


def test_caption_stays_in_its_source_file(tmp_path):
    config = project(tmp_path / "project", "Alpha")
    (config.parent / "chapter.md").write_text("| A |\n| --- |\n| 1 |\n", encoding="utf-8")
    (config.parent / "second.md").write_text("Table: Separate paragraph\n", encoding="utf-8")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings["files"].append("second.md")
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    rendered = build(config).read_text(encoding="utf-8")
    assert "<caption" not in rendered
    assert "<p>Table: Separate paragraph</p>" in rendered