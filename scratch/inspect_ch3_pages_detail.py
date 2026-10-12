import fitz

doc = fitz.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

for p in range(106, 131):
    txt = doc[p].get_text("text")
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    top_line = lines[0] if lines else ""
    headings = [l for l in lines if any(l.startswith(f"3.{d}") for d in range(1, 10))]
    print(f"PDF p.{p+1:3d} (pr {p+1-14:3d}): Top='{top_line[:40]}' | Headings={headings}")
