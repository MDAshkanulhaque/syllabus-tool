import sys
import os
import fitz

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('backend')
from qa_engine import AcademicSyllabusQAEngine

uploads = os.path.join('backend', 'uploads')

pdf_a = 'PANIMALAR ENGINEERING COLLAGE -CSE-Curriculum & Syllabus Batch 2024-2025.pdf'
pdf_b = 'rit.pdf'
pdf_c = 'ST.JOSEPH\'S College of engineering SYLLABUS.pdf'

# STEP 1: Upload PDF A
p_a = os.path.join(uploads, pdf_a)
doc_a = fitz.open(p_a)
txt_a = ''
for i, page in enumerate(doc_a, start=1):
    txt_a += f'\n--- PAGE {i} ---\n' + page.get_text()
doc_a.close()

engine = AcademicSyllabusQAEngine(txt_a, pdf_a, file_path=p_a)
q1 = 'Database Management Systems Laboratory ka syllabus bhejo'
res1 = engine.answer_question(q1)

print('==================================================')
print('TEST 1: PDF A (PANIMALAR) -> Query: DBMS Lab')
print(res1['answer'][:400])

# STEP 2: Swap Session to PDF B
p_b = os.path.join(uploads, pdf_b)
doc_b = fitz.open(p_b)
txt_b = ''
for i, page in enumerate(doc_b, start=1):
    txt_b += f'\n--- PAGE {i} ---\n' + page.get_text()
doc_b.close()

engine = AcademicSyllabusQAEngine(txt_b, pdf_b, file_path=p_b)
res2 = engine.answer_question(q1)

print('==================================================')
print('TEST 2: PDF B (RIT) -> Same Query: DBMS Lab')
print(res2['answer'][:400])

# STEP 3: Swap Session to PDF C
p_c = os.path.join(uploads, pdf_c)
doc_c = fitz.open(p_c)
txt_c = ''
for i, page in enumerate(doc_c, start=1):
    txt_c += f'\n--- PAGE {i} ---\n' + page.get_text()
doc_c.close()

engine = AcademicSyllabusQAEngine(txt_c, pdf_c, file_path=p_c)
q3 = 'Python Programming Laboratory ka syllabus bhejo'
res3 = engine.answer_question(q3)

print('==================================================')
print('TEST 3: PDF C (ST. JOSEPH\'S) -> Query: Python Lab')
print(res3['answer'][:400])
