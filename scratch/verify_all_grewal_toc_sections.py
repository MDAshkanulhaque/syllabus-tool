import fitz
import re

doc = fitz.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

# Extract TOC from pages 5 to 14
toc_lines = []
for p in range(4, 14):
    for l in doc[p].get_text("text").splitlines():
        l = l.strip()
        if l:
            toc_lines.append(l)

entries = []
current_ch_num = None
current_ch_title = None

i = 0
while i < len(toc_lines):
    line = toc_lines[i]
    m_ch = re.match(r"^Chapter\s+(\d+)\s*(.*)$", line, re.IGNORECASE)
    if m_ch:
        current_ch_num = int(m_ch.group(1))
        raw_title = m_ch.group(2).strip()
        i += 1
        while i < len(toc_lines) and not toc_lines[i].isdigit() and not re.match(r"^\d+\.\d+", toc_lines[i]) and not re.match(r"^Chapter", toc_lines[i], re.IGNORECASE):
            raw_title += " " + toc_lines[i]
            i += 1
        if i < len(toc_lines) and toc_lines[i].isdigit():
            i += 1
        current_ch_title = f"Chapter {current_ch_num}: {raw_title}".strip()
        current_ch_title = re.sub(r"\s+", " ", current_ch_title)
        continue

    m_sec = re.match(r"^(\d+\.\d{1,2})\s*(.*)$", line)
    if m_sec:
        sec_num = m_sec.group(1)
        raw_sec_title = m_sec.group(2).strip()
        i += 1
        while i < len(toc_lines) and not toc_lines[i].isdigit() and not re.match(r"^\d+\.\d+", toc_lines[i]) and not re.match(r"^Chapter", toc_lines[i], re.IGNORECASE) and not toc_lines[i].startswith("Exercises"):
            raw_sec_title += " " + toc_lines[i]
            i += 1
        sec_printed = None
        if i < len(toc_lines) and toc_lines[i].isdigit():
            sec_printed = int(toc_lines[i])
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

print(f"Total parsed TOC entries: {len(entries)}")

# Verify each entry against actual PDF text
verified = []
for entry in entries:
    s_num = entry["section_num"]
    s_title = entry["section_title"]
    nom_pdf = entry["start_pdf"]
    nom_pr = entry["printed_page"]
    
    # Check if section number is found on nominal PDF page
    text_nom = doc[nom_pdf - 1].get_text("text")
    found_on = None
    if re.search(rf"\b{re.escape(s_num)}\b", text_nom):
        found_on = nom_pdf
    else:
        # Check adjacent pages
        for p_cand in [nom_pdf + 1, nom_pdf - 1]:
            if 1 <= p_cand <= len(doc):
                text_cand = doc[p_cand - 1].get_text("text")
                if re.search(rf"\b{re.escape(s_num)}\b", text_cand):
                    found_on = p_cand
                    break
    
    verified.append({
        **entry,
        "actual_start_pdf": found_on or nom_pdf,
        "shift": (found_on - nom_pdf) if found_on else 0
    })

shifts = [v for v in verified if v["shift"] != 0]
print(f"Entries with page shift from TOC: {len(shifts)}")
for s in shifts:
    print(f"Sec {s['section_num']}: TOC pr={s['printed_page']} (PDF {s['start_pdf']}) -> Actual PDF {s['actual_start_pdf']} (shift: {s['shift']})")
