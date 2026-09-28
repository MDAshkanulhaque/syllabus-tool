import os
import sys
import fitz
import re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from syllabus_extractor import COURSE_CODE_PATTERNS, INVALID_CODES

def is_page_overview_table(text: str) -> bool:
    if not text:
        return False
    # Count unique course codes on the page
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
files = ["ssn.pdf", "avit syllabus.pdf", "ST.JOSEPH'S College of engineering SYLLABUS.pdf", "HINDUSTAN INSTITUTE OF TECHNOLOGY  SYLLABUS PDF.pdf"]

for fname in files:
    fpath = os.path.join(uploads_dir, fname)
    if not os.path.exists(fpath):
        continue
    doc = fitz.open(fpath)
    print(f"\n==========================================")
    print(f"TESTING OVERVIEW FIX ON: {fname} (Total Pages: {len(doc)})")
    print(f"==========================================")
    
    overview_pages = []
    detailed_pages = []
    
    for pno in range(1, len(doc) + 1):
        txt = doc[pno - 1].get_text()
        if is_page_overview_table(txt):
            overview_pages.append(pno)
        else:
            if re.search(r"\bUNIT\s*(?:I|1)\b", txt, re.I) or re.search(r"\bOBJECTIVES\b", txt, re.I) or re.search(r"\bCOURSE OUTCOMES\b", txt, re.I) or re.search(r"\bLIST OF EXPERIMENTS\b", txt, re.I):
                detailed_pages.append(pno)
                
    print(f"Overview Pages detected ({len(overview_pages)}): {overview_pages[:15]}")
    print(f"Detailed Pages detected ({len(detailed_pages)}): {detailed_pages[:15]}")
    doc.close()
