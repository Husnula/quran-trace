# Design System - Trace Qur'an

> Design read: **Desktop utility app untuk pendidik Islam, trust-first, clean, fungsional.**
> Dials: `DESIGN_VARIANCE: 4` / `MOTION_INTENSITY: 2` / `VISUAL_DENSITY: 5`
> Framework: Python Tkinter (native widgets) + ttkthemes/sv-ttk untuk modern look.

---

## 1. Prinsip Desain

Aplikasi ini bukan marketing page. Ini alat kerja untuk guru. Prinsip:

1. **Fungsional di atas estetika** - setiap elemen punya tujuan, tidak ada dekorasi kosong
2. **Jelas dan tenang** - tidak ada warna mencolok, tidak ada animasi berlebihan
3. **Kepercayaan** - visual yang rapi dan profesional memberi rasa aman pada pengguna non-teknis
4. **Efisiensi** - 3 klik untuk hasil, tidak ada langkah tersembunyi

---

## 2. Palet Warna

Menggunakan pendekatan **monochrome + single warm accent** (tidak beige+brass, sesuai rules).

### Warna Utama

| Token | Hex | Penggunaan |
|---|---|---|
| `--bg-base` | `#F7F7F5` | Background window utama |
| `--bg-panel` | `#FFFFFF` | Panel settings dan preview |
| `--bg-sunken` | `#EEEDE9` | Drop zone, input background |
| `--border-subtle` | `#DDDBD5` | Border panel, divider |
| `--border-strong` | `#B8B5AE` | Border input, hover states |

### Teks

| Token | Hex | Penggunaan |
|---|---|---|
| `--text-primary` | `#1C1917` | Judul, label utama |
| `--text-secondary` | `#57534E` | Label sekunder, deskripsi |
| `--text-muted` | `#A8A29E` | Placeholder, hint |
| `--text-inverse` | `#FAFAF9` | Teks di atas tombol gelap |

### Aksen (satu warna, dipakai konsisten)

Memilih **Forest Green** - cocok untuk konteks pendidikan Islam, tenang, tidak AI-purple.

| Token | Hex | Penggunaan |
|---|---|---|
| `--accent` | `#2D6A4F` | Tombol primary, border active |
| `--accent-hover` | `#245C42` | Hover state tombol |
| `--accent-light` | `#D8F3DC` | Background checkbox checked, badge |
| `--accent-muted` | `#52B788` | Border input focused |

### Status

| Token | Hex | Penggunaan |
|---|---|---|
| `--success` | `#2D6A4F` | Sama dengan accent (konsisten) |
| `--error` | `#C0392B` | Pesan error, border error |
| `--error-bg` | `#FEF0EF` | Background pesan error |
| `--warning` | `#92400E` | Peringatan |
| `--warning-bg` | `#FEF3C7` | Background peringatan |

---

## 3. Tipografi

### Font Stack

Tkinter menggunakan system fonts. Urutan prioritas:

```python
FONT_SANS = ("Segoe UI", "SF Pro Text", "Ubuntu", "Helvetica Neue", "sans-serif")
FONT_MONO = ("Cascadia Code", "Consolas", "Fira Code", "Courier New", "monospace")
```

**Tidak memakai Inter** (sesuai rule anti-default). Segoe UI sudah rapi di Windows.

### Skala Tipografi

| Token | Size | Weight | Penggunaan |
|---|---|---|---|
| `--type-title` | 18px | Bold (700) | Judul window/dialog |
| `--type-label` | 13px | Semibold (600) | Label form, section header |
| `--type-body` | 13px | Regular (400) | Teks biasa, deskripsi |
| `--type-small` | 11px | Regular (400) | Hint text, status bar |
| `--type-mono` | 12px | Regular (400) | Path file, persentase |

---

## 4. Spacing & Layout

### Grid

- Window minimum: 900px x 600px
- Panel kiri (settings): **300px tetap**
- Panel kanan (preview): **sisa lebar, minimum 500px**
- Gutter antar panel: **1px border**

### Spacing Scale

| Token | Value | Penggunaan |
|---|---|---|
| `--space-1` | 4px | Jarak antar inline elements |
| `--space-2` | 8px | Padding dalam komponen kecil |
| `--space-3` | 12px | Padding input, margin antar form row |
| `--space-4` | 16px | Padding section, margin antar groups |
| `--space-5` | 24px | Padding panel |
| `--space-6` | 32px | Jarak antar section utama |

### Border Radius

Satu sistem: **6px untuk semua** (all-soft, konsisten).

```python
RADIUS = 6  # px, dipakai di semua widget custom
```

---

## 5. Komponen

### 5.1 Tombol Primary (Proses Semua)

```
┌──────────────────────────┐
│      PROSES SEMUA (24)   │   bg: --accent (#2D6A4F)
└──────────────────────────┘   text: --text-inverse
                               border-radius: 6px
                               padding: 10px 16px
                               font: --type-label
                               hover: --accent-hover
                               active: scale 0.98 (subtle press)
                               disabled: opacity 0.5
```

### 5.2 Tombol Secondary

```
┌──────────────────┐
│   Ganti          │   bg: transparent
└──────────────────┘   text: --text-secondary
                       border: 1px --border-strong
                       border-radius: 6px
                       padding: 6px 12px
                       hover: bg --bg-sunken
```

### 5.3 Drop Zone

```
┌──────────────────────────────────┐
│                                  │   bg: --bg-sunken
│   [ikon upload]                  │   border: 1.5px dashed --border-strong
│   Drag PDF ke sini               │   border-radius: 6px
│   atau klik untuk pilih          │   padding: 24px
│                                  │   text: --text-muted
└──────────────────────────────────┘
   hover: border --accent-muted
   active/filled: bg --accent-light, border --accent
```

