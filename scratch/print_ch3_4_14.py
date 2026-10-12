import sys
sys.path.insert(0, ".")
from scratch.compute_grewal_ranges import verified_sections

for s in verified_sections:
    if s['chapter_num'] in [3, 4, 14]:
        cnt = s['end_pdf'] - s['start_pdf'] + 1
        print(f"[{s['chapter_heading'][:18]}] {s['section_heading']:45s} | PDF {s['start_pdf']:3d}–{s['end_pdf']:3d} ({cnt:2d} pgs | pr {s['start_printed']:3d}–{s['end_pdf']-14:3d})")
