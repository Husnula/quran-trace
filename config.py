"""
Trace Qur'an - Konfigurasi Global
"""

# ── Fade level presets ─────────────────────────────────────────────────────
FADE_PRESETS = {
    "Sangat Samar": 0.10,   # 10% dari hitam asli
    "Samar":        0.18,   # 18% (standar ideal FunFurqan & Trace Qur'an)
    "Agak Terlihat": 0.30,  # 30% panduan jelas
}
FADE_DEFAULT = "Samar"
FADE_MIN = 0.05
FADE_MAX = 0.50

# ── Rendering ──────────────────────────────────────────────────────────────
DPI_PRINT = 300
DPI_DRAFT = 150
DPI_PREVIEW = 150   # preview 150 DPI untuk respon cepat

# ── Design tokens (untuk GUI Tkinter) ────────────────────────────────────
COLORS = {
    "bg_base":        "#F7F7F5",
    "bg_panel":       "#FFFFFF",
    "bg_sunken":      "#EEEDE9",
    "border_subtle":  "#DDDBD5",
    "border_strong":  "#B8B5AE",
    "text_primary":   "#1C1917",
    "text_secondary": "#57534E",
    "text_muted":     "#A8A29E",
    "text_inverse":   "#FAFAF9",
    "accent":         "#2D6A4F",
    "accent_hover":   "#245C42",
    "accent_light":   "#D8F3DC",
    "accent_muted":   "#52B788",
    "error":          "#C0392B",
    "error_bg":       "#FEF0EF",
    "warning":        "#92400E",
    "warning_bg":     "#FEF3C7",
}

FONTS = {
    "display":  ("Segoe UI", 16, "bold"),
    "title":    ("Segoe UI", 14, "bold"),
    "heading":  ("Segoe UI", 12, "bold"),
    "section":  ("Segoe UI", 11, "bold"),
    "label":    ("Segoe UI", 10),
    "body":     ("Segoe UI", 10),
    "caption":  ("Segoe UI", 9),
    "small":    ("Segoe UI", 9),
    "mono":     ("Consolas", 9),
}

# ── Layout dimensi GUI ────────────────────────────────────────────────────
WINDOW_MIN_W = 960
WINDOW_MIN_H = 680
PANEL_LEFT_W = 340
