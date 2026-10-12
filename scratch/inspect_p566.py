import json
with open('backend/book_index/pages_index.json', 'r', encoding='utf-8') as f:
    records = json.load(f)

for r in records:
    if 'kreyszig' in r.get('book_name', '').lower() and r.get('pdf_page') == 566:
        print(f"=== PAGE 566 (Section: {r.get('section_heading')}) ===")
        for line in r.get('text', '').splitlines():
            if any(k in line.lower() for k in ["fourier", "prerequisite", "chap. 11", "concept"]):
                print("  ", line.strip())
