import pymupdf
import re

doc = pymupdf.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

# Sample physical pages across the book and read the printed page number from the header/footer
offsets = {}
for p_idx in range(14, len(doc)):
    txt = doc[p_idx].get_text("text")
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    pdf_p = p_idx + 1
    
    # Check top 3 lines or bottom 3 lines for printed page number
    found_printed = None
    for l in lines[:3] + lines[-3:]:
        # Pattern like "100 • NUMERICAL..." or "SOLUTION ... • 101" or standalone number
        m1 = re.search(r"^(\d{1,3})\s*•", l)
        m2 = re.search(r"•\s*(\d{1,3})$", l)
        m3 = re.match(r"^(\d{1,3})$", l)
        if m1:
            found_printed = int(m1.group(1))
            break
        elif m2:
            found_printed = int(m2.group(1))
            break
        elif m3 and int(m3.group(1)) > 0:
            found_printed = int(m3.group(1))
            break
            
    if found_printed:
        diff = pdf_p - found_printed
        offsets[diff] = offsets.get(diff, 0) + 1

print("Offsets (PDF page - Printed page) distribution:")
for diff, cnt in sorted(offsets.items()):
    print(f"Diff {diff}: {cnt} pages")
