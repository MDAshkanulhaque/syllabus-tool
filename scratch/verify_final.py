import sys
sys.path.append("backend")
from qa_engine import AcademicSyllabusQAEngine

sample_text = """
--- PAGE 1 ---
SEMESTER I
1. 17EGHS01 TECHNICAL ENGLISH ENGLISH FC (HSS)
UNIT I : Subject and Verb Agreement (concord) - Preposition and Relative Pronoun
2. 17MABS01 ENGINEERING MATHEMATICS MATHEMATICS FC (BS)
Unit 1: To familiar with numerical solution of equations
3. 17MECC02 ENGINEERING THERMODYNAMICS MECH CC
4. 17ATCC10 AUTOMOTIVE POLLUTION CONTROL AUTO EC - PS
5. 17ATEC12 FUEL CELL TECHNOLOGY AUTO EC - OE
6. 17MEPI01 PROJECT WORK MECHANICAL PI
7. ENGINEERING MATHEMATICS
8. ENVIRONMENTAL SCIENCE AND ENGINEERING

--- PAGE 2 ---
SEMESTER II
9. ENGINEERING MECHANICS
Unit 1: To understand basic mechanical forces acting on rigid and deformable bodies.
10. MANUFACTURING ENGINEERING
PRINCIPLES OF TOTAL QUALITY MANAGEMENT
11. MANUFACURING ENGINEERING
12. To enable students to develop LSRW skills in English
13. To impart and enhance corporate communication
14. BUSINESS ENGLISH
15. PHYSICAL SCIENCES
16. SMART MATERIALS
"""

engine = AcademicSyllabusQAEngine(sample_text, "syllabus.pdf")

print("=== SEMESTER 1 QUERY ===")
res1 = engine.answer_question("first sem ka syllabus")
print(res1["answer"])

print("\n=== FIRST YEAR QUERY ===")
res2 = engine.answer_question("first year ka syllabus")
print(res2["answer"])

print("\n=== FIRST SEM COUNT QUERY ===")
res3 = engine.answer_question("first sem me kitne subject hain")
print(res3["answer"])

print("\n=== FIRST YEAR COUNT QUERY ===")
res4 = engine.answer_question("first year me total kitne subject hain")
print(res4["answer"])
