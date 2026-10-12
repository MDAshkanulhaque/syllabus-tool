import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.book_engine.book_search import search_book_sections

results = search_book_sections("Fourier Series")

for book, secs in results.items():
    for s in secs:
        if "12.1" in s["section_heading"]:
            print(f"Book: {book}")
            print(f"Section: {s['section_heading']}")
            print(f"Chapter: {s['chapter_heading']}")
            print(f"Match category: {s['match_category']}")
            print(f"Score: {s['score']}")
            print(f"Matching pages: {s['matching_pages']}")
            print(f"Total pages: {s['page_count']}")
            print("--- MATCHED TEXT ON PAGES ---")
            for p in s["pages"]:
                p_text = p.get("text", "")
                occurrences = [line.strip() for line in p_text.splitlines() if "fourier" in line.lower()]
                if occurrences:
                    print(f"Page {p['pdf_page']}: {occurrences}")
