import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.book_engine.book_search import search_book_sections, format_book_sections_response

results = search_book_sections("Fourier Series")
for b, secs in results.items():
    print(f"\n=== {b} ({len(secs)} secs) ===")
    for i, s in enumerate(secs[:10]):
        print(f"{i+1}. Ch: {s.get('chapter_heading')} | Sec: {s.get('section_heading')} | Score: {s.get('score')} | Pages: {len(s.get('matching_pages', []))}")
