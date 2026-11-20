"""
gui/app.py
Trace Qur'an (Duta Ilmu) - Aplikasi Desktop Windows
UI baru berbasis CustomTkinter. Logika pemrosesan (processor/) tidak diubah.
Engine: PyMuPDF + OpenCV (300 DPI High-Precision)
"""
from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    FADE_PRESETS, FADE_DEFAULT, FADE_MIN, FADE_MAX,
    DPI_PRINT, DPI_DRAFT, DPI_PREVIEW,
)
from processor import process_pdf, preview_page
from processor.pdf_reader import open_pdf, render_page, page_count

# ── Palet warna (selaras dengan versi web) ──────────────────────────────────
BG = "#F2F5F1"
CARD = "#FFFFFF"
BORDER = "#DDE5DE"
HEADER = "#17352A"
AMBER = "#F5B731"
GREEN = "#1F7A4F"
GREEN_HOVER = "#17613E"
GREEN_SOFT = "#E7F3EB"
GREEN_LINE = "#B9D8C5"
TEXT = "#1A2820"
MUTED = "#66766D"
CHIP = "#EDF1ED"
DISABLED = "#A9B8AF"
DANGER = "#C0392B"
PREVIEW_BG = "#E6EAE5"

FONT = "Segoe UI"
MODE_TRACE = "Hasil tracing"
MODE_ORIG = "Gambar asli"


def _font(size: int, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT, size=size, weight=weight)


def _shorten(path: str, limit: int = 40) -> str:
    """Potong path panjang di bagian tengah agar tetap muat di satu baris."""
    if len(path) <= limit:
        return path
    keep = (limit - 3) // 2
    return f"{path[:keep]}...{path[-keep:]}"


def _bind_click(widget, callback):
    """Pasang klik + kursor tangan ke widget beserta semua anaknya."""
    widget.bind("<Button-1>", lambda e: callback())
    try:
        widget.configure(cursor="hand2")
    except Exception:
        pass
    for child in widget.winfo_children():
        _bind_click(child, callback)


