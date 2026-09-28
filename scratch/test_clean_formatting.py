import fitz
import sys
import os
import re

pdf_path = "backend/uploads/RAJALAKSHMIINSTITUTEOF TECHNOLOGY BE-CSE-SYLLABUS-2023-27.pdf"
doc = fitz.open(pdf_path)

print("Total pages in RIT PDF:", len(doc))

# Search for pages containing detailed unit descriptions
for p_idx, page in enumerate(doc, 1):
    text = page.get_text()
    if "DATABASE MANAGEMENT SYSTEMS" in text.upper():
        print(f"Page {p_idx} has DBMS. Has UNIT I? {'UNIT I' in text.upper() or 'UNIT 1' in text.upper()}")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for l in lines[:10]:
            print("   ", l[:80])
