import re

# ============================================================
# PATTERNS & CONSTANTS
# ============================================================

COURSE_CODE_PATTERNS = [
    re.compile(r"\b[A-Z]{1,5}\d{3,5}[A-Z]?\b", re.I),
    re.compile(r"\b\d{2}[A-Z]{2,6}\d{2,4}[A-Z]?\b", re.I),
    re.compile(r"\b[A-Z]{2,6}\s*[-/]?\s*\d{3,5}[A-Z]?\b", re.I),
]

INVALID_CODES = {
    "PAGE", "UNIT", "SEM", "SEM1", "SEM2", "SEM3", "SEM4", "SEM5", "SEM6", "SEM7", "SEM8",
    "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026",
    "LTPC", "CBCS", "HTML", "IEEE", "ISBN", "ISSN", "TOTAL", "CO1", "CO2", "CO3", "PO1", "PSO1",
    "PERIODS", "HOURS", "MARKS", "TEXT", "UNIT1", "UNIT2", "UNIT3", "UNIT4", "UNIT5"
}

CATEGORY_TAG_PATTERN = re.compile(
    r"^("
    r"HSMC|BSC|ESC|PCC|PEC|OEC|EEC|AC|"
    r"FC\s*\([^)]*\)|"
    r"EC\s*-\s*(PS|OE|PC)|"
    r"FC|PC|PE|OE|PI|HS|BS|ES|EEC|MC|CC|SC|AC|"
    r"Major\s+Core|Program\s+Elective|Skill\s+Enhancement|Ability\s+Enhancement|University\s+Core|Internship|Summer\s+Internship"
    r")$", re.I
)

CREDIT_PATTERN = re.compile(
    r"^("
    r"L\s*T\s*P\s*C|"
    r"\d\s+\d\s+\d\s+\d|"
    r"\d\s+\d\s+\d\s+\d\s+\d|"
    r"\d-\d-\d-\d|"
    r"\d+"
    r")$", re.I
)

OFFERING_DEPTS = {
    "ENGLISH", "MATHEMATICS", "MATHS", "PHYSICS", "CHEMISTRY", "PHYSICS/CHEMISTRY",
    "MANAGEMENT", "MECHANICAL", "MECH", "CIVIL", "AUTO", "AUTOMOBILE",
    "BIOTECH", "BIOTECHNOLOGY", "BIOMEDICAL", "EEE", "ECE", "CSE", "ELECTRICAL",
    "ELECTRONICS", "HUMANITIES", "HSS", "MBA", "MCA", "IT", "LAW", "PHARMACY",
    "AEROSPACE", "CHEMICAL", "MECHATRONICS", "ROBOTICS", "COMMERCE"
}

COURSE_TYPE_WORDS = {
    "THEORY ONLY", "LAB ONLY", "EMBEDDED", "EMBEDDED THEORY AND LAB",
    "EMBEDDED THEORY & LAB", "SOFT SKILL", "ONLINE COURSE", "BASKET",
    "AUDIT COURSE", "VALUE ADDED COURSE", "NON-GRADED CORE REQUIREMENT",
    "BRIDGE COURSE"
}

# Words that mean management is part of title, NOT an offering department column
TITLE_MANAGEMENT_PREFIXES = {
    "SOFTWARE PROJECT", "TOTAL QUALITY", "SUPPLY CHAIN", "RESOURCE", "MAINTENANCE",
    "SIX SIGMA QUALITY", "PRODUCT LIFE CYCLE", "RISK", "HOSPITAL", "DATABASE",
    "SERVICE", "ENVIRONMENT", "INFORMATION", "INNOVATION", "TECHNOLOGY", "PROJECT"
}

TRAILING_DEPT_REGEX = re.compile(
    r"\s+\b(MECH|MECHANICAL|CIVIL|AUTO|AUTOMOBILE|BIOTECH|BIOMEDICAL|EEE|ECE|CSE|IT|HSS)\s*$",
    re.I
)

