import pymupdf

doc = pymupdf.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")
print("=== PDF Page 39 ===")
for l in doc[38].get_text("text").splitlines()[:10]:
    print("  ", l)
print("=== PDF Page 40 ===")
for l in doc[39].get_text("text").splitlines()[:10]:
    print("  ", l)
