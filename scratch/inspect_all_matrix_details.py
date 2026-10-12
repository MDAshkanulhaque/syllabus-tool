import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.book_engine.book_search import search_book_sections

results = search_book_sections("matrix")

for book, secs in results.items():
    print(f"\n==========================================")
    print(f"BOOK: {book}")
    print(f"==========================================")
    for s in secs:
        title = s["section_heading"]
        ch = s["chapter_heading"]
        cat = s["match_category"]
        score = s["score"]
        mp = len(s["matching_pages"])
        tp = s["page_count"]
        # Count total query term occurrences
        occurrences = 0
        for p in s["pages"]:
            st = p.get("search_text", "")
            occurrences += st.count("matrix") + st.count("matrices")
        print(f"[{cat:25}] Score: {score:7.1f} | Occur: {occurrences:3d} | Pgs: {mp:2d}/{tp:2d} | Sec: {title} | Ch: {ch}")
