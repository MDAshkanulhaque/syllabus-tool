import json
with open('backend/book_index/pages_index.json', 'r', encoding='utf-8') as f:
    records = json.load(f)

for r in records:
    if 'GREWAL' in r.get('book_name', '') and 694 <= r.get('pdf_page', 0) <= 699:
        print(f"=== Page {r['pdf_page']} ===")
        print("FIRST 5 LINES:")
        for line in r.get('text', '').splitlines()[:5]:
            print("  ", line)
