import os
import sys
import fitz

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from syllabus_extractor import build_canonical_course_records

files = [
    "COIMBATORE INSTITUTE OF TECHNOLOGY, COIMBATORE_B_E_CSE_2023_Syllabus_(I_to_VIII).pdf",
    "HINDUSTAN INSTITUTE OF TECHNOLOGY  SYLLABUS PDF.pdf",
    "ST.JOSEPH'S College of engineering SYLLABUS.pdf",
    "avit syllabus.pdf",
    "ssn.pdf"
]

uploads_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "uploads")

for fname in files:
    fpath = os.path.join(uploads_dir, fname)
    if not os.path.exists(fpath):
        continue
    print(f"\n==========================================")
    print(f"DEBUGGING: {fname}")
    print(f"==========================================")
    records = build_canonical_course_records(fpath)
    
    # Filter records to those where start_page == overview_page or start_page is in overview section (pages 1-15)
    detailed_records = [r for r in records if r["start_page"] > 10]
    overview_only = [r for r in records if r["start_page"] <= 10]
    
    print(f"Total Records: {len(records)}")
    print(f"  - Detailed Pages (start_page > 10): {len(detailed_records)}")
    print(f"  - Overview/Early Pages (start_page <= 10): {len(overview_only)}")
    
    print("\n  Sample Detailed Records:")
    for r in detailed_records[:5]:
        print(f"    - Code: '{r['code']}' | Title: '{r['title'][:35]}' | Pages: {r['start_page']}-{r['end_page']}")
        
    print("\n  Sample Overview-Only Records:")
    for r in overview_only[:5]:
        print(f"    - Code: '{r['code']}' | Title: '{r['title'][:35]}' | Pages: {r['start_page']}-{r['end_page']}")
