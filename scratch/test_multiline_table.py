import fitz
import re

pdf_path = "backend/uploads/Sri Sivasubramaniya Nadar College of Engineering  ( SSN ) SYLLABUS.pdf"
doc = fitz.open(pdf_path)

sem_map = {f"Semester {i}": [] for i in range(1, 9)}
num_map = {"1":1, "I":1, "2":2, "II":2, "3":3, "III":3, "4":4, "IV":4, "5":5, "V":5, "6":6, "VI":6, "7":7, "VII":7, "8":8, "VIII":8}

sem_header_re = re.compile(r"^\s*(?:SEMESTER|SEM)\s*[-–:]?\s*([0-9]{1,2}|I{1,3}|IV|V|VI{0,3}|VII|VIII)\b", re.I)

curr_sem = None

# Scan pages 11 to 17 (Official Curriculum Tables for SSN PDF)
for p_num in range(11, 17):
    p_text = doc[p_num - 1].get_text()
    lines = [l.strip() for l in p_text.splitlines() if l.strip()]

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        l_up = line.upper()

        m = sem_header_re.match(line)
        if m and len(line.split()) <= 4:
            val = m.group(1).upper()
            if val in num_map:
                curr_sem = num_map[val]
                print(f"--> Found Semester {curr_sem} Header on Page {p_num}")
                idx += 1
                continue

        if curr_sem:
            # Check if line starts a course row (e.g. "1.", "2.", "3." or course code like "UCS1301", "UMA1377")
            m_seq = re.match(r"^([0-9]{1,2})\.\s*(.*)", line)
            m_code = re.match(r"^([A-Z0-9]{5,10})$", line)

            if m_seq or m_code:
                # Accumulate title text from next lines until category/credit/number or next row starts
                raw_parts = []
                if m_seq and m_seq.group(2):
                    raw_parts.append(m_seq.group(2))

                step = idx + 1
                while step < len(lines):
                    nxt = lines[step]
                    nxt_up = nxt.upper()

                    # Stop if next row or table footer/header begins
                    if sem_header_re.match(nxt) or re.match(r"^([0-9]{1,2})\.\s*", nxt) or nxt_up in ["THEORY", "PRACTICALS", "TOTAL", "S. NO", "COURSE CODE", "COURSE TITLE", "CATEGORY"]:
                        break

                    # If line is category or credit (e.g. BS, PC, ES, HS, EEC, 3, 4, 1.5, 5), stop!
                    if nxt_up in ["BS", "PC", "ES", "HS", "PE", "OE", "EEC", "MC"] or nxt.isdigit():
                        break

                    # If line is course code (e.g. UMA1377), skip code
                    if not re.match(r"^[A-Z0-9]{5,10}$", nxt):
                        raw_parts.append(nxt)

                    step += 1

                full_title = " ".join(raw_parts).strip()
                # Clean up title
                clean_title = re.sub(r"^[A-Z0-9]{5,10}\s*", "", full_title).strip()
                clean_title = re.sub(r"\s+", " ", clean_title)

                if len(clean_title) >= 3 and not any(clean_title.lower() == s.lower() for s in sem_map[f"Semester {curr_sem}"]):
                    if not any(k in clean_title.upper() for k in ["COURSE TITLE", "CATEGORY", "CONTACT", "PERIODS", "THEORY", "PRACTICALS", "TOTAL"]):
                        sem_map[f"Semester {curr_sem}"].append(clean_title)

                idx = step
                continue

        idx += 1

print("=" * 50)
print("EXTRACTED CURRICULUM TABLE SUBJECTS:")
for sem, subs in sem_map.items():
    print(f"{sem}: {len(subs)} subjects")
    for s in subs:
        print("   -", s)
