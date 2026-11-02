import os
import sys

root_dir = os.path.dirname(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.book_engine.internet_books import (
    clean_search_query,
    fetch_open_library,
    fetch_internet_archive,
    fetch_google_books,
    score_and_rank_books
)

q = "Algebra and Trigonometry"
clean_info = clean_search_query(q)
print("Clean info:", clean_info)

print("\n--- 1. Testing Open Library ---")
try:
    ol_books = fetch_open_library(clean_info, timeout=5)
    print(f"Open Library returned {len(ol_books)} books")
    for b in ol_books[:3]:
        print("  OL:", b.get("title"), "|", b.get("authors"))
except Exception as e:
    print("OL error:", e)

print("\n--- 2. Testing Internet Archive ---")
try:
    ia_books = fetch_internet_archive(clean_info, timeout=5)
    print(f"Internet Archive returned {len(ia_books)} books")
    for b in ia_books[:3]:
        print("  IA:", b.get("title"), "|", b.get("authors"))
except Exception as e:
    print("IA error:", e)

print("\n--- 3. Testing Google Books ---")
try:
    gb_books = fetch_google_books(clean_info, timeout=5)
    print(f"Google Books returned {len(gb_books)} books")
    for b in gb_books[:3]:
        print("  GB:", b.get("title"), "|", b.get("authors"))
except Exception as e:
    print("GB error:", e)

all_books = ol_books + ia_books + gb_books
print(f"\nTotal raw books across providers: {len(all_books)}")
ranked = score_and_rank_books(all_books, clean_info)
print(f"Ranked books count: {len(ranked)}")
