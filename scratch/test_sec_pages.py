import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.book_engine.book_search import load_index, search_book_sections

records = load_index()
kreyszig = [p for p in records if "kreyszig" in p.get("file_path", "").lower()]
print(f"Total Kreyszig records: {len(kreyszig)}")
for p in kreyszig:
    pp = p.get("pdf_page")
    if 499 <= pp <= 512:
        print(f"PDF {pp}: ch='{p.get('chapter_heading')}' | sec='{p.get('section_heading')}' | pr={p.get('printed_page')}")

print("\n--- Search sections for Fourier Series ---")
res = search_book_sections("Fourier Series")
for b, s_list in res.items():
    if "kreyszig" in b.lower():
        top = s_list[0]
        print(f"Top section: {top['section_heading']}")
        print(f"PDF range: {top['pdf_range']}")
        print(f"Pages in sec: {[p['pdf_page'] for p in top['pages']]}")
