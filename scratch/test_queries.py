import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.book_engine.book_search import search_book_sections, format_book_sections_response

queries = [
    "Orthogonal Series. Generalized Fourier Series",
    "Fourier Series",
    "Matrix",
    "Quantum Electrodynamics Superstring 999xyz"
]

for q in queries:
    print("=" * 70)
    print(f"QUERY: '{q}'")
    print("=" * 70)
    res = search_book_sections(q)
    print(f"Books returned: {len(res)}")
    for b_name, sec_list in res.items():
        direct = [s for s in sec_list if s.get("category_key") == "direct"]
        related = [s for s in sec_list if s.get("category_key") == "related"]
        content = [s for s in sec_list if s.get("category_key") == "content"]
        print(f"  Book: {b_name} -> Total {len(sec_list)} (Direct: {len(direct)}, Related: {len(related)}, Content: {len(content)})")
        for i, s in enumerate(sec_list[:3]):
            matching_cnt = len(s.get("matching_pages", []))
            total_cnt = s.get("page_count", len(s.get("pages", [])))
            print(f"    Top {i+1} [{s.get('category_key')}]: {s.get('section_heading')}")
            print(f"      PDF pp: {s.get('pdf_range')} | Printed pp: {s.get('printed_range')}")
            print(f"      Coverage: {matching_cnt}/{total_cnt} matching pages")
            print(f"      Pages list count: {len(s.get('pages', []))}")
    formatted = format_book_sections_response(q, res)
    print("First 300 chars of formatted response:")
    print(formatted[:300])
    print()
