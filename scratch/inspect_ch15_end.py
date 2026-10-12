import fitz

doc = fitz.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

for p in range(843, 853):
    txt = doc[p].get_text("text")
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    top = lines[0] if lines else ""
    secs = [l for l in lines if "15." in l or "16." in l or "Exercises" in l or "Chapter" in l or "C H A P T E R" in l]
    print(f"PDF p.{p+1} (pr {p+1-14}): Top='{top[:35]}' | Secs={secs}")
