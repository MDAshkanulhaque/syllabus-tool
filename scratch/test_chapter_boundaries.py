import re
import fitz

doc = fitz.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

with open("scratch/toc_full_text.txt", "r", encoding="utf-8") as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]

entries = []
chapter_starts = {}
chapter_titles = {}
exercises_starts = {} # ch_num -> [(ex_title, pdf_page)]

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
        ch_printed = None
        if i < len(lines) and lines[i].isdigit():
            ch_printed = int(lines[i])
            i += 1
        current_ch_title = f"Chapter {current_ch_num}: {raw_title}".strip()
        current_ch_title = re.sub(r"\s+", " ", current_ch_title)
        chapter_titles[current_ch_num] = current_ch_title
        if ch_printed:
            chapter_starts[current_ch_num] = ch_printed + 14
        continue

    if line.startswith("Exercises"):
        ex_title = line
        i += 1
        ex_printed = None
        if i < len(lines) and lines[i].isdigit():
            ex_printed = int(lines[i])
            i += 1
        if current_ch_num and ex_printed:
            if current_ch_num not in exercises_starts:
                exercises_starts[current_ch_num] = []
            exercises_starts[current_ch_num].append((ex_title, ex_printed + 14))
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
            # Last section in this chapter!
            # Check if chapter has end-of-chapter exercises (like Exercises 14.1, 15.1, 16.1)
            ch_exs = exercises_starts.get(c_num, [])
            # Find any exercises that start AFTER this section's start_pdf
            post_sec_exs = [ex for ex in ch_exs if ex[1] > entry["start_pdf"]]
            if post_sec_exs:
                first_post_ex = post_sec_exs[0]
                entry["end_pdf"] = first_post_ex[1] - 1
            else:
                next_c_num = next_entry["chapter_num"]
                next_c_start = chapter_starts.get(next_c_num, 905)
                entry["end_pdf"] = max(entry["start_pdf"], next_c_start - 1)
    else:
        # Last section in book (16.30)
        ch_exs = exercises_starts.get(c_num, [])
        post_sec_exs = [ex for ex in ch_exs if ex[1] > entry["start_pdf"]]
        if post_sec_exs:
            entry["end_pdf"] = post_sec_exs[0][1] - 1
        else:
            entry["end_pdf"] = 900

print("\n--- CHAPTER STARTS ---")
for c, p in sorted(chapter_starts.items()):
    print(f"Chapter {c:2d} starts on PDF p.{p}")

print("\n--- LAST SECTIONS ENDS ---")
for c in range(1, 17):
    c_entries = [e for e in entries if e["chapter_num"] == c]
    last_e = c_entries[-1]
    print(f"Chapter {c:2d}: {last_e['section_num']} '{last_e['section_title'][:30]}' -> PDF {last_e['start_pdf']}–{last_e['end_pdf']}")
