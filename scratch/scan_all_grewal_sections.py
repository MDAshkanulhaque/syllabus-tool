import pymupdf
import re

doc_g = pymupdf.open('backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf')

# Scan for all sections of form X.Y Title
all_sections = []
for p_num in range(15, 931):
    text = doc_g[p_num - 1].get_text("text")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for l in lines:
        # Match e.g. "3.2 Introduction to Matrices" or "12.1 Introduction"
        m = re.match(r"^(\d{1,2}\.\d{1,2})\s+([A-Z][a-zA-Z0-9\s\-\,\(\)\/\–\—\:\.]{2,80})$", l)
        if m:
            sec_num = m.group(1)
            sec_title = m.group(2).strip()
            # Filter out math equations or citations like "3.2 (a)" or ending with punctuation
            if not any(bad in sec_title for bad in ["=", "+", "dx", "dt", "Table", "Fig", "Example"]):
                all_sections.append((p_num, sec_num, f"{sec_num} {sec_title}"))

print(f"Total section candidates in Grewal: {len(all_sections)}")
# Group by section number (first occurrence is where the section starts)
seen = set()
unique_sections = []
for p, num, full in all_sections:
    if num not in seen:
        seen.add(num)
        unique_sections.append((p, num, full))

print(f"Unique sections: {len(unique_sections)}")
for s in unique_sections[:20]:
    print(f"  PDF Page {s[0]}: {s[2]}")
