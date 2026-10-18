import io
import os

import pdfplumber
import docx


class ResumeParseError(Exception):
    pass


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract plain text from a resume file. Supports .pdf, .docx, .txt."""
    ext = os.path.splitext(filename or "")[1].lower()

    try:
        if ext == ".pdf":
            return _extract_pdf(file_bytes)
        elif ext == ".docx":
            return _extract_docx(file_bytes)
        elif ext == ".txt":
            return file_bytes.decode("utf-8", errors="ignore")
        else:
            raise ResumeParseError(
                f"Unsupported resume file type '{ext}'. Please upload PDF, DOCX or TXT."
            )
    except ResumeParseError:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise ResumeParseError(f"Could not read resume file: {exc}") from exc


def _extract_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    text = "\n".join(text_parts).strip()
    if not text:
        raise ResumeParseError(
            "No extractable text found in PDF (it may be a scanned image)."
        )
    return text


def _extract_docx(file_bytes: bytes) -> str:
    document = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs).strip()
    if not text:
        raise ResumeParseError("No extractable text found in DOCX.")
    return text


def truncate_for_prompt(text: str, max_chars: int = 6000) -> str:
    """Keep prompts a reasonable size - resumes rarely need more than this."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"
