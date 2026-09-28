import sys
import os
import fitz

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from subject_detector import extract_subject_candidates
from syllabus_extractor import build_canonical_course_records
from qa_engine import AcademicSyllabusQAEngine

uploads_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "uploads")
files = [f for f in os.listdir(uploads_dir) if f.endswith(".pdf")]

with open("scratch/stats_summary.txt", "w", encoding="utf-8") as out:
    out.write(f"{'PDF FILENAME':<55} | {'CANDIDATES':<10} | {'CANONICAL RECORDS':<18}\n")
    out.write("-" * 90 + "\n")

    for fname in sorted(files):
        fpath = os.path.join(uploads_dir, fname)
        try:
            doc = fitz.open(fpath)
            full_text = ""
            for i, page in enumerate(doc):
                pno = i + 1
                txt = page.get_text("text")
                full_text += f"\n\n--- PAGE {pno} ---\n\n" + txt
            doc.close()
            
            candidates = extract_subject_candidates(full_text)
            records = build_canonical_course_records(fpath)
            
            out.write(f"{fname[:54]:<55} | {len(candidates):<10} | {len(records):<18}\n")
        except Exception as e:
            import traceback
            out.write(f"{fname[:54]:<55} | ERROR: {e}\n")
            out.write(traceback.format_exc() + "\n")

print("Wrote to scratch/stats_summary.txt")
