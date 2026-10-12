import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging
logging.getLogger("streamlit").setLevel(logging.ERROR)
logging.getLogger("root").setLevel(logging.ERROR)

import backend.book_engine.book_search as bs
from frontend.app import render_pdf_page_image

def run_tests():
    print("=================================================================")
    print("TEST 1: Search Relevance for 'Fourier Series'")
    print("=================================================================")
    results_fourier = bs.search_book_sections("Fourier Series")

    # 1. Verify B.S. Grewal has 0 matches
    grewal_name = "NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL"
    grewal_secs = results_fourier.get(grewal_name, [])
    assert len(grewal_secs) == 0, f"Expected 0 matches for Grewal, got {len(grewal_secs)}"
    print("[OK] B. S. Grewal has 0 matches (no false positive series approximations)")

    # 2. Verify Kreyszig matches
    kreyszig_name = "advanced-engineering-mathematics_by-erwin-kreyszig-__10th_edition-1"
    kreyszig_secs = results_fourier.get(kreyszig_name, [])
    assert len(kreyszig_secs) > 0, "Expected matches in Kreyszig"

    # 3. Verify Priority 1 is '11.1 Fourier Series'
    top_sec = kreyszig_secs[0]
    assert "11.1 Fourier Series" in top_sec["section_heading"], f"Top section was {top_sec['section_heading']}"
    assert top_sec["category_key"] == "direct", f"Expected direct match, got {top_sec['category_key']}"
    print(f"[OK] Priority 1 Direct Match: '{top_sec['section_heading']}' (PDF pp. {top_sec['pdf_range']})")

    # 4. Verify exclusions: 'Power Series Method' and 'Error in a Series Approximation' must NOT be in results
    all_headings = [s["section_heading"].lower() for s in kreyszig_secs]
    assert not any("power series method" in h for h in all_headings), "Power Series Method must NOT match"
    assert not any("error in a series" in h for h in all_headings), "Error in a Series must NOT match"
    print("[OK] False positives 'Power Series Method' and 'Error in a Series Approximation' are strictly excluded")

    # 5. Verify Related Topics & Applications: Fourier Transform, Fourier Integral, Generalized Fourier Series, and PDE applications
    direct_headings = [s["section_heading"] for s in kreyszig_secs if s["category_key"] == "direct"]
    assert len(direct_headings) == 1 and "11.1 Fourier Series" in direct_headings[0], f"Expected only 11.1 as direct, got {direct_headings}"
    print("[OK] '11.1 Fourier Series' is the sole primary Direct Match")

    related_headings = [s["section_heading"] for s in kreyszig_secs if s["category_key"] == "related"]
    assert any("fourier transform" in h.lower() for h in related_headings), "Fourier Transform must be in related topics"
    assert any("fourier integral" in h.lower() for h in related_headings), "Fourier Integral must be in related topics"
    assert any("generalized fourier series" in h.lower() for h in related_headings), "Generalized Fourier Series must be in related topics"
    assert any("rectangular membrane" in h.lower() for h in related_headings), "12.9 Rectangular Membrane must be in related topics/applications"
    assert any("heat equation" in h.lower() for h in related_headings), "12.6 Heat Equation must be in related topics/applications"
    assert any("forced oscillations" in h.lower() for h in related_headings), "11.3 Forced Oscillations must be in related topics/applications"
    print(f"[OK] Related topics & applications verified ({len(related_headings)} total, including PDE and oscillation applications):")
    for rh in related_headings[:5]:
        print(f"   - {rh}")

    # 6. Verify Formatted Response Output
    formatted = bs.format_book_sections_response("Fourier Series", results_fourier)
    assert "🎯 DIRECT MATCHES:" in formatted
    assert "🔗 RELATED TOPICS & APPLICATIONS:" in formatted
    assert "11.1 Fourier Series" in formatted
    assert "Section Page Coverage:" in formatted
    assert "Complete Physical PDF Range:" in formatted
    print("[OK] Formatted response correctly groups by Direct Matches and Related Topics & Applications with coverage details")

    print("\n=================================================================")
    print("TEST 2: Search for 'Matrix'")
    print("=================================================================")
    results_matrix = bs.search_book_sections("Matrix")
    assert len(results_matrix) == 2, f"Expected 2 books matching Matrix, got {len(results_matrix)}"
    for b_name, m_secs in results_matrix.items():
        direct_cnt = sum(1 for s in m_secs if s["category_key"] == "direct")
        print(f"[OK] {b_name}: {len(m_secs)} sections total ({direct_cnt} direct matches)")
        top = m_secs[0]
        print(f"   Top result: {top['section_heading']} (PDF pp. {top['pdf_range']})")

    print("\n=================================================================")
    print("TEST 3: Search for Unknown Query 'Quantum Electrodynamics Superstring 999xyz'")
    print("=================================================================")
    results_unknown = bs.search_book_sections("Quantum Electrodynamics Superstring 999xyz")
    assert len(results_unknown) == 0, f"Expected 0 results, got {results_unknown}"
    un_formatted = bs.format_book_sections_response("Quantum Electrodynamics Superstring 999xyz", results_unknown)
    assert "not found in the books" in un_formatted
    print(f"[OK] Unknown query correctly returns empty result: \"{un_formatted}\"")

    print("\n=================================================================")
    print("TEST 4: PDF Rendering Function and Return Value Verification")
    print("=================================================================")
    # Get physical PDF file
    pdf_path = top_sec["file_path"]
    target_page = top_sec["pdf_start"] # e.g. 500
    img_bytes = render_pdf_page_image(pdf_path, target_page, dpi=130)

    assert isinstance(img_bytes, bytes), f"Expected bytes, got {type(img_bytes)}"
    assert img_bytes.startswith(b"\x89PNG\r\n\x1a\n"), "Rendered image must be a valid PNG binary"
    assert len(img_bytes) > 10000, f"Expected image size > 10KB, got {len(img_bytes)} bytes"
    print(f"[OK] Rendered physical PDF page {target_page} successfully: {len(img_bytes)} bytes valid PNG image")

    # Edge cases: invalid page or non-existent file
    assert render_pdf_page_image(pdf_path, 0) is None, "Page 0 must return None, not 0"
    assert render_pdf_page_image(pdf_path, 999999) is None, "Out-of-bound page must return None"
    assert render_pdf_page_image("non_existent_file.pdf", 1) is None, "Non-existent file must return None"
    print("[OK] Function strictly returns None (never numeric 0 or int) on invalid input or failure")

    print("\n=================================================================")
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
