import pymupdf

doc = pymupdf.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")
print("=== PDF Page 170 (pr 156) ===")
print(doc[169].get_text("text"))
