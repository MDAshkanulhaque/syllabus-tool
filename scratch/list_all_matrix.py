import sys
from pathlib import Path

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
        print(f"[{i+1}] [{cat}] (Score: {score}) {title} | Ch: {ch} | Pages: {matching_cnt}/{total_cnt}")
