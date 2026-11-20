# Wireframes - Trace Qur'an GUI

> Aplikasi Python desktop (Tkinter). Single-window, 3-panel layout.

---

## Layar Utama (Single Window)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Trace Qur'an                                              [_ □ ×]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─── PANEL KIRI (Settings) ──────┐  ┌─── PANEL KANAN (Preview) ──┐│
│  │                                │  │                             ││
│  │  [FILE INPUT]                  │  │                             ││
│  │  ┌────────────────────────┐    │  │   [PREVIEW HALAMAN]        ││
│  │  │  Drag PDF ke sini      │    │  │                             ││
│  │  │  atau klik untuk pilih │    │  │   Belum ada file dipilih   ││
│  │  └────────────────────────┘    │  │                             ││
│  │  juz1.pdf (30 MB, 24 hal)      │  │   ← Pilih file PDF dulu    ││
│  │                                │  │      untuk melihat preview  ││
│  │  [FADE LEVEL]                  │  │                             ││
│  │  ○ Sangat Samar (15%)          │  │                             ││
│  │  ● Samar (25%)         ◄ def   │  │                             ││
│  │  ○ Agak Terlihat (40%)         │  │                             ││
│  │                                │  │                             ││
│  │  Custom: [━━━━━●────] 25%      │  │                             ││
│  │                                │  │                             ││
│  │  [OPSI TAMBAHAN]               │  │                             ││
│  │  ☑ Pertahankan border          │  │                             ││
│  │  ☑ Pertahankan tanda waqf      │  │                             ││
│  │  ☐ Pertahankan nomor ayat      │  │                             ││
│  │                                │  │                             ││
│  │  [HALAMAN PREVIEW]             │  │                             ││
│  │  Halaman: [1  ▼]  [Refresh]    │  │                             ││
│  │                                │  │                             ││
│  │  [OUTPUT]                      │  │                             ││
│  │  Simpan ke:                    │  │                             ││
│  │  [juz1_trace.pdf    ] [Ubah]   │  │                             ││
│  │                                │  │                             ││
│  │  Kualitas:  ○ Draft (150 DPI)  │  │                             ││
│  │             ● Cetak (300 DPI)  │  │                             ││
│  │                                │  │                             ││
│  │  ┌────────────────────────┐    │  │                             ││
│  │  │   PROSES SEMUA (24)    │    │  │                             ││
│  │  └────────────────────────┘    │  │                             ││
│  │                                │  │                             ││
│  └────────────────────────────────┘  └─────────────────────────────┘│
│                                                                     │
│  Status: Siap                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## State: File Dipilih, Preview Aktif

```
┌─────────────────────────────────────────────────────────────────────┐
│  Trace Qur'an - juz1.pdf                                  [_ □ ×]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─── PANEL KIRI (Settings) ──────┐  ┌─── PANEL KANAN (Preview) ──┐│
│  │                                │  │                             ││
│  │  [FILE INPUT]                  │  │  ┌───────────────────────┐  ││
│  │  ✓ juz1.pdf                    │  │  │  ╔═══════════════════╗ │  ││
│  │    30 MB · 24 halaman  [Ganti] │  │  │  ║  بِسۡمِ ٱللَّهِ      ║ │  ││
│  │                                │  │  │  ║  ٱلرَّحۡمَـٰنِ        ║ │  ││
│  │  [FADE LEVEL]                  │  │  │  ║  ٱلرَّحِیمِ           ║ │  ││
│  │  ○ Sangat Samar (15%)          │  │  │  ║                   ║ │  ││
│  │  ● Samar (25%)                 │  │  │  ║  [teks Arab samar]║ │  ││
│  │  ○ Agak Terlihat (40%)         │  │  │  ╚═══════════════════╝ │  ││
│  │                                │  │  └───────────────────────┘  ││
│  │  Custom: [━━━━━●────] 25%      │  │                             ││
│  │                                │  │  Halaman 1 dari 24          ││
│  │  [OPSI TAMBAHAN]               │  │  [◄ Prev]      [Next ►]     ││
│  │  ☑ Pertahankan border          │  │                             ││
│  │  ☑ Pertahankan tanda waqf      │  │                             ││
│  │  ☐ Pertahankan nomor ayat      │  │                             ││
│  │                                │  │                             ││
│  │  [OUTPUT]                      │  │                             ││
│  │  [juz1_trace.pdf    ] [Ubah]   │  │                             ││
│  │                                │  │                             ││
│  │  Kualitas: ● Cetak (300 DPI)   │  │                             ││
│  │                                │  │                             ││
│  │  ┌────────────────────────┐    │  │                             ││
│  │  │   PROSES SEMUA (24)    │    │  │                             ││
│  │  └────────────────────────┘    │  │                             ││
│  │                                │  │                             ││
│  └────────────────────────────────┘  └─────────────────────────────┘│
│                                                                     │
│  Status: Preview halaman 1 selesai (0.8 detik)                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## State: Sedang Proses

```
┌─────────────────────────────────────────────────────────────────────┐
│  Trace Qur'an - Memproses...                              [_ □ ×]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─── PANEL KIRI (Settings) ──────┐  ┌─── PANEL KANAN (Preview) ──┐│
│  │                                │  │                             ││
│  │  [FILE INPUT]                  │  │  ┌───────────────────────┐  ││
│  │  ✓ juz1.pdf · 24 halaman       │  │  │                       │  ││
│  │                                │  │  │   [Preview halaman 1] │  ││
│  │  [FADE LEVEL]                  │  │  │   (tidak berubah saat │  ││
│  │  ● Samar (25%)                 │  │  │    proses berlangsung)│  ││
│  │                                │  │  │                       │  ││
│  │  [semua kontrol disabled]      │  │  └───────────────────────┘  ││
│  │                                │  │                             ││
│  │  ┌────────────────────────┐    │  │                             ││
│  │  │  PROSES BERJALAN...    │    │  │                             ││
│  │  └────────────────────────┘    │  │                             ││
│  │                                │  │                             ││
│  │  Memproses halaman 8 dari 24   │  │                             ││
│  │  [████████████░░░░░░░░░░] 33%  │  │                             ││
│  │                                │  │                             ││
│  │  Estimasi: 32 detik lagi       │  │                             ││
│  │                                │  │                             ││
│  │  [Batalkan]                    │  │                             ││
│  │                                │  │                             ││
│  └────────────────────────────────┘  └─────────────────────────────┘│
│                                                                     │
│  Status: Memproses halaman 8/24...                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## State: Selesai

