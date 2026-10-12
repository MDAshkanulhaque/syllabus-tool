import pymupdf
import re
from pathlib import Path

grewal_path = Path("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")
doc_g = pymupdf.open(grewal_path)

# Let's search for "C H A P T E R" or "CHAPTER" or chapter beginnings in Grewal
print("Scanning Grewal for Chapter headers...")
chapter_pages = []
for p_idx in range(len(doc_g)):
    text = doc_g[p_idx].get_text("text")
    first_lines = [l.strip() for l in text.splitlines()[:10] if l.strip()]
    first_block = " ".join(first_lines)
    # Check if chapter starts here
    m = re.search(r"C\s*H\s*A\s*P\s*T\s*E\s*R\s*(\d+)", first_block, re.IGNORECASE)
    if m:
        chapter_pages.append((p_idx + 1, m.group(0), first_lines[:4]))

print(f"Found {len(chapter_pages)} chapters in Grewal:")
for cp in chapter_pages:
    print(f"  PDF Page {cp[0]}: {cp[1]} -> {cp[2]}")
