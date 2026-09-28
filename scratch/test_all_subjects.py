import sys, os, json
sys.path.insert(0, os.path.abspath('.'))

from backend.syllabus_extractor import extract_course_details

test_codes = ['AMA102', 'APH101', 'ACB509', 'ACS107', 'ACS108', 'ACS306']
pdf_path = 'backend/uploads/Jeppair-R2024-Curriculum-and-Syllabus-CSBS.pdf'

for code in test_codes:
    res = extract_course_details(pdf_path, code)
    c = res['course']
    print('=== COURSE:', c['code'], '-', c['title'], '===')
    print('  Pages:', c['pages'])
    print('  L-T-P-C:', f"{c['lecture']}-{c['tutorial']}-{c['practical']}-{c['credits']}", 'Total Hrs:', sum(u['hours'] for u in res['units']))
    print('  Units Count:', len(res['units']))
    for u in res['units']:
        print(f"    Unit {u['number']}: {u['title']} ({u['hours']} Hrs) -> {len(u['topics'])} topics")
        if u['topics']:
            print(f"      First topic: {u['topics'][0]['text'][:70]}")
    print('  COs Count:', len(res['course_outcomes']))
    print('  POs Count:', len(res['programme_outcomes']))
    print('  Books Count:', len(res['books']))
    for b in res['books'][:2]:
        print(f"    Book ({b['kind']}): {b['title']} by {b['author']}")
    print('-'*60)
