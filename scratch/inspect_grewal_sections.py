import pymupdf
import re
from pathlib import Path

grewal_path = Path("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")
doc_g = pymupdf.open(grewal_path)

# Let's inspect pages 107-168 (Chapter 3) and pages 169-206 (Chapter 4)
for p in [107, 108, 109, 110, 114, 115, 116, 120, 169, 170, 171]:
    text = doc_g[p - 1].get_text("text")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    print(f"\n=== Grewal PDF Page {p} ===")
    # Look for section patterns like "3.1", "3.2", "4.1" etc.
    sec_matches = [l for l in lines if re.match(r"^\d+\.\d+\b", l)]
    print("Section-like lines:", sec_matches)
    print("Top 3 lines:", lines[:3])
