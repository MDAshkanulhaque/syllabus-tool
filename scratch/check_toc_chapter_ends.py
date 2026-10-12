import fitz
import re

with open("scratch/toc_full_text.txt", "r", encoding="utf-8") as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]

print("--- Check end of each chapter in TOC ---")

i = 0
current_ch = None
while i < len(lines):
    l = lines[i]
    m_ch = re.match(r"^Chapter\s+(\d+)\s*(.*)$", l, re.IGNORECASE)
    if m_ch:
        current_ch = int(m_ch.group(1))
        # print previous lines before this chapter
        if i > 5:
            print(f"\nBefore Chapter {current_ch}:")
            for j in range(max(0, i - 6), i):
                print(f"  {lines[j]}")
    i += 1

# Also check end of Chapter 16 (end of book)
print(f"\nEnd of TOC (Chapter 16):")
for j in range(len(lines) - 8, len(lines)):
    print(f"  {lines[j]}")
