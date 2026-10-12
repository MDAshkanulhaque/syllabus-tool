import pymupdf

doc = pymupdf.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")
print("=== PAGE 128 (PDF p.128, printed 114) ===")
print(doc[127].get_text("text"))

print("\n=== PAGE 129 (PDF p.129, printed 115) ===")
print(doc[128].get_text("text"))
