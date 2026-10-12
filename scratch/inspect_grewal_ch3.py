import pymupdf
import re
from pathlib import Path

pdf_path = Path("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")
doc = pymupdf.open(pdf_path)

print(f"Total pages in Grewal: {len(doc)}")

# Look for Chapter 3 and Section 3.2
for p_idx in range(90, 150):
    text = doc[p_idx].get_text("text")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    first_few = " | ".join(lines[:4])
    has_3_2 = any("3.2" in l for l in lines)
    has_matrix = any("matrices" in l.lower() or "matrix" in l.lower() for l in lines)
    if has_3_2 or (95 <= p_idx + 1 <= 125 and ("chapter 3" in text.lower() or "simultaneous" in text.lower() or has_matrix)):
        print(f"PDF p.{p_idx + 1}: {first_few[:120]}")
        for l in lines:
            if "3.2" in l or "3.1" in l or "3.3" in l or "chapter 3" in l.lower() or "introduction to matrices" in l.lower():
                print(f"    --> {l}")