ELECTIVE_SLOT_REGEX = re.compile(
    r"^(open\s+elective|professional\s+elective|programme\s+elective|university\s+open\s+elective|elective|b\.?tech\.?\s+.*elective|b\.?tech\.?\s+.*foreign\s+language)\s*[-–—]?\s*(i|ii|iii|iv|v|vi|1|2|3|4|5|6|2021.*)?$",
    re.I
)

SYLLABUS_BODY_STOPPERS = [
    "syllabus", "preamble", "course objective", "course outcome", "programme outcome",
    "text book", "textbook", "text books", "references", "reference books", "web reference",
    "unit ", "module ", "list of experiments", "course designer", "name of the faculty",
    "faculty name", "designation", "department/name", "email id", "mapping",
    "s- strong", "m-medium", "l-low", "need for and", "quality system", "douglas",
    "srinivasan", "tom denton", "william", "alan", "beckwith", "srinath", "prentice",
    "mcgraw", "wiley", "springer", "addison", "elsevier", "edward arnold", "john wiley",
    "laxmi publications", "tata mcgraw", "katsun", "rai & sons", "sharing information",
    "general reading", "total :", "periods", "credit summary", "mapping of cos",
    "subject title", "education", "publications", "co1", "co2", "co3", "co4", "co5", "co6"
]

SUBJECT_LABEL_PATTERNS = [
    re.compile(r"\bcourse\s*(title|name)\s*[:\-]?\s*(.+)", re.I),
    re.compile(r"\bsubject\s*(title|name)\s*[:\-]?\s*(.+)", re.I),
    re.compile(r"\bpaper\s*(title|name)\s*[:\-]?\s*(.+)", re.I),
]

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clean_line(l: str) -> str:
    if not l:
        return ""
    l = l.replace("\t", " ").replace("\r", " ")
    l = re.sub(r"\s+", " ", l)
    return l.strip(" :_|;")

def contains_course_code(line: str) -> bool:
    if not line:
        return False
    for p in COURSE_CODE_PATTERNS:
        m = p.search(line)
        if m:
            code = m.group(0).upper().strip()
            if code not in INVALID_CODES and not code.isdigit():
                return True
    return False

def extract_course_code(line: str) -> str:
    if not line:
        return ""
    for p in COURSE_CODE_PATTERNS:
        m = p.search(line)
        if m:
            code = m.group(0).upper().strip()
            if code not in INVALID_CODES and not code.isdigit():
                return code
    return ""

def remove_course_code(line: str) -> str:
    res = line
    for p in COURSE_CODE_PATTERNS:
        matches = p.findall(res)
        for m in matches:
            if m.upper().strip() not in INVALID_CODES:
                res = res.replace(m, " ")
    return clean_line(res)

def remove_serial_number(line: str) -> str:
    return re.sub(r"^\s*\d{1,4}\s*[.)\-:]\s*", "", line).strip()

def is_course_type_metadata(line: str, has_title: bool = True) -> bool:
    l = clean_line(line).upper()
    if not l:
        return False
    if l in COURSE_TYPE_WORDS:
        return True
    if l == "PROJECT" and has_title:
        return True
    if re.match(r"^v?\d+\.\d+$", l, re.I):
        return True
    if l.isdigit() and len(l) <= 2:
        return True
    return False

