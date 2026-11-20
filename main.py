"""
main.py - Entry point Trace Qur'an

Mode GUI (default):
    python main.py

Mode CLI:
    python main.py --cli --input "JUZ 1.pdf" [--output out.pdf] [--opacity 0.2]
                   [--keep-waqf] [--keep-border] [--keep-ayat] [--dpi 300]
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path


def run_gui():
    """Jalankan aplikasi GUI Tkinter."""
    try:
        import sv_ttk
        _has_sv_ttk = True
    except ImportError:
        _has_sv_ttk = False

    from gui.app import TraceQuranApp
    app = TraceQuranApp()

    if _has_sv_ttk:
        sv_ttk.set_theme("light")

    app.mainloop()


def run_cli(args):
    """Jalankan mode CLI tanpa GUI."""
    from processor import process_pdf
    from processor.pdf_writer import build_output_path
    from config import DPI_PRINT, DPI_DRAFT

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File tidak ditemukan - {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else build_output_path(input_path)
    dpi = DPI_PRINT if args.dpi == 300 else DPI_DRAFT

    print(f"Input  : {input_path}")
    print(f"Output : {output_path}")
    print(f"Model  : {args.model}")
    print(f"Opacity: {args.opacity} ({int(args.opacity*100)}%)")
    print(f"DPI    : {dpi}")
    print(f"Keep border: {not args.no_border}")
    print(f"Keep waqf  : {not args.no_waqf}")
    print(f"Keep ayat  : {not args.no_ayat}")
    print()

    def on_progress(done: int, total: int):
        bar_len = 30
        filled = int(bar_len * done / total)
        bar = "█" * filled + "░" * (bar_len - filled)
        pct = int(done / total * 100)
        print(f"\r  [{bar}] {pct}%  Halaman {done}/{total}", end="", flush=True)

    try:
        result = process_pdf(
            input_path,
            output_path=output_path,
            model=args.model,
            opacity=args.opacity,
            keep_border=not args.no_border,
            keep_waqf=not args.no_waqf,
            keep_ayat=not args.no_ayat,
            dpi=dpi,
            progress_callback=on_progress,
        )
        print(f"\n\nSelesai! Output: {result}")
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except InterruptedError:
        print("\nDibatalkan.", file=sys.stderr)
        sys.exit(130)


def main():
    parser = argparse.ArgumentParser(
        description="Trace Qur'an - Buat lembar latihan menulis Arab dari PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  python main.py                                    # GUI
  python main.py --cli --input "JUZ 1.pdf"         # CLI dasar
  python main.py --cli --input "JUZ 1.pdf" --opacity 0.15 --dpi 300
        """,
    )
    parser.add_argument("--cli", action="store_true", help="Jalankan mode CLI (tanpa GUI)")
    parser.add_argument("--input", "-i", help="Path ke file PDF Al-Qur'an")
    parser.add_argument("--output", "-o", help="Path file output (opsional)")
    parser.add_argument(
        "--model", choices=["gray", "outline"], default="gray",
        help="Model tracing: 'gray' (Light Gray) atau 'outline' (Garis tepi tipis). Default: gray",
    )
    parser.add_argument(
        "--opacity", type=float, default=0.18,
        help="Level samar: 0.08 (sangat samar) - 0.50 (agak terlihat). Default: 0.18",
    )
    parser.add_argument("--dpi", type=int, default=300, choices=[150, 300],
                        help="Resolusi output. 150=draft, 300=cetak. Default: 300")
    parser.add_argument("--no-border", action="store_true",
                        help="Ikutkan border ornamen dalam fade (tidak disarankan)")
    parser.add_argument("--no-waqf", action="store_true",
                        help="Ikutkan tanda waqf margin dalam fade")
    parser.add_argument("--no-ayat", action="store_true",
                        help="Ikutkan roset nomor ayat dalam fade (default: roset tetap hitam)")

    args = parser.parse_args()

    if args.cli:
        if not args.input:
            parser.error("--cli membutuhkan --input")
        run_cli(args)
    else:
        run_gui()


if __name__ == "__main__":
    main()
