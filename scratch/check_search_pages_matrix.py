import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.book_engine.book_search import search_pages

pages = search_pages("matrix", limit=100)
count = 0
for p in pages:
    if "GREWAL" in p["book_name"]:
        print(f"PDF p.{p['pdf_page']} (pr:{p['printed_page']}) | Score: {p['score']} | Sec: {p['section_heading']}")
        count += 1
        if count >= 10:
            break
