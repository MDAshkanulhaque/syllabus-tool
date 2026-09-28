import sys
import os
import fitz

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('backend')
from syllabus_extractor import extract_course_details

test_courses = [
    ('PANIMALAR ENGINEERING COLLAGE -CSE-Curriculum & Syllabus Batch 2024-2025.pdf', '23CS1301'),
    ('PANIMALAR ENGINEERING COLLAGE -CSE-Curriculum & Syllabus Batch 2024-2025.pdf', '23CS1302'),
    ('ST.JOSEPH\'S College of engineering SYLLABUS.pdf', 'MA1301'),
    ('COIMBATORE INSTITUTE OF TECHNOLOGY, COIMBATORE_B_E_CSE_2023_Syllabus_(I_to_VIII).pdf', '23FYM11'),
    ('avit syllabus.pdf', '17MABS01')
]

uploads = os.path.join('backend', 'uploads')
for filename, code in test_courses:
    p = os.path.join(uploads, filename)
    if not os.path.exists(p):
        continue
    print('==================================================')
    print('FILE:', filename, '| CODE:', code)
    details = extract_course_details(p, code)
    print(f"COURSE: {details['course']['code']} - {details['course']['title']}")
    for u in details.get('units', []):
        print(f"\n  Unit {u['number']}: title=\"{u['title']}\" (Hours: {u['hours']})")
        for top in u.get('topics', [])[:3]:
            print(f"    - [{top['id']}] {top['text']}")
    print('\n  BOOKS:')
    for b in details.get('books', []):
        print(f"    [{b['kind']}] Title: \"{b['title']}\" | Author: \"{b['author']}\" | Pub: \"{b['publisher']}\" | Ed: \"{b['edition']}\" | Year: {b['year']}")
