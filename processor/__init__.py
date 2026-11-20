"""
processor/__init__.py
Pipeline utama: baca → deteksi struktur → fade seragam → tulis PDF
"""
from __future__ import annotations
from pathlib import Path
from typing import Callable
from PIL import Image

from .pdf_reader import open_pdf, render_page, page_count
from .region_detector import detect_quran_layout, QuranLayout
from .waqf_detector import detect_ayah_rosettes
from .fade_engine import fade_page, process_page
from .pdf_writer import images_to_pdf, build_output_path
import numpy as np
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DPI_PRINT, DPI_PREVIEW


def process_pdf(
    input_path: str | Path,
    output_path: str | Path | None = None,
    opacity: float = 0.18,
    keep_border: bool = True,
    keep_waqf: bool = True,
    keep_ayat: bool = True,
    dpi: int = DPI_PRINT,
    progress_callback: Callable[[int, int], None] | None = None,
    cancel_flag: list[bool] | None = None,
) -> Path:
    """
    Pipeline lengkap: input PDF → output PDF trace berkualitas cetak profesional.

    Args:
        input_path: Path ke PDF asli
        output_path: Path output (opsional, auto-generate jika None)
        opacity: 0.08-0.50 (makin kecil makin samar, default 0.18)
        keep_border: pertahankan border ornamen dan garis (default: True)
        keep_waqf: pertahankan tanda waqf margin (default: True)
        keep_ayat: pertahankan nomor ayat dalam roset (default: True)
        dpi: resolusi render (default: 300)
        progress_callback: fn(halaman_selesai, total_halaman)
        cancel_flag: list dengan 1 elemen bool; set [True] untuk membatalkan

    Returns:
        Path ke file PDF hasil trace
    """
    if cancel_flag is None:
        cancel_flag = [False]

    output_path = output_path or build_output_path(input_path)
    output_path = Path(output_path)

    doc = open_pdf(input_path)
    total = page_count(doc)
    processed_images: list[Image.Image] = []

    for i in range(total):
        if cancel_flag[0]:
            doc.close()
            raise InterruptedError("Proses dibatalkan pengguna.")

        # 1. Render halaman PDF
        img = render_page(doc, i, dpi=dpi)

        # 2. Proses penyamaran dengan deteksi slot struktural & preservasi roset
        result_img = fade_page(
            img=img,
            opacity=opacity,
            keep_border=keep_border,
            keep_waqf=keep_waqf,
            keep_ayat=keep_ayat,
        )
        processed_images.append(result_img)

        if progress_callback:
            progress_callback(i + 1, total)

    doc.close()

    # 3. Simpan sebagai PDF teroptimasi
    images_to_pdf(processed_images, output_path)

    return output_path


def preview_page(
    input_path: str | Path,
    page_num: int = 0,
    opacity: float = 0.18,
    keep_waqf: bool = True,
    keep_ayat: bool = True,
    dpi: int = DPI_PREVIEW,
) -> Image.Image:
    """
    Render preview cepat untuk satu halaman (biasanya 150 DPI).

    Args:
        input_path: Path ke PDF
        page_num: Nomor halaman (0-indexed)
        opacity: Tingkat samar
        keep_waqf: Pertahankan waqf margin
        keep_ayat: Pertahankan roset ayat
        dpi: Resolusi preview

    Returns:
        PIL Image siap tampil di GUI
    """
    doc = open_pdf(input_path)
    img = render_page(doc, page_num, dpi=dpi)
    doc.close()

    return fade_page(
        img=img,
        opacity=opacity,
        keep_waqf=keep_waqf,
        keep_ayat=keep_ayat,
    )
