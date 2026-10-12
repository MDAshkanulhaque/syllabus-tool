import pymupdf
import re

def parse_grewal_toc(pdf_path):
    doc = pymupdf.open(pdf_path)
    
    # TOC is on pages 5 to 14 (0-indexed 4 to 13)
    toc_text = ""
    for p in range(4, 14):
        toc_text += doc[p].get_text("text") + "\n"
        
    lines = [l.strip() for l in toc_text.splitlines() if l.strip()]
    
    entries = []
    current_ch_num = None
    current_ch_title = None
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check Chapter header e.g. "Chapter 1 Approximations and Errors"
        m_ch = re.match(r"^Chapter\s+(\d+)\s*(.*)$", line, re.IGNORECASE)
        if m_ch:
            current_ch_num = int(m_ch.group(1))
            raw_title = m_ch.group(2).strip()
            i += 1
            # Next line(s) might be continuation of chapter title
            while i < len(lines) and not lines[i].isdigit() and not re.match(r"^\d+\.\d+", lines[i]) and not re.match(r"^Chapter", lines[i], re.IGNORECASE):
                raw_title += " " + lines[i]
                i += 1
            # Next line might be chapter start page
            if i < len(lines) and lines[i].isdigit():
                i += 1
            current_ch_title = f"Chapter {current_ch_num}: {raw_title}".strip()
            current_ch_title = re.sub(r"\s+", " ", current_ch_title)
            continue
            
        # Check section header e.g. "1.1", "14.7", "3.2"
        m_sec = re.match(r"^(\d+\.\d{1,2})\s*(.*)$", line)
        if m_sec:
            sec_num = m_sec.group(1)
            raw_sec_title = m_sec.group(2).strip()
            i += 1
            while i < len(lines) and not lines[i].isdigit() and not re.match(r"^\d+\.\d+", lines[i]) and not re.match(r"^Chapter", lines[i], re.IGNORECASE) and not lines[i].startswith("Exercises"):
                raw_sec_title += " " + lines[i]
                i += 1
            sec_printed = None
            if i < len(lines) and lines[i].isdigit():
                sec_printed = int(lines[i])
                i += 1
                
            full_sec_title = f"{sec_num} {raw_sec_title}".strip()
            full_sec_title = re.sub(r"\s+", " ", full_sec_title)
            
            entries.append({
                "chapter_num": int(sec_num.split(".")[0]),
                "chapter_title": current_ch_title,
                "section_num": sec_num,
                "section_title": full_sec_title,
                "printed_page": sec_printed,
                "start_pdf": sec_printed + 14 if sec_printed else None,
            })
            continue
            
        i += 1

    # Verify and adjust any section start page by checking the actual text in the PDF
    # (e.g. Section 2.3 starts on printed page 26 / PDF page 40 rather than 25)
    for entry in entries:
        s_num = entry["section_num"]
        nominal_pdf = entry["start_pdf"]
        if not nominal_pdf or nominal_pdf > len(doc):
            continue
            
        # Check if heading is on nominal_pdf or nominal_pdf + 1
        p_text = doc[nominal_pdf - 1].get_text("text")
        if not re.search(rf"\b{re.escape(s_num)}\b", p_text):
            if nominal_pdf < len(doc):
                next_text = doc[nominal_pdf].get_text("text")
                if re.search(rf"\b{re.escape(s_num)}\b", next_text):
                    entry["start_pdf"] = nominal_pdf + 1
                    entry["printed_page"] = entry["printed_page"] + 1

    # Now compute exact end_pdf for each section:
    # A section ends on the page before the next section in the same chapter,
    # or before the next chapter begins!
    chapter_starts = {}
    for entry in entries:
        c_num = entry["chapter_num"]
        if c_num not in chapter_starts:
            chapter_starts[c_num] = entry["start_pdf"]
            
    for i, entry in enumerate(entries):
        c_num = entry["chapter_num"]
        if i + 1 < len(entries):
            next_entry = entries[i + 1]
            if next_entry["chapter_num"] == c_num:
                # Same chapter
                if next_entry["start_pdf"] > entry["start_pdf"]:
                    entry["end_pdf"] = next_entry["start_pdf"] - 1
                else:
                    entry["end_pdf"] = entry["start_pdf"]
            else:
                # Next chapter
                next_c_num = next_entry["chapter_num"]
                next_c_start = chapter_starts.get(next_c_num, 905)
                entry["end_pdf"] = max(entry["start_pdf"], next_c_start - 1)
        else:
            # Last section in book
            entry["end_pdf"] = 904 # Before Appendix A

    doc.close()
    return entries

if __name__ == "__main__":
    entries = parse_grewal_toc("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")
    print(f"Total entries: {len(entries)}")
    for e in entries:
        if e["section_num"] in ["1.1", "2.12", "3.2", "4.11", "4.12", "7.2", "10.7", "14.5", "14.7", "14.8", "16.2"]:
            cnt = e["end_pdf"] - e["start_pdf"] + 1
            print(f"Sec {e['section_num']:6s}: PDF {e['start_pdf']:3d}–{e['end_pdf']:3d} ({cnt:2d} pgs | pr {e['printed_page']}–{e['end_pdf']-14}) | {e['section_title']}")
