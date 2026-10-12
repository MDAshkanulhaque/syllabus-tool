import sys
sys.path.insert(0, ".")

import fitz
from backend.book_engine.book_search import search_book_sections

doc = fitz.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

queries = [
    "matrix",
    "linear equations",
    "eigenvalues",
    "interpolation",
    "numerical integration",
    "differential equations",
    "finite differences",
    "curve fitting",
    "bisection method",
    "newton raphson",
    "gauss elimination",
    "runge kutta",
    "trapezoidal rule",
    "simpson rule",
    "least squares",
]

suspicious_records = []

for q in queries:
    res = search_book_sections(q)
    g_secs = res.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])
    for s in g_secs:
        # Check if 1 matching page in a multi-page section OR Other Content Match
        if s["category_key"] == "content" or (len(s["matching_pages"]) == 1 and s["page_count"] > 1):
            suspicious_records.append({
                "query": q,
                "section": s["section_heading"],
                "chapter": s["chapter_heading"],
                "category": s["category_key"],
                "pdf_range": s["pdf_range"],
                "matching_pages": s["matching_pages"],
                "page_count": s["page_count"],
                "score": s["score"]
            })

print(f"Total suspicious results across all {len(queries)} queries: {len(suspicious_records)}")

# Group by section
by_sec = {}
for r in suspicious_records:
    sec = r["section"]
    if sec not in by_sec:
        by_sec[sec] = []
    by_sec[sec].append(r)

for sec, items in sorted(by_sec.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\nSection: {sec} ({len(items)} queries flagged)")
    for it in items:
        print(f"   Query '{it['query']}' [{it['category']}] -> PDF {it['pdf_range']} | matched: {it['matching_pages']}/{it['page_count']}")
