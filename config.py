"""
Trace Qur'an - Konfigurasi Global
"""

# ── Fade level presets ─────────────────────────────────────────────────────
FADE_PRESETS = {
    "Sangat Samar": 0.12,   # 12% dari hitam asli → hampir tidak terlihat
    "Samar":        0.22,   # 22% → bisa ditebalkan dengan nyaman
    "Agak Terlihat": 0.38,  # 38% → masih cukup jelas sebagai panduan
}
FADE_DEFAULT = "Samar"
FADE_MIN = 0.08
FADE_MAX = 0.60

# ── Rendering ──────────────────────────────────────────────────────────────
DPI_PRINT = 300
DPI_DRAFT = 150
DPI_PREVIEW = 150   # preview cukup 150 DPI untuk kecepatan

# ── Border detection ───────────────────────────────────────────────────────
# Margin padding setelah deteksi border (pixel pada 300 DPI)
BORDER_INNER_MARGIN = 60      # px: masuk ke dalam dari tepi border
BORDER_MIN_AREA_RATIO = 0.5  # kontur valid jika area > 50% halaman

# ── Waqf detection ────────────────────────────────────────────────────────
# Tanda waqf: simbol kecil di luar jalur teks utama
# Heuristik: area kecil (< threshold), umumnya di kiri atau kanan baris teks
WAQF_MAX_COMPONENT_AREA = 1200   # px² pada 300 DPI: komponen lebih kecil ini dianggap waqf
WAQF_MAX_COMPONENT_WIDTH = 55    # px: lebar max komponen waqf
WAQF_MAX_COMPONENT_HEIGHT = 70   # px: tinggi max komponen waqf
# Tanda waqf juga bisa di dalam teks (superscript) → gunakan combined approach
WAQF_SUPERSCRIPT_Y_RATIO = 0.25  # komponen di atas 25% tinggi baris = superscript

# ── Ayat number detection ─────────────────────────────────────────────────
# Nomor ayat: dalam lingkaran/oktagon dekoratif, ukuran sedang
AYAT_MIN_AREA = 1500        # px²: minimal untuk membedakan dari waqf
AYAT_MAX_AREA = 25000       # px²: nomor ayat tidak terlalu besar
AYAT_CIRCULARITY_MIN = 0.5  # cukup bulat (0=garis, 1=lingkaran sempurna)

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
    "title":   ("Segoe UI", 18, "bold"),
    "section": ("Segoe UI", 11, "bold"),
    "label":   ("Segoe UI", 11, "normal"),
    "body":    ("Segoe UI", 10, "normal"),
    "small":   ("Segoe UI", 9,  "normal"),
    "mono":    ("Consolas",  10, "normal"),
}

WINDOW_MIN_W = 960
WINDOW_MIN_H = 620
PANEL_LEFT_W = 310
