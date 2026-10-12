import pymupdf

doc = pymupdf.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

for p in range(4, 8):
    print(f"=== PDF Page {p+1} ===")
    print(doc[p].get_text("text"))
