from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError


class CoverError(ValueError):
    pass


def page_size(page) -> tuple[float, float]:
    scale = float(page.get("/UserUnit", 1))
    width = float(page.mediabox.width) * scale
    height = float(page.mediabox.height) * scale
    return (height, width) if page.rotation % 180 else (width, height)


def merge_covers(content: bytes, covers: dict[str, Path]) -> bytes:
    body = PdfReader(BytesIO(content))
    readers = {}
    for role, path in covers.items():
        try:
            reader = PdfReader(BytesIO(path.read_bytes()))
            if reader.is_encrypted:
                raise CoverError(f"{role}: encrypted PDF covers are not supported: {path}")
            if len(reader.pages) != 1:
                raise CoverError(f"{role}: PDF cover must contain exactly one page: {path}")
            expected = page_size(body.pages[0 if role == "front_cover" else -1])
            actual = page_size(reader.pages[0])
            if any(abs(actual_dimension - expected_dimension) > 1 for actual_dimension, expected_dimension in zip(actual, expected)):
                raise CoverError(
                    f"{role}: cover size {actual[0]:.1f} x {actual[1]:.1f} pt "
                    f"does not match document size {expected[0]:.1f} x {expected[1]:.1f} pt: {path}"
                )
            readers[role] = reader
        except (OSError, PdfReadError, ValueError) as error:
            if isinstance(error, CoverError):
                raise
            raise CoverError(f"{role}: cannot read PDF cover {path}: {error}") from error
    writer = PdfWriter()
    if "front_cover" in readers:
        writer.append(readers["front_cover"])
    writer.append(body)
    if "back_cover" in readers:
        writer.append(readers["back_cover"])
    if body.metadata:
        writer.add_metadata({key: value for key, value in body.metadata.items() if isinstance(value, str)})
    destination = BytesIO()
    writer.write(destination)
    writer.close()
    return destination.getvalue()