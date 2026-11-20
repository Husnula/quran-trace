"""
processor/fade_engine.py
Engine penyamar teks ayat Al-Qur'an dengan preservasi struktur mushaf.

Menjaga 100% ketajaman:
- Border ornamen dan frame luar
- Banner judul surat & hiasan awal surat
- Garis pembatas horizontal baris ayat
- Garis vertikal pembatas kolom teks dan margin
- Roset nomor ayat (bunga nomor ayat)
- Tanda waqf margin (seperti 'ع' waqf lazim / ruku')
- Halaman non-ayat (cover, daftar tajwid, dll.)

Menyamarkan secara halus & merata:
- Teks ayat Al-Qur'an (huruf hijaiyah + harakat + tanda baca)
  agar dapat ditebalkan dengan mudah dan jelas oleh siswa/santri.
"""
from __future__ import annotations
import cv2
import numpy as np
from PIL import Image
from .region_detector import detect_quran_layout, QuranLayout
from .waqf_detector import detect_ayah_rosettes


def fade_page(
    img: Image.Image,
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
        opacity: tingkat kecerahan samar (0.18 default, 0.08 sangat samar, 0.35 cukup terlihat)
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

    # Jika bukan halaman ayat (misal Cover / Pengantar Tajwid), kembalikan asli tanpa ubahan
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

    # 6. Blend penyamaran: pixel_faded = pixel * opacity + 255 * (1 - opacity)
    faded = (arr.astype(np.float32) * opacity + 255.0 * (1.0 - opacity)).clip(0, 255).astype(np.uint8)

    # Gabungkan: area terlindungi pakai pixel asli, area teks pakai faded
    result = np.where(preserve_mask[:, :, None], arr, faded)
    return Image.fromarray(result, mode="RGB")


def process_page(
    img: Image.Image,
    opacity: float = 0.18,
    keep_border: bool = True,
    keep_waqf: bool = True,
    keep_ayat: bool = True,
) -> Image.Image:
    """Wrapper praktis untuk fade_page."""
    return fade_page(
        img=img,
        opacity=opacity,
        keep_border=keep_border,
        keep_waqf=keep_waqf,
        keep_ayat=keep_ayat,
    )
