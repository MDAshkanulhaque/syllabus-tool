import pymupdf
import re

doc = pymupdf.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

# Parse entire TOC from pages 5 to 14
toc_text = ""
for p in range(4, 14):
    toc_text += doc[p].get_text("text") + "\n"

# Let's inspect all lines
lines = [l.strip() for l in toc_text.splitlines() if l.strip()]

all_toc_entries = []
current_ch_num = 0
current_ch_name = ""

i = 0
while i < len(lines):
    l = lines[i]
    m_ch = re.match(r"^Chapter\s+(\d+)\s*(.*)$", l, re.IGNORECASE)
    if m_ch:
        current_ch_num = int(m_ch.group(1))
        current_ch_name = m_ch.group(2).strip()
        i += 1
        # if next line is not a number and not a section, it's title continuation
        while i < len(lines) and not lines[i].isdigit() and not re.match(r"^\d+\.\d+", lines[i]) and not re.match(r"^Chapter", lines[i], re.IGNORECASE):
            current_ch_name += " " + lines[i]
            i += 1
        # page number might follow
        if i < len(lines) and lines[i].isdigit():
            i += 1
        continue
        
    m_sec = re.match(r"^(\d+\.\d{1,2})\s*(.*)$", l)
    if m_sec:
        sec_num = m_sec.group(1)
        sec_title = m_sec.group(2).strip()
        i += 1
        while i < len(lines) and not lines[i].isdigit() and not re.match(r"^\d+\.\d+", lines[i]) and not re.match(r"^Chapter", lines[i], re.IGNORECASE) and not lines[i].startswith("Exercises"):
            sec_title += " " + lines[i]
            i += 1
        page_num = None
        if i < len(lines) and lines[i].isdigit():
            page_num = int(lines[i])
            i += 1
            
        all_toc_entries.append({
            "chapter_num": current_ch_num,
            "chapter_name": current_ch_name,
            "section_num": sec_num,
            "section_title": sec_title.strip(),
            "printed_page": page_num,
            "pdf_page": page_num + 14 if page_num else None
        })
        continue
    i += 1

print(f"Total sections extracted from TOC: {len(all_toc_entries)}")
for entry in all_toc_entries:
    print(f"Ch {entry['chapter_num']:2d} | Sec {entry['section_num']:5s} | Printed p.{entry['printed_page']:3d} | PDF p.{entry['pdf_page']:3d} | {entry['section_title']}")
