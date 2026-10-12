import pymupdf
import re

doc_g = pymupdf.open('backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf')

# Let's inspect sections across Chapter 3 (107 to 168) and Chapter 4 (169 to 206)
ch3_sections = []
for p_num in range(107, 169):
    text = doc_g[p_num - 1].get_text("text")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for l in lines:
        m = re.match(r"^(3\.\d{1,2})\s+([A-Z][^\n]{2,100})$", l)
        if m:
            ch3_sections.append((p_num, m.group(1), m.group(2)))

print(f"Chapter 3 sections found: {len(ch3_sections)}")
for s in ch3_sections:
    print(f"  PDF Page {s[0]}: {s[1]} {s[2]}")
