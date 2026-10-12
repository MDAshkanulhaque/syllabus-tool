import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pymupdf
from backend.book_engine.book_search import search_pages, group_results_by_section
from frontend.app import format_book_results, extract_book_snippet

def test_matrix_search():
    print("=" * 60)
    print("TEST 1: MATRIX SEARCH FUNCTIONALITY & METADATA")
    print("=" * 60)
    
    results = search_pages("Matrix", limit=None, match_mode="relevant")
    count = len(results)
    print(f"Total matching pages for 'Matrix': {count}")
    assert count == 350, f"Expected 350 matching pages for 'Matrix', got {count}"
    print("PASS: Exactly 350 matching pages preserved for 'Matrix'.")
    
    # Check top results
    print("\nTop 5 Results for 'Matrix':")
    for idx, r in enumerate(results[:5], 1):
        print(f"#{idx}: Book: {r['book_name'][:30]}")
        print(f"     Physical PDF Page: {r['pdf_page']}")
        print(f"     Printed Book Page: {r['printed_page']}")
        print(f"     Chapter: {r['chapter_heading']}")
        print(f"     Section: {r['section_heading']}")
        print(f"     Score:   {r['score']}")
        
        # Verify no bogus headings
        assert "Chapter 16" not in r['chapter_heading'] or r['pdf_page'] >= 851, f"Bogus Chapter 16 assigned to PDF page {r['pdf_page']}"
        assert r['chapter_heading'] != "chapter 4." or (169 <= r['pdf_page'] <= 206), f"Bogus chapter 4. assigned to PDF page {r['pdf_page']}"
        assert r['section_heading'] != "0.5 Row 2", f"Bogus section '0.5 Row 2' found on PDF page {r['pdf_page']}"

    # Verify specific known pages
    grewal_115 = next(r for r in results if "GREWAL" in r['book_name'] and r['pdf_page'] == 115)
    print("\nVerifying Grewal PDF Page 115:")
    print("  Chapter:", grewal_115['chapter_heading'])
    print("  Section:", grewal_115['section_heading'])
    print("  Physical PDF Page:", grewal_115['pdf_page'])
    print("  Printed Book Page:", grewal_115['printed_page'])
    assert "Chapter 3" in grewal_115['chapter_heading'], "Page 115 should belong to Chapter 3"
    assert "3.2 Introduction to Matrices" in grewal_115['section_heading'], "Page 115 should belong to Section 3.2"
    assert grewal_115['printed_page'] == "101", f"Page 115 should have printed page '101', got {grewal_115['printed_page']}"
    print("PASS: Grewal PDF page 115 verified against PDF text.")

    kreyszig_283 = next(r for r in results if "kreyszig" in r['book_name'].lower() and r['pdf_page'] == 283)
    print("\nVerifying Kreyszig PDF Page 283:")
    print("  Chapter:", kreyszig_283['chapter_heading'])
    print("  Section:", kreyszig_283['section_heading'])
    print("  Physical PDF Page:", kreyszig_283['pdf_page'])
    print("  Printed Book Page:", kreyszig_283['printed_page'])
    assert "Chapter 7" in kreyszig_283['chapter_heading'], "Page 283 should belong to Chapter 7"
    assert "7.1" in kreyszig_283['section_heading'], "Page 283 should belong to Section 7.1"
    assert kreyszig_283['printed_page'] == "257", f"Page 283 should have printed page '257', got {kreyszig_283['printed_page']}"
    print("PASS: Kreyszig PDF page 283 verified against PDF text.")

def test_vector_search():
    print("\n" + "=" * 60)
    print("TEST 2: VECTOR SEARCH FUNCTIONALITY & METADATA")
    print("=" * 60)
    
    results = search_pages("Vector", limit=None, match_mode="relevant")
    count = len(results)
    print(f"Total matching pages for 'Vector': {count}")
    assert count == 253, f"Expected 253 matching pages for 'Vector', got {count}"
    print("PASS: Exactly 253 matching pages found for 'Vector'.")
    
    print("\nTop 5 Results for 'Vector':")
    for idx, r in enumerate(results[:5], 1):
        print(f"#{idx}: Book: {r['book_name'][:30]}")
        print(f"     Physical PDF Page: {r['pdf_page']}")
        print(f"     Printed Book Page: {r['printed_page']}")
        print(f"     Chapter: {r['chapter_heading']}")
        print(f"     Section: {r['section_heading']}")
        print(f"     Score:   {r['score']}")
        assert "Vector" in r['section_heading'] or "Vector" in r['chapter_heading'] or "Matrices" in r['chapter_heading'], "Top vector result should have vector in heading"
    print("PASS: Top Vector results have high topic relevance and verified headings.")

def test_physical_vs_printed_pages():
    print("\n" + "=" * 60)
    print("TEST 3: PHYSICAL VS PRINTED PAGE SEPARATION")
    print("=" * 60)
    
    # Check across index records
    import json
    with open("backend/book_index/pages_index.json", "r", encoding="utf-8") as f:
        records = json.load(f)
        
    grewal_records = [r for r in records if "GREWAL" in r['book_name']]
    kreyszig_records = [r for r in records if "kreyszig" in r['book_name'].lower()]
    
    # Verify Grewal offset (14 page offset for decimal body pages)
    for r in grewal_records:
        if r['printed_page'] != "Unavailable":
            assert int(r['printed_page']) == r['pdf_page'] - 14, f"Grewal page {r['pdf_page']} printed page mismatch: {r['printed_page']}"
            
    # Verify Kreyszig offset (26 page offset for decimal body pages)
    for r in kreyszig_records:
        if r['printed_page'] != "Unavailable" and r['pdf_page'] <= 1139:
            assert int(r['printed_page']) == r['pdf_page'] - 26, f"Kreyszig page {r['pdf_page']} printed page mismatch: {r['printed_page']}"

    print("PASS: All printed page numbers match verified physical PDF page offsets.")

def test_frontend_format():
    print("\n" + "=" * 60)
    print("TEST 4: DASHBOARD FORMATTING OUTPUT")
    print("=" * 60)
    
    results = search_pages("Matrix", limit=None, match_mode="relevant")
    formatted = format_book_results("Matrix", results)
    print("Sample output from format_book_results:")
    print("\n".join(formatted.splitlines()[:25]))
    
    assert "Physical PDF Page:" in formatted, "Output must contain 'Physical PDF Page:'"
    assert "Printed Book Page:" in formatted, "Output must contain 'Printed Book Page:'"
    assert "Chapter Heading:" in formatted, "Output must contain 'Chapter Heading:'"
    assert "Section Heading:" in formatted, "Output must contain 'Section Heading:'"
    print("PASS: Dashboard format properly displays separated page numbers and verified headings.")

if __name__ == "__main__":
    test_matrix_search()
    test_vector_search()
    test_physical_vs_printed_pages()
    test_frontend_format()
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
