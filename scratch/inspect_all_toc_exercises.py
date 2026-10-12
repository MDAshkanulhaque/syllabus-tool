import re

with open("scratch/toc_full_text.txt", "r", encoding="utf-8") as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]

i = 0
current_ch = None
while i < len(lines):
    l = lines[i]
    m_ch = re.match(r"^Chapter\s+(\d+)\s*(.*)$", l, re.IGNORECASE)
    if m_ch:
        current_ch = int(m_ch.group(1))
        i += 1
        continue
    if l.startswith("Exercises"):
        ex_name = l
        i += 1
        pr = None
        if i < len(lines) and lines[i].isdigit():
            pr = int(lines[i])
            i += 1
        print(f"Chapter {current_ch:2d}: {ex_name} -> Printed p.{pr} (PDF {pr+14 if pr else '?'})")
        continue
    i += 1
