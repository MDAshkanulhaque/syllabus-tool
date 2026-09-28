import re
import os
import sys
from typing import Dict, List, Any, Optional

# Add backend path to sys.path for extractor imports
sys.path.insert(0, os.path.dirname(__file__))

from subject_detector import (
    extract_subject_candidates,
    clean_line,
    clean_title_formatting,
    contains_course_code,
    extract_course_code,
    remove_course_code,
    remove_serial_number,
    is_header_or_garbage,
    is_category_line,
    is_credit_line,
    ELECTIVE_SLOT_REGEX
)
from syllabus_extractor import (
    find_matching_course_record,
    extract_course_details,
    build_canonical_course_records,
    normalize_text_key
)

ROMAN_ARABIC_MAP = {
    "1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI", "7": "VII", "8": "VIII",
    "I": "1", "II": "2", "III": "3", "IV": "4", "V": "5", "VI": "6", "VII": "7", "VIII": "8"
}

SUBJECT_ACRONYMS = {
    "dbms": "database management systems",
    "dsa": "data structures",
    "ds": "data structures",
    "oop": "object oriented programming",
    "oops": "object oriented programming",
    "java": "java",
    "os": "operating system",
    "cn": "computer network",
    "co": "computer organization",
    "coa": "computer organization",
    "toc": "theory of computation",
    "cd": "compiler design",
    "se": "software engineering",
    "ai": "artificial intelligence",
    "ml": "machine learning",
    "maths": "mathematics",
    "math": "mathematics",
    "discrete": "discrete mathematics",
    "python": "python programming",
    "cpp": "c++",
    "c": "programming in c",
    "tqm": "total quality management",
    "pehv": "professional ethics and human values",
    "ipr": "intellectual property rights",
    "em": "engineering mathematics",
    "ece": "electronics and communication",
    "eee": "electrical and electronics",
    "electrical": "electrical engineering",
    "electronics": "electronics engineering",
    "biomedical": "biomedical engineering",
    "law": "constitutional law",
    "phys": "physics",
    "physics": "physics",

    "chem": "chemistry",
    "chemistry": "chemistry"
}

CATEGORY_KEYWORDS = {
    "maths": ["math", "maths", "mathematics", "calculus", "algebra", "numerical", "statistics", "transforms", "probability", "discrete", "matrices", "differential", "vector", "geometry", "trigonometry"],
    "physics": ["physics", "laser", "optics", "quantum", "semiconductor", "electromagnetics", "physical sciences", "mechanics", "astrophysics"],
    "chemistry": ["chemistry", "electrochemistry", "polymers", "water treatment", "environmental chemistry", "organic", "inorganic", "biochemistry"],
    "programming": ["programming", "python", "c programming", "java", "data structures", "c++", "coding", "software", "algorithms", "dbms", "database", "operating system", "web", "oop", "oops", "compiler"],
    "electrical": ["electrical", "circuits", "electronics", "digital", "signals", "microprocessor", "microcontroller", "analog", "control systems", "power electronics", "vlsi"],
    "mechanical": ["thermodynamics", "fluid", "heat transfer", "kinematics", "manufacturing", "mechanical", "solid mechanics", "machine design", "cad", "cam", "robotics", "automobile"],
    "civil": ["surveying", "concrete", "structural", "geotechnical", "hydraulics", "civil", "environmental engineering", "transportation", "construction"],
    "computer_science": ["computer science", "computer networks", "network", "operating system", "compiler", "theory of computation", "cyber", "security", "ai", "machine learning", "data science", "cloud", "software engineering", "information technology"],
    "management": ["management", "marketing", "finance", "accounting", "human resource", "hr", "business", "economics", "ethics", "entrepreneurship", "organizational"]
}

