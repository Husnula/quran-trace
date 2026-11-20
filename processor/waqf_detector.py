"""
processor/waqf_detector.py
Deteksi dan mask tanda waqf agar tidak ikut terfade.

Tanda waqf dalam mushaf Utsmani (Rasm Utsmani):
  ع / م  = Waqf Lazim (harus berhenti)
  ط       = Waqf Mutlak
  ص       = Waqf Murakhkhas  
  ج       = Waqf Jaiz
  ز       = Waqf Mujawwaz
  ق       = Qila Fihil Waqf
  لا      = La Waqf (jangan berhenti)
  قلي     = Qalil

Semua simbol ini:
1. Berukuran KECIL (superscript di atas kata atau di margin)
2. Terletak di luar jalur teks utama (di atas atau di kiri baris)
3. Berbentuk huruf Arab tunggal atau dua huruf

Strategi deteksi:
- Jalankan connected component analysis
- Komponen kecil (< WAQF_MAX_COMPONENT_AREA px²) DI LUAR zona teks normal
  dianggap sebagai kandidat waqf/harakat
- Nomor ayat: juga kecil tetapi lebih besar, dalam lingkaran → exclude
"""
from __future__ import annotations
import cv2
import numpy as np
from PIL import Image
from .region_detector import Zone
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    WAQF_MAX_COMPONENT_AREA,
    WAQF_MAX_COMPONENT_WIDTH,
    WAQF_MAX_COMPONENT_HEIGHT,
    AYAT_MIN_AREA,
    AYAT_MAX_AREA,
    AYAT_CIRCULARITY_MIN,
)


def build_preserve_mask(
    img_array: np.ndarray,
    text_zone: Zone,
    keep_waqf: bool = True,
    keep_ayat: bool = False,
) -> np.ndarray:
    """
    Buat mask boolean (H x W) di mana True = pixel yang HARUS tetap hitam.

    Returns:
        preserve_mask: np.ndarray bool, True di area yang tidak boleh difade
    """
    h, w = img_array.shape[:2]
    preserve_mask = np.zeros((h, w), dtype=bool)

    # ── Area luar text_zone selalu dipertahankan (border ornamen) ─────────
    # Area border = semua yang di luar zone
    preserve_mask[:text_zone.y1, :] = True          # atas
    preserve_mask[text_zone.y2:, :] = True          # bawah
    preserve_mask[:, :text_zone.x1] = True          # kiri
    preserve_mask[:, text_zone.x2:] = True          # kanan

    if not keep_waqf and not keep_ayat:
        return preserve_mask

    # ── Connected component analysis dalam text_zone ─────────────────────
    # Ambil region teks saja
    region = img_array[text_zone.y1:text_zone.y2, text_zone.x1:text_zone.x2]
    gray_region = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY) if region.ndim == 3 else region
    _, binary = cv2.threshold(gray_region, 180, 255, cv2.THRESH_BINARY_INV)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)

    for label_id in range(1, num_labels):  # skip background (0)
        x, y, bw, bh, area = stats[label_id, :5]
        circularity = _circularity(binary, labels, label_id, bw, bh, area)

        if keep_waqf and _is_waqf_candidate(area, bw, bh):
            # Tandai komponen ini sebagai preserve
            comp_mask = (labels == label_id)
            # Offset balik ke koordinat gambar penuh
            full_y1 = text_zone.y1 + y
            full_y2 = text_zone.y1 + y + bh
            full_x1 = text_zone.x1 + x
            full_x2 = text_zone.x1 + x + bw
            # Clamp
            full_y2 = min(full_y2, h)
            full_x2 = min(full_x2, w)
            # Tambahkan sedikit padding di sekitar simbol
            pad = 4
            py1 = max(0, full_y1 - pad)
            py2 = min(h, full_y2 + pad)
            px1 = max(0, full_x1 - pad)
            px2 = min(w, full_x2 + pad)
            preserve_mask[py1:py2, px1:px2] = True

        elif keep_ayat and _is_ayat_candidate(area, bw, bh, circularity):
            full_y1 = text_zone.y1 + y
            full_x1 = text_zone.x1 + x
            full_y2 = min(text_zone.y1 + y + bh, h)
            full_x2 = min(text_zone.x1 + x + bw, w)
            pad = 6
            preserve_mask[
                max(0, full_y1 - pad):min(h, full_y2 + pad),
                max(0, full_x1 - pad):min(w, full_x2 + pad),
            ] = True

    return preserve_mask


def _is_waqf_candidate(area: int, bw: int, bh: int) -> bool:
    """Heuristik: komponen kecil = kemungkinan tanda waqf atau harakat."""
    return (
        area < WAQF_MAX_COMPONENT_AREA
        and bw < WAQF_MAX_COMPONENT_WIDTH
        and bh < WAQF_MAX_COMPONENT_HEIGHT
        and area > 20  # bukan noise 1-2 pixel
    )


def _is_ayat_candidate(area: int, bw: int, bh: int, circularity: float) -> bool:
    """Heuristik: nomor ayat dalam lingkaran/oktagon."""
    return (
        AYAT_MIN_AREA <= area <= AYAT_MAX_AREA
        and circularity >= AYAT_CIRCULARITY_MIN
        and abs(bw - bh) < max(bw, bh) * 0.4  # rasio mendekati kotak
    )


def _circularity(
    binary: np.ndarray,
    labels: np.ndarray,
    label_id: int,
    bw: int,
    bh: int,
    area: int,
) -> float:
    """Hitung circularity = 4π*area / perimeter²."""
    comp = (labels == label_id).astype(np.uint8) * 255
    contours, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0
    perimeter = cv2.arcLength(contours[0], True)
    if perimeter == 0:
        return 0.0
    return (4 * np.pi * area) / (perimeter ** 2)
