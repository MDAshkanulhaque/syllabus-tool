import json
import pymupdf
from pathlib import Path
from backend.book_engine.book_search import search_pages

results = search_pages("Matrix")
print(f"Total results: {len(results)}")

for idx, r in enumerate(results[:25]):
    print(f"\n--- Result #{idx+1} ---")
    print(f"Book: {r['book_name']}")
    print(f"PDF Page: {r['pdf_page']}")
    print(f"Reported Ch: '{r['chapter_heading']}'")
    print(f"Reported Sec: '{r['section_heading']}'")
    print(f"Score: {r['score']}")
