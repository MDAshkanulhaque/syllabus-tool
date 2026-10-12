import json

with open("backend/book_index/pages_index.json", "r", encoding="utf-8") as f:
    records = json.load(f)

grewal_sections = {}
for r in records:
    if "GREWAL" in r.get("book_name", ""):
        ch = r.get("chapter_heading") or ""
        sec = r.get("section_heading") or ""
        p = r.get("pdf_page")
        if ch != "Unavailable" and sec != "Unavailable":
            if (ch, sec) not in grewal_sections:
                grewal_sections[(ch, sec)] = []
            grewal_sections[(ch, sec)].append(p)

for (ch, sec), pages in grewal_sections.items():
    start, end = min(pages), max(pages)
    cnt = len(pages)
    print(f"[{ch[:25]}] {sec} -> PDF {start}–{end} (cnt={cnt}, printed {start-14}–{end-14})")
