import fitz

doc = fitz.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

for p in range(106, 113):
    txt = doc[p].get_text("text").lower()
    if "matrix" in txt or "matrices" in txt:
        print(f"PDF p.{p+1} contains matrix!")
        for l in doc[p].get_text("text").splitlines():
            if "matrix" in l.lower() or "matrices" in l.lower():
                print("   ", l.strip())
