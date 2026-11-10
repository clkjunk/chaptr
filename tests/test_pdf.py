from io import BytesIO
import re

import pytest
import yaml
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

from chaptr.cli import BuildError, build
from chaptr.pdf import CoverError, merge_covers
from test_build import project


def pdf_bytes(labels, width=595.28, height=841.89, password=None):
    writer = PdfWriter()
    for label in labels:
        page = writer.add_blank_page(width=width, height=height)
        page[NameObject("/TestLabel")] = TextStringObject(label)
    writer.add_metadata({"/Title": "Sample document"})
    if password:
        writer.encrypt(password)
    destination = BytesIO()
    writer.write(destination)
    return destination.getvalue()


@pytest.mark.parametrize("roles", [("front_cover",), ("back_cover",), ("front_cover", "back_cover")])
def test_merge_pdf_covers_preserves_pages(roles, tmp_path):
    covers = {}
    for role in roles:
        path = tmp_path / f"{role}.pdf"
        path.write_bytes(pdf_bytes([role]))
        covers[role] = path
    body = pdf_bytes(["first content page", "second content page"])
    result = PdfReader(BytesIO(merge_covers(body, covers)))
    expected = (["front_cover"] if "front_cover" in roles else [])
    expected += ["first content page", "second content page"]
    expected += (["back_cover"] if "back_cover" in roles else [])
    assert [page["/TestLabel"] for page in result.pages] == expected
    assert result.metadata.title == "Sample document"
    for role, path in covers.items():
        assert path.read_bytes() == pdf_bytes([role])


@pytest.mark.parametrize("kind,message", [
    ("multiple", "exactly one page"), ("empty", "exactly one page"),
    ("size", "does not match"), ("encrypted", "encrypted"),
    ("broken", "cannot read PDF cover"), ("missing", "cannot read PDF cover"),
])
def test_invalid_pdf_covers(kind, message, tmp_path):
    path = tmp_path / "cover.pdf"
    if kind == "multiple":
        path.write_bytes(pdf_bytes(["front", "another page"]))
    elif kind == "empty":
        path.write_bytes(pdf_bytes([]))
    elif kind == "size":
        path.write_bytes(pdf_bytes(["front"], width=612, height=792))
    elif kind == "encrypted":
        path.write_bytes(pdf_bytes(["front"], password="test-password"))
    elif kind == "broken":
        path.write_bytes(b"not a PDF")
    with pytest.raises(CoverError, match=message):
        merge_covers(pdf_bytes(["body"]), {"front_cover": path})


@pytest.mark.parametrize("format_name", ["html", "markdown"])
def test_non_pdf_builds_omit_pdf_covers(format_name, tmp_path):
    config = project(tmp_path / "project", "Alpha")
    with config.open("a", encoding="utf-8") as destination:
        destination.write("front_cover: missing-front.pdf\nback_cover: missing-back.PDF\n")
    rendered = build(config, format_name).read_text(encoding="utf-8")
    assert "Alpha" in rendered
    assert "front-cover document-page" not in rendered
    assert "back-cover document-page" not in rendered


def test_pdf_cover_cannot_be_output_file(tmp_path):
    config = project(tmp_path / "project", "Alpha")
    with config.open("a", encoding="utf-8") as destination:
        destination.write("front_cover: build/document.pdf\n")
    with pytest.raises(BuildError, match="cannot also be the output"):
        build(config, "pdf")


@pytest.fixture
def weasyprint_html():
    try:
        from weasyprint import HTML
    except (ImportError, OSError):
        pytest.skip("WeasyPrint and its native libraries are required for PDF integration tests")
    return HTML


def test_pdf_cover_build_preserves_contents_and_links(tmp_path, weasyprint_html):
    config = project(tmp_path / "project", "Alpha")
    root = config.parent
    for role, label in (("front", "External front cover"), ("back", "External back cover")):
        weasyprint_html(string=f"<style>@page {{ size: A4; margin: 0; }}</style><h1>{label}</h1>").write_pdf(root / f"{role}.pdf")
    (root / "chapter.md").write_text("# First chapter\n\nFirst content marker.\n", encoding="utf-8")
    (root / "second.md").write_text("# Second chapter\n\nSecond content marker.\n", encoding="utf-8")
    with config.open("a", encoding="utf-8") as destination:
        destination.write(
            "front_cover: front.pdf\nback_cover: back.pdf\ntitle_page: true\n"
            "table_of_contents: true\ntoc_depth: 1\n"
        )
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings["files"].append("second.md")
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    result = PdfReader(build(config, "pdf"))
    texts = [page.extract_text() for page in result.pages]
    assert len(texts) == 6
    assert "External front cover" in texts[0]
    assert "External back cover" in texts[-1]
    assert "First content marker" in texts[3]
    assert "Second content marker" in texts[4]
    assert re.search(r"First chapter[.\s]*2", texts[2]), texts[2]
    assert result.get_destination_page_number(result.named_destinations["first-chapter"]) == 3
    assert result.get_destination_page_number(result.named_destinations["second-chapter"]) == 4
    assert any(
        annotation.get_object().get("/Dest") == "first-chapter"
        for annotation in result.pages[2].get("/Annots", [])
    )


