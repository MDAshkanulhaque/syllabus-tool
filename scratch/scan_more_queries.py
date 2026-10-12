import sys
from pathlib import Path
sys.path.insert(0, ".")

import fitz
from backend.book_engine.book_search import search_book_sections

doc = fitz.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

queries = [
    "gauss elimination",
    "runge kutta",
    "bisection method",
    "newton raphson",
    "simpson rule",
    "trapezoidal rule",
    "euler method",
    "taylor series",
    "cramer rule",
    "regula falsi",
    "jacobi method",
    "secant method",
]

for q in queries:
    res = search_book_sections(q)
    g_secs = res.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])
    suspicious = [
        s for s in g_secs 
        if s["category_key"] == "content" or len(s["matching_pages"]) == 1
    ]
    if suspicious:
        print(f"\n=======================================================")
        print(f"QUERY: '{q}' ({len(suspicious)} suspicious / 1-page / content matches)")
        print(f"=======================================================")
        for s in suspicious:
            sec_title = s["section_heading"]
            cat = s["category_key"]
            m_pages = s["matching_pages"]
            p_range = s["pdf_range"]
            print(f"  [{cat.upper():7s}] {sec_title} (PDF {p_range}) | Matched {len(m_pages)}/{s['page_count']} pgs: {m_pages}")
            for p in m_pages:
                txt = doc[p - 1].get_text("text")
                snippets = [l.strip() for l in txt.splitlines() if any(w in l.lower() for w in q.lower().split())]
                print(f"     p.{p}: {snippets[:2]}")
