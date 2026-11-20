"""
gui/app.py
Aplikasi Desktop Windows - Trace Qur'an (Duta Ilmu)
Engine: PyMuPDF + OpenCV (300 DPI High-Precision)
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import os
from PIL import Image, ImageTk

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    COLORS, FONTS, WINDOW_MIN_W, WINDOW_MIN_H, PANEL_LEFT_W,
    FADE_PRESETS, FADE_DEFAULT, FADE_MIN, FADE_MAX,
    DPI_PRINT, DPI_DRAFT, DPI_PREVIEW,
)
from processor import process_pdf, preview_page
from processor.pdf_writer import build_output_path
from processor.pdf_reader import open_pdf, render_page, page_count


class TraceQuranApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trace Qur'an - Duta Ilmu")
        self.minsize(1040, 720)
        self.geometry("1100x780")
        self.configure(bg="#F4F6F8")

        # State
        self._pdf_path: str | None = None
        self._total_pages: int = 0
        self._preview_page_num: int = 0
        self._cancel_flag: list[bool] = [False]
        self._processing: bool = False
        self._preview_mode: str = "trace"  # "trace" atau "original"
        self._output_folder: Path | None = None
        self._last_trace_img: Image.Image | None = None
        self._last_orig_img: Image.Image | None = None
        self._preview_timer = None

        # Tkinter variables
        self._model_var = tk.StringVar(value="gray")
        self._fade_preset = tk.StringVar(value=FADE_DEFAULT)
        self._opacity_var = tk.DoubleVar(value=FADE_PRESETS[FADE_DEFAULT])
        self._keep_border = tk.BooleanVar(value=True)
        self._keep_waqf = tk.BooleanVar(value=True)
        self._keep_ayat = tk.BooleanVar(value=True)
        self._dpi_var = tk.StringVar(value="Cetak (300 DPI)")
        self._output_folder_var = tk.StringVar(value="")
        self._output_filename_var = tk.StringVar(value="")
        self._status_var = tk.StringVar(value="Siap - Silakan pilih file PDF Al-Qur'an")
        self._progress_var = tk.DoubleVar(value=0.0)
        self._progress_label_var = tk.StringVar(value="")

        # Watchers untuk Auto-Preview
        self._model_var.trace_add("write", lambda *_: self._schedule_preview())
        self._fade_preset.trace_add("write", self._on_preset_change)

        self._build_ui()
        self._setup_keybindings()

    # ── UI Builder ──────────────────────────────────────────────────────────

    def _build_ui(self):
        # 1. Header Banner Atas
        self._build_top_header()

        # 2. Body Container (Left Settings + Right Preview)
        body = tk.Frame(self, bg="#F4F6F8")
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        # Left panel (Settings)
        left_card = tk.Frame(body, bg="#FFFFFF", width=380, highlightthickness=1, highlightbackground="#E2E8F0")
        left_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=4)
        left_card.pack_propagate(False)

        # Right panel (Preview)
        right_card = tk.Frame(body, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E2E8F0")
        right_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=4)

        self._build_left_panel(left_card)
        self._build_right_panel(right_card)

        # 3. Status Bar Bawah
        status_bar = tk.Frame(self, bg="#FFFFFF", height=30, highlightthickness=1, highlightbackground="#E2E8F0")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            status_bar,
            textvariable=self._status_var,
            bg="#FFFFFF",
            fg="#64748B",
            font=("Segoe UI", 9),
            anchor="w",
            padx=14,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _build_top_header(self):
        header = tk.Frame(self, bg="#0F5132", height=64)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        content = tk.Frame(header, bg="#0F5132")
        content.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        # Title & Badge
        title_row = tk.Frame(content, bg="#0F5132")
        title_row.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            title_row,
            text="TRACE QUR'AN",
            font=("Segoe UI", 15, "bold"),
            bg="#0F5132",
            fg="#FFFFFF",
        ).pack(side=tk.LEFT)

        badge = tk.Label(
            title_row,
            text=" DUTA ILMU ",
            font=("Segoe UI", 9, "bold"),
            bg="#D1E7DD",
            fg="#0F5132",
            padx=6,
            pady=2,
        )
        badge.pack(side=tk.LEFT, padx=8)

        tk.Label(
            content,
            text="Aplikasi Pembuat Lembar Latihan Menulis Kaligrafi Al-Qur'an (300 DPI High-Precision)",
            font=("Segoe UI", 9),
            bg="#0F5132",
            fg="#A3CFBB",
        ).pack(side=tk.BOTTOM, anchor="w", pady=(2, 0))

        # Status badge di kanan
        self._badge_ready = tk.Label(
            content,
            text="● Siap Digunakan",
            font=("Segoe UI", 9, "bold"),
            bg="#0F5132",
            fg="#75B798",
        )
        self._badge_ready.pack(side=tk.RIGHT, anchor="center")

    def _build_left_panel(self, parent):
        canvas = tk.Canvas(parent, bg="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        frame = tk.Frame(canvas, bg="#FFFFFF")
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw", width=360)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        p = 14

        # ── 1. Upload File PDF ─────────────────────────────────────────────
        _section_header(frame, "1. UPLOAD FILE PDF")
        
        self._upload_box = tk.Frame(frame, bg="#F8FAFC", highlightthickness=1, highlightbackground="#CBD5E1", padx=10, pady=12)
        self._upload_box.pack(fill=tk.X, padx=p, pady=(4, 6))

        self._btn_pick_file = tk.Button(
            self._upload_box,
            text="📂 Pilih File PDF Al-Qur'an",
            command=self._pick_pdf_dialog,
            font=("Segoe UI", 10, "bold"),
            bg="#198754",
            fg="#FFFFFF",
            activebackground="#157347",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            cursor="hand2",
            pady=8,
        )
        self._btn_pick_file.pack(fill=tk.X)

        self._upload_hint = tk.Label(
            self._upload_box,
            text="Klik tombol di atas untuk memilih Mushaf PDF",
            font=("Segoe UI", 8),
            bg="#F8FAFC",
            fg="#64748B",
            pady=4,
        )
        self._upload_hint.pack()

        # File Selected Card (tersembunyi sampai file dipilih)
        self._file_card = tk.Frame(frame, bg="#E8F5E9", highlightthickness=1, highlightbackground="#A5D6A7", padx=10, pady=8)
        self._file_name_lbl = tk.Label(
            self._file_card, text="", font=("Segoe UI", 9, "bold"),
            bg="#E8F5E9", fg="#1B5E20", anchor="w", wraplength=260
        )
        self._file_name_lbl.pack(fill=tk.X)
        self._file_meta_lbl = tk.Label(
            self._file_card, text="", font=("Segoe UI", 8),
            bg="#E8F5E9", fg="#2E7D32", anchor="w"
        )
        self._file_meta_lbl.pack(fill=tk.X, pady=(2, 0))

        _divider(frame)

        # ── 2. Model Tracing ───────────────────────────────────────────────
        _section_header(frame, "2. PILIH MODEL TRACING")
        model_box = tk.Frame(frame, bg="#FFFFFF")
        model_box.pack(fill=tk.X, padx=p, pady=2)

        # Model A Card
        rb_a = tk.Radiobutton(
            model_box,
            text=" Model A: Light Gray\n  Tulisan Arab jadi abu-abu tipis (standar FunFurqan)",
            variable=self._model_var,
            value="gray",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#1E293B",
            selectcolor="#D1E7DD",
            activebackground="#FFFFFF",
            justify=tk.LEFT,
        )
        rb_a.pack(anchor="w", pady=(0, 6))

        # Model B Card
        rb_b = tk.Radiobutton(
            model_box,
            text=" Model B: Outline (Hollow)\n  Garis tepi kaligrafi tipis, huruf berongga putih",
            variable=self._model_var,
            value="outline",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#1E293B",
            selectcolor="#D1E7DD",
            activebackground="#FFFFFF",
            justify=tk.LEFT,
        )
        rb_b.pack(anchor="w")

        _divider(frame)

        # ── 3. Tingkat Kepekatan Samar ───────────────────────────────────
        _section_header(frame, "3. TINGKAT KEPEKATAN ABU-ABU")
        preset_row = tk.Frame(frame, bg="#FFFFFF")
        preset_row.pack(fill=tk.X, padx=p, pady=2)

        for label in ["Sangat Samar", "Samar", "Agak Terlihat"]:
            pct_val = int(FADE_PRESETS[label] * 100)
            tk.Radiobutton(
                preset_row,
                text=f"{label} ({pct_val}%)",
                variable=self._fade_preset,
                value=label,
                font=("Segoe UI", 9),
                bg="#FFFFFF",
                fg="#1E293B",
                selectcolor="#D1E7DD",
                activebackground="#FFFFFF",
            ).pack(anchor="w", pady=1)

        slider_box = tk.Frame(frame, bg="#FFFFFF")
        slider_box.pack(fill=tk.X, padx=p, pady=(6, 0))
        tk.Label(slider_box, text="Slider:", font=("Segoe UI", 9), bg="#FFFFFF", fg="#64748B").pack(side=tk.LEFT)
        self._slider = ttk.Scale(
            slider_box, from_=FADE_MIN, to=FADE_MAX,
            orient=tk.HORIZONTAL, variable=self._opacity_var,
            command=self._on_slider_move,
        )
        self._slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self._slider.bind("<ButtonRelease-1>", lambda e: self._schedule_preview())

        self._slider_pct_label = tk.Label(
            slider_box, text=f"{int(self._opacity_var.get()*100)}%",
            font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#198754", width=5,
        )
        self._slider_pct_label.pack(side=tk.LEFT)

        _divider(frame)

        # ── 4. Pertahankan Hitam ──────────────────────────────────────────
        _section_header(frame, "4. ELEMEN TETAP HITAM PEKAT")
        for text, var in [
            ("Border ornamen halaman mushaf", self._keep_border),
            ("Tanda waqf margin ('ع' waqf lazim & ruku')", self._keep_waqf),
            ("Nomor ayat dalam lingkaran roset", self._keep_ayat),
        ]:
            cb = tk.Checkbutton(
                frame, text=text, variable=var,
                font=("Segoe UI", 9), bg="#FFFFFF", fg="#1E293B",
                selectcolor="#D1E7DD", activebackground="#FFFFFF",
                command=self._schedule_preview,
            )
            cb.pack(anchor="w", padx=p, pady=1)

        _divider(frame)

        # ── 5. Folder Penyimpanan Output ──────────────────────────────────
        _section_header(frame, "5. FOLDER PENYIMPANAN OUTPUT")
        out_box = tk.Frame(frame, bg="#F8FAFC", highlightthickness=1, highlightbackground="#CBD5E1", padx=10, pady=8)
        out_box.pack(fill=tk.X, padx=p, pady=2)

        self._btn_pick_folder = tk.Button(
            out_box,
            text="📁 Pilih Folder Penyimpanan...",
            command=self._pick_folder_dialog,
            font=("Segoe UI", 9, "bold"),
            bg="#F1F5F9",
            fg="#1E293B",
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
            pady=4,
            highlightthickness=1,
            highlightbackground="#CBD5E1",
        )
        self._btn_pick_folder.pack(fill=tk.X, pady=(0, 4))

        self._folder_label = tk.Label(
            out_box,
            text="Folder: (Sama dengan folder file PDF)",
            font=("Segoe UI", 8),
            bg="#F8FAFC",
            fg="#64748B",
            anchor="w",
            wraplength=320,
            justify=tk.LEFT,
        )
        self._folder_label.pack(fill=tk.X)

        self._filename_label = tk.Label(
            out_box,
            text="Nama Hasil: -",
            font=("Segoe UI", 8, "bold"),
            bg="#F8FAFC",
            fg="#198754",
            anchor="w",
            pady=2,
        )
        self._filename_label.pack(fill=tk.X)

        # Kualitas Cetak
        dpi_row = tk.Frame(frame, bg="#FFFFFF")
        dpi_row.pack(fill=tk.X, padx=p, pady=(8, 0))
        tk.Label(dpi_row, text="Kualitas:", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#1E293B").pack(side=tk.LEFT)
        for txt in ["Cetak (300 DPI)", "Draft (150 DPI)"]:
            tk.Radiobutton(
                dpi_row, text=txt, variable=self._dpi_var, value=txt,
                font=("Segoe UI", 9), bg="#FFFFFF", fg="#1E293B",
                selectcolor="#D1E7DD", activebackground="#FFFFFF",
            ).pack(side=tk.LEFT, padx=(6, 0))

        _divider(frame)

        # ── 6. Progress & Tombol Eksekusi ─────────────────────────────────
        self._progress_label = tk.Label(
            frame, textvariable=self._progress_label_var,
            font=("Segoe UI", 9), bg="#FFFFFF", fg="#64748B", anchor="w",
        )
        self._progress_label.pack(fill=tk.X, padx=p, pady=(4, 2))

        self._progress_bar = ttk.Progressbar(
            frame, variable=self._progress_var, maximum=100, mode="determinate"
        )
        self._progress_bar.pack(fill=tk.X, padx=p, pady=(0, 10))

        self._btn_process = tk.Button(
            frame,
            text="⚡ PROSES & UNDUH SEMUA HALAMAN (300 DPI)",
            command=self._do_process,
            font=("Segoe UI", 10, "bold"),
            bg="#198754",
            fg="#FFFFFF",
            activebackground="#157347",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            cursor="hand2",
            pady=10,
        )
        self._btn_process.pack(fill=tk.X, padx=p, pady=(0, 6))

        self._btn_cancel = tk.Button(
            frame, text="Batalkan Proses", command=self._do_cancel,
            font=("Segoe UI", 9), bg="#FFFFFF", fg="#DC3545",
            relief=tk.FLAT, cursor="hand2", pady=4, state=tk.DISABLED,
        )
        self._btn_cancel.pack(fill=tk.X, padx=p, pady=(0, p))

    def _build_right_panel(self, parent):
        # 1. Header Preview Bar
        bar = tk.Frame(parent, bg="#FFFFFF", height=48, highlightthickness=1, highlightbackground="#E2E8F0")
        bar.pack(fill=tk.X, side=tk.TOP)
        bar.pack_propagate(False)

        # Kiri: Mode Toggle (Hasil Tracing vs Gambar Asli)
        tabs_box = tk.Frame(bar, bg="#FFFFFF")
        tabs_box.pack(side=tk.LEFT, padx=12)

        self._btn_mode_trace = tk.Button(
            tabs_box, text="✨ Hasil Tracing", font=("Segoe UI", 9, "bold"),
            bg="#198754", fg="#FFFFFF", relief=tk.FLAT, padx=10, pady=4, cursor="hand2",
            command=lambda: self._set_preview_mode("trace"),
        )
        self._btn_mode_trace.pack(side=tk.LEFT, padx=(0, 4))

        self._btn_mode_orig = tk.Button(
            tabs_box, text="📖 Gambar Asli", font=("Segoe UI", 9),
            bg="#F1F5F9", fg="#475569", relief=tk.FLAT, padx=10, pady=4, cursor="hand2",
            command=lambda: self._set_preview_mode("original"),
        )
        self._btn_mode_orig.pack(side=tk.LEFT)

        # Kanan: Navigasi Halaman
        nav_box = tk.Frame(bar, bg="#FFFFFF")
        nav_box.pack(side=tk.RIGHT, padx=12)

        self._btn_prev = tk.Button(
            nav_box, text="◀ Prev", font=("Segoe UI", 9, "bold"),
            bg="#F1F5F9", fg="#1E293B", relief=tk.FLAT, padx=8, pady=3, cursor="hand2",
            command=self._prev_page,
        )
        self._btn_prev.pack(side=tk.LEFT, padx=2)

        tk.Label(nav_box, text="Hal", font=("Segoe UI", 9), bg="#FFFFFF", fg="#64748B").pack(side=tk.LEFT, padx=(4, 2))

        self._page_spin = ttk.Spinbox(
            nav_box, from_=1, to=1, width=4, font=("Segoe UI", 9),
            command=self._on_page_spin_change,
        )
        self._page_spin.pack(side=tk.LEFT, padx=2)
        self._page_spin.set(1)
        self._page_spin.bind("<Return>", lambda e: self._on_page_spin_change())

        self._total_pages_lbl = tk.Label(
            nav_box, text="/ 0", font=("Segoe UI", 9), bg="#FFFFFF", fg="#64748B"
        )
        self._total_pages_lbl.pack(side=tk.LEFT, padx=(2, 6))

        self._btn_next = tk.Button(
            nav_box, text="Next ▶", font=("Segoe UI", 9, "bold"),
            bg="#F1F5F9", fg="#1E293B", relief=tk.FLAT, padx=8, pady=3, cursor="hand2",
            command=self._next_page,
        )
        self._btn_next.pack(side=tk.LEFT, padx=2)

        # 2. Preview Canvas
        self._preview_canvas = tk.Canvas(
            parent, bg="#EEEDE9", highlightthickness=0, cursor="arrow"
        )
        self._preview_canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        self._preview_canvas.bind("<Configure>", self._on_canvas_resize)
        self._preview_placeholder()

    def _setup_keybindings(self):
        self.bind("<Left>", lambda e: self._prev_page())
        self.bind("<Right>", lambda e: self._next_page())

    # ── Logic & Handlers ────────────────────────────────────────────────────

    def _pick_pdf_dialog(self):
        path = filedialog.askopenfilename(
            title="Pilih File Al-Qur'an PDF",
            filetypes=[("PDF files", "*.pdf"), ("Semua File", "*.*")],
        )
        if path:
            self._load_pdf(path)

    def _pick_folder_dialog(self):
        initial = str(self._output_folder) if self._output_folder else ""
        folder = filedialog.askdirectory(title="Pilih Folder Penyimpanan Output", initialdir=initial)
        if folder:
            self._output_folder = Path(folder)
            self._folder_label.config(text=f"Folder: {self._output_folder}")
            self._update_output_preview()

    def _load_pdf(self, path: str):
        try:
            doc = open_pdf(path)
            self._total_pages = page_count(doc)
            doc.close()
        except Exception as e:
            messagebox.showerror("Gagal Membuka File", f"File PDF tidak valid:\n{e}")
            return

        self._pdf_path = path
        p = Path(path)

        # Update card file
        size_mb = p.stat().st_size / (1024 * 1024)
        self._file_name_lbl.config(text=f"✓ {p.name}")
        self._file_meta_lbl.config(text=f"{self._total_pages} Halaman  •  {size_mb:.1f} MB")
        self._file_card.pack(fill=tk.X, padx=14, pady=(0, 6), after=self._upload_box)
        self._upload_hint.config(text="File siap diproses")
        self._btn_pick_file.config(text="🔄 Ganti File PDF...")

        # Update pagination
        self._preview_page_num = 0
        self._page_spin.config(to=self._total_pages)
        self._page_spin.set(1)
        self._total_pages_lbl.config(text=f"/ {self._total_pages}")

        # Update folder output default
        if self._output_folder is None:
            self._output_folder = p.parent
            self._folder_label.config(text=f"Folder: {self._output_folder}")

        self._update_output_preview()
        self.title(f"Trace Qur'an - {p.name}")
        self._status(f"File {p.name} dimuat ({self._total_pages} halaman). Memuat preview...")
        self._do_preview()

    def _update_output_preview(self):
        if not self._pdf_path:
            return
        p = Path(self._pdf_path)
        stem = p.stem
        model_suffix = "_trace_outline.pdf" if self._model_var.get() == "outline" else "_trace.pdf"
        out_name = f"{stem}{model_suffix}"
        self._filename_label.config(text=f"Nama File: {out_name}")

    def _set_preview_mode(self, mode: str):
        self._preview_mode = mode
        if mode == "trace":
            self._btn_mode_trace.config(bg="#198754", fg="#FFFFFF")
            self._btn_mode_orig.config(bg="#F1F5F9", fg="#475569")
            if self._last_trace_img:
                self._show_pil_in_canvas(self._last_trace_img)
            else:
                self._do_preview()
        else:
            self._btn_mode_orig.config(bg="#198754", fg="#FFFFFF")
            self._btn_mode_trace.config(bg="#F1F5F9", fg="#475569")
            if self._last_orig_img:
                self._show_pil_in_canvas(self._last_orig_img)
            else:
                self._do_preview()

    def _prev_page(self):
        if not self._pdf_path or self._preview_page_num <= 0:
            return
        self._preview_page_num -= 1
        self._page_spin.set(self._preview_page_num + 1)
        self._do_preview()

    def _next_page(self):
        if not self._pdf_path or self._preview_page_num >= self._total_pages - 1:
            return
        self._preview_page_num += 1
        self._page_spin.set(self._preview_page_num + 1)
        self._do_preview()

    def _on_page_spin_change(self):
        try:
            n = int(self._page_spin.get()) - 1
            n = max(0, min(n, self._total_pages - 1))
            if n != self._preview_page_num:
                self._preview_page_num = n
                self._do_preview()
        except ValueError:
            pass

    def _on_preset_change(self, *_):
        preset = self._fade_preset.get()
        if preset in FADE_PRESETS:
            self._opacity_var.set(FADE_PRESETS[preset])
            self._slider_pct_label.config(text=f"{int(FADE_PRESETS[preset]*100)}%")
            self._schedule_preview()

    def _on_slider_move(self, val):
        pct = int(float(val) * 100)
        self._slider_pct_label.config(text=f"{pct}%")

    def _schedule_preview(self):
        self._update_output_preview()
        if self._preview_timer is not None:
            self.after_cancel(self._preview_timer)
        self._preview_timer = self.after(250, self._do_preview)

    def _do_preview(self):
        if not self._pdf_path or self._processing:
            return
        self._status(f"Merender preview halaman {self._preview_page_num + 1}...")

        def _run():
            try:
                # Render gambar asli untuk tab "Gambar Asli"
                doc = open_pdf(self._pdf_path)
                orig_img = render_page(doc, self._preview_page_num, dpi=DPI_PREVIEW)
                doc.close()
                self._last_orig_img = orig_img

                # Render gambar hasil trace
                trace_img = preview_page(
                    self._pdf_path,
                    page_num=self._preview_page_num,
                    model=self._model_var.get(),
                    opacity=self._opacity_var.get(),
                    keep_waqf=self._keep_waqf.get(),
                    keep_ayat=self._keep_ayat.get(),
                    dpi=DPI_PREVIEW,
                )
                self._last_trace_img = trace_img

                def _update_ui():
                    target = trace_img if self._preview_mode == "trace" else orig_img
                    self._show_pil_in_canvas(target)
                    self._status(f"Preview halaman {self._preview_page_num + 1} siap.")

                self.after(0, _update_ui)
            except Exception as e:
                self.after(0, lambda: self._status(f"Error preview: {e}"))

        threading.Thread(target=_run, daemon=True).start()

    def _show_pil_in_canvas(self, img: Image.Image):
        canvas = self._preview_canvas
        cw = canvas.winfo_width() or 600
        ch = canvas.winfo_height() or 650

        iw, ih = img.size
        scale = min((cw - 24) / iw, (ch - 24) / ih, 1.0)
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
        thumb = img.resize((nw, nh), Image.LANCZOS)

        tk_img = ImageTk.PhotoImage(thumb)
        canvas.delete("all")
        canvas.create_image(cw // 2, ch // 2, anchor=tk.CENTER, image=tk_img)
        canvas._tk_img = tk_img

    def _preview_placeholder(self):
        self._preview_canvas.delete("all")
        w = self._preview_canvas.winfo_width() or 600
        h = self._preview_canvas.winfo_height() or 650
        self._preview_canvas.create_text(
            w // 2, h // 2,
            text="Silakan pilih file PDF Mushaf Al-Qur'an untuk melihat preview halaman.",
            fill="#94A3B8", font=("Segoe UI", 11),
        )

    def _on_canvas_resize(self, event):
        img = self._last_trace_img if self._preview_mode == "trace" else self._last_orig_img
        if img:
            self._show_pil_in_canvas(img)

    # ── Eksekusi & Notifikasi Lengkap ────────────────────────────────────────

    def _do_process(self):
        if not self._pdf_path:
            messagebox.showwarning("File Belum Dipilih", "Silakan pilih file PDF Al-Qur'an terlebih dahulu.")
            return
        if self._processing:
            return

        p = Path(self._pdf_path)
        model = self._model_var.get()
        model_suffix = "_trace_outline.pdf" if model == "outline" else "_trace.pdf"
        out_folder = self._output_folder or p.parent
        out_path = out_folder / f"{p.stem}{model_suffix}"

        dpi = DPI_PRINT if "300" in self._dpi_var.get() else DPI_DRAFT
        self._processing = True
        self._cancel_flag[0] = False
        self._btn_process.config(state=tk.DISABLED, bg="#94A3B8")
        self._btn_cancel.config(state=tk.NORMAL)
        self._progress_var.set(0)
        self._progress_label_var.set(f"Memproses 0 dari {self._total_pages} halaman...")
        self._status("Proses dimulai...")

        def _run():
            try:
                result = process_pdf(
                    self._pdf_path,
                    output_path=out_path,
                    model=model,
                    opacity=self._opacity_var.get(),
                    keep_border=self._keep_border.get(),
                    keep_waqf=self._keep_waqf.get(),
                    keep_ayat=self._keep_ayat.get(),
                    dpi=dpi,
                    progress_callback=self._on_progress,
                    cancel_flag=self._cancel_flag,
                )
                self.after(0, lambda: self._on_process_done(result))
            except InterruptedError:
                self.after(0, self._on_process_cancelled)
            except Exception as e:
                self.after(0, lambda: self._on_process_error(str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _on_progress(self, done: int, total: int):
        pct = done / total * 100
        self.after(0, lambda: self._progress_var.set(pct))
        self.after(0, lambda: self._progress_label_var.set(
            f"Memproses halaman {done} dari {total} ({int(pct)}%)..."
        ))
        self.after(0, lambda: self._status(f"Sedang memproses halaman {done}/{total}..."))

    def _on_process_done(self, result_path: Path):
        self._processing = False
        self._btn_process.config(state=tk.NORMAL, bg="#198754")
        self._btn_cancel.config(state=tk.DISABLED)
        self._progress_var.set(100)
        self._progress_label_var.set(f"Selesai! {self._total_pages} halaman berhasil diproses.")
        self._status(f"Selesai tersimpan di: {result_path.name}")

        # Bunyikan notifikasi lonceng sistem
        try:
            self.bell()
        except Exception:
            pass

        # Tampilkan Modal Pop-up Sukses yang Jelas
        self._show_success_modal(result_path)

    def _show_success_modal(self, result_path: Path):
        dlg = tk.Toplevel(self)
        dlg.title("🎉 Tracing Selesai - Duta Ilmu")
        dlg.geometry("520x360")
        dlg.resizable(False, False)
        dlg.configure(bg="#FFFFFF")
        dlg.transient(self)
        dlg.grab_set()

        # Center modal
        dlg.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 520) // 2
        y = self.winfo_y() + (self.winfo_height() - 360) // 2
        dlg.geometry(f"+{x}+{y}")

        content = tk.Frame(dlg, bg="#FFFFFF", padx=24, pady=20)
        content.pack(fill=tk.BOTH, expand=True)

        # Header Icon & Title
        tk.Label(content, text="🎉", font=("Segoe UI", 32), bg="#FFFFFF").pack()
        tk.Label(
            content, text="PROSES SELESAI!",
            font=("Segoe UI", 16, "bold"), bg="#FFFFFF", fg="#198754",
        ).pack(pady=(4, 2))

        tk.Label(
            content,
            text=f"Seluruh {self._total_pages} halaman berhasil diproses dengan kualitas cetak 300 DPI.",
            font=("Segoe UI", 10), bg="#FFFFFF", fg="#475569",
        ).pack(pady=(0, 14))

        # File Info Card
        info_card = tk.Frame(content, bg="#F8FAFC", highlightthickness=1, highlightbackground="#E2E8F0", padx=12, pady=10)
        info_card.pack(fill=tk.X, pady=(0, 16))

        tk.Label(
            info_card, text=f"📄 File: {result_path.name}",
            font=("Segoe UI", 9, "bold"), bg="#F8FAFC", fg="#0F172A", anchor="w",
        ).pack(fill=tk.X)

        tk.Label(
            info_card, text=f"📁 Folder: {result_path.parent}",
            font=("Segoe UI", 8), bg="#F8FAFC", fg="#64748B", anchor="w", wraplength=450, justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(2, 0))

        # Tombol Aksi Langsung
        btn_box = tk.Frame(content, bg="#FFFFFF")
        btn_box.pack(fill=tk.X)

        def _open_pdf():
            try:
                os.startfile(str(result_path))
            except Exception as e:
                messagebox.showerror("Error", f"Gagal membuka PDF:\n{e}")

        def _open_folder():
            try:
                os.startfile(str(result_path.parent))
            except Exception as e:
                messagebox.showerror("Error", f"Gagal membuka folder:\n{e}")

        btn_open_file = tk.Button(
            btn_box, text="📄 Buka File PDF", command=_open_pdf,
            font=("Segoe UI", 10, "bold"), bg="#198754", fg="#FFFFFF",
            relief=tk.FLAT, cursor="hand2", padx=14, pady=8,
        )
        btn_open_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        btn_open_dir = tk.Button(
            btn_box, text="📁 Buka Folder", command=_open_folder,
            font=("Segoe UI", 10, "bold"), bg="#0D6EFD", fg="#FFFFFF",
            relief=tk.FLAT, cursor="hand2", padx=14, pady=8,
        )
        btn_open_dir.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        btn_close = tk.Button(
            btn_box, text="Tutup", command=dlg.destroy,
            font=("Segoe UI", 10), bg="#E2E8F0", fg="#334155",
            relief=tk.FLAT, cursor="hand2", padx=14, pady=8,
        )
        btn_close.pack(side=tk.LEFT, fill=tk.X)

    def _on_process_cancelled(self):
        self._processing = False
        self._btn_process.config(state=tk.NORMAL, bg="#198754")
        self._btn_cancel.config(state=tk.DISABLED)
        self._progress_label_var.set("Proses dibatalkan.")
        self._status("Proses dibatalkan oleh pengguna.")

    def _on_process_error(self, msg: str):
        self._processing = False
        self._btn_process.config(state=tk.NORMAL, bg="#198754")
        self._btn_cancel.config(state=tk.DISABLED)
        self._status(f"Error: {msg}")
        messagebox.showerror("Gagal Memproses", f"Terjadi kesalahan saat memproses:\n{msg}")

    def _do_cancel(self):
        self._cancel_flag[0] = True
        self._status("Membatalkan proses...")

    def _status(self, msg: str):
        self._status_var.set(msg)


# ── Widget Styling Helpers ──────────────────────────────────────────────────

def _section_header(parent, text: str):
    tk.Label(
        parent, text=text,
        font=("Segoe UI", 9, "bold"),
        bg="#FFFFFF", fg="#0F5132",
        anchor="w", padx=14,
    ).pack(fill=tk.X, pady=(6, 4))


def _divider(parent):
    tk.Frame(parent, bg="#E2E8F0", height=1).pack(fill=tk.X, pady=8, padx=14)
