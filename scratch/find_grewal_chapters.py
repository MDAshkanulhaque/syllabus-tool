import pymupdf
import re

doc_g = pymupdf.open('backend/books/NUMERICAL METHODS IN ENGINEERING & SCIENCE B. S. GREWAL.pdf')

# Let's inspect:
# 1. How chapter starts look on the page in Grewal.
# 2. How running headers look on odd/even pages in Grewal.
# 3. How sections look on the page in Grewal.

for p_num in range(1, len(doc_g) + 1):
    text = doc_g[p_num - 1].get_text("text")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        continue
    # Check for chapter title page: usually starts with "C H A P T E R <num>" or "C H A P T E R<num>"
    for idx, line in enumerate(lines[:6]):
        m = re.match(r"^C\s*H\s*A\s*P\s*T\s*E\s*R\s*(\d+)$", line, re.IGNORECASE)
        if m:
            ch_num = m.group(1)
            # The next 1-3 lines are the chapter title
            title_parts = []
            for next_line in lines[idx+1:idx+4]:
                if "chapter objectives" in next_line.lower() or "introduction" in next_line.lower():
                    break
                title_parts.append(next_line)
            ch_title = " ".join(title_parts)
            print(f"Grewal PDF Page {p_num}: Chapter {ch_num} - {ch_title}")
