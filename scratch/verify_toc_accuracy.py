import pymupdf
import re

doc = pymupdf.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

# Import the extracted TOC entries from scratch/extract_all_toc_entries.py logic
with open("scratch/grewal_raw_toc.txt", "r", encoding="utf-8") as f:
    toc_text = f.read()

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
        while i < len(lines) and not lines[i].isdigit() and not re.match(r"^\d+\.\d+", lines[i]) and not re.match(r"^Chapter", lines[i], re.IGNORECASE):
            current_ch_name += " " + lines[i]
            i += 1
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

# Check each section: does its section number or title appear on PDF page `pdf_page` (or `pdf_page - 1` or `pdf_page + 1`)?
matches = 0
mismatches = 0
for entry in all_toc_entries:
    sec_num = entry["section_num"]
    sec_title = entry["section_title"]
    p_num = entry["pdf_page"]
    if not p_num or p_num > len(doc):
        continue
        
    page_text = doc[p_num - 1].get_text("text")
    # Clean check
    found_exact = (sec_num in page_text)
    # Check adjacent if not found
    found_prev = (sec_num in doc[p_num - 2].get_text("text")) if p_num > 1 else False
    found_next = (sec_num in doc[p_num].get_text("text")) if p_num < len(doc) else False
    
    if found_exact:
        matches += 1
    else:
        mismatches += 1
        print(f"NOT on expected p.{p_num}: Sec {sec_num} ({sec_title}) | prev(p.{p_num-1})={found_prev} | next(p.{p_num+1})={found_next}")

print(f"\nTotal verified: {matches} exact matches on PDF p = printed + 14, {mismatches} mismatches out of {len(all_toc_entries)}")
