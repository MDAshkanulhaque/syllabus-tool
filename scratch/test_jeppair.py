import sys
import os
import fitz

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from qa_engine import AcademicSyllabusQAEngine
from syllabus_extractor import find_matching_course_record, extract_courses_from_pdf, extract_course_details

uploads_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "uploads")
pdf_path = os.path.join(uploads_dir, "Jeppair-R2024-Curriculum-and-Syllabus-CSBS.pdf")

print(f"\n--- Testing Step 8 Cases on PDF: {os.path.basename(pdf_path)} ---")

doc = fitz.open(pdf_path)
full_text = ""
for page_num, page in enumerate(doc, start=1):
    full_text += f"\n\n--- PAGE {page_num} ---\n\n" + page.get_text()
doc.close()

engine = AcademicSyllabusQAEngine(full_text=full_text, filename=os.path.basename(pdf_path))

test_cases = [
    ("TEST 1", "dbms"),
    ("TEST 2", "dbms ka syllabus bhejo"),
    ("TEST 3", "ACS108"),
    ("TEST 4", "acb509"),
    ("TEST 5", "DATABASE MANAGEMENT SYSTEMS LABORATORY"),
    ("TEST 6", "ACS306")
]

for label, q in test_cases:
    print(f"\n[{label}] Query: '{q}'")
    res = engine.answer_question(q)
    print("  Found:", res.get("found"))
    ans = res.get("answer", "").encode('ascii', 'ignore').decode('ascii')
    lines = [l for l in ans.split("\n") if l.strip()]
    print("  Answer snippet:")
    for line in lines[:4]:
        print("    ", line)
    print("---------------------------------------------------------------")