def clean_title_formatting(title: str) -> str:
    if not title:
        return ""
    # Strip trailing course type metadata if concatenated
    title = re.sub(r"\s+\b(Theory Only|Lab Only|Embedded Theory and Lab|Embedded Theory & Lab|Embedded|Soft Skill|Online Course|Basket)\b.*$", "", title, flags=re.I)
    
    # Strip trailing Project if preceded by a title
    title = re.sub(r"(\b(?:Internship|Project\s*-\s*[I|V|X\d]+|Engineering|Course)\b.*?\s+)Project\b.*$", r"\1", title, flags=re.I)
    title = re.sub(r"^(.*?)\s+Project\s+\d+.*$", r"\1", title, flags=re.I)

    # Strip trailing version numbers like 1.0, 2.0, 0.0
    title = re.sub(r"\s+\b\d+\.\d+\b.*$", "", title)

    # Strip trailing standalone numbers (credits/L/T/P/J values like 0, 1, 2)
    title = re.sub(r"\s+\b\d{1,2}\b\s*$", "", title)

    # Fix spacing issues where Lab or Laboratory is concatenated without space (e.g. MultimediaLab -> Multimedia Lab)
    title = re.sub(r"([a-z])(Lab|Laboratory)\b", r"\1 \2", title)
    title = re.sub(r"([A-Z]{2,})(Lab|Laboratory)\b", r"\1 \2", title)

    # Strip parenthetical common-to info
    title = re.sub(r"\s*\([^)]*common\s+to[^)]*\)", "", title, flags=re.I)
    title = re.sub(r"\s*\([^)]*branches[^)]*\)", "", title, flags=re.I)
    title = re.sub(r"\s*\([^)]*\)$", "", title)
    
    # Strip trailing dept code if present
    title = TRAILING_DEPT_REGEX.sub("", title)

    # Normalize dash characters (en-dash / em-dash to standard hyphen)
    title = title.replace("–", "-").replace("—", "-")
    title = re.sub(r"\s+", " ", title)
    return title.strip(" -:,.")

def is_category_line(line: str) -> bool:
    l = clean_line(line)
    return bool(CATEGORY_TAG_PATTERN.match(l))

def is_credit_line(line: str) -> bool:
    l = clean_line(line)
    return bool(CREDIT_PATTERN.match(l))

def is_prereq_line(line: str) -> bool:
    l = clean_line(line).upper()
    return l in {"NIL", "NONE", "PREREQUISITE", "PRE-REQUISITE"}

def is_offering_dept_word(line: str) -> bool:
    l = clean_line(line).upper()
    return l in OFFERING_DEPTS

def is_actual_dept_boundary(line: str, next_line: str = "", current_title_prefix: str = "") -> bool:
    if not is_offering_dept_word(line):
        return False

    nxt = clean_line(next_line)
    if not is_category_line(nxt):
        return False

    if line.upper() == "MANAGEMENT":
        prefix_upper = current_title_prefix.upper().strip()
        if "MANAGEMENT" in prefix_upper.split():
            return True
        if any(prefix_upper.endswith(p) or p in prefix_upper for p in TITLE_MANAGEMENT_PREFIXES):
            return False

    return True

def is_syllabus_stopper(line: str) -> bool:
    l = clean_line(line).lower()
    if not l:
        return True
    for s in SYLLABUS_BODY_STOPPERS:
        if s in l:
            return True
    if len(l.split()) > 12 or l.count(".") > 1:
        return True
    return False

def is_header_or_garbage(line: str) -> bool:
    l = clean_line(line).lower()
    if not l:
        return True
    if l in {"s.no", "s.no.", "code", "course code", "course title", "course name", "course category", "type of program", "cluster", "institute", "department", "credits", "contact periods", "l", "t", "p", "c", "prerequisite", "offering", "ver", "sio", "n", "j"}:
        return True
    if "curriculum & syllabus" in l or "category a" in l or "category b" in l or "category c" in l or "category d" in l or "curriculum -" in l or "curriculum for" in l:
        return True
    if "humanities and sciences" in l or "basic sciences" in l or "schedulingofcourses" in l or "credit summary" in l or "program schemes" in l:
        return True
    return is_syllabus_stopper(line)

def subject_key(subject: str) -> str:
    key = subject.lower()
    key = key.replace("&", " and ").replace("–", "-").replace("—", "-")
    key = re.sub(r"[^a-z0-9]+", "", key)
    # Ignore trailing 's' in key matching to deduplicate Measurement vs Measurements singular/plural table variants
    if key.endswith("s"):
        key = key[:-1]
    return key.strip()

# ============================================================
# PRIMARY EXTRACTION LOGIC
# ============================================================

