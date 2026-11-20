# Trace Qur'an

Aplikasi Python desktop untuk mengubah PDF Al-Qur'an menjadi **lembar latihan menulis Arab**. Teks Arab difade/samarkan sehingga siswa bisa menebalkan tulisan tangan di atas cetakannya. Border ornamen dan tanda waqf tetap hitam.

**100% offline. Tidak perlu API key atau internet.**

---

## Fitur

- Upload PDF Al-Qur'an via drag & drop atau dialog pilih file
- Teks Arab otomatis disamarkan (fade)
- Border ornamen halaman tetap hitam (tidak disentuh)
- Tanda waqf (ع، ط، م، ص، ج dll) tetap hitam
- Nomor ayat tetap hitam (opsional)
- 3 preset level fade: Sangat Samar, Samar, Agak Terlihat
- Preview real-time sebelum proses semua halaman
- Progress bar per halaman
- Output PDF siap cetak (300 DPI)

---

## Instalasi

### 1. Install Python 3.9+

Download dari [python.org](https://www.python.org/downloads/)

### 2. Install dependensi

```bash
pip install -r requirements.txt
```

### 3. Jalankan aplikasi

```bash
python main.py
```

Atau untuk mode CLI:

```bash
python main.py --cli --input "JUZ 1.pdf" --output "JUZ 1_trace.pdf" --opacity 0.2
```

---

## Cara Pakai (GUI)

1. Drag PDF Al-Qur'an ke area drop, atau klik "Pilih File"
2. Pilih level fade (Sangat Samar / Samar / Agak Terlihat)
3. Centang opsi yang ingin dipertahankan hitam (border, waqf, nomor ayat)
4. Klik "Preview" untuk melihat hasilnya di halaman pertama
5. Klik "Proses Semua" dan tunggu progress bar selesai
6. File output tersimpan otomatis di folder yang sama dengan nama `[asli]_trace.pdf`

---

## Cara Pakai (CLI)

```bash
# Dasar
python main.py --cli --input "JUZ 1.pdf"

# Dengan semua opsi
python main.py --cli \
  --input "JUZ 1.pdf" \
  --output "JUZ 1_trace.pdf" \
  --opacity 0.2 \
  --keep-waqf \
  --keep-border \
  --dpi 300
```

| Argumen | Default | Keterangan |
|---|---|---|
| `--input` | wajib | Path ke file PDF |
| `--output` | `[input]_trace.pdf` | Path output |
| `--opacity` | `0.2` | 0.1 (sangat samar) - 0.6 (agak terlihat) |
| `--keep-waqf` | True | Pertahankan tanda waqf hitam |
| `--keep-border` | True | Pertahankan border ornamen hitam |
| `--keep-ayat` | False | Pertahankan nomor ayat hitam |
| `--dpi` | `300` | Resolusi output (150=draft, 300=cetak) |

---

## Tanda Waqf yang Dikenali

| Simbol | Nama | Keterangan |
|---|---|---|
| ع | Waqf Lazim (م) | Harus berhenti |
| ط | Waqf Mutlak | Lebih baik berhenti |
| ص | Waqf Murakhkhas | Boleh lanjut karena nafas |
| ج | Waqf Jaiz | Boleh berhenti atau lanjut |
| ز | Waqf Mujawwaz | Lebih baik lanjut |
| ق | Qila Fihil Waqf | Ada yang bilang waqf |
| لا | La Waqf | Jangan berhenti |
| قلي | Qalil | Lebih baik lanjut (jarang) |

Aplikasi mendeteksi simbol-simbol ini secara visual (ukuran kecil di luar area teks utama) dan mempertahankannya hitam pekat.

---

## Teknologi

| Komponen | Library |
|---|---|
| Baca/render PDF | PyMuPDF (fitz) |
| Image processing | Pillow (PIL) |
| Computer Vision | OpenCV |
| Array math | NumPy |
| GUI | Tkinter + sv-ttk |

---

## Lisensi

MIT License - bebas digunakan untuk kepentingan pendidikan Islam.
