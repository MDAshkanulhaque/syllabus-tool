import os
import sys
import fitz
import re

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from syllabus_extractor import find_matching_course_record, extract_course_details, build_canonical_course_records
from subject_detector import remove_serial_number, clean_title_formatting

uploads_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "uploads")
files = [
    "PANIMALAR ENGINEERING COLLAGE -CSE-Curriculum & Syllabus Batch 2024-2025.pdf",
    "ST.JOSEPH'S College of engineering SYLLABUS.pdf",
    "ssn.pdf",
    "avit syllabus.pdf",
    "COIMBATORE INSTITUTE OF TECHNOLOGY, COIMBATORE_B_E_CSE_2023_Syllabus_(I_to_VIII).pdf"
]

test_queries = {
    "PANIMALAR ENGINEERING COLLAGE -CSE-Curriculum & Syllabus Batch 2024-2025.pdf": [
        "Matrices and Calculus", "Programming in C", "Engineering Physics", "Communicative English"
    ],
    "ST.JOSEPH'S College of engineering SYLLABUS.pdf": [
        "Communicative English", "Engineering Mathematics - I", "Engineering Physics", "Engineering Chemistry"
    ],
    "ssn.pdf": [
        "Communicative English", "Algebra and Calculus", "Engineering Physics", "Engineering Chemistry"
    ],
    "avit syllabus.pdf": [
        "Technical English", "Business English", "Total Quality Management", "Engineering Startups"
    ],
    "COIMBATORE INSTITUTE OF TECHNOLOGY, COIMBATORE_B_E_CSE_2023_Syllabus_(I_to_VIII).pdf": [
        "Technical English", "Matrices and Vector Calculus", "Applied Physics", "Applied Chemistry"
    ]
}

for fname in files:
    fpath = os.path.join(uploads_dir, fname)
    if not os.path.exists(fpath):
        continue
    print(f"\n==========================================")
    print(f"TESTING MATCHING ON: {fname}")
    print(f"==========================================")
    
    queries = test_queries.get(fname, [])
    for q in queries:
        rec = find_matching_course_record(fpath, q)
        if rec:
            code = rec["code"]
            dtls = extract_course_details(fpath, code)
            u_cnt = len(dtls.get("units", []))
            e_cnt = len(dtls.get("experiments", []))
            print(f"  [QUERY]: '{q}' => Code: '{code}', Title: '{rec['title']}', Pages: {rec['start_page']}-{rec['end_page']} | Units: {u_cnt}, Exps: {e_cnt}")
        else:
            print(f"  [QUERY]: '{q}' => ❌ NO MATCH FOUND")