### 5.4 Radio Button Group (Fade Level)

```
○ Sangat Samar (15%)      -- default radio styling OS
● Samar (25%)             -- selected: dot warna --accent
○ Agak Terlihat (40%)

Custom: ━━━━━●──── 25%    -- Tkinter Scale widget
         10%          60%   -- label bawah kiri/kanan
```

### 5.5 Checkbox

```
☑ Pertahankan border      -- checked: bg --accent-light, border --accent
☑ Pertahankan tanda waqf  -- text: --text-primary
☐ Pertahankan nomor ayat  -- unchecked: border --border-strong
```

### 5.6 Progress Bar

```
Memproses halaman 8 dari 24
[████████████░░░░░░░░░░] 33%
Estimasi: 32 detik lagi

-- fill color: --accent
-- track color: --bg-sunken
-- text: --type-small --text-secondary
-- border-radius: 3px (half of komponen)
```

### 5.7 Status Bar

```
│ Status: Preview halaman 1 selesai (0.8 detik)                    │
  -- bg: --bg-sunken
  -- border-top: 1px --border-subtle
  -- padding: 6px 16px
  -- font: --type-small
  -- text: --text-secondary
  -- di-update setiap aksi
```

### 5.8 Panel Preview

```
┌──────────────────────────────────────────┐
│  [Gambar halaman Al-Qur'an terpreview]  │  bg: --bg-sunken (saat kosong)
│                                          │  bg: --bg-panel (saat ada gambar)
└──────────────────────────────────────────┘
   -- fit-to-panel (scale down, preserve aspect ratio)
   -- border: 1px --border-subtle
   -- navigasi halaman di bawah panel
```

---

## 6. Ikonografi

Menggunakan **sistem ikon built-in Tkinter** untuk kesederhanaan, atau gunakan karakter Unicode:

| Situasi | Karakter/Simbol |
|---|---|
| File valid | `✓` (U+2713) |
| Error | `✗` (U+2717) |
| Upload/pilih file | `↑` atau teks "Pilih File" |
| Navigasi prev | `◄` |
| Navigasi next | `►` |
| Loading | `...` atau progress bar (tidak pakai spinner) |
| Info | `ⓘ` (U+24D8) |

**Tidak ada emoji** (sesuai rules). Tidak ada ikon library eksternal (untuk menjaga zero-dependency GUI).

---

## 7. Motion & Interaksi

`MOTION_INTENSITY: 2` - hanya state transition, tidak ada animasi dekoratif.

| Interaksi | Behavior |
|---|---|
| Hover tombol | Warna berubah instan (no transition) |
| Klik tombol | Scale 0.98 selama 100ms (tactile feedback) |
| File drop | Drop zone border berubah warna |
| Progress bar | Update per halaman, tidak animated smooth |
| Dialog sukses/error | Langsung muncul (tidak fade in) |

**Tidak ada:** animasi loading spinner, fade transition antar panel, atau parallax.

---

## 8. Implementasi Tkinter

### Theme

Gunakan `sv-ttk` (Sun Valley theme) untuk tampilan Windows 11-like yang bersih:

```python
# requirements.txt
sv-ttk>=2.6.0

# main.py
import sv_ttk
sv_ttk.set_theme("light")
```

Alternatif tanpa library tambahan: `ttk.Style` dengan konfigurasi manual.

### Warna dalam Kode

```python
# config.py - Design Tokens
COLORS = {
    "bg_base":       "#F7F7F5",
    "bg_panel":      "#FFFFFF",
    "bg_sunken":     "#EEEDE9",
    "border_subtle": "#DDDBD5",
    "border_strong": "#B8B5AE",

    "text_primary":   "#1C1917",
    "text_secondary": "#57534E",
    "text_muted":     "#A8A29E",
    "text_inverse":   "#FAFAF9",

    "accent":        "#2D6A4F",
    "accent_hover":  "#245C42",
    "accent_light":  "#D8F3DC",
    "accent_muted":  "#52B788",

    "error":         "#C0392B",
    "error_bg":      "#FEF0EF",
}

FONTS = {
    "title":  ("Segoe UI", 18, "bold"),
    "label":  ("Segoe UI", 13, "normal"),
    "body":   ("Segoe UI", 13, "normal"),
    "small":  ("Segoe UI", 11, "normal"),
    "mono":   ("Cascadia Code", 12, "normal"),
}

SPACING = {
    1: 4, 2: 8, 3: 12, 4: 16, 5: 24, 6: 32
}

RADIUS = 6
```

---

## 9. Dark Mode

Tkinter bawaan tidak support dark mode toggle yang mulus. Keputusan: **light mode only** untuk v1.0.

Alasan:
- Pengguna: guru non-teknis, biasa dengan light interface
- Konten preview (halaman Al-Qur'an) lebih jelas di light background
- Menghindari kompleksitas implementation di Tkinter

Bisa ditambahkan di v2.0 jika ada permintaan.

---

## 10. Checklist Pre-Ship

- [ ] Semua tombol punya contrast ratio WCAG AA (teks atas background)
- [ ] Font size minimum 11px
- [ ] Tidak ada hardcoded warna di luar `COLORS` dict
- [ ] Tidak ada animasi selain tactile button press
- [ ] Semua state (empty, filled, loading, success, error) sudah didesain
- [ ] Komponen responsive saat window di-resize (minimum 900x600)
- [ ] Panel preview scale gambar dengan benar di berbagai ukuran halaman PDF
- [ ] Status bar selalu update saat aksi berlangsung
