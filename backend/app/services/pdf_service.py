import re
from typing import List, Dict, Any
from pypdf import PdfReader


def clean_text(text: str) -> str:
    """Normalize extracted text by stripping null bytes and excessive whitespace."""
    if not text:
        return ""
    # Remove null characters and control codes that may corrupt Postgres/JSON
    text = text.replace("\x00", " ")
    # Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace multiple horizontal spaces/tabs with single space
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse more than 2 consecutive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_pages(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract text per page from a PDF file using pypdf.
    Preserves authentic 1-indexed page numbers.
    Raises ValueError if extraction produces no readable text.
    """
    try:
        reader = PdfReader(file_path)
    except Exception as e:
        raise ValueError(f"Failed to read PDF file: {str(e)}")

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("PDF contains no pages.")

    pages_data: List[Dict[str, Any]] = []
    has_text = False

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        try:
            raw_text = page.extract_text() or ""
        except Exception:
            raw_text = ""
        
        cleaned = clean_text(raw_text)
        if cleaned:
            has_text = True
            pages_data.append({
                "page_number": page_num,
                "text": cleaned,
            })

    if not has_text:
        raise ValueError("No extractable text found in PDF (file may be scanned/image-only).")

    return pages_data
