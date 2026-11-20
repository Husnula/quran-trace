"""
processor/region_detector.py
Deteksi area border ornamen dan zona teks aman.

Strategi untuk mushaf Utsmani (JUZ 1 & 2 dari Duta Ilmu):
- Halaman berbentuk portrait dengan border ornamen di kiri dan kanan
- Border berupa pola garis tebal + ornamen dekoratif
- Area teks aman = rectangle di dalam border
- Pendekatan: cari garis vertikal tebal di kiri dan kanan,
  ambil ruang di antara keduanya sebagai safe zone
"""
from __future__ import annotations
import cv2
import numpy as np
from PIL import Image
from dataclasses import dataclass


@dataclass
class Zone:
    """Koordinat rectangle (pixel, 0-indexed, inklusif)."""
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self):
        return self.x2 - self.x1

    @property
    def height(self):
        return self.y2 - self.y1


def pil_to_gray_array(img: Image.Image) -> np.ndarray:
    """PIL RGB → numpy grayscale uint8."""
    return np.array(img.convert("L"))


def detect_text_zone(img: Image.Image, inner_margin: int = 60) -> Zone:
    """
    Deteksi zona teks aman (di dalam border ornamen).

    Mengembalikan Zone yang sudah dikurangi margin agar
    pixel border tidak ikut terfade.

    Fallback: jika deteksi gagal, gunakan 8% margin dari tepi.
    """
    gray = pil_to_gray_array(img)
    h, w = gray.shape

    # ── Threshold: piksel gelap = hitam/teks/border ──────────────────────
    # Inverse binary: gelap → putih (foreground)
    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

    # ── Cari kolom dengan density piksel gelap tinggi (= border vertikal) ─
    col_density = binary.mean(axis=0)   # rata-rata per kolom

    # Ambang: kolom dengan > 15% piksel gelap = kemungkinan border
    BORDER_THRESHOLD = 15.0

    left_x = _find_border_x(col_density, direction="left", threshold=BORDER_THRESHOLD, w=w)
    right_x = _find_border_x(col_density, direction="right", threshold=BORDER_THRESHOLD, w=w)

    # ── Cari baris dengan density piksel gelap tinggi (= border horizontal) ─
    row_density = binary.mean(axis=1)
    top_y = _find_border_y(row_density, direction="top", threshold=BORDER_THRESHOLD, h=h)
    bottom_y = _find_border_y(row_density, direction="bottom", threshold=BORDER_THRESHOLD, h=h)

    # ── Tambahkan inner margin ──────────────────────────────────────────
    x1 = min(left_x + inner_margin, w // 2)
    x2 = max(right_x - inner_margin, w // 2)
    y1 = min(top_y + inner_margin // 2, h // 2)
    y2 = max(bottom_y - inner_margin // 2, h // 2)

    # Validasi: zone harus masuk akal
    if x2 - x1 < w * 0.3 or y2 - y1 < h * 0.3:
        # Fallback ke 8% margin
        margin_x = int(w * 0.08)
        margin_y = int(h * 0.05)
        x1, x2 = margin_x, w - margin_x
        y1, y2 = margin_y, h - margin_y

    return Zone(x1=x1, y1=y1, x2=x2, y2=y2)


def _find_border_x(col_density: np.ndarray, direction: str, threshold: float, w: int) -> int:
    """Cari posisi x border dari kiri atau kanan."""
    if direction == "left":
        for x in range(0, w // 3):
            if col_density[x] > threshold:
                # Scan ke kanan sampai density turun
                for x2 in range(x, w // 3):
                    if col_density[x2] < threshold * 0.3:
                        return x2
                return x + 20
        return int(w * 0.08)  # fallback
    else:  # right
        for x in range(w - 1, w * 2 // 3, -1):
            if col_density[x] > threshold:
                for x2 in range(x, w * 2 // 3, -1):
                    if col_density[x2] < threshold * 0.3:
                        return x2
                return x - 20
        return int(w * 0.92)  # fallback


def _find_border_y(row_density: np.ndarray, direction: str, threshold: float, h: int) -> int:
    """Cari posisi y border dari atas atau bawah."""
    if direction == "top":
        for y in range(0, h // 5):
            if row_density[y] > threshold:
                for y2 in range(y, h // 5):
                    if row_density[y2] < threshold * 0.3:
                        return y2
                return y + 10
        return int(h * 0.05)  # fallback
    else:  # bottom
        for y in range(h - 1, h * 4 // 5, -1):
            if row_density[y] > threshold:
                for y2 in range(y, h * 4 // 5, -1):
                    if row_density[y2] < threshold * 0.3:
                        return y2
                return y - 10
        return int(h * 0.95)  # fallback
