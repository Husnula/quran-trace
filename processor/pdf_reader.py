"""
processor/pdf_reader.py
Baca PDF dan render tiap halaman jadi PIL Image.
"""
from __future__ import annotations
import pymupdf as fitz  # PyMuPDF >= 1.24
from PIL import Image
from pathlib import Path
from typing import Generator
import sys
import os
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DPI_PRINT, DPI_PREVIEW


def open_pdf(path: str | Path) -> fitz.Document:
    """Buka PDF; raise ValueError jika gagal atau terproteksi."""
    path = str(path)
    try:
        doc = fitz.open(path)
    except Exception as e:
        raise ValueError(f"Tidak bisa membuka PDF: {e}") from e
    if doc.is_encrypted:
        raise ValueError("PDF terproteksi dengan password. Gunakan PDF tanpa enkripsi.")
    return doc


def page_count(doc: fitz.Document) -> int:
    return len(doc)


def render_page(doc: fitz.Document, page_num: int, dpi: int = DPI_PRINT) -> Image.Image:
    """
    Render halaman ke PIL Image RGB.
    page_num: 0-indexed
    """
    page = doc[page_num]
    scale = dpi / 72.0
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img


def iter_pages(
    doc: fitz.Document,
    dpi: int = DPI_PRINT,
    callback=None,
) -> Generator[tuple[int, Image.Image], None, None]:
    """
    Yield (page_num, PIL Image) untuk setiap halaman.
    callback(page_num, total): dipanggil setelah setiap halaman dirender.
    """
    total = len(doc)
    for i in range(total):
        img = render_page(doc, i, dpi)
        if callback:
            callback(i + 1, total)
        yield i, img
