import sys
import io
import importlib
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Dynamically locate project root (directory containing 'backend')
current_dir = Path(__file__).resolve().parent
project_root = current_dir if (current_dir / "backend").exists() else current_dir.parent
if not (project_root / "backend").exists():
    candidate = Path(r"c:\Users\haque\OneDrive\Music\antigravity folder 2\syllabus-tool")
    if (candidate / "backend").exists():
        project_root = candidate
    else:
        project_root = Path.cwd()

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Dynamic import ensures clean resolution and prevents Pyrefly missing-import diagnostics
internet_books = importlib.import_module("backend.book_engine.internet_books")
search_internet_books = getattr(internet_books, "search_internet_books")
format_internet_books_chat_response = getattr(internet_books, "format_internet_books_chat_response")

print("Testing search_internet_books on Calculus Made Easy...")
res = search_internet_books("Calculus Made Easy", limit=8, timeout=6.0)

primary = res.get("primary_book")
print("Primary book title:", primary.get("title") if isinstance(primary, dict) else "None")
print("Primary author:", primary.get("authors") if isinstance(primary, dict) else "None")
print("Sources:", primary.get("source_provider") if isinstance(primary, dict) else "None")
print("Reading status:", primary.get("reading_status") if isinstance(primary, dict) else "None")
print("Reading url:", primary.get("reading_url") if isinstance(primary, dict) else "None")
print("Download status:", primary.get("download_status") if isinstance(primary, dict) else "None")
print("Download url:", primary.get("download_url") if isinstance(primary, dict) else "None")

formatted = format_internet_books_chat_response(res)
print("\n--- FORMATTED CHAT OUTPUT ---")
print(formatted)
