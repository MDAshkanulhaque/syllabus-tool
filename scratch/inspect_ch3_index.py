import json

with open("backend/book_index/pages_index.json", "r", encoding="utf-8") as f:
    records = json.load(f)

for r in records:
    if "GREWAL" in r.get("book_name", ""):
        ch = r.get("chapter_heading") or ""
        sec = r.get("section_heading") or ""
        p = r.get("pdf_page")
        pr = r.get("printed_page")
        if "Chapter 3" in ch:
            print(f"PDF p.{p:3d} (pr:{pr}): sec='{sec}' | ch='{ch}'")
