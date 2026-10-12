import sys
from pathlib import Path
sys.path.insert(0, ".")

import fitz
from backend.book_engine.book_search import search_book_sections, load_index

doc = fitz.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

queries = [
    "matrix",
    "matrices",
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

print("=================================================================")
print("SCANNING SUSPICIOUS SEARCH RESULTS IN B. S. GREWAL")
print("=================================================================")

for q in queries:
    res = search_book_sections(q)
    grewal_secs = res.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])
    
    suspicious = []
    for s in grewal_secs:
        cat = s["category_key"]
        matching_cnt = len(s["matching_pages"])
        total_cnt = s["page_count"]
        # suspicious if Other Content Match OR matching_cnt == 1 (especially when section has many pages)
        if cat == "content" or (matching_cnt == 1 and total_cnt > 1):
            suspicious.append(s)

    if suspicious:
        print(f"\n--- Query: '{q}' ({len(suspicious)} suspicious results) ---")
        for s in suspicious:
            sec_title = s["section_heading"]
            cat = s["category_key"]
            match_pages = s["matching_pages"]
            pdf_range = s["pdf_range"]
            print(f"  [{cat.upper()}] {sec_title} | Range: PDF {pdf_range} | Matching: {len(match_pages)}/{s['page_count']} (PDF pages: {match_pages})")
            
            # Print the actual text snippet matching on those pages
            for p_num in match_pages:
                txt = doc[p_num - 1].get_text("text")
                matching_lines = [
                    l.strip() for l in txt.splitlines() 
                    if any(w in l.lower() for w in q.lower().split())
                ]
                print(f"    Page {p_num} snippets ({len(matching_lines)} lines): {matching_lines[:2]}")
