import fitz
import re
from backend.book_engine.book_search import search_book_sections, load_index

doc = fitz.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

test_cases = [
    # (topic_query, expected_sec_prefix, expected_ch_num)
    ("Useful Rules for Estimating Errors", "1.4", 1),
    ("Error in a Series Approximation", "1.7", 1),
    ("Bisection Method", "2.8", 2),
    ("Newton-Raphson Method", "2.12", 2),
    ("Muller's Method", "2.14", 2),
    ("Lin-Bairstow's Method", "2.18", 2),
    ("Introduction to Matrices", "3.2", 3),
    ("Direct Methods of Solution", "3.4", 3),
    ("Ill-Conditioned Equations", "3.6", 3),
    ("Matrix Inversion", "4.2", 4),
    ("Gauss Elimination Method", "4.3", 4),
    ("Eigenvalues and Eigenvectors", "4.8", 4),
    ("Power Method", "4.11", 4),
    ("Jacobi's Method", "4.12", 4),
    ("Summation of Series", "6.11", 6),
    ("Newton's Forward Interpolation", "7.2", 7),
    ("Lagrange's Interpolation Formula", "7.12", 7),
    ("Spline Interpolation", "7.17", 7),
    ("Newton-Cotes Quadrature", "8.5", 8),
    ("Romberg's Method", "8.7", 8),
    ("Euler's Method", "10.4", 10),
    ("Runge-Kutta Method", "10.7", 10),
    ("Milne's Method", "10.9", 10),
    ("Simplex Method", "12.7", 12),
    ("Transportation Problem", "12.14", 12),
    ("Assignment Problem", "12.17", 12),
    ("Multiplication of Matrices", "14.7", 14),
    ("Overview of MATLAB", "16.2", 16),
]

print("=" * 80)
print("COMPREHENSIVE CROSS-CHAPTER SECTION MAPPING VERIFICATION")
print("=" * 80)

records = load_index()
grewal_records = [r for r in records if "GREWAL" in r.get("book_name", "")]

# Group by (chapter_heading, section_heading)
section_pages = {}
for r in grewal_records:
    sec = r.get("section_heading")
    ch = r.get("chapter_heading")
    if sec and sec != "Unavailable":
        key = (ch, sec)
        if key not in section_pages:
            section_pages[key] = []
        section_pages[key].append(r["pdf_page"])

all_passed = True

for query, sec_prefix, ch_num in test_cases:
    # 1. Find section in indexed pages
    matched_key = None
    for (ch, sec) in section_pages:
        if sec.startswith(sec_prefix + " "):
            matched_key = (ch, sec)
            break
            
    if not matched_key:
        print(f"FAILED to find {sec_prefix} in indexed sections!")
        all_passed = False
        continue

    ch_name, sec_name = matched_key
    pages = sorted(section_pages[matched_key])
    first_p = pages[0]
    last_p = pages[-1]
    pr_first = first_p - 14
    pr_last = last_p - 14
    seq_continuous = (pages == list(range(first_p, last_p + 1)))

    # 2. Verify heading in physical PDF at first_p
    p_text = doc[first_p - 1].get_text("text")
    heading_found_on_first = bool(re.search(rf"\b{re.escape(sec_prefix)}\b", p_text))

    # 3. Check search_book_sections result
    search_res = search_book_sections(query)
    grewal_res = search_res.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])
    top_sec = grewal_res[0] if grewal_res else None
    search_matches = (top_sec and top_sec["section_heading"].startswith(sec_prefix))

    status = "OK" if (heading_found_on_first and seq_continuous) else "FAIL"
    if status != "OK":
        all_passed = False

    print(f"[{status}] Ch {ch_num:2d} | Sec {sec_name[:40]:40s}")
    print(f"       Range: PDF {first_p}–{last_p} (printed {pr_first}–{pr_last}) | Count: {len(pages)} pgs | Contig: {seq_continuous}")
    print(f"       Heading in PDF p.{first_p}: {heading_found_on_first} | Top Search Result: {top_sec['section_heading'] if top_sec else 'None'}")

print("=" * 80)
print(f"FINAL RESULT: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
print("=" * 80)
