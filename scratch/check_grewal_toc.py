import pymupdf

doc = pymupdf.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

print("doc.get_toc():", doc.get_toc()[:10])

for p in range(0, 20):
    txt = doc[p].get_text("text")
    if any(k in txt.lower() for k in ["contents", "brief contents"]):
        print(f"=== PDF Page {p+1} ===")
        print(txt[:1000])
