import fitz
import sys
import os

sys.path.append("backend")
from qa_engine import AcademicSyllabusQAEngine

pdf_path = "backend/uploads/RAJALAKSHMIINSTITUTEOF TECHNOLOGY BE-CSE-SYLLABUS-2023-27.pdf"
doc = fitz.open(pdf_path)
txt = ""
for i, p in enumerate(doc):
    txt += f"\n\n--- PAGE {i+1} ---\n\n" + p.get_text()

engine = AcademicSyllabusQAEngine(txt, "RAJALAKSHMI.pdf")

print("Mapped Semesters:")
for sem, subs in engine.semester_map.items():
    print(f"{sem}: {len(subs)} subjects")
    for s in subs:
        print("  -", s.encode('ascii', 'ignore').decode('ascii'))

print("=" * 50)
res = engine.answer_question("4th sem ka syllabus")
with open("scratch/rit_4th_sem_res.txt", "w", encoding="utf-8") as f:
    f.write(res["answer"])

print("Saved 4th sem answer to scratch/rit_4th_sem_res.txt")