@pytest.mark.parametrize("front_cover", [None, "markdown", "pdf"])
@pytest.mark.parametrize("title_page", [False, True])
@pytest.mark.parametrize("authors", [False, True])
def test_pdf_page_numbers_start_after_front_matter(front_cover, title_page, authors, tmp_path, weasyprint_html):
    config = project(tmp_path / "project", "Alpha")
    root = config.parent
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings.update({"title_page": title_page, "table_of_contents": True})
    if front_cover == "pdf":
        weasyprint_html(string="<style>@page { size: A4; margin: 0; }</style><h1>Front cover</h1>").write_pdf(root / "front.pdf")
        settings["front_cover"] = "front.pdf"
    elif front_cover == "markdown":
        (root / "front.md").write_text("# Front cover\n", encoding="utf-8")
        settings["front_cover"] = "front.md"
    if authors:
        (root / "authors.md").write_text("# Authors\n\nAuthor details.\n", encoding="utf-8")
        settings["author_section"] = "authors.md"
    (root / "back.md").write_text("# Back cover\n", encoding="utf-8")
    settings["back_cover"] = "back.md"
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    result = PdfReader(build(config, "pdf"))
    texts = [page.extract_text().strip() for page in result.pages]
    first_numbered = int(front_cover is not None) + int(title_page)
    for text in texts[:first_numbered]:
        assert not re.search(r"\n\d+$", text), text
    for number, text in enumerate(texts[first_numbered:-1], 1):
        assert text.splitlines()[-1] == str(number), text
    assert texts[-1] == "Back cover"
    if authors:
        assert texts[first_numbered].startswith("Authors")
    contents = texts[first_numbered + int(authors)]
    assert re.search(rf"Alpha[.\s]*{2 + int(authors)}", contents), contents


def test_pdf_page_number_customization(tmp_path, weasyprint_html):
    config = project(tmp_path / "project", "Alpha")
    document = weasyprint_html(filename=str(build(config))).render()
    page = document.pages[0]
    footer = next(
        box for box in page._page_box.descendants()
        if getattr(box, "at_keyword", None) == "@bottom-right"
    )
    number = next(box for box in footer.descendants() if getattr(box, "text", None) == "1")
    assert number.position_x > page.width / 2
    assert number.position_y > page.height - 20 * 96 / 25.4
    (config.parent / "styles.css").write_text(
        ':root { --page-number-content: "Page " counter(page); }', encoding="utf-8"
    )
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings["stylesheet"] = "styles.css"
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    assert PdfReader(build(config, "pdf")).pages[0].extract_text().strip().endswith("Page 1")
    (config.parent / "styles.css").write_text(
        ':root { --page-number-content: none; }', encoding="utf-8"
    )
    assert not re.search(r"\n\d+$", PdfReader(build(config, "pdf")).pages[0].extract_text().strip())


def test_contents_links_have_no_underline(tmp_path, weasyprint_html):
    config = project(tmp_path / "project", "Alpha")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings["table_of_contents"] = True
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    document = weasyprint_html(filename=str(build(config))).render()
    links = [box for box in document.pages[0]._page_box.descendants() if box.element_tag == "a"]
    assert links
    assert all("underline" not in box.style["text_decoration_line"] for box in links)


@pytest.mark.parametrize("layout,ratios", [
    ("columns", [1, 1]), ("columns columns-3", [1, 1, 1]),
    ("columns columns-2-1", [2, 1]), ("columns columns-1-2", [1, 2]),
])
def test_base_column_layout(layout, ratios, tmp_path, weasyprint_html):
    config = project(tmp_path / "project", "Alpha")
    columns = "\n\n".join(
        f"::: column\nColumn {number}\n:::" for number in range(len(ratios))
    )
    (config.parent / "chapter.md").write_text(
        f":::: {layout}\n{columns}\n::::\n", encoding="utf-8"
    )
    document = weasyprint_html(filename=str(build(config))).render()
    assert len(document.pages) == 1
    boxes = [
        box for box in document.pages[0]._page_box.descendants()
        if box.element_tag == "div" and box.element.get("class") == "column"
    ]
    assert len(boxes) == len(ratios)
    unit = boxes[0].width / ratios[0]
    for position, (box, ratio) in enumerate(zip(boxes, ratios)):
        assert box.width == pytest.approx(unit * ratio)
        assert box.position_y == pytest.approx(boxes[0].position_y)
        if position:
            assert box.position_x >= boxes[position - 1].position_x + boxes[position - 1].width


