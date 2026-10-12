import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.book_engine.book_search import search_pages, search_book_sections

print("=== search_pages('Introduction to Matrices') ===")
p_res = search_pages("Introduction to Matrices", limit=5)
for r in p_res:
    print(f"Book: {r['book_name'][:20]} | PDF: {r['pdf_page']} (pr:{r['printed_page']}) | Sec: {r['section_heading']}")

print("\n=== search_book_sections('Introduction to Matrices') ===")
s_res = search_book_sections("Introduction to Matrices")
for b, secs in s_res.items():
    print(f"Book: {b[:20]}")
    for s in secs[:3]:
        print(f"  Sec: {s['section_heading']} | Range: PDF {s['pdf_range']} (pr:{s['printed_range']}) | Pages: {s['matching_pages']}")
