import json

with open("backend/book_index/pages_index.json", "r", encoding="utf-8") as f:
    records = json.load(f)

for r in records:
    if "GREWAL" in r.get("book_name", "") and "Chapter 10" in (r.get("chapter_heading") or ""):
        sec = r.get("section_heading")
        p = r.get("pdf_page")
        pr = r.get("printed_page")
        print(f"p.{p} (pr {pr}): {sec}")
