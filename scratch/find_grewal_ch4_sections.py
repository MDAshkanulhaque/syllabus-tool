import pymupdf
import re

doc_g = pymupdf.open('backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf')

ch4_sections = []
for p_num in range(169, 207):
    text = doc_g[p_num - 1].get_text("text")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for l in lines:
        m = re.match(r"^(4\.\d{1,2})\s+([A-Z][^\n]{2,100})$", l)
        if m:
            ch4_sections.append((p_num, m.group(1), m.group(2)))

print(f"Chapter 4 sections found: {len(ch4_sections)}")
for s in ch4_sections:
    print(f"  PDF Page {s[0]}: {s[1]} {s[2]}")
