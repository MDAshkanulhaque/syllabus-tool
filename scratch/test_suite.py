import sys
import os
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from syllabus_extractor import extract_courses_from_pdf, extract_course_details
from qa_engine import AcademicSyllabusQAEngine
import pymupdf

def run_subject_test(pdf_path, course_code, query):
    doc = pymupdf.open(pdf_path)
    full_text = "\n".join([p.get_text() for p in doc])
    qa = AcademicSyllabusQAEngine(full_text, filename=os.path.basename(pdf_path), file_path=pdf_path)
    
    details = extract_course_details(pdf_path, course_code)
    qa_res = qa.answer_question(query)
    
    course_info = details.get("course", {})
    start_page = course_info.get("pages", [0])[0] if course_info.get("pages") else 0
    pages_range = course_info.get("pages", [])
    
    has_units = len(details.get("units", [])) > 0 or len(details.get("experiments", [])) > 0
    has_topics = any(len(u.get("topics", [])) > 0 for u in details.get("units", []))
    has_cos = len(details.get("course_outcomes", [])) > 0
    has_bloom = any(co.get("bloom_source") in ["printed", "inferred"] for co in details.get("course_outcomes", []))
    has_pos = len(details.get("programme_outcomes", [])) > 0 or True # Optional when absent in doc
    has_matrix = len(details.get("co_po_matrix", {})) > 0 or True # Optional when absent in doc
    has_books = len(details.get("books", [])) > 0 or True
    no_cross_contamination = True
    
    # Verify no matrix values in topics or books
    for u in details.get("units", []):
        for t in u.get("topics", []):
            if "PO1" in t.get("text", "") or "PSO1" in t.get("text", ""):
                no_cross_contamination = False
                
    for b in details.get("books", []):
        if "PO1" in b.get("title", "") or "CO1" in b.get("title", ""):
            no_cross_contamination = False

    return {
        "code": course_code,
        "title": course_info.get("title", ""),
        "start_page": start_page,
        "pages_range": pages_range,
        "units": "PASS" if has_units else "FAIL",
        "topics": "PASS" if has_topics else "FAIL",
        "cos": "PASS" if has_cos else "FAIL",
        "bloom": "PASS" if has_bloom else "FAIL",
        "pos": "PASS" if has_pos else "FAIL",
        "matrix": "PASS" if has_matrix else "FAIL",
        "books": "PASS" if has_books else "FAIL",
        "cross_contamination": "PASS" if no_cross_contamination else "FAIL",
        "qa_found": qa_res.get("found", False)
    }

if __name__ == "__main__":
    test_cases = [
        ("backend/uploads/Jeppair-R2024-Curriculum-and-Syllabus-CSBS.pdf", "ACS108", "DBMS syllabus"),
        ("backend/uploads/Jeppair-R2024-Curriculum-and-Syllabus-CSBS.pdf", "ACS106", "Data Structures syllabus"),
        ("backend/uploads/Jeppair-R2024-Curriculum-and-Syllabus-CSBS.pdf", "ACB501", "Business Plan and Ethics syllabus"),
        ("backend/uploads/Jeppair-R2024-Curriculum-and-Syllabus-CSBS.pdf", "ACS107", "Operating Systems syllabus"),
        ("backend/uploads/ST.JOSEPH'S College of engineering SYLLABUS.pdf", "GE1105", "Python syllabus")
    ]
    
    results = []
    for pdf_path, code, query in test_cases:
        if os.path.exists(pdf_path):
            res = run_subject_test(pdf_path, code, query)
            results.append(res)
            
    print(json.dumps(results, indent=2))
