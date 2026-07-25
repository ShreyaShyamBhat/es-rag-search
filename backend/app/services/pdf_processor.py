import io
from dataclasses import dataclass

import pdfplumber


class PDFExtractionError(Exception):
    """Raised when a PDF cannot be parsed or contains no extractable text."""


@dataclass
class PageText:
    page_number: int
    text: str


def extract_pages(file_bytes: bytes) -> list[PageText]:
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = [
                PageText(page_number=i + 1, text=(page.extract_text() or "").strip())
                for i, page in enumerate(pdf.pages)
            ]
    except Exception as exc:  # pdfplumber wraps pdfminer errors in various types
        raise PDFExtractionError(f"Failed to parse PDF: {exc}") from exc

    non_empty_pages = [p for p in pages if p.text]
    if not non_empty_pages:
        raise PDFExtractionError("No extractable text found in PDF")

    return pages
