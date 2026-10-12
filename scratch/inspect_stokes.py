from backend.book_engine.book_search import search_book_sections, load_index

records = load_index()
stokes = [p for p in records if "stokes" in (p.get("section_heading") or "").lower()]
print(f"Stokes pages count: {len(stokes)}")
for p in stokes:
    txt = p.get("search_text", "")
    has_fourier = "fourier" in txt
    has_series = "series" in txt
    pdf_p = p.get("pdf_page")
    print(f"PDF {pdf_p}: fourier={has_fourier}, series={has_series}")
    if has_fourier:
        for line in p.get("text", "").splitlines():
            if "fourier" in line.lower():
                print(f"   Fourier line in p.{pdf_p}: {line.strip()}")

fourier_res = search_book_sections("Fourier Series")
kreyszig = fourier_res.get("advanced-engineering-mathematics_by-erwin-kreyszig-__10th_edition-1", [])
for s in kreyszig:
    if "stokes" in s.get("section_heading", "").lower():
        print("\nStokes match found in results:")
        print("Category:", s.get("category_key"), s.get("match_category"))
        print("Score:", s.get("score"))
        print("Matching pages:", s.get("matching_pages"))
        print("Page count:", s.get("page_count"))
