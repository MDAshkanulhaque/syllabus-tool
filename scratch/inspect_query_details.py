from backend.book_engine.book_search import search_book_sections

queries = [
    "numerical integration",
    "trapezoidal rule",
    "simpson rule",
    "runge kutta",
    "newton raphson",
    "least squares",
    "matrix",
]

for q in queries:
    res = search_book_sections(q)
    g_secs = res.get("NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL", [])
    print(f"\n=======================================================")
    print(f"QUERY: '{q}' -> {len(g_secs)} Grewal sections")
    print(f"=======================================================")
    for i, s in enumerate(g_secs):
        cat = s["category_key"]
        p_range = s["pdf_range"]
        m_cnt = len(s["matching_pages"])
        t_cnt = s["page_count"]
        score = s["score"]
        title = s["section_heading"]
        print(f"  [{i+1}] [{cat.upper():7s}] {title} | PDF {p_range} | Match: {m_cnt}/{t_cnt} | Score: {score}")
