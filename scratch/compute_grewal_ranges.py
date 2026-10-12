import pymupdf
import re

doc = pymupdf.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

# Extract TOC from pages 5 to 14
toc_text = ""
for p in range(4, 14):
    toc_text += doc[p].get_text("text") + "\n"

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

print(f"Extracted {len(all_toc_entries)} TOC entries.")

# Now verify and refine exact start page by checking where the heading actually appears
verified_sections = []
for idx, entry in enumerate(all_toc_entries):
    sec_num = entry["section_num"]
    sec_title = entry["section_title"]
    nominal_pdf = entry["pdf_page"]
    
    # Check nominal page, -1, +1, +2
    actual_start = nominal_pdf
    # Pattern to match in page text: e.g. "3.2 Introduction to Matrices" or "3.2 " at start of a line
    found_on = None
    for p_check in [nominal_pdf, nominal_pdf + 1, nominal_pdf - 1, nominal_pdf + 2]:
        if 1 <= p_check <= len(doc):
            p_text = doc[p_check - 1].get_text("text")
            # check if sec_num followed by space, dot, or title words appears as a heading or in text
            if re.search(rf"\b{re.escape(sec_num)}\b", p_text):
                found_on = p_check
                break
                
    if found_on:
        actual_start = found_on
    else:
        # Keep nominal_pdf
        actual_start = nominal_pdf

    # Clean section title
    clean_title = f"{sec_num} {sec_title}".strip()
    clean_title = re.sub(r"\s+", " ", clean_title)
    
    # Clean chapter title
    ch_num = entry["chapter_num"]
    ch_name = entry["chapter_name"].strip()
    ch_name = re.sub(r"\s+", " ", ch_name)
    clean_ch = f"Chapter {ch_num}: {ch_name}".strip()
    
    verified_sections.append({
        "chapter_num": ch_num,
        "chapter_heading": clean_ch,
        "section_num": sec_num,
        "section_heading": clean_title,
        "start_pdf": actual_start,
        "start_printed": actual_start - 14,
    })

# Now compute end_pdf for each section:
# A section ends on the page before the next section in the same chapter,
# or for the last section in a chapter, on the page before the next chapter starts!
# Let's find chapter start pages from TOC
chapter_starts = {}
for s in verified_sections:
    c_num = s["chapter_num"]
    if c_num not in chapter_starts:
        chapter_starts[c_num] = s["start_pdf"]

# Also find start of Appendix A (printed page 891 -> PDF page 905)
end_of_book_pdf = 905 # Appendix A

for i, s in enumerate(verified_sections):
    c_num = s["chapter_num"]
    if i + 1 < len(verified_sections):
        next_s = verified_sections[i + 1]
        if next_s["chapter_num"] == c_num:
            # Next section in same chapter
            # If next section starts on page X, does current section end on X or X-1?
            # If next section starts on page X, current section pages are start_pdf .. max(start_pdf, next_s["start_pdf"] - 1)
            # UNLESS next section starts on the same page!
            if next_s["start_pdf"] > s["start_pdf"]:
                s["end_pdf"] = next_s["start_pdf"] - 1
            else:
                s["end_pdf"] = s["start_pdf"]
        else:
            # Last section in chapter! Ends before next chapter starts
            next_ch_num = next_s["chapter_num"]
            next_ch_start = chapter_starts.get(next_ch_num, end_of_book_pdf)
            s["end_pdf"] = max(s["start_pdf"], next_ch_start - 1)
    else:
        # Last section in book
        s["end_pdf"] = 904 # before Appendix A

for s in verified_sections[:20]:
    cnt = s["end_pdf"] - s["start_pdf"] + 1
    print(f"[{s['chapter_heading'][:20]}] {s['section_heading'][:35]} | PDF {s['start_pdf']}–{s['end_pdf']} ({cnt} pgs)")
