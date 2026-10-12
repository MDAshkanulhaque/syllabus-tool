import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.book_engine.book_search import search_book_sections

results = search_book_sections("matrix")

for book, secs in results.items():
    print(f"\n==========================================")
    print(f"BOOK: {book} (Total sections: {len(secs)})")
    print(f"==========================================")
    for i, s in enumerate(secs):
        title = s["section_heading"]
        ch = s["chapter_heading"]
        cat = s["match_category"]
        score = s["score"]
        matching_cnt = len(s["matching_pages"])
        total_cnt = s["page_count"]
        
        # Check targets or list summary
        is_target = ("newton" in title.lower() or "objective" in title.lower() or 
                     "4.15" in title or "14.5" in title)
        
        if is_target or i < 5:
            prefix = ">>> [TARGET] " if is_target else "    "
            print(f"{prefix}[#{i+1}] {title} | Ch: {ch} | Cat: {cat} | Score: {score} | Pages: {matching_cnt}/{total_cnt}")
            if is_target:
                # Print matched text snippet
                for p in s["pages"]:
                    p_txt = p.get("search_text", "")
                    if "matrix" in p_txt or "matrices" in p_txt:
                        lines = [line.strip() for line in p.get("text", "").splitlines() if any(w in line.lower() for w in ["matrix", "matrices"])]
                        print(f"       Page {p['pdf_page']} occurrences: {lines[:3]}")
