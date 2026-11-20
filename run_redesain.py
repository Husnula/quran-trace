"""
run_redesain.py
Jalankan aplikasi versi CustomTkinter dari folder gui/REDESAIN/
"""
import sys
from pathlib import Path

# Pastikan root workspace dan gui/REDESAIN masuk ke sys.path
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "gui" / "REDESAIN"))

from app import TraceQuranApp

if __name__ == "__main__":
    app = TraceQuranApp()
    app.mainloop()
