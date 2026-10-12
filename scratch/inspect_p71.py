import fitz

doc = fitz.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

print("=== PDF Page 71 (pr 57) ===")
print(doc[70].get_text("text")[:1000])
