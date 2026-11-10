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

from chaptr.cli import BuildError, build, init_project, main, substitute, theme_css


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
    assert "<title>chaptr documentation</title>" in rendered
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
        "files": ["chapter.md"], "variables": {"product": product}
    }), encoding="utf-8")
    return config


def test_classed_container(tmp_path):
    config = project(tmp_path / "project", "Alpha")
    source = (
        "# Notes\n\n::: note-panel toc=exclude\n"
        "## Panel heading\n\nA highlighted note.\n\n"
        "| Label | Value |\n| --- | --- |\n| Item | Example |\n\n"
        "### Detail\n\nA secondary heading.\n\n![Reference](reference.png)\n\n"
        "<script>unsafe()</script>\n:::\n\n## After the block\n"
    )
    (config.parent / "chapter.md").write_text(source, encoding="utf-8")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings["table_of_contents"] = True
    settings["toc_depth"] = 3
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    rendered = build(config).read_text(encoding="utf-8")
    assert '<div class="note-panel">' in rendered
    assert '<h2 id="panel-heading">Panel heading</h2>' in rendered
    assert '<h3 id="detail">Detail</h3>' in rendered
    assert 'A highlighted note.' in rendered
    assert '<table>' in rendered
    assert (config.parent / "reference.png").as_uri() in rendered
    assert '<script>' not in rendered
    assert '&lt;script&gt;unsafe()&lt;/script&gt;' in rendered
    assert 'href="#panel-heading"' not in rendered
    assert 'href="#detail"' not in rendered
    assert 'href="#after-the-block"' in rendered
    assert '</div>\n<h2 id="after-the-block">' in rendered
    assert '::: note-panel toc=exclude' not in rendered
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
    (themes / "company.css").write_text("h1 { color: red; }", encoding="utf-8")
    (config.parent / "styles.css").write_text("body { line-height: 1.9; }", encoding="utf-8")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings["theme"] = "company"
    settings["stylesheet"] = "styles.css"
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    rendered = build(config).read_text(encoding="utf-8")
    assert "color: red" in rendered
    assert rendered.index(".columns {") < rendered.index("color: red")
    assert rendered.index("line-height: 1.9") > rendered.index("color: red")
    base = build(config, theme="base").read_text(encoding="utf-8")
    assert "color: red" not in base
    assert "line-height: 1.9" in base


def test_base_is_the_only_bundled_theme_and_default(tmp_path):
    from importlib.resources import files

    bundled = files("chaptr").joinpath("themes")
    assert {path.name for path in bundled.iterdir() if path.name.endswith(".css")} == {"base.css"}
    config = project(tmp_path / "project", "Alpha")
    assert build(config).read_bytes() == build(config, theme="base").read_bytes()
    assert theme_css(config.parent, "base", None) == bundled.joinpath("base.css").read_text(encoding="utf-8")
    for removed in ("modern", "vintage"):
        with pytest.raises(BuildError, match="Unknown theme"):
            build(config, theme=removed)


def test_local_base_keeps_shared_foundation(tmp_path):
    themes = tmp_path / "themes"
    themes.mkdir()
    (themes / "base.css").write_text("body { font-size: 14pt; }", encoding="utf-8")
    css = theme_css(tmp_path, "base", None)
    assert css.count("@page {") == 1
    assert css.index("font-size: 12pt") < css.index("font-size: 14pt")


@pytest.mark.parametrize("layout,count", [
    ("columns", 2), ("columns columns-3", 3),
    ("columns columns-2-1", 2), ("columns columns-1-2", 2),
])
def test_layout_containers(layout, count, tmp_path):
    config = project(tmp_path / "project", "Alpha")
    (config.parent / "image.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="48">'
        '<rect width="80" height="48" fill="#ddd"/>'
        '<path d="M10 38L30 12L45 28L56 18L72 38Z" fill="#555"/></svg>',
        encoding="utf-8",
    )
    columns = "\n\n".join(
        f"::: column\n## Column {number + 1}\n\n**Content**\n\n"
        "A paragraph of ordinary Markdown that wraps to the available column width.\n\n"
        "| Item | Cost |\n| --- | ---: |\n| Rope | 5 |\n\n"
        "![Image](image.svg)\n:::" for number in range(count)
    )
    source = f":::: {layout}\n{columns}\n::::\n\n::: align-center\n![Image](image.svg)\n:::\n"
    (config.parent / "chapter.md").write_text(source, encoding="utf-8")
    rendered = build(config).read_text(encoding="utf-8")
    assert f'<div class="{layout}">' in rendered
    assert rendered.count('<div class="column">') == count
    assert rendered.count("<strong>Content</strong>") == count
    assert '<div class="align-center">' in rendered
    assert rendered.count("<table>") == count
    assert (config.parent / "image.svg").as_uri() in rendered
    assert build(config, "markdown").read_text(encoding="utf-8") == source


