import re

with open("scratch/grewal_raw_toc.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Let's inspect the patterns in the TOC text
lines = [l.strip() for l in text.splitlines() if l.strip()]

chapters = []
sections = []

current_ch = None
for i, l in enumerate(lines):
    # Chapter match
    m_ch = re.match(r"^Chapter\s+(\d+)\s+(.+)$", l, re.IGNORECASE)
    if m_ch:
        ch_num = int(m_ch.group(1))
        ch_title = m_ch.group(2).strip()
        # sometimes page number is on next line or end of line
        current_ch = (ch_num, ch_title)
        chapters.append(current_ch)
        continue

print(f"Detected {len(chapters)} chapters in TOC text:")
for c in chapters:
    print(c)