class TraceQuranApp(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        super().__init__(fg_color=BG)

        self.title("Trace Qur'an - Duta Ilmu")
        self.geometry("1200x820")
        self.minsize(1080, 700)

        # ── State ────────────────────────────────────────────────────────
        self._pdf_path: str | None = None
        self._total_pages = 0
        self._page = 0
        self._model = "gray"
        self._opacity = float(FADE_PRESETS[FADE_DEFAULT])
        self._preview_mode = "trace"
        self._output_folder: Path | None = None
        self._processing = False
        self._cancel_flag: list[bool] = [False]
        self._last_dpi = DPI_PRINT

        self._trace_img: Image.Image | None = None
        self._orig_img: Image.Image | None = None
        self._orig_page = -1
        self._preview_req = 0
        self._preview_timer = None

        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._drag_from: tuple[int, int] | None = None
        self._photo: ImageTk.PhotoImage | None = None
        self._photo_key: tuple | None = None

        self._keep_border = tk.BooleanVar(value=True)
        self._keep_waqf = tk.BooleanVar(value=True)
        self._keep_ayat = tk.BooleanVar(value=True)
        self._quality_var = tk.StringVar(value="Cetak 300 DPI")

        self._build_ui()
        self._bind_keys()

    # ══════════════════════════════════════════════════════════════════════
    # Layout
    # ══════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        self._build_header()
        tk.Frame(self, bg=AMBER, height=2).pack(fill="x")
        self._build_statusbar()

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=14)

        left = ctk.CTkFrame(body, fg_color="transparent", width=420)
        left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False)

        right = ctk.CTkFrame(
            body, fg_color=CARD, corner_radius=14,
            border_width=1, border_color=BORDER,
        )
        right.pack(side="left", fill="both", expand=True)

        self._build_left(left)
        self._build_preview(right)

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=HEADER, corner_radius=0, height=68)
        header.pack(fill="x")
        header.pack_propagate(False)

        logo = ctk.CTkLabel(
            header, text="✒", width=40, height=40, corner_radius=10,
            fg_color=AMBER, text_color=HEADER, font=_font(20, "bold"),
        )
        logo.pack(side="left", padx=(20, 12))

        titles = ctk.CTkFrame(header, fg_color="transparent")
        titles.pack(side="left")
        row = ctk.CTkFrame(titles, fg_color="transparent")
        row.pack(anchor="w")
        ctk.CTkLabel(
            row, text="Arabic Tracing Maker", font=_font(17, "bold"), text_color="white",
        ).pack(side="left")
        ctk.CTkLabel(
            row, text=" Duta Ilmu ", height=20, corner_radius=6,
            fg_color=AMBER, text_color=HEADER, font=_font(10, "bold"),
        ).pack(side="left", padx=10)
        ctk.CTkLabel(
            titles,
            text="Ubah PDF mushaf menjadi lembar latihan menebalkan (300 DPI)",
            font=_font(11), text_color="#9CC8AE",
        ).pack(anchor="w")

        self._reset_btn = ctk.CTkButton(
            header, text="Reset", width=76, height=30, corner_radius=15,
            fg_color="transparent", border_width=1, border_color="#3E6B58",
            hover_color="#24503D", text_color="white", font=_font(12, "bold"),
            command=self._reset,
        )
        self._reset_btn.pack(side="right", padx=(8, 20))

        self._pill = ctk.CTkLabel(
            header, text="  ●  Siap digunakan  ", height=30, corner_radius=15,
            fg_color="#24503D", text_color="#9FE3BA", font=_font(12, "bold"),
        )
        self._pill.pack(side="right")

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, fg_color=CARD, corner_radius=0, height=28)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)
        self._status = ctk.CTkLabel(
            bar, text="Pilih file PDF mushaf untuk memulai.",
            font=_font(11), text_color=MUTED, anchor="w",
        )
        self._status.pack(side="left", padx=16)

    # ── Panel kiri ──────────────────────────────────────────────────────────

    def _card(self, parent, step: int, title: str):
        card = ctk.CTkFrame(
            parent, fg_color=CARD, corner_radius=14,
            border_width=1, border_color=BORDER,
        )
        card.pack(fill="x", pady=(0, 10))
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(
            head, text=str(step), width=24, height=24, corner_radius=12,
            fg_color=GREEN, text_color="white", font=_font(11, "bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            head, text=title, font=_font(14, "bold"), text_color=TEXT,
        ).pack(side="left", padx=10)
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=16, pady=(0, 16))
        return body

    def _build_left(self, left):
        # Area aksi menempel di bawah (selalu terlihat, tanpa scroll)
        self._build_action_card(left)

        scroll = ctk.CTkScrollableFrame(
            left, fg_color="transparent", corner_radius=0,
            scrollbar_button_color="#C9D5CC", scrollbar_button_hover_color="#AFC0B4",
        )
        scroll.pack(side="top", fill="both", expand=True)

        self._build_upload_card(scroll)
        self._build_style_card(scroll)
        self._build_keep_card(scroll)

    def _build_upload_card(self, parent):
        body = self._card(parent, 1, "File PDF")

        self._drop = ctk.CTkFrame(
            body, fg_color=GREEN_SOFT, corner_radius=12,
            border_width=1, border_color=GREEN_LINE, height=92,
        )
        self._drop.pack(fill="x")
        self._drop.pack_propagate(False)

        inner = ctk.CTkFrame(self._drop, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        self._drop_icon = ctk.CTkLabel(inner, text="📂", font=_font(22))
        self._drop_icon.pack()
        self._drop_title = ctk.CTkLabel(
            inner, text="Klik untuk memilih file PDF",
            font=_font(13, "bold"), text_color=TEXT,
        )
        self._drop_title.pack()
        self._drop_sub = ctk.CTkLabel(
            inner, text="Mushaf Al-Qur'an, Juz 1 sampai 30",
            font=_font(11), text_color=MUTED,
        )
        self._drop_sub.pack()
        _bind_click(self._drop, self._pick_pdf)

    def _build_style_card(self, parent):
        body = self._card(parent, 2, "Gaya tracing")

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        row.grid_columnconfigure((0, 1), weight=1, uniform="model")

        self._model_cards: dict[str, dict] = {}
        models = [
            ("gray", "Model A", "Light Gray", "Huruf jadi abu-abu tipis"),
            ("outline", "Model B", "Outline", "Garis tepi tipis, isi putih"),
        ]
        for i, (key, cap, title, desc) in enumerate(models):
            frame = ctk.CTkFrame(
                row, corner_radius=12, border_width=2,
                fg_color=CARD, border_color=BORDER,
            )
            frame.grid(row=0, column=i, sticky="nsew", padx=(0, 5) if i == 0 else (5, 0))

            top = ctk.CTkFrame(frame, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(10, 0))
            ctk.CTkLabel(top, text=cap, font=_font(11), text_color=MUTED).pack(side="left")
            mark = ctk.CTkLabel(top, text="○", font=_font(14, "bold"), text_color=MUTED)
            mark.pack(side="right")
            ctk.CTkLabel(
                frame, text=title, font=_font(14, "bold"), text_color=TEXT, anchor="w",
            ).pack(fill="x", padx=12)
            ctk.CTkLabel(
                frame, text=desc, font=_font(11), text_color=MUTED,
                anchor="w", justify="left", wraplength=140,
            ).pack(fill="x", padx=12, pady=(0, 10))

            self._model_cards[key] = {"frame": frame, "mark": mark}
            _bind_click(frame, lambda k=key: self._select_model(k))
        self._refresh_model_cards()

        # Kepekatan
        head = ctk.CTkFrame(body, fg_color="transparent")
        head.pack(fill="x", pady=(16, 0))
        ctk.CTkLabel(
            head, text="Kepekatan abu-abu", font=_font(12, "bold"), text_color=TEXT,
        ).pack(side="left")
        self._pct_lbl = ctk.CTkLabel(
            head, text="", width=48, height=22, corner_radius=8,
            fg_color=GREEN_SOFT, text_color=GREEN, font=_font(12, "bold"),
        )
        self._pct_lbl.pack(side="right")

        steps = max(1, int(round((FADE_MAX - FADE_MIN) * 100)))
        self._slider = ctk.CTkSlider(
            body, from_=FADE_MIN, to=FADE_MAX, number_of_steps=steps,
            progress_color=GREEN, button_color=GREEN, button_hover_color=GREEN_HOVER,
            fg_color="#D5DED7", command=self._on_slider,
        )
        self._slider.set(self._opacity)
        self._slider.pack(fill="x", pady=(8, 8))

        chips = ctk.CTkFrame(body, fg_color="transparent")
        chips.pack(fill="x")
        chips.grid_columnconfigure((0, 1, 2), weight=1, uniform="chip")
        self._chips: dict[str, ctk.CTkButton] = {}
        for i, label in enumerate(FADE_PRESETS):
            btn = ctk.CTkButton(
                chips, text=label, height=28, corner_radius=14, font=_font(11),
                fg_color=CHIP, hover_color=GREEN_SOFT, text_color=TEXT,
                command=lambda lb=label: self._apply_preset(lb),
            )
            btn.grid(row=0, column=i, sticky="ew", padx=2)
            self._chips[label] = btn
        self._refresh_opacity_ui()

    def _build_keep_card(self, parent):
        body = self._card(parent, 3, "Tetap hitam pekat")
        for text, var in [
            ("Border ornamen halaman", self._keep_border),
            ("Tanda waqf di margin", self._keep_waqf),
            ("Nomor ayat dalam roset", self._keep_ayat),
        ]:
            ctk.CTkSwitch(
                body, text=text, variable=var, font=_font(12), text_color=TEXT,
                progress_color=GREEN, button_color="white", button_hover_color="#F0F0F0",
                fg_color="#BCC8BF", switch_width=38, switch_height=20,
                command=self._schedule_preview,
            ).pack(anchor="w", pady=4)

    def _build_action_card(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=CARD, corner_radius=14,
            border_width=1, border_color=BORDER,
        )
        card.pack(side="bottom", fill="x", pady=(2, 0))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        # Folder tujuan
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")
        txt = ctk.CTkFrame(row, fg_color="transparent")
        txt.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            txt, text="Simpan hasil di", font=_font(11), text_color=MUTED, anchor="w",
        ).pack(fill="x")
        self._folder_lbl = ctk.CTkLabel(
            txt, text="Sama dengan folder PDF", font=_font(12, "bold"),
            text_color=TEXT, anchor="w",
        )
        self._folder_lbl.pack(fill="x")
        self._filename_lbl = ctk.CTkLabel(
            txt, text="", font=_font(11), text_color=GREEN, anchor="w",
        )
        self._filename_lbl.pack(fill="x")
        ctk.CTkButton(
            row, text="Ubah", width=64, height=30, corner_radius=8, font=_font(12, "bold"),
            fg_color=CHIP, hover_color=GREEN_SOFT, text_color=TEXT,
            command=self._pick_folder,
        ).pack(side="right")

        # Kualitas
        self._quality = ctk.CTkSegmentedButton(
            inner, values=["Cetak 300 DPI", "Draft 150 DPI"], variable=self._quality_var,
            font=_font(12), selected_color=GREEN, selected_hover_color=GREEN_HOVER,
            unselected_color=CHIP, unselected_hover_color=GREEN_SOFT,
            text_color="white", fg_color=CHIP, height=30,
            command=lambda _v: self._update_output_names(),
        )
        self._quality.pack(fill="x", pady=(12, 12))
        self._quality_var.set("Cetak 300 DPI")

        # Progres
        self._progress_lbl = ctk.CTkLabel(
            inner, text="", font=_font(11), text_color=MUTED, anchor="w",
        )
        self._progress_lbl.pack(fill="x")
        self._progress = ctk.CTkProgressBar(
            inner, height=8, corner_radius=4, progress_color=GREEN, fg_color="#D5DED7",
        )
        self._progress.set(0)
        self._progress.pack(fill="x", pady=(2, 10))

        self._btn_process = ctk.CTkButton(
            inner, text="⚡  Proses & unduh semua halaman", height=46, corner_radius=12,
            font=_font(14, "bold"), fg_color=DISABLED, hover_color=GREEN_HOVER,
            text_color="white", text_color_disabled="white", state="disabled",
            command=self._do_process,
        )
        self._btn_process.pack(fill="x")

        self._btn_cancel = ctk.CTkButton(
            inner, text="Batalkan proses", height=28, font=_font(12),
            fg_color="transparent", hover_color="#FBEAE8", text_color=DANGER,
            command=self._do_cancel,
        )
        # tombol batal baru dipasang saat proses berjalan

    # ── Panel kanan (preview) ───────────────────────────────────────────────

    def _build_preview(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=(14, 10))

        self._mode_btn = ctk.CTkSegmentedButton(
            bar, values=[MODE_TRACE, MODE_ORIG], font=_font(12, "bold"), height=32,
            selected_color=GREEN, selected_hover_color=GREEN_HOVER,
            unselected_color=CHIP, unselected_hover_color=GREEN_SOFT,
            text_color="white", fg_color=CHIP,
            command=self._on_mode,
        )
        self._mode_btn.pack(side="left")
        self._mode_btn.set(MODE_TRACE)

        self._busy_lbl = ctk.CTkLabel(
            bar, text="", font=_font(11), text_color=MUTED,
        )
        self._busy_lbl.pack(side="left", padx=14)

        ctk.CTkLabel(
            bar, text="Scroll untuk zoom, seret untuk menggeser",
            font=_font(11), text_color=MUTED,
        ).pack(side="right")

        holder = ctk.CTkFrame(parent, fg_color=PREVIEW_BG, corner_radius=12)
        holder.pack(fill="both", expand=True, padx=16)
        self._canvas = tk.Canvas(
            holder, bg=PREVIEW_BG, highlightthickness=0, bd=0, cursor="arrow",
        )
        self._canvas.pack(fill="both", expand=True, padx=2, pady=2)
        self._canvas.bind("<Configure>", lambda e: self._render_canvas())
        self._canvas.bind("<MouseWheel>", self._on_wheel)
        self._canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", lambda e: setattr(self, "_drag_from", None))
        self._canvas.bind("<Double-Button-1>", lambda e: self._zoom_fit())

        nav = ctk.CTkFrame(parent, fg_color="transparent")
        nav.pack(fill="x", padx=16, pady=12)

        pager = ctk.CTkFrame(nav, fg_color="transparent")
        pager.pack(side="left")
        self._btn_prev = self._small_btn(pager, "◀", self._prev_page)
        self._btn_prev.pack(side="left")
        ctk.CTkLabel(pager, text="Hal", font=_font(12), text_color=MUTED).pack(side="left", padx=(10, 6))
        self._page_entry = ctk.CTkEntry(
            pager, width=52, height=32, justify="center", font=_font(12, "bold"),
            fg_color=CARD, border_color=BORDER, text_color=TEXT,
        )
        self._page_entry.pack(side="left")
        self._page_entry.insert(0, "0")
        self._page_entry.bind("<Return>", lambda e: self._goto_page_from_entry())
        self._page_entry.bind("<FocusOut>", lambda e: self._sync_page_entry())
        self._total_lbl = ctk.CTkLabel(pager, text="/ 0", font=_font(12), text_color=MUTED)
        self._total_lbl.pack(side="left", padx=(6, 10))
        self._btn_next = self._small_btn(pager, "▶", self._next_page)
        self._btn_next.pack(side="left")

        zoom = ctk.CTkFrame(nav, fg_color="transparent")
        zoom.pack(side="right")
        self._small_btn(zoom, "−", lambda: self._zoom_by(1 / 1.25)).pack(side="left")
        self._zoom_lbl = ctk.CTkLabel(
            zoom, text="100%", width=54, font=_font(12, "bold"), text_color=TEXT,
        )
        self._zoom_lbl.pack(side="left")
        self._small_btn(zoom, "+", lambda: self._zoom_by(1.25)).pack(side="left")
        ctk.CTkButton(
            zoom, text="Pas layar", width=76, height=32, corner_radius=8, font=_font(12),
            fg_color=CHIP, hover_color=GREEN_SOFT, text_color=TEXT,
            command=self._zoom_fit,
        ).pack(side="left", padx=(8, 0))

    def _small_btn(self, parent, text, command):
        return ctk.CTkButton(
            parent, text=text, width=36, height=32, corner_radius=8, font=_font(13, "bold"),
            fg_color=CHIP, hover_color=GREEN_SOFT, text_color=TEXT, command=command,
        )

    def _bind_keys(self):
        self.bind("<Left>", lambda e: None if self._typing() else self._prev_page())
        self.bind("<Right>", lambda e: None if self._typing() else self._next_page())
        self.bind("<space>", lambda e: None if self._typing() else self._toggle_mode())

    def _typing(self) -> bool:
        try:
            w = self.focus_get()
            return w is not None and w.winfo_class() in ("Entry", "TEntry", "Text")
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════════
    # Pilihan & pengaturan
    # ══════════════════════════════════════════════════════════════════════

    def _select_model(self, key: str):
        if key == self._model:
            return
        self._model = key
        self._refresh_model_cards()
        self._schedule_preview()

    def _refresh_model_cards(self):
        for key, parts in self._model_cards.items():
            active = key == self._model
            parts["frame"].configure(
                border_color=GREEN if active else BORDER,
                fg_color=GREEN_SOFT if active else CARD,
            )
            parts["mark"].configure(
                text="✓" if active else "○",
                text_color=GREEN if active else MUTED,
            )

    def _on_slider(self, value):
        self._opacity = float(value)
        self._refresh_opacity_ui()
        self._schedule_preview()

    def _apply_preset(self, label: str):
        self._opacity = float(FADE_PRESETS[label])
        self._slider.set(self._opacity)
        self._refresh_opacity_ui()
        self._schedule_preview()

    def _refresh_opacity_ui(self):
        self._pct_lbl.configure(text=f"{int(round(self._opacity * 100))}%")
        for label, btn in self._chips.items():
            active = abs(FADE_PRESETS[label] - self._opacity) < 0.005
            btn.configure(
                fg_color=GREEN if active else CHIP,
                text_color="white" if active else TEXT,
                hover_color=GREEN_HOVER if active else GREEN_SOFT,
            )

    def _set_status(self, msg: str):
        self._status.configure(text=msg)

    def _set_pill(self, text: str, bg: str, fg: str):
        self._pill.configure(text=f"  ●  {text}  ", fg_color=bg, text_color=fg)

    # ══════════════════════════════════════════════════════════════════════
    # File & folder
    # ══════════════════════════════════════════════════════════════════════

    def _pick_pdf(self):
        if self._processing:
            return
        path = filedialog.askopenfilename(
            title="Pilih file PDF Al-Qur'an",
            filetypes=[("File PDF", "*.pdf"), ("Semua file", "*.*")],
        )
        if path:
            self._load_pdf(path)

    def _pick_folder(self):
        initial = str(self._output_folder) if self._output_folder else ""
        folder = filedialog.askdirectory(title="Pilih folder penyimpanan", initialdir=initial)
        if folder:
            self._output_folder = Path(folder)
            self._update_output_names()

    def _load_pdf(self, path: str):
        try:
            doc = open_pdf(path)
            total = page_count(doc)
            doc.close()
        except Exception as e:
            messagebox.showerror("Gagal membuka file", f"File PDF tidak valid:\n{e}")
            return

        p = Path(path)
        self._pdf_path = path
        self._total_pages = total
        self._page = 0
        self._trace_img = None
        self._orig_img = None
        self._orig_page = -1
        self._zoom_fit(render=False)

        size_mb = p.stat().st_size / (1024 * 1024)
        self._drop_icon.configure(text="📄")
        self._drop_title.configure(text=_shorten(p.name, 34))
        self._drop_sub.configure(text=f"{total} halaman  •  {size_mb:.1f} MB  •  klik untuk ganti")
        self._drop.configure(fg_color="#DCEFE3", border_color=GREEN)

        if self._output_folder is None:
            self._output_folder = p.parent
        self._sync_page_entry()
        self._total_lbl.configure(text=f"/ {total}")
        self._update_output_names()
        self._set_process_enabled(True)
        self.title(f"Trace Qur'an - {p.name}")
        self._set_status(f"{p.name} dimuat ({total} halaman). Memuat preview...")
        self._do_preview()

    def _output_path(self) -> Path | None:
        if not self._pdf_path:
            return None
        p = Path(self._pdf_path)
        suffix = "_trace_outline.pdf" if self._model == "outline" else "_trace.pdf"
        return (self._output_folder or p.parent) / f"{p.stem}{suffix}"

    def _update_output_names(self):
        out = self._output_path()
        if out is None:
            return
        self._folder_lbl.configure(text=_shorten(str(out.parent), 38))
        self._filename_lbl.configure(text=_shorten(out.name, 44))
        dpi = self._current_dpi()
        self._btn_process.configure(
            text=f"⚡  Proses & unduh semua halaman ({dpi} DPI)"
        )

    def _current_dpi(self) -> int:
        return DPI_PRINT if "300" in self._quality_var.get() else DPI_DRAFT

    def _set_process_enabled(self, enabled: bool):
        self._btn_process.configure(
            state="normal" if enabled else "disabled",
            fg_color=GREEN if enabled else DISABLED,
        )

    def _reset(self):
        if self._processing:
            return
        self._pdf_path = None
        self._total_pages = 0
        self._page = 0
        self._trace_img = None
        self._orig_img = None
        self._orig_page = -1
        self._preview_req += 1
        self._output_folder = None
        self._zoom_fit(render=False)

        self._drop_icon.configure(text="📂")
        self._drop_title.configure(text="Klik untuk memilih file PDF")
        self._drop_sub.configure(text="Mushaf Al-Qur'an, Juz 1 sampai 30")
        self._drop.configure(fg_color=GREEN_SOFT, border_color=GREEN_LINE)
        self._folder_lbl.configure(text="Sama dengan folder PDF")
        self._filename_lbl.configure(text="")
        self._btn_process.configure(text="⚡  Proses & unduh semua halaman")
        self._set_process_enabled(False)
        self._progress.set(0)
        self._progress_lbl.configure(text="")
        self._sync_page_entry()
        self._total_lbl.configure(text="/ 0")
        self._busy_lbl.configure(text="")
        self.title("Trace Qur'an - Duta Ilmu")
        self._set_status("Pilih file PDF mushaf untuk memulai.")
        self._render_canvas()

    # ══════════════════════════════════════════════════════════════════════
    # Preview
    # ══════════════════════════════════════════════════════════════════════

    def _on_mode(self, value: str):
        self._preview_mode = "trace" if value == MODE_TRACE else "original"
        self._render_canvas()

    def _toggle_mode(self):
        if not self._pdf_path:
            return
        new = MODE_ORIG if self._preview_mode == "trace" else MODE_TRACE
        self._mode_btn.set(new)
        self._on_mode(new)

    def _prev_page(self):
        if self._pdf_path and self._page > 0:
            self._page -= 1
            self._sync_page_entry()
            self._do_preview()

    def _next_page(self):
        if self._pdf_path and self._page < self._total_pages - 1:
            self._page += 1
            self._sync_page_entry()
            self._do_preview()

    def _goto_page_from_entry(self):
        if not self._pdf_path:
            return
        try:
            n = int(self._page_entry.get()) - 1
        except ValueError:
            self._sync_page_entry()
            return
        n = max(0, min(n, self._total_pages - 1))
        if n != self._page:
            self._page = n
            self._do_preview()
        self._sync_page_entry()
        self.focus_set()

    def _sync_page_entry(self):
        self._page_entry.delete(0, "end")
        self._page_entry.insert(0, str(self._page + 1 if self._pdf_path else 0))

    def _schedule_preview(self):
        self._update_output_names()
        if self._preview_timer is not None:
            self.after_cancel(self._preview_timer)
        self._preview_timer = self.after(300, self._do_preview)

    def _do_preview(self):
        if not self._pdf_path or self._processing:
            return
        self._preview_req += 1
        token = self._preview_req

        # Ambil semua nilai di thread utama, lalu kirim ke thread kerja.
        path = self._pdf_path
        page = self._page
        model = self._model
        opacity = self._opacity
        keep_waqf = self._keep_waqf.get()
        keep_ayat = self._keep_ayat.get()
        need_orig = self._orig_page != page or self._orig_img is None

        self._busy_lbl.configure(text="Merender preview...")
        self._set_status(f"Merender halaman {page + 1}...")

        def _run():
            try:
                orig = None
                if need_orig:
                    doc = open_pdf(path)
                    orig = render_page(doc, page, dpi=DPI_PREVIEW)
                    doc.close()
                trace = preview_page(
                    path, page_num=page, model=model, opacity=opacity,
                    keep_waqf=keep_waqf, keep_ayat=keep_ayat, dpi=DPI_PREVIEW,
                )
            except Exception as e:
                err = str(e)
                self.after(0, lambda: self._on_preview_error(token, err))
                return
            self.after(0, lambda: self._on_preview_ready(token, page, orig, trace))

        threading.Thread(target=_run, daemon=True).start()

    def _on_preview_ready(self, token, page, orig, trace):
        if token != self._preview_req:
            return  # hasil usang, sudah ada permintaan yang lebih baru
        if orig is not None:
            self._orig_img = orig
            self._orig_page = page
        self._trace_img = trace
        self._busy_lbl.configure(text="")
        self._set_status(f"Preview halaman {page + 1} siap.")
        self._render_canvas()

    def _on_preview_error(self, token, msg):
        if token != self._preview_req:
            return
        self._busy_lbl.configure(text="")
        self._set_status(f"Gagal membuat preview: {msg}")

    # ── Kanvas, zoom, geser ─────────────────────────────────────────────────

    def _current_image(self) -> Image.Image | None:
        return self._trace_img if self._preview_mode == "trace" else self._orig_img

    def _render_canvas(self):
        c = self._canvas
        c.delete("all")
        cw, ch = c.winfo_width(), c.winfo_height()
        if cw < 20 or ch < 20:
            return

        img = self._current_image()
        if img is None:
            self._draw_empty(cw, ch)
            return

        iw, ih = img.size
        fit = min((cw - 40) / iw, (ch - 40) / ih)
        scale = fit * self._zoom
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))

        key = (id(img), nw, nh)
        if key != self._photo_key:
            self._photo = ImageTk.PhotoImage(img.resize((nw, nh), Image.LANCZOS))
            self._photo_key = key

        max_x = max(0.0, (nw - cw) / 2) + 60
        max_y = max(0.0, (nh - ch) / 2) + 60
        self._pan_x = max(-max_x, min(max_x, self._pan_x))
        self._pan_y = max(-max_y, min(max_y, self._pan_y))
        x, y = cw / 2 + self._pan_x, ch / 2 + self._pan_y

        c.create_rectangle(
            x - nw / 2 + 4, y - nh / 2 + 5, x + nw / 2 + 4, y + nh / 2 + 5,
            fill="#C9D0C8", outline="",
        )
        c.create_image(x, y, image=self._photo, anchor="center")
        c.configure(cursor="fleur" if self._zoom > 1.001 else "arrow")
        self._zoom_lbl.configure(text=f"{int(round(self._zoom * 100))}%")

    def _draw_empty(self, cw, ch):
        c = self._canvas
        if self._pdf_path:
            c.create_text(
                cw / 2, ch / 2, text="Merender preview...",
                fill=MUTED, font=(FONT, 12),
            )
            return
        c.create_text(cw / 2, ch / 2 - 46, text="📖", font=(FONT, 34))
        c.create_text(
            cw / 2, ch / 2 + 2, text="Belum ada dokumen",
            fill=TEXT, font=(FONT, 14, "bold"),
        )
        c.create_text(
            cw / 2, ch / 2 + 30,
            text="Pilih file PDF di panel kiri.\nHasil tracing akan tampil di sini.",
            fill=MUTED, font=(FONT, 11), justify="center",
        )

    def _zoom_by(self, factor: float):
        self._zoom = max(1.0, min(5.0, self._zoom * factor))
        if self._zoom <= 1.0:
            self._pan_x = self._pan_y = 0.0
        self._render_canvas()

    def _zoom_fit(self, render: bool = True):
        self._zoom = 1.0
        self._pan_x = self._pan_y = 0.0
        if render:
            self._render_canvas()

    def _on_wheel(self, event):
        if self._current_image() is None:
            return
        self._zoom_by(1.15 if event.delta > 0 else 1 / 1.15)

    def _on_drag_start(self, event):
        self._drag_from = (event.x, event.y)

    def _on_drag(self, event):
        if self._drag_from is None or self._zoom <= 1.001:
            return
        dx, dy = event.x - self._drag_from[0], event.y - self._drag_from[1]
        self._drag_from = (event.x, event.y)
        self._pan_x += dx
        self._pan_y += dy
        self._render_canvas()

    # ══════════════════════════════════════════════════════════════════════
    # Proses
    # ══════════════════════════════════════════════════════════════════════

    def _do_process(self):
        if not self._pdf_path:
            messagebox.showwarning("File belum dipilih", "Pilih file PDF Al-Qur'an terlebih dahulu.")
            return
        if self._processing:
            return

        out_path = self._output_path()
        dpi = self._current_dpi()
        self._last_dpi = dpi

        # Ambil semua nilai di thread utama
        path = self._pdf_path
        model = self._model
        opacity = self._opacity
        keep_border = self._keep_border.get()
        keep_waqf = self._keep_waqf.get()
        keep_ayat = self._keep_ayat.get()

        self._processing = True
        self._cancel_flag[0] = False
        self._set_process_enabled(False)
        self._btn_process.configure(text="Sedang memproses...")
        self._btn_cancel.pack(fill="x", pady=(6, 0))
        self._progress.set(0)
        self._progress_lbl.configure(text=f"Memproses 0 dari {self._total_pages} halaman...")
        self._set_pill("Memproses", "#5A4A12", "#FFD970")
        self._set_status("Proses dimulai...")

        def _run():
            try:
                result = process_pdf(
                    path,
                    output_path=out_path,
                    model=model,
                    opacity=opacity,
                    keep_border=keep_border,
                    keep_waqf=keep_waqf,
                    keep_ayat=keep_ayat,
                    dpi=dpi,
                    progress_callback=self._on_progress,
                    cancel_flag=self._cancel_flag,
                )
                self.after(0, lambda: self._on_done(result))
            except InterruptedError:
                self.after(0, self._on_cancelled)
            except Exception as e:
                err = str(e)
                self.after(0, lambda: self._on_error(err))

        threading.Thread(target=_run, daemon=True).start()

    def _on_progress(self, done: int, total: int):
        frac = done / total if total else 0

        def _ui():
            self._progress.set(frac)
            self._progress_lbl.configure(
                text=f"Memproses halaman {done} dari {total} ({int(frac * 100)}%)"
            )
            self._set_status(f"Sedang memproses halaman {done}/{total}...")

        self.after(0, _ui)

    def _finish_ui(self):
        self._processing = False
        self._btn_cancel.pack_forget()
        self._set_process_enabled(True)
        self._update_output_names()
        self._set_pill("Siap digunakan", "#24503D", "#9FE3BA")

    def _on_done(self, result_path: Path):
        self._finish_ui()
        self._progress.set(1)
        self._progress_lbl.configure(text=f"Selesai. {self._total_pages} halaman berhasil diproses.")
        self._set_status(f"Tersimpan: {Path(result_path).name}")
        try:
            self.bell()
        except Exception:
            pass
        self._show_success(Path(result_path))

    def _on_cancelled(self):
        self._finish_ui()
        self._progress.set(0)
        self._progress_lbl.configure(text="Proses dibatalkan.")
        self._set_status("Proses dibatalkan.")

    def _on_error(self, msg: str):
        self._finish_ui()
        self._set_status(f"Gagal: {msg}")
        messagebox.showerror("Gagal memproses", f"Terjadi kesalahan saat memproses:\n{msg}")

    def _do_cancel(self):
        self._cancel_flag[0] = True
        self._btn_cancel.configure(state="disabled")
        self._set_status("Membatalkan proses...")

    # ── Dialog sukses ───────────────────────────────────────────────────────

    def _show_success(self, result_path: Path):
        w, h = 500, 330
        dlg = ctk.CTkToplevel(self, fg_color=CARD)
        dlg.title("Tracing selesai")
        dlg.resizable(False, False)
        dlg.transient(self)
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")
        dlg.after(150, lambda: (dlg.lift(), dlg.grab_set()))

        ctk.CTkLabel(
            dlg, text="✓", width=56, height=56, corner_radius=28,
            fg_color=GREEN_SOFT, text_color=GREEN, font=_font(28, "bold"),
        ).pack(pady=(26, 10))
        ctk.CTkLabel(
            dlg, text="Tracing selesai", font=_font(19, "bold"), text_color=TEXT,
        ).pack()
        ctk.CTkLabel(
            dlg,
            text=f"{self._total_pages} halaman diproses dengan kualitas {self._last_dpi} DPI.",
            font=_font(12), text_color=MUTED,
        ).pack(pady=(2, 14))

        info = ctk.CTkFrame(dlg, fg_color="#F6F8F6", corner_radius=10, border_width=1, border_color=BORDER)
        info.pack(fill="x", padx=28)
        ctk.CTkLabel(
            info, text=_shorten(result_path.name, 52), font=_font(12, "bold"),
            text_color=TEXT, anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 0))
        ctk.CTkLabel(
            info, text=_shorten(str(result_path.parent), 60), font=_font(11),
            text_color=MUTED, anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 10))

        def _open(target: Path):
            try:
                os.startfile(str(target))  # Windows
            except Exception as e:
                messagebox.showerror("Gagal membuka", str(e), parent=dlg)

        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack(fill="x", padx=28, pady=20)
        btns.grid_columnconfigure((0, 1), weight=1, uniform="b")
        ctk.CTkButton(
            btns, text="Buka PDF", height=40, corner_radius=10, font=_font(13, "bold"),
            fg_color=GREEN, hover_color=GREEN_HOVER,
            command=lambda: _open(result_path),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(
            btns, text="Buka folder", height=40, corner_radius=10, font=_font(13, "bold"),
            fg_color=CHIP, hover_color=GREEN_SOFT, text_color=TEXT,
            command=lambda: _open(result_path.parent),
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ctk.CTkButton(
            dlg, text="Tutup", height=28, font=_font(12), fg_color="transparent",
            hover_color=CHIP, text_color=MUTED, command=dlg.destroy,
        ).pack()
