"""
processor/region_detector.py
Deteksi grid slot baris ayat, border ornamen, dan margin mushaf.

Menggunakan analisa morfologi presisi:
- Deteksi garis horizontal divider baris (morphological opening 280x1)
- Deteksi garis vertikal frame mushaf (morphological opening 1x200)
- Identifikasi inner text column (memisahkan kolom teks dari kolom margin waqf/ruku')
- Klasifikasi halaman ayat vs halaman non-ayat (cover, daftar tajwid, dll.)
"""
from __future__ import annotations
import cv2
import numpy as np
from PIL import Image
from dataclasses import dataclass


@dataclass
class QuranLayout:
    """Informasi layout terstruktur halaman mushaf."""
    is_verse_page: bool
    slots: list[tuple[int, int]]       # list of (y_top, y_bot) untuk setiap baris ayat
    inner_left: int                    # batas kiri area teks ayat
    inner_right: int                   # batas kanan area teks ayat
    horiz_lines: np.ndarray            # binary mask garis horizontal
    vert_lines: np.ndarray             # binary mask garis vertikal


def detect_quran_layout(
    img: Image.Image | np.ndarray,
    min_row_spacing: int = 75,
    max_row_spacing: int = 122,
    min_verse_slots: int = 5,
) -> QuranLayout:
    """
    Analisa struktur halaman mushaf secara matematis.

    Args:
        img: PIL Image atau numpy array BGR/RGB
        min_row_spacing: tinggi minimum slot baris ayat (px at ~150 DPI)
        max_row_spacing: tinggi maksimum slot baris ayat (px at ~150 DPI)
        min_verse_slots: jumlah minimum slot agar dianggap halaman ayat

    Returns:
        QuranLayout
    """
    if isinstance(img, Image.Image):
        arr = np.array(img)
        if arr.ndim == 3 and arr.shape[2] == 3:
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        elif arr.ndim == 3 and arr.shape[2] == 4:
            gray = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)
        else:
            gray = arr
    else:
        if img.ndim == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

    h, w = gray.shape[:2]
    _, binary = cv2.threshold(gray, 190, 255, cv2.THRESH_BINARY_INV)

    # 1. Deteksi garis pembatas horizontal tipis (> 280 px lebar, 1-3 px tinggi)
    horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (280, 1))
    horiz_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horiz_kernel)

    # Cari posisi Y tengah dari setiap garis horizontal
    y_lines: list[int] = []
    in_line = False
    start_y = 0
    for y in range(h):
        val = horiz_lines[y].mean()
        if val > 5:
            if not in_line:
                in_line = True
                start_y = y
        else:
            if in_line:
                in_line = False
                y_lines.append((start_y + y) // 2)

    # Cari slot baris ayat yang valid (jarak antar garis sesuai tinggi baris teks)
    slots: list[tuple[int, int]] = []
    for i in range(len(y_lines) - 1):
        spacing = y_lines[i + 1] - y_lines[i]
        if min_row_spacing <= spacing <= max_row_spacing:
            slots.append((y_lines[i], y_lines[i + 1]))

    # Jika slot baris kurang dari batas minimum (misal Cover, Tajwid guide):
    # Tandai sebagai non-verse page agar tidak disentuh sama sekali
    is_verse_page = len(slots) >= min_verse_slots

    # 2. Deteksi garis frame vertikal (> 200 px tinggi)
    vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 200))
    vert_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vert_kernel)

    v_indices = np.where(vert_lines.mean(axis=0) > 2)[0]
    left_v = v_indices[v_indices < w // 2]
    right_v = v_indices[v_indices >= w // 2]

    # Inner left bound: garis terkanan di sisi kiri frame (melindungi kolom margin waqf/ruku')
    inner_left = int(left_v[-1] + 2) if len(left_v) > 0 else int(w * 0.14)
    # Inner right bound: garis terkiri di sisi kanan frame (melindungi kolom margin kanan)
    inner_right = int(right_v[0] - 2) if len(right_v) > 0 else int(w * 0.88)

    return QuranLayout(
        is_verse_page=is_verse_page,
        slots=slots,
        inner_left=inner_left,
        inner_right=inner_right,
        horiz_lines=horiz_lines,
        vert_lines=vert_lines,
    )
