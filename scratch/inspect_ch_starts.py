import re

with open("scratch/toc_full_text.txt", "r", encoding="utf-8") as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]

chapters = []
i = 0
while i < len(lines):
    l = lines[i]
    m_ch = re.match(r"^Chapter\s+(\d+)\s*(.*)$", l, re.IGNORECASE)
    if m_ch:
        ch_num = int(m_ch.group(1))
        ch_title = m_ch.group(2).strip()
        i += 1
        while i < len(lines) and not lines[i].isdigit() and not re.match(r"^\d+\.\d+", lines[i]) and not re.match(r"^Chapter", lines[i], re.IGNORECASE):
            ch_title += " " + lines[i]
            i += 1
        ch_pr = None
        if i < len(lines) and lines[i].isdigit():
            ch_pr = int(lines[i])
            i += 1
        ch_title = re.sub(r"\s+", " ", ch_title)
        chapters.append((ch_num, ch_title, ch_pr, ch_pr + 14 if ch_pr else None))
        continue
    i += 1

print("--- CHAPTER START PAGES IN TOC ---")
for c_num, c_title, pr, pdf in chapters:
    print(f"Chapter {c_num:2d}: '{c_title}' -> Printed p.{pr:3d} (PDF p.{pdf:3d})")
