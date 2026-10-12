import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.book_engine.book_search import search_book_sections

results = search_book_sections("matrix")

print("--- GREWAL SECTIONS ---")
for i, s in enumerate(results.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])):
    title = s["section_heading"]
    ch = s["chapter_heading"]
    cat = s["match_category"]
    sc = s["score"]
    mp = len(s["matching_pages"])
    tp = s["page_count"]
    print(f"G[{i+1:2d}] {cat:20} sc={sc:6.1f} p={mp:2d}/{tp:2d} | Sec: '{title}' | Ch: '{ch}'")

print("\n--- KREYSZIG SECTIONS ---")
for i, s in enumerate(results.get("advanced-engineering-mathematics_by-erwin-kreyszig-__10th_edition-1", [])):
    title = s["section_heading"]
    ch = s["chapter_heading"]
    cat = s["match_category"]
    sc = s["score"]
    mp = len(s["matching_pages"])
    tp = s["page_count"]
    print(f"K[{i+1:2d}] {cat:20} sc={sc:6.1f} p={mp:2d}/{tp:2d} | Sec: '{title}' | Ch: '{ch}'")
