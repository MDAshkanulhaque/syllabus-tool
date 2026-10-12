import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.book_engine.book_search import search_book_sections

results = search_book_sections("matrix")
grewal = results.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])

for s in grewal:
    title = s["section_heading"]
    if "14.5" in title or "4.15" in title:
        print(f"=== {title} ===")
        print(f"Chapter: {s['chapter_heading']}")
        print(f"Category: {s['match_category']}, Score: {s['score']}")
        print(f"Matching pages: {s['matching_pages']}")
        for p in s["pages"]:
            if p["pdf_page"] in s["matching_pages"]:
                p_text = p.get("text", "")
                print(f"--- Page {p['pdf_page']} ---")
                for line in p_text.splitlines():
                    if "matrix" in line.lower() or "matrices" in line.lower() or "newton" in line.lower():
                        print("  ", line.strip())
