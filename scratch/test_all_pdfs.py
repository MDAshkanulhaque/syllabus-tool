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

for fname in sorted(files):
    fpath = os.path.join(uploads_dir, fname)
    print(f"\n==========================================")
    print(f"TESTING: {fname}")
    print(f"==========================================")
    try:
        doc = fitz.open(fpath)
        pages_dict = {}
        full_text = ""
        for i, page in enumerate(doc):
            pno = i + 1
            txt = page.get_text("text")
            pages_dict[pno] = txt
            full_text += f"\n\n--- PAGE {pno} ---\n\n" + txt
        doc.close()
        
        candidates = extract_subject_candidates(full_text)
        print(f"Total Candidates Extracted from Overview/Headers: {len(candidates)}")
        for c in candidates[:5]:
            print(f"  - Candidate: '{c}'")
        if len(candidates) > 5:
            print(f"  ... and {len(candidates)-5} more candidates")
            
        records = build_canonical_course_records(pages_dict)
        print(f"Total Canonical Course Records Built: {len(records)}")
        for k, v in list(records.items())[:5]:
            code = v.get('code', '')
            name = v.get('name', '')
            units = len(v.get('unit_blocks', []))
            exps = len(v.get('experiments', []))
            start_p = v.get('start_page')
            end_p = v.get('end_page')
            print(f"  - Record Key: '{k}' | Code: '{code}' | Name: '{name}' | Pages: {start_p}-{end_p} | Units: {units} | Exps: {exps}")
            
        qa = AcademicSyllabusQAEngine(full_text=full_text, filename=fname, subjects=candidates, file_path=fpath)
        
        # Test sample queries
        print("\n--- Testing QA Queries ---")
        test_queries = []
        if candidates:
            test_queries.append(candidates[0])
            if len(candidates) > 1:
                test_queries.append(candidates[1])
        else:
            test_queries.append("Syllabus")
            
        for q in test_queries:
            ans = qa.answer_query(q)
            print(f"\n[QUERY]: '{q}'")
            lines = ans.splitlines()
            head_lines = "\n".join(lines[:8])
            print(f"[ANSWER PREVIEW]:\n{head_lines}\n--- (Length: {len(ans)} chars) ---")

    except Exception as e:
        print(f"ERROR processing {fname}: {e}")
        import traceback
        traceback.print_exc()
