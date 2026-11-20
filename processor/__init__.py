"""
processor/__init__.py
Pipeline utama: baca → detect → fade → tulis
"""
from __future__ import annotations
from pathlib import Path
from typing import Callable
from PIL import Image

from .pdf_reader import open_pdf, render_page, page_count
from .region_detector import detect_text_zone
from .waqf_detector import build_preserve_mask
from .fade_engine import process_page
from .pdf_writer import images_to_pdf, build_output_path
import numpy as np
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DPI_PRINT, DPI_PREVIEW


def process_pdf(
    input_path: str | Path,
    output_path: str | Path | None = None,
    opacity: float = 0.22,
    keep_border: bool = True,
    keep_waqf: bool = True,
    keep_ayat: bool = False,
    dpi: int = DPI_PRINT,
    progress_callback: Callable[[int, int], None] | None = None,
    cancel_flag: list[bool] | None = None,  # cancel_flag[0] = True untuk batal
) -> Path:
    """
    Pipeline lengkap: input PDF → output PDF trace.

    Args:
        input_path: Path ke PDF asli
        output_path: Path output (opsional, auto-generate jika None)
        opacity: 0.0-1.0 (makin kecil makin samar)
        keep_border: pertahankan border ornamen (selalu True, ini default)
        keep_waqf: pertahankan tanda waqf
        keep_ayat: pertahankan nomor ayat dalam lingkaran
        dpi: resolusi render
        progress_callback: fn(halaman_selesai, total_halaman)
        cancel_flag: list dengan 1 elemen bool; set [True] untuk membatalkan

    Returns:
        Path ke file output yang dibuat
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

        # 1. Render
        img = render_page(doc, i, dpi=dpi)
        img_array = np.array(img)

        # 2. Deteksi zona teks (di dalam border)
        text_zone = detect_text_zone(img)

        # 3. Buat preserve mask
        preserve_mask = build_preserve_mask(
            img_array,
            text_zone,
            keep_waqf=keep_waqf,
            keep_ayat=keep_ayat,
        )

        # 4. Fade
        result_img = process_page(img, text_zone, preserve_mask, opacity=opacity)
        processed_images.append(result_img)

        if progress_callback:
            progress_callback(i + 1, total)

    doc.close()

    # 5. Simpan PDF
    images_to_pdf(processed_images, output_path)

    return output_path


def preview_page(
    input_path: str | Path,
    page_num: int = 0,
    opacity: float = 0.22,
    keep_waqf: bool = True,
    keep_ayat: bool = False,
    dpi: int = DPI_PREVIEW,
) -> Image.Image:
    """
    Proses satu halaman dan return PIL Image (untuk preview GUI).
    page_num: 0-indexed
    """
    doc = open_pdf(input_path)
    img = render_page(doc, page_num, dpi=dpi)
    doc.close()

    img_array = np.array(img)
    text_zone = detect_text_zone(img)
    preserve_mask = build_preserve_mask(
        img_array, text_zone, keep_waqf=keep_waqf, keep_ayat=keep_ayat
    )
    return process_page(img, text_zone, preserve_mask, opacity=opacity)
