import sys
import os
import fitz

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from qa_engine import AcademicSyllabusQAEngine
from syllabus_extractor import find_matching_course_record, extract_courses_from_pdf, extract_course_details

# Find a sample PDF in backend/uploads
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "uploads")
pdf_files = [f for f in os.listdir(uploads_dir) if f.endswith(".pdf")]

print("Available sample PDFs:", pdf_files)

target_pdf = None
for f in pdf_files:
    if "rit" in f.lower() or "hindustan" in f.lower() or "coimbatore" in f.lower() or "panimalar" in f.lower():
        target_pdf = os.path.join(uploads_dir, f)
        break

if not target_pdf and pdf_files:
    target_pdf = os.path.join(uploads_dir, pdf_files[0])

print(f"\n--- Testing with PDF: {os.path.basename(target_pdf)} ---")

doc = fitz.open(target_pdf)
full_text = ""
for page_num, page in enumerate(doc, start=1):
    full_text += f"\n\n--- PAGE {page_num} ---\n\n" + page.get_text()
doc.close()

engine = AcademicSyllabusQAEngine(full_text=full_text, filename=os.path.basename(target_pdf))

test_queries = [
    "dbms",
    "dbms ka syllabus bhejo",
    "ACS108",
    "acb509",
    "DATABASE MANAGEMENT SYSTEMS LABORATORY",
    "ACS306"
]

print("\n================== RUNNING STEP 8 TEST CASES ==================")
for idx, q in enumerate(test_queries, 1):
    print(f"\n[TEST {idx}] Query: '{q}'")
    res = engine.answer_question(q)
    print("Found:", res.get("found"))
    print("Answer snippet:")
    lines = res.get("answer", "").split("\n")
    for line in lines[:6]:
        print("  ", line)
    print("---------------------------------------------------------------")
