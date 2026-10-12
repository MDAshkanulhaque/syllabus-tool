import fitz
import json

doc = fitz.open("backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf")

with open("scratch/toc_full_text.txt", "r", encoding="utf-8") as f:
    toc_lines = [l.strip() for l in f.readlines() if l.strip()]

from scratch.compare_grewal_toc_with_index import parsed_toc

# Group parsed_toc by chapter_num
ch_secs = {}
for s in parsed_toc:
    c = s["chapter_num"]
    if c not in ch_secs:
        ch_secs[c] = []
    ch_secs[c].append(s)

print("--- LAST SECTION OF EACH CHAPTER VS CHAPTER END ---")
for c in range(1, 17):
    secs = ch_secs[c]
    last_sec = secs[-1]
    nom_start = last_sec["pdf_page"]
    
    # check where next chapter begins in PDF
    # or check lines in TOC after this section
    print(f"\nChapter {c:2d}: Last section is {last_sec['section_num']} '{last_sec['section_title']}' (Nominal PDF {nom_start}, pr {last_sec['printed_page']})")
