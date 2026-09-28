import re
import os
import fitz  # PyMuPDF
from typing import Dict, List, Any, Optional, Tuple

# ============================================================
# CONSTANTS & BLOOM TAXONOMY VERB MAPPING
# ============================================================

BLOOM_LEVELS = ["remember", "understand", "apply", "analyse", "evaluate", "create"]

BLOOM_VERBS = {
    "remember": {
        "define", "list", "recall", "state", "name", "identify", "label", "memorize",
        "repeat", "reproduce", "retrieve", "outline", "record", "match", "quote", "select"
    },
    "understand": {
        "explain", "describe", "discuss", "illustrate", "summarize", "interpret", "classify",
        "express", "locate", "recognize", "report", "review", "translate", "paraphrase",
        "concept", "introduction", "overview", "basic", "basics", "fundamentals", "types",
        "elements", "architecture", "structure", "meaning", "comparison"
    },
    "apply": {
        "apply", "calculate", "solve", "compute", "implement", "demonstrate", "execute",
        "operate", "sketch", "use", "construct", "modify", "prepare", "show", "write",
        "process", "practice", "operation", "operations", "algorithm", "algorithms",
        "traversal", "search", "sorting", "manipulation", "derivation"
    },
    "analyse": {
        "analyze", "analyse", "compare", "contrast", "differentiate", "examine", "test",
        "experiment", "distinguish", "question", "diagram", "dissect", "inspect", "inventory",
        "performance", "complexity", "efficiency", "decomposition", "breakdown"
    },
    "evaluate": {
        "evaluate", "assess", "judge", "verify", "critique", "appraise", "defend",
        "value", "rate", "measure", "estimation", "validation", "comparison", "benchmark"
    },
    "create": {
        "design", "create", "develop", "formulate", "plan", "compose", "invent",
        "setup", "organize", "assemble", "generate", "synthesize", "build", "modeling",
        "model", "construction", "synthesis"
    }
}

BLOOM_PRINTED_PATTERNS = [
    (re.compile(r"\b[\[\(]?(?:K1|L1|Remember|Remembering)[\]\)]?\b", re.I), "remember"),
    (re.compile(r"\b[\[\(]?(?:K2|L2|Understand|Understanding)[\]\)]?\b", re.I), "understand"),
    (re.compile(r"\b[\[\(]?(?:K3|L3|Apply|Applying)[\]\)]?\b", re.I), "apply"),
    (re.compile(r"\b[\[\(]?(?:K4|L4|Analyse|Analyzing|Analysis)[\]\)]?\b", re.I), "analyse"),
    (re.compile(r"\b[\[\(]?(?:K5|L5|Evaluate|Evaluating|Evaluation)[\]\)]?\b", re.I), "evaluate"),
    (re.compile(r"\b[\[\(]?(?:K6|L6|Create|Creating|Synthesis)[\]\)]?\b", re.I), "create"),
]

COURSE_CODE_PATTERNS = [
    re.compile(r"\b[A-Z]{1,5}\d{3,5}[A-Z]?\b"),
    re.compile(r"\b\d{2}[A-Z]{2,6}\d{2,4}[A-Z]?\b"),
    re.compile(r"\b[A-Z]{2,6}\s*[-/]?\s*\d{3,5}[A-Z]?\b"),
]

INVALID_CODES = {
    "PAGE", "UNIT", "SEM", "SEM1", "SEM2", "SEM3", "SEM4", "SEM5", "SEM6", "SEM7", "SEM8",
    "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027",
    "LTPC", "CBCS", "HTML", "IEEE", "ISBN", "ISSN", "TOTAL", "CO1", "CO2", "CO3", "CO4", "CO5",
    "PO1", "PO2", "PO3", "PO4", "PO5", "PSO1", "PSO2", "PERIODS", "HOURS", "MARKS", "TEXT",
    "UNIT1", "UNIT2", "UNIT3", "UNIT4", "UNIT5", "PART", "ANNA", "R2023", "R2021", "R2017"
}

