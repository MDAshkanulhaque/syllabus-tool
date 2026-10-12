import json

with open("backend/book_index/pages_index.json", "r", encoding="utf-8") as f:
    records = json.load(f)

ch7_secs = {}
for r in records:
    if "GREWAL" in r.get("book_name", "") and "Chapter 7" in (r.get("chapter_heading") or ""):
        sec = r.get("section_heading")
        p = r.get("pdf_page")
        if sec not in ch7_secs: ch7_secs[sec] = []
        ch7_secs[sec].append(p)

for s, p in ch7_secs.items():
    print(f"Ch 7: {s} -> PDF {min(p)}–{max(p)} ({len(p)} pages)")