@pytest.mark.parametrize("size,width,height", [
    ("A3", 297, 420), ("A4", 210, 297), ("A5", 148, 210),
    ("Letter", 215.9, 279.4), ("Legal", 215.9, 355.6),
])
def test_configured_pdf_page_size(size, width, height, tmp_path, weasyprint_html):
    config = project(tmp_path / "project", "Alpha")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings.update({"page_size": size, "title_page": True})
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    result = PdfReader(build(config, "pdf"))
    assert len(result.pages) == 2
    for page in result.pages:
        assert float(page.mediabox.width) == pytest.approx(width * 72 / 25.4, abs=0.01)
        assert float(page.mediabox.height) == pytest.approx(height * 72 / 25.4, abs=0.01)


@pytest.mark.parametrize("language,expected", [("en", "Tekst w"), ("pl", "w\xa0domu")])
def test_polish_words_stay_on_the_same_pdf_line(language, expected, tmp_path, weasyprint_html):
    config = project(tmp_path / "project", "Alpha")
    (config.parent / "chapter.md").write_text("Tekst w domu.\n", encoding="utf-8")
    (config.parent / "styles.css").write_text("p { width: 65px; }", encoding="utf-8")
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    settings.update({"language": language, "stylesheet": "styles.css"})
    config.write_text(yaml.safe_dump(settings), encoding="utf-8")
    document = weasyprint_html(filename=str(build(config))).render()
    lines = [
        "".join(child.text for child in box.descendants() if hasattr(child, "text"))
        for box in document.pages[0]._page_box.descendants()
        if type(box).__name__ == "LineBox" and box.element_tag == "p"
    ]
    assert any(expected in line for line in lines), lines
    if language == "pl":
        assert all(not line.endswith(" w") for line in lines)


def test_invalid_cover_keeps_existing_output(tmp_path, weasyprint_html):
    config = project(tmp_path / "project", "Alpha")
    (config.parent / "cover.pdf").write_bytes(pdf_bytes(["cover"], width=612, height=792))
    with config.open("a", encoding="utf-8") as destination:
        destination.write("front_cover: cover.pdf\n")
    output = config.parent / "build/document.pdf"
    output.parent.mkdir()
    output.write_bytes(b"existing output")
    with pytest.raises(BuildError, match="does not match"):
        build(config, "pdf")
    assert output.read_bytes() == b"existing output"


def test_columns_continue_across_pdf_pages(tmp_path, weasyprint_html):
    config = project(tmp_path / "project", "Alpha")
    left = "\n\n".join(f"Left marker {number:03d}." for number in range(80))
    right = "\n\n".join(f"Right marker {number:03d}." for number in range(30))
    (config.parent / "chapter.md").write_text(
        f":::: columns columns-2-1\n::: column\n{left}\n:::\n\n"
        f"::: column\n{right}\n:::\n::::\n\nAfter the columns.\n",
        encoding="utf-8",
    )
    result = PdfReader(build(config, "pdf"))
    assert len(result.pages) > 1
    text = "\n".join(page.extract_text() for page in result.pages)
    for label, count in (("Left", 80), ("Right", 30)):
        for number in range(count):
            assert text.count(f"{label} marker {number:03d}.") == 1
    assert text.count("After the columns.") == 1


def test_rotated_pdf_cover_matches_display_orientation(tmp_path):
    writer = PdfWriter()
    page = writer.add_blank_page(width=841.89, height=595.28)
    page.rotate(90)
    destination = BytesIO()
    writer.write(destination)
    path = tmp_path / "rotated.pdf"
    path.write_bytes(destination.getvalue())
    result = PdfReader(BytesIO(merge_covers(pdf_bytes(["body"]), {"front_cover": path})))
    assert result.pages[0].rotation == 90
    assert float(result.pages[0].mediabox.width) == pytest.approx(841.89)


def test_merging_preserves_body_bookmarks(tmp_path):
    writer = PdfWriter()
    writer.add_blank_page(width=595.28, height=841.89)
    writer.add_outline_item("Content chapter", 0)
    destination = BytesIO()
    writer.write(destination)
    cover = tmp_path / "front.pdf"
    cover.write_bytes(pdf_bytes(["cover"]))
    result = PdfReader(BytesIO(merge_covers(destination.getvalue(), {"front_cover": cover})))
    assert result.outline[0].title == "Content chapter"
    assert result.get_destination_page_number(result.outline[0]) == 1