import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.book_engine.book_search import search_book_sections

results = search_book_sections("matrix")
grewal = results.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])
for i, s in enumerate(grewal):
    print(f"[{i+1}] [{s['match_category']}] (Score: {s['score']}) {s['section_heading']} | Ch: {s['chapter_heading']} | Pages: {len(s['matching_pages'])}/{s['page_count']}")
