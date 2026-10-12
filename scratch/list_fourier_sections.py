import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.book_engine.book_search import search_book_sections

results = search_book_sections("Fourier Series")

for book, secs in results.items():
    print(f"=== {book} (Total {len(secs)} sections) ===")
    for i, s in enumerate(secs):
        print(f"[{i+1}] [{s['match_category']}] {s['section_heading']} (Score: {s['score']}, Pages: {len(s['matching_pages'])}/{s['page_count']})")