CATEGORY_PATTERN = re.compile(
    r"\b(PC|PE|OE|HS|BS|ES|EEC|MC|PCC|PEC|BSC|ESC|HSMC|OEC|AC|CC|SC)\b", re.I
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_text_key(text: str) -> str:
    """Normalizes string for comparison by removing special chars and extra spaces."""
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", text)
    return " ".join(cleaned.upper().split())


def infer_bloom_level(text: str) -> Tuple[str, str]:
    """
    Returns (bloom_level, bloom_source) for a given topic or outcome text.
    First checks for printed levels, otherwise infers using verb matching.
    """
    for pattern, level in BLOOM_PRINTED_PATTERNS:
        if pattern.search(text):
            return level, "printed"

    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    for word in words:
        for level, verb_set in BLOOM_VERBS.items():
            if word in verb_set:
                return level, "inferred"

    return "understand", "inferred"


def is_page_overview_table(text: str) -> bool:
    """
    Identifies whether a page is a multi-course overview curriculum table page.
    """
    if not text:
        return False
    found_codes = set()
    for line in text.splitlines():
        for pat in COURSE_CODE_PATTERNS:
            for m in pat.finditer(line):
                code = m.group(0).replace(" ", "").upper()
                if code not in INVALID_CODES and len(code) >= 5 and not code.isdigit():
                    found_codes.add(code)
    if len(found_codes) >= 3:
        return True
    if re.search(r"\bSEMESTER\s+(?:I|II|III|IV|V|VI|VII|VIII|[1-8])\b", text, re.I) and ("CREDITS" in text.upper() or "L T P C" in text.upper() or "L  T  P  C" in text.upper()):
        return True
    if bool(re.search(r"\bS\.?\s*No\b.*\bCourse\s+Title\b", text, re.S | re.I)) or bool(re.search(r"\bS\.?\s*No\b.*\bCredits\b", text, re.S | re.I)):
        return True
    return False


def build_canonical_course_records(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Scans PDF page by page to find all courses, tracking both initial overview page
    and detailed syllabus start page.
    """
    doc = fitz.open(pdf_path)
    page_texts = [doc[p].get_text() for p in range(len(doc))]
    records = []
    code_map = {}

    course_header_regex = re.compile(
        r"(?:COURSE\s+CODE|CODE|SUBJECT\s+CODE)?\s*[:\s]*\b([A-Z]{2,6}\s*[-/]?\s*\d{3,5}[A-Z]?)\b\s*[:\-\|]?\s*(.+)",
        re.I
    )

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        is_table_overview_page = is_page_overview_table(text)

        is_detailed_page = not is_table_overview_page and (
            bool(re.search(r"\bUNIT\s*[\-\–\—\:]?\s*(I|1|ONE)\b", text, re.I)) or
            bool(re.search(r"\bMODULE\s*[\-\–\—\:]?\s*(I|1|ONE)\b", text, re.I)) or
            bool(re.search(r"\b(?:LIST OF EXPERIMENTS|LAB EXPERIMENTS|LABORATORY EXPERIMENTS|PRACTICAL EXPERIMENTS|EXPERIMENTS|PRACTICALS|LABORATORY EXERCISES|PRACTICAL EXERCISES|PRACTICAL CONTENT|LAB CONTENT)\b", text, re.I)) or
            bool(re.search(r"\bPREAMBLE\b", text, re.I)) or
            bool(re.search(r"\bCOURSE\s*(?:OBJECTIVES?|OUTCOMES?)\b", text, re.I)) or
            bool(re.search(r"\bSDGs\s+Mapped\b", text, re.I)) or
            bool(re.search(r"\bPractical Course\b", text, re.I))
        )


        for i, line in enumerate(lines):
            match = course_header_regex.search(line)
            code = None
            title = None

            if match:
                potential_code = match.group(1).replace(" ", "").upper()
                potential_title = match.group(2).strip()
                if potential_code not in INVALID_CODES and len(potential_code) >= 5:
                    code = potential_code
                    title = potential_title
            else:
                for pat in COURSE_CODE_PATTERNS:
                    c_match = pat.search(line)
                    if c_match:
                        potential_code = c_match.group(0).replace(" ", "").upper()
                        if potential_code not in INVALID_CODES and len(potential_code) >= 5:
                            code = potential_code
                            title_part = line.replace(c_match.group(0), "").strip(" :-|")
                            if not title_part and i + 1 < len(lines):
                                title_part = lines[i + 1].strip()
                            title = title_part
                            break

            if code:
                title_clean = re.sub(r"^\s*\d+[\.\s\-]+", "", title or "").strip()
                title_clean = re.sub(r"\s*(?:L\s*T\s*P\s*C|CREDITS|\d\s+\d\s+\d\s+\d).*$", "", title_clean, flags=re.I).strip(" :-|")
                if not title_clean or len(title_clean) < 3:
                    if i + 1 < len(lines):
                        title_clean = re.sub(r"^\s*\d+[\.\s\-]+", "", lines[i + 1]).strip()

                if title_clean.upper() in {"SYLLABUS", "CURRICULUM", "COURSE OBJECTIVES", "UNIT I"}:
                    if i + 2 < len(lines):
                        title_clean = re.sub(r"^\s*\d+[\.\s\-]+", "", lines[i + 2]).strip()

                if code not in code_map:
                    rec = {
                        "code": code,
                        "title": title_clean.upper() if title_clean else code,
                        "normalized_code": normalize_text_key(code),
                        "normalized_title": normalize_text_key(title_clean),
                        "overview_page": page_num + 1,
                        "start_page": page_num + 1 if is_detailed_page else None,
                        "end_page": len(doc)
                    }
                    code_map[code] = rec
                    records.append(rec)
                else:
                    rec = code_map[code]
                    if is_detailed_page:
                        if rec["start_page"] is None or (page_num + 1 > rec["overview_page"] and rec["start_page"] == rec["overview_page"]):
                            rec["start_page"] = page_num + 1
                    if title_clean and len(title_clean) > len(rec["title"]):
                        rec["title"] = title_clean.upper()
                        rec["normalized_title"] = normalize_text_key(title_clean)

        if is_detailed_page and page_num > 0:
            prev_txt = page_texts[page_num - 1]
            for c_code, r_item in code_map.items():
                if r_item["start_page"] is None or r_item["start_page"] == r_item["overview_page"]:
                    if c_code in prev_txt:
                        r_item["start_page"] = page_num

    doc.close()

    for r in records:
        if r["start_page"] is None:
            r["start_page"] = r["overview_page"]

    records.sort(key=lambda r: (r["start_page"], r["overview_page"]))

    for idx in range(len(records)):
        if idx + 1 < len(records):
            next_start = records[idx + 1]["start_page"]
            if next_start > records[idx]["start_page"]:
                records[idx]["end_page"] = next_start - 1
            else:
                records[idx]["end_page"] = next_start

    return records


def extract_courses_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Task 1 Interface: Returns list of all detected courses with code, title, and page.
    """
    records = build_canonical_course_records(pdf_path)
    return [
        {
            "code": r["code"],
            "title": r["title"],
            "page": r["overview_page"]
        }
        for r in records
    ]


def find_matching_course_record(pdf_path: str, query: str) -> Optional[Dict[str, Any]]:
    """
    Search pipeline:
    1. Exact / Normalized Course Code match (Highest priority)
    2. Normalized Title match with Laboratory vs Theory protection.
    """
    records = build_canonical_course_records(pdf_path)
    if not records or not query:
        return None

    clean_query = query.strip()
    norm_query_code = re.sub(r"[^\w]", "", clean_query.upper())

    # STEP 1: Course Code Matching (Highest Priority)
    for r in records:
        norm_rec_code = re.sub(r"[^\w]", "", r["code"].upper())
        if norm_query_code == norm_rec_code or norm_rec_code in norm_query_code.split():
            return r
        if len(norm_rec_code) >= 4 and re.search(r"\b" + re.escape(norm_rec_code) + r"\b", norm_query_code):
            return r

    # STEP 2: Course Title & Acronym Matching
    norm_query_title = normalize_text_key(clean_query)

    is_lab_query = any(kw in clean_query.lower() for kw in ["lab", "laboratory", "practical", "experiments"])

    candidates = []
    for r in records:
        r_title = r["title"].upper()
        is_lab_course = "LAB" in r_title or "LABORATORY" in r_title or "PRACTICAL" in r_title

        if is_lab_query == is_lab_course:
            if norm_query_title in r["normalized_title"] or r["normalized_title"] in norm_query_title:
                candidates.append(r)

    if candidates:
        return candidates[0]

    for r in records:
        if norm_query_title in r["normalized_title"]:
            return r

    return None


NON_COURSE_PREFIXES = {
    "MAY", "JAN", "FEB", "MAR", "APR", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
    "ISO", "IEEE", "ISBN", "PAGE", "PART", "UNIT", "ACT", "FROM", "INTO", "WITH", "YEAR",
    "PUBL", "HTTP", "HTTPS", "VOL", "ISSUE", "EDIT", "CHAP"
}

def extract_course_code_local(line: str) -> str:
    if not line:
        return ""
    for pat in COURSE_CODE_PATTERNS:
        m = pat.search(line)
        if m:
            code = m.group(0).replace(" ", "").upper().strip()
            prefix3 = code[:3]
            prefix4 = code[:4]
            if prefix3 in NON_COURSE_PREFIXES or prefix4 in NON_COURSE_PREFIXES:
                continue
            if code not in INVALID_CODES and len(code) >= 5 and not code.isdigit():
                return code
    return ""


def extract_course_details(pdf_path: str, target_course_code: str) -> Dict[str, Any]:
    """
    Task 2 Interface: Extracts complete detailed syllabus JSON for a specific course code.
    Bounded strictly to that course's canonical page range.
    """
    records = build_canonical_course_records(pdf_path)
    target_record = None

    target_code_norm = re.sub(r"[^\w]", "", target_course_code.upper())
    for r in records:
        if re.sub(r"[^\w]", "", r["code"].upper()) == target_code_norm:
            target_record = r
            break

    if not target_record:
        target_record = find_matching_course_record(pdf_path, target_course_code)

    doc = fitz.open(pdf_path)

    if target_record:
        start_page = target_record["start_page"]
        end_page = target_record["end_page"]
        course_title = target_record["title"]
        actual_code = target_record["code"]
        course_pages = list(range(start_page, min(end_page + 2, len(doc) + 1)))
    else:
        actual_code = target_course_code
        course_title = target_course_code
        course_pages = [1]

    raw_course_pages = []
    for p in course_pages:
        if 1 <= p <= len(doc):
            p_text = doc[p - 1].get_text()
            raw_course_pages.append((p, p_text))

    full_course_text = ""
    for p, p_text in raw_course_pages:
        if p > (start_page if target_record else 1):
            # Check if a NEW course starts on this page after target_record
            next_code_pos = -1
            for line in p_text.splitlines():
                c_code_found = extract_course_code_local(line)
                if c_code_found and c_code_found != actual_code:
                    pos = p_text.find(line)
                    if pos != -1:
                        next_code_pos = pos
                        break

            if next_code_pos != -1:
                full_course_text += f"\n--- PAGE {p} ---\n" + p_text[:next_code_pos]
                break

            # Check if a UNIT I or MODULE I of a DIFFERENT course starts on this page
            m_unit1 = re.search(r"\b(?:UNIT|MODULE)\s*[\-\–\—\:]?\s*(?:I|1|ONE)\b", p_text, re.I)
            if m_unit1:
                prev_text = p_text[:m_unit1.start()]
                m_prev_code = re.search(r"\b([A-Z]{2,6}\d{3,5}[A-Z]?)\b", prev_text)
                if m_prev_code and m_prev_code.group(1).upper() != actual_code:
                    pos = p_text.find(m_prev_code.group(0))
                    full_course_text += f"\n--- PAGE {p} ---\n" + p_text[:pos]
                    break

        full_course_text += f"\n--- PAGE {p} ---\n" + p_text

    # Crop full_course_text starting from exact course code line if present on start page
    code_pos = full_course_text.find(actual_code)
    if code_pos != -1:
        full_course_text = full_course_text[code_pos:]

    t_match = re.search(re.escape(actual_code) + r"\s*[-–:]\s*([^\n]+)", full_course_text, re.I)
    if t_match:
        course_title = t_match.group(1).strip(" :-|")
        course_title = re.sub(r"\s*(?:L\s*T\s*P\s*C|CREDITS|\d\s+\d\s+\d\s+\d).*$", "", course_title, flags=re.I).strip()

    category = "PC"
    cat_match = CATEGORY_PATTERN.search(full_course_text)
    if cat_match:
        category = cat_match.group(1).upper()

    lecture, tutorial, practical, credits_val = 3, 0, 0, 3
    ltpc_match = re.search(r"L\s*T\s*P\s*C\s*[:\-\|]?\s*(\d)\s+(\d)\s+(\d)\s+(\d)", full_course_text, re.I)
    if not ltpc_match:
        ltpc_match = re.search(r"\b(\d)\s+[\-\s]\s*(\d)\s+[\-\s]\s*(\d)\s+[\-\s]\s*(\d)\b", full_course_text)

    if ltpc_match:
        lecture = int(ltpc_match.group(1))
        tutorial = int(ltpc_match.group(2))
        practical = int(ltpc_match.group(3))
        credits_val = int(ltpc_match.group(4))

    # Total Hours / Total Periods Extraction
    total_hrs = None
    tot_match = re.search(r"Total\s+(?:Periods|Hours|Hrs)\s*[:\-\|]?\s*(\d+)", full_course_text, re.I)
    if tot_match:
        total_hrs = int(tot_match.group(1))

    # Units & Topics Extraction
    units = []
    experiments = []
    lab_heading = "List of Experiments"

    unit_blocks = re.split(r"(?:^|\n|\r)\s*(?:UNIT|MODULE|CHAPTER)\s*[^\w\s]?\s*([I|V|X|\d]+)", full_course_text, flags=re.I)

    if len(unit_blocks) > 1:
        for i in range(1, len(unit_blocks), 2):
            unit_num_str = unit_blocks[i].strip()
            unit_content = unit_blocks[i + 1] if i + 1 < len(unit_blocks) else ""

            roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}
            unit_num = roman_map.get(unit_num_str.upper(), int(unit_num_str) if unit_num_str.isdigit() else (i // 2 + 1))

            lines = [l.strip() for l in unit_content.split("\n") if l.strip()]

            title_lines = [lines[0]] if lines else [f"UNIT {unit_num}"]
            idx = 1
            while idx < len(lines):
                l_next = lines[idx]
                is_bullet_or_num = bool(re.match(r"^(?:[●•\*]|(?:\d+[\.\)\-]))", l_next))
                is_hour_only = bool(re.match(r"^\d+(?:\+\d+)?\s*(?:PERIODS|HOURS|HRS)?$", l_next, re.I))

                prev_title = " ".join(title_lines)
                ends_incomplete = bool(re.search(r"\b(?:IN|AND|FOR|OF|TO|WITH|ON|THE|AN|A|BY|AT|FROM|-[-\s]*)$\b", prev_title, re.I)) or prev_title.endswith("-") or prev_title.endswith("–")
                is_title_case = l_next.isupper() or bool(re.match(r"^[A-Z0-9\s\-\–\—\:\,\(\)]+$", l_next))

                if not is_bullet_or_num and not is_hour_only and (ends_incomplete or (is_title_case and len(l_next.split()) <= 4 and not re.search(r"\b(?:introduction|basics|types|concept|overview|definition|classification)\b", l_next, re.I))):
                    title_lines.append(l_next)
                    idx += 1
                else:
                    break

            unit_title_raw = " ".join(title_lines)
            hours_in_title = re.search(r"(\d+)(?:\s*\+\s*(\d+))?\s*(?:PERIODS|HOURS|HRS)?\s*$", unit_title_raw, re.I)
            if hours_in_title:
                h1 = int(hours_in_title.group(1))
                h2 = int(hours_in_title.group(2)) if hours_in_title.group(2) else 0
                hours = h1 + h2
                unit_title = re.sub(r"\s*\d+(?:\s*\+\s*\d+)?\s*(?:PERIODS|HOURS|HRS)?\s*$", "", unit_title_raw, flags=re.I).strip(" .:-")
            else:
                hours = 9
                hours_match = re.search(r"(\d+)(?:\s*\+\s*(\d+))?\s*(?:PERIODS|HOURS|HRS)?", unit_content, re.I)
                if hours_match:
                    h1 = int(hours_match.group(1))
                    h2 = int(hours_match.group(2)) if hours_match.group(2) else 0
                    hours = h1 + h2
                unit_title = unit_title_raw.strip(" .:-")

            raw_unit_lines = []
            for line in lines[idx:]:
                if re.match(r"^(?:---\s*)?PAGE\s*\d+(?:\s*---)?$", line, re.I):
                    continue
                if re.match(r"^\d+(?:\+\d+)?\s*$", line):
                    continue
                if re.match(r"^(?:DEPARTMENT OF|AUTONOMOUS CURRICULUM|SEMESTER|B\.?TECH|S\.?NO|L\s*T\s*P\s*C|CREDITS|CATEGORY|PREAMBLE|PREREQUISITES)", line, re.I):
                    continue
                if re.match(r"^(?:TEXT|REFERENCE|COURSE OUTCOME|CO\d|PO\d|TOTAL|PERIODS)", line, re.I):
                    break
                raw_unit_lines.append(line)

            rejoined_lines = []
            for l in raw_unit_lines:
                if rejoined_lines and (rejoined_lines[-1].endswith("-") or rejoined_lines[-1].endswith("–")):
                    # Word split across line
                    rejoined_lines[-1] = rejoined_lines[-1][:-1] + l.lstrip()
                else:
                    rejoined_lines.append(l)

            raw_unit_text = "\n".join(rejoined_lines).strip()
            raw_unit_text = re.sub(r"^\s*\d+(?:\s*\+\s*\d+)?\s*(?:PERIODS|HOURS|HRS)?\s*", "", raw_unit_text, flags=re.I).strip()

            if not raw_unit_text:
                raw_unit_text = unit_title

            topics = []
            # Split raw_unit_text into individual topics by spaced hyphens, newlines, semicolons, or bullet characters
            raw_chunks = re.split(r"\n|\s+[\-\–\—]\s+|;\s*|[•●▪➢❖\*]\s*", raw_unit_text)
            topic_count = 1

            for chunk in raw_chunks:
                t_clean = chunk.strip(" .-,;")
                t_clean = re.sub(r"^(?:---\s*)?PAGE\s*\d+(?:\s*---)?\s*", "", t_clean, flags=re.I).strip(" .-,;")
                if len(t_clean) > 2 and not re.match(r"^\d+(?:\+\d+)?\s*(?:PERIODS|HOURS|HRS)?$", t_clean, re.I):
                    bloom_lvl, bloom_src = infer_bloom_level(t_clean)
                    topics.append({
                        "id": f"u{unit_num}t{topic_count}",
                        "text": t_clean,
                        "bloom": bloom_lvl,
                        "bloom_source": bloom_src
                    })
                    topic_count += 1

            if not topics:
                topics.append({
                    "id": f"u{unit_num}t1",
                    "text": raw_unit_text,
                    "bloom": "understand",
                    "bloom_source": "inferred"
                })

            units.append({
                "number": unit_num,
                "title": unit_title.strip(" .:-"),
                "hours": hours,
                "text": raw_unit_text,
                "topics": topics
            })

    # If no units exist, check for Laboratory / Practical Experiments section
    if not units:
        lab_header_re = re.compile(
            r"(?:^|\n)\s*(LIST OF EXPERIMENTS|LAB EXPERIMENTS|LABORATORY EXPERIMENTS|PRACTICAL EXPERIMENTS|EXPERIMENTS|PRACTICALS|LABORATORY EXERCISES|PRACTICAL EXERCISES|PROGRAMS|PRACTICAL CONTENT|LAB CONTENT|LIST OF PRACTICALS|EXERCISES)\b",
            re.I
        )
        lab_match = lab_header_re.search(full_course_text)
        if lab_match:
            lab_heading = lab_match.group(1).title()
            exp_text_segment = full_course_text[lab_match.end():]

            # Cut off before COs, Books, Total Periods, CO-PO matrix or next course header
            end_match = re.search(
                r"\n\s*(?:COURSE\s*OUTCOME|WEB\s*REFERENCE|TEXT\s*BOOK|REFERENCE|CO\-PO|TOTAL\s*(?:PERIODS|HOURS)|TOTAL\s*:|[A-Z]{2,6}\d{3,5})\b",
                exp_text_segment,
                re.I
            )
            if end_match:
                exp_text_segment = exp_text_segment[:end_match.start()]

            lines_raw = [l.strip() for l in exp_text_segment.splitlines() if l.strip()]
            clean_exp_lines = []
            for l in lines_raw:
                if re.match(r"^(?:---\s*)?PAGE\s*\d+(?:\s*---)?$", l, re.I):
                    continue
                if re.match(r"^\d+\s*$", l):
                    continue
                if re.search(r"(?:CURRICULUM|SYLLABUS|COLLEGE|INSTITUTE|DEPARTMENT|APPROVED|BOS|SEM\.|SEMESTER|B\.?E|B\.?TECH|SDGs|PRACTICAL COURSE)", l, re.I):
                    continue
                if re.match(r"^(?:L\s*T\s*P\s*C|CREDITS|CATEGORY|COURSE OBJECTIVE|OBJECTIVES)", l, re.I):
                    continue
                clean_exp_lines.append(l)

            raw_exps = []
            curr_exp = ""
            curr_num = 1

            for l in clean_exp_lines:
                num_m = re.match(r"^(\d+)[\.\)\-]\s*(.*)", l)
                bullet_m = re.match(r"^[●•\*]\s*(.*)", l)

                if num_m:
                    if curr_exp:
                        raw_exps.append({"number": curr_num, "text": curr_exp})
                    curr_num = int(num_m.group(1))
                    curr_exp = num_m.group(2).strip()
                elif bullet_m:
                    if curr_exp:
                        raw_exps.append({"number": curr_num, "text": curr_exp})
                        curr_num += 1
                    curr_exp = bullet_m.group(1).strip()
                else:
                    if curr_exp:
                        if curr_exp.endswith("-") or curr_exp.endswith("–"):
                            curr_exp = curr_exp[:-1] + "-" + l
                        else:
                            curr_exp += " " + l
                    else:
                        curr_exp = l
                        curr_num = len(raw_exps) + 1

            if curr_exp:
                raw_exps.append({"number": curr_num, "text": curr_exp})

            for e in raw_exps:
                clean_t = re.sub(r"\s*(?:TOTAL\s*(?:PERIODS|HOURS|HRS)|COURSE\s*OUTCOME|WEB\s*REFERENCE|CO\-PO|CO\d|PO\d).*", "", e["text"], flags=re.S | re.I)
                clean_t = re.sub(r"^(?:---\s*)?PAGE\s*\d+(?:\s*---)?\s*", "", clean_t, flags=re.I).strip(" .-,;")
                if len(clean_t) >= 3:
                    experiments.append({"number": e["number"], "text": clean_t})

    # Determine final total hours
    if total_hrs is None:
        if units:
            total_hrs = sum(u.get("hours", 9) for u in units)
        elif practical > 0:
            total_hrs = practical * 15
        else:
            total_hrs = 45

    # Course Outcomes (COs) - Extract real outcome statements, ignoring matrix table ratings
    course_outcomes = []
    # Match CO definitions e.g. "CO1 Formulate and apply relational algebraic expressions... K4"
    co_matches = re.findall(r"\b(CO\d+)\s*[:\-\s]+(.+?)(?=(?:\bCO\d+\b|\bPO\d+\b|\bUNIT\b|COURSE OUTCOMES|PROGRAMME OUTCOMES|[A-Z]{2,6}\d{3,5}|\n\n|$))", full_course_text, re.S)
    
    seen_cos = set()
    for co_id, co_text in co_matches:
        k_printed = re.search(r"\b(K[1-6]|L[1-6])\b", co_text, re.I)
        co_clean = re.sub(r"\s*(?:K[1-6]|L[1-6]|\d+)\s*$", "", co_text.strip(), flags=re.I).strip(" :-|")
        co_clean = re.sub(r"\s+", " ", co_clean)
        # Verify co_clean is a real statement with English words, not a matrix rating or header
        has_real_words = bool(re.search(r"[a-zA-Z]{3,}\s+[a-zA-Z]{3,}", co_clean))
        if len(co_clean) >= 12 and has_real_words and not re.match(r"^[\d\s\-SML]+$", co_clean) and co_id.upper() not in seen_cos:
            bloom_lvl, bloom_src = infer_bloom_level(co_clean)
            if k_printed:
                bloom_lvl = k_printed.group(1).upper()
                bloom_src = "printed"
            course_outcomes.append({
                "id": co_id.upper(),
                "text": co_clean,
                "bloom": bloom_lvl,
                "bloom_source": bloom_src
            })

    # Programme Outcomes (POs) - Extract explicit PO text definitions if present in doc
    programme_outcomes = []
    po_matches = re.findall(r"\b(PO\d+)\s*[:\-\s]+([A-Za-z][^\n]{15,})", full_course_text)
    seen_pos = set()
    for po_id, po_text in po_matches:
        po_clean = po_text.strip()
        # Require real sentence words, avoid column headers like PO9: PO10 or matrix rows
        has_real_words = bool(re.search(r"[a-zA-Z]{3,}\s+[a-zA-Z]{3,}", po_clean))
        if has_real_words and not re.search(r"^(?:PO\d+|PSO\d+|\s|-)+$", po_clean, re.I) and po_id.upper() not in seen_pos:
            seen_pos.add(po_id.upper())
            programme_outcomes.append({
                "id": po_id.upper(),
                "text": po_clean
            })

    # CO-PO Matrix
    co_po_matrix = {}
    # CO-PO / CO-PSO Matrix Extraction
    co_po_matrix = {}
    matrix_hdr_m = re.search(r"(?:COs?/POs?|POs?/COs?|CO/PO|CO\-PO|POs|MAPPING OF COs)[^\n]*\n([^\n]+)", full_course_text, re.I)
    col_names = []
    if matrix_hdr_m:
        hdr_line = matrix_hdr_m.group(1)
        col_names = [c.upper() for c in re.findall(r"\b(PO\d+|PSO\d+)\b", hdr_line, re.I)]

    matrix_rows = re.findall(r"\b(CO\d+)\s+((?:[SML123\-\s]{10,}))", full_course_text)
    for co_id, vals in matrix_rows:
        tokens = [v.strip() for v in vals.split() if v.strip()]
        co_key = co_id.upper()
        if co_key not in co_po_matrix:
            co_po_matrix[co_key] = {}
        for idx, val in enumerate(tokens):
            if val in {"S", "M", "L", "1", "2", "3"}:
                col_key = col_names[idx] if idx < len(col_names) else f"PO{idx + 1}"
                co_po_matrix[co_key][col_key] = val

    # Textbooks & Reference Books Extraction
    KNOWN_PUBLISHERS = [
        "Pearson", "McGraw-Hill", "McGraw Hill", "MC Graw Hill", "Elsevier", "Wiley", "Oxford", "Cambridge",
        "Prentice", "Khanna", "Cengage", "CENGAGE", "Springer", "O'Reilly", "O’Reilly", "Shroff",
        "Addison-Wesley", "Morgan Kaufmann", "New Age", "Tata McGraw", "Laxmi", "Vikas", "PHI", "S. Chand"
    ]

    books = []
    book_block = re.search(r"(?:TEXTBOOK|TEXT BOOKS|REFERENCES|REFERENCE BOOKS)\s*[:\-\n]+(.*?)(?:CO\-PO|COURSE DESIGNERS|WEB REFERENCES|OUTCOMES|COURSE OUTCOMES|[A-Z]{2,6}\d{3,5}|$)", full_course_text, re.S | re.I)

    if book_block:
        block_text = book_block.group(1)
        sub_sections = re.split(r"(REFERENCES\s*[:\-\n]+)", block_text, flags=re.I)

        current_kind = "text"
        sec_texts = []
        for part in sub_sections:
            if re.match(r"REFERENCES", part, re.I):
                current_kind = "reference"
            else:
                sec_texts.append((current_kind, part))

        for kind_val, text_segment in sec_texts:
            raw_lines = [l.strip() for l in text_segment.split("\n") if l.strip()]
            entries = []
            curr_entry = ""
            for l in raw_lines:
                if re.match(r"^(?:[TR]?\d+[\.\)\-]|[\-\•\●\*]|\[(?:T|R)?\d+\])", l, re.I):
                    if curr_entry:
                        entries.append(curr_entry)
                    curr_entry = l
                else:
                    if curr_entry:
                        curr_entry += " " + l
                    else:
                        curr_entry = l
            if curr_entry:
                entries.append(curr_entry)

            for entry in entries:
                clean_e = re.sub(r"[^\x00-\x7F]+", " ", entry).strip()
                clean_e = re.sub(r"(?:---\s*)?PAGE\s*\d+(?:\s*---)?", "", clean_e, flags=re.I).strip(" .-,;")
                clean_e = re.sub(r"^\s*(?:[TR]?\d+[\.\)\-]?\s*|[\-\•\●\*]\s*)+", "", clean_e).strip()
                
                is_matrix_text = bool(re.search(r"\b(POs|COs|PSOs|PO\d+|CO\d+|CO\-PO|CO/PO)\b", clean_e, re.I)) and bool(re.search(r"[\d\s\-]{6,}", clean_e))
                has_words = bool(re.search(r"[a-zA-Z]{3,}\s+[a-zA-Z]{3,}", clean_e))
                if len(clean_e) < 8 or "http" in clean_e.lower() or "www." in clean_e.lower() or is_matrix_text or not has_words:
                    continue

                year_m = re.search(r"\b(19\d{2}|20\d{2})\b", clean_e)
                year_val = int(year_m.group(1)) if year_m else "Not specified"
                clean_no_yr = re.sub(r"\b(19\d{2}|20\d{2})\b", "", clean_e)

                ed_m = re.search(r"\b((?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|\d+(?:st|nd|rd|th))\s+(?:Edition|Ed\.?))\b", clean_no_yr, re.I)
                ed_val = ed_m.group(1) if ed_m else "Standard Edition"
                clean_no_ed = re.sub(r"\b((?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|\d+(?:st|nd|rd|th))\s+(?:Edition|Ed\.?))\b", "", clean_no_yr, flags=re.I)

                quote_m = re.search(r'["“]([^"”]+)["”]', clean_no_ed)
                if quote_m:
                    title_val = quote_m.group(1).strip(" ,.-;")
                    author_part = clean_no_ed[:quote_m.start()].strip(" ,.-;")
                    pub_part = clean_no_ed[quote_m.end():].strip(" ,.-;")
                    author_val = re.sub(r"^\s*(?:[TR]?\d+[\.\)\-]?\s*)+", "", author_part).strip(" ,.-;")
                    publisher_val = re.sub(r"\([^)]*\)", "", pub_part).strip(" ,.-;")
                else:
                    dot_parts = [p.strip(" ,-;") for p in clean_no_ed.split(".") if p.strip(" ,-;")]
                    if len(dot_parts) >= 2:
                        p0 = dot_parts[0]
                        p1 = dot_parts[1]
                        # Check if p0 is author list (contains names or initial patterns like 'Silberschatz A' or 'Elmasri R')
                        w_count0 = len(p0.split())
                        is_p0_title = bool(re.search(r"\b(Introduction|Principles|Fundamentals|Digital|Data|Computer|Programming|System|Architecture|Design|Engineering|Mathematics)\b", p0, re.I))
                        
                        if is_p0_title or w_count0 > 8:
                            title_val = p0
                            author_val = "Not specified"
                            publisher_val = ". ".join(dot_parts[1:])
                        else:
                            author_val = p0
                            title_val = p1
                            publisher_val = ". ".join(dot_parts[2:]) if len(dot_parts) > 2 else "Not specified"
                    else:
                        earliest_pub_pos = len(clean_no_ed)
                        for pub_kw in KNOWN_PUBLISHERS:
                            m_pub = re.search(rf"\b{re.escape(pub_kw)}\b", clean_no_ed, re.I)
                            if m_pub and m_pub.start() < earliest_pub_pos:
                                earliest_pub_pos = m_pub.start()

                        if earliest_pub_pos < len(clean_no_ed):
                            publisher_val = clean_no_ed[earliest_pub_pos:].strip(" ,.-;")
                            before_pub = clean_no_ed[:earliest_pub_pos].strip(" ,.-;")
                            comma_parts = [p.strip(" ,.-;") for p in before_pub.split(",") if p.strip(" ,.-;")]
                            if len(comma_parts) >= 2:
                                author_val = comma_parts[0]
                                title_val = ", ".join(comma_parts[1:])
                            else:
                                author_val = "Not specified"
                                title_val = before_pub
                        else:
                            parts = [p.strip(" ,.-;") for p in clean_no_ed.split(",") if p.strip(" ,.-;")]
                            if len(parts) >= 2:
                                author_val = parts[0]
                                title_val = ", ".join(parts[1:])
                            else:
                                author_val = "Not specified"
                                title_val = clean_no_ed
                            publisher_val = "Not specified"

                publisher_val = re.sub(r"\s*(?:\.|,\s*)?(?:COURSE DESIGNERS|WEB REFERENCES|S\.No|FACULTY|DESIGNATION|MAIL ID).*", "", publisher_val, flags=re.S | re.I).strip(" ,.-;")
                author_val = author_val if author_val and len(author_val) >= 3 else "Not specified"
                publisher_val = publisher_val if publisher_val and len(publisher_val) >= 3 else "Not specified"
                title_val = title_val if title_val else clean_e

                books.append({
                    "kind": kind_val,
                    "title": title_val,
                    "author": author_val,
                    "publisher": publisher_val,
                    "edition": ed_val,
                    "year": year_val
                })

    doc.close()

    not_extracted = []
    if not course_outcomes:
        not_extracted.append("course_outcomes - Information not found in the uploaded document.")
    if not programme_outcomes:
        not_extracted.append("programme_outcomes - Information not found in the uploaded document.")
    if not co_po_matrix:
        not_extracted.append("co_po_matrix - Information not found in the uploaded document.")


    return {
        "course": {
            "code": actual_code,
            "title": course_title,
            "category": category,
            "lecture": lecture,
            "tutorial": tutorial,
            "practical": practical,
            "credits": credits_val,
            "pages": course_pages,
            "total_hours": total_hrs
        },
        "units": units,
        "experiments": experiments,
        "lab_heading": lab_heading,
        "course_outcomes": course_outcomes,
        "programme_outcomes": programme_outcomes,
        "co_po_matrix": co_po_matrix,
        "books": books[:6],
        "not_extracted": not_extracted
    }