def extract_subject_candidates(text: str):
    """
    Academic Syllabus Subject Extraction Engine.
    
    Extracts complete, unique, actual subject names while excluding metadata,
    scheduling placeholders, textbook citations, and unit topics.
    """
    if not text:
        return []

    lines_raw = text.splitlines()

    pages_dict = {}
    current_page = 1
    page_text_list = []

    for l in lines_raw:
        m = re.search(r"--- PAGE (\d+) ---", l)
        if m:
            if page_text_list:
                pages_dict[current_page] = "\n".join(page_text_list)
                page_text_list = []
            current_page = int(m.group(1))
        else:
            page_text_list.append(l)
    if page_text_list:
        pages_dict[current_page] = "\n".join(page_text_list)

    # Scan all pages of the active PDF to ensure complete course detection
    target_pages = list(pages_dict.values())
    combined_text = "\n".join(target_pages)
    lines = [clean_line(l) for l in combined_text.splitlines()]

    subjects = []
    seen_keys = set()
    seen_codes = set()

    # PASS 1: Course Code Primary Pass
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue

        if contains_course_code(line):
            code = extract_course_code(line)
            code_line_clean = remove_course_code(remove_serial_number(line))
            
            title_parts = []
            if code_line_clean and not is_header_or_garbage(code_line_clean) and not is_category_line(code_line_clean) and not is_course_type_metadata(code_line_clean, False):
                title_parts.append(code_line_clean)

            j = i + 1
            while j < len(lines) and len(title_parts) < 8:
                nxt = lines[j]
                if not nxt:
                    j += 1
                    continue

                if contains_course_code(nxt):
                    break

                if is_syllabus_stopper(nxt) or is_header_or_garbage(nxt):
                    break

                nxt_after1 = lines[j+1] if j+1 < len(lines) else ""

                if is_category_line(nxt) or is_credit_line(nxt) or is_prereq_line(nxt) or is_course_type_metadata(nxt, bool(title_parts)):
                    break

                current_prefix = " ".join(title_parts)
                if is_actual_dept_boundary(nxt, nxt_after1, current_prefix):
                    break

                nxt_clean = remove_serial_number(nxt)
                if nxt_clean:
                    title_parts.append(nxt_clean)

                j += 1

            raw_title = " ".join(title_parts)
            clean_title = clean_title_formatting(raw_title)

            lower_title = clean_title.lower()
            if clean_title and not ELECTIVE_SLOT_REGEX.match(lower_title) and len(clean_title) >= 3 and not is_header_or_garbage(clean_title):
                key = subject_key(clean_title)
                
                # Check deduplication by code AND title key
                code_seen = code and code in seen_codes
                key_seen = key and key in seen_keys

                if not code_seen and not key_seen:
                    if code:
                        seen_codes.add(code)
                    if key:
                        seen_keys.add(key)
                    subjects.append(clean_title)

            i = max(i + 1, j)
            continue

        # Check explicit subject labels
        for pattern in SUBJECT_LABEL_PATTERNS:
            match = pattern.search(line)
            if match:
                raw_val = match.group(match.lastindex)
                cand = clean_title_formatting(remove_course_code(remove_serial_number(raw_val)))
                lower_cand = cand.lower()
                if cand and not ELECTIVE_SLOT_REGEX.match(lower_cand) and len(cand) >= 3 and not is_header_or_garbage(cand):
                    key = subject_key(cand)
                    if key and key not in seen_keys:
                        seen_keys.add(key)
                        subjects.append(cand)
                break

        i += 1

    # PASS 2: Table Category Fallback (For syllabi like Chandigarh University)
    if not subjects:
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line or is_header_or_garbage(line) or contains_course_code(line):
                i += 1
                continue

            nxt1 = lines[i+1] if i+1 < len(lines) else ""
            nxt2 = lines[i+2] if i+2 < len(lines) else ""

            if is_category_line(nxt1) and (is_credit_line(nxt2) or not nxt2):
                cand = clean_title_formatting(remove_serial_number(line))
                lower_cand = cand.lower()
                if cand and not ELECTIVE_SLOT_REGEX.match(lower_cand) and len(cand) >= 3 and not is_header_or_garbage(cand):
                    key = subject_key(cand)
                    if key and key not in seen_keys:
                        seen_keys.add(key)
                        subjects.append(cand)
                i += 2
                continue

            i += 1

    return subjects


def extract_subjects(text: str):
    subjects = extract_subject_candidates(text)
    return {
        "subject_count": len(subjects),
        "subjects_found": subjects
    }