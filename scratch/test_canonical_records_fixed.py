import os
import sys
import fitz
import re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from syllabus_extractor import COURSE_CODE_PATTERNS, INVALID_CODES, normalize_text_key

def is_page_overview_table(text: str) -> bool:
    if not text:
        return False
    found_codes = set()
    for line in text.splitlines():
        for pat in COURSE_CODE_PATTERNS:
            for m in pat.finditer(line):
                code = m.group(0).replace(" ", "").upper()
                if code not in INVALID_CODES and len(code) >= 5 and not code.isdigit():
                    found_codes.add(code)
    if len(found_codes) >= 3:
        return True
    if re.search(r"\bSEMESTER\s+(?:I|II|III|IV|V|VI|VII|VIII|[1-8])\b", text, re.I) and ("CREDITS" in text.upper() or "L T P C" in text.upper() or "L  T  P  C" in text.upper()):
        return True
    return False

uploads_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "uploads")
files = [
    "ssn.pdf",
    "avit syllabus.pdf",
    "ST.JOSEPH'S College of engineering SYLLABUS.pdf",
    "HINDUSTAN INSTITUTE OF TECHNOLOGY  SYLLABUS PDF.pdf",
    "COIMBATORE INSTITUTE OF TECHNOLOGY, COIMBATORE_B_E_CSE_2023_Syllabus_(I_to_VIII).pdf",
    "PANIMALAR ENGINEERING COLLAGE -CSE-Curriculum & Syllabus Batch 2024-2025.pdf",
    "Jeppair-R2024-Curriculum-and-Syllabus-CSBS.pdf"
]

for fname in files:
    fpath = os.path.join(uploads_dir, fname)
    if not os.path.exists(fpath):
        continue
    doc = fitz.open(fpath)
    print(f"\n==========================================")
    print(f"CANONICAL RECORDS FOR: {fname}")
    print(f"==========================================")
    
    code_map = {}
    records = []
    
    course_header_regex = re.compile(
        r"(?:COURSE\s+CODE|CODE|SUBJECT\s+CODE)?\s*[:\s]*\b([A-Z]{2,6}\s*[-/]?\s*\d{3,5}[A-Z]?)\b\s*[:\-\|]?\s*(.+)",
        re.I
    )

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        is_table_overview_page = is_page_overview_table(text)

        is_detailed_page = not is_table_overview_page and (
            bool(re.search(r"\bUNIT\s*[\-\–\—\:]?\s*(I|1|ONE)\b", text, re.I)) or
            bool(re.search(r"\bMODULE\s*[\-\–\—\:]?\s*(I|1|ONE)\b", text, re.I)) or
            bool(re.search(r"\b(?:LIST OF EXPERIMENTS|LAB EXPERIMENTS|LABORATORY EXPERIMENTS|PRACTICAL EXPERIMENTS|EXPERIMENTS|PRACTICALS|LABORATORY EXERCISES|PRACTICAL EXERCISES|PRACTICAL CONTENT|LAB CONTENT)\b", text, re.I)) or
            bool(re.search(r"\bPREAMBLE\b", text, re.I)) or
            bool(re.search(r"\bCOURSE\s*(?:OBJECTIVES?|OUTCOMES?)\b", text, re.I)) or
            bool(re.search(r"\bSDGs\s+Mapped\b", text, re.I)) or
            bool(re.search(r"\bPractical Course\b", text, re.I))
        )

        for i, line in enumerate(lines):
            code = None
            title = None
            match = course_header_regex.search(line)
            if match:
                potential_code = match.group(1).replace(" ", "").upper()
                potential_title = match.group(2).strip()
                if potential_code not in INVALID_CODES and len(potential_code) >= 5:
                    code = potential_code
                    title = potential_title
            else:
                for pat in COURSE_CODE_PATTERNS:
                    c_match = pat.search(line)
                    if c_match:
                        potential_code = c_match.group(0).replace(" ", "").upper()
                        if potential_code not in INVALID_CODES and len(potential_code) >= 5:
                            code = potential_code
                            title_part = line.replace(c_match.group(0), "").strip(" :-|")
                            if not title_part and i + 1 < len(lines):
                                title_part = lines[i + 1].strip()
                            title = title_part
                            break

            if code:
                title_clean = re.sub(r"\s*(?:L\s*T\s*P\s*C|CREDITS|\d\s+\d\s+\d\s+\d).*$", "", title or "", flags=re.I).strip(" :-|")
                if not title_clean or len(title_clean) < 3:
                    if i + 1 < len(lines):
                        title_clean = lines[i + 1].strip()

                if code not in code_map:
                    rec = {
                        "code": code,
                        "title": title_clean.upper() if title_clean else code,
                        "overview_page": page_num + 1,
                        "start_page": page_num + 1 if is_detailed_page else None,
                        "end_page": len(doc)
                    }
                    code_map[code] = rec
                    records.append(rec)
                else:
                    rec = code_map[code]
                    if is_detailed_page and (rec["start_page"] is None or page_num + 1 > rec["overview_page"]):
                        rec["start_page"] = page_num + 1
                    if title_clean and len(title_clean) > len(rec["title"]):
                        rec["title"] = title_clean.upper()

    doc.close()

    detailed_recs = [r for r in records if r["start_page"] is not None]
    print(f"Total Unique Codes Extracted: {len(records)}")
    print(f"Records mapped to Detailed Pages: {len(detailed_recs)}")
    for r in detailed_recs[:6]:
        print(f"  - Code: '{r['code']}' | Title: '{r['title'][:35]}' | Overview Page: {r['overview_page']} | Detailed Start Page: {r['start_page']}")
