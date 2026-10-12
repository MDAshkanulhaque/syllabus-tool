import json
with open('backend/book_index/pages_index.json', 'r', encoding='utf-8') as f:
    records = json.load(f)

for r in records:
    if 'kreyszig' in r.get('book_name', '').lower() and '6.9' in r.get('section_heading', ''):
        for line in r.get('text', '').splitlines():
            if 'matrix' in line.lower():
                print(f"p.{r['pdf_page']}: {line.strip()}")
