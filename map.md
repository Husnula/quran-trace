# Trace Qur'an - Project Map

## Ringkasan Proyek

Aplikasi multi-platform (Desktop GUI Python + Web Client-Side Next.js) untuk mengubah PDF mushaf Al-Qur'an menjadi lembar latihan menulis Arab (Quran Tracing Book). Teks ayat Al-Qur'an disamarkan secara halus dan seragam (18% opacity, standar FunFurqan) sehingga santri/siswa dapat menebalkannya dengan nyaman.

Struktur mushaf dipertahankan 100% hitam pekat & tajam:
- Border ornamen dan frame luar
- Garis pembatas horizontal antar baris ayat
- Garis vertikal pembatas kolom teks dan margin luar
- Banner judul surat & hiasan awal surat
- Roset nomor ayat (bunga/lingkaran nomor ayat)
- Tanda waqf margin (misal tanda waqf lazim / ruku' 'ع' di kolom margin)
- Halaman non-ayat (cover buku, daftar tajwid) otomatis 100% utuh tanpa diubah

**100% Offline. Tanpa API Key. Pure Client-Side / Pure Python.**

---

## Arsitektur Sistem

```
INPUT: PDF Al-Qur'an (JUZ 1-30, standar 15 baris / rasm Utsmani)
        |
        v
[1. PDF RENDERER]
  - Desktop: PyMuPDF (fitz) render high-res (300 DPI print, 150 DPI preview)
  - Web: PDF.js canvas renderer (client-side di browser)
        |
        v
[2. PRECISION LAYOUT & SLOT DETECTOR]
  - Deteksi garis horizontal divider baris (morphological opening 280x1)
  - Ekstraksi y_lines & slot baris ayat (kriteria: 75px <= spacing <= 122px)
  - Deteksi garis vertikal frame mushaf (morphological opening 1x200)
  - Penentuan inner_left dan inner_right (melindungi kolom margin waqf/ruku')
  - Validasi halaman ayat vs non-ayat (jika slot < 5, halaman tidak difade)
        |
        v
[3. AYAH ROSETTE DETECTOR]
  - Deteksi roset nomor ayat (bunga nomor ayat) via contour hierarchy & geometry
  - Kriteria: ukuran 30-80px, aspek rasio 0.7-1.3, child_count >= 8, area > 1000px²
  - Roset nomor ayat dan nomor di dalamnya dipertahankan 100% hitam pekat
        |
        v
[4. UNIFORM FADE ENGINE]
  - Hanya area teks di dalam slot baris ayat yang difade
  - Garis pembatas horizontal dilindungi (dilasi 1-2px)
  - Garis pembatas vertikal dilindungi (dilasi 1-2px)
  - Blend teks ayat: pixel = pixel * opacity + 255 * (1 - opacity)
  - Teks ayat, harakat, dan tanda waqf dalam baris disamarkan secara seragam
        |
        v
[5. PDF ASSEMBLER]
  - Desktop: PyMuPDF assembler (lossless / high-quality JPEG stream)
  - Web: pdf-lib generator (ekspor langsung ke download browser)
        |
        v
OUTPUT: PDF lembar latihan trace siap cetak berkualitas profesional
```

---

## Struktur File

```
trace-quran/
├── config.py                 # Konfigurasi preset fade, design tokens, DPI
├── main.py                   # Entry point - GUI Tkinter atau CLI
├── processor/
│   ├── __init__.py           # Pipeline utama (process_pdf, preview_page)
│   ├── pdf_reader.py         # PyMuPDF: render PDF ke PIL Image
│   ├── region_detector.py    # Deteksi slot horizontal & inner frame vertikal
│   ├── waqf_detector.py      # Deteksi roset nomor ayat via contour hierarchy
│   ├── fade_engine.py        # Logika blending presisi & preservasi elemen
│   └── pdf_writer.py         # PyMuPDF assembler ke file PDF baru
├── gui/
│   ├── __init__.py
│   └── app.py                # Tkinter GUI (drag & drop, live preview, progress)
├── web/                      # Web App untuk Cloudflare Pages (Next.js Static Export)
│   ├── app/                  # Next.js App Router (page.tsx, layout.tsx, globals.css)
│   ├── components/
│   │   └── TraceApp.tsx      # Antarmuka web responsif (drag & drop, preview, progress)
│   ├── lib/
│   │   └── pdf-processor.ts  # Engine client-side HTML Canvas + pdf-lib
│   ├── public/               # Static assets & _headers
│   ├── package.json          # Dependencies Next.js, pdf-lib, pdfjs-dist, motion
│   └── next.config.ts        # Next.js config (output: "export")
├── map.md                    # System architecture & file map
├── prd.md                    # Product Requirements Document
├── wireframes.md             # Wireframes & antarmuka UI
└── design-system.md          # Forest green design system tokens
```

---

## Panduan Menjalankan

### 1. Desktop GUI (Python)
```bash
python main.py
```

### 2. Desktop CLI (Python)
```bash
# Konversi dasar
python main.py --cli --input "JUZ 1.pdf"

# Konversi kustom
python main.py --cli --input "JUZ 1.pdf" --output "JUZ 1_trace.pdf" --opacity 0.18 --dpi 300
```

### 3. Web App (Cloudflare Pages)
```bash
cd web
npm install
npm run build   # Hasil build ada di web/out/
```
Deploy ke Cloudflare Pages:
- Root directory: `web`
- Build command: `npm run build`
- Build output directory: `out`
- Framework preset: `Next.js (Static Export)`
