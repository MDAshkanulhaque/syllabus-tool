import os
import sys

root_dir = os.path.dirname(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.book_engine.internet_books import search_internet_books

print("=== SEARCHING ONLINE FOR 'Algebra and Trigonometry' ===")
res = search_internet_books("Algebra and Trigonometry", limit=5, timeout=4)
print(f"Total found: {res.get('total_found')}")
for b in res.get("results", []):
    print(" -", b.get("title"), "|", b.get("authors"), "|", b.get("published_year"), "| Read:", b.get("reading_status"), "| DL:", b.get("download_status"))
