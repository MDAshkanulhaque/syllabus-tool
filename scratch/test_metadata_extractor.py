import sys
sys.path.insert(0, ".")
import pymupdf
from backend.book_engine.book_loader import load_books
from scratch.draft_grewal_extractor import extract_grewal_sections_and_metadata

books = load_books()
grewal_book = [b for b in books if "GREWAL" in b["book_name"]][0]
doc = pymupdf.open(grewal_book["file_path"])

meta = extract_grewal_sections_and_metadata(grewal_book, doc)
doc.close()

print(f"Total pages in Grewal: {len(meta)}")

# Sample various pages across different chapters
test_pages = [
    (15, "1.1 Introduction"),
    (27, "1.7 Error in a Series Approximation"),
    (52, "2.8 Bisection Method"),
    (71, "2.12 Newton-Raphson Method"),
    (82, "2.14 Muller’s Method"),
    (107, "3.1 Introduction t to Determinants"),
    (114, "3.2 Introduction To Matrices"),
    (120, "3.2 Introduction To Matrices"),
    (127, "3.2 Introduction To Matrices"),
    (128, "3.3 Solution of Linear Simultaneous Equations"),
    (129, "3.4 Direct Methods of Solution"),
    (170, "4.2 Matrix Inversion or 4.3 Gauss Elimination"),
    (188, "4.11 Power Method"),
    (193, "4.12 Jacobi’s Method"),
    (288, "7.2 Newton’s Forward Interpolation Formula"),
    (321, "7.12 Lagrange’s Interpolation Formula"),
    (373, "8.5 Newton-Cotes Quadrature Formula"),
    (454, "10.7 Runge-Kutta Method"),
    (470, "10.10 Adams-Bashforth Method"),
    (587, "12.7 Simplex Method"),
    (633, "12.14 Transportation Problem"),
    (693, "14.5 Newton Raphson Method"),
    (698, "14.7 Multiplication of Matrices"),
    (701, "14.8 Gauss Elimination Method"),
    (852, "16.2 An Overview of MATLAB Features"),
]

print("\n--- SAMPLE PAGE VERIFICATION ---")
for p, expected in test_pages:
    item = meta[p - 1]
    sec = item["section_heading"]
    ch = item["chapter_heading"]
    pr = item["printed_page"]
    print(f"PDF p.{p:3d} (pr:{pr:3s}) -> {sec[:40]} | {ch[:30]}")
