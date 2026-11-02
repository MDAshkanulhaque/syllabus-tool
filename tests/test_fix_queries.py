import os
import sys

root_dir = os.path.dirname(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.book_engine.internet_books import search_internet_books

print("=== 1. SEARCH FOR 'story book' ===")
res1 = search_internet_books("story book", limit=5)
print(f"Total found: {res1.get('total_found')}")
for b in res1.get("results", [])[:3]:
    print(" -", b.get("title"), "|", b.get("authors"), "|", b.get("reading_status"), "|", b.get("download_status"))

print("\n=== 2. SEARCH FOR 'Advanced Engineering Mathematics by Erwin Kreyszig' ===")
res2 = search_internet_books("Advanced Engineering Mathematics by Erwin Kreyszig", limit=5)
print(f"Total found: {res2.get('total_found')}")
for b in res2.get("results", [])[:3]:
    print(" -", b.get("title"), "|", b.get("authors"), "|", b.get("reading_status"), "|", b.get("download_status"))
