import json
with open('backend/book_index/pages_index.json', 'r', encoding='utf-8') as f:
    records = json.load(f)

obj_secs = set()
for r in records:
    sec = r.get("section_heading") or ""
    ch = r.get("chapter_heading") or ""
    b = r.get("book_name") or ""
    if "objective" in sec.lower():
        obj_secs.add((b, ch, sec))

for b, ch, sec in sorted(obj_secs):
    print(f"Book: {b[:25]} | Ch: {ch} | Sec: {sec}")
