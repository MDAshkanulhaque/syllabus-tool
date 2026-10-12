import pymupdf
import re

doc = pymupdf.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

toc_text = ""
for p in range(4, 14):
    toc_text += f"\n--- TOC PAGE {p+1} ---\n" + doc[p].get_text("text")

print(f"Total TOC text length: {len(toc_text)}")

# Let's write the raw TOC text to scratch for inspection
with open("scratch/grewal_raw_toc.txt", "w", encoding="utf-8") as f:
    f.write(toc_text)

print("Saved scratch/grewal_raw_toc.txt")
