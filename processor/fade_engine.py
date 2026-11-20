"""
processor/fade_engine.py
Fade pixel gelap dalam zona teks, pertahankan area di preserve_mask.
"""
from __future__ import annotations
import numpy as np
from PIL import Image
from .region_detector import Zone


def fade_page(
    img: Image.Image,
    text_zone: Zone,
    preserve_mask: np.ndarray,
    opacity: float = 0.22,
) -> Image.Image:
    """
    Fade pixel gelap dalam text_zone.

    opacity: 0.1 = sangat samar (10% dari hitam asli)
             0.22 = samar default
             0.5 = masih cukup terlihat

    preserve_mask: bool array (H x W), True = jangan sentuh pixel ini
    """
    arr = np.array(img, dtype=np.float32)  # (H, W, 3), range 0-255

    # Hanya proses area dalam text_zone
    zone_slice = (
        slice(text_zone.y1, text_zone.y2),
        slice(text_zone.x1, text_zone.x2),
    )
    region = arr[zone_slice]
    zone_preserve = preserve_mask[zone_slice]

    # Pixel gelap = teks Arab (nilai rata-rata < threshold)
    pixel_brightness = region.mean(axis=2)   # (H_zone, W_zone)
    dark_mask = pixel_brightness < 200        # < 200/255 = cukup gelap

    # Gabungkan: fade hanya pixel gelap yang BUKAN preserve
    fade_mask = dark_mask & ~zone_preserve

    # Blend ke putih: result = pixel * opacity + 255 * (1 - opacity)
    white = np.full_like(region, 255.0)
    region[fade_mask] = (
        region[fade_mask] * opacity + white[fade_mask] * (1.0 - opacity)
    )

    # Tulis balik
    arr[zone_slice] = region

    # Clamp dan convert ke uint8
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, mode="RGB")


def process_page(
    img: Image.Image,
    text_zone: Zone,
    preserve_mask: np.ndarray,
    opacity: float = 0.22,
) -> Image.Image:
    """Wrapper singkat untuk fade_page."""
    return fade_page(img, text_zone, preserve_mask, opacity)
