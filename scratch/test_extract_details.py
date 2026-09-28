import os
import sys
import fitz

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from syllabus_extractor import extract_course_details, build_canonical_course_records
from subject_detector import extract_subject_candidates

uploads_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "uploads")
files = [
    "BCI-2024-2025 VIT SYLLABUS.pdf",
    "COIMBATORE INSTITUTE OF TECHNOLOGY, COIMBATORE_B_E_CSE_2023_Syllabus_(I_to_VIII).pdf",
    "HINDUSTAN INSTITUTE OF TECHNOLOGY  SYLLABUS PDF.pdf",
    "PANIMALAR ENGINEERING COLLAGE -CSE-Curriculum & Syllabus Batch 2024-2025.pdf",
    "ST.JOSEPH'S College of engineering SYLLABUS.pdf",
    "avit syllabus.pdf",
    "ssn.pdf"
]

for fname in files:
    fpath = os.path.join(uploads_dir, fname)
    if not os.path.exists(fpath):
        continue
    print(f"\n==========================================")
    print(f"TESTING EXTRACT DETAILS ON: {fname}")
    print(f"==========================================")
    
    doc = fitz.open(fpath)
    full_text = ""
    for i, page in enumerate(doc):
        full_text += f"\n\n--- PAGE {i+1} ---\n\n" + page.get_text("text")
    doc.close()
    
    records = build_canonical_course_records(fpath)
    print(f"Canonical Records Found: {len(records)}")
    
    for r in records[:6]:
        code = r["code"]
        title = r["title"]
        start_p = r["start_page"]
        end_p = r["end_page"]
        details = extract_course_details(fpath, code)
        units_cnt = len(details.get("units", []))
        exps_cnt = len(details.get("experiments", []))
        print(f"  - Record Code: '{code}' | Title: '{title[:30]}' | Pages: {start_p}-{end_p} => Units: {units_cnt}, Exps: {exps_cnt}")
