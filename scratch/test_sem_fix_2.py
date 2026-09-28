import sys
import re
from typing import Dict, List, Any, Optional

ROMAN_ARABIC_MAP = {
    "1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI", "7": "VII", "8": "VIII",
    "I": "1", "II": "2", "III": "3", "IV": "4", "V": "5", "VI": "6", "VII": "7", "VIII": "8"
}

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

pages = {
    1: sample_text.split("--- PAGE 2 ---")[0],
    2: "--- PAGE 2 ---" + sample_text.split("--- PAGE 2 ---")[1]
}

subjects = [
    "17EGHS01 TECHNICAL ENGLISH ENGLISH FC (HSS)",
    "17MABS01 ENGINEERING MATHEMATICS MATHEMATICS FC (BS)",
    "17MECC02 ENGINEERING THERMODYNAMICS MECH CC",
    "17ATCC10 AUTOMOTIVE POLLUTION CONTROL AUTO EC - PS",
    "17ATEC12 FUEL CELL TECHNOLOGY AUTO EC - OE",
    "17MEPI01 PROJECT WORK MECHANICAL PI",
    "ENGINEERING MATHEMATICS",
    "ENVIRONMENTAL SCIENCE AND ENGINEERING",
    "ENGINEERING MECHANICS",
    "MANUFACTURING ENGINEERING",
    "MANUFACURING ENGINEERING",
    "To enable students to develop LSRW skills in English",
    "To impart and enhance corporate communication",
    "BUSINESS ENGLISH",
    "PHYSICAL SCIENCES",
    "SMART MATERIALS"
]

def clean_subject_title(raw_subj: str) -> str:
    s = raw_subj
    s = re.sub(r"^\d+[\.\s]+", "", s)
    s = re.sub(r"^\s*[A-Z0-9]{6,10}\s+", "", s)
    s = re.sub(r"\s+\bL\s*T\s*P\s*C\b.*$", "", s, flags=re.I)
    s = re.sub(r"\s+\b\d\s+\d\s+\d\s+\d\b.*$", "", s)
    s = re.sub(r"\s+\b\d{1,2}\b\s*$", "", s)
    return s.strip(" -:,.")

def build_semester_map(pages, subjects):
    sem_map = {f"Semester {i}": [] for i in range(1, 9)}
    num_map = {
        "1":"1", "I":"1", "2":"2", "II":"2", "3":"3", "III":"3", "4":"4", "IV":"4",
        "5":"5", "V":"5", "6":"6", "VI":"6", "7":"7", "VII":"7", "8":"8", "VIII":"8"
    }
    word_sem_map = {
        "first": 1, "1st": 1, "second": 2, "2nd": 2,
        "third": 3, "3rd": 3, "fourth": 4, "4th": 4,
        "fifth": 5, "5th": 5, "sixth": 6, "6th": 6,
        "seventh": 7, "7th": 7, "eighth": 8, "8th": 8
    }

    sem_header_re = re.compile(
        r"\b(?:SEMESTER|SEM)\s*[-–:]?\s*([0-9]{1,2}|I{1,3}|IV|V|VI{0,3}|VII|VIII)\b|\b(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|1ST|2ND|3RD|4TH|5TH|6TH|7TH|8TH)\s*(?:SEM|SEMESTER)\b",
        re.I
    )

    def get_sem_from_text(text: str) -> Optional[int]:
        m = sem_header_re.search(text)
        if m:
            v1 = m.group(1)
            v2 = m.group(2)
            if v1:
                s_str = num_map.get(v1.upper(), v1)
                if s_str.isdigit() and 1 <= int(s_str) <= 8:
                    return int(s_str)
            if v2:
                val = word_sem_map.get(v2.lower())
                if val:
                    return val
        return None

    current_sem_num = 1
    for p_num in range(1, len(pages) + 1):
        p_text = pages.get(p_num, "")
        lines = [l.strip() for l in p_text.splitlines() if l.strip()]
        
        for line in lines:
            detected_sem = get_sem_from_text(line)
            if detected_sem and len(line.split()) <= 8 and not ("SEMESTER I TO" in line.upper() or "SEMESTER 1 TO" in line.upper()):
                current_sem_num = detected_sem
                continue

            clean_l = clean_subject_title(line)
            matched_subj = None
            for s in subjects:
                clean_s = clean_subject_title(s)
                if len(clean_s) >= 4 and (clean_s.lower() in line.lower() or clean_s.lower() == clean_l.lower()):
                    matched_subj = clean_s
                    break

            if matched_subj:
                target_key = f"Semester {current_sem_num}"
                if matched_subj not in sem_map[target_key]:
                    for other_key, other_list in sem_map.items():
                        if other_key != target_key and matched_subj in other_list:
                            other_list.remove(matched_subj)
                    sem_map[target_key].append(matched_subj)

    return sem_map

sem_map = build_semester_map(pages, subjects)
print("SEMESTER MAP:")
for k, v in sem_map.items():
    if v:
        print(f"{k} ({len(v)} subjects): {v}")
