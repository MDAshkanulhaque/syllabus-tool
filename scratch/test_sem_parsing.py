import sys
import re
from typing import Dict, List, Any, Optional

sys.path.append("backend")
from subject_detector import extract_subject_candidates, contains_course_code, remove_course_code, remove_serial_number, clean_title_formatting, is_header_or_garbage, is_category_line, ELECTIVE_SLOT_REGEX

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

print("Testing regex:")
print("SEMESTER I:", get_sem_from_text("SEMESTER I"))
print("SEMESTER - II:", get_sem_from_text("SEMESTER - II"))
print("3RD SEMESTER:", get_sem_from_text("3RD SEMESTER"))
print("Semester : 4:", get_sem_from_text("Semester : 4"))
print("SEM-5:", get_sem_from_text("SEM-5"))
