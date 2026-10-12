import json
import re
import pymupdf
from pathlib import Path

def extract_grewal_sections_and_metadata(book, doc):
    total_pages = len(book["pages"])
    page_metadata = [{} for _ in range(total_pages)]
    
    # 1. Determine printed page numbers:
    # In B. S. Grewal, physical page 15 is printed page 1, up to page 904 which is printed page 890.
    for p_idx in range(total_pages):
        pdf_page = p_idx + 1
        if 15 <= pdf_page <= 904:
            page_metadata[p_idx]["printed_page"] = str(pdf_page - 14)
        else:
            page_metadata[p_idx]["printed_page"] = "Unavailable"
            
    # 2. Parse authoritative TOC from pages 5 to 14 (indices 4 to 13)
    toc_text = ""
    for p in range(4, 14):
        if p < total_pages:
            toc_text += doc[p].get_text("text") + "\n"
            
    lines = [l.strip() for l in toc_text.splitlines() if l.strip()]
    
    entries = []
    current_ch_num = None
    current_ch_title = None
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        m_ch = re.match(r"^Chapter\s+(\d+)\s*(.*)$", line, re.IGNORECASE)
        if m_ch:
            current_ch_num = int(m_ch.group(1))
            raw_title = m_ch.group(2).strip()
            i += 1
            while i < len(lines) and not lines[i].isdigit() and not re.match(r"^\d+\.\d+", lines[i]) and not re.match(r"^Chapter", lines[i], re.IGNORECASE):
                raw_title += " " + lines[i]
                i += 1
            if i < len(lines) and lines[i].isdigit():
                i += 1
            current_ch_title = f"Chapter {current_ch_num}: {raw_title}".strip()
            current_ch_title = re.sub(r"\s+", " ", current_ch_title)
            continue
            
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

    # Verify start_pdf against PDF text
    for entry in entries:
        s_num = entry["section_num"]
        nominal_pdf = entry["start_pdf"]
        if not nominal_pdf or nominal_pdf > total_pages:
            continue
        p_text = doc[nominal_pdf - 1].get_text("text")
        if not re.search(rf"\b{re.escape(s_num)}\b", p_text):
            if nominal_pdf < total_pages:
                next_text = doc[nominal_pdf].get_text("text")
                if re.search(rf"\b{re.escape(s_num)}\b", next_text):
                    entry["start_pdf"] = nominal_pdf + 1
                    entry["printed_page"] = entry["printed_page"] + 1

    # Compute boundaries
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
                if next_entry["start_pdf"] > entry["start_pdf"]:
                    entry["end_pdf"] = next_entry["start_pdf"] - 1
                else:
                    entry["end_pdf"] = entry["start_pdf"]
            else:
                next_c_num = next_entry["chapter_num"]
                next_c_start = chapter_starts.get(next_c_num, 905)
                entry["end_pdf"] = max(entry["start_pdf"], next_c_start - 1)
        else:
            entry["end_pdf"] = min(total_pages, 904)

    # Assign metadata to every page
    # Default everything to Unavailable
    for p_idx in range(total_pages):
        page_metadata[p_idx]["chapter_heading"] = "Unavailable"
        page_metadata[p_idx]["section_heading"] = "Unavailable"

    # Map each section's exact range
    for entry in entries:
        s_start = entry["start_pdf"]
        s_end = entry["end_pdf"]
        ch_title = entry["chapter_title"] or "Unavailable"
        s_title = entry["section_title"] or "Unavailable"
        for p_num in range(s_start, min(s_end + 1, total_pages + 1)):
            page_metadata[p_num - 1]["chapter_heading"] = ch_title
            page_metadata[p_num - 1]["section_heading"] = s_title

    # Front matter (before ch 1) and back matter (after ch 16) remain Unavailable
    first_p = entries[0]["start_pdf"] if entries else 15
    for p_idx in range(first_p - 1):
        page_metadata[p_idx]["chapter_heading"] = "Unavailable"
        page_metadata[p_idx]["section_heading"] = "Unavailable"
        page_metadata[p_idx]["printed_page"] = "Unavailable"
        
    last_p = entries[-1]["end_pdf"] if entries else 904
    for p_idx in range(last_p, total_pages):
        page_metadata[p_idx]["chapter_heading"] = "Unavailable"
        page_metadata[p_idx]["section_heading"] = "Unavailable"
        page_metadata[p_idx]["printed_page"] = "Unavailable"

    return page_metadata

print("Ready to integrate.")
