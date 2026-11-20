# Trace Qur'an - Project Map

## Ringkasan Proyek

Aplikasi Python desktop untuk mengubah PDF halaman Al-Qur'an menjadi lembar latihan menulis Arab. Teks Arab difade/samarkan sehingga siswa bisa menebalkan tulisan tangan di atas cetakannya. Border ornamen dan tanda waqf tetap hitam (tidak diubah).

**Offline. Tanpa API key. Pure Python + image processing.**

---

## Arsitektur Sistem

```
INPUT: PDF Al-Qur'an (JUZ 1-30, berbagai ukuran)
        |
        v
[1. PDF RENDERER]
  - PyMuPDF (fitz) render tiap halaman jadi high-res image (300 DPI)
        |
        v
[2. REGION DETECTOR]
  - Deteksi border ornamen (margin tepi halaman)
  - Tentukan "safe zone" = area isi teks Arab
  - Metode: kontur tepi, pixel density analysis
        |
        v
[3. FADE PROCESSOR]
  - Hanya area dalam safe zone yang diproses
  - Pixel hitam pekat → diubah ke abu-abu transparan sesuai level fade
  - Pixel border (di luar safe zone) → tetap hitam (tidak disentuh)
  - Tanda waqf (ukuran kecil, tertentu) → opsi: tetap hitam
        |
        v
[4. PDF ASSEMBLER]
  - Tiap halaman yang sudah diproses dikumpulkan
  - Diekspor menjadi PDF baru dengan nama output yang jelas
        |
        v
OUTPUT: PDF siap cetak dengan teks Arab samar
```

---

## Struktur File

```
trace-quran/
├── main.py                 # Entry point - GUI atau CLI
├── processor/
│   ├── __init__.py
│   ├── pdf_reader.py       # PyMuPDF: baca & render PDF jadi images
│   ├── region_detector.py  # OpenCV: deteksi border vs area teks
│   ├── fade_engine.py      # Pillow/NumPy: logika fade pixel
│   └── pdf_writer.py       # PyMuPDF: assembler halaman jadi PDF baru
├── gui/
│   ├── __init__.py
│   ├── app.py              # Tkinter main window
│   ├── preview_panel.py    # Preview halaman sebelum/sesudah
│   └── settings_panel.py   # Kontrol fade level, margin, dll
├── utils/
│   ├── __init__.py
│   ├── config.py           # Default settings
│   └── validators.py       # Validasi input PDF
├── requirements.txt
├── README.md
└── sample/
    └── juz1_sample.pdf     # PDF contoh untuk testing
```

---

## Stack Teknologi

| Komponen | Library | Versi | Alasan |
|---|---|---|---|
| Baca/render PDF | `PyMuPDF` (fitz) | >= 1.23 | Render high-DPI, preserve vektor |
| Image processing | `Pillow` | >= 10.0 | Manipulasi pixel, export gambar |
| Computer Vision | `opencv-python` | >= 4.8 | Deteksi kontur border |
| Array math | `numpy` | >= 1.24 | Operasi pixel massal (cepat) |
| GUI | `tkinter` | stdlib | Sudah built-in Python, tidak perlu install |
| PDF assembler | `PyMuPDF` (fitz) | >= 1.23 | Sama dengan reader, assembler bawaan |
| Config | `json` / `configparser` | stdlib | Simpan preset fade level |

**Install:** `pip install PyMuPDF Pillow opencv-python numpy`

---

## Alur Proses Teknis Detail

### Step 1: Render PDF ke Image

```python
import fitz  # PyMuPDF

doc = fitz.open("juz1.pdf")
for page_num in range(len(doc)):
    page = doc[page_num]
    mat = fitz.Matrix(300/72, 300/72)  # 300 DPI
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
```

### Step 2: Deteksi Border Region

```python
import cv2
import numpy as np

# Convert ke grayscale
gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
# Threshold
_, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
# Deteksi kontur border terluar
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
# Ambil bounding box terbesar = border ornamen
border_rect = max_contour_bounding_box(contours)
# Safe zone = sedikit dalam dari border
inner_zone = shrink_rect(border_rect, margin=50)  # px
```

### Step 3: Fade Engine

```python
def fade_region(img_array, zone, opacity=0.15):
    """
    Fade pixel gelap dalam zone menjadi abu-abu.
    opacity=0.15 -> sangat samar (15% dari hitam asli)
    opacity=0.40 -> agak terlihat
    """
    region = img_array[zone.y1:zone.y2, zone.x1:zone.x2]
    # Pixel gelap (< 128) = teks/konten
    dark_mask = region.mean(axis=2) < 128
    # Fade: blend ke putih
    region[dark_mask] = (region[dark_mask] * opacity + 255 * (1 - opacity)).astype(np.uint8)
    img_array[zone.y1:zone.y2, zone.x1:zone.x2] = region
    return img_array
```

### Step 4: Assembel ke PDF

```python
def images_to_pdf(image_list, output_path):
    doc = fitz.open()
    for img in image_list:
        # Konversi PIL Image ke bytes
        img_bytes = pil_to_bytes(img)
        # Buat halaman PDF seukuran gambar
        page = doc.new_page(width=img.width, height=img.height)
        page.insert_image(page.rect, stream=img_bytes)
    doc.save(output_path)
    doc.close()
```

---

## Mode Penggunaan

### Mode 1: CLI (untuk pengguna teknis)
```bash
python main.py --input juz1.pdf --output juz1_trace.pdf --opacity 0.15
python main.py --input juz1.pdf --output juz1_trace.pdf --opacity 0.3 --keep-waqf
```

### Mode 2: GUI (untuk guru/admin)
- Window drag & drop PDF
- Slider opacity (10% - 50%)
- Preview real-time halaman pertama
- Tombol "Proses Semua" dan "Simpan PDF"

---

## Tantangan dan Solusi

| Tantangan | Solusi |
|---|---|
| Border ornamen ikut terfade | Deteksi border terlebih dahulu, exclude dari fade zone |
| Tanda waqf ikut terfade | Opsi: ukuran kecil (< X pixel) dikecualikan dari fade |
| PDF berbeda-beda layout per penerbit | Settings adjustable margin detection per file |
| File 30 MB, proses lambat | Progress bar, proses per halaman, preview hanya page 1 |
| Kualitas print rendah jika DPI kurang | Default 300 DPI, opsi 150 DPI untuk draft |
| Warna background halaman tidak putih murni | Threshold adaptif, bukan nilai tetap |

---

## Fase Pengembangan

### Fase 1 - MVP (Prioritas Utama)
- [x] Spesifikasi
- [ ] CLI processor: baca PDF → fade area tengah → output PDF
- [ ] Validasi dengan JUZ 1 yang diberikan klien
- [ ] Adjust threshold dan opacity berdasarkan hasil

### Fase 2 - GUI
- [ ] Tkinter window dasar
- [ ] File picker untuk PDF
- [ ] Slider opacity
- [ ] Preview halaman pertama
- [ ] Tombol proses dan simpan

### Fase 3 - Polish
- [ ] Deteksi waqf yang lebih akurat
- [ ] Batch processing (banyak file sekaligus)
- [ ] Preset (Sangat Samar / Samar / Agak Terlihat)
- [ ] Export ke format gambar (PNG per halaman) selain PDF

---

## Deliverable

| File | Deskripsi |
|---|---|
| `trace_quran.exe` atau `main.py` | Aplikasi siap pakai |
| `requirements.txt` | Daftar dependensi |
| `README.md` | Panduan instalasi dan penggunaan |
| Sample output | 2-3 halaman JUZ 1 yang sudah diproses sebagai contoh |
