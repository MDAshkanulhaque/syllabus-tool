import sys
import os
import fitz

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('backend')
from syllabus_extractor import extract_course_details, build_canonical_course_records

files = [
    'avit syllabus.pdf',
    'PANIMALAR ENGINEERING COLLAGE -CSE-Curriculum & Syllabus Batch 2024-2025.pdf',
    'ST.JOSEPH\'S College of engineering SYLLABUS.pdf',
    'Jeppair-R2024-Curriculum-and-Syllabus-CSBS.pdf'
]

for f in files:
    p = os.path.join('backend', 'uploads', f)
    if not os.path.exists(p):
        continue
    records = build_canonical_course_records(p)
    print('==================================================')
    print('FILE:', f)
    theory_records = [r for r in records if 'LAB' not in r['title'] and 'PRACTICAL' not in r['title']][:2]
    for r in theory_records:
        details = extract_course_details(p, r['code'])
        print(f"\nCOURSE: {details['course']['code']} - {details['course']['title']}")
        for u in details.get('units', []):
            first_t = u['topics'][0]['text'] if u.get('topics') else ''
            print(f"  Unit {u['number']}: title=\"{u['title']}\", first_topic=\"{first_t}\"")
        print('  BOOKS:')
        for b in details.get('books', []):
            print(f"    [{b['kind']}] Title=\"{b['title']}\" | Author=\"{b['author']}\" | Pub=\"{b['publisher']}\" | Year={b['year']}")