def test_nested_local_theme(tmp_path):
    config = project(tmp_path / "project", "Alpha")
    theme_directory = config.parent / "themes" / "roleplaying"
    theme_directory.mkdir(parents=True)
    (theme_directory / "roleplaying.css").write_text(
        "h1 { color: red; }", encoding="utf-8"
    )
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings["theme"] = "roleplaying"
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")

    rendered = build(config).read_text(encoding="utf-8")

    assert "h1 { color: red; }" in rendered


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
                                         ("toc_depth", 0), ("toc_depth", True), ("front_cover", 42),
                                         ("page_size", "A0"), ("page_size", 4), ("page_size", []),
                                         ("page_size", None), ("language", ""), ("language", 42),
                                         ("language", ["pl"]), ("language", 'pl" onload="bad')])
def test_invalid_document_options(field, value, tmp_path):
    config = project(tmp_path / "project", "Alpha")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings[field] = value
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    with pytest.raises(BuildError, match=field):
        build(config)


@pytest.mark.parametrize("size,width,height", [
    ("A3", 297, 420), ("A4", 210, 297), ("A5", 148, 210),
    ("Letter", 215.9, 279.4), ("Legal", 215.9, 355.6),
])
def test_page_dimensions_in_html(size, width, height, tmp_path):
    config = project(tmp_path / "project", "Alpha")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings["page_size"] = size
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    rendered = build(config).read_text(encoding="utf-8")
    assert f"--page-width: {width}mm" in rendered
    assert f"--page-height: {height}mm" in rendered


@pytest.mark.parametrize("language", [None, "en", "en-GB", "pl", "pl-PL"])
def test_language_specific_word_spacing(language, tmp_path):
    config = project(tmp_path / "project", "Alpha")
    source = (
        '# O domu\n\nA i o u w z domu. (W domu), "Z lasu".\n\n'
        'w **domu**, **z** lasu, o [mapie](https://example.test/z).\n\n'
        'w\nogrodzie\n\nw  \nogrodzie\n\n'
        '`w kodzie`\n\n```text\nz kodu\n```\n\n'
        '<https://example.test/z>\n\n![w obrazie](image.png)\n\n'
        'Table: O domu\n\n| Opis |\n| --- |\n| w domu |\n\n'
        'Przypis.[^note]\n\n[^note]: Z lasu.\n'
    )
    (config.parent / "chapter.md").write_text(source, encoding="utf-8")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings.update({"title": "O domu", "subtitle": "W ogrodzie", "author": "Jan z lasu",
                     "title_page": True, "table_of_contents": True})
    if language is not None:
        settings["language"] = language
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    rendered = build(config).read_text(encoding="utf-8")
    assert f'<html lang="{language or "en"}">' in rendered
    assert '<code>w kodzie</code>' in rendered
    assert '<code class="language-text">z kodu\n</code>' in rendered
    assert 'href="https://example.test/z"' in rendered
    assert '>https://example.test/z</a>' in rendered
    assert 'alt="w obrazie"' in rendered
    assert 'w<br />\nogrodzie' in rendered
    assert 'id="o-domu"' in rendered
    if language in {"pl", "pl-PL"}:
        assert 'A\xa0i\xa0o\xa0u\xa0w\xa0z\xa0domu.' in rendered
        assert '(W\xa0domu), &quot;Z\xa0lasu&quot;.' in rendered
        assert 'w\xa0<strong>domu</strong>, <strong>z</strong>\xa0lasu, o\xa0<a' in rendered
        assert '<p>w\xa0ogrodzie</p>' in rendered
        assert '<td>w\xa0domu</td>' in rendered
        assert 'Table 1. O\xa0domu' in rendered
        assert '>O\xa0domu</a>' in rendered
        assert '>W\xa0ogrodzie</p>' in rendered
        assert '>Jan z\xa0lasu</p>' in rendered
        assert 'Z\xa0lasu.' in rendered
    else:
        assert '\xa0' not in rendered
    assert build(config, "markdown").read_text(encoding="utf-8") == source


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