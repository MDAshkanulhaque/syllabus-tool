import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pymupdf
from backend.book_engine.book_search import search_book_sections, format_book_sections_response

print("=" * 70)
print("TESTING BOOK SEARCH UI & ORIGINAL PDF RENDERING")
print("=" * 70)

# TEST 1: MATRIX SEARCH & RENDERING
print("\n--- TEST 1: MATRIX SEARCH & ORIGINAL PDF RENDERING ---")
matrix_res = search_book_sections("matrix")
assert len(matrix_res) == 2, f"Expected 2 books, got {len(matrix_res)}"
total_matrix_secs = sum(len(s) for s in matrix_res.values())
print(f"Matrix search found {total_matrix_secs} sections across {len(matrix_res)} books.")

formatted_matrix = format_book_sections_response("matrix", matrix_res)
line_count = len(formatted_matrix.splitlines())
print(f"Formatted Matrix response line count: {line_count} lines (NO raw text dump!)")
assert line_count < 100, f"Expected concise response (<100 lines), got {line_count} lines!"
assert "• Complete Relevant Original Content:" not in formatted_matrix, "Raw content still being dumped!"
assert "• Chapter Heading:" in formatted_matrix
assert "• Section Heading:" in formatted_matrix
assert "• Printed Book Pages:" in formatted_matrix
assert "• Physical PDF Pages:" in formatted_matrix
assert "• Matching Pages:" in formatted_matrix
print("PASS: Matrix search response is concise, structured, and does not dump raw text.")

# Test rendering top section from both books for Matrix
for b_name, s_list in matrix_res.items():
    top_sec = s_list[0]
    pdf_path = top_sec["file_path"]
    start_p = top_sec["pdf_start"]
    doc = pymupdf.open(pdf_path)
    page_obj = doc[start_p - 1]
    pix = page_obj.get_pixmap(dpi=130)
    img_bytes = pix.tobytes("png")
    doc.close()
    
    print(f"PASS: Rendered original PDF page {start_p} for '{b_name[:30]}' ({pix.width}x{pix.height} px, {len(img_bytes)} bytes)")
    assert len(img_bytes) > 20000, "Rendered page image seems too small!"


# TEST 2: FOURIER SERIES SEARCH & RENDERING
print("\n--- TEST 2: FOURIER SERIES SEARCH & ORIGINAL PDF RENDERING ---")
fourier_res = search_book_sections("Fourier Series")
assert len(fourier_res) == 2, f"Expected 2 books, got {len(fourier_res)}"
total_fourier_secs = sum(len(s) for s in fourier_res.values())
print(f"Fourier Series search found {total_fourier_secs} sections across {len(fourier_res)} books.")

formatted_fourier = format_book_sections_response("Fourier Series", fourier_res)
f_line_count = len(formatted_fourier.splitlines())
print(f"Formatted Fourier response line count: {f_line_count} lines.")
assert f_line_count < 100, f"Expected concise response (<100 lines), got {f_line_count} lines!"
assert "• Complete Relevant Original Content:" not in formatted_fourier, "Raw content still being dumped!"

for b_name, s_list in fourier_res.items():
    if not s_list:
        continue
    top_sec = s_list[0]
    pdf_path = top_sec["file_path"]
    start_p = top_sec["pdf_start"]
    doc = pymupdf.open(pdf_path)
    page_obj = doc[start_p - 1]
    pix = page_obj.get_pixmap(dpi=130)
    img_bytes = pix.tobytes("png")
    doc.close()
    
    print(f"PASS: Rendered original PDF page {start_p} for '{b_name[:30]}' ({pix.width}x{pix.height} px, {len(img_bytes)} bytes)")
    assert len(img_bytes) > 20000, "Rendered page image seems too small!"

# TEST 3: MULTI-PAGE NAVIGATION IN SECTION
print("\n--- TEST 3: SECTION PAGE NAVIGATION & SURROUNDING PAGES ---")
kreyszig_secs = matrix_res.get("advanced-engineering-mathematics_by-erwin-kreyszig-__10th_edition-1", [])
top_k_sec = kreyszig_secs[0]
sec_pages = [p["pdf_page"] for p in top_k_sec["pages"]]
print(f"Top Kreyszig section '{top_k_sec['section_heading']}' spans {len(sec_pages)} pages: {sec_pages}")
assert len(sec_pages) >= 2, "Expected multi-page section"

# Verify all pages in section can be rendered cleanly
doc = pymupdf.open(top_k_sec["file_path"])
for p_num in sec_pages:
    page_obj = doc[p_num - 1]
    pix = page_obj.get_pixmap(dpi=130)
    assert pix.width > 500 and pix.height > 500
doc.close()
print(f"PASS: All {len(sec_pages)} pages of section verified for high-res vector rendering.")

print("\n" + "=" * 70)
print("ALL UI AND RENDERING TESTS PASSED SUCCESSFULLY!")
print("=" * 70)
