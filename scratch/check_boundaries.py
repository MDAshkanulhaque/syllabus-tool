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

# Check start_pdf adjustments against actual text
for entry in entries:
    s_num = entry["section_num"]
    nominal_pdf = entry["start_pdf"]
    if not nominal_pdf or nominal_pdf > len(doc):
        continue
    p_text = doc[nominal_pdf - 1].get_text("text")
    if not re.search(rf"\b{re.escape(s_num)}\b", p_text):
        if nominal_pdf < len(doc):
            next_text = doc[nominal_pdf].get_text("text")
            if re.search(rf"\b{re.escape(s_num)}\b", next_text):
                entry["start_pdf"] = nominal_pdf + 1
                entry["printed_page"] = entry["printed_page"] + 1

# Map chapter starts
chapter_starts = {}
for entry in entries:
    c_num = entry["chapter_num"]
    if c_num not in chapter_starts:
        chapter_starts[c_num] = entry["start_pdf"]

# Determine end_pdf for each section
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
        entry["end_pdf"] = 904

print(f"Total entries: {len(entries)}")

# Verify every section
anomalies = []
for i, entry in enumerate(entries):
    if entry["start_pdf"] > entry["end_pdf"]:
        anomalies.append(f"Inverted range: {entry['section_num']} {entry['start_pdf']} > {entry['end_pdf']}")
    # Verify that start page contains the section number or title
    p_text = doc[entry["start_pdf"] - 1].get_text("text")
    if not re.search(rf"\b{re.escape(entry['section_num'])}\b", p_text):
        anomalies.append(f"Section {entry['section_num']} not found on page {entry['start_pdf']}")

print(f"Anomalies found: {len(anomalies)}")
for a in anomalies:
    print("  ", a)
