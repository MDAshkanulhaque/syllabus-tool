import pymupdf

doc = pymupdf.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

for p in range(113, 136):
    lines = [l.strip() for l in doc[p].get_text("text").splitlines() if l.strip()]
    first_few = " | ".join(lines[:4])
    headings = [l for l in lines if any(k in l.lower() for k in ["3.", "introduction", "matrices", "matrix", "solution", "elimination", "gauss", "linear"])]
    print(f"PDF p.{p+1} (printed {p-13}): {first_few[:80]}")
    for h in headings[:3]:
        print(f"     h: {h}")
