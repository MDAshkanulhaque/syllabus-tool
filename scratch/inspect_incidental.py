import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.book_engine.book_search import search_book_sections

results = search_book_sections("matrix")
grewal = results.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])

for s in grewal:
    title = s["section_heading"]
    if any(k in title for k in ["Adams", "Least Squares", "Group Averages", "Newton", "Objective"]):
        print(f"=== {title} ===")
        for p in s["pages"]:
            if p["pdf_page"] in s["matching_pages"]:
                st = p.get("text", "")
                matches = [l.strip() for l in st.splitlines() if "matrix" in l.lower() or "matrices" in l.lower()]
                print(f"  Page {p['pdf_page']}: {matches}")