class AcademicSyllabusQAEngine:
    """
    100% PDF-Grounded Academic Syllabus Engine with Generic Extraction Pipeline
    for ANY course present in the uploaded PDF.
    """

    def __init__(self, full_text: str, filename: str = "", subjects: Optional[List[str]] = None, file_path: str = ""):
        self.filename = filename

        if not file_path and filename:
            candidates = [
                os.path.join("backend", "uploads", filename),
                os.path.join("uploads", filename),
                filename
            ]
            for cand in candidates:
                if os.path.exists(cand):
                    file_path = cand
                    break

        self.file_path = file_path
        self.full_text = full_text
        self.pages = self._split_into_pages(full_text)
        
        raw_subjects = subjects if subjects is not None else extract_subject_candidates(full_text)
        if self.file_path and os.path.exists(self.file_path):
            try:
                rec_list = build_canonical_course_records(self.file_path)
                rec_titles = [r["title"] for r in rec_list if r.get("title")]
            except Exception:
                rec_titles = []
        else:
            rec_titles = []

        combined = []
        seen_keys = set()
        for s_title in (raw_subjects + rec_titles):
            c_s = self._clean_subject_title(s_title)
            key = normalize_text_key(c_s)
            if key and key not in seen_keys and len(c_s) >= 3:
                seen_keys.add(key)
                combined.append(c_s)

        self.subjects = combined
        self.dynamic_acronym_map = self._build_dynamic_acronym_map()
        self.semester_map = self._build_semester_map()
        self.subject_page_map = self._build_subject_page_map()

    def _build_dynamic_acronym_map(self) -> Dict[str, str]:
        """
        Dynamically generates acronym mappings for all detected subjects in the active PDF.
        E.g. "DATABASE MANAGEMENT SYSTEMS" -> "dbms", "CYBER SECURITY PRINCIPLES" -> "csp"
        """
        acronym_map = {}
        STOP_WORDS = {"and", "or", "for", "in", "of", "to", "with", "the", "a", "an"}
        
        for subj in self.subjects:
            clean_s = self._clean_subject_title(subj)
            title_only = remove_course_code(clean_s) if contains_course_code(clean_s) else clean_s
            words = [w for w in re.split(r"[^\w]+", title_only) if w and w.lower() not in STOP_WORDS]
            
            if len(words) >= 2:
                acronym = "".join([w[0].lower() for w in words if w[0].isalpha()])
                if len(acronym) >= 2 and acronym not in acronym_map:
                    acronym_map[acronym] = title_only.lower()
                    
        return acronym_map


    def _split_into_pages(self, full_text: str) -> Dict[int, str]:
        pages = {}
        parts = re.split(r"--- PAGE (\d+) ---", full_text)
        if len(parts) >= 3:
            for i in range(1, len(parts), 2):
                p_num = int(parts[i])
                p_content = parts[i+1]
                pages[p_num] = p_content
        else:
            pages[1] = full_text
        return pages

    def _build_semester_map(self) -> Dict[str, List[str]]:
        sem_map = {f"Semester {i}": [] for i in range(1, 9)}

        num_map = {
            "1": 1, "I": 1, "2": 2, "II": 2, "3": 3, "III": 3, "4": 4, "IV": 4,
            "5": 5, "V": 5, "6": 6, "VI": 6, "7": 7, "VII": 7, "8": 8, "VIII": 8
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

        def get_sem_from_line(line: str) -> Optional[int]:
            l_strip = line.strip().upper()
            if "SEMESTER I TO" in l_strip or "SEMESTER 1 TO" in l_strip:
                return None
            if l_strip in num_map:
                return num_map[l_strip]
            m = sem_header_re.search(line)
            if m:
                v1 = m.group(1)
                v2 = m.group(2)
                if v1:
                    return num_map.get(v1.upper())
                if v2:
                    return word_sem_map.get(v2.lower())
            return None

        cleaned_known = {}
        for s in self.subjects:
            c_s = self._clean_subject_title(s)
            if len(c_s) >= 4:
                cleaned_known[c_s.lower()] = s

        for p_num in range(1, len(self.pages) + 1):
            p_text = self.pages.get(p_num, "")
            p_lines = [l.strip() for l in p_text.splitlines() if l.strip()]

            i = 0
            curr_sem = None
            while i < len(p_lines):
                line = p_lines[i]
                s_found = get_sem_from_line(line)
                if s_found and len(line.split()) <= 6:
                    curr_sem = s_found
                    i += 1
                    continue

                if curr_sem is not None:
                    clean_l = self._clean_subject_title(clean_title_formatting(line))
                    if len(clean_l) >= 4 and not is_header_or_garbage(clean_l):
                        target_key = f"Semester {curr_sem}"
                        if clean_l not in sem_map[target_key]:
                            sem_map[target_key].append(clean_l)
                i += 1

        if self.subjects:
            unmapped_subjects = [s for s in self.subjects if not any(s in sub_list for sub_list in sem_map.values())]
            for s in unmapped_subjects:
                c_m = re.search(r"\b[A-Z]{2,4}\s*([1-8])\d{2,4}\b", s)
                sem_idx = int(c_m.group(1)) if c_m else 1
                sem_key = f"Semester {sem_idx}"
                if s not in sem_map[sem_key]:
                    sem_map[sem_key].append(s)

        return sem_map

    def _build_subject_page_map(self) -> Dict[str, List[int]]:
        sub_page_map = {}
        for subj in self.subjects:
            sub_page_map[subj] = []
            s_lower = subj.lower()
            for p_num, p_text in self.pages.items():
                if s_lower in p_text.lower():
                    sub_page_map[subj].append(p_num)
        return sub_page_map

    def _clean_subject_title(self, raw_subj: str) -> str:
        s = raw_subj
        s = re.sub(r"\s+\bL\s*T\s*P\s*C\b.*$", "", s, flags=re.I)
        s = re.sub(r"\s+\b\d\s+\d\s+\d\s+\d\b.*$", "", s)
        s = re.sub(r"\s+\b\d{1,2}\b\s*$", "", s)
        return s.strip(" -:,.")

    def _detect_user_intent(self, q_lower: str) -> Dict[str, Any]:
        q_norm = re.sub(r"\b([1-8])\s+(st|nd|rd|th)\b", r"\1\2", q_lower.strip(), flags=re.I)

        matched_cat = None
        for cat_name, kw_list in CATEGORY_KEYWORDS.items():
            if any(re.search(rf"\b{kw}\b", q_norm) for kw in kw_list):
                matched_cat = cat_name
                break

        sem_num = None
        ord_map = {
            "1st":1, "first":1, "2nd":2, "second":2, "3rd":3, "third":3, "4th":4, "fourth":4,
            "5th":5, "fifth":5, "6th":6, "sixth":6, "7th":7, "seventh":7, "8th":8, "eighth":8
        }

        sem_ord_m = re.search(r"\b(1st|2nd|3rd|4th|5th|6th|7th|8th|first|second|third|fourth|fifth|sixth|seventh|eighth)\b", q_norm)
        if sem_ord_m and not re.search(r"\b(year|yr|saal)\b", q_norm):
            sem_num = ord_map.get(sem_ord_m.group(1).lower())

        if not sem_num:
            sem_m = re.search(r"\b(sem|semester)\s*[-–:]?\s*([0-9]{1,2}|i{1,3}|iv|v|vi{0,3}|vii|viii)\b", q_norm)
            if sem_m:
                val = sem_m.group(2).upper()
                num_map = {"1":1, "I":1, "2":2, "II":2, "3":3, "III":3, "4":4, "IV":4, "5":5, "V":5, "6":6, "VI":6, "7":7, "VII":7, "8":8, "VIII":8}
                sem_num = num_map.get(val)

        year_num = None
        if re.search(r"\b(1st|first)\s*(year|yr|saal)\b", q_norm): year_num = 1
        elif re.search(r"\b(2nd|second)\s*(year|yr|saal)\b", q_norm): year_num = 2
        elif re.search(r"\b(3rd|third)\s*(year|yr|saal)\b", q_norm): year_num = 3
        elif re.search(r"\b(4th|fourth|final)\s*(year|yr|saal)\b", q_norm): year_num = 4

        return {
            "category": matched_cat,
            "year": year_num,
            "semester": sem_num
        }

    def _find_all_target_subjects(self, q_lower: str) -> List[Dict[str, Any]]:
        """
        Generic Course Matching Pipeline:
        1. Exact Course Code Match (Highest Priority)
        2. Scored Title & Acronym Match with Laboratory vs Theory distinction.
        """
        tokens = [w.upper() for w in re.split(r"[^\w]+", q_lower) if w]
        is_lab_query = any(w in ["LAB", "LABORATORY", "PRACTICAL", "EXPERIMENTS", "EXERCISES"] for w in tokens)

        # STEP 1: Search Exact / Case-Insensitive Course Code match
        for s in self.subjects:
            c_code = extract_course_code(s)
            clean_s = self._clean_subject_title(s)
            if c_code:
                norm_c = re.sub(r"[^\w]", "", c_code.upper())
                for t in tokens:
                    norm_t = re.sub(r"[^\w]", "", t)
                    if norm_t == norm_c or (len(norm_t) >= 4 and norm_t == norm_c):
                        return [{"subject": s, "clean_title": clean_s, "found_in_pdf": True, "code": c_code}]

        # Search full text for standalone course code match e.g. "ACB509", "ACS108"
        for t in tokens:
            norm_t = re.sub(r"[^\w]", "", t)
            if len(norm_t) >= 5 and re.match(r"^[A-Z]{2,6}\d{3,5}[A-Z]?$", norm_t):
                m_match = re.search(rf"\b{norm_t}\b[^\n]*", self.full_text, re.I)
                if m_match:
                    hdr = m_match.group(0).strip()
                    clean_h = clean_title_formatting(hdr)
                    return [{"subject": clean_h or norm_t, "clean_title": clean_h or norm_t, "found_in_pdf": True, "code": norm_t}]

        # STEP 2: Acronym & Title Normalization
        q_title = q_lower
        
        # Check dynamic acronym map first (from active PDF), then static SUBJECT_ACRONYMS
        acronyms_combined = {**self.dynamic_acronym_map, **SUBJECT_ACRONYMS}
        for acr, exp in acronyms_combined.items():
            if re.search(rf"\b{acr}\b", q_lower):
                q_title = re.sub(rf"\b{acr}\b", exp, q_title)

        GENERIC_STOP_WORDS = {
            "and", "with", "for", "ka", "ki", "ke", "ko", "syllabus", "bhejo", "batao",
            "course", "subject", "bataiye", "give", "show", "me", "tell", "what", "is",
            "the", "units", "topics", "outcomes", "books", "code", "detail", "details"
        }

        q_words = [w for w in re.split(r"[^\w]+", q_title) if len(w) >= 2]
        q_non_stop = [w for w in q_words if w not in GENERIC_STOP_WORDS]

        scored_candidates = []

        for s in self.subjects:
            clean_s = self._clean_subject_title(s)
            cs_low = clean_s.lower()
            is_lab_subj = "lab" in cs_low or "laboratory" in cs_low or "practical" in cs_low

            if is_lab_query != is_lab_subj:
                continue

            c_code = extract_course_code(s)
            s_words = [w for w in re.split(r"[^\w]+", cs_low) if len(w) >= 2]
            s_non_stop = [w for w in s_words if w not in GENERIC_STOP_WORDS]

            score = 0
            if cs_low and cs_low in q_title:
                score = 1000
            elif cs_low and q_title in cs_low:
                score = 800

            matching_non_stop = set(q_non_stop).intersection(set(s_non_stop))
            if matching_non_stop:
                score += len(matching_non_stop) * 200

            if score > 0:
                scored_candidates.append({
                    "score": score,
                    "item": {"subject": s, "clean_title": clean_s, "found_in_pdf": True, "code": c_code}
                })

        if scored_candidates:
            scored_candidates.sort(key=lambda x: x["score"], reverse=True)
            return [scored_candidates[0]["item"]]

        return []


    def _handle_subject_syllabus(self, subjects: List[Dict[str, Any]], query: str = "") -> Dict[str, Any]:
        """
        Generic 100% PDF-Grounded Response Generator for ANY matched subject.
        """
        subj_blocks = []
        for item in subjects:
            if isinstance(item, dict):
                s = item.get("subject", "")
                code = item.get("code") or extract_course_code(s)
            else:
                s = str(item)
                code = extract_course_code(s)

            clean_s = self._clean_subject_title(s)

            details = None
            if self.file_path and os.path.exists(self.file_path):
                try:
                    details = extract_course_details(self.file_path, code or clean_s)
                except Exception:
                    details = None

            if details and details.get("course"):
                c_meta = details["course"]
                actual_code = c_meta.get("code") or code or "N/A"
                actual_title = c_meta.get("title") or clean_s
                cat = c_meta.get("category", "PC")
                l = c_meta.get("lecture", 3)
                t = c_meta.get("tutorial", 0)
                p = c_meta.get("practical", 0)
                c = c_meta.get("credits", 3)
                total_hrs = c_meta.get("total_hours") or 45

                # Standardized Response Header
                header = (
                    f"**Course Code**: `{actual_code}`\n"
                    f"**Subject Name**: `{actual_title}`\n"
                    f"**Category**: `{cat}` | **L-T-P-C**: `{l}-{t}-{p}-{c}`\n"
                    f"**Total Hours**: `{total_hrs}`\n"
                )

                # Format Units vs Experiments
                units_formatted = ""
                if details.get("experiments"):
                    lab_hdg = details.get("lab_heading", "List of Experiments")
                    exp_lines = []
                    for exp in details["experiments"]:
                        exp_num = exp.get("number", 1)
                        exp_text = exp.get("text", "")
                        exp_lines.append(f"{exp_num}. {exp_text}")
                    units_formatted = f"### {lab_hdg}:\n" + "\n".join(exp_lines)
                elif details.get("units"):
                    unit_blocks = []
                    for u in details["units"]:
                        u_num = u.get("number", 1)
                        u_title = u.get("title", f"UNIT {u_num}")
                        u_hours = u.get("hours", 9)
                        u_text = u.get("text", "")

                        topics_list = u.get("topics", [])
                        if topics_list:
                            topic_bullets = "\n".join([f"- {top.get('text')}" for top in topics_list if top.get('text')])
                        else:
                            raw_items = [it.strip() for it in re.split(r'\n|\s+-\s+|;', u_text) if it.strip()]
                            if raw_items:
                                topic_bullets = "\n".join([f"- {it}" for it in raw_items])
                            else:
                                topic_bullets = f"- {u_text}"

                        unit_blocks.append(f"### Unit {u_num}: {u_title} ({u_hours} Hours)\n{topic_bullets}")
                    units_formatted = "\n\n".join(unit_blocks)
                else:
                    is_lab = p > 0 or "LAB" in actual_title.upper() or "LABORATORY" in actual_title.upper() or "PRACTICAL" in actual_title.upper()
                    if is_lab:
                        units_formatted = "#### Laboratory Experiments / Practical Content:\n- *Information not found in the uploaded document.*"
                    else:
                        units_formatted = "#### Syllabus Topics:\n- *Information not found in the uploaded document.*"

                # Format COs if present
                co_str = ""
                if details.get("course_outcomes"):
                    co_lines = [f"- **{co['id']}**: {co['text']}" for co in details["course_outcomes"] if len(co.get('text', '')) > 2]
                    if co_lines:
                        co_str = "\n\n#### 🎯 Course Outcomes (COs):\n" + "\n".join(co_lines)

                # Format POs if present
                po_str = ""
                if details.get("programme_outcomes"):
                    po_lines = [f"- **{po['id']}**: {po['text']}" for po in details["programme_outcomes"] if len(po.get('text', '')) > 2]
                    if po_lines:
                        po_str = "\n\n#### 🎓 Programme Outcomes (POs):\n" + "\n".join(po_lines)

                # Format Books if present
                books_str = ""
                if details.get("books"):
                    bk_lines = []
                    for b in details["books"]:
                        k_str = b.get("kind", "text").capitalize()
                        bk_lines.append(f"- [{k_str}] *{b.get('title')}* by {b.get('author')} ({b.get('publisher')}, {b.get('year')})")
                    if bk_lines:
                        books_str = "\n\n#### 📚 Textbooks & Reference Books:\n" + "\n".join(bk_lines)

                full_block = f"{header}\n{units_formatted}{co_str}{po_str}{books_str}"
                subj_blocks.append(full_block)
            else:
                code_str = code or "N/A"
                subj_blocks.append(
                    f"**Course Code**: `{code_str}`\n"
                    f"**Subject Name**: `{clean_s}`\n\n"
                    f"#### Syllabus Content:\n"
                    f"- *Information not found in the uploaded document.*"
                )

        ans = "\n\n---\n\n".join(subj_blocks)
        return {"answer": ans, "found": True}

    def answer_question(self, query: str) -> Dict[str, Any]:
        q = query.strip()
        q_lower = q.lower()

        greetings = ["hi", "hello", "hii", "hey", "good morning", "good afternoon"]
        if any(w == q_lower for w in greetings) or any(q_lower.startswith(g + " ") for g in ["hi ", "hello ", "hey "]):
            return {
                "answer": f"Hello! 👋 Ask me any question about your uploaded syllabus PDF (**{self.filename or 'Document'}**).",
                "source_pages": [1],
                "found": True
            }

        # Find Target Subject Matches via canonical code & lab-aware title matching
        target_matches = self._find_all_target_subjects(q_lower)

        if target_matches:
            return self._handle_subject_syllabus(target_matches, q_lower)

        return {"answer": "Information not found in the uploaded document.", "found": False}

