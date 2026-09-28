import os
import sys
import fitz

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from qa_engine import AcademicSyllabusQAEngine
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
    print(f"TESTING QA ON: {fname}")
    print(f"==========================================")
    doc = fitz.open(fpath)
    full_text = ""
    for i, page in enumerate(doc):
        full_text += f"\n\n--- PAGE {i+1} ---\n\n" + page.get_text("text")
    doc.close()
    
    candidates = extract_subject_candidates(full_text)
    qa = AcademicSyllabusQAEngine(full_text=full_text, filename=fname, subjects=candidates, file_path=fpath)
    
    # Pick 4 subject titles from candidates
    test_subjs = candidates[:4]
    for subj in test_subjs:
        print(f"\n---> User Question: '{subj}'")
        res_dict = qa.answer_question(subj)
        res = res_dict.get("answer", "")
        lines = [l for l in res.splitlines() if l.strip()]
        first_few = "\n".join(lines[:6])
        print(f"RESPONSE:\n{first_few}")
        if "Information not found" in res:
            print("❌ FAILURE: Returned 'Information not found'")
        else:
            print("✅ SUCCESS: Extracted detailed syllabus")
