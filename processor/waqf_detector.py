"""
processor/waqf_detector.py
Deteksi dan proteksi penanda nomor ayat (Ayah Rosettes) dan tanda waqf margin.

Prinsip deteksi:
1. Roset Nomor Ayat (Bunga/Lingkaran Ayat):
   - Berupa ornamen bunga/lingkaran dengan ukiran berulang dan angka ayat di dalamnya.
   - Memiliki kontur berlapis (hierarchy child_count >= 8) dan area > 1000 px².
   - Aspek rasio simetris (~0.70 - 1.30) dan ukuran standar (~30 - 80 px).
   - Dipertahankan 100% hitam pekat agar nomor ayat tetap jelas dibaca.

2. Tanda Waqf Margin (misal Waqf Lazim 'ع' / Ruku' di kolom margin luar):
   - Terletak di luar batas inner_left/inner_right text column.
   - Otomatis 100% terlindungi oleh layout masking.

3. Tanda Waqf & Harakat dalam Baris Ayat:
   - Dibuat samar seragam bersama huruf ayat agar santri dapat menebalkan
     seluruh tulisan ayat secara natural (sesuai standar FunFurqan & Trace Quran).
"""
from __future__ import annotations
import cv2
import numpy as np
from .region_detector import QuranLayout


def detect_ayah_rosettes(
    binary: np.ndarray,
    layout: QuranLayout,
    min_size: int = 30,
    max_size: int = 80,
    min_area: float = 1000.0,
    min_children: int = 8,
    pad: int = 3,
) -> np.ndarray:
    """
    Deteksi roset nomor ayat di dalam zona teks menggunakan analisa hierarki kontur.

    Args:
        binary: gambar biner inversi (foreground = 255)
        layout: QuranLayout hasil deteksi region_detector
        min_size: lebar/tinggi minimum roset
        max_size: lebar/tinggi maksimum roset
        min_area: luas kontur minimum
        min_children: jumlah anak kontur minimum (lingkaran ornamen + angka)
        pad: padding pixel pelindung di sekitar roset

    Returns:
        np.ndarray bool (H, W) di mana True = area roset nomor ayat
    """
    h, w = binary.shape[:2]
    rosette_mask = np.zeros((h, w), dtype=bool)

    if not layout.is_verse_page:
        return rosette_mask

    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None or len(contours) == 0:
        return rosette_mask

    hierarchy = hierarchy[0]
    for i, c in enumerate(contours):
        x, y, bw, bh = cv2.boundingRect(c)

        # Harus berada di dalam rentang kolom teks ayat
        if layout.inner_left <= x and x + bw <= layout.inner_right:
            if min_size <= bw <= max_size and min_size <= bh <= max_size:
                aspect = bw / float(bh)
                if 0.70 <= aspect <= 1.30:
                    # Hitung anak kontur (child hierarchy)
                    child_count = 0
                    child_idx = hierarchy[i][2]
                    while child_idx != -1:
                        child_count += 1
                        child_idx = hierarchy[child_idx][0]

                    area = cv2.contourArea(c)
                    if child_count >= min_children and area > min_area:
                        y1 = max(0, y - pad)
                        y2 = min(h, y + bh + pad)
                        x1 = max(0, x - pad)
                        x2 = min(w, x + bw + pad)
                        rosette_mask[y1:y2, x1:x2] = True

    return rosette_mask
