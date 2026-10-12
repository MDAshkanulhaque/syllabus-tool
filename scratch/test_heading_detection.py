import pymupdf
import re
from pathlib import Path

def extract_headings_for_book(doc, book_name):
    total_pages = len(doc)
    page_metadata = [{} for _ in range(total_pages)]
    
    # Check TOC first
    toc = doc.get_toc()
    # Check if TOC has detailed chapters/sections (e.g. Kreyszig)
    chapters_in_toc = [item for item in toc if item[0] == 2 and "chapter" in item[1].lower()]
    sections_in_toc = [item for item in toc if item[0] == 3 and re.match(r"^\d+\.\d+", item[1].strip())]
    
    if len(chapters_in_toc) >= 5:
        print(f"[{book_name}] Using PDF outline TOC ({len(chapters_in_toc)} chapters, {len(sections_in_toc)} sections)")
        # Build chapter ranges
        # Sort by start page
        chapters_sorted = sorted(chapters_in_toc, key=lambda x: x[2])
        sections_sorted = sorted(sections_in_toc, key=lambda x: x[2])
        
        for p_idx in range(total_pages):
            p_num = p_idx + 1
            # Find chapter
            ch_title = "Unavailable"
            for i, ch in enumerate(chapters_sorted):
                start = ch[2]
                end = chapters_sorted[i+1][2] if i + 1 < len(chapters_sorted) else total_pages + 1
                if start <= p_num < end:
                    ch_title = ch[1].strip()
                    break
                    
            # Find section
            sec_title = "Unavailable"
            for i, sec in enumerate(sections_sorted):
                start = sec[2]
                end = sections_sorted[i+1][2] if i + 1 < len(sections_sorted) else total_pages + 1
                if start <= p_num < end:
                    # Only accept section if it belongs to the same chapter or is reasonable
                    # Check chapter prefix e.g. "7.1" matches "Chapter 7"
                    sec_match = re.match(r"^(\d+)\.", sec[1].strip())
                    ch_match = re.search(r"Chapter\s+(\d+)", ch_title, re.IGNORECASE)
                    if sec_match and ch_match and sec_match.group(1) != ch_match.group(1):
                        sec_title = "Unavailable"
                    else:
                        sec_title = sec[1].strip()
                    break
            
            # If page is before chapter 1 or after chapters
            if p_num < chapters_sorted[0][2]:
                ch_title = "Unavailable"
                sec_title = "Unavailable"
                
            page_metadata[p_idx] = {
                "chapter_heading": ch_title,
                "section_heading": sec_title
            }
    else:
        print(f"[{book_name}] Detecting chapters and sections from text...")
        # Step 1: Detect Chapter start pages
        chapters = []
        for p_idx in range(total_pages):
            p_num = p_idx + 1
            text = doc[p_idx].get_text("text")
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            for idx, line in enumerate(lines[:6]):
                # Match e.g. "C H A P T E R 3" or "C H A P T E R3" or "CHAPTER 3"
                m = re.match(r"^C\s*H\s*A\s*P\s*T\s*E\s*R\s*(\d+)$", line, re.IGNORECASE)
                if m:
                    ch_num = int(m.group(1))
                    # Grab chapter title from subsequent 1-3 lines
                    title_parts = []
                    for next_line in lines[idx+1:idx+4]:
                        if any(w in next_line.lower() for w in ["chapter objectives", "introduction", "unit", "contents"]):
                            break
                        title_parts.append(next_line)
                    title = " ".join(title_parts).strip()
                    full_ch_title = f"Chapter {ch_num}: {title.title()}" if title else f"Chapter {ch_num}"
                    chapters.append((p_num, ch_num, full_ch_title))
                    break
                    
        print(f"  Found {len(chapters)} chapters in text")
        
        # Step 2: For each chapter, detect sections within its page range
        for c_idx, (ch_start, ch_num, ch_title) in enumerate(chapters):
            ch_end = chapters[c_idx + 1][0] if c_idx + 1 < len(chapters) else total_pages + 1
            
            # Find sections in [ch_start, ch_end)
            sections = []
            for p_num in range(ch_start, ch_end):
                text = doc[p_num - 1].get_text("text")
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                for line in lines:
                    # Match e.g. "3.2 Introduction to Matrices"
                    m = re.match(rf"^({ch_num}\.\d{{1,2}})\s+([A-Z][a-zA-Z0-9\s\-\,\(\)\/\–\—\:\.]{{2,80}})$", line)
                    if m:
                        sec_num = m.group(1)
                        sec_title = m.group(2).strip()
                        if not any(bad in sec_title for bad in ["=", "+", "dx", "dt", "Table", "Fig", "Example"]):
                            # avoid duplicates
                            if not any(s[1] == sec_num for s in sections):
                                sections.append((p_num, sec_num, f"{sec_num} {sec_title}"))
            
            # Assign chapters and sections to pages in this chapter
            for p_num in range(ch_start, ch_end):
                p_idx = p_num - 1
                sec_assigned = "Unavailable"
                for s_idx, (s_start, s_num, s_title) in enumerate(sections):
                    s_end = sections[s_idx + 1][0] if s_idx + 1 < len(sections) else ch_end
                    if s_start <= p_num < s_end:
                        sec_assigned = s_title
                        break
                page_metadata[p_idx] = {
                    "chapter_heading": ch_title,
                    "section_heading": sec_assigned
                }
                
        # Pages before first chapter or after last chapter
        first_ch_start = chapters[0][0] if chapters else total_pages + 1
        last_ch_start = chapters[-1][0] if chapters else 0
        # If last chapter ends at back matter (e.g. 930 for Grewal)
        for p_idx in range(first_ch_start - 1):
            page_metadata[p_idx] = {
                "chapter_heading": "Unavailable",
                "section_heading": "Unavailable"
            }
        for p_idx in range(930, total_pages):
            page_metadata[p_idx] = {
                "chapter_heading": "Unavailable",
                "section_heading": "Unavailable"
            }
            
    return page_metadata

# Test on both books
grewal_path = Path("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")
doc_g = pymupdf.open(grewal_path)
meta_g = extract_headings_for_book(doc_g, "Grewal")

print("\n--- Grewal Samples ---")
for p in [5, 14, 15, 16, 107, 114, 115, 118, 169, 170, 893, 940]:
    print(f"p.{p}: Ch='{meta_g[p-1]['chapter_heading']}' | Sec='{meta_g[p-1]['section_heading']}'")

kreyszig_path = Path("backend/books/advanced-engineering-mathematics_by-erwin-kreyszig-__10th_edition-1.pdf")
doc_k = pymupdf.open(kreyszig_path)
meta_k = extract_headings_for_book(doc_k, "Kreyszig")

print("\n--- Kreyszig Samples ---")
for p in [1, 20, 27, 28, 282, 283, 284, 289, 349, 905, 1200]:
    print(f"p.{p}: Ch='{meta_k[p-1]['chapter_heading']}' | Sec='{meta_k[p-1]['section_heading']}'")
