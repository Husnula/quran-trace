"""
gui/app.py
Main Tkinter window - Trace Qur'an GUI.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
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
from processor.pdf_reader import open_pdf, page_count


class TraceQuranApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trace Qur'an")
        self.minsize(WINDOW_MIN_W, WINDOW_MIN_H)
        self.configure(bg=COLORS["bg_base"])

        # State
        self._pdf_path: str | None = None
        self._total_pages: int = 0
        self._preview_page_num: int = 0
        self._cancel_flag: list[bool] = [False]
        self._processing: bool = False

        # Tkinter variables
        self._model_var = tk.StringVar(value="gray")
        self._fade_preset = tk.StringVar(value=FADE_DEFAULT)
        self._opacity_var = tk.DoubleVar(value=FADE_PRESETS[FADE_DEFAULT])
        self._keep_border = tk.BooleanVar(value=True)
        self._keep_waqf = tk.BooleanVar(value=True)
        self._keep_ayat = tk.BooleanVar(value=True)
        self._dpi_var = tk.StringVar(value="Cetak (300 DPI)")
        self._output_path_var = tk.StringVar(value="")
        self._status_var = tk.StringVar(value="Siap - Pilih atau drag PDF Al-Qur'an")
        self._progress_var = tk.DoubleVar(value=0.0)
        self._progress_label_var = tk.StringVar(value="")

        # Sync slider ke preset
        self._fade_preset.trace_add("write", self._on_preset_change)

        self._build_ui()
        self._setup_drag_drop()

    # ── UI Builder ──────────────────────────────────────────────────────────

    def _build_ui(self):
        # Main container
        main = tk.Frame(self, bg=COLORS["bg_base"])
        main.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Left panel (settings)
        left = tk.Frame(main, bg=COLORS["bg_panel"], width=PANEL_LEFT_W)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        # Divider
        div = tk.Frame(main, bg=COLORS["border_subtle"], width=1)
        div.pack(side=tk.LEFT, fill=tk.Y)

        # Right panel (preview)
        right = tk.Frame(main, bg=COLORS["bg_base"])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_left_panel(left)
        self._build_right_panel(right)

        # Status bar
        status_bar = tk.Frame(self, bg=COLORS["bg_sunken"], height=28)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(
            status_bar,
            textvariable=self._status_var,
            bg=COLORS["bg_sunken"],
            fg=COLORS["text_secondary"],
            font=FONTS["small"],
            anchor="w",
            padx=12,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _build_left_panel(self, parent):
        canvas = tk.Canvas(parent, bg=COLORS["bg_panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        frame = tk.Frame(canvas, bg=COLORS["bg_panel"])
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        p = 16

        # ── Judul ──────────────────────────────────────────────────────────
        tk.Label(frame, text="Trace Qur'an", font=FONTS["title"],
                 bg=COLORS["bg_panel"], fg=COLORS["text_primary"],
                 anchor="w").pack(fill=tk.X, padx=p, pady=(p, 2))
        tk.Label(frame, text="Buat lembar latihan menulis Arab", font=FONTS["small"],
                 bg=COLORS["bg_panel"], fg=COLORS["text_muted"],
                 anchor="w").pack(fill=tk.X, padx=p, pady=(0, p))
        _divider(frame)

        # ── File Input ────────────────────────────────────────────────────
        _section_label(frame, "FILE PDF")
        self._drop_zone = _DropZone(frame, on_file=self._load_pdf)
        self._drop_zone.pack(fill=tk.X, padx=p, pady=(4, 0))
        self._file_label = tk.Label(
            frame, text="", font=FONTS["small"],
            bg=COLORS["bg_panel"], fg=COLORS["text_secondary"],
            anchor="w", wraplength=PANEL_LEFT_W - 32,
        )
        self._file_label.pack(fill=tk.X, padx=p, pady=(4, p))
        _divider(frame)

        # ── Model Tracing ──────────────────────────────────────────────────
        _section_label(frame, "MODEL TRACING")
        for val, text, desc in [
            ("gray", "Model A: Light Gray", "Abu-abu tipis presisi (standar)"),
            ("outline", "Model B: Outline", "Garis tepi tipis, huruf putih hollow"),
        ]:
            rb = tk.Radiobutton(
                frame, text=f"{text}\n  {desc}",
                variable=self._model_var, value=val,
                font=FONTS["label"], bg=COLORS["bg_panel"],
                fg=COLORS["text_primary"],
                selectcolor=COLORS["accent_light"],
                activebackground=COLORS["bg_panel"],
                justify=tk.LEFT,
                command=self._do_preview,
            )
            rb.pack(anchor="w", padx=p, pady=2)
        _divider(frame)

        # ── Fade Level ────────────────────────────────────────────────────
        _section_label(frame, "TINGKAT SAMAR")
        for label in FADE_PRESETS:
            rb = tk.Radiobutton(
                frame, text=f"{label}  ({int(FADE_PRESETS[label]*100)}%)",
                variable=self._fade_preset, value=label,
                font=FONTS["label"], bg=COLORS["bg_panel"],
                fg=COLORS["text_primary"],
                selectcolor=COLORS["accent_light"],
                activebackground=COLORS["bg_panel"],
            )
            rb.pack(anchor="w", padx=p, pady=1)

        # Custom slider
        slider_row = tk.Frame(frame, bg=COLORS["bg_panel"])
        slider_row.pack(fill=tk.X, padx=p, pady=(6, 0))
        tk.Label(slider_row, text="Custom:", font=FONTS["small"],
                 bg=COLORS["bg_panel"], fg=COLORS["text_secondary"]).pack(side=tk.LEFT)
        self._slider = ttk.Scale(
            slider_row, from_=FADE_MIN, to=FADE_MAX,
            orient=tk.HORIZONTAL, variable=self._opacity_var,
            command=self._on_slider_change,
        )
        self._slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 4))
        self._slider_pct_label = tk.Label(
            slider_row, text=f"{int(self._opacity_var.get()*100)}%",
            font=FONTS["mono"], bg=COLORS["bg_panel"], fg=COLORS["text_secondary"],
            width=4,
        )
        self._slider_pct_label.pack(side=tk.LEFT)
        _divider(frame)

        # ── Opsi Tambahan ────────────────────────────────────────────────
        _section_label(frame, "PERTAHANKAN HITAM")
        for text, var in [
            ("Border ornamen halaman", self._keep_border),
            ("Tanda waqf (ع، ط، ص، ج dll)", self._keep_waqf),
            ("Nomor ayat dalam lingkaran", self._keep_ayat),
        ]:
            cb = tk.Checkbutton(
                frame, text=text, variable=var,
                font=FONTS["label"], bg=COLORS["bg_panel"],
                fg=COLORS["text_primary"],
                selectcolor=COLORS["accent_light"],
                activebackground=COLORS["bg_panel"],
            )
            cb.pack(anchor="w", padx=p, pady=1)
        _divider(frame)

        # ── Preview control ───────────────────────────────────────────────
        _section_label(frame, "PREVIEW")
        nav_row = tk.Frame(frame, bg=COLORS["bg_panel"])
        nav_row.pack(fill=tk.X, padx=p, pady=(4, 0))
        tk.Label(nav_row, text="Halaman:", font=FONTS["label"],
                 bg=COLORS["bg_panel"], fg=COLORS["text_primary"]).pack(side=tk.LEFT)
        self._page_spin = ttk.Spinbox(nav_row, from_=1, to=1, width=4,
                                       command=self._on_page_change)
        self._page_spin.pack(side=tk.LEFT, padx=(4, 8))
        self._page_spin.set(1)
        btn_preview = _make_button(nav_row, "Refresh Preview", self._do_preview, style="secondary")
        btn_preview.pack(side=tk.LEFT)
        _divider(frame)

        # ── Output ───────────────────────────────────────────────────────
        _section_label(frame, "OUTPUT")
        out_row = tk.Frame(frame, bg=COLORS["bg_panel"])
        out_row.pack(fill=tk.X, padx=p, pady=(4, 0))
        self._output_entry = tk.Entry(
            out_row, textvariable=self._output_path_var,
            font=FONTS["mono"], bg=COLORS["bg_sunken"],
            fg=COLORS["text_primary"], relief=tk.FLAT,
            insertbackground=COLORS["text_primary"],
        )
        self._output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        _make_button(out_row, "Ubah", self._pick_output, style="secondary").pack(side=tk.LEFT, padx=(4, 0))

        dpi_row = tk.Frame(frame, bg=COLORS["bg_panel"])
        dpi_row.pack(fill=tk.X, padx=p, pady=(8, 0))
        tk.Label(dpi_row, text="Kualitas:", font=FONTS["label"],
                 bg=COLORS["bg_panel"], fg=COLORS["text_primary"]).pack(side=tk.LEFT)
        for txt in ["Draft (150 DPI)", "Cetak (300 DPI)"]:
            tk.Radiobutton(
                dpi_row, text=txt, variable=self._dpi_var, value=txt,
                font=FONTS["label"], bg=COLORS["bg_panel"],
                fg=COLORS["text_primary"], selectcolor=COLORS["accent_light"],
                activebackground=COLORS["bg_panel"],
            ).pack(side=tk.LEFT, padx=(8, 0))

        # ── Progress ─────────────────────────────────────────────────────
        _divider(frame)
        self._progress_label = tk.Label(
            frame, textvariable=self._progress_label_var,
            font=FONTS["small"], bg=COLORS["bg_panel"],
            fg=COLORS["text_secondary"], anchor="w",
        )
        self._progress_label.pack(fill=tk.X, padx=p, pady=(p, 2))
        self._progress_bar = ttk.Progressbar(
            frame, variable=self._progress_var,
            maximum=100, mode="determinate",
        )
        self._progress_bar.pack(fill=tk.X, padx=p, pady=(0, 8))

        # ── Tombol Utama ──────────────────────────────────────────────────
        self._btn_process = _make_button(
            frame, "PROSES SEMUA", self._do_process, style="primary",
        )
        self._btn_process.pack(fill=tk.X, padx=p, pady=(4, 4))
        self._btn_cancel = _make_button(
            frame, "Batalkan", self._do_cancel, style="secondary",
        )
        self._btn_cancel.pack(fill=tk.X, padx=p, pady=(0, p))
        self._btn_cancel.config(state=tk.DISABLED)

    def _build_right_panel(self, parent):
        # Header
        header = tk.Frame(parent, bg=COLORS["bg_panel"], height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="Preview Halaman",
            font=FONTS["section"], bg=COLORS["bg_panel"],
            fg=COLORS["text_secondary"], anchor="w", padx=16,
        ).pack(fill=tk.BOTH, expand=True)
        tk.Frame(parent, bg=COLORS["border_subtle"], height=1).pack(fill=tk.X)

        # Preview image
        self._preview_canvas = tk.Canvas(
            parent, bg=COLORS["bg_sunken"],
            highlightthickness=0, cursor="arrow",
        )
        self._preview_canvas.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        self._preview_canvas.bind("<Configure>", self._on_canvas_resize)
        self._preview_placeholder()

    def _preview_placeholder(self):
        self._preview_canvas.delete("all")
        w = self._preview_canvas.winfo_width() or 400
        h = self._preview_canvas.winfo_height() or 400
        self._preview_canvas.create_text(
            w // 2, h // 2,
            text="Pilih file PDF untuk melihat preview",
            fill=COLORS["text_muted"], font=FONTS["body"],
        )

    # ── Event handlers ──────────────────────────────────────────────────────

    def _on_preset_change(self, *_):
        preset = self._fade_preset.get()
        if preset in FADE_PRESETS:
            self._opacity_var.set(FADE_PRESETS[preset])
            self._slider_pct_label.config(text=f"{int(FADE_PRESETS[preset]*100)}%")

    def _on_slider_change(self, val):
        pct = int(float(val) * 100)
        self._slider_pct_label.config(text=f"{pct}%")
        # Clear preset selection jika slider digeser manual
        cur_opacity = float(val)
        for preset, v in FADE_PRESETS.items():
            if abs(v - cur_opacity) < 0.01:
                self._fade_preset.set(preset)
                return

    def _on_page_change(self):
        try:
            n = int(self._page_spin.get()) - 1
            self._preview_page_num = max(0, min(n, self._total_pages - 1))
        except ValueError:
            pass

    def _on_canvas_resize(self, event):
        if hasattr(self, "_last_preview_img") and self._last_preview_img:
            self._show_pil_in_canvas(self._last_preview_img)

    def _load_pdf(self, path: str):
        try:
            doc = open_pdf(path)
            self._total_pages = page_count(doc)
            doc.close()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        self._pdf_path = path
        p = Path(path)
        self._file_label.config(
            text=f"✓  {p.name}  ({self._total_pages} halaman)",
            fg=COLORS["accent"],
        )
        self._page_spin.config(to=self._total_pages)
        self._page_spin.set(1)
        self._preview_page_num = 0

        # Auto-set output path
        out = build_output_path(path)
        self._output_path_var.set(str(out))

        self.title(f"Trace Qur'an - {p.name}")
        self._status("File dipilih, mengambil preview...")
        self._do_preview()

    def _do_preview(self):
        if not self._pdf_path or self._processing:
            return
        self._status("Memuat preview...")

        def _run():
            try:
                img = preview_page(
                    self._pdf_path,
                    page_num=self._preview_page_num,
                    model=self._model_var.get(),
                    opacity=self._opacity_var.get(),
                    keep_waqf=self._keep_waqf.get(),
                    keep_ayat=self._keep_ayat.get(),
                    dpi=DPI_PREVIEW,
                )
                self.after(0, lambda: self._show_pil_in_canvas(img))
                self.after(0, lambda: self._status(
                    f"Preview halaman {self._preview_page_num + 1} selesai"
                ))
            except Exception as e:
                self.after(0, lambda: self._status(f"Error preview: {e}"))

        threading.Thread(target=_run, daemon=True).start()

    def _show_pil_in_canvas(self, img: Image.Image):
        self._last_preview_img = img
        canvas = self._preview_canvas
        cw = canvas.winfo_width() or 400
        ch = canvas.winfo_height() or 500

        # Scale ke canvas sambil mempertahankan aspect ratio
        iw, ih = img.size
        scale = min(cw / iw, ch / ih, 1.0)
        nw, nh = int(iw * scale), int(ih * scale)
        thumb = img.resize((nw, nh), Image.LANCZOS)

        tk_img = ImageTk.PhotoImage(thumb)
        canvas.delete("all")
        canvas.create_image(cw // 2, ch // 2, anchor=tk.CENTER, image=tk_img)
        canvas._tk_img = tk_img  # prevent GC

    def _do_process(self):
        if not self._pdf_path:
            messagebox.showwarning("Belum ada file", "Pilih file PDF terlebih dahulu.")
            return
        if self._processing:
            return

        output = self._output_path_var.get().strip()
        if not output:
            output = str(build_output_path(self._pdf_path))
            self._output_path_var.set(output)

        dpi = DPI_PRINT if "300" in self._dpi_var.get() else DPI_DRAFT
        self._processing = True
        self._cancel_flag[0] = False
        self._btn_process.config(state=tk.DISABLED)
        self._btn_cancel.config(state=tk.NORMAL)
        self._progress_var.set(0)
        self._progress_label_var.set(f"Memproses 0 dari {self._total_pages} halaman...")
        self._status("Proses dimulai...")

        def _run():
            try:
                result = process_pdf(
                    self._pdf_path,
                    output_path=output,
                    model=self._model_var.get(),
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
                self.after(0, lambda: self._on_process_cancelled())
            except Exception as e:
                self.after(0, lambda: self._on_process_error(str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _on_progress(self, done: int, total: int):
        pct = done / total * 100
        self.after(0, lambda: self._progress_var.set(pct))
        self.after(0, lambda: self._progress_label_var.set(
            f"Memproses halaman {done} dari {total}..."
        ))
        self.after(0, lambda: self._status(f"Halaman {done}/{total} selesai"))

    def _on_process_done(self, result_path: Path):
        self._processing = False
        self._btn_process.config(state=tk.NORMAL)
        self._btn_cancel.config(state=tk.DISABLED)
        self._progress_var.set(100)
        self._progress_label_var.set(f"Selesai! {self._total_pages} halaman diproses.")
        self._status(f"Tersimpan: {result_path.name}")

        ans = messagebox.askyesno(
            "Selesai",
            f"File berhasil dibuat:\n{result_path}\n\nBuka folder output?",
        )
        if ans:
            import os
            os.startfile(str(result_path.parent))

    def _on_process_cancelled(self):
        self._processing = False
        self._btn_process.config(state=tk.NORMAL)
        self._btn_cancel.config(state=tk.DISABLED)
        self._progress_label_var.set("Dibatalkan.")
        self._status("Proses dibatalkan.")

    def _on_process_error(self, msg: str):
        self._processing = False
        self._btn_process.config(state=tk.NORMAL)
        self._btn_cancel.config(state=tk.DISABLED)
        self._status(f"Error: {msg}")
        messagebox.showerror("Gagal memproses", msg)

    def _do_cancel(self):
        self._cancel_flag[0] = True
        self._status("Membatalkan...")

    def _pick_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Simpan PDF trace ke...",
        )
        if path:
            self._output_path_var.set(path)

    def _status(self, msg: str):
        self._status_var.set(msg)

    # ── Drag & Drop ─────────────────────────────────────────────────────────

    def _setup_drag_drop(self):
        """Setup drag & drop menggunakan tkinterdnd2 jika tersedia, fallback ke dialog."""
        try:
            from tkinterdnd2 import DND_FILES, TkinterDnD
            # shortcut: tkinterdnd2 perlu root yang diinisialisasi berbeda
            # jika tersedia, bind ke drop zone
        except ImportError:
            pass  # drag & drop via klik tetap berfungsi


# ── Reusable widget helpers ─────────────────────────────────────────────────

class _DropZone(tk.Canvas):
    """Area drag & drop (klik untuk buka dialog)."""

    def __init__(self, parent, on_file, **kw):
        super().__init__(
            parent,
            bg=COLORS["bg_sunken"],
            highlightthickness=1,
            highlightbackground=COLORS["border_strong"],
            height=72,
            cursor="hand2",
            **kw,
        )
        self._on_file = on_file
        self._draw_text("Drag PDF ke sini  /  klik untuk pilih")
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda e: self.config(highlightbackground=COLORS["accent_muted"]))
        self.bind("<Leave>", lambda e: self.config(highlightbackground=COLORS["border_strong"]))

        # Tkinter DnD (built-in, hanya folder pada Windows - fallback ke klik)
        try:
            self.drop_target_register("DND_Files")
            self.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass

    def _draw_text(self, text: str):
        self.delete("all")
        self.update_idletasks()
        w = self.winfo_width() or 260
        h = self.winfo_height() or 72
        self.create_text(
            w // 2, h // 2, text=text,
            fill=COLORS["text_muted"], font=FONTS["small"],
        )

    def _on_click(self, event):
        path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("Semua file", "*.*")],
            title="Pilih file PDF Al-Qur'an",
        )
        if path:
            self._on_file(path)

    def _on_drop(self, event):
        # event.data berisi path, mungkin dalam kurung kurawal di Windows
        path = event.data.strip().strip("{}")
        if path.lower().endswith(".pdf"):
            self._on_file(path)


def _divider(parent):
    tk.Frame(parent, bg=COLORS["border_subtle"], height=1).pack(fill=tk.X, pady=8)


def _section_label(parent, text: str):
    tk.Label(
        parent, text=text,
        font=("Segoe UI", 9, "bold"),
        bg=COLORS["bg_panel"], fg=COLORS["text_muted"],
        anchor="w", padx=16,
    ).pack(fill=tk.X, pady=(4, 2))


def _make_button(parent, text: str, command, style: str = "primary") -> tk.Button:
    if style == "primary":
        btn = tk.Button(
            parent, text=text, command=command,
            font=FONTS["label"], bg=COLORS["accent"],
            fg=COLORS["text_inverse"], relief=tk.FLAT,
            activebackground=COLORS["accent_hover"],
            activeforeground=COLORS["text_inverse"],
            padx=14, pady=8, cursor="hand2",
            borderwidth=0,
        )
    else:
        btn = tk.Button(
            parent, text=text, command=command,
            font=FONTS["label"], bg=COLORS["bg_panel"],
            fg=COLORS["text_secondary"], relief=tk.FLAT,
            activebackground=COLORS["bg_sunken"],
            activeforeground=COLORS["text_primary"],
            padx=10, pady=5, cursor="hand2",
            borderwidth=1, highlightbackground=COLORS["border_strong"],
        )
    return btn
