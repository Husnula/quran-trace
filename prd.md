# PRD - Trace Qur'an

**Versi:** 1.0
**Tanggal:** November 2026
**Status:** Draft

---

## 1. Latar Belakang

Guru tahsin/Al-Qur'an di Duta Ilmu membutuhkan lembar latihan untuk murid. Caranya: murid menebalkan huruf Arab yang sudah dicetak dengan kondisi samar. Metode ini terbukti efektif untuk melatih motorik menulis Arab.

Selama ini lembar latihan dibuat manual (desain ulang di komputer, huruf per huruf). Proses ini lambat dan mahal. Solusinya: satu aplikasi Python yang otomatis mengubah PDF Al-Qur'an menjadi lembar trace siap cetak.

---

## 2. Problem Statement

**Pengguna:** Guru/admin Duta Ilmu (non-developer)

**Masalah utama:**
1. PDF Al-Qur'an tersedia digital (berbagai JUZ) tetapi tidak bisa langsung dijadikan lembar trace
2. Proses manual memakan waktu berjam-jam per JUZ
3. Tidak semua guru bisa menggunakan software desain grafis

**Yang diinginkan:**
> "Upload PDF Al-Qur'an, terus outputnya jadi tulisan samar-samar, tujuannya untuk ditebalkan. Intinya border tetap hitam (asli), kalau bisa waqofnya juga tetap hitam (asli), hanya arabnya saja yang samar-samar."
> - Mbah Soleh, Duta Ilmu

---

## 3. Tujuan Produk

| Tujuan | Metrik Sukses |
|---|---|
| Proses PDF jadi lembar trace otomatis | 1 JUZ (24-30 halaman) selesai < 5 menit |
| Tidak perlu internet atau API | 100% offline, tanpa login |
| Mudah digunakan oleh guru non-teknis | Proses dalam 3 klik: pilih file, atur level, simpan |
| Kualitas cetak baik | Output 300 DPI, border tetap tajam |

---

## 4. User Stories

### Primary User: Guru/Admin

**US-01** - Upload PDF
> Sebagai guru, saya ingin memilih file PDF Al-Qur'an dari komputer saya, agar bisa diproses menjadi lembar trace.

Kriteria:
- Bisa pilih file via dialog atau drag & drop
- Mendukung PDF ukuran besar (s.d. 100 MB)
- Validasi jika file bukan PDF atau corrupt

**US-02** - Atur level fade
> Sebagai guru, saya ingin mengatur seberapa samar tulisan Arabnya, agar bisa disesuaikan dengan kemampuan murid.

Kriteria:
- Minimal 3 preset: Sangat Samar (15%), Samar (25%), Agak Terlihat (40%)
- Slider manual opsional (10%-60%)
- Preview berubah real-time saat slider bergerak

**US-03** - Preview sebelum proses
> Sebagai guru, saya ingin melihat preview hasilnya sebelum memproses semua halaman, agar tidak membuang waktu jika hasilnya tidak sesuai.

Kriteria:
- Preview halaman pertama (atau halaman pilihan)
- Preview cukup detail untuk menilai kualitas fade
- Preview cepat (< 3 detik untuk 1 halaman)

**US-04** - Proses dan simpan
> Sebagai guru, saya ingin memproses semua halaman dan menyimpan hasilnya sebagai PDF baru, agar bisa langsung dicetak.

Kriteria:
- Progress bar selama proses berlangsung
- Nama file output otomatis: `[nama_asli]_trace.pdf`
- Lokasi simpan bisa dipilih
- Notifikasi jelas saat selesai

**US-05** - Pertahankan border dan waqf
> Sebagai guru, saya ingin border ornamen dan tanda waqf tetap hitam pekat, agar halaman terlihat rapi dan murid tahu batas baca.

Kriteria:
- Border ornamen di tepi halaman: tetap hitam
- Tanda waqf (tanda berhenti): opsi tetap hitam
- Nomor halaman/ayat: opsi tetap hitam

