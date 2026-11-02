import os
import sys

root_dir = os.path.dirname(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.book_engine.internet_books import (
    clean_search_query,
    fetch_open_library,
    fetch_internet_archive,
    score_and_rank_books,
    deduplicate_books
)

queries = [
    "Algebra and Trigonometry",
    "Advanced Engineering Mathematics by Erwin Kreyszig",
    "Project Gutenberg",
    "story book",
    "Python programming books",
    "free linear algebra books",
    "Computer Networks by Andrew Tanenbaum",
]

for q in queries:
    info = clean_search_query(q)
    print(f"\n==================================================")
    print(f"QUERY: '{q}'")
    print(f"Clean info: {info}")
    
    # Test OL with fields
    ol = fetch_open_library(info, timeout=6)
    print(f" -> Open Library: {len(ol)} books")
    
    # Test IA
    ia = fetch_internet_archive(info, timeout=6)
    print(f" -> Internet Archive: {len(ia)} books")
    
    combined = score_and_rank_books(ol + ia, info)
    dedup = deduplicate_books(combined)
    print(f" -> Total Combined & Deduplicated: {len(dedup)} books")
    for b in dedup[:2]:
        print(f"    * '{b.get('title')}' by {b.get('authors')} ({b.get('published_year')}) | Read: {b.get('reading_status')} | DL: {b.get('download_status')}")