```
┌─────────────────────────────────────────────────────────────────────┐
│  Trace Qur'an                                              [_ □ ×]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                │ │
│  │  ✓  Selesai!                                                  │ │
│  │                                                                │ │
│  │  juz1_trace.pdf berhasil dibuat                               │ │
│  │  24 halaman · 28.4 MB · Waktu proses: 48 detik               │ │
│  │                                                                │ │
│  │  [Buka File]    [Buka Folder]    [Proses PDF Lain]            │ │
│  │                                                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Status: Selesai                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## State: Error

```
┌─────────────────────────────────────────────────────────────────────┐
│  Trace Qur'an                                              [_ □ ×]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                │ │
│  │  ✗  Gagal memproses                                           │ │
│  │                                                                │ │
│  │  File PDF terproteksi dengan password.                        │ │
│  │  Gunakan PDF tanpa proteksi.                                  │ │
│  │                                                                │ │
│  │  Detail: fitz.FitzError: cannot authenticate                  │ │
│  │  [Lihat Log]                           [Tutup]                │ │
│  │                                                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Status: Error - PDF terproteksi                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Flow Diagram

```
[Buka Aplikasi]
       |
       v
[Layar Utama - Empty State]
       |
       v (drag PDF / klik pilih)
[File Dipilih]
       |
       ├──> [Preview otomatis halaman 1]
       |
       v (atur slider, opsi)
[Settings Dikonfigurasi]
       |
       v (klik Proses Semua)
[Proses Berjalan - progress bar per halaman]
       |
       ├──> [Error] ──> [Pesan error] ──> [Kembali ke Settings]
       |
       v (semua halaman selesai)
[Dialog Sukses]
       |
       ├──> [Buka File] ──> PDF viewer OS
       ├──> [Buka Folder] ──> File explorer
       └──> [Proses PDF Lain] ──> Reset ke Empty State
```

---

## Komponen UI (Tkinter)

| Komponen | Widget Tkinter | Catatan |
|---|---|---|
| Window utama | `tk.Tk` | Resizable, min 900x600 |
| Panel kiri | `ttk.Frame` | Lebar tetap 300px |
| Panel kanan | `ttk.Frame` | Expand mengisi sisa |
| File drop zone | `tk.Canvas` | Custom drag & drop binding |
| Radio buttons | `ttk.Radiobutton` | 3 preset fade |
| Slider | `ttk.Scale` | Horizontal, range 10-60 |
| Checkboxes | `ttk.Checkbutton` | Opsi border/waqf/nomor |
| Preview image | `tk.Label` + `PhotoImage` | PIL ImageTk |
| Progress bar | `ttk.Progressbar` | Determinate mode |
| Tombol utama | `ttk.Button` | Custom style |
| Status bar | `tk.Label` | Di bawah window |
