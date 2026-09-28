import fitz

doc = fitz.open("backend/uploads/BCI-2024-2025 VIT SYLLABUS.pdf")
print("Total pages:", len(doc))

for pno in range(1, len(doc) + 1):
    txt = doc[pno - 1].get_text()
    if len(txt.strip()) > 50:
        lines = [l.strip() for l in txt.splitlines() if l.strip()]
        print(f"\n--- PAGE {pno} (Lines: {len(lines)}) ---")
        for l in lines[:6]:
            print("  ", l)
doc.close()
