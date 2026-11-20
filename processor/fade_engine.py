"""
processor/fade_engine.py
Engine penyamar teks ayat Al-Qur'an dengan preservasi struktur mushaf.
Mendukung 2 Model Tracing:
- Model A: Light Gray (Abu-abu tipis presisi, standar FunFurqan)
- Model B: Outline (Garis tepi tipis, dalam huruf putih/hollow kaligrafi)

Menjaga 100% ketajaman:
- Border ornamen dan frame luar
- Banner judul surat & hiasan awal surat
- Garis pembatas horizontal baris ayat
- Garis vertikal pembatas kolom teks dan margin
- Roset nomor ayat (bunga nomor ayat)
- Tanda waqf margin (seperti 'ع' waqf lazim / ruku')
- Halaman non-ayat (cover, daftar tajwid, dll.)
"""
from __future__ import annotations
import cv2
import numpy as np
from PIL import Image
from .region_detector import detect_quran_layout, QuranLayout
from .waqf_detector import detect_ayah_rosettes


def fade_page(
    img: Image.Image,
    model: str = "gray",
    opacity: float = 0.18,
    keep_border: bool = True,
    keep_waqf: bool = True,
    keep_ayat: bool = True,
    layout: QuranLayout | None = None,
) -> Image.Image:
    """
    Proses penyamaran satu halaman mushaf.

    Args:
        img: PIL Image RGB/RGBA
        model: "gray" (Light Gray) atau "outline" (Garis tepi / hollow)
        opacity: tingkat kecerahan samar (0.18 default)
        keep_border: pertahankan border ornamen dan garis (selalu True)
        keep_waqf: pertahankan tanda waqf margin
        keep_ayat: pertahankan roset nomor ayat
        layout: QuranLayout yang sudah dihitung (opsional, auto jika None)

    Returns:
        PIL Image RGB hasil pemrosesan
    """
    arr = np.array(img.convert("RGB"))
    h, w, _ = arr.shape

    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 190, 255, cv2.THRESH_BINARY_INV)

    # 1. Deteksi layout struktural halaman
    if layout is None:
        layout = detect_quran_layout(gray)

    # Jika bukan halaman ayat (Cover / Pengantar Tajwid), kembalikan asli tanpa ubahan
    if not layout.is_verse_page:
        return Image.fromarray(arr, mode="RGB")

    # 2. Inisialisasi preserve_mask: default SEMUA pixel terlindungi (True)
    preserve_mask = np.ones((h, w), dtype=bool)

    # 3. Hanya aktifkan penyamaran (preserve = False) di dalam slot baris ayat yang valid
    for (y_top, y_bot) in layout.slots:
        preserve_mask[y_top + 2: y_bot - 2, layout.inner_left: layout.inner_right] = False

    # 4. Lindungi garis horizontal dan vertikal agar tetap 100% hitam pekat
    horiz_dilated = cv2.dilate(layout.horiz_lines, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3)))
    vert_dilated = cv2.dilate(layout.vert_lines, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1)))

    preserve_mask |= (horiz_dilated > 0)
    preserve_mask |= (vert_dilated > 0)

    # 5. Lindungi roset nomor ayat jika diaktifkan (default: True)
    if keep_ayat:
        rosette_mask = detect_ayah_rosettes(binary, layout)
        preserve_mask |= rosette_mask

    # 6. Pemrosesan teks ayat berdasarkan model tracing
    if model == "outline":
        # MODEL B: Outline (Garis tepi tipis, dalam huruf putih)
        text_pixels = (binary > 0) & (~preserve_mask)
        text_binary = text_pixels.astype(np.uint8) * 255

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        eroded = cv2.erode(text_binary, kernel)
        outline = cv2.subtract(text_binary, eroded)

        # Background putih
        faded = np.full_like(arr, 255)
        # Garis tepi tipis abu-abu tajam
        line_val = int(110 * (1.0 - opacity * 0.5))
        faded[outline > 0] = [line_val, line_val, line_val]
    else:
        # MODEL A: Light Gray (Abu-abu seragam)
        faded = (arr.astype(np.float32) * opacity + 255.0 * (1.0 - opacity)).clip(0, 255).astype(np.uint8)

    # Gabungkan: area terlindungi pakai pixel asli, area teks pakai faded
    result = np.where(preserve_mask[:, :, None], arr, faded)
    return Image.fromarray(result, mode="RGB")


def process_page(
    img: Image.Image,
    model: str = "gray",
    opacity: float = 0.18,
    keep_border: bool = True,
    keep_waqf: bool = True,
    keep_ayat: bool = True,
) -> Image.Image:
    """Wrapper praktis untuk fade_page."""
    return fade_page(
        img=img,
        model=model,
        opacity=opacity,
        keep_border=keep_border,
        keep_waqf=keep_waqf,
        keep_ayat=keep_ayat,
    )