---

## 5. Spesifikasi Fungsional

### 5.1 Core Processing

| Fitur | Deskripsi | Prioritas |
|---|---|---|
| Render PDF ke image | PyMuPDF, 300 DPI per halaman | P0 |
| Deteksi border region | OpenCV kontur, exclude dari fade | P0 |
| Fade teks Arab | Pixel gelap → abu-abu sesuai level | P0 |
| Assembel ke PDF baru | PyMuPDF, semua halaman tergabung | P0 |
| Keep waqf marks | Opsi: exclude pixel kecil dari fade | P1 |
| Progress tracking | Callback per halaman | P0 |

### 5.2 GUI

| Fitur | Deskripsi | Prioritas |
|---|---|---|
| File picker | Dialog OS standar + drag & drop | P0 |
| Fade level slider | 10%-60%, snap ke preset | P0 |
| Preview panel | Render 1 halaman dengan setting saat ini | P0 |
| Progress bar | Per halaman, dengan persentase | P0 |
| Tombol Proses | Mulai batch processing semua halaman | P0 |
| Output path picker | Dialog simpan file | P0 |
| Notifikasi selesai | Dialog sukses dengan tombol buka folder | P1 |

### 5.3 CLI (Alternatif)

```bash
# Basic
python main.py input.pdf

# Dengan opsi
python main.py input.pdf --output output.pdf --opacity 0.2 --keep-waqf --dpi 300
```

---

## 6. Spesifikasi Non-Fungsional

| Aspek | Requirement |
|---|---|
| Platform | Windows 10/11 (utama), Mac/Linux secondary |
| Python | 3.9+ |
| Offline | 100%, tidak ada network call |
| Memory | Maks 500 MB RAM saat proses (stream per halaman) |
| Kecepatan | 1 halaman/detik pada mesin standar (i5, 8 GB RAM) |
| Kualitas output | 300 DPI default, border tajam, teks fade merata |
| File size output | Kurang dari 2x ukuran input |

---

## 7. Batasan Produk (Out of Scope v1.0)

Hal-hal berikut TIDAK termasuk dalam versi pertama:

- OCR (mengenali teks Arab secara semantik)
- Pilihan halaman tertentu (hanya semua halaman atau tidak sama sekali)
- Cloud storage atau berbagi file
- Aplikasi mobile
- Dukungan format selain PDF (gambar, Word, dll)
- Pembuatan soal atau latihan interaktif
- Deteksi otomatis jenis Al-Qur'an/mushaf

---

## 8. Risiko dan Mitigasi

| Risiko | Kemungkinan | Dampak | Mitigasi |
|---|---|---|---|
| Border ikut terfade | Tinggi | Tinggi | Region detection sebelum fade, threshold adjustable |
| PDF dengan layout berbeda tidak terdeteksi | Sedang | Sedang | Parameter margin bisa diatur manual |
| Proses terlalu lambat di mesin lama | Sedang | Rendah | Opsi DPI rendah (150), stream per halaman |
| Kualitas fade tidak merata | Sedang | Tinggi | Preview sebelum proses, opsi ulang dengan setting berbeda |
| File PDF terproteksi/enkripsi | Rendah | Rendah | Pesan error yang jelas, minta PDF yang tidak diproteksi |

---

## 9. Acceptance Criteria (DoD)

Produk dianggap selesai jika:

- [ ] JUZ 1 PDF yang diberikan klien bisa diproses tanpa error
- [ ] Border ornamen halaman tetap hitam di output
- [ ] Teks Arab terlihat samar (setidaknya di level 20%)
- [ ] Waktu proses 24 halaman < 5 menit di mesin standar
- [ ] Output bisa dicetak langsung dari PDF viewer
- [ ] Guru bisa menggunakan tanpa panduan teknis (3 klik)
- [ ] Tidak ada dependensi internet sama sekali
