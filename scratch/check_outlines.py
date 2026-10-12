import pymupdf
import re
from pathlib import Path

grewal_path = Path("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")
kreyszig_path = Path("backend/books/advanced-engineering-mathematics_by-erwin-kreyszig-__10th_edition-1.pdf")

doc_k = pymupdf.open(kreyszig_path)
toc_k = doc_k.get_toc() # [lvl, title, page]

print(f"Kreyszig TOC count: {len(toc_k)}")
for item in toc_k:
    if "7" in item[1] or "Matrix" in item[1] or "Matrices" in item[1] or "Linear Algebra" in item[1]:
        print("K TOC:", item)

doc_g = pymupdf.open(grewal_path)
print(f"Grewal TOC count: {len(doc_g.get_toc())}")
print("Grewal TOC:", doc_g.get_toc())
