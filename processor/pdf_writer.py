"""
processor/pdf_writer.py
Assembel list PIL Image menjadi PDF output.
"""
from __future__ import annotations
import pymupdf as fitz
import io
from PIL import Image
from pathlib import Path


def images_to_pdf(images: list[Image.Image], output_path: str | Path) -> None:
    """
    Simpan list PIL Image sebagai PDF baru.
    Tiap image = 1 halaman, ukuran halaman mengikuti ukuran gambar (px → pt at 300 DPI).
    """
    output_path = str(output_path)
    doc = fitz.open()

    for img in images:
        # PIL → bytes JPEG (lebih kecil dari PNG, cukup untuk dokumen cetak)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92, optimize=True)
        buf.seek(0)
        img_bytes = buf.read()

        # Konversi px → point (1 pt = 1/72 inch; 300 DPI → pt = px * 72 / 300)
        w_pt = img.width * 72 / 300
        h_pt = img.height * 72 / 300

        page = doc.new_page(width=w_pt, height=h_pt)
        rect = fitz.Rect(0, 0, w_pt, h_pt)
        page.insert_image(rect, stream=img_bytes)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()


def build_output_path(input_path: str | Path, suffix: str = "_trace") -> Path:
    """
    Buat path output otomatis.
    Contoh: "JUZ 1.pdf" → "JUZ 1_trace.pdf"
    """
    p = Path(input_path)
    return p.parent / f"{p.stem}{suffix}{p.suffix}"
