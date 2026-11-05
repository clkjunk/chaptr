from io import BytesIO
import re

import pytest
import yaml
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

from mdoc.cli import BuildError, build
from mdoc.pdf import CoverError, merge_covers
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
    assert re.search(r"First chapter[.\s]*4", texts[2]), texts[2]
    assert result.get_destination_page_number(result.named_destinations["first-chapter"]) == 3
    assert result.get_destination_page_number(result.named_destinations["second-chapter"]) == 4
    assert any(
        annotation.get_object().get("/Dest") == "first-chapter"
        for annotation in result.pages[2].get("/Annots", [])
    )


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