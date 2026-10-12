import sys
sys.path.insert(0, ".")
from backend.book_engine.book_search import search_book_sections

for q in ["Fourier Series", "Matrix", "least squares", "secant method", "bisection method", "interpolation"]:
    res = search_book_sections(q)
    for b, secs in res.items():
        unavail = [s for s in secs if s["section_heading"] == "Unavailable"]
        if unavail:
            print(f"Query '{q}' in '{b[:25]}' has {len(unavail)} Unavailable sections: {[u['pdf_range'] for u in unavail]}")
