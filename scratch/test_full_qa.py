import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

sys.path.append("backend")
from qa_engine import AcademicSyllabusQAEngine

sample_text = """
--- PAGE 1 ---
SEMESTER I
1. 17EGHS01 TECHNICAL ENGLISH ENGLISH FC (HSS)
UNIT I : Subject and Verb Agreement (concord) - Preposition and Relative Pronoun
UNIT II : Stress (Word Stress and Sentence Stress) Intonation

2. 17MABS01 ENGINEERING MATHEMATICS MATHEMATICS FC (BS)
Unit 1: To familiar with numerical solution of equations
Unit 2: To be get exposed to finite differences and interpolation

--- PAGE 2 ---
SEMESTER II
3. ENGINEERING MECHANICS
Unit 1: Basic mechanical forces acting on rigid and deformable bodies

4. BUSINESS ENGLISH
Unit 1: Reading skills and inferences
Unit 2: Corporate communication and recommendations
"""

engine = AcademicSyllabusQAEngine(sample_text, "test.pdf")

print("=== SEMESTER 1 QUERY ===")
r1 = engine.answer_question("First semester ka syllabus bhejo")
print(r1["answer"])

print("\n=== SEMESTER 2 QUERY ===")
r2 = engine.answer_question("Second semester ka syllabus bhejo")
print(r2["answer"])

print("\n=== FIRST YEAR QUERY ===")
r3 = engine.answer_question("First year ka syllabus bhejo")
print(r3["answer"])

print("\n=== SPECIFIC SUBJECT QUERY (BUSINESS ENGLISH) ===")
r4 = engine.answer_question("BUSINESS ENGLISH ka syllabus bhejo")
print(r4["answer"])
