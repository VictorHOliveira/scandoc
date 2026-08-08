import zipfile
from typing import Callable, Optional

from . import docx_scanner, html_scanner, image_scanner, pdf_scanner, text_scanner

TEXT_EXT = {".txt", ".md", ".markdown", ".csv", ".log"}
HTML_EXT = {".html", ".htm"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif"}

DOCX_MAGIC = b"PK\x03\x04"
DOC_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
PDF_MAGIC = b"%PDF"


def detect_format(filename: str, data: bytes) -> str | None:
    lower = filename.lower()
    dot_ext = "." + lower.rsplit(".", 1)[-1] if "." in lower else ""

    if data.startswith(PDF_MAGIC) or dot_ext == ".pdf":
        return "pdf"
    if data.startswith(DOC_MAGIC):
        return "doc"
    if dot_ext == ".docx":
        return "docx"
    if data.startswith(DOCX_MAGIC):
        try:
            import io as _io

            z = zipfile.ZipFile(_io.BytesIO(data))
            if any(n.startswith("word/") for n in z.namelist()):
                return "docx"
        except Exception:
            pass
    if dot_ext in HTML_EXT or data.lstrip().lower().startswith((b"<!doctype html", b"<html")):
        return "html"
    if dot_ext in IMAGE_EXT:
        return "image"
    if dot_ext in TEXT_EXT:
        return "text"
    return None


def run_scan(filename: str, data: bytes, on_progress: Callable[[int, str], None] | None = None) -> dict:
    fmt = detect_format(filename, data)
    if fmt is None:
        raise ValueError("Formato não suportado")
    if fmt == "doc":
        raise ValueError("Formato .doc (Word legado) não é suportado ainda. Converta o arquivo para .docx e tente novamente.")
    if on_progress:
        on_progress(5, f"Formato detectado: {fmt.upper()}")
    scanners = {
        "pdf": pdf_scanner.scan_pdf,
        "docx": docx_scanner.scan_docx,
        "html": html_scanner.scan_html,
        "image": image_scanner.scan_image,
        "text": text_scanner.scan_text,
    }
    return scanners[fmt](filename, data, on_progress=on_progress)
