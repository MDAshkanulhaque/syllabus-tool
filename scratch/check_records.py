import json
with open('backend/book_index/pages_index.json', 'r', encoding='utf-8') as f:
    records = json.load(f)

for r in records:
    if 'GREWAL' in r.get('book_name', '') and 695 <= r.get('pdf_page', 0) <= 715:
        print(f"p.{r['pdf_page']}: sec='{r.get('section_heading')}' | ch='{r.get('chapter_heading')}'")
