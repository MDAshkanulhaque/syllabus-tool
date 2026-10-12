import json
import re
import pymupdf

doc = pymupdf.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

# Parse TOC from pages 5 to 14
toc_lines = []
for p in range(4, 14):
    text = doc[p].get_text("text")
    for l in text.splitlines():
        l = l.strip()
        if l:
            toc_lines.append(l)

# Let's inspect how TOC entries are parsed
parsed_toc = []
current_ch_num = None
current_ch_title = None

i = 0
while i < len(toc_lines):
    line = toc_lines[i]
    
    # Check chapter
    m_ch = re.match(r"^Chapter\s+(\d+)\s+(.+)$", line, re.IGNORECASE)
    if m_ch:
        current_ch_num = int(m_ch.group(1))
        current_ch_title = m_ch.group(2).strip()
        # Look ahead for page number
        i += 1
        if i < len(toc_lines) and toc_lines[i].isdigit():
            ch_page = int(toc_lines[i])
            i += 1
        continue
        
    # Check section e.g. "3.2" or "3.2 Introduction to Matrices"
    m_sec = re.match(r"^(\d+\.\d{1,2})\s*(.*)$", line)
    if m_sec:
        sec_num = m_sec.group(1)
        sec_title = m_sec.group(2).strip()
        i += 1
        # Title might continue on next line if next line is not a digit and not another section/chapter
        while i < len(toc_lines) and not toc_lines[i].isdigit() and not re.match(r"^\d+\.\d{1,2}", toc_lines[i]) and not re.match(r"^Chapter", toc_lines[i], re.IGNORECASE) and not toc_lines[i].startswith("Exercises"):
            sec_title += " " + toc_lines[i]
            i += 1
        # Next line might be the page number
        sec_page = None
        if i < len(toc_lines) and toc_lines[i].isdigit():
            sec_page = int(toc_lines[i])
            i += 1
            
        parsed_toc.append({
            "chapter_num": int(sec_num.split(".")[0]),
            "chapter_title": current_ch_title,
            "section_num": sec_num,
            "section_title": sec_title.strip(),
            "printed_page": sec_page,
            "pdf_page": (sec_page + 14) if sec_page else None
        })
        continue
        
    i += 1

print(f"Total TOC sections parsed: {len(parsed_toc)}")

# Load existing index
with open("backend/book_index/pages_index.json", "r", encoding="utf-8") as f:
    records = json.load(f)

# Group existing Grewal records by section_heading
existing_sections = {}
for r in records:
    if "GREWAL" in r.get("book_name", ""):
        sec = r.get("section_heading")
        p = r.get("pdf_page")
        if sec and sec != "Unavailable":
            if sec not in existing_sections:
                existing_sections[sec] = []
            existing_sections[sec].append(p)

print(f"Total existing indexed sections in Grewal: {len(existing_sections)}")

# Compare each parsed TOC section
print("\n--- COMPARISON (TOC vs Existing Index) ---")
for s in parsed_toc:
    s_num = s["section_num"]
    s_title = s["section_title"]
    toc_pr = s["printed_page"]
    toc_pdf = s["pdf_page"]
    
    # find in existing
    match = None
    for ex_sec, pages in existing_sections.items():
        if ex_sec.startswith(s_num + " "):
            match = (ex_sec, min(pages), max(pages), len(pages))
            break
            
    if match:
        ex_name, ex_start, ex_end, ex_cnt = match
        diff_str = "" if ex_start == toc_pdf else f" MISMATCH START: index={ex_start} vs toc={toc_pdf}"
        print(f"Sec {s_num:5s}: TOC PDF {toc_pdf} (pr {toc_pr}) | Index PDF {ex_start}–{ex_end} (cnt={ex_cnt}){diff_str}")
    else:
        print(f"Sec {s_num:5s}: TOC PDF {toc_pdf} (pr {toc_pr}) | MISSING IN INDEX! ({s_title})")
