import pymupdf

doc = pymupdf.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")
for p in [112, 113, 114, 115]:
    print(f"=== PHYSICAL PDF PAGE {p+1} ===")
    print(doc[p].get_text("text"))
